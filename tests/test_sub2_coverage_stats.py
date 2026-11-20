import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / 'translation_review/batch2/sub2_coverage.jsonl'
BLOCKS = ROOT / 'translation_review/batch2/sub2_block_coverage.jsonl'

ALLOWED = {
    'auto_strong', 'auto_semantic', 'ai_confirmed_unmatched',
    'code_table_formula_verified', 'structure_non_body', 'non_body',
    'duplicate', 'unresolved',
}


def load(path):
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]


class Sub2CoverageStatsChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = load(COVERAGE)
        cls.blocks = load(BLOCKS)
        cls.by_path = {}
        for b in cls.blocks:
            cls.by_path.setdefault(b['path'], []).append(b)

    def test_page_count_and_no_boolean_coverage_flag(self):
        self.assertEqual(len(self.summary), 25)
        for row in self.summary:
            self.assertNotIn('main_body_checked_by_ai', row)

    def test_all_blocks_have_traceable_status_and_allowed_category(self):
        self.assertEqual(len(self.blocks), 3085)
        for b in self.blocks:
            self.assertIn(b['status'], ALLOWED)
            self.assertTrue(b['evidence'])
            self.assertIn(b['side'], {'en', 'zh'})
            self.assertIsInstance(b['index'], int)

    def test_summary_closes_per_page_for_both_sides(self):
        for row in self.summary:
            blocks = self.by_path[row['path']]
            counts = Counter((b['side'], b['status']) for b in blocks)
            en_sum = sum(counts[('en', s)] for s in ALLOWED)
            zh_sum = sum(counts[('zh', s)] for s in ALLOWED)
            self.assertEqual(en_sum, row['en_blocks'], row['path'])
            self.assertEqual(zh_sum, row['zh_blocks'], row['path'])
            self.assertEqual(row['auto_strong_pairs'], sum(1 for b in blocks if b['side'] == 'en' and b['status'] == 'auto_strong'))
            self.assertEqual(row['auto_semantic_pairs'], sum(1 for b in blocks if b['side'] == 'en' and b['status'] == 'auto_semantic'))
            self.assertEqual(row['unresolved_en'], counts[('en', 'unresolved')])
            self.assertEqual(row['unresolved_zh'], counts[('zh', 'unresolved')])

    def test_totals_are_recomputable(self):
        counts = Counter((b['side'], b['status']) for b in self.blocks)
        expected = {
            ('en', 'auto_strong'): 320, ('zh', 'auto_strong'): 320,
            ('en', 'auto_semantic'): 276, ('zh', 'auto_semantic'): 276,
            ('en', 'unresolved'): 0, ('zh', 'unresolved'): 0,
        }
        for key, value in expected.items():
            self.assertEqual(counts[key], value, key)
        self.assertEqual(sum(counts[('en', s)] for s in ALLOWED), 1683)
        self.assertEqual(sum(counts[('zh', s)] for s in ALLOWED), 1402)

    def test_ai_confirmed_and_structure_counts_are_not_duplicated(self):
        for row in self.summary:
            self.assertNotIn('structure_diff_verified', row)
            self.assertEqual(row['ai_confirmed_unmatched_en'], sum(
                1 for b in self.by_path[row['path']]
                if b['side'] == 'en' and b['status'] == 'ai_confirmed_unmatched'))
            self.assertEqual(row['ai_confirmed_unmatched_zh'], sum(
                1 for b in self.by_path[row['path']]
                if b['side'] == 'zh' and b['status'] == 'ai_confirmed_unmatched'))

if __name__ == '__main__':
    unittest.main()
