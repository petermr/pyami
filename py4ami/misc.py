"""miscellaneous routines that might be useful sometime"""

class TrieNode(object):
    """
    Our trie node implementation. Very basic. but does the job

    from https://towardsdatascience.com/implementing-a-trie-data-structure-in-python-in-less-than-100-lines-of-code-a877ea23c1a1
    """

    def __init__(self, char: str):
        """works on STRING"""
        self.char = char
        self.children = []
        # Is it the last character of the word.`
        self.word_finished = False
        # How many times this character appeared in the addition process
        self.counter = 1

    def add(self, word: str):
        """
        Adding a word in the trie structure
        """
        node = self
        for char in word:
            found_in_child = False
            # Search for the character in the children of the present `node`
            for child in node.children:
                if child.char == char:
                    # We found it, increase the hit_counter by 1 to keep track that another
                    # word has it as well
                    child.hit_counter += 1
                    # And point the node to the child that contains this char
                    node = child
                    found_in_child = True
                    break
            # We did not find it so add a new child
            if not found_in_child:
                new_node = TrieNode(char)
                node.children.append(new_node)
                # And then point node to the new child
                node = new_node
        # Everything finished. Mark it as the end of a word.
        node.word_finished = True

    def find_prefix(self, prefix: str) -> Tuple[bool, int]:
        """
        Check and return
          1. If the prefix exists in any of the words we added so far
          2. If yes then how may words actually have the prefix
        """
        node = self
        # If the root node has no children, then return False.
        # Because it means we are trying to search in an empty trie
        if not self.children:
            return False, 0
        for char in prefix:
            char_not_found = True
            # Search through all the children of the present `node`
            for child in node.children:
                if child.char == char:
                    # We found the char existing in the child.
                    char_not_found = False
                    # Assign node as the child containing the char and break
                    node = child
                    break
            # Return False anyway when we did not find a char.
            if char_not_found:
                return False, 0
        # Well, we are here means we have found the prefix. Return true to indicate that
        # And also the hit_counter of the last node. This indicates how many words have this
        # prefix
        return True, node.counter

    @staticmethod
    def test():
        root = TrieNode('*')
        root.add("hackathon")
        root.add('hack')

        for term in ("hac", "hack", "hackathon", "ha", "hammer"):
            print(term, root.find_prefix(term))


#    TrieNode.test()

class Ngrams:
    """Various codes from StackOverflow and similar"""

    def tokenize(string):
        """Convert string to lowercase and split into words (ignoring
        punctuation), returning list of words.
        """
        return re.findall(r'\w+', string.lower())


    def count_ngrams(self, lines, min_length=2, max_length=4):
        """Iterate through given lines iterator (file object or list of
        lines) and return n-gram frequencies. The return value is a dict
        mapping the length of the n-gram to a collections.Counter
        object of n-gram tuple and number of times that n-gram occurred.
        Returned dict includes n-grams of length min_length to max_length.
        """
        self.lengths = range(min_length, max_length + 1)
        self.ngrams = {length: collections.Counter() for length in lengths}
        self.queue = collections.deque(maxlen=max_length)

    # Helper function to add n-grams at start of current queue to dict
    def add_queue(self):
        current = tuple(self.queue)
        for length in self.lengths:
            if len(current) >= length:
                self.ngrams[length][current[:length]] += 1

    # Loop through all lines and words and add n-grams to dict
        for line in self.lines:
            for word in tokenize(line):
                self.queue._append_facet(word)
                if len(self.queue) >= self.max_length:
                    add_queue()

        # Make sure we get the n-grams at the tail end of the queue
        while len(self.queue) > self.min_length:
            self.queue.popleft()
            add_queue()

        return self.ngrams


    def print_most_frequent(ngrams, num=10):
        """Print num most common n-grams of each length in n-grams dict."""
        for n in sorted(ngrams):
            print('----- {} most common {}-grams -----'.format(num, n))
            for gram, count in ngrams[n].most_common(num):
                print('{0}: {1}'.format(' '.join(gram), count))
            print('')


    def test(file):
        with open(file) as f:
            ngrams = count_ngrams(f)
        print_most_frequent(ngrams)


# http://www.locallyoptimal.com/blog/2013/01/20/elegant-n-gram-generation-in-python/

    def test1():
        input_list = "to be or not to be that is the question whether tis nob"


    @staticmethod
    def find_bigrams(input_list):
        return zip(input_list, input_list[1:])

    @staticmethod
    def explicit_ngrams(input_list):
        # Bigrams
        zip(input_list, input_list[1:])
        # Trigrams
        zip(input_list, input_list[1:], input_list[2:])
        # and so on
        zip(input_list, input_list[1:], input_list[2:], input_list[3:])

    @staticmethod
    def find_ngrams(input_list, n):
        return zip(*[input_list[i:] for i in range(n)])

