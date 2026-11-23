#!/usr/bin/env python3
"""Unit tests for segmentation.py.

Run from the repository root: python3 -B -m unittest test_segmentation
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import segmentation  # noqa: E402


def write(directory, name, text):
    path = os.path.join(directory, name)
    with open(path, 'w', encoding='utf-8', newline='\n') as fp:
        fp.write(text)
    return path


class IgnoredTest(unittest.TestCase):
    def test_punctuation_spaces_and_symbols(self):
        for token in ['、', '。', ' ', chr(0x3000), '「', '!', '-', '$', '+', "'s", '\t']:
            self.assertTrue(segmentation.is_ignored(token), token)

    def test_words_and_numbers(self):
        for token in ['猫', '吾輩', 'cat', "n't", '12', '１２', '조약']:
            self.assertFalse(segmentation.is_ignored(token), token)

    def test_hangul_letter_araea(self):
        self.assertTrue(segmentation.is_ignored(chr(0x318D)))

    def test_empty(self):
        self.assertTrue(segmentation.is_ignored(''))


class ReadTokensTest(unittest.TestCase):
    def test_blocks_and_empty_lines(self):
        with tempfile.TemporaryDirectory() as d:
            path = write(d, 't.txt', 'a\nb\n\n\nc\n \n\n')
            self.assertEqual(segmentation.read_tokens(path), [['a', 'b'], [], ['c', ' ']])

    def test_missing_final_empty_line(self):
        with tempfile.TemporaryDirectory() as d:
            path = write(d, 't.txt', 'a\n\nb\n')
            self.assertEqual(segmentation.read_tokens(path), [['a'], ['b']])


class AlignTest(unittest.TestCase):
    def test_spans_skip_dropped_text(self):
        self.assertEqual(segmentation.align('吾輩は、猫', ['吾輩', 'は', '猫']), [(0, 2), (2, 3), (4, 5)])

    def test_offset(self):
        self.assertEqual(segmentation.align('do', ['d', 'o'], 10), [(10, 11), (11, 12)])

    def test_failure(self):
        with self.assertRaises(segmentation.AlignmentError):
            segmentation.align('猫です', ['犬'])

    def test_order(self):
        with self.assertRaises(segmentation.AlignmentError):
            segmentation.align('ab', ['b', 'a'])


class MergeNumbersTest(unittest.TestCase):
    def test_adjacent_digits(self):
        line = '12年'
        self.assertEqual(segmentation.merge_numbers(line, [(0, 1), (1, 2), (2, 3)]), ([(0, 2), (2, 3)], 1))

    def test_not_across_a_gap_or_a_comma(self):
        line = '1,000 2'
        spans = [(0, 1), (1, 2), (2, 5), (6, 7)]
        self.assertEqual(segmentation.merge_numbers(line, spans), (spans, 0))


class CountsTest(unittest.TestCase):
    def test_precision_recall_f1(self):
        counts = segmentation.Counts()
        counts.add([(0, 2), (2, 3), (3, 5)], [(0, 2), (2, 5)])
        self.assertEqual((counts.correct, counts.system, counts.gold), (1, 3, 2))
        self.assertAlmostEqual(counts.precision(), 1 / 3)
        self.assertAlmostEqual(counts.recall(), 1 / 2)
        self.assertAlmostEqual(counts.f1(), 0.4)
        self.assertEqual(counts.differing_lines, 1)

    def test_identical_lines(self):
        counts = segmentation.Counts()
        counts.add([(0, 1)], [(0, 1)])
        self.assertEqual((counts.f1(), counts.differing_lines, counts.lines), (1.0, 0, 1))


class ScoreAgainstTest(unittest.TestCase):
    def test_ignored_tokens_are_dropped_from_both_sides(self):
        lines = ['猫、犬']
        system = [['猫', '犬']]           # punctuation discarded, as Lucene does
        gold = [[(0, 1), (1, 2), (2, 3)]]  # punctuation kept, as MeCab does
        counts = segmentation.score_against(lines, system, gold, [[]], merge=False)
        self.assertEqual((counts.f1(), counts.differing_lines), (1.0, 0))

    def test_numbers_are_merged_only_when_asked(self):
        lines = ['12年']
        system = [['1', '2', '年']]
        gold = [[(0, 2), (2, 3)]]
        self.assertEqual(segmentation.score_against(lines, system, gold, [[]], merge=True).f1(), 1.0)
        self.assertLess(segmentation.score_against(lines, system, gold, [[]], merge=False).f1(), 1.0)

    def test_excluded_ranges(self):
        lines = ['된다 집']
        system = [['된', '다', '집']]
        gold = [[(3, 4)]]
        counts = segmentation.score_against(lines, system, gold, [[(0, 2)]], merge=False)
        self.assertEqual((counts.system, counts.gold, counts.f1()), (1, 1, 1.0))

    def test_unaligned_lines_are_counted(self):
        counts = segmentation.score_against(['猫'], [['犬']], [[(0, 1)]], [[]], merge=False)
        self.assertEqual((counts.failures, counts.lines), (1, 0))


CONLLU = """# sent_id = 1
# text = I don't know.
1\tI\tI\tPRON\t_\t_\t3\tnsubj\t_\t_
2-3\tdon't\t_\t_\t_\t_\t_\t_\t_\t_
2\tdo\tdo\tAUX\t_\t_\t3\taux\t_\t_
3\tn't\tnot\tPART\t_\t_\t4\tadvmod\t_\t_
4\tknow\tknow\tVERB\t_\t_\t0\troot\t_\tSpaceAfter=No
5\t.\t.\tPUNCT\t_\t_\t4\tpunct\t_\t_

# sent_id = 2
# text = vámonos
1-2\tvámonos\t_\t_\t_\t_\t_\t_\t_\t_
1\tvamos\tir\tVERB\t_\t_\t0\troot\t_\t_
2\tnos\tnosotros\tPRON\t_\t_\t1\tobj\t_\t_

"""

KLUE = """## 칼럼명 : INDEX\tWORD_FORM\tLEMMA\tPOS\tHEAD\tDEPREL
## klue-dp-v1_dev_00000_test\t유희열이 탈락에 흘렸다.
1\t유희열이\t유희열 이\tNNP+JKS\t3\tNP_SBJ
2\t탈락에\t탈락 에\tNNG+JKB\t3\tNP_AJT
3\t흘렸다.\t흘리 었 다 .\tVV+EP+EF+SF\t0\tVP

"""


class ReadersTest(unittest.TestCase):
    def test_conllu_layers(self):
        with tempfile.TemporaryDirectory() as d:
            sentences, unsplit = segmentation.read_conllu(write(d, 'g.conllu', CONLLU))
        first = sentences[0]
        self.assertEqual(first.text, "I don't know.")
        self.assertEqual([first.text[s:e] for s, e in first.layers['token']], ['I', "don't", 'know', '.'])
        self.assertEqual([first.text[s:e] for s, e in first.layers['word']], ['I', 'do', "n't", 'know', '.'])
        # vamos + nos are not substrings of vámonos: kept whole and counted.
        self.assertEqual(sentences[1].layers['word'], [(0, 7)])
        self.assertEqual(unsplit, 1)

    def test_klue_contractions_are_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            sentences, eojeols, scored = segmentation.read_klue(write(d, 'k.tsv', KLUE))
        sentence = sentences[0]
        self.assertEqual(sentence.text, '유희열이 탈락에 흘렸다.')
        self.assertEqual([sentence.text[s:e] for s, e in sentence.layers['word']], ['유희열', '이', '탈락', '에'])
        self.assertEqual(sentence.excluded, [(9, 13)])
        self.assertEqual((eojeols, scored), (3, 2))

    def test_klue_text_is_the_joined_forms(self):
        # The sentence line has a curly quote where the form has an ASCII one.
        tsv = KLUE.replace('\t유희열이 탈락에 흘렸다.\n', "\t'유희열’이 탈락에 흘렸다.\n").replace(
            '1\t유희열이\t유희열 이\t', "1\t'유희열'이\t' 유희열 ' 이\t")
        with tempfile.TemporaryDirectory() as d:
            sentences, _, _ = segmentation.read_klue(write(d, 'k.tsv', tsv))
        self.assertEqual(sentences[0].text, "'유희열'이 탈락에 흘렸다.")


class BlocksForTest(unittest.TestCase):
    def test_trailing_whitespace_lines_without_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            path = write(d, 't.txt', 'a\n\n')
            self.assertEqual(segmentation.blocks_for(['a', '', ' '], path), [['a'], [], []])

    def test_missing_blocks_for_text(self):
        with tempfile.TemporaryDirectory() as d:
            path = write(d, 't.txt', 'a\n\n')
            with self.assertRaises(segmentation.AlignmentError):
                segmentation.blocks_for(['a', 'b'], path)


class SeriesTest(unittest.TestCase):
    def test_every_series_has_a_display_name_and_a_language(self):
        stats = segmentation.load_stats()
        names = [name for name, _, _ in stats.RE_DICT]
        self.assertEqual(sorted(names), sorted(segmentation.DISPLAY))
        languages = segmentation.series_languages(stats)
        for _, reference, others in segmentation.AGREEMENT_GROUPS:
            for name in [reference] + others:
                self.assertIn(name, languages)
        for gold in segmentation.GOLD_SETS:
            for name in gold.same | gold.close:
                self.assertEqual(languages[name], gold.language, name)


if __name__ == '__main__':
    unittest.main()
