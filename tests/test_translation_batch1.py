import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def text(rel):
    return (ROOT / rel).read_text(encoding='utf-8', errors='ignore')

def visible(rel):
    raw = text(rel)
    raw = re.sub(r'<script.*?</script>', ' ', raw, flags=re.S | re.I)
    raw = re.sub(r'<style.*?</style>', ' ', raw, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', raw)).strip()

class TranslationBatch1Checks(unittest.TestCase):
    def test_initialize_prerequisites(self):
        t = text('doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.initialize.html')
        self.assertEqual(t.count('本命令应在指定本构模型之后使用。'), 2)

    def test_initialize_stresses_fixes(self):
        t = text('doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.initialize-stresses.html')
        self.assertIn('本命令应在指定本构模型、设置重力和材料密度之后使用。', t)
        self.assertIn('y 向应力比', t)
        self.assertNotIn('y 向尺寸', t)

    def test_apply_notes(self):
        t = text('doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.apply.html')
        self.assertIn('此关键字仅在热模型选项（thermal model option）下可用。', t)
        self.assertIn('必须已存在流体流动模型，此命令才有效。', t)

    def test_gridpoint_fix_keyword_block(self):
        t = text('doc/flac3d/zone/doc/manual/zone_manual/zone_commands/zonegridpoint/cmd_zone.gridpoint.fix.html')
        self.assertIn('id="gridpointfixblock"', t)
        self.assertGreaterEqual(t.count('[gridpointfixblock]'), 16)
        for key in ('id="kwd:add"', 'id="kwd:multiply"', 'id="kwd:gradient"', 'id="kwd:vary"'):
            self.assertIn(key, t)

    def test_gridpoint_free_cross_reference(self):
        t = text('doc/flac3d/zone/doc/manual/zone_manual/zone_commands/zonegridpoint/cmd_zone.gridpoint.free.html')
        self.assertIn('to that for  zone.gridpoint.fix', t)
        self.assertNotIn('to that for  zone.gridpoint.free', t)

    def test_boundary_examples(self):
        t = visible('doc/flac3d/docproject/source/modeling/problemsolving/boundary_conditions.html')
        self.assertIn('stress-xx -1e5 servo ramp range group', t)
        self.assertIn('fish apply range group', t)
        self.assertIn("table 'ramp' time dynamic", t)
        self.assertNotIn('采用卸荷时', t)

    def test_input_fixes(self):
        t = text('doc/flac3d/docproject/source/theory/fluid-mechanical/input/input.html')
        self.assertIn('用平均的基于网格点的孔隙压力自动初始化', t)
        self.assertIn('单元平均流量（<code class="xref fish fish-func docutils literal"><span class="pre">zone.flux</span></code>）', t)
        self.assertNotIn('单元平均热通量（<code class="xref fish fish-func docutils literal"><span class="pre">zone.flux</span></code>）', t)

    def test_initial_conditions_formula(self):
        t = text('doc/flac3d/docproject/source/modeling/problemsolving/initial_conditions.html')
        self.assertIn('\\(ν/(1-ν)\\)', t)
        self.assertNotIn('\\(ν/(1-\\ν)\\)', t)

    def test_hoek_fixes(self):
        t = text('doc/common/models/hoek/doc/modelhoek.html')
        self.assertIn('{{N_{\\phi_c} -1} \\over {N_{\\phi_c} +1}}', t)
        self.assertIn('id="kwd:hoek-brown.table-mb"', t)
        self.assertIn('L_c/\\sqrt[3]{V_z}', t)
        self.assertNotIn('id="kwd:hoek-brown.table-m">', t)

    def test_property_distribution_fixes(self):
        t = text('doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.property-distribution.html')
        self.assertIn('<span class="cmdkey">[property]</span>', t)
        self.assertIn('<span class="varfloat">fvalue</span>', t)
        self.assertIn('cohesion </span><span class="m m-Double">600</span>', t)
        self.assertIn('均值为 600、标准差为 10 的黏聚力高斯分布', t)

    def test_cmodel_fixes(self):
        t = text('doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.cmodel.html')
        self.assertIn('modelname007.dll', t)
        self.assertIn('<span class="pre">plugins</span>', t)
        self.assertIn('热-力耦合分析', t)
        self.assertNotIn('modelname006.dll', t)
        self.assertNotIn('热力学分析', t)

    def test_search_index_updates(self):
        t = text('doc/_static/zh-search-data.js')
        for phrase in ('本命令应在指定本构模型之后使用', '本命令应在指定本构模型、设置重力和材料密度之后使用',
                       'y 向应力比', '采用松弛开挖时', '热-力耦合分析', 'table-mb s'):
            self.assertIn(phrase, t)

if __name__ == '__main__':
    unittest.main()
