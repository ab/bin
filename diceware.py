#!/usr/bin/env python3

import math
import random
import string
import sys

# SystemRandom is a subclass of random that uses os.urandom
systemrandom = random.SystemRandom()

# TODO: use optparse
punctuation = False

def getlist_words(fname):
    words = []
    with open(fname, 'r') as f:
        previous = None

        for line in f:
            word = line.strip()

            if not word:
                continue

            # strip 's suffixes
            if previous and word == previous + "'s":
                continue

            words.append(word)
            previous = word

    return words

def getlist_diceware(fname):
    words = []
    with open(fname, 'r') as f:
        for line in f:
            word = line.strip()

            if not word:
                continue

            # strip index
            try:
                index, word = word.split('\t')
            except ValueError:
                sys.stderr.write("Bad line format? Expected index<tab>word, not " +
                                 repr(line) + "\n")
                raise
            assert index.isdigit(), 'index should consist of digits'

            words.append(word)

    return words

def getlist_auto(fname):
    if '\t' in open(fname, 'r').readline():
        return getlist_diceware(fname)
    else:
        return getlist_words(fname)

def getwords(wordlist, num=1):
    dictionary = getlist_auto(wordlist)
    return [pair_from_word_list(dictionary) for i in range(num)]

def pair_from_word_list(word_list):
    """
    Get a random word and the entropy it represents from the given word_list.
    """
    return systemrandom.choice(word_list), math.log(len(word_list), 2)

if __name__ == '__main__':
    try:
        num = int(sys.argv[1])
    except (IndexError, ValueError):
        num = 1
    try:
        fname = sys.argv[2]
    except IndexError:
        fname = '/usr/share/dict/words'

    sys.stderr.write("Dictionary: %r\n" % fname)
    words = getwords(fname, num)
    if punctuation:
        punc_words = []
        for word in words[:-1]:
            punc_words.append(word)
            punc_words.append(pair_from_word_list(string.punctuation))
        punc_words.append(words[-1])

        words = punc_words
        sep = ''
    else:
        sep = ' '

    entropy = sum(pair[1] for pair in words)

    sys.stderr.write("Entropy: ~%.1f bits\n" % round(entropy, 1))

    print(sep.join(pair[0] for pair in words))
