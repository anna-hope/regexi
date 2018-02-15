This repository hosts a collection of scripts which attempt to find common patterns in groups of words.

## generalize.py
The script generalize.py takes a JSON-file with an array of two or more lists of words, e.g.

    [["abc", "bac"], ["def", "fed"]] 
    
(you can find real-world examples in the data directory).

The script then compares each group against the other(s), attempting to find the group 
(or multiple groups) of words in which the words are connected by some common pattern
 (e.g. every word in a group contains an 'e').
 
For each group, the script splits every word into its segments and compares each segment of every group against
a corresponding segment of the other groups, finding 'unique' elements of that segment 
(i.e. elements that that segment in that group has that the corresponding segment in other groups do not).* 
The script picks the 'best' group based on how many elements the words of that group share
which are 'unique' to that group. Once the 'best' group is identified, its 'unique' elements are taken to be that group's common pattern.

To ensure that the pattern is more accurate, the scripts performs the above process twice: from left-to-right and from right-to-left.

If the script successfully finds such a pattern, it converts that pattern into a regular expression,
which should match every word from the 'best' group.
So, from the example above, the script might identify the second group as 'special', 
and produce a regular expression like:

    .+e.+
  
This script was written mainly to find morphophonological generalistions in groups of words,
such as patterns of vowel harmony or alterations in suffixes (like 'cat/cat-s' but 'bus/bus-es').
You can try the script with some sample data from the data folder by running:

    ./generalize.py data/english_plurals.json

or

    ./generalize.py data/finnish.json
  
*Despite their name, these elements don't have to be completely unique, 
but they must appear in one group so frequently that their occurrence in the other groups was not statistically significant.

## patternize.py

This script takes a text file with a list of words and tries to find the most explicit regular expression which connects those words (if such a pattern exists). 
For example, if given the words 'string sing bring ring fringe', the script returns the regex

    .*ing.*
    
This script may be used for identifying roots in languages with non-concatenative morphology (e.g. Arabic, Hebrew).
For example, run

    ./patternize.py data/arabic_ktb.txt
   
to test the script as it identifies the pattern ````.*k.*t.*b.*```` for a derivational paradigm of the Arabic root k-t-b.

The script **patternize.py** was created as more of a conceptual exercise and at the moment likely offers less opportunities to be used in practice.
However, this project is still a work in progress, and the script's functionality may be expanded in the future (this also goes for **natclesses.py**).

Additionally, **generalize.py** and **patternize.py** may at some point be integrated together to provide more comprehensive and versatile analyses of morphophonological patterns.

## classify.py

On its surface, this script is somewhat similar to **generalize.py,** in that it tries to find patterns and groups of words
connected by those patterns. However, this script works in a very different way — unlike **generalize.py**,
which must be provided with a JSON file of words that are already pre-packaged into separate groups, 
**classify.py** takes a simple word list and attempts to find groups of words automatically.

The script makes initial groups based on the Levenshtein distance between the words. Once those groups are assembled,
the program goes through each group and combines every possible non-repeated pair of words using **patternize.py**
to create initial ‘candidate patterns.’ The script then puts those candidate patterns together and tries to combine as many
of them with each other as possible to make ‘superpatterns‘ — i.e., if there is a pattern ```^a.*le$``` which connects
5 words, and a pattern ```^.*le$``` which points to 11 words, including the 5 from the previous pattern, ```^a.*le$```
should be discarded. Eventually, every ‘candidate‘ pattern will either be combined with another pattern, or, if it can't
be merged with any other pattern, it will be left as a potential superpattern in itself.

The resulting combined (super)patterns are assigned a score based on the pattern's
length number, the number of words connected by that pattern, and the number of those words which overlap with words
connected by other patterns, like this:

    num(words) * log2(pattern_length) / sum(overlap ratios)

The value of a pattern's length includes begginning of string (^) or end of string ($) anchors, if they are present. Conversely,
it does not count optional characters (```.*```). Thus, if the pattern is ```.*e$```, its length would be 2 (e + $),
and its log2 value would be 1. But if the pattern is ```.*e.*```, its length would be 1 (e), and its log2 value would thus
be 0. Using a logarithm for the pattern's length helps in two ways:

1. It prevents the script from over-promoting patterns which are too long, and are thus unlikely to provide meaningful
generalisations about the data.
2. It gives one-element ‘patterns‘ (like ```.*e.*```) a score of 0, which is good because a `pattern` consisting of
one letter occurring at an arbitrary point in some words is not really a pattern.

After each pattern is assigned such a score, the script picks the pattern with the highest score, adds it to a list
of 'optimal' patterns, takes out the words associated with that pattern, and runs the same process again from the start
(but now without those words and therefore with less patterns). So, if the top pattern from the first run was
‘‘‘^a.*‘‘‘, the algorithm would take out every word that begins with the letter 'a.' Thus, when the script runs the next time,
it will identify a different as the best. Alternatively, if no pattern receives a score above zero (meaning that what's 
left is not likely to contain meaningful patterns), or if no words are left, 
the script stops execution and returns what optimal patterns it had found up to that point. 

The main test case for this script was a list of words derived from several Arabic roots (you can find the words in
data/arabic_roots.txt), with the the script grouping the words by their respective roots. However, the script should 
potentially be able to find patterns in any list of words, as long as the words in that list are indeed connected by
patterns.

Usage example:

    ./classify.py data/arabic_roots.txt

(run ```classify.py -h``` for available options)

It must be noted that **classify.py** is highly experimental. Of the three scripts in this repository, it will produce 
the most unpredictable results, and its output may vary dramatically between runs. While, on some occasions its output
will be exactly correct, on many others its results will be slightly (or very) different from what the user might expect.
However, if your data is not well-structured and you don't know exactly what it you are trying to find in it,
**classify.py** may be the best (and sometimes the only) script in this repository to provide you with useful hints.

If you give **classify.py** some data and it finds no patterns, it could be that the data has no identifiable patterns,
or that the data is too variable and broad (for instance, a word list obtained from a natural corpus, like a novel),
or that the script isn't yet clever enough to find them. Whatever you do, make sure to run the script a few times.


## regexi_test.py

This script tests whether a pattern identified by **patternize.py** does in fact work on the data it was given. It does so by running **patternize.py** and then testing the resulting regex against the list of words. It may be used like this:
    
    ./regexi_test.py <data>

This script currently doesn't test the output of **generalize.py.** This should change in the future (I hope).
Also, this script doesn't test the results of **classify.py** because I don't currently know what a good test algorithm
for that script would be.

## Requirements

All scripts in this package were written for Python 3.4+. With some work, they will probably work on Python3.3 
(such as installing a backported version of statistics and getting around Python3.3's lack of a log2 function), but this has not been tested and is not officially supported.

**classify.py** requires python-levenshtein.
