class Node:
    id = 0

    def __init__(self, char) -> None:
        self.id = Node.id
        Node.id += 1

        self.terminal_node = False
        self.char = char
        self.children = {}

    def __repr__(self) -> str:
        return f'{self.char} ({self.id})'

    def __str__(self):
        return f'{self.char}'


def add_node(trie, word):

    curr_node = trie

    for char in word:
        if char in curr_node.children:
            curr_node = curr_node.children[char]
        else:
            curr_node.children[char] = Node(char)
            curr_node = curr_node.children[char]

    curr_node.children['$'] = Node('$')
    terminal_node = curr_node.children['$']
    terminal_node.terminal_node = True


def create_trie(word_dictionary):
    trie = Node('*')
    with open(word_dictionary, 'r') as file:
        lexicon = file.read().split('\n')
    for word in sorted(lexicon):
        add_node(trie, word)

    return trie


if __name__ == '__main__':
    DICTIONARY = "valid_words.txt"
    trie = create_trie(DICTIONARY)
