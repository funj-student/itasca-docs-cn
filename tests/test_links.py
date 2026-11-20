import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'scripts' / 'check_links.py'


class LinkChecks(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.site = Path(temp.name)

    def write(self, name, text=''):
        path = self.site / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def check(self, expected_code, *args):
        result = subprocess.run(
            [sys.executable, str(CHECKER), str(self.site), *args],
            capture_output=True, text=True, encoding='utf-8',
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
        )
        self.assertEqual(result.returncode, expected_code, result.stdout + result.stderr)
        return result.stdout

    def test_same_page_and_cross_page_fragments(self):
        self.write('docs/a.html', """
            <h2 ID='中文&amp;图'></h2><a NAME=legacy></a>
            <a href='#%E4%B8%AD%E6%96%87%26%E5%9B%BE'>encoded</a>
            <a href='?view=1#legacy'>query</a> <a href=#TOP>top</a>
            <a href=b.html#later>forward</a>
            <a href="#missing">broken</a><a href="b.html#legacy">wrong page</a>
            <!-- <a href='#comment'> --> <script>const s = '<a href="#js">';</script>
        """)
        self.write('docs/b.html', '<p id=later></p><a href="a.html#legacy">back</a>')
        output = self.check(1)
        self.assertIn('pages=2 missing_files=0 missing_anchors=2', output)
        self.assertIn('docs/a.html:6: missing anchor: #missing', output)
        self.assertIn('missing anchor: b.html#legacy', output)

    def test_html_assets_and_srcset(self):
        self.write('index.html', """
            <link href=site.css rel=stylesheet><script src="app.js?v=2"></script>
            <img src='plot%201.png' srcset='small.png 1x, large.png 2x'>
            <picture><source srcset="data:image/png;base64,AA== 1x, high.png 2x"></picture>
            <video poster=p.jpg><source src=movie.mp4><track src=captions.vtt></video>
            <audio src=sound.ogg></audio><iframe src=frame.html></iframe>
            <object data=manual.pdf></object><embed src=model.svg>
            <link rel=preload imagesrcset="first.png, next.png">
            <img src="https://cdn.example/remote.png"><script src="//cdn.example/app.js"></script>
            <a href=mailto:docs@example.org>email</a><img src=data:image/png;base64,AA==>
        """)
        missing = ('site.css', 'app.js?v=2', 'plot%201.png', 'small.png', 'large.png',
                   'high.png', 'p.jpg', 'movie.mp4', 'captions.vtt', 'sound.ogg',
                   'frame.html', 'manual.pdf', 'model.svg', 'first.png', 'next.png')
        output = self.check(1)
        self.assertIn(f'missing_files={len(missing)} missing_anchors=0', output)
        for url in missing:
            self.assertIn(f'missing file: {url}\n', output)
        for url in missing:
            self.write(unquote(url.split('?')[0]))
        self.assertIn('missing_files=0 missing_anchors=0', self.check(0))

    def test_css_references_and_imports(self):
        self.write('index.html', """
            <style>.a { background: url('inline.png') }</style>
            <div style="background:url(attr.png)"></div>
        """)
        self.write('styles/main.css', """
            @import "theme.css" screen;
            @import url('print.css');
            .a { background: linear-gradient(white, black), url(../images/plot.svg#view) }
            @font-face { src: url("my font.woff2?v=1") }
            /* url(comment.png) */
            .b::after { content: "url(string.png)"; filter: url(#shadow) }
        """)
        self.write('styles/print.css')
        self.write('images/plot.svg')
        output = self.check(1)
        self.assertIn('missing_files=4 missing_anchors=0', output)
        self.assertIn('styles/main.css:2: missing file: theme.css', output)
        for name in ('inline.png', 'attr.png', 'styles/theme.css', 'styles/my font.woff2'):
            self.write(name)
        self.check(0)

    def test_pages_paths_and_directory_indexes(self):
        self.write('guide/index.html', '<h1 id=ok></h1>')
        self.write('nested/page.html', """
            <base href='../guide/'>
            <a href='./#ok'>index</a>
            <a href='/itasca-docs-cn/guide#ok'>project path</a>
            <a href='https://funj-student.github.io/itasca-docs-cn/guide/#ok'>canonical</a>
            <a href='https://funj-student.github.io/another-project/'>other site</a>
            <a href='../empty/'>empty</a>
            <img src='Index.html'><img src='/guide/wrong-root.png'>
        """)
        (self.site / 'empty').mkdir()
        output = self.check(1)
        self.assertIn('missing_files=3 missing_anchors=0', output)
        for url in ('../empty/', 'Index.html', '/guide/wrong-root.png'):
            self.assertIn(f'missing file: {url}\n', output)

    def test_mobile_stylesheet_emitted_by_the_theme(self):
        self.write('doc/index.html', """<script>
            document.write('<link rel="stylesheet" href="_static/mobile.css" />')
            document.write('<link rel="stylesheet" href="file:///C:/old/site.css" />')
        </script>""")
        output = self.check(1)
        self.assertIn('doc/index.html:2: missing file: _static/mobile.css', output)
        self.assertIn('doc/index.html:3: missing file: file:///C:/old/site.css', output)

    def test_known_missing_is_exact_counted_and_retires_when_fixed(self):
        self.write('known.json', json.dumps([{'page': 'a.html', 'url': 'figure.*'}]))
        args = ('--known-missing', str(self.site / 'known.json'))
        self.write('a.html', '<img src="figure.*">')
        self.check(1)  # The default scan is strict.
        self.assertIn('known_missing_files=1', self.check(0, *args))
        self.write('a.html', '<img src="figure.*"><img src="figure.*"><img src="figure.png">')
        self.write('b.html', '<img src="figure.*">')
        self.assertIn('missing_files=4 missing_anchors=0 known_missing_files=1', self.check(1, *args))
        self.write('a.html', '<img src="fixed.png">')
        self.write('fixed.png')
        self.write('b.html')
        self.assertIn('stale known-missing entry', self.check(1, *args))


if __name__ == '__main__':
    unittest.main()
