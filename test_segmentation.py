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

# UD Japanese: MISC marks the bunsetsu and long-unit boundaries of each word.
JAPANESE = """# sent_id = 1
# text = 国際連合で猫を見た。
1\t国際\t国際\tNOUN\t_\t_\t3\tcompound\t_\tBunsetuBILabel=B|LUWBILabel=B|SpaceAfter=No
2\t連合\t連合\tNOUN\t_\t_\t6\tobl\t_\tBunsetuBILabel=I|LUWBILabel=I|SpaceAfter=No
3\tで\tで\tADP\t_\t_\t2\tcase\t_\tBunsetuBILabel=I|LUWBILabel=B|SpaceAfter=No
4\t猫\t猫\tNOUN\t_\t_\t6\tobj\t_\tBunsetuBILabel=B|LUWBILabel=B|SpaceAfter=No
5\tを\tを\tADP\t_\t_\t4\tcase\t_\tBunsetuBILabel=I|LUWBILabel=B|SpaceAfter=No
6\t見\t見る\tVERB\t_\t_\t0\troot\t_\tBunsetuBILabel=B|LUWBILabel=B|SpaceAfter=No
7\tた\tた\tAUX\t_\t_\t6\taux\t_\tBunsetuBILabel=I|LUWBILabel=B|SpaceAfter=No
8\t。\t。\tPUNCT\t_\t_\t6\tpunct\t_\tBunsetuBILabel=I|LUWBILabel=B|SpaceAfter=No

"""

# UD_Korean-Kaist: each word is an eojeol, and its LEMMA gives its morphemes.
KOREAN = """# sent_id = 1
# text = 이 조약에 의해 영국은.
1\t이\t이\tDET\t_\t_\t2\tdet\t_\t_
2\t조약에\t조약+에\tADV\t_\t_\t3\tobl\t_\t_
3\t의해\t의하+어\tSCONJ\t_\t_\t4\tadvcl\t_\t_
4\t영국은\t영국+은\tPROPN\t_\t_\t0\troot\t_\tSpaceAfter=No
5\t.\t.\tPUNCT\t_\t_\t4\tpunct\t_\t_

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
        # Without the MISC fields or morphemes, no other layer is built.
        self.assertEqual(sorted(first.layers), ['token', 'word'])
        self.assertEqual((first.boundaries, first.excluded), ([], {}))

    def test_japanese_long_units_and_bunsetsu_boundaries(self):
        with tempfile.TemporaryDirectory() as d:
            sentences, _ = segmentation.read_conllu(write(d, 'j.conllu', JAPANESE))
        sentence = sentences[0]
        self.assertEqual([sentence.text[s:e] for s, e in sentence.layers['word']],
                         ['国際', '連合', 'で', '猫', 'を', '見', 'た', '。'])
        self.assertEqual([sentence.text[s:e] for s, e in sentence.layers['luw']],
                         ['国際連合', 'で', '猫', 'を', '見', 'た', '。'])
        # 猫 and 見 start a bunsetsu; the first word is not a boundary.
        self.assertEqual(sentence.boundaries, [5, 7])

    def test_korean_morphemes_exclude_only_from_their_layer(self):
        with tempfile.TemporaryDirectory() as d:
            sentences, _ = segmentation.read_conllu(write(d, 'k.conllu', KOREAN), morphemes=True)
        sentence = sentences[0]
        self.assertEqual([sentence.text[s:e] for s, e in sentence.layers['word']],
                         ['이', '조약에', '의해', '영국은', '.'])
        self.assertEqual([sentence.text[s:e] for s, e in sentence.layers['morpheme']],
                         ['이', '조약', '에', '영국', '은', '.'])
        # 의하 + 어 does not concatenate back to 의해.
        self.assertEqual(sentence.excluded, {'morpheme': [(6, 8)]})

    def test_morphemes_only_when_asked(self):
        with tempfile.TemporaryDirectory() as d:
            sentences, _ = segmentation.read_conllu(write(d, 'k.conllu', KOREAN))
        self.assertNotIn('morpheme', sentences[0].layers)


class CountBoundariesTest(unittest.TestCase):
    def test_dropped_punctuation_keeps_the_boundary(self):
        # The bunsetsu 「犬」 starts at 3; a row that drops 、 and 「 has no
        # token ending or starting there, but no token crosses it.
        counts = segmentation.count_boundaries(['猫だ、「犬」'], [['猫', 'だ', '犬']], [[3]])
        self.assertEqual((counts.kept, counts.total), (1, 1))

    def test_a_crossing_token_loses_the_boundary(self):
        counts = segmentation.count_boundaries(['役に立つ', '役に立つ'], [['役に立つ'], ['役', 'に', '立つ']],
                                               [[2], [2]])
        self.assertEqual((counts.kept, counts.total), (1, 2))
        self.assertAlmostEqual(counts.share(), 0.5)

    def test_an_ignored_token_crosses_nothing(self):
        counts = segmentation.count_boundaries(['猫、「犬'], [['猫', '、「', '犬']], [[2]])
        self.assertEqual((counts.kept, counts.total), (1, 1))

    def test_unaligned_lines_are_counted(self):
        counts = segmentation.count_boundaries(['猫'], [['犬']], [[]])
        self.assertEqual((counts.failures, counts.total), (1, 0))


class CountCutsTest(unittest.TestCase):
    def test_cuts_inside_units_are_not_matched(self):
        counts = segmentation.count_cuts(['조약에'], [['조', '약', '에']], [[(0, 2), (2, 3)]], [[]], merge=False)
        self.assertEqual((counts.matched, counts.total), (1, 2))
        self.assertAlmostEqual(counts.share(), 0.5)

    def test_digit_runs_are_merged_only_when_asked(self):
        args = (['12年'], [['1', '2', '年']], [[(0, 2), (2, 3)]], [[]])
        merged = segmentation.count_cuts(*args, merge=True)
        self.assertEqual((merged.matched, merged.total), (1, 1))
        unmerged = segmentation.count_cuts(*args, merge=False)
        self.assertEqual((unmerged.matched, unmerged.total), (1, 2))

    def test_excluded_ranges(self):
        # 된다 has no morphemes: the cut inside it is not counted, and the cut
        # at its edge is a gold boundary.
        counts = segmentation.count_cuts(['된다 집'], [['된', '다', '집']], [[(3, 4)]], [[(0, 2)]], merge=False)
        self.assertEqual((counts.matched, counts.total), (2, 2))

    def test_edges_of_the_line_and_of_ignored_tokens(self):
        # The line's ends are not cuts, and the row's cut between 、 and 。,
        # which the gold data keeps together, is not counted: only the edges
        # of 猫 and 犬 are.
        counts = segmentation.count_cuts(['猫、。犬'], [['猫', '、', '。', '犬']], [[(0, 1), (1, 3), (3, 4)]], [[]],
                                         merge=False)
        self.assertEqual((counts.matched, counts.total), (2, 2))

    def test_unaligned_lines_are_counted(self):
        counts = segmentation.count_cuts(['猫'], [['犬']], [[(0, 1)]], [[]], merge=False)
        self.assertEqual((counts.failures, counts.total), (1, 0))


class LayerBoundariesTest(unittest.TestCase):
    def test_the_start_of_every_unit_but_the_first(self):
        self.assertEqual(segmentation.layer_boundaries('ab c', [(0, 1), (1, 2), (3, 4)], merge=False), [1, 3])

    def test_digit_runs_are_merged_only_when_asked(self):
        spans = [(0, 1), (1, 2), (2, 3)]
        self.assertEqual(segmentation.layer_boundaries('12年', spans, merge=True), [2])
        self.assertEqual(segmentation.layer_boundaries('12年', spans, merge=False), [1, 2])


def gold_set(key):
    return next(gold for gold in segmentation.GOLD_SETS if gold.key == key)


class ScoreGoldTest(unittest.TestCase):
    def test_korean_hierarchy(self):
        gold = gold_set('ko-kaist')
        with tempfile.TemporaryDirectory() as d:
            sentences, _ = segmentation.read_conllu(write(d, gold.file, KOREAN), morphemes=True)
        scores = segmentation.score_gold(gold, sentences, [['이', '조', '약에', '의해', '영국은', '.']])
        # 의해 is scored as an eojeol (the period is ignored) but not as morphemes.
        self.assertEqual((scores.units['word'].correct, scores.units['word'].gold), (3, 4))
        self.assertEqual((scores.units['morpheme'].correct, scores.units['morpheme'].gold), (1, 5))
        # Cuts 1 2 3 5 6 8 9 12: only 3 (inside 조약) is not a morpheme boundary.
        self.assertEqual((scores.cuts.matched, scores.cuts.total), (7, 8))
        self.assertEqual((scores.kept['word'].kept, scores.kept['word'].total), (4, 4))
        self.assertNotIn('bunsetsu', scores.kept)
        self.assertEqual(scores.failures(), {})

    def test_japanese_hierarchy_and_bunsetsu(self):
        gold = gold_set('ja-pud')
        with tempfile.TemporaryDirectory() as d:
            sentences, _ = segmentation.read_conllu(write(d, gold.file, JAPANESE))
        scores = segmentation.score_gold(gold, sentences, [['国際連合で', '猫を', '見た', '。']])
        self.assertEqual([scores.units[layer].correct for layer in gold.layers], [0, 0])
        # The cuts 5 7 9 are short-unit boundaries; 国際連合で crosses the
        # long-unit boundary 4 and 猫を the one at 6, 見た the one at 8.
        self.assertEqual((scores.cuts.matched, scores.cuts.total), (3, 3))
        self.assertEqual((scores.kept['luw'].kept, scores.kept['luw'].total), (3, 6))
        self.assertEqual((scores.kept['bunsetsu'].kept, scores.kept['bunsetsu'].total), (2, 2))

    def test_without_hierarchy(self):
        gold = gold_set('en-pud')
        with tempfile.TemporaryDirectory() as d:
            sentences, _ = segmentation.read_conllu(write(d, gold.file, CONLLU))
        scores = segmentation.score_gold(gold, sentences[:1], [['I', 'don', "'t", 'know', '.']])
        self.assertIsNone(scores.cuts)
        self.assertEqual(scores.kept, {})
        self.assertEqual([scores.units[layer].correct for layer in gold.layers], [2, 2])


class GoldColumnsTest(unittest.TestCase):
    def titles(self, key):
        gold = gold_set(key)
        scores = segmentation.GoldScores({layer: segmentation.Counts() for layer in gold.layers},
                                         segmentation.CutCounts(),
                                         {layer: segmentation.BoundaryCounts()
                                          for layer in list(gold.layers[1:]) + ['bunsetsu']})
        return [title for title, _ in segmentation.gold_columns(gold, scores)]

    def test_japanese(self):
        self.assertEqual(self.titles('ja-pud'), [
            'F1, short units [%]', 'Boundary precision (short units) [%]', 'F1, long units [%]',
            'Boundary recall (long units) [%]', 'Boundary recall (bunsetsu) [%]'])

    def test_korean(self):
        self.assertEqual(self.titles('ko-kaist'), [
            'F1, morphemes [%]', 'Boundary precision (morphemes) [%]', 'F1, eojeols [%]',
            'Boundary recall (eojeols) [%]'])

    def test_english_and_chinese(self):
        self.assertEqual(self.titles('en-pud'), ['Precision [%]', 'Recall [%]', 'F1 [%]', 'F1, tokens [%]'])
        self.assertEqual(self.titles('zh-pud'), ['Precision [%]', 'Recall [%]', 'F1 [%]'])


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


class PercentTest(unittest.TestCase):
    def test_two_decimals(self):
        self.assertEqual(segmentation.percent(0.5), '50.00')
        self.assertEqual(segmentation.percent(0.123456), '12.35')
        self.assertEqual(segmentation.percent(0.0), '0.00')

    def test_only_an_exact_match_is_100(self):
        self.assertEqual(segmentation.percent(1.0), '100.00')
        # 99.996 % rounds to 100.00 but is not an exact match.
        self.assertEqual(segmentation.percent(0.99996), '99.99')
        self.assertEqual(segmentation.percent(199_999 / 200_000), '99.99')

    def test_values_that_round_below_100_are_unchanged(self):
        self.assertEqual(segmentation.percent(0.99994), '99.99')
        self.assertEqual(segmentation.percent(0.9996), '99.96')


class SeriesTest(unittest.TestCase):
    def test_every_series_has_a_display_name_and_a_language(self):
        stats = segmentation.load_stats()
        names = [name for name, _, _ in stats.RE_DICT]
        self.assertEqual(sorted(names), sorted(segmentation.DISPLAY))
        languages = segmentation.series_languages(stats)
        for _, reference, others in segmentation.AGREEMENT_GROUPS:
            for name in [reference] + others:
                self.assertIn(name, languages)

    def test_every_gold_set_has_rows_a_text_file_and_column_names(self):
        languages = set(segmentation.series_languages(segmentation.load_stats()).values())
        self.assertEqual(sorted(segmentation.TEXT_FILES), sorted(g.key for g in segmentation.GOLD_SETS))
        for gold in segmentation.GOLD_SETS:
            self.assertIn(gold.language, languages, gold.key)
            named = gold.layers if gold.hierarchy else gold.layers[1:]
            for layer in named:
                self.assertIn(layer, gold.names, gold.key)


if __name__ == '__main__':
    unittest.main()
