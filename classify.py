__author__ = 'Anton Osten'

from argparse import ArgumentParser
from collections import defaultdict, Counter
import functools
import itertools
import math
import pprint
import re
import statistics

import Levenshtein as lev

import patternize

class Pattern:
    def __init__(self, pattern):

        self.pattern = self._clean_up(pattern)
        self.skeleton = tuple(element for element in self.pattern if element)
        self._regex = None

    @staticmethod
    def _clean_up(pattern):
        # add the beginning of string anchor if the pattern begins with a meaningful character
        # not a None (i.e. optional .*)

        if pattern[0] not in {None, '^'}:
            pattern = ['^'] + pattern

        # remove it if it was for some reason there but the next character is not meaningful
        elif pattern[0] == '^' and pattern[-1] is None:
            pattern = pattern[1:]

        # do the same for the end of string anchor
        if pattern[-1] not in {None, '$'}:
            pattern = pattern + ['$']
        elif pattern[-1] == '$' and pattern[-2] is None:
            pattern = pattern[:-1]

        return tuple(pattern)



    @property
    def regex(self):
        """
        This is a lazy property — the result is only computed when it is first needed,
        and stored for the duration of the object's existence after that"""
        if not self._regex:
            self._regex = str(patternize.make_regex(self.pattern))
        return self._regex

    def __repr__(self):
        return 'Pattern({})'.format(self.regex)

    def __str__(self):
        return self.regex

    def __len__(self):
        return len(self.skeleton)

    def __hash__(self):
        return hash(self.pattern)

    def __eq__(self, other):
        return self.pattern == other.pattern

    def __add__(self, other):
        pattern = self.pattern
        other_pattern = other.pattern

        # if pattern[0] == '^' and other_pattern[0] != '^':
        #     pattern = pattern[1:]
        # elif other_pattern[0] == '^' and pattern[0] != '^':
        #     other_pattern = other_pattern[1:]
        #
        #
        # if pattern[-1] == '$' and other_pattern[-1] != '$':
        #     pattern = pattern[:-1]
        # elif other_pattern[-1] == '$' and pattern[-1] != '$':
        #     other_pattern = other_pattern[:-1]

        combined_pattern = patternize.find_pattern(
            (pattern, other_pattern))[0]
        if combined_pattern:
            return Pattern(combined_pattern)
        else:
            return None



def get_substrings(string):
    """
    This function is not used by the current version of the program and will be removed in the future.
    :param string:
    :return:
    """
    length = len(string)

    if length == 1:
        yield string
        return

    # the 'starting position' loop
    for n in range(length):

        # the 'skip step' loop

        for step in range(1, length):

            # make substrings
            # starting at position 'n' and going up to the length of the string
            for index in range(n, length, step):
                # go from the next character
                index += 1

                # don't emit duplicates
                # (if the step is greater than one
                # and than the length of the would be substring,
                # it's a duplicate
                if step > 1 and index - n < step:
                    continue
                else:

                    chars = string[n:index:step]
                    yield chars

def get_distance_ratios(word, group, pick_last=5):
    for a_word in group[-pick_last:]:
        ratio = lev.ratio(word, a_word)
        yield ratio


def group_by_distance(words, groups=None):
    """
    Group words together based on Levenshtein distance
    :param words:
    :param groups:
    :return:
    """
    if not words:
        # make sure there are no singleton groups at the end
        singleton_groups = [group for group in groups if len(group) == 1]
        for group in singleton_groups:
            word = group[0]
            other_groups = ((g, n) for n, g in enumerate(groups) if word not in g)
            distance_ratio = functools.partial(get_distance_ratios, word)

            try:
                    closest_group, closest_index = max(other_groups,
                                                       key=lambda item: statistics.mean(distance_ratio(item[0])))
            except ValueError:
                continue

            groups[closest_index].append(word)
            groups.remove(group)


        return groups

    if not groups:
        groups = []

    current_group = []
    words_left = []

    for word in words:
        if not current_group:
            current_group.append(word)
        else:
            add_to_this = True
            distance_ratios = get_distance_ratios(word, current_group)
            for ratio in distance_ratios:
                if ratio < 0.39:
                    add_to_this = False
                    break

            if add_to_this:
                current_group.append(word)
            else:
                # check if it fits with any of the existing groups
                words_left.append(word)

    groups.append(current_group)
    return group_by_distance(words_left, groups)


def find_matches(pattern, words):
    positive_results = (word for word in words if re.match(str(pattern), word))
    return positive_results


def find_all_matches(patterns, words):
    pattern_variations = defaultdict(set)

    for pattern in patterns:
        #variations = get_substrings(pattern)
        variation = pattern

        # for variation in variations:
        matches = set(find_matches(variation, words))
        if matches:
            pattern_variations[variation].update(matches)


    return pattern_variations



def collapse_subsets(patterns: dict):

    superpatterns = defaultdict(set)
    # patterns_to_super = defaultdict(Counter)

    keep_going = True
    i = 1

    while keep_going:
        # pattern_scores = dict(get_pattern_scores(patterns))

        sorted_patterns = sorted(patterns.items(), key=lambda item: len(item[1]))

        print('-----round {}-----'.format(i))
        print(len(patterns), 'patterns remaining')
        keep_going = False

        for pattern, matches in sorted_patterns:

            for other_pattern, other_matches in reversed(sorted_patterns):
                if pattern != other_pattern and matches != other_matches:
                    superpattern = pattern + other_pattern
                    # check if they can be combined

                    # EXPERIMENT
                    # if pattern_scores[pattern] > pattern_scores[other_pattern]:
                    #     break
                    #
                    # # experiment
                    if len(matches) / len(other_matches) > 0.7:
                        continue

                    if matches.issubset(other_matches) and superpattern:

                        superpatterns[superpattern].update(other_matches)

                        keep_going = True
                        # merge only a pair of patterns each time
                        break
            else:
                superpatterns[pattern].update(matches)

        patterns, superpatterns = superpatterns, defaultdict(set)
        i += 1

    return patterns

def get_pattern_scores(patterns: dict):

    for pattern, words in patterns.items():
        match_scores = []
        for other_pattern, other_words in patterns.items():
            if pattern != other_pattern:
                intersection = words.intersection(other_words)
                score = len(intersection) / len(words)
                match_scores.append(score)

        # one-element patterns should be discarded (because they aren't really patterns)
        # and overly long patterns should be demoted,
        # which is why we need to take a log of a pattern's length
        score_factor = len(words) * math.log2(len(pattern))

        try:
            pattern_score = score_factor / sum(match_scores)
        except ZeroDivisionError:
            pattern_score = score_factor

        yield pattern, pattern_score

    # return pattern_scores



def make_groups(pattern_groups):
    for n, pattern_group in enumerate(pattern_groups):
        other = itertools.chain.from_iterable(pattern_groups[:n] + pattern_groups[n+1:])
        other = [e for e in other if e not in pattern_group]

        yield pattern_group, other


def remove_group(pattern_words, pattern_groups):
    all_words = itertools.chain.from_iterable(pattern_groups.values())
    other_words = {word for word in all_words if word not in pattern_words}
    return other_words

def get_patterns(words):
    patterns = Counter()

    words_combinations = itertools.combinations(words, 2)

    for word1, word2 in words_combinations:
        pattern, _ = patternize.find_pattern((word1, word2))
        if pattern:
            pattern = Pattern(pattern)
            patterns[pattern] += 1

    return patterns

def get_regex_matches(pattern: Pattern, words):
    for word in words:
        if re.match(pattern.regex, word):
            yield word


def get_top_patterns(words, top_patterns=None):
    # for debug
    print = pprint.pprint
    ###
    if not words:
        return top_patterns

    if top_patterns is None:
        top_patterns = []

    __builtins__.print('{} words'.format(len(words)))

    groups = group_by_distance(words)

    all_patterns = itertools.chain.from_iterable(get_patterns(group) for group in groups)
    patterns = find_all_matches(set(all_patterns), words)

    patterns = collapse_subsets(patterns)
    patterns = {pattern: set(get_regex_matches(pattern, words))
                for pattern in patterns}

    uniqueness_scores = get_pattern_scores(patterns)
    try:
        top_pattern, score = max(uniqueness_scores, key=lambda item: item[1])
        if score > 0:
            top_patterns.append((top_pattern, score))
        else:
            raise ValueError
    except ValueError:
        return top_patterns

    print((top_pattern, score))

    other_words = remove_group(patterns[top_pattern], patterns)
    return get_top_patterns(other_words, top_patterns)

def run(words):
    # words = sorted(words)

    patterns = dict(get_top_patterns(words))
    patterns_and_matches = ((pattern, list(get_regex_matches(pattern, words)))
                            for pattern in patterns)

    sorted_patterns = sorted(patterns_and_matches, key=lambda item: patterns[item[0]],
                             reverse=True)
    return sorted_patterns





if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('words', help='the file with words')
    arg_parser.add_argument('--casefold', action='store_true',
                            help='ignore case in the input data')
    args = arg_parser.parse_args()

    with open(args.words) as file:
        the_words = re.findall("\w+'\w+|\w+", file.read())

    if args.casefold:
        the_words = (w.casefold() for w in the_words)

    the_words = Counter(the_words)
    result = run(the_words)
    print('found {} pattern groups'.format(len(result)))
    pprint.pprint(result)
