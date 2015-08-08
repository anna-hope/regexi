__author__ = 'anton'

from argparse import ArgumentParser
from collections import Counter
from itertools import zip_longest, chain
import json
from pprint import pprint

def ngramicise(word_list, n=2):
    for word in word_list:
        current = 0
        next = current + n
        ngram_word = []
        while next < len(word) + 1:
            ngram_word.append(tuple(word[current:next]))
            current += 1
            next = current + n
        yield ngram_word


def find_letters(word_list, reverse=False):

    for segments in zip_longest(*word_list):
        counted_segments = Counter(segments)
        yield counted_segments


def get_differences(first_set, second_set):

    unique_set1 = []
    unique_set2 = []
    for letters1, letters2 in zip_longest(first_set, second_set, fillvalue=set()):
        first_letters, second_letters = set(letters1), set(letters2)

        unique_1 = first_letters.difference(second_letters)
        unique_2 = second_letters.difference(first_letters)

        unique_set1.append(unique_1)
        unique_set2.append(unique_2)

    return unique_set1, unique_set2


def pick_best_segment(scores):
    maximum = max(enumerate(scores), key=lambda x: x[1])
    best_segment = maximum[0]
    return best_segment

def get_set_score(letter_set, letter_list):
    if not letter_set:
        return 0
    set_length = len(letter_set)
    occurrence = 0
    for letter in letter_set:
        if letter in letter_list:
            occurrence += 1

    coverage = occurrence / len(letter_list)
    score = coverage / set_length
    return score

def pick_best_set(scores1, scores2):
    """
    get the most 'useful' set
    :param scores1:
    :param scores2:
    :return:
    """
    # best_counts = Counter()
    # for score1, score2 in zip(scores1, scores2):
    #     best_set_segment = max(score1, score2)
    #     if best_set_segment is score1:
    #         best_counts[0] += 1
    #     else:
    #         best_counts[1] += 1

    best_set = max(scores1, scores2, key=lambda x: max(x))
    if best_set is scores1:
        return 0
    else:
        return 1


def filter_spurious_data(unique_set):
    for segment_point in unique_set:
        threshold = min(5, sum(segment_point.values()) * 0.001)
        good_segments = {}
        for segment, count in segment_point.items():
            if count > threshold:
                good_segments[segment] = count
        yield good_segments



def run_letters(first, second):
    first_list, second_list = list(find_letters(first)), list(find_letters(second))
    differences_1, differences_2 = get_differences(first_list, second_list)

    scores_1 = [get_set_score(unique_set, letters_at_segment)
                for unique_set, letters_at_segment in zip(differences_1, first_list)]
    scores_2 = [get_set_score(unique_set, letters_at_segment)
                for unique_set, letters_at_segment in zip(differences_2, second_list)]

    best_set = pick_best_set(scores_1, scores_2)

    print('best set', best_set)

    # run it again with filtered data
    if best_set == 0:
        second_list = filter_spurious_data(second_list)
        new_differences1, _ = get_differences(first_list, second_list)
        differences = new_differences1
        best_segment = pick_best_segment(scores_1)
    else:
        first_list = filter_spurious_data(first_list)
        _, new_differences2 = get_differences(first_list, second_list)
        differences = new_differences2
        best_segment = pick_best_segment(scores_2)


    differences = set(chain.from_iterable(subset for subset in differences if subset))
    return differences, best_segment




def run(file):
    with open(file) as words_file:
      words = json.load(words_file)


    # left to right
    print('left to right')
    first, second = words
    # first = ngramicise(first)
    # second = ngramicise(second)
    ltr = run_letters(first, second)
    pprint(ltr)

    # right to left
    print()
    print('*' * 10)
    print('right to left')
    first, second = words
    first = [list(reversed(word)) for word in first]
    second = [list(reversed(word)) for word in second]
    # first = ngramicise(first)
    # second = ngramicise(second)
    rtl = run_letters(first, second)
    pprint(rtl)










if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('words')
    args = arg_parser.parse_args()
    run(args.words)