from argparse import ArgumentParser
from pprint import pprint
import re

import regexi

def test_regex(regex, words):
    for word in words:
        match = re.match(regex, word)
        if match:
            yield word, True
        else:
            yield word, False

def run_test(file):
    regex = regexi.run(file, None, verbose=True, test_every_step=True)
    with open(file) as word_list:
        words = (w.strip() for w in word_list.readlines())

    print('testing', regex)
    results = test_regex(regex, words)

    fail = 0

    for word, status in results:
        if not status:
            fail += 1
            print(word, 'failed')

    if not fail:
        print('all tests passed')

if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('file', help='file with a list of words')
    args = arg_parser.parse_args()
    run_test(args.file)
