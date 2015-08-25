This repository hosts a pair of scripts which attempt to find common patterns in groups of words.

##natclasses.py
The script natclasses.py takes a JSON-file with an array of two or more lists of words, e.g.

    [["abc", "bac"], ["def", "fed"]] 
(you can find real-world examples in the data directory).

The script then compares each group against the other(s), attempting to find the group 
(or multiple groups) of words in which the words are connected by some common pattern
 (e.g. every word in a group contains an 'e').
 
For each group, the script splits every word into its segments and compares each segment of every group against a corresponding segment of the other groups, finding 'unique' elements of that segment (i.e. elements that that segment in that group has that the corresponding segment in other groups do not).* The script picks the 'best' group based on how many elements the words of that group share
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

    ./natclasses.py data/english_plurals.json

or

    ./natclasses.py data/finnish.json
  
*Despite their name, these elements don't have to be completely unique, but they must appear in one group so frequently that their occurrence in the other groups was not statistically significant.

##patternize.py

This script takes a text file with a list of words and tries to find the most explicit regular expression which connects those words (if such a pattern exists). 
For example, if given the words 'string sing bring ring fringe', the script returns the regex

    .*ing.*
    
This script may be used for identifying roots in languages with non-concatenative morphology (e.g. Arabic, Hebrew).
For example, run

    ./patternize.py data/arabic_ktb.txt
   
to test the script as it identifies the pattern '.*k.*t.*b.*' for a derivational paradigm of the Arabic root k-t-b.

The script **patternize.py** was created as more of a conceptual exercise and at the moment likely offers less opportunities to be used in practice.
However, this project is still a work in progress, and the script's functionality may be expanded in the future (this also goes for **natclesses.py**).

Additionally, **natclasses.py** and **patternize.py** may at some point be integrated together to provide more comprehensive and versatile analyses of morphophonological patterns.

##regexi_test.py

This script tests whether a pattern identified by **patternize.py** does in fact work on the data it was given. It does so by running **patternize.py** and then testing the resulting regex against the list of words. It may be used like this:
    
    ./regexi_test.py <data>

This script currently doesn't test the output of **natclasses.py.** This should change in the future (I hope).

##Requirements

All scripts in this package were written for Python 3.4+. With some work, they will probably work on Python3.3 
(such as installing a backported version of statistics and getting around Python3.3's lack of a log2 function), but this has not been tested and is not officially supported.