#!/usr/bin/env python

"""
What is a keyword? Glad you asked!

- A word with a non-initial capital.
- A word with no lowercase letters.
- A word in a known list of keywords.
"""

import re
import sys

types = {
    'mobile': ['ios', 'blackberry', 'android', 'iphone', 'app', 'apps'],
    'companies': ['facebook', 'google', 'microsoft', 'apple', 'yahoo', 'adobe'],
    'languages': ['python', 'ruby', 'perl', 'java', 'c', 'c++'],
    'frameworks': ['rails', 'django', 'sinatra', 'flask'],
    'OSes': ['linux', 'windows', 'mac', 'dos', 'solaris', 'bsd'],
    'data': ['mysql', 'mongo', 'redis', 'memcached', 'sql']
}

all_keywords = set()
for name, vals in types.iteritems():
    all_keywords.update(vals)

def non_initial_capital(word):
    return re.search('^.+[A-Z]', word)

def all_uppercase(word):
    return word.isupper()

def letters_and_numbers(word):
    return any(lambda c: c.isdigit()) and any(lambda c: c.isalpha())

def known_keyword(word):
    return word.lower() in all_keywords

matchers = [non_initial_capital, all_uppercase, known_keyword]

def is_keyword(word):
    for f in matchers:
        if f(word):
            return True
    return False

def process(stream):
    found_keywords = set()
    for line in stream:
        for word in re.split('[\s,/:.()-]', line):
            if not word:
                continue
            if is_keyword(word) and word not in found_keywords:
                found_keywords.add(word)
                print word

if __name__ == '__main__':
    f = open(sys.argv[1], 'r')
    process(f)
