__author__ = 'anton'

from argparse import ArgumentParser
from collections import defaultdict
from functools import partial
from itertools import combinations, chain, zip_longest
from pprint import pprint, pformat
import re

from greenery import lego


class Element:

    def __init__(self, value):
        self.value = value
        self.frequency = 1

    def __repr__(self):
        return repr(self.value)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if other:
            return self.value == other.value
        else:
            # the other must be None
            return False

    def __len__(self):
        return len(self.value)

    def __contains__(self, item):
        return item in self.value

    def __iter__(self):
        return iter(self.value)

    def intersection(self, other) -> set:
        return self.value.intersection(other.value)

class StringElement(Element, str):
    pass

class AmbiguousElement(Element):
    def __init__(self, chars):
        temp_chars = []
        for char in chars:
            if isinstance(char, AmbiguousElement):
                temp_chars += list(char.chars)
            elif isinstance(char, (list, tuple)):
                temp_chars += list(char)
            else:
                temp_chars.append(char)

        super().__init__(frozenset(temp_chars))

    def __repr__(self):
        return '[{}]'.format('/'.join(sorted(self.value)))

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        for character in self:
            try:
                if character in other:
                    return True
            except TypeError:
                return False
        else:
            return False

    def __add__(self, other):
        new_chars = list(self.chars) + list(other.chars)
        self.chars = frozenset(new_chars)





def is_none_tuple(element) -> bool:
    try:
        return None in element
    except TypeError:
        # not a tuple
        return False


def find_intersection(word1, word2):
    intersection = set()

    word1 = [c for c in word1 if c]

    for element in word1:

        for other_element in word2:
            if (isinstance(element, AmbiguousElement)
                and isinstance(other_element, AmbiguousElement)):
                if element == other_element:
                    ambiguous_intersection = element.intersection(other_element)

                    # add the intersection of the ambiguous element
                    # i.e. for [an] and [mn] it would be 'n'

                    for e in ambiguous_intersection:

                        intersection.add(e)

            elif isinstance(element, AmbiguousElement):
                if other_element in element:
                    intersection.add(other_element)
            elif isinstance(other_element, AmbiguousElement):
                if element in other_element:
                    intersection.add(element)
            else:
                if element == other_element:
                    intersection.add(element)

    return intersection


def get_common_letters(word, intersection):
    intersection_word = defaultdict(list)

    for n, element in enumerate(word):
        if isinstance(element, AmbiguousElement):
            for character in element:
                if character in intersection:
                    intersection_word[character].append(n)
        else:
            if element in intersection:
                intersection_word[element].append(n)

    return intersection_word


def find_closest_indexes(indexes1, indexes2, length1, length2):
    # take the indexes from the word which has less of them
    # pick the most closely located indexes between the two words

    close_indexes_1 = []
    close_indexes_2 = []

    if len(indexes1) == len(indexes2):
        close_indexes_1, close_indexes_2 = indexes1, indexes2

    elif len(indexes1) < len(indexes2):

        for index1, index2 in zip(indexes1, indexes2):

            # index1 is from the shorter string
            # so we multiply them by the offset
            # (see below for explanation)

            closest_other = min(indexes2,
                                key=lambda n: abs(n / length2 - index1 / length1))
            close_indexes_1.append(index1)
            close_indexes_2.append(closest_other)

    else:

        for index1, index2 in zip(indexes1, indexes2):

            # n is the index from the shorter string
            # so that's the index we multiply by the offset
            # (ibid.)

            closest_other = min(indexes1,
                                key=lambda n: abs(n / length1 - index2 / length2))
            close_indexes_1.append(closest_other)
            close_indexes_2.append(index2)


    return close_indexes_1, close_indexes_2


def find_intersection_indexes(word1, word2):
    intersection = find_intersection(word1, word2)

    if not intersection:
        raise ValueError

    intersection_1, intersection_2 = (get_common_letters(word1, intersection),
                                      get_common_letters(word2, intersection))

    adjusted_intersection_1 = {}
    adjusted_intersection_2 = {}

    find_closest = partial(find_closest_indexes,
                           length1=len(word1), length2=len(word2))

    for letter in intersection:
        indexes1 = intersection_1[letter]
        indexes2 = intersection_2[letter]
        closest1, closest2 = find_closest(indexes1, indexes2)

        adjusted_intersection_1[letter] = closest1
        adjusted_intersection_2[letter] = closest2

    return adjusted_intersection_1, adjusted_intersection_2


def make_pattern_word(indexes_word, word, verbose=False):
    pattern_length = len(word)
    pattern = [None for _ in range(pattern_length)]

    for letter, indexes in indexes_word.items():
        for index in indexes:
            if pattern[index] is None:
                pattern[index] = letter
            elif pattern[index] == letter:
                # this letter occurs twice and has already been assigned
                pass
            else:
                # a letter has already been assigned to that index
                pattern[index] = AmbiguousElement((pattern[index], letter))

    # collapse the None's (put consecutive None's into tuples)
    # we need this to build the general pattern later
    # where one word could have symbols in a place where another word does not
    # e.g. 'tr' in 'string' vs. 'sing' should yield ['s', (None, None), 'i', 'n', 'g']

    optimised_pattern = []
    nones = []
    for n, element in enumerate(pattern):

        if element:
            if nones:
                # append the list of None's if there is anything in it
                optimised_pattern.append(tuple(nones))
                nones.clear()

            optimised_pattern.append(element)
        else:
            nones.append(None)
            if n + 1 == len(pattern):
                # this pattern ends in None
                optimised_pattern.append(tuple(nones))

    if verbose:
        print(word, pformat(optimised_pattern))

    return optimised_pattern


def find_pattern_pair(word1, word2, verbose=False):
    # word1 should be the shorter word (if length is unequal)

    if verbose:
        print('*' * 10)
        print('words:', word1, word2)

    try:
        if len(word1) > len(word2):
            return find_pattern_pair(word2, word1)

        indexes1, indexes2 = find_intersection_indexes(word1, word2)

    except (TypeError, ValueError):
        return None

    pattern1, pattern2 = (make_pattern_word(indexes1, word1, verbose=verbose),
                          make_pattern_word(indexes2, word2, verbose=verbose))

    shorter_pattern, longer_pattern = sorted((pattern1, pattern2), key=len)

    # iterate over both patterns
    # we need to keep the indexes separate because the patterns can have unequal lengths
    # and have None tuples at arbitrary places where the other pattern has a symbol
    # so we advance the indexes separately according to each pattern

    common_pattern = []

    i1, i2 = 0, 0
    while i1 < len(longer_pattern):
        element1 = longer_pattern[i1]

        try:
            element2 = shorter_pattern[i2]
        except IndexError:

            # this means the shorter pattern has been exhausted

            # we need to fill the rest of the pattern with Nones
            # caveat: we need to keep the last character of the shorter pattern last
            # so that strings which match on the last character produce a more accurate pattern
            # (e.g. 'olga' and 'hanna')
            # for this, we need to split the existing pattern
            # and insert the tuple of Nones before the last character

            # *start, end = common_pattern
            # num_remaining_elements = len(longer_pattern) - i1
            # end_nones = tuple(None for _ in range(num_remaining_elements))
            # common_pattern = start + [end_nones, end]

            # iteration is over
            break

        # both elements are None tuples
        if is_none_tuple(element1) and is_none_tuple(element2):
            bigger_none = max(element1, element2, key=len)
            common_pattern.append(bigger_none)
            i1 += 1
            i2 += 1
        elif is_none_tuple(element1):
            common_pattern.append(element1)
            i1 += 1
        elif is_none_tuple(element2):
            common_pattern.append(element2)
            i2 += 1
        else:
            # neither of them are None tuples
            if element1 == element2:
                common_pattern.append(element1)
            else:

                # the order cannot be established unambiguously
                # falling back to the 'ambiguous' pattern
                # where the same position may be occupied by 2+ characters

                common_pattern.append(AmbiguousElement((element1, element2)))

            i1 += 1
            i2 += 1

    unpacked_pattern = []
    for element in common_pattern:
        if is_none_tuple(element):
            unpacked_pattern += list(element)
        else:
            unpacked_pattern.append(element)

    if verbose:
        print('combined pattern', unpacked_pattern)

    return unpacked_pattern


def find_pattern(words, verbose=False, test_every_step=False):

    while len(words) > 2:
        one, two, *rest = words
        combined_pattern = find_pattern_pair(one, two, verbose=verbose)
        words = [combined_pattern] + rest
        if verbose:
            print('remaining words:')
            pprint(words)

    combined_pattern = find_pattern_pair(words[0], words[1], verbose=verbose)

    return combined_pattern


def make_regex(pattern):
    if pattern is None:
        return None

    expression = ''
    for element in pattern:
        if element:
            if len(element) > 1:
                expression += '[{}]'.format(''.join(element))
            else:
                expression += element
        else:
            # hack with completely optional None characters
            # (specifying length may yield an incorrect pattern)
            expression += '.*'

    # optimise the expression with lego

    expression = lego.parse(expression)

    return expression


def run(file, tolerance, verbose=False):
    with open(file) as word_list_file:
        words = re.findall('\w+', word_list_file.read(), re.MULTILINE)

    if not words:
        raise ValueError('the word list is empty')

    words = [[StringElement(char) for char in word] for word in words]

    pattern = find_pattern(words, verbose=verbose)

    regex = make_regex(pattern)
    if not pattern:
        if tolerance == 0:
            return '.+'
        else:
            return None
    else:
        return str(regex)


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('file', help='file with a list of words')
    arg_parser.add_argument('-t', '--tolerance', type=int, choices=range(101),
                            default=70)
    args = arg_parser.parse_args()
    run(args.file, args.tolerance)
