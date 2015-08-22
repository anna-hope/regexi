__author__ = 'anton'

from argparse import ArgumentParser
from collections import Counter, namedtuple
from functools import reduce, partial
from itertools import zip_longest, chain
import json
import math
from operator import add
from pprint import pprint, pformat
import statistics

GroupRule = namedtuple('GroupRule', ('rule', 'group', 'segment'))

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



def get_set_ratio(unique_set, top=3, verbose=False):
    all_set_frequencies = reduce(add, unique_set)

    if verbose:
        pprint(all_set_frequencies.most_common())

    # divide the frequency of top n elements by the frequency of the top n * 2 elements
    # (sets of elements connected by a rule are usually heavily skewed towards the elements
    # which form part of the rule)
    most_top_frequencies = sum(item[1] for item in all_set_frequencies.most_common(top))
    top_freqs = sum(item[1] for item in all_set_frequencies.most_common(top * 2))

    top_vs_all = most_top_frequencies / top_freqs
    return top_vs_all

def pick_best_set(unique_1, unique_2):
    """
    get the most 'useful' set based on the set ratio
    :param unique_1:
    :param unique_2:
    :return:
    """

    ratio_1, ratio_2 = get_set_ratio(unique_1), get_set_ratio(unique_2)


    best_set = max(ratio_1, ratio_2)
    # print('----RATIOS----', ratio_1, ratio_2)

    if best_set is ratio_1:
        return 0
    else:
        return 1

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
    avg_freq = statistics.mean(item[1] for item in total_counted.most_common(5))

    for unique_segment, whole_segment in zip(unique_set, segment_list):
        if not unique_segment:
            yield 0
            continue

        # to each element's count at this segment, we add a 'weight'
        # which is the difference between the element's total frequency
        # and the average frequency of top 5 elements
        # in the entire set of unique elements
        weighted_segment_freqs = (count + (total_counted[letter] - avg_freq)
                                  for letter, count in unique_segment.items())
        total_segment_freqs = sum(weighted_segment_freqs)
        whole_segment_freqs = sum(whole_segment.values())
        unique_length = len(unique_segment)

        score = total_segment_freqs / whole_segment_freqs / unique_length
        yield score


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
        # pprint(unique_segment_lists, indent=4)
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

    return differences, best_set_index, best_segment


def run_words(words, ngrams=0, rtl=False, verbose=False):
    """
    Returns the optimal generalisation,
    the list it came from and the segment in that list which gave it
    :param words:
    :param ngrams:
    :param rtl:
    :param verbose:
    :return best_rule, best_set, best_segment:
    """

    first, second = words

    if rtl:
        first = (tuple(reversed(word)) for word in first)
        second = (tuple(reversed(word)) for word in second)

    if ngrams > 1:
        first = ngramicise(first, ngrams)
        second = ngramicise(second, ngrams)

    best_segment_letters, best_set, best_segment = run_letters(first, second, verbose=verbose)
    best_segment_letters = tuple(best_segment_letters)

    if verbose:
        print('most informative segment:', best_segment)

    if ngrams > 1:
        if rtl:
            best_segment_letters = (reversed(element) for element in best_segment_letters)
        best_segment_letters = tuple(''.join(ngram) for ngram in best_segment_letters)

    if verbose:
        print(best_segment_letters)

    return best_segment_letters, best_set, best_segment


def run_multi_ngrams(words, ngrams, verbose=False):
    for n in range(1, ngrams+1):
        best_segment_ltr = run_words(words, n, verbose=verbose)
        best_segment_rtl = run_words(words, n, rtl=True, verbose=verbose)

        yield set(best_segment_ltr + best_segment_rtl)

def run_two(words, ngrams, with_ngrams=False, verbose=False):

    if with_ngrams:
        # if verbose:
        #     print('running with up to {}-grams'.format(ngrams))
        #
        # result = run_multi_ngrams(words, ngrams)
        # pprint(list(result))

         return NotImplemented


    else:

        if verbose:
            print('running left-to-right')

        result_ltr = run_words(words, ngrams, verbose=verbose)

        if verbose:
            print('running right-to-left')

        result_rtl = run_words(words, ngrams, rtl=True, verbose=verbose)


        rules_ltr = GroupRule(*result_ltr)
        rules_rtl = GroupRule(*result_rtl)

        return rules_ltr, rules_rtl



def run_many(words, ngrams, with_ngrams=False, verbose=False):

    results_ltr, results_rtl = [], []

    for n, group in enumerate(words):
        other_group = tuple(chain.from_iterable(g for g in words if g != group))
        word_groups = (tuple(group), other_group)

        if verbose:
            print('*' * 5)
            print('run', n + 1)
            pprint(word_groups)

        result_ltr = run_words(word_groups, ngrams=ngrams, verbose=verbose)
        result_rtl = run_words(word_groups, ngrams=ngrams, rtl=True, verbose=False)

        # we need this to pick the 'special sets' and the 'everything else' set
        best_words_ltr = word_groups[result_ltr[1]]
        best_words_rtl = word_groups[result_rtl[1]]

        results_ltr.append((result_ltr, best_words_ltr))
        results_rtl.append((result_rtl, best_words_rtl))

    return results_ltr, results_rtl

def pick_best_word_group(special_group, all_words):

    for n, word_group in enumerate(all_words):
        word_set = set(word_group)

        if word_set.intersection(special_group):
            return n


def process_results_many(results, words):
    best_groups = {n: 0 for n in range(len(words))}

    def get_rules():
        for result, best_word_set in results:
            best_rule, best_set, best_segment = result
            best_word_group = pick_best_word_group(best_word_set, words)

            # add the best group to the counter
            best_groups[best_word_group] += 1
            rule = GroupRule(best_rule, best_word_group, best_segment)

            yield rule


    rules = get_rules()
    else_group = min(best_groups, key=lambda item: best_groups[item])

    return rules, else_group

def make_regex_rule(rule_ltr, rule_rtl, min_length, max_length):
    regex = []
    combined_rule = set(rule_ltr.rule + rule_rtl.rule)

    if len(combined_rule) > 1:
        regex.append('[{}]'.format(''.join(combined_rule)))
    else:
        regex.append(combined_rule.pop())

    # check if it occurs at beginnings of words
    if rule_ltr.segment == 0 and min_length <= rule_rtl.segment + 1 <= max_length:
        regex.append('^.+')

    # check if it occurs at ends of words
    elif rule_rtl.segment == 0 and min_length <= rule_ltr.segment + 1 <= max_length:
        regex = ['.+'] + regex + ['$']

    # it occurs in the middle
    else:
        regex = ['.*'] + regex + ['.*']

    regex_string = ''.join(regex)

    return regex_string

def make_regex_rules(processed_ltr, procesed_rtl, words):
    rules_ltr, else_ltr = processed_ltr
    rules_rtl, else_rtl = procesed_rtl

    assert else_ltr == else_rtl, ("'elsewhere' groups don't match: LTR is {} but RTL is {}"
                                  .format(else_ltr, else_rtl))

    regex_rules = (make_regex_rule_p(rule_ltr, rule_rtl) for rule_ltr, rule_rtl
                    in zip(rules_ltr, rules_rtl))
    return regex_rules




def run(file, ngrams, with_ngrams=False, verbose=False):
    with open(file) as words_file:
        words = json.load(words_file)

    # get the length ranges for words
    # this is needed to know if the rules identified above
    # occur at beginnings or ends of words
    word_lengths = set(len(word) for word in chain.from_iterable(words))
    min_length, max_length = min(word_lengths), max(word_lengths)

    global make_regex_rule_p # I know
    make_regex_rule_p = partial(make_regex_rule,
                                min_length=min_length, max_length=max_length)

    if len(words) == 2:
        result = run_two(words, ngrams, with_ngrams, verbose)

        regex_rules = make_regex_rule_p(*result)

    elif len(words) > 2:

        results_ltr, results_rtl = run_many(words, ngrams, with_ngrams, verbose=verbose)
        rules_ltr = process_results_many(results_ltr, words)
        rules_rtl = process_results_many(results_rtl, words)

        regex_rules = tuple(make_regex_rules(rules_ltr, rules_rtl, words))
        else_group = rules_ltr[1]
        print("the 'else' group:", else_group)


    else:
        raise ValueError('the file must have 2 or more lists of words')

    print('regex:', regex_rules)



if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('words')
    arg_parser.add_argument('-ng', '--ngrams', type=int, default=1, required=False)
    arg_parser.add_argument('--with-ngrams', action='store_true',
                            help='')
    arg_parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    args = arg_parser.parse_args()
    run(args.words, args.ngrams, args.with_ngrams, verbose=args.verbose)