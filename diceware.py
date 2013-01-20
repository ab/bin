#!/usr/bin/env python

import random
import sys

# SystemRandom is a subclass of random that uses os.urandom
randrange = random.SystemRandom().randrange

def getlist(fname):
    f = open(fname, 'r')
    d = ['']

    for line in f:
        word = line.strip()

        # skip "" and "...'s"
        if not word or word == d[-1] + "'s":
            continue

        # strip index, if any:
        if '\t' in word:
            x = word.split('\t')
            if len(x) == 2 and x[0].isdigit():
                word = x[1]

        d.append(word)

    f.close()

    d.remove('')
    return d

def getwords(wordlist, num=1):
    words = getlist(wordlist)
    maxword = len(words)

    result = []

    for i in range(num):
        result.append(words[randrange(maxword)])

    return result


if __name__ == '__main__':
    try:
        num = int(sys.argv[1])
    except (IndexError, ValueError):
        num = 1
    try:
        fname = sys.argv[2]
    except IndexError:
        fname = '/usr/share/dict/words'

    sys.stderr.write("Using '%s'.\n" % fname)
    print ' '.join(getwords(fname, num))

