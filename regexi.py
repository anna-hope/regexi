__author__ = 'anton'

from argparse import ArgumentParser
from collections import defaultdict
from enum import Enum
from functools import partial
from pprint import pprint, pformat
import re

from greenery import lego


class Element:

    def __init__(self, value, frequency=1):
        self.value = value
        self.frequency = frequency

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
    def __init__(self, elements):
        temp_elements = []
        for element in elements:
            if isinstance(element, AmbiguousElement):
                temp_elements += list(element.value)
            elif isinstance(element, (list, tuple)):
                temp_elements += list(element)
            else:
                temp_elements.append(element)

        frequency = max(e.frequency for e in temp_elements)

        super().__init__(frozenset(temp_elements), frequency=frequency)

    # def __repr__(self):
    #     return '[{}]'.format('/'.join(sorted(self.value)))

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

class Mode(Enum):
    all = 'all'
    compare_two = 'vs'




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

def normalise_index(index_x, index_y, length_x, length_y):
    normalised = abs(index_x / length_x - index_y / length_y)
    return normalised


def find_closest_indexes(indexes1, indexes2, length1, length2):
    # take the indexes from the word which has less of them
    # pick the most closely located indexes between the two words
    # normalising the indexes according to the length of the word

    close_indexes_1 = []
    close_indexes_2 = []

    if len(indexes1) == len(indexes2):
        close_indexes_1, close_indexes_2 = indexes1, indexes2

    elif len(indexes1) < len(indexes2):
        closest_with_lengths = partial(normalise_index, length_x=length2, length_y=length1)

        for index1, index2 in zip(indexes1, indexes2):

            # index1 is from the shorter string
            # so we multiply them by the offset
            # (see below for explanation)

            closest = partial(closest_with_lengths, index_y=index1)
            closest_other = min(indexes2, key=closest)
            close_indexes_1.append(index1)
            close_indexes_2.append(closest_other)

    else:
        closest_with_lengths = partial(normalise_index, length_x=length1, length_y=length2)

        for index1, index2 in zip(indexes1, indexes2):

            # n is the index from the shorter string
            # so that's the index we multiply by the offset
            # (ibid.)

            closest = partial(closest_with_lengths, index_y=index2)
            closest_other = min(indexes1, key=closest)
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
                pattern[index].frequency += letter.frequency
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

    if verbose:
        print('*' * 10)
        print('words:', word1, word2)

    try:
        if len(word1) > len(word2):
            return find_pattern_pair(word2, word1)

        indexes1, indexes2 = find_intersection_indexes(word1, word2)

    except ValueError:
        if verbose:
            print('no intersection found')
        return None
    except TypeError:
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
                element1.frequency += element2.frequency
                common_pattern.append(element1)
            else:

                # the order cannot be established unambiguously
                # falling back to the 'ambiguous' pattern
                # where the same position may be occupied by 2+ characters
                element1.frequency += 1
                element2.frequency += 1
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


def find_pattern(words, allow_unmatched=False, verbose=False):

    unmatched_words = []
    combined_pattern = None
    rest = words

    while rest:
        one, two, *rest = words

        if verbose:
            print('remaining words:')
            pprint(rest)

        new_pattern = find_pattern_pair(one, two, verbose=verbose)

        if new_pattern:
            # only assign the pattern if one could be found
            combined_pattern = new_pattern
        else:
            if allow_unmatched:
                unmatched_words.append(two)
            else:
                return None, rest

        words = [combined_pattern] + rest

    return combined_pattern, unmatched_words

def check_valid(pattern, words, verbose=False):
    """
    A pattern is valid if that pattern and that word have an intersection.
    This function tests whether an intersection may be found between the given pattern
    and every given word.
    :param pattern:
    :param words:
    :param verbose:
    :return:
    """

    for word in words:
        if not find_intersection(pattern, word):
            if verbose:
                print('failed to find an intersection for {} and {}'.format(pattern, word))
            return False
    else:
        return True

def combine_patterns(patterns):
    shortest, *other = sorted(patterns)
    # TODO: finish


def find_pattern_combination(words, verbose=False):
    initial_patterns = []
    unmatched_words = words

    while len(unmatched_words) >= 2:
        initial_pattern, unmatched_words = find_pattern(unmatched_words,
                                                        allow_unmatched=True,
                                                        verbose=verbose)
        if initial_pattern:
            initial_patterns.append(initial_pattern)
        else:
            # no new pattern could be find
            break

    if unmatched_words:
        # if there are still unmatched words, add them as 'patterns'
        initial_patterns += unmatched_words

    # TODO: finish






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

def run_find_all(words, verbose=False):
    pattern, unmatched_words = find_pattern(words, verbose=verbose)
    regex = make_regex(pattern)
    if not pattern:
        return ''
    else:
        return str(regex)

def run_compare_two(words1, words2, verbose=False):
    # TODO: words that can be related at all always will be, no matter the existing pattern
    # TODO: you have to work out a way to combine patterns which are not related on the surface
    ...


def run(file, mode, verbose=False):
    with open(file) as word_list_file:
        words = re.findall('\w+', word_list_file.read(), re.MULTILINE)

    if not words:
        raise ValueError('the word list is empty')

    words = [[StringElement(char) for char in word] for word in words]

    mode = Mode(mode)
    if mode == Mode.all:
        result = run_find_all(words, verbose=verbose)
        print(result)
    elif mode == Mode.compare_two:
        ...
        result = None
    else:
        raise ValueError('unsupported mode')

    return result




if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('file', help='file with a list of words')
    arg_parser.add_argument('-t', '--tolerance', type=int, choices=range(101),
                            default=70)
    arg_parser.add_argument('--mode', choices=('all', 'vs'), default='all')
    args = arg_parser.parse_args()
    run(args.file, args.tolerance)
