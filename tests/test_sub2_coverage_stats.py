import hashlib
import importlib.util
import json
import re
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / 'translation_review/batch2/sub2_coverage.jsonl'
BLOCKS = ROOT / 'translation_review/batch2/sub2_block_coverage.jsonl'
MANIFEST = ROOT / 'translation_review/batch2/sub2_coverage_manifest.json'

ALLOWED = {
    'auto_strong', 'auto_semantic', 'ai_confirmed', 'candidate_match',
    'structure_candidate', 'non_body', 'duplicate', 'pending',
}
CONFIRMED_OR_MATCHED = {'auto_strong', 'auto_semantic', 'ai_confirmed',
                        'candidate_match', 'structure_candidate'}


def load(path):
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


def normalized_sha256_bytes(data):
    return hashlib.sha256(re.sub(rb'\r\n?', b'\n', data)).hexdigest()


def normalized_sha256(path):
    return normalized_sha256_bytes(path.read_bytes())


class Sub2CoverageStatsChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = load(COVERAGE)
        cls.blocks = load(BLOCKS)
        cls.manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        cls.by_path = defaultdict(list)
        for b in cls.blocks:
            cls.by_path[b['path']].append(b)
        spec = importlib.util.spec_from_file_location(
            'review', ROOT / 'scripts/review_translation_batch.py')
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_all_statuses_are_honest_categories(self):
        self.assertEqual(len(self.summary), 25)
        self.assertEqual(len(self.blocks), 3085)
        for b in self.blocks:
            self.assertIn(b['status'], ALLOWED)
            self.assertNotIn('verified', b['status'])
            self.assertTrue(b['evidence'])
            self.assertEqual(b['source_commit'], self.manifest['source_commit'])

    def test_summary_closes_per_page(self):
        for row in self.summary:
            blocks = self.by_path[row['path']]
            counts = Counter((b['side'], b['status']) for b in blocks)
            for side, total_key in [('en', 'en_blocks'), ('zh', 'zh_blocks')]:
                self.assertEqual(sum(counts[(side, s)] for s in ALLOWED), row[total_key])
            fields = {
                'auto_strong': (row['auto_strong_pairs'], row['auto_strong_pairs']),
                'auto_semantic': (row['auto_semantic_pairs'], row['auto_semantic_pairs']),
                'ai_confirmed': (row['ai_confirmed_en'], row['ai_confirmed_zh']),
                'candidate_match': (row['candidate_match_en'], row['candidate_match_zh']),
                'structure_candidate': (row['structure_candidate_en'], row['structure_candidate_zh']),
                'non_body': (row['non_body_en'], row['non_body_zh']),
                'duplicate': (row['duplicate_en'], row['duplicate_zh']),
                'pending': (row['pending_en'], row['pending_zh']),
            }
            for status, (en_expected, zh_expected) in fields.items():
                self.assertEqual(counts[('en', status)], en_expected, (row['path'], status, 'en'))
                self.assertEqual(counts[('zh', status)], zh_expected, (row['path'], status, 'zh'))

    def test_totals_recomputable_and_pending_allowed(self):
        counts = Counter((b['side'], b['status']) for b in self.blocks)
        for side, total in [('en', 1683), ('zh', 1402)]:
            self.assertEqual(sum(counts[(side, s)] for s in ALLOWED), total)
        self.assertGreater(counts[('en', 'pending')], 0)
        self.assertGreater(counts[('zh', 'pending')], 0)

    def test_wrong_pair_is_not_confirmed(self):
        en = next(b for b in self.blocks
                  if b['side'] == 'en' and b['text'].startswith('If specified, only tetrahedral zones'))
        zh = next(b for b in self.blocks
                  if b['side'] == 'zh' and norm(b['text']) == 'zone generate 命令')
        self.assertEqual(en['status'], 'pending')
        self.assertIsNone(en['matched_index'])
        self.assertEqual(zh['status'], 'pending')
        self.assertIsNone(zh['matched_index'])

    def test_no_reused_targets_for_confirmed_or_candidate_matches(self):
        for path, blocks in self.by_path.items():
            for side in ('en', 'zh'):
                targets = [b['matched_index'] for b in blocks
                           if b['side'] == side and b['status'] in CONFIRMED_OR_MATCHED]
                self.assertEqual(len(targets), len(set(targets)), (path, side))

    def test_ai_confirmed_requires_explicit_evidence(self):
        for b in self.blocks:
            ev = b['evidence']
            if b['status'] == 'ai_confirmed':
                self.assertEqual(ev.get('type'), 'verified_pair')
                self.assertTrue(ev.get('evidence_id'))
                self.assertTrue(ev.get('reason'))
                self.assertTrue(ev.get('source_record'))
                self.assertTrue(ev.get('en_snippet'))
                self.assertTrue(ev.get('zh_snippet'))
            else:
                self.assertNotEqual(ev.get('type'), 'verified_pair')

    def test_structure_candidates_are_not_semantic_confirmations(self):
        for b in self.blocks:
            if b['status'] == 'structure_candidate':
                self.assertEqual(b['evidence'].get('type'), 'structure_candidate')
                self.assertNotIn('verified', b['evidence'].get('reason', ''))

    def test_no_old_version_text_remains(self):
        self.assertEqual(sum(1 for b in self.blocks if 'stress-strength-ratio' in b['text']), 0)
        self.assertEqual(sum(1 for b in self.blocks if 'strength-stress-ratio' in b['text']) > 0, True)

    def test_record_hashes_match_current_input_files(self):
        self.assertIn('normalize_newlines', self.manifest['hash_method'])
        for path, hashes in self.manifest['files'].items():
            self.assertEqual(normalized_sha256(ROOT / 'doc' / path), hashes['zh_sha256'], path)
        en_dir = Path(self.manifest['en_dir'])
        if en_dir.exists():
            for path, hashes in self.manifest['files'].items():
                en_path = en_dir / path.replace('/', '_')
                if en_path.exists():
                    self.assertEqual(normalized_sha256(en_path), hashes['en_sha256'], path)

    def test_english_snapshot_metadata_is_explicit_when_ci_cannot_verify(self):
        self.assertFalse(self.manifest['en_snapshot_available_in_ci'])
        self.assertEqual(len(self.manifest['en_sources']), 25)
        for path, src in self.manifest['en_sources'].items():
            self.assertTrue(src['source_url'].startswith('https://docs.itascacg.com/'))
            self.assertTrue(src['collected_at'])
            self.assertRegex(src['sha256_normalized'], r'^[0-9a-f]{64}$')
            self.assertFalse(src['available_in_ci'])
        en_dir = Path(self.manifest['en_dir'])
        if not en_dir.exists():
            # CI cannot access the Windows worktree snapshot. Do not claim
            # English content was verified; only metadata is checked above.
            self.assertTrue(self.manifest['en_snapshot_available_in_ci'] is False)

    def test_source_commit_is_verifiable_and_not_self_referential(self):
        self.assertEqual(self.manifest['source_commit'],
                         '235af521d76b774618c0edfcfaa8ce8230a0b24a')
        self.assertIn('parent PR head', self.manifest['source_commit_note'])
        self.assertNotIn('git_head', self.manifest)

    def test_normalized_hash_ignores_line_endings_but_detects_content_changes(self):
        self.assertEqual(normalized_sha256_bytes(b'a\r\nb\r\n'),
                         normalized_sha256_bytes(b'a\nb\n'))
        self.assertNotEqual(normalized_sha256_bytes(b'a\nb\n'),
                            normalized_sha256_bytes(b'a\nc\n'))

    def test_recorded_text_exists_in_current_html(self):
        for path, blocks in self.by_path.items():
            zh_texts = {norm(b['text']) for b in self.mod.blocks_with_context(ROOT / 'doc' / path)}
            for b in blocks:
                if b['side'] == 'zh':
                    self.assertIn(norm(b['text']), zh_texts, (path, b['index']))
        en_dir = Path(self.manifest['en_dir'])
        if en_dir.exists():
            for path, blocks in self.by_path.items():
                en_path = en_dir / path.replace('/', '_')
                if not en_path.exists():
                    continue
                en_texts = {norm(b['text']) for b in self.mod.blocks_with_context(en_path)}
                for b in blocks:
                    if b['side'] == 'en':
                        self.assertIn(norm(b['text']), en_texts, (path, b['index']))

if __name__ == '__main__':
    unittest.main()
