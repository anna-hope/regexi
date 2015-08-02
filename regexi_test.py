from argparse import ArgumentParser
from collections import Counter
from itertools import chain, tee
from pprint import pprint
import re

import regexi

def test_regex_matches(regex, words):
    for word in words:
        match = re.match(regex, word)
        if match:
            yield word, True
        else:
            yield word, False

def test_all(regex, words, must_work=True):
    if not regex:
        print('no regex given')
        return False

    results1, results2 = tee(test_regex_matches(regex, words), 2)

    status = all(result for _, result in results1)

    if not must_work:
        status = not status

    if status:
        print('all words passed the test')
        return True
    else:
        for word, status in results2:
            if status is not must_work:
                print('{} failed'.format(word))
        return False




def run_test(file, mode):
    regex = regexi.run(file, mode, verbose=True)

    with open(file) as word_list:
        words = [w.strip() for w in word_list.readlines()]


    print('testing', regex)
    result = test_all(regex, words)


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('file', help='file with a list of words')
    arg_parser.add_argument('--mode', choices=('all', 'vs'), default='all')
    args = arg_parser.parse_args()
    run_test(args.file, args.mode)
