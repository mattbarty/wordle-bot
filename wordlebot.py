from suffix_trie import create_trie
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

DICTIONARY = "english_lexicon.txt"
trie = create_trie(DICTIONARY)


def search_trie(trie, rack, square):
    possible_words = []

    def traverse(node, rack, square, word=''):
        if square:
            if square.terminal_node and '$' in node.children:
                possible_words.append(word)
            if not square.letter:  # -- If a letter isn't certain
                for letter in rack:
                    if letter == '?':
                        for key in node.children:
                            if key not in square.exclude:
                                new_node = node.children[key]
                                new_rack = rack.copy()
                                new_rack.remove(letter)
                                new_word = word + key
                                next_square = square.next
                                traverse(new_node, new_rack, next_square,
                                         new_word)
                            else:
                                continue
                    else:
                        for key in node.children:
                            if letter == key and letter in rack and letter not in square.exclude:
                                new_node = node.children[letter]
                                new_rack = rack.copy()
                                new_rack.remove(letter)
                                new_word = word + letter
                                next_square = square.next
                                traverse(new_node, new_rack, next_square,
                                         new_word)
            else:  # -- If a letter is certain
                if square.letter in node.children and square.letter in rack:
                    new_node = node.children[square.letter]
                    new_rack = rack.copy()
                    new_rack.remove(square.letter)
                    new_word = word + square.letter
                    next_square = square.next
                    traverse(new_node, new_rack, next_square, new_word)

    traverse(trie, rack, square)

    return possible_words


class Square:
    id = 0

    def __init__(self, letter='', exclude=[]):
        self.pos = Square.id
        Square.id += 1
        self.next = None
        self.letter = letter
        self.exclude = exclude
        self.terminal_node = False

    def __repr__(self):
        return f'sq{self.pos}'


class WordleBot:

    game = 0

    def __init__(self, delay=0.25):
        self.delay = delay

        self.a = Square('', exclude=list(''))
        self.b = Square('', exclude=list(''))
        self.c = Square('', exclude=list(''))
        self.d = Square('', exclude=list(''))
        self.e = Square('', exclude=list(''))
        self._f = Square()  # -- Terminal node.

        self.a.next = self.b
        self.b.next = self.c
        self.c.next = self.d
        self.d.next = self.e
        self.e.next = self._f
        self._f.terminal_node = True

        self.game += WordleBot.game
        WordleBot.game += 1
        self.round = 0

        self.used_words = []
        self.known_letters = []
        self.exclude_list = []
        self.squares = [self.a, self.b, self.c, self.d, self.e]
        self.guess = 'arose'

    def type_with_delay(self, keys, body):
        for key in keys:
            body.send_keys(key)
        time.sleep(self.delay)

    def play(self, games=1):
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        driver = Chrome()

        driver.get('https://www.wordleunlimited.com/')
        for x in range(games):
            print(f'game: {x + 1}')
            self.solve(driver)
            self.reset()
        print('game over!')
        time.sleep(1000)

    def solve(self, driver):
        rows = driver.find_elements_by_class_name('RowL')
        body = driver.find_element_by_tag_name('body')

        for row in rows:
            self.type_with_delay(list(self.guess.lower()), body)
            time.sleep(self.delay)
            body.send_keys(Keys.ENTER)

            answers = row.find_elements_by_tag_name('div')

            decode_dict = {
                'RowL-letter letter-absent': 'absent',
                'RowL-letter letter-elsewhere': 'elsewhere',
                'RowL-letter letter-correct': 'correct',
                'RowL-letter': 'empty'
            }

            self.clues = [
                decode_dict[square.get_attribute('class')]
                for square in answers
            ]

            if self.check_win() or self.round == 5:
                time.sleep(0.25)
                body.send_keys(Keys.ENTER)
                break
            else:
                self.update_clues()
                self.best_guess()
                self.round += 1

    def weighted_answers(self, potential_answers):
        pos_weight = {
            0: {},
            1: {},
            2: {},
            3: {},
            4: {},
        }

        for word in potential_answers:
            for i, letter in enumerate(word):
                if letter in pos_weight[i]:
                    pos_weight[i][letter] += 1
                else:
                    pos_weight[i][letter] = 1

        _max = sum([value[1] for value in list(pos_weight[0].items())])

        for index in pos_weight:
            pos_weight[index] = {
                key: round(((value / _max) * 100), 1)
                for key, value in pos_weight[index].items()
            }

        def apply_weights(word):
            res = 0
            for i, letter in enumerate(word):
                res += pos_weight[i].get(letter)
            return round(res, 1)

        return sorted([(x, apply_weights(x)) for x in potential_answers],
                      key=lambda x: x[1],
                      reverse=True)

    def best_guess(self):

        def clues():
            print('\n')
            print(
                f'{self.a} | letter: {self.a.letter} | exclude: {self.a.exclude}'
            )
            print(
                f'{self.b} | letter: {self.b.letter} | exclude: {self.b.exclude}'
            )
            print(
                f'{self.c} | letter: {self.c.letter} | exclude: {self.c.exclude}'
            )
            print(
                f'{self.d} | letter: {self.d.letter} | exclude: {self.d.exclude}'
            )
            print(
                f'{self.e} | letter: {self.e.letter} | exclude: {self.e.exclude}'
            )

        known_letters = self.known_letters

        for square in self.squares:
            if square.letter:
                known_letters.append(square.letter)

        known_letters = list(''.join(known_letters).rjust(5, '?'))
        potential_answers = set(search_trie(trie, known_letters, self.a))
        potential_answers = [
            word for word in potential_answers if word not in self.used_words
        ]
        weighted_guesses = self.weighted_answers(potential_answers)
        self.guess = weighted_guesses[0][0]
        self.used_words.append(self.guess)

    def check_win(self):
        return all(clues == 'correct' or clues == 'empty'
                   for clues in self.clues)

    def update_clues(self):
        for square, letter, clue in zip(self.squares, self.guess.upper(),
                                        self.clues):
            if clue == 'correct':
                square.letter = letter
                if letter in self.known_letters:
                    self.known_letters.remove(letter)
            elif clue == 'elsewhere':
                square.exclude += letter
                if letter not in self.known_letters:
                    self.known_letters += letter
            elif clue == 'absent':
                if letter not in self.exclude_list and letter not in self.known_letters:
                    self.exclude_list += letter

        for square in self.squares:
            square.exclude += self.exclude_list
        self.exclude_list = []

    def reset(self):
        for square in self.squares:
            square.exclude = []
            square.letter = ''
        self.known_letters = []
        self.exclude_list = []
        self.used_words = []

        self.guess = 'arose'
        self.round = 0


if __name__ == '__main__':
    bot = WordleBot(delay=0)
    bot.play(5)
