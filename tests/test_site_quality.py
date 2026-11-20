import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class SiteQualityChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'translation_review/site_quality_report.json').read_text(encoding='utf-8'))

    def test_readme_page_count_matches_audit(self):
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('6,577 个 HTML', text)
        self.assertEqual(self.report['html_pages'], 6577)

    def test_search_index_missing_pages_are_non_content(self):
        for path in self.report['search_missing_content_pages']:
            self.assertTrue(path.startswith('doxygen/') or 'dynamic_calculations.html' in path, path)

    def test_sitemap_has_no_search_page_and_no_stale_doc_entries(self):
        sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
        self.assertNotIn('/doc/search.html', sitemap)
        self.assertEqual(self.report['sitemap_stale_doc_entries'], [])

    def test_search_page_is_noindex_and_contents_has_canonical(self):
        search = (ROOT / 'doc/search.html').read_text(encoding='utf-8')
        self.assertIn('noindex,follow', search)
        contents = (ROOT / 'doc/contents.html').read_text(encoding='utf-8')
        self.assertIn('rel="canonical"', contents)
        self.assertIn('name="description"', contents)

    def test_actual_zh_search_queries_are_relevant(self):
        checks = [q for q in self.report['query_checks'] if q['engine'] == 'zh-search.js actual']
        self.assertEqual(len(checks), 10)
        for q in checks:
            self.assertTrue(q['results_relevant'], q['query'])
        self.assertEqual(self.report['summary']['zero_match_correct'], 1)
        zero = next(q for q in checks if q['kind'] == 'zero_match')
        self.assertEqual(zero['count'], 0)
        exclusion = next(q for q in checks if q['kind'] == 'exclusion')
        self.assertTrue(exclusion['negative'])
        self.assertIn('expected_in_top5', self.report['summary'])

    def test_english_queries_are_marked_unverified(self):
        english = [q for q in self.report['query_checks'] if q['kind'] == 'english']
        self.assertEqual(len(english), 3)
        for q in english:
            self.assertIsNone(q['has_results'])
            self.assertIn('未验证', q['limitation'])

    def test_unindexed_stub_pages_have_assessment(self):
        notes = self.report['unindexed_page_assessment']
        for path in notes:
            self.assertTrue(notes[path])
        self.assertIn('dynamic_calculations.html', ' '.join(notes.keys()))
        self.assertIn('class_variant_1_1_user_type_base.html', ' '.join(notes.keys()))

if __name__ == '__main__':
    unittest.main()
