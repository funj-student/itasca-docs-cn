import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github' / 'workflows'


def workflow(name):
    # BaseLoader keeps the Actions trigger key "on" as a string.
    return yaml.load((WORKFLOWS / name).read_text(encoding='utf-8'), Loader=yaml.BaseLoader)


class PagesChecks(unittest.TestCase):
    def test_quality_gates_artifact_and_deployment(self):
        jobs = workflow('deploy-pages.yml')['jobs']
        self.assertEqual(jobs['quality']['uses'], './.github/workflows/term-check.yml')
        self.assertEqual(jobs['build']['needs'], 'quality')
        self.assertEqual(jobs['deploy']['needs'], 'build')
        triggers = workflow('term-check.yml')['on']
        self.assertIn('workflow_call', triggers)
        self.assertIn('main', triggers['pull_request']['branches'])

    def test_glossary_build_matches_published_page(self):
        with TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / 'scripts').mkdir()
            for name in ('scripts/generate_glossary.py', '术语词库.md', 'disclaimer.html'):
                shutil.copyfile(ROOT / name, site / name)
            subprocess.run([sys.executable, str(site / 'scripts/generate_glossary.py')], check=True)
            self.assertEqual((site / 'glossary.html').read_text(encoding='utf-8'),
                             (ROOT / 'glossary.html').read_text(encoding='utf-8'))

    def test_runtime_search_indexes_are_shipped(self):
        # The English and Chinese loaders request these by name at runtime.
        for path in ('doc/searchindex.js', 'doc/_static/zh-search-data.js'):
            with self.subTest(path=path):
                self.assertGreater((ROOT / path).stat().st_size, 0)
