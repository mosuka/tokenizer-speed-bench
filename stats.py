#!/usr/bin/env python3

from __future__ import annotations

import collections
import math
import re
import sys


CORPUS_JA = './resources/wagahaiwa_nekodearu.txt'
CORPUS_KO = './resources/mujeong.txt'
CORPUS_ZH = './resources/rulin_waishi.txt'

RE_DICT = [
    ('kytea', re.compile(r'Elapsed-kytea: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('vaporetto', re.compile(r'Elapsed-vaporetto: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('mecab-ipadic-2_7_0', re.compile(r'Elapsed-mecab-ipadic-2_7_0: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('mecab-unidic-3_1_1', re.compile(r'Elapsed-mecab-unidic-3_1_1: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('kuromoji', re.compile(r'Elapsed-kuromoji: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('lindera-ipadic', re.compile(r'Elapsed-lindera-ipadic: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('lindera-unidic', re.compile(r'Elapsed-lindera-unidic: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('lindera-cc-cedict', re.compile(r'Elapsed-lindera-cc-cedict: ([0-9\.]+) \[sec\]'), CORPUS_ZH),
    ('lindera-jieba', re.compile(r'Elapsed-lindera-jieba: ([0-9\.]+) \[sec\]'), CORPUS_ZH),
    ('lindera-ko-dic', re.compile(r'Elapsed-lindera-ko-dic: ([0-9\.]+) \[sec\]'), CORPUS_KO),
    ('sudachi', re.compile(r'Elapsed-sudachi: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('sudachi.rs', re.compile(r'Elapsed-sudachi.rs: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('rust-tinysegmenter', re.compile(r'Elapsed-rust-tinysegmenter: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('litsea-japanese', re.compile(r'Elapsed-litsea-japanese: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('litsea-japanese-pos', re.compile(r'Elapsed-litsea-japanese-pos: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('litsea-korean', re.compile(r'Elapsed-litsea-korean: ([0-9\.]+) \[sec\]'), CORPUS_KO),
    ('litsea-korean-pos', re.compile(r'Elapsed-litsea-korean-pos: ([0-9\.]+) \[sec\]'), CORPUS_KO),
    ('litsea-chinese', re.compile(r'Elapsed-litsea-chinese: ([0-9\.]+) \[sec\]'), CORPUS_ZH),
    ('litsea-chinese-pos', re.compile(r'Elapsed-litsea-chinese-pos: ([0-9\.]+) \[sec\]'), CORPUS_ZH),
    ('litsea-japanese-two-stage', re.compile(r'Elapsed-litsea-japanese-two-stage: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('litsea-korean-two-stage', re.compile(r'Elapsed-litsea-korean-two-stage: ([0-9\.]+) \[sec\]'), CORPUS_KO),
    ('litsea-chinese-two-stage', re.compile(r'Elapsed-litsea-chinese-two-stage: ([0-9\.]+) \[sec\]'), CORPUS_ZH),
    ('vibrato-ipadic-mecab-2_7_0', re.compile(r'Elapsed-vibrato-ipadic-mecab-2_7_0: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('vibrato-unidic-cwj-3_1_1', re.compile(r'Elapsed-vibrato-unidic-cwj-3_1_1: ([0-9\.]+) \[sec\]'), CORPUS_JA),
    ('vibrato-unidic-cwj-3_1_1+compact-dual', re.compile(r'Elapsed-vibrato-unidic-cwj-3_1_1\+compact-dual: ([0-9\.]+) \[sec\]'), CORPUS_JA),
]


def count_chars(corpus: str) -> int:
    n_chars = 0
    with open(corpus) as fp:
        for line in fp:
            n_chars += len(line.rstrip('\n'))
    return n_chars


def mean_std(n_chars: int, times: list[float]) -> (float, float):
    speeds = [n_chars / time for time in times]
    mean = sum(speeds) / len(speeds)
    dist = sum((speed - mean) ** 2 for speed in speeds) / len(speeds)
    return mean, math.sqrt(dist)


def _main():
    n_chars = {corpus: count_chars(corpus) for _, _, corpus in RE_DICT}
    times = collections.defaultdict(list)
    for line in sys.stdin:
        for name, r, _ in RE_DICT:
            m = r.match(line)
            if m is not None:
                times[name].append(float(m.group(1)))
                break

    # The first trial should be ignored
    # to avoid unfair results due to lazy loading.
    for name, _, _ in RE_DICT:
        times[name] = times[name][1:]

    for name, _, corpus in RE_DICT:
        mean, std = mean_std(n_chars[corpus], times[name])
        print(f'{name} {mean} {std}')


if __name__ == '__main__':
    _main()
