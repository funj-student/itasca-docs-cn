import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def raw(rel):
    return (ROOT / rel).read_text(encoding='utf-8', errors='ignore')

def visible(rel):
    t = raw(rel)
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()

class TranslationBatch2Sub2Checks(unittest.TestCase):
    def test_strength_stress_ratio_keyword(self):
        for name in ('cmd_zone.history.html', 'cmd_zone.list.html'):
            rel = f'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/{name}'
            t = raw(rel)
            self.assertIn('strength-stress-ratio', t)
            self.assertNotIn('stress-strength-ratio', t)

    def test_dynamic_damping_examples_and_note(self):
        rel = 'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html'
        t = visible(rel)
        self.assertEqual(t.count('对于目标 0.05（5%）的阻尼比，输入值应为'), 2)
        self.assertNotIn('默认阻尼值为 0.8', t)
        self.assertIn('数值稳定所需的临界时步将自动减小', t)
        self.assertIn('model dynamic timestep', t)

    def test_relax_delete_behavior(self):
        rel = 'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.relax.html'
        t = visible(rel)
        self.assertIn('如果折减因子已达到 0，则材料已被置空', t)
        self.assertIn('无需再次删除', t)

    def test_material_properties_table_friction(self):
        rel = 'doc/flac3d/docproject/source/modeling/problemsolving/material_properties.html'
        t = raw(rel)
        self.assertIn('<span class="pre">table-friction</span>', t)
        self.assertNotIn('<span class="pre">ftable</span>', t)

    def test_identifyingregions_constitute(self):
        rel = 'doc/flac3d/docproject/source/modeling/problemsolving/identifyingregions.html'
        t = visible(rel)
        self.assertIn('返回构成模型外边界的这组面上已赋的分组名', t)
        self.assertNotIn('本构模型外边界', t)

    def test_search_index_updates(self):
        t = raw('doc/_static/zh-search-data.js')
        self.assertIn('strength-stress-ratio', t)
        self.assertNotIn('stress-strength-ratio', t)
        self.assertIn('table-friction', t)
        self.assertIn('返回构成模型外边界的这组面上已赋的分组名', t)

if __name__ == '__main__':
    unittest.main()
