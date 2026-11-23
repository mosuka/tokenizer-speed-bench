#!/usr/bin/env python3
"""Score the segmentations the benches write with BENCH_TOKENS.

A bench run with BENCH_TOKENS=<file> writes, for each input line, its tokens
one per line followed by an empty line; each token is a substring of the
input line. This module maps the tokens back to character spans of the line
and scores them in two ways:

- agreement: each row against the reference implementation of the same
  dictionary or model, on the speed corpora (AGREEMENT_GROUPS);
- accuracy: each row against gold-standard data of its language (GOLD_SETS).

A token counts as correct when its span equals a span of the other side.
Tokens whose first character is whitespace, punctuation, a symbol or a
control character are dropped from both sides first, as Lucene's kuromoji
and nori drop them, so that rows that discard punctuation can be compared
with rows that keep it.

Usage (from the repository root):
  segmentation.py text <gold dir> <output dir>
      Write the sentences of each gold set, one per line, as bench input.
  segmentation.py report <gold dir> <segmentation dir>
      Print the agreement and accuracy tables in Markdown. The segmentation
      directory holds corpus/, pud/ and klue/, one tokens file per series
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
class Sentence:
    """A gold sentence: its text, its gold spans per layer, and the ranges
    excluded from scoring."""

    text: str
    layers: dict[str, list[tuple[int, int]]]
    excluded: list[tuple[int, int]] = dataclasses.field(default_factory=list)


def read_conllu(path: str) -> tuple[list[Sentence], int]:
    """Read a CoNLL-U file into sentences with a 'word' and a 'token' layer.

    The token layer has the surface tokens (a multi-word token such as
    "don't" once); the word layer has the syntactic words ("do", "n't").
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
        tokens = []  # (form, [word forms]) per surface token
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
                tokens[-1][1].append(form)
                words_in_range -= 1
            else:
                tokens.append((form, [form]))
        token_spans = align(text, [form for form, _ in tokens])
        word_spans = []
        for (form, words), (start, end) in zip(tokens, token_spans):
            try:
                word_spans.extend(align(text[start:end], words, start))
            except AlignmentError:
                word_spans.append((start, end))
                unsplit += 1
        sentences.append(Sentence(text, {'token': token_spans, 'word': word_spans}))
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


def read_klue(path: str) -> tuple[list[Sentence], int, int]:
    """Read KLUE-DP's TSV into sentences with a 'word' layer of morphemes.

    KLUE-DP gives each eojeol's morphemes as base forms. When they do not
    concatenate back to the eojeol (contractions such as 된 = 되 + ㄴ), the
    eojeol is excluded from scoring. The sentence is the eojeol forms joined
    by spaces, the text that was annotated; the "## klue-dp" line differs
    from it in a few sentences (6 of the 2,000 in dev: digits and a quote).
    Returns the sentences, the number of eojeols and the number of eojeols
    scored.
    """
    sentences = []
    eojeols = scored = 0
    text = None
    rows: list[list[str]] = []

    def flush():
        nonlocal text, rows, eojeols, scored
        if text is None:
            return
        forms = [cols[1] for cols in rows]
        text = ' '.join(forms)
        spans = []
        excluded = []
        for cols, (start, end) in zip(rows, align(text, forms)):
            eojeols += 1
            morphemes = cols[2].split(' ')
            if ''.join(morphemes) == cols[1]:
                spans.extend(align(cols[1], morphemes, start))
                scored += 1
            else:
                excluded.append((start, end))
        sentences.append(Sentence(text, {'word': spans}, excluded))
        text = None
        rows = []

    with open(path, encoding='utf-8') as fp:
        for raw in fp:
            line = raw.rstrip('\n')
            if line.startswith('## klue-dp'):
                text = line.split('\t', 1)[1]
            elif line.startswith('##'):
                continue
            elif line == '':
                flush()
            else:
                rows.append(line.split('\t'))
    flush()
    return sentences, eojeols, scored


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
    'sudachi': ('sudachi', 'sudachi-dictionary-20261015-core'),
    'sudachi.rs': ('sudachi.rs', 'sudachi-dictionary-20261015-core'),
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
    ('SudachiDict 20261015 core', 'sudachi', ['sudachi.rs']),
    ('KyTea model jp-0.4.7-5', 'kytea', ['vaporetto']),
]


@dataclasses.dataclass
class GoldSet:
    """Gold data for one language, and how each row's standard relates to it."""

    key: str
    title: str
    language: str
    file: str
    run: str
    same: frozenset
    close: frozenset = frozenset()
    layers: tuple = ('word',)
    merge_numbers: bool = False


GOLD_SETS = [
    GoldSet('ja-pud', 'Japanese, UD_Japanese-PUD r2.19 (UniDic short units)', 'ja', 'ja_pud-ud-test.conllu', 'pud',
            same=frozenset({'mecab-unidic-3_1_1', 'mecab-unidic-202512', 'vibrato-unidic-cwj-3_1_1',
                            'vibrato-unidic-cwj-3_1_1+compact-dual', 'lindera-unidic', 'lindera-unidic-cwj',
                            'lindera-unidic-csj', 'litsea-japanese', 'litsea-japanese-two-stage'}),
            close=frozenset({'kytea', 'vaporetto'}), merge_numbers=True),
    GoldSet('ko-pud', 'Korean, UD_Korean-PUD r2.19 (eojeols)', 'ko', 'ko_pud-ud-test.conllu', 'pud',
            same=frozenset({'litsea-korean', 'litsea-korean-two-stage'})),
    GoldSet('ko-klue', 'Korean, KLUE-DP v1.1 dev (morphemes)', 'ko', 'klue-dp-v1.1_dev.tsv', 'klue',
            same=frozenset(),
            close=frozenset({'mecab-ko-ko-dic-2_1_1', 'mecab-ko-dic-2_1_1', 'lindera-ko-dic', 'lucene-nori',
                             'alyze-nori'})),
    GoldSet('zh-pud', 'Chinese, UD_Chinese-PUD r2.19 (traditional)', 'zh', 'zh_pud-ud-test.conllu', 'pud',
            same=frozenset({'litsea-chinese', 'litsea-chinese-two-stage', 'lindera-jieba'})),
    GoldSet('en-pud', 'English, UD_English-PUD r2.19', 'en', 'en_pud-ud-test.conllu', 'pud',
            same=frozenset({'litsea-english', 'litsea-english-two-stage'}), layers=('word', 'token')),
]

TEXT_FILES = {
    'ja-pud': 'ja_pud.txt',
    'ko-pud': 'ko_pud.txt',
    'ko-klue': 'klue_dp_dev.txt',
    'zh-pud': 'zh_pud.txt',
    'en-pud': 'en_pud.txt',
}


def read_gold(gold_dir: str, gold: GoldSet) -> tuple[list[Sentence], str]:
    """Read a gold set; returns its sentences and a note on what was adjusted."""
    path = os.path.join(gold_dir, gold.file)
    if gold.file.endswith('.conllu'):
        sentences, unsplit = read_conllu(path)
        return sentences, f'{unsplit} multi-word tokens kept whole in the word layer'
    sentences, eojeols, scored = read_klue(path)
    return sentences, f'{scored} of {eojeols} eojeols ({100 * scored / eojeols:.1f} %) scored'


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


def percent(value: float) -> str:
    return f'{100 * value:.2f}'


def agreement_tables(stats, segmentation_dir: str) -> list[str]:
    """The agreement tables, one per group, on the speed corpora."""
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
        for name in others:
            blocks = blocks_for(lines, os.path.join(segmentation_dir, 'corpus', name + '.txt'))
            counts = score_against(lines, blocks, ref_spans, no_ranges, merge=False)
            if counts.failures:
                print(f'{name}: {counts.failures} lines not aligned', file=sys.stderr)
            tokenizer, dictionary = DISPLAY[name]
            out.append(f'| {tokenizer} | {dictionary} | {percent(counts.f1())} | '
                       f'{counts.differing_lines:,} of {counts.lines:,} |')
        out.append('')
    return out


def gold_tables(stats, gold_dir: str, segmentation_dir: str) -> list[str]:
    """The accuracy tables, one per gold set, every row of its language."""
    languages = series_languages(stats)
    out = []
    for gold in GOLD_SETS:
        sentences, note = read_gold(gold_dir, gold)
        print(f'{gold.key}: {len(sentences)} sentences; {note}', file=sys.stderr)
        lines = [sentence.text for sentence in sentences]
        excluded = [sentence.excluded for sentence in sentences]
        rows = []
        for name, _, _ in stats.RE_DICT:
            if languages[name] != gold.language:
                continue
            blocks = blocks_for(lines, os.path.join(segmentation_dir, gold.run, name + '.txt'))
            results = []
            for layer in gold.layers:
                counts = score_against(lines, blocks, [s.layers[layer] for s in sentences], excluded,
                                       gold.merge_numbers)
                if counts.failures:
                    print(f'{gold.key} {name}: {counts.failures} lines not aligned', file=sys.stderr)
                results.append(counts)
            standard = 'same' if name in gold.same else 'close' if name in gold.close else 'different'
            rows.append((standard, name, results))
        order = {'same': 0, 'close': 1, 'different': 2}
        rows.sort(key=lambda row: (order[row[0]], -row[2][0].f1()))
        out.append(f'#### {gold.title}')
        out.append('')
        if gold.layers == ('word', 'token'):
            out.append('| Tokenizer | Dictionary / Model | Standard | Precision [%] | Recall [%] | F1 [%] | F1, tokens [%] |')
            out.append('| --- | --- | --- | ---: | ---: | ---: | ---: |')
        else:
            out.append('| Tokenizer | Dictionary / Model | Standard | Precision [%] | Recall [%] | F1 [%] |')
            out.append('| --- | --- | --- | ---: | ---: | ---: |')
        for standard, name, results in rows:
            tokenizer, dictionary = DISPLAY[name]
            cells = [tokenizer, dictionary, standard, percent(results[0].precision()),
                     percent(results[0].recall()), percent(results[0].f1())]
            cells += [percent(counts.f1()) for counts in results[1:]]
            out.append('| ' + ' | '.join(cells) + ' |')
            if results[0].merges:
                print(f'{gold.key} {name}: {results[0].merges} number merges', file=sys.stderr)
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
