__author__ = 'anton'

from argparse import ArgumentParser
from collections import Counter
from itertools import zip_longest, chain
import json
from pprint import pprint

def find_letters(word_list):
    words = set(word_list)

    for segments in zip_longest(*words):
        counted_segments = Counter(segments)
        yield counted_segments


def get_differences(first_set, second_set):

    for letters1, letters2 in zip_longest(first_set, second_set, fillvalue=set()):
        first_letters, second_letters = set(letters1), set(letters2)
        difference = first_letters.difference(second_letters)
        if difference in first_letters:
            group = 1
        else:
            group = 2
        if difference:
            yield difference, group

def filter_noise(segment_list):
    for counted_segments in segment_list:
        num_all_segments = sum(counted_segments.values())
        threshold = min(num_all_segments * 0.001, 5)
        good_segments = {segment for segment, count in counted_segments.items()
                         if count >= threshold}
        yield good_segments


def run(file):
    with open(file) as words_file:
      words = json.load(words_file)

    first, second = words

    first_list, second_list = list(find_letters(first)), list(find_letters(second))
    # filtered_first, filtered_second = filter_noise(first_list), filter_noise(second_list)
    differences = get_differences(first_list, second_list)

    unique_letters = set()
    which_group = Counter()
    for difference, group in differences:
        unique_letters.update(difference)
        which_group[group] += 1

    print('intermediate result')
    pprint(unique_letters)

    better_group = max(which_group, key=lambda item: which_group[item])

    if better_group == 1:
        first_list = filter_noise(first_list)
    else:
        second_list = filter_noise(second_list)

    # run it again
    differences = get_differences(first_list, second_list)
    print(set(letters.pop() for letters, _ in differences))






if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('words')
    args = arg_parser.parse_args()
    run(args.words)