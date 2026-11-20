import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def raw(rel):
    return (ROOT / 'doc' / rel).read_text(encoding='utf-8', errors='ignore')

def visible(rel):
    t = raw(rel)
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()

class TranslationBatch2Sub34Checks(unittest.TestCase):
    def test_fish_automatic_create_command(self):
        t = visible('flac3d/docproject/source/modeling/tutorials/basicclifish.html')
        self.assertIn('fish automatic-create', t)
        self.assertNotIn('fish auto-create', t)

    def test_thermal_advection_warning_present(self):
        t = visible('flac3d/docproject/source/options/thermalanalysis/thermal/numerical-form.html')
        self.assertIn('FLAC3D 采用的显式时步对平流逻辑并非无条件稳定', t)

    def test_block_initialize_rvelocity_family(self):
        t = raw('3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.initialize.html')
        for suffix in ['rvelocity', 'rvelocity-x', 'rvelocity-y', 'rvelocity-z']:
            self.assertIn(f'id="kwd:block.initialize.{suffix}"', t)

    def test_block_generate_primary_keywords(self):
        t = raw('3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.generate.html')
        line = next(l for l in t.splitlines() if '<p class="last">' in l and 'block.generate.from-vrml' in l)
        for token in ['from-vrml', 'from-geometry', 'from-topography', 'voronoi']:
            self.assertIn(token, line)
        for token in ['break-angle', 'geometry-set', 'ratio', 'segments']:
            self.assertNotIn(token, line)

    def test_rayleigh_damping_semantics(self):
        t = visible('3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.mechanical.html')
        self.assertIn('将阻尼限制为仅与质量成比例', t)
        self.assertIn('将阻尼限制为仅与刚度成比例', t)
        self.assertNotIn('将质量阻尼项设为 0', t)
        self.assertNotIn('将刚度阻尼项设为 0', t)
        self.assertNotIn('bcmass', t)

    def test_pfc_parameter_labels(self):
        t = visible('pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.tractions.html')
        self.assertIn('x 方向周期性', t)
        self.assertIn('y 方向周期性', t)
        self.assertIn('z 方向周期性', t)
        self.assertIn('y 方向比值系数', t)
        m = visible('pfc/pfcmodule/doc/manual/measure_manual/command_reference/cmd_measure/cmd_measure.create.html')
        self.assertIn('浮点值上限（fh）', m)
        self.assertNotIn('高度系数（fh）', m)

    def test_escaping_the_box(self):
        t = visible('pfc/docproject/source/manual/examples/tutorials/generating_a_bonded_assembly/generating_a_bonded_assembly.html')
        self.assertIn('也不逸出盒子（容器）', t)
        self.assertNotIn('也不产生显著运动', t)

    def test_search_index_synced(self):
        t = (ROOT / 'doc/_static/zh-search-data.js').read_text(encoding='utf-8')
        self.assertIn('fish automatic-create', t)
        self.assertIn('也不逸出盒子（容器）', t)
        self.assertIn('浮点值上限（fh）', t)

if __name__ == '__main__':
    unittest.main()
