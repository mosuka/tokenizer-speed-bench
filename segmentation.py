#!/usr/bin/env python3
"""Score the segmentations the benches write with BENCH_TOKENS.

A bench run with BENCH_TOKENS=<file> writes, for each input line, its tokens
one per line followed by an empty line; each token is a substring of the
input line. This module maps the tokens back to character spans of the line
and scores them in two ways:

- agreement: each row against the reference implementation of the same
  dictionary or model, on the speed corpora (AGREEMENT_GROUPS);
- accuracy: each row against the layers of the Universal Dependencies (UD)
  gold data of its language (GOLD_SETS): for Japanese short units, long
  units and bunsetsu, for Korean morphemes and eojeols, for Chinese words,
  for English words and the surface tokens.

A token counts as correct when its span equals a span of the other side.
Tokens whose first character is whitespace, punctuation, a symbol or a
control character are dropped from both sides first, as Lucene's kuromoji
and nori drop them, so that rows that discard punctuation can be compared
with rows that keep it. For the layers of Japanese and Korean, which run
from fine to coarse, a row's cut (an edge of a scored token inside the
line) counts as right when it is a boundary of the finest layer (boundary
precision), and a boundary of a coarser layer counts as kept when no scored
token crosses it (boundary recall).

Usage (from the repository root):
  segmentation.py text <gold dir> <output dir>
      Write the sentences of each gold set, one per line, as bench input.
  segmentation.py report <gold dir> <segmentation dir>
      Print the agreement and accuracy tables in Markdown. The segmentation
      directory holds corpus/ and ud/, one tokens file per series
      (segment_all.sh writes them).
"""

from __future__ import annotations

import dataclasses
import importlib.util
import os
import sys
import unicodedata

# The Unicode general categories of Lucene 10.6.0's isPunctuation
# (ViterbiNBest in kuromoji, Viterbi in nori). Lucene drops a token when its
# first character is of one of them; nori also drops U+318D (Hangul Letter
# Araea, used as an interpunct).
IGNORED_CATEGORIES = frozenset({
    'Zs', 'Zl', 'Zp', 'Cc', 'Cf',
    'Pd', 'Ps', 'Pe', 'Pc', 'Po', 'Pi', 'Pf',
    'Sm', 'Sc', 'Sk', 'So',
})
IGNORED_CHARACTERS = frozenset({chr(0x318D)})


class AlignmentError(ValueError):
    """A token is not a substring of its line at or after the previous token."""


def is_ignored(token: str) -> bool:
    """Whether a token is dropped before scoring (by its first character)."""
    if not token:
        return True
    first = token[0]
    return first in IGNORED_CHARACTERS or unicodedata.category(first) in IGNORED_CATEGORIES


def read_tokens(path: str) -> list[list[str]]:
    """Read a BENCH_TOKENS file: one list of tokens per input line."""
    blocks: list[list[str]] = []
    current: list[str] = []
    with open(path, encoding='utf-8', newline='') as fp:
        for raw in fp:
            token = raw[:-1] if raw.endswith('\n') else raw
            if token == '':
                blocks.append(current)
                current = []
            else:
                current.append(token)
    if current:
        blocks.append(current)
    return blocks


def align(line: str, tokens: list[str], offset: int = 0) -> list[tuple[int, int]]:
    """Map tokens to (start, end) character spans of the line, in order.

    Each token is searched from the end of the previous one, so text a
    tokenizer drops (spaces, discarded punctuation) is skipped. The spans are
    shifted by offset.
    """
    spans = []
    position = 0
    for token in tokens:
        start = line.find(token, position)
        if start < 0:
            raise AlignmentError(f'token {token!r} not found after position {position} in {line!r}')
        end = start + len(token)
        spans.append((offset + start, offset + end))
        position = end
    return spans


def is_number(text: str) -> bool:
    """Whether every character is a decimal digit (Unicode category Nd)."""
    return text != '' and all(unicodedata.category(c) == 'Nd' for c in text)


def merge_numbers(line: str, spans: list[tuple[int, int]]) -> tuple[list[tuple[int, int]], int]:
    """Merge adjacent spans that are made only of digits into one span.

    Returns the merged spans and how many merges were made. UD Japanese
    concatenates cardinal numbers into one word, while some tokenizers split
    a number into digits.
    """
    merged: list[tuple[int, int]] = []
    merges = 0
    for start, end in spans:
        if merged and merged[-1][1] == start and is_number(line[merged[-1][0]:merged[-1][1]]) and is_number(line[start:end]):
            merged[-1] = (merged[-1][0], end)
            merges += 1
        else:
            merged.append((start, end))
    return merged, merges


def overlaps(span: tuple[int, int], ranges: list[tuple[int, int]]) -> bool:
    """Whether a span overlaps any of the ranges."""
    return any(span[0] < end and span[1] > start for start, end in ranges)


def scored_spans(line: str, spans: list[tuple[int, int]], excluded: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Drop the ignored tokens and the spans inside excluded ranges."""
    return [span for span in spans if not is_ignored(line[span[0]:span[1]]) and not overlaps(span, excluded)]


@dataclasses.dataclass
class Counts:
    """Counts for precision, recall and F1, and the lines that differ."""

    correct: int = 0
    system: int = 0
    gold: int = 0
    lines: int = 0
    differing_lines: int = 0
    merges: int = 0
    failures: int = 0

    def add(self, system: list[tuple[int, int]], gold: list[tuple[int, int]]) -> None:
        self.correct += len(set(system) & set(gold))
        self.system += len(system)
        self.gold += len(gold)
        self.lines += 1
        if system != gold:
            self.differing_lines += 1

    def precision(self) -> float:
        return self.correct / self.system if self.system else 0.0

    def recall(self) -> float:
        return self.correct / self.gold if self.gold else 0.0

    def f1(self) -> float:
        p, r = self.precision(), self.recall()
        return 2 * p * r / (p + r) if p + r else 0.0


@dataclasses.dataclass
class BoundaryCounts:
    """Counts of the gold boundaries that no scored token crosses."""

    kept: int = 0
    total: int = 0
    failures: int = 0

    def share(self) -> float:
        return self.kept / self.total if self.total else 0.0


@dataclasses.dataclass
class CutCounts:
    """Counts of the cuts of the scored tokens that are gold boundaries."""

    matched: int = 0
    total: int = 0
    failures: int = 0

    def share(self) -> float:
        return self.matched / self.total if self.total else 0.0


@dataclasses.dataclass
class Sentence:
    """A gold sentence: its text, its gold spans per layer, the ranges each
    layer excludes from scoring, and the positions where a bunsetsu starts
    (other than the first)."""

    text: str
    layers: dict[str, list[tuple[int, int]]]
    excluded: dict[str, list[tuple[int, int]]] = dataclasses.field(default_factory=dict)
    boundaries: list[int] = dataclasses.field(default_factory=list)


def misc_fields(cols: list[str]) -> dict[str, str]:
    """The Name=Value items of a CoNLL-U word line's MISC column."""
    return dict(item.split('=', 1) for item in cols[9].split('|') if '=' in item)


def read_conllu(path: str, morphemes: bool = False) -> tuple[list[Sentence], int]:
    """Read a CoNLL-U file into sentences with a 'word' and a 'token' layer.

    The token layer has the surface tokens (a multi-word token such as
    "don't" once); the word layer has the syntactic words ("do", "n't").
    When every word has MISC LUWBILabel (UD Japanese), a 'luw' layer joins
    each word labelled I (inside a long unit) to the one before it; when
    every word has MISC BunsetuBILabel, the sentence's boundaries are the
    starts of the words labelled B, except the first word. With morphemes
    (UD_Korean-Kaist), a 'morpheme' layer splits each word's LEMMA at "+"
    (조약에: 조약+에); a word whose parts do not concatenate back to it (의해:
    의하+어) is excluded from the morpheme layer only.
    Returns the sentences and the number of multi-word tokens whose words are
    not substrings of the token, which are kept whole in the word layer.
    """
    sentences = []
    unsplit = 0
    text = None
    rows: list[list[str]] = []

    def flush():
        nonlocal text, rows, unsplit
        if text is None:
            return
        tokens = []  # (form, [word lines]) per surface token
        words_in_range = 0
        for cols in rows:
            ident, form = cols[0], cols[1]
            if '.' in ident:
                continue
            if '-' in ident:
                first, last = (int(x) for x in ident.split('-'))
                tokens.append((form, []))
                words_in_range = last - first + 1
            elif words_in_range:
                tokens[-1][1].append(cols)
                words_in_range -= 1
            else:
                tokens.append((form, [cols]))
        token_spans = align(text, [form for form, _ in tokens])
        words = []  # (span, word line); an unsplit token keeps its first word line
        for (form, word_lines), (start, end) in zip(tokens, token_spans):
            try:
                words.extend(zip(align(text[start:end], [cols[1] for cols in word_lines], start), word_lines))
            except AlignmentError:
                words.append(((start, end), word_lines[0]))
                unsplit += 1
        sentence = Sentence(text, {'token': token_spans, 'word': [span for span, _ in words]})
        fields = [misc_fields(cols) for _, cols in words]
        if words and all('LUWBILabel' in item for item in fields):
            luw: list[tuple[int, int]] = []
            for (start, end), item in zip(sentence.layers['word'], fields):
                if item['LUWBILabel'] == 'I' and luw:
                    luw[-1] = (luw[-1][0], end)
                else:
                    luw.append((start, end))
            sentence.layers['luw'] = luw
        if words and all('BunsetuBILabel' in item for item in fields):
            sentence.boundaries = [start for (start, _), item in zip(sentence.layers['word'][1:], fields[1:])
                                   if item['BunsetuBILabel'] == 'B']
        if morphemes:
            spans, excluded = [], []
            for (start, end), cols in words:
                parts = cols[2].split('+')
                if '' not in parts and ''.join(parts) == cols[1]:
                    spans.extend(align(cols[1], parts, start))
                else:
                    excluded.append((start, end))
            sentence.layers['morpheme'] = spans
            sentence.excluded['morpheme'] = excluded
        sentences.append(sentence)
        text = None
        rows = []

    with open(path, encoding='utf-8') as fp:
        for raw in fp:
            line = raw.rstrip('\n')
            if line.startswith('# text = '):
                text = line[len('# text = '):]
            elif line == '':
                flush()
            elif not line.startswith('#'):
                rows.append(line.split('\t'))
    flush()
    return sentences, unsplit


def load_stats():
    """stats.py, the one list of series and their corpora."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stats.py')
    spec = importlib.util.spec_from_file_location('stats', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# series: (Tokenizer, Dictionary / Model), as in the README's result tables.
DISPLAY = {
    'kytea': ('kytea', 'jp-0.4.7-5.mod'),
    'vaporetto': ('vaporetto', 'kytea jp-0.4.7-5.mod'),
    'mecab-ipadic-2_7_0': ('mecab', 'ipadic 2.7.0'),
    'mecab-unidic-3_1_1': ('mecab', 'unidic-cwj-3.1.1'),
    'mecab-unidic-202512': ('mecab', 'unidic-cwj-202512'),
    'mecab-ko-dic-2_1_1': ('mecab', 'mecab-ko-dic 2.1.1-20180720'),
    'mecab-ko-ko-dic-2_1_1': ('mecab-ko', 'mecab-ko-dic 2.1.1-20180720'),
    'kuromoji': ('kuromoji (Atilika)', 'ipadic (bundled)'),
    'lucene-kuromoji': ('kuromoji (Lucene)', 'ipadic (bundled)'),
    'lucene-nori': ('nori (Lucene)', 'mecab-ko-dic (bundled)'),
    'lindera-ipadic': ('lindera', 'ipadic'),
    'lindera-unidic': ('lindera', 'unidic'),
    'lindera-sudachidict': ('lindera', 'sudachidict'),
    'lindera-unidic-cwj': ('lindera', 'unidic-cwj'),
    'lindera-unidic-csj': ('lindera', 'unidic-csj'),
    'lindera-cc-cedict': ('lindera', 'cc-cedict'),
    'lindera-jieba': ('lindera', 'jieba'),
    'lindera-ko-dic': ('lindera', 'ko-dic'),
    'sudachi-a': ('sudachi (mode A)', 'sudachi-dictionary-20261015-core'),
    'sudachi-b': ('sudachi (mode B)', 'sudachi-dictionary-20261015-core'),
    'sudachi-c': ('sudachi (mode C)', 'sudachi-dictionary-20261015-core'),
    'sudachi.rs-a': ('sudachi.rs (mode A)', 'sudachi-dictionary-20261015-core'),
    'sudachi.rs-b': ('sudachi.rs (mode B)', 'sudachi-dictionary-20261015-core'),
    'sudachi.rs-c': ('sudachi.rs (mode C)', 'sudachi-dictionary-20261015-core'),
    'rust-tinysegmenter': ('rust-tinysegmenter', '-'),
    'litsea-japanese': ('litsea (japanese)', 'japanese.model'),
    'litsea-korean': ('litsea (korean)', 'korean.model'),
    'litsea-chinese': ('litsea (chinese)', 'chinese.model'),
    'litsea-japanese-two-stage': ('litsea (japanese, two-stage)', 'japanese_pos.model'),
    'litsea-korean-two-stage': ('litsea (korean, two-stage)', 'korean_pos.model'),
    'litsea-chinese-two-stage': ('litsea (chinese, two-stage)', 'chinese_pos.model'),
    'litsea-english': ('litsea (english)', 'english.model'),
    'litsea-english-two-stage': ('litsea (english, two-stage)', 'english_pos.model'),
    'vibrato-ipadic-mecab-2_7_0': ('vibrato', 'ipadic-mecab-2.7.0'),
    'vibrato-unidic-cwj-3_1_1': ('vibrato', 'unidic-cwj-3.1.1'),
    'vibrato-unidic-cwj-3_1_1+compact-dual': ('vibrato', 'unidic-cwj-3.1.1+compact-dual'),
    'alyze-kuromoji': ('alyze (kuromoji)', 'ipadic (embedded)'),
    'alyze-nori': ('alyze (nori)', 'mecab-ko-dic (embedded)'),
    'alyze-smartcn': ('alyze (smartcn)', 'smartcn (embedded)'),
    'alyze-uax29': ('alyze (UAX #29)', '-'),
}

# (title, reference series, other series), scored on the speed corpora.
AGREEMENT_GROUPS = [
    ('IPADIC', 'mecab-ipadic-2_7_0',
     ['lindera-ipadic', 'vibrato-ipadic-mecab-2_7_0', 'kuromoji', 'lucene-kuromoji', 'alyze-kuromoji']),
    ('UniDic CWJ 3.1.1', 'mecab-unidic-3_1_1',
     ['vibrato-unidic-cwj-3_1_1', 'vibrato-unidic-cwj-3_1_1+compact-dual']),
    ('UniDic CWJ 202512', 'mecab-unidic-202512', ['lindera-unidic-cwj']),
    ('mecab-ko-dic 2.1.1', 'mecab-ko-ko-dic-2_1_1',
     ['mecab-ko-dic-2_1_1', 'lindera-ko-dic', 'lucene-nori', 'alyze-nori']),
    ('SudachiDict 20261015 core, mode A', 'sudachi-a', ['sudachi.rs-a']),
    ('SudachiDict 20261015 core, mode B', 'sudachi-b', ['sudachi.rs-b']),
    ('SudachiDict 20261015 core, mode C', 'sudachi-c', ['sudachi.rs-c']),
    ('KyTea model jp-0.4.7-5', 'kytea', ['vaporetto']),
]


@dataclasses.dataclass
class GoldSet:
    """UD gold data for one language and the layers it is scored by.

    Without hierarchy, the first layer is given with precision, recall and
    F1, and the other layers with F1. With hierarchy, the layers run from
    fine to coarse, and each is given with its unit F1 and, for the finest
    layer, the boundary precision (the share of the row's cuts that are its
    boundaries: low when the row splits inside its units) or, for a coarser
    layer, the boundary recall (the share of its boundaries that no token of
    the row crosses: low when the row joins its units). With bunsetsu, the
    boundary recall of bunsetsu is given last.

    names maps a layer to its name in the columns ("long units"); the first
    layer needs one only with hierarchy.
    """

    key: str
    title: str
    language: str
    file: str
    layers: tuple = ('word',)
    names: dict = dataclasses.field(default_factory=dict)
    hierarchy: bool = False
    morphemes: bool = False
    bunsetsu: bool = False
    merge_numbers: bool = False


GOLD_SETS = [
    GoldSet('ja-pud', 'Japanese, UD_Japanese-PUD r2.19 (short units, long units, bunsetsu)', 'ja',
            'ja_pud-ud-test.conllu', layers=('word', 'luw'),
            names={'word': 'short units', 'luw': 'long units'},
            hierarchy=True, bunsetsu=True, merge_numbers=True),
    GoldSet('ko-kaist', 'Korean, UD_Korean-Kaist r2.19 test (morphemes, eojeols)', 'ko',
            'ko_kaist-ud-test.conllu', layers=('morpheme', 'word'),
            names={'morpheme': 'morphemes', 'word': 'eojeols'},
            hierarchy=True, morphemes=True),
    GoldSet('zh-pud', 'Chinese, UD_Chinese-PUD r2.19 (traditional)', 'zh', 'zh_pud-ud-test.conllu'),
    GoldSet('en-pud', 'English, UD_English-PUD r2.19', 'en', 'en_pud-ud-test.conllu', layers=('word', 'token'),
            names={'token': 'tokens'}),
]

TEXT_FILES = {
    'ja-pud': 'ja_pud.txt',
    'ko-kaist': 'ko_kaist.txt',
    'zh-pud': 'zh_pud.txt',
    'en-pud': 'en_pud.txt',
}


def read_gold(gold_dir: str, gold: GoldSet) -> tuple[list[Sentence], str]:
    """Read a gold set; returns its sentences and a note on what was adjusted."""
    sentences, unsplit = read_conllu(os.path.join(gold_dir, gold.file), morphemes=gold.morphemes)
    notes = [f'{unsplit} multi-word tokens kept whole in the word layer']
    if gold.morphemes:
        words = sum(len(sentence.layers['word']) for sentence in sentences)
        excluded = sum(len(sentence.excluded['morpheme']) for sentence in sentences)
        notes.append(f'{words - excluded} of {words} words ({100 * (words - excluded) / words:.1f} %) '
                     'scored for morphemes')
    return sentences, '; '.join(notes)


def series_languages(stats) -> dict[str, str]:
    """series -> language code, from stats.py's corpora."""
    language = {stats.CORPUS_JA: 'ja', stats.CORPUS_KO: 'ko', stats.CORPUS_ZH: 'zh', stats.CORPUS_EN: 'en'}
    return {name: language[corpus] for name, _, corpus in stats.RE_DICT}


def corpus_lines(path: str) -> list[str]:
    with open(path, encoding='utf-8') as fp:
        return [line.rstrip('\n') for line in fp]


def blocks_for(lines: list[str], path: str) -> list[list[str]]:
    """The tokens file of a series, one block per input line.

    The Java benches read their input with Scanner.hasNext(), which stops
    before trailing lines that hold only whitespace; those lines get no block
    and are given an empty one here.
    """
    blocks = read_tokens(path)
    if len(blocks) < len(lines) and all(not line.strip() for line in lines[len(blocks):]):
        blocks += [[] for _ in lines[len(blocks):]]
    if len(blocks) != len(lines):
        raise AlignmentError(f'{path}: {len(blocks)} blocks for {len(lines)} lines')
    return blocks


def score_against(lines: list[str], system: list[list[str]], gold: list[list[tuple[int, int]]],
                  excluded: list[list[tuple[int, int]]], merge: bool) -> Counts:
    """Score system tokens against gold spans, line by line."""
    counts = Counts()
    for line, tokens, gold_spans, ranges in zip(lines, system, gold, excluded):
        try:
            spans = align(line, tokens)
        except AlignmentError:
            counts.failures += 1
            continue
        if merge:
            spans, merges = merge_numbers(line, spans)
            counts.merges += merges
            gold_spans, _ = merge_numbers(line, gold_spans)
        counts.add(scored_spans(line, spans, ranges), scored_spans(line, gold_spans, ranges))
    return counts


def count_boundaries(lines: list[str], system: list[list[str]], boundaries: list[list[int]]) -> BoundaryCounts:
    """Count the gold boundaries that no scored system token crosses, line by
    line. Ignored tokens cross nothing, so a row that drops punctuation keeps
    the boundaries next to the punctuation it drops."""
    counts = BoundaryCounts()
    for line, tokens, positions in zip(lines, system, boundaries):
        try:
            spans = align(line, tokens)
        except AlignmentError:
            counts.failures += 1
            continue
        kept = scored_spans(line, spans, [])
        counts.total += len(positions)
        counts.kept += sum(1 for position in positions if not any(s < position < e for s, e in kept))
    return counts


def count_cuts(lines: list[str], system: list[list[str]], gold: list[list[tuple[int, int]]],
               excluded: list[list[tuple[int, int]]], merge: bool) -> CutCounts:
    """Count the cuts of the scored system tokens (their edges inside the
    line) that are edges of gold spans, line by line. A cut inside an
    excluded range is not counted, and the edges of excluded ranges count as
    gold edges. With merge, runs of digits are merged on both sides first."""
    counts = CutCounts()
    for line, tokens, gold_spans, ranges in zip(lines, system, gold, excluded):
        try:
            spans = align(line, tokens)
        except AlignmentError:
            counts.failures += 1
            continue
        if merge:
            spans, _ = merge_numbers(line, spans)
            gold_spans, _ = merge_numbers(line, gold_spans)
        edges = {p for span in gold_spans + ranges for p in span}
        cuts = {p for span in scored_spans(line, spans, []) for p in span
                if 0 < p < len(line) and not any(s < p < e for s, e in ranges)}
        counts.total += len(cuts)
        counts.matched += len(cuts & edges)
    return counts


def layer_boundaries(line: str, spans: list[tuple[int, int]], merge: bool) -> list[int]:
    """The boundaries between the units of a layer: the start of every unit
    but the first. With merge, runs of digits are merged first."""
    if merge:
        spans, _ = merge_numbers(line, spans)
    return [start for start, _ in spans[1:]]


def percent(value: float) -> str:
    """A share as a percentage with two decimals. Only a share of exactly 1
    is shown as 100.00: a share below it that rounds up to 100.00 (one token
    in 200,000 that differs) is shown as 99.99, so that 100.00 always means
    that the two sides are the same."""
    text = f'{100 * value:.2f}'
    return '99.99' if text == '100.00' and value < 1 else text


def agreement_tables(stats, segmentation_dir: str) -> list[str]:
    """The agreement tables, one per group, on the speed corpora, sorted by
    the agreement F1."""
    corpus = {name: corpus for name, _, corpus in stats.RE_DICT}
    out = []
    for title, reference, others in AGREEMENT_GROUPS:
        lines = corpus_lines(corpus[reference])
        ref_blocks = blocks_for(lines, os.path.join(segmentation_dir, 'corpus', reference + '.txt'))
        ref_spans = [align(line, tokens) for line, tokens in zip(lines, ref_blocks)]
        no_ranges = [[] for _ in lines]
        tokenizer, dictionary = DISPLAY[reference]
        out.append(f'#### {title} (reference: {tokenizer}, {dictionary})')
        out.append('')
        out.append('| Tokenizer | Dictionary / Model | Agreement F1 [%] | Lines that differ |')
        out.append('| --- | --- | ---: | ---: |')
        rows = []
        for name in others:
            blocks = blocks_for(lines, os.path.join(segmentation_dir, 'corpus', name + '.txt'))
            counts = score_against(lines, blocks, ref_spans, no_ranges, merge=False)
            if counts.failures:
                print(f'{name}: {counts.failures} lines not aligned', file=sys.stderr)
            rows.append((name, counts))
        rows.sort(key=lambda row: -row[1].f1())
        for name, counts in rows:
            tokenizer, dictionary = DISPLAY[name]
            out.append(f'| {tokenizer} | {dictionary} | {percent(counts.f1())} | '
                       f'{counts.differing_lines:,} of {counts.lines:,} |')
        out.append('')
    return out


@dataclasses.dataclass
class GoldScores:
    """One row's scores against a gold set: unit counts per layer, the cuts
    at boundaries of the finest layer (with hierarchy), and the boundaries
    kept per coarser layer and for 'bunsetsu'."""

    units: dict[str, Counts]
    cuts: CutCounts | None = None
    kept: dict[str, BoundaryCounts] = dataclasses.field(default_factory=dict)

    def failures(self) -> dict[str, int]:
        """Lines that did not align, per count that has any."""
        named = [(layer, counts) for layer, counts in self.units.items()]
        named += [('cuts', self.cuts)] if self.cuts else []
        named += [(f'{layer} boundaries', counts) for layer, counts in self.kept.items()]
        return {name: counts.failures for name, counts in named if counts.failures}


def score_gold(gold: GoldSet, sentences: list[Sentence], system: list[list[str]]) -> GoldScores:
    """Score one row's tokens against each layer of a gold set, each layer
    with its own excluded ranges."""
    lines = [sentence.text for sentence in sentences]
    scores = GoldScores({layer: score_against(lines, system, [s.layers[layer] for s in sentences],
                                              [s.excluded.get(layer, []) for s in sentences], gold.merge_numbers)
                         for layer in gold.layers})
    if gold.hierarchy:
        finest = gold.layers[0]
        scores.cuts = count_cuts(lines, system, [s.layers[finest] for s in sentences],
                                 [s.excluded.get(finest, []) for s in sentences], gold.merge_numbers)
        for layer in gold.layers[1:]:
            scores.kept[layer] = count_boundaries(
                lines, system, [layer_boundaries(s.text, s.layers[layer], gold.merge_numbers) for s in sentences])
    if gold.bunsetsu:
        scores.kept['bunsetsu'] = count_boundaries(lines, system, [s.boundaries for s in sentences])
    return scores


def gold_columns(gold: GoldSet, scores: GoldScores) -> list[tuple[str, float]]:
    """The (column title, share) pairs of one row of a gold set's table."""
    first = gold.layers[0]
    if gold.hierarchy:
        columns = [(f'F1, {gold.names[first]} [%]', scores.units[first].f1()),
                   (f'Boundary precision ({gold.names[first]}) [%]', scores.cuts.share())]
        for layer in gold.layers[1:]:
            columns += [(f'F1, {gold.names[layer]} [%]', scores.units[layer].f1()),
                        (f'Boundary recall ({gold.names[layer]}) [%]', scores.kept[layer].share())]
    else:
        counts = scores.units[first]
        columns = [('Precision [%]', counts.precision()), ('Recall [%]', counts.recall()), ('F1 [%]', counts.f1())]
        columns += [(f'F1, {gold.names[layer]} [%]', scores.units[layer].f1()) for layer in gold.layers[1:]]
    if gold.bunsetsu:
        columns.append(('Boundary recall (bunsetsu) [%]', scores.kept['bunsetsu'].share()))
    return columns


def gold_tables(stats, gold_dir: str, segmentation_dir: str) -> list[str]:
    """The accuracy tables, one per gold set, every row of its language,
    sorted by the F1 of the first layer. The tokens are in
    <segmentation dir>/ud."""
    languages = series_languages(stats)
    out = []
    for gold in GOLD_SETS:
        sentences, note = read_gold(gold_dir, gold)
        print(f'{gold.key}: {len(sentences)} sentences; {note}', file=sys.stderr)
        lines = [sentence.text for sentence in sentences]
        rows = []
        for name, _, _ in stats.RE_DICT:
            if languages[name] != gold.language:
                continue
            blocks = blocks_for(lines, os.path.join(segmentation_dir, 'ud', name + '.txt'))
            scores = score_gold(gold, sentences, blocks)
            for count, failures in scores.failures().items():
                print(f'{gold.key} {name} {count}: {failures} lines not aligned', file=sys.stderr)
            merges = scores.units[gold.layers[0]].merges
            if merges:
                print(f'{gold.key} {name}: {merges} number merges', file=sys.stderr)
            rows.append((name, scores))
        rows.sort(key=lambda row: -row[1].units[gold.layers[0]].f1())
        head = ['Tokenizer', 'Dictionary / Model'] + [title for title, _ in gold_columns(gold, rows[0][1])]
        out.append(f'#### {gold.title}')
        out.append('')
        out.append('| ' + ' | '.join(head) + ' |')
        out.append('| --- | --- |' + ' ---: |' * (len(head) - 2))
        for name, scores in rows:
            tokenizer, dictionary = DISPLAY[name]
            cells = [tokenizer, dictionary] + [percent(share) for _, share in gold_columns(gold, scores)]
            out.append('| ' + ' | '.join(cells) + ' |')
        out.append('')
    return out


def write_texts(gold_dir: str, out_dir: str) -> None:
    """Write each gold set's sentences, one per line, as bench input."""
    os.makedirs(out_dir, exist_ok=True)
    for gold in GOLD_SETS:
        sentences, _ = read_gold(gold_dir, gold)
        with open(os.path.join(out_dir, TEXT_FILES[gold.key]), 'w', encoding='utf-8', newline='\n') as fp:
            for sentence in sentences:
                fp.write(sentence.text + '\n')


def _main():
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'text' and len(sys.argv) == 4:
        write_texts(sys.argv[2], sys.argv[3])
    elif command == 'report' and len(sys.argv) == 4:
        stats = load_stats()
        print('\n'.join(agreement_tables(stats, sys.argv[3]) + gold_tables(stats, sys.argv[2], sys.argv[3])))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    _main()
