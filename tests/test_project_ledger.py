import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'translation_review'

def load_jsonl(name):
    return [json.loads(l) for l in (R / name).read_text(encoding='utf-8').splitlines() if l.strip()]

class ProjectLedgerChecks(unittest.TestCase):
    def test_product_classification_uses_doc_relative_path(self):
        spec = importlib.util.spec_from_file_location('project_audit', ROOT / 'scripts/project_audit.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.classify('flac3d/zone/doc/manual/cmd_zone.create.html')[0], 'flac3d')
        self.assertEqual(mod.classify(ROOT / 'doc/3dec/block/doc/manual/cmd_block.create.html')[0], '3dec')
        self.assertEqual(mod.classify('pfc/pfcmodule/doc/manual/ball.html')[0], 'pfc')
        self.assertEqual(mod.classify('common/models/elastic/model.html')[0], 'common')
        s = json.loads((R / 'project_master_status.json').read_text(encoding='utf-8'))
        products = s['totals']['products']
        for key in ('flac3d', '3dec', 'pfc', 'common', 'other'):
            self.assertIn(key, products)
        self.assertEqual(sum(products.values()), s['totals']['html_pages'])
        self.assertLess(products['other'], s['totals']['html_pages'])

    def test_merge_dependency_is_explicit(self):
        s = json.loads((R / 'project_master_status.json').read_text(encoding='utf-8'))
        self.assertTrue(s['merge_dependency']['pr7_must_merge_first'])
        self.assertIn('重新生成', s['merge_dependency']['reason'])

    def test_master_status_consistent(self):
        s = json.loads((R / 'project_master_status.json').read_text(encoding='utf-8'))
        self.assertEqual(s['reviewed']['batch2_reviewed_count_exact'], 50)
        self.assertEqual(s['queue_size'], 50)
        self.assertEqual(s['history']['closed_stale_prs'], [4])
        self.assertEqual(s['totals']['html_pages'], 6577)

    def test_site_risk_index_counts_and_honest_semantic_status(self):
        rows = load_jsonl('site_risk_index.jsonl')
        self.assertEqual(len(rows), 6577)
        c = Counter(r['review_status'] for r in rows)
        self.assertEqual(c['reviewed_batch2_1_50'], 50)
        self.assertEqual(c['queued_batch2_51_100'], 50)
        for r in rows:
            self.assertNotIn('risk', r)
            self.assertEqual(r['severity_confirmed'], None)
            self.assertEqual(r['risk_basis'], 'heuristic_path_keywords')
            if r['review_status'] == 'not_reviewed':
                self.assertEqual(r['semantic_status'], 'unknown')

    def test_legacy_pending_not_cleared(self):
        t = (R / 'legacy_pending_review.md').read_text(encoding='utf-8')
        for name in ['fish_gp.accel.html', 'fish_zone.flux.html', 'fish_zone.face.pos.html']:
            self.assertIn(name, t)
        self.assertIn('继续', t)

if __name__ == '__main__':
    unittest.main()
