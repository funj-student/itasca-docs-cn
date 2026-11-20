import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('review_translation_batch', ROOT / 'scripts/review_translation_batch.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class ReviewAlignmentChecks(unittest.TestCase):
    def test_empty_signatures_are_not_paired(self):
        en = [((), ()), ((), ()), ((), ())]
        zh = [((), ()), ((), ()), ((), ())]
        self.assertEqual(module.align_pairs(en, zh), [])

    def test_nonempty_matching_signature_is_paired(self):
        en = [((), ()), (('1e5',), ('zone.face.apply',)), ((), ())]
        zh = [((), ()), (('1e5',), ('zone.face.apply',)), ((), ())]
        self.assertEqual(module.align_pairs(en, zh), [(1, 1)])

    def test_signature_tokens_ignore_plain_prose(self):
        en_sig = module.signature_tokens('This sentence has no numbers or command names.')
        zh_sig = module.signature_tokens('这句话没有数字或命令名。')
        self.assertEqual(en_sig, ((), ()))
        self.assertEqual(zh_sig, ((), ()))

    def test_semantic_alignment_uses_section_and_concepts(self):
        en = [{'text': 'The stress and strain state is shown.', 'section': 's1', 'headings': ('', 'State', '', '')}]
        zh = [{'text': '图中显示应力和应变状态。', 'section': 's1', 'headings': ('', '状态', '', '')}]
        pairs = module.semantic_align(en, zh, [])
        self.assertEqual([(e, z) for e, z, _ in pairs], [(0, 0)])

    def test_semantic_alignment_rejects_different_sections(self):
        en = [{'text': 'The stress and strain state is shown.', 'section': 's1', 'headings': ('', 'State', '', '')}]
        zh = [{'text': '图中显示应力和应变状态。', 'section': 's2', 'headings': ('', 'State', '', '')}]
        self.assertEqual(module.semantic_align(en, zh, []), [])

    @staticmethod
    def parse_html(html):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'sample.html'
            p.write_text(html, encoding='utf-8')
            return module.blocks_with_context(p)

    def test_real_html_heading_levels_and_nesting(self):
        blocks = self.parse_html('''
        <html><body><div id="s1">
          <h1>Manual Title</h1>
          <h2>State Section</h2>
          <p>The <span>stress</span> and <em>strain</em> state is shown here.</p>
          <h3>Detail</h3>
          <p>More detailed temperature and pressure notes are given.</p>
          <h2>Other Section</h2>
          <p>Velocity and displacement values are listed below.</p>
        </div></body></html>
        ''')
        texts = [b['text'] for b in blocks]
        self.assertIn('The stress and strain state is shown here.', texts)
        self.assertIn('More detailed temperature and pressure notes are given.', texts)
        p1 = next(b for b in blocks if b['text'].startswith('The stress'))
        p2 = next(b for b in blocks if b['text'].startswith('More detailed'))
        p3 = next(b for b in blocks if b['text'].startswith('Velocity'))
        self.assertEqual(p1['headings'][:3], ('Manual Title', 'State Section', ''))
        self.assertEqual(p2['headings'][:3], ('Manual Title', 'State Section', 'Detail'))
        self.assertEqual(p3['headings'][:3], ('Manual Title', 'Other Section', ''))

    def test_real_html_sections_are_isolated(self):
        blocks = self.parse_html('''
        <html><body>
          <div id="sec-a"><h2>Stress</h2><p>The stress and strain state is shown.</p></div>
          <div id="sec-b"><h2>Stress</h2><p>The stress and strain state is shown.</p></div>
        </body></html>
        ''')
        paras = [b for b in blocks if b['text'].startswith('The stress')]
        self.assertEqual(len(paras), 2)
        self.assertEqual(paras[0]['section'], 'sec-a')
        self.assertEqual(paras[1]['section'], 'sec-b')
        self.assertEqual(module.semantic_align([paras[0]], [paras[1]], []), [])

if __name__ == '__main__':
    unittest.main()
