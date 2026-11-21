import importlib.util
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'translation_review'
sys.path.insert(0, str(ROOT / 'scripts'))
from review_status import build_review_status_map, summarize


def load_jsonl(name):
    return [json.loads(l) for l in (R / name).read_text(encoding='utf-8').splitlines() if l.strip()]


class ProjectLedgerChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = json.loads((R / 'project_master_status.json').read_text(encoding='utf-8'))
        cls.page_list = load_jsonl('batch2/page_list.jsonl')
        cls.review_map = build_review_status_map(cls.page_list)
        cls.review_summary = summarize(cls.review_map)

    def test_product_classification_uses_doc_relative_path(self):
        spec = importlib.util.spec_from_file_location('project_audit', ROOT / 'scripts/project_audit.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.classify('flac3d/zone/doc/manual/cmd_zone.create.html')[0], 'flac3d')
        self.assertEqual(mod.classify(ROOT / 'doc/3dec/block/doc/manual/cmd_block.create.html')[0], '3dec')
        self.assertEqual(mod.classify('pfc/pfcmodule/doc/manual/ball.html')[0], 'pfc')
        self.assertEqual(mod.classify('common/models/elastic/model.html')[0], 'common')
        products = self.status['totals']['products']
        for key in ('flac3d', '3dec', 'pfc', 'common', 'other'):
            self.assertIn(key, products)
        self.assertEqual(sum(products.values()), self.status['totals']['html_pages'])
        self.assertLess(products['other'], self.status['totals']['html_pages'])

    def test_status_derived_from_actual_evidence_files(self):
        self.assertEqual(self.review_summary['reviewed_pages'], len(self.page_list))
        self.assertEqual(self.review_summary['unreviewed_pages'], 0)
        for path, info in self.review_map.items():
            self.assertEqual(info['review_status'], 'completed_ai_review_report')
            self.assertEqual(info['status_label'], '已完成本批 AI 审校报告')
            self.assertFalse(info['full_text_confirmed'])
            self.assertIn(info['evidence_status'], {'partial_evidence_backed', 'report_only'})
            if info['evidence_status'] == 'report_only':
                self.assertEqual(info['evidence_ids'], [])

    def test_pr7_additions_in_ledger(self):
        pr7 = self.status['pr7_integration']
        self.assertEqual(pr7['confirmed_count'], 10)
        self.assertEqual(pr7['pending_count'], 8)
        self.assertEqual(len(pr7['confirmed_ids']), 10)
        self.assertEqual(len(pr7['pending_records']), 8)
        self.assertEqual(self.status['merge_dependency']['pr7_merged'], True)
        self.assertEqual(self.status['base_commit'], 'd28ea7fec82f2131de4df36b177168d85bbbae49')

    def test_master_status_consistent(self):
        reviewed = self.status['reviewed']
        self.assertEqual(reviewed['batch2_report_reviewed_count'], self.review_summary['reviewed_pages'])
        self.assertEqual(reviewed['batch2_unreviewed_count'], self.review_summary['unreviewed_pages'])
        self.assertEqual(reviewed['batch2_evidence_backed_pages'], self.review_summary['evidence_backed_pages'])
        self.assertEqual(reviewed['batch2_report_only_pages'], self.review_summary['report_only_pages'])
        self.assertFalse(reviewed['full_text_confirmed_claim'])
        self.assertEqual(self.status['queue_size'], self.review_summary['unreviewed_pages'])
        self.assertEqual(self.status['pending']['count'], 23)
        self.assertNotIn('batch2_reviewed_count_exact', reviewed)
        self.assertEqual(self.status['history']['closed_stale_prs'], [4])

    def test_site_risk_index_counts_and_honest_semantic_status(self):
        rows = load_jsonl('site_risk_index.jsonl')
        c = Counter(r['review_status'] for r in rows)
        self.assertEqual(len(rows), self.status['totals']['html_pages'])
        self.assertEqual(c['completed_ai_review_report'], self.review_summary['reviewed_pages'])
        self.assertEqual(c['not_reviewed'], len(rows) - c['completed_ai_review_report'])
        for r in rows:
            self.assertNotIn('risk', r)
            self.assertNotIn(r['review_status'], {'reviewed_batch2_1_50', 'queued_batch2_51_100'})
            self.assertEqual(r['severity_confirmed'], None)
            self.assertEqual(r['risk_basis'], 'heuristic_path_keywords')
            self.assertFalse(r['full_text_confirmed'])
            if r['review_status'] == 'not_reviewed':
                self.assertEqual(r['semantic_status'], 'unknown')

    def test_legacy_pending_not_cleared(self):
        t = (R / 'legacy_pending_review.md').read_text(encoding='utf-8')
        for name in ['fish_gp.accel.html', 'fish_zone.flux.html', 'fish_zone.face.pos.html']:
            self.assertIn(name, t)
        self.assertIn('继续', t)

    def test_pr8_overlap_is_recorded(self):
        t = (R / 'pr8_conflict_check.md').read_text(encoding='utf-8')
        self.assertIn('doc/search.html', t)
        self.assertIn('doc/_static/zh-search.js', t)
        self.assertIn('未修改', t)

if __name__ == '__main__':
    unittest.main()
