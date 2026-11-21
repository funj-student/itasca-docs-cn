import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_STATEMENTS = [
    'caseof - case - endcase', 'command - endcommand', 'define - end', 'exit',
    'global', 'if - else if - else - endif', 'local', 'lock',
    'loop - endloop - exit loop - continue', 'return',
    'section - endsection - exit section', 'struct - structure',
]


class MobileLayoutChecks(unittest.TestCase):
    def test_scan_and_browser_reports_exist_and_are_clean(self):
        cand = json.loads((ROOT / 'tests/mobile_layout_candidates.json').read_text(encoding='utf-8'))
        p1 = json.loads((ROOT / 'tests/mobile_layout_browser_p1_report.json').read_text(encoding='utf-8'))
        reg = json.loads((ROOT / 'tests/mobile_layout_browser_report.json').read_text(encoding='utf-8'))
        self.assertGreater(cand['total_pages'], 6500)
        self.assertGreater(cand['candidate_pages'], 0)
        self.assertEqual(p1['confirmed_checks'], 0)
        self.assertEqual(reg['confirmed_checks'], 0)

    def test_fish_table_content_and_links_preserved(self):
        path = ROOT / 'doc/common/docproject/source/manual/scripting/fish_scripting/fish_statements.html'
        text = path.read_text(encoding='utf-8')
        table = re.search(r'<table[^>]+id="tableoffishstatements".*?</table>', text, re.S)
        self.assertIsNotNone(table)
        body = table.group(0)
        self.assertEqual(len(re.findall(r'<tr\b', body)), 12)
        for statement in EXPECTED_STATEMENTS:
            self.assertIn(statement, body)
        self.assertEqual(len(re.findall(r'<a\s+class="reference internal"', body)), 12)

    def test_css_contains_targeted_fixes(self):
        css = (ROOT / 'doc/_static/itasca.css').read_text(encoding='utf-8')
        doxygen = (ROOT / 'doc/doxygen/html/doxygen.css').read_text(encoding='utf-8')
        self.assertIn('#tableoffishstatements', css)
        self.assertIn('max-width: 389px', css)
        self.assertIn('div.contents table', doxygen)
        self.assertIn('table.classindex', doxygen)
        self.assertNotIn('body { overflow-x: hidden; }', css)
        self.assertNotIn('body{overflow-x:hidden}', doxygen)

    def test_no_global_hiding_rules(self):
        for path in list((ROOT / 'doc/_static').glob('*.css')) + list((ROOT / 'doc/doxygen/html').glob('*.css')):
            text = path.read_text(encoding='utf-8', errors='ignore')
            self.assertIsNone(re.search(r'body\s*\{[^}]*overflow-x\s*:\s*hidden', text, re.S | re.I), str(path))
            self.assertIsNone(re.search(r'(?<![\w.\-#])table\s*\{[^}]*display\s*:\s*block', text, re.S | re.I), str(path))

    def test_all_tables_get_scroll_wrapper(self):
        js = (ROOT / 'doc/_static/icgscripts.js').read_text(encoding='utf-8')
        self.assertIn("main.querySelectorAll('table')", js)
        self.assertIn("document.querySelector('div.contents')", js)

if __name__ == '__main__':
    unittest.main()
