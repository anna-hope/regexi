__author__ = 'anton'

from argparse import ArgumentParser
from collections import Counter
from functools import reduce
from itertools import zip_longest, chain
import json
import math
from operator import add
from pprint import pprint, pformat

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

def get_letter_differences(first_set: Counter, second_set: Counter,
                           min_count=2, threshold=0.15):
    differences = Counter()

    for letter, count in first_set.items():
        if letter is None:
            continue

        if letter not in second_set:
            differences[letter] = count
        elif count > min_count:
            # get the frequency threshold of the other letter (rounding up)
            other_freq_threshold = math.ceil(count * threshold)
            # add the letter if its frequency in the other set is smaller than the threshold
            if second_set[letter] <= other_freq_threshold:
                differences[letter] = count



    return differences

def get_differences(first_set, second_set):

    unique_set1 = []
    unique_set2 = []

    for first_letters, second_letters in zip_longest(first_set, second_set, fillvalue=Counter()):
        unique_1 = get_letter_differences(first_letters, second_letters)
        unique_2 = get_letter_differences(second_letters, first_letters)

        unique_set1.append(unique_1)
        unique_set2.append(unique_2)

    return unique_set1, unique_set2


def get_segment_scores(unique_set: list, segment_list: list):
    """
    get the score of each set of unique letters for each segment of the words.
    this score is calculated based on how many of all letters at that segment
    are the letters unique for the set of given words,
    i.e. how well can a set of unique letters account for the whole segment,
    while staying short.
    :param unique_letters:
    :param letters_at_segment:
    :return:
    """

    total_counted = reduce(add, unique_set)

    for unique_segment, whole_segment in zip(unique_set, segment_list):
        if not unique_segment:
            yield 0
            continue

        weighted_segment_freqs = (count + total_counted[letter]
                                  for letter, count in unique_segment.items())
        total_segment_freqs = sum(weighted_segment_freqs)
        whole_segment_freqs = sum(whole_segment.values())
        unique_length = len(unique_segment)

        score = total_segment_freqs / whole_segment_freqs / unique_length
        yield score



def get_set_ratio(unique_set, top=3, verbose=True):
    all_set_frequencies = reduce(add, unique_set)

    if verbose:
        pprint(all_set_frequencies.most_common())

    total_frequencies = sum(all_set_frequencies.values())
    top_frequencies = sum(item[1] for item in all_set_frequencies.most_common(top))

    top_vs_all = top_frequencies / total_frequencies
    return top_vs_all

def pick_best_set(unique_1, unique_2):
    """
    get the most 'useful' set based on the set ratio
    :param unique_1:
    :param unique_2:
    :return:
    """

    ratio_1, ratio_2 = get_set_ratio(unique_1), get_set_ratio(unique_2, verbose=False)


    best_set = max(ratio_1, ratio_2)

    if best_set is ratio_1:
        return 0
    else:
        return 1

def pick_best_segment(scores):
    maximum = max(enumerate(scores), key=lambda x: x[1])
    best_segment = maximum[0]
    return best_segment



def filter_spurious_data(unique_set):
    threshold = sum(sum(segment_point.values()) for segment_point in unique_set) * 0.01

    for segment_point in unique_set:
        good_segments = {}
        for segment, count in segment_point.items():
            if count >= threshold:
                good_segments[segment] = count
        yield good_segments



def run_letters(first, second, verbose=False, filter_spurious=True):
    segment_lists = list(find_letters(first)), list(find_letters(second))

    unique_segment_lists = get_differences(*segment_lists)

    if verbose:
        print('***')
        pprint(unique_segment_lists, indent=4)
        print('---')

    best_set_index = pick_best_set(*unique_segment_lists)
    best_set = unique_segment_lists[best_set_index]

    scores = get_segment_scores(best_set, segment_lists[best_set_index])
    best_segment = pick_best_segment(scores)

    if verbose:
        print('best set', best_set_index)


    if filter_spurious:
        best_set = tuple(filter_spurious_data(best_set))

    differences = best_set[best_segment]

    return differences, best_segment


def run_words(words, ngrams=0, rtl=False, verbose=False):
    first, second = words

    if rtl:
        first = (tuple(reversed(word)) for word in first)
        second = (tuple(reversed(word)) for word in second)

    if ngrams > 1:
        first = ngramicise(first, ngrams)
        second = ngramicise(second, ngrams)

    best_segment_letters, n = run_letters(first, second, verbose=verbose)
    best_segment_letters = tuple(best_segment_letters)

    if verbose:
        print('most informative segment:', n)

    if ngrams > 1:
        if rtl:
            best_segment_letters = (reversed(element) for element in best_segment_letters)
        best_segment_letters = tuple(''.join(ngram) for ngram in best_segment_letters)

    if verbose:
        print(best_segment_letters)

    return best_segment_letters


def run_multi_ngrams(words, ngrams, verbose=False):
    for n in range(1, ngrams+1):
        best_segment_ltr = run_words(words, n, verbose=verbose)
        best_segment_rtl = run_words(words, n, rtl=True, verbose=verbose)

        yield set(best_segment_ltr + best_segment_rtl)

def run_two(words, ngrams, with_ngrams=False, verbose=False):

    if with_ngrams:
        if verbose:
            print('running with up to {}-grams'.format(ngrams))

        result = run_multi_ngrams(words, ngrams)
        pprint(list(result))


    else:

        if verbose:
            print('running left-to-right')
            
        best_segment_ltr = run_words(words, ngrams, verbose=verbose)

        if verbose:
            print('running right-to-left')

        best_segment_rtl = run_words(words, ngrams, rtl=True, verbose=verbose)

        best_elements = set(best_segment_ltr + best_segment_rtl)

        return best_elements

def run_many(words, verbose=False):

    for n, group in enumerate(words):
        other_group = tuple(chain.from_iterable(g for g in words if g != group))
        word_groups = (group, other_group)
        if verbose:
            print('*' * 5)
            print('run', n + 1)
            pprint(word_groups)
        this_result_ltr = run_words(word_groups, verbose=verbose)
        this_result_rtl = run_words(word_groups, rtl=True, verbose=False)

        yield this_result_ltr, this_result_rtl




def run(file, ngrams, with_ngrams=False, verbose=False):
    with open(file) as words_file:
        words = json.load(words_file)

    if len(words) == 2:
        result = run_two(words, ngrams, with_ngrams, verbose)
    elif len(words) > 2:

        # TODO integrate with run_two
        result = tuple(run_many(words, verbose=verbose))
    else:
        raise ValueError('the file must have 2 or more lists of words')

    pprint(result)



if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('words')
    arg_parser.add_argument('-ng', '--ngrams', type=int, default=1, required=False)
    arg_parser.add_argument('--with-ngrams', action='store_true',
                            help='')
    arg_parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    args = arg_parser.parse_args()
    run(args.words, args.ngrams, args.with_ngrams, verbose=args.verbose)