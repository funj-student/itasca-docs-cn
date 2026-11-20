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

    def test_high_frequency_queries_return_nonempty_results(self):
        for q in self.report['query_checks']:
            self.assertTrue(q['top'], q['query'])
        self.assertGreaterEqual(self.report['query_pass_count'], 6)

if __name__ == '__main__':
    unittest.main()
