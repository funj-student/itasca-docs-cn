import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FISH = ROOT / 'doc/flac3d/zone/doc/manual/zone_manual/zone_fish'

def raw(rel):
    return (ROOT / rel).read_text(encoding='utf-8', errors='ignore')

def visible(rel):
    t = raw(rel)
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()

class TranslationBatch2Sub1Checks(unittest.TestCase):
    def test_zone_flux_component_terms(self):
        rel = 'doc/flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.flux.html'
        t = visible(rel)
        for c in 'xyz':
            self.assertIn(f'网格单元平均热通量向量的 {c} 分量', t)
            self.assertNotIn(f'网格单元通量向量的 {c} 分量', t)
        self.assertNotIn('获取网格单元通量的', t)

    def test_gp_vel_component_terms(self):
        rel = 'doc/flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.vel.html'
        t = visible(rel)
        for c in 'xyz':
            self.assertIn(f'速度向量的 \\({c}\\) 分量', t)
            self.assertNotIn(f'{c} 分量速度向量', t)

    def test_plane_traction_no_contextual_expansion(self):
        rel = 'doc/flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.plane.traction.html'
        t = visible(rel)
        self.assertIn('参数数组（arr）', t)
        self.assertNotIn('裂隙参数数组', t)

    def test_search_index_updates(self):
        t = raw('doc/_static/zh-search-data.js')
        self.assertIn('网格单元平均热通量向量的 \\\\(x\\\\) 分量', t)
        self.assertIn('速度矢量的 x 分量', t)
        self.assertIn('参数数组（arr）', t)
        self.assertNotIn('裂隙参数数组', t)

if __name__ == '__main__':
    unittest.main()
