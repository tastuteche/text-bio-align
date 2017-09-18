"""
Implementation of prefix-free compression and decompression.
"""
import doctest
from itertools import islice
from collections import Counter
import random
import json

INPUT_FILE = "test/commedia.txt"
COMPRESSED_OUTPUT_FILE = "test/commedia.pfc"
DICTIONARY_OUTPUT_FILE = "test/commedia.pfcd"


def binary_strings(s):
    """
    Given an initial list of binary strings `s`,
    yield all binary strings ending in one of `s` strings.

    >>> take(9, binary_strings(["010", "111"]))
    ['010', '111', 'A010', 'C010', 'G010', 'T010', 'A111', 'C111', 'G111']
    """
    yield from s
    while True:
        s = [b + x for x in s for b in "ACGT"]
        yield from s


def take(n, iterable):
    """
    Return first n items of the iterable as a list.

    >>> take(5, range(10))
    [0, 1, 2, 3, 4]
    """
    return list(islice(iterable, n))


def chunks(xs, n, pad='0'):
    """
    Yield successive n-sized chunks from xs.

    >>> list(chunks([1, 2, 3, 4, 5, 6], 2))
    [[1, 2], [3, 4], [5, 6]]
    """
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def reverse_dict(dictionary):
    """
    >>> sorted(reverse_dict({1 : "a", 2 : "b"}).items())
    [('a', 1), ('b', 2)]
    """
    return {value: key for key, value in dictionary.items()}


def prefix_free(generator):
    """
    Given a `generator`, yield all the items from it
    that do not start with any preceding element.

    >>> take(6, prefix_free(binary_strings(["00", "01"])))
    ['00', '01', 'A00', 'C00', 'G00', 'T00']
    """
    seen = []
    for x in generator:
        if not any(x.startswith(i) for i in seen):
            yield x
            seen.append(x)


def build_translation_dict(text, starting_binary_codes=["000", "100", "111"]):
    """
    Builds a dict for `prefix_free_compression` where
       More common char -> More short binary strings
    This is compression as the shorter binary strings will be seen more times than
    the long ones.

    Univocity in decoding is given by the binary_strings being prefix free.

    >>> sorted(build_translation_dict("aaaaa bbbb ccc dd e", ["01", "11"]).items())
    [(' ', 'A01'), ('a', '01'), ('b', '11'), ('c', 'C01'), ('d', 'G01'), ('e', 'T01')]
    """
    binaries = sorted(list(take(
        len(set(text)), prefix_free(binary_strings(starting_binary_codes)))), key=len)
    frequencies = Counter(text)
    # char value tiebreaker to avoid non-determinism                     v
    alphabet = sorted(
        list(set(text)), key=(lambda ch: (frequencies[ch], ch)), reverse=True)
    return dict(zip(alphabet, binaries))


def prefix_free_compression(text, starting_binary_codes=["AAA", "BAA", "BBB"]):
    """
    Implements `prefix_free_compression`, simply uses the dict
    made with `build_translation_dict`.

    Returns a tuple (compressed_message, tranlation_dict) as the dict is needed
    for decompression.

    >>> prefix_free_compression("aaaaa bbbb ccc dd e", ["01", "11"])[0]
    '0101010101A0111111111A01C01C01C01A01G01G01A01T01'
    """
    translate = build_translation_dict(text, starting_binary_codes)
    return ''.join(translate[i] for i in text), translate, ''.join('<' + i + '>' + translate[i] for i in text)


def _prefix_free_compression(text, translate):
    return ''.join(translate[i] for i in text)


def prefix_free_decompression(compressed, translation_dict):
    """
    Decompresses a prefix free `compressed` message in the form of a string
    composed only of '0' and '1'.

    Being the binary codes prefix free,
    the decompression is allowed to take the earliest match it finds.

    >>> message, d, message_pos = prefix_free_compression("aaaaa bbbb ccc dd e", ["01", "11"])
    >>> message
    '0101010101A0111111111A01C01C01C01A01G01G01A01T01'
    >>> sorted(d.items())
    [(' ', 'A01'), ('a', '01'), ('b', '11'), ('c', 'C01'), ('d', 'G01'), ('e', 'T01')]
    >>> ''.join(prefix_free_decompression(message, d))
    'aaaaa bbbb ccc dd e'
    """
    decoding_translate = reverse_dict(translation_dict)
    word = ''
    for bit in compressed:
        if word in decoding_translate:
            yield decoding_translate[word]
            word = ''
        word += bit
    yield decoding_translate[word]


def _prefix_free_decompression(compressed, translation_dict):
    decoding_translate = reverse_dict(translation_dict)
    word = ''
    for bit in compressed:
        if bit == '\n':
            yield '\n'
            continue
        if bit == '-':
            yield '-'
            continue
        if word in decoding_translate:
            yield decoding_translate[word]
            word = ''
        word += bit.upper()

    if word in decoding_translate:
        yield decoding_translate[word]
    else:
        yield '***' + word


def lines(translation_dict):
    ll = []
    with open(INPUT_FILE) as f:
        text = f.read()
        for l in text.splitlines():
            header = '>' + l + ' #'
            ll.append(header)
            compressed = _prefix_free_compression(l, translation_dict)
            ll.append(compressed)
    with open('test/fasta', 'w') as f:
        f.write('\n'.join(ll))


def output_uncompressed(d):
    ll = []
    with open('test/output.txt', 'r') as f:
        output = f.read()
        alllines = output.splitlines()
        total = len(alllines)
        section = []
        for i, l in enumerate(alllines):
            if l.startswith('>'):
                header = l
                ll.append(l)
                section = []
            else:
                section.append(l)
            if i == total - 1 or alllines[i + 1].startswith('>'):
                section_str = '\n'.join(section)
                uncompressed = ''.join(
                    _prefix_free_decompression(section_str, d))
                ll.append(uncompressed)
    with open('test/output_.txt', 'w') as f:
        f.write('\n'.join(ll))


if __name__ == "__main__":

    doctest.testmod()
    with open(INPUT_FILE) as f:
        text = f.read()
    compressed, d, compressed_pos = prefix_free_compression(text)
    with open(COMPRESSED_OUTPUT_FILE, "w") as f:
        f.write(compressed)
    with open(DICTIONARY_OUTPUT_FILE, "w") as f:
        f.write(json.dumps(d))

    lines(d)
    import os
    os.system('mafft  test/fasta > test/output.txt')
    # dividing by 8 goes from bit length to byte length
    print("Compressed / uncompressed ratio is {}".format(
        (len(json.dumps(d)) + len(compressed) // 8) / len(text)))
    original = ''.join(prefix_free_decompression(compressed, d))
    with open('test/original.txt', 'w') as f:
        f.write(original)
    assert original == text
    output_uncompressed(d)
    # mafft  test/fasta > test/output.txt
