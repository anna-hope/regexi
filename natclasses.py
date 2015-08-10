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

    for letters1, letters2 in zip_longest(first_set, second_set, fillvalue=()):
        first_letters, second_letters = set(letters1), set(letters2)

        unique_1 = first_letters.difference(second_letters)
        unique_2 = second_letters.difference(first_letters)

        # get the counts of these unique letters
        counted_unique_1 = {letter: letters1[letter] for letter in unique_1
                            if letter}
        counted_unique_2 = {letter: letters2[letter] for letter in unique_2
                            if letter}


        unique_set1.append(counted_unique_1)
        unique_set2.append(counted_unique_2)

    return unique_set1, unique_set2


def pick_best_segment(scores):
    maximum = max(enumerate(scores), key=lambda x: x[1])
    best_segment = maximum[0]
    return best_segment

def get_set_score(letter_set: Counter, letters_at_segment: Counter):
    """
    get the score of each set of unique letters for each segment of the words.
    this score is calculated based on how many of all letters at that segment
    are the letters unique for the set of given words,
    i.e. how well can a set of unique letters account for the whole segment,
    while staying short.
    :param letter_set:
    :param letters_at_segment:
    :return:
    """
    if not letter_set:
        return 0

    frequency_letters_set = sum(letter_set.values())
    total_frequency_segment = sum(letters_at_segment.values())

    unique_set_length = len(letter_set)
    coverage = frequency_letters_set / total_frequency_segment
    score = coverage / unique_set_length

    return score

def pick_best_set(scores1, scores2):
    """
    get the most 'useful' set based on which set has the highest scoring segment
    :param scores1:
    :param scores2:
    :return:
    """
    best_set = max(scores1, scores2, key=lambda segment: max(segment))
    if best_set is scores1:
        return 0
    else:
        return 1


def filter_spurious_data(unique_set):
    for segment_point in unique_set:
        # threshold = min(5, sum(segment_point.values()) * 0.001)
        threshold = 5
        good_segments = {}
        for segment, count in segment_point.items():
            if count > threshold:
                good_segments[segment] = count
        yield good_segments



def run_letters(first, second, verbose=False):
    first_list, second_list = list(find_letters(first)), list(find_letters(second))
    differences_1, differences_2 = get_differences(first_list, second_list)

    scores_1 = [get_set_score(unique_set, letters_at_segment)
                for unique_set, letters_at_segment in zip(differences_1, first_list)]
    scores_2 = [get_set_score(unique_set, letters_at_segment)
                for unique_set, letters_at_segment in zip(differences_2, second_list)]

    best_set = pick_best_set(scores_1, scores_2)

    if verbose:
        print('best set', best_set)

    if best_set == 0:
        differences = differences_1
        best_segment = pick_best_segment(scores_1)
    else:
        differences = differences_2
        best_segment = pick_best_segment(scores_2)

    differences = set(chain.from_iterable(subset for subset in differences if subset))
    # differences = differences[best_segment]
    return differences, best_segment




def run(file, ngrams):
    with open(file) as words_file:
      words = json.load(words_file)


    # left to right
    print('left to right')
    first, second = words

    if ngrams > 1:
        first = ngramicise(first, ngrams)
        second = ngramicise(second, ngrams)
    ltr = run_letters(first, second)
    pprint(ltr)

    # right to left
    print()
    print('*' * 10)
    print('right to left')
    first, second = words
    first = [list(reversed(word)) for word in first]
    second = [list(reversed(word)) for word in second]

    if ngrams > 1:
        first = ngramicise(first, ngrams)
        second = ngramicise(second, ngrams)
    rtl = run_letters(first, second)
    pprint(rtl)










if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('words')
    arg_parser.add_argument('--ngrams', type=int, default=1)
    args = arg_parser.parse_args()
    run(args.words, args.ngrams)