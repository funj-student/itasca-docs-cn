"""缓存失效构建（scripts/build_site.py）的自动化测试。

覆盖任务要求的十个验收点：
1.  构建前后 HTML 正文内容逐字节不变（剥离 v= 参数后与源文件一致，含 CRLF）。
2.  所有版本化本地 CSS/JS 引用都指向存在的文件。
3.  文件内容变化时版本号同步变化。
4.  文件内容不变时版本号保持稳定（两次构建产物完全一致）。
5.  多层相对路径解析正确。
6.  MathJax.js 的既有查询参数（?config=…）保留且用 & 拼接版本号。
7.  引用保持相对形式，不引入绝对路径（GitHub Pages 子路径 /itasca-docs-cn/ 兼容）。
8.  搜索索引与目录页面的特殊加载点被正确改写。
9.  重复构建幂等：不叠加版本号。
10. 外部 CDN、普通文档链接、缺失目标的引用一律不改写。
"""

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'scripts' / 'build_site.py'

REF_RE = re.compile(r'((?:href|src)\s*=\s*")([^"*?#:]*?)(\.(?:css|js))(\?[^"]*)?(")')


def read_exact(path):
    """按 UTF-8 读取且不转换换行符（兼容 Python < 3.13 的 Path.read_text）。"""
    with open(path, 'r', encoding='utf-8', newline='') as fh:
        return fh.read()


def build(source: Path, output: Path, manifest: Path | None = None):
    cmd = [sys.executable, str(BUILDER), '--source', str(source), '--output', str(output)]
    if manifest:
        cmd += ['--manifest', str(manifest)]
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding='utf-8',
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
    )
    return result


class Fixture:
    """构造一个覆盖各种引用形态的迷你站点。"""

    def __init__(self, base: Path):
        self.base = base
        self.src = base / 'src'
        self.make_fixture()

    def write_bytes(self, rel: str, data: bytes):
        path = self.src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def write(self, rel: str, text: str):
        # 全站约定为 CRLF，与真实仓库一致；先归一化避免重复 CR。
        normalized = text.replace('\r\n', '\n').replace('\n', '\r\n')
        self.write_bytes(rel, normalized.encode('utf-8'))

    def make_fixture(self):
        self.write('.nojekyll', '')
        self.write('robots.txt', 'User-agent: *\n')
        self.write('notes.md', '# 说明\n')
        self.write('package.json', '{}')          # 应被排除
        self.write('scripts/keep.py', 'x = 1\n')  # scripts/ 目录应被排除
        self.write('tests/keep.js', 'var x;\n')   # tests/ 目录应被排除

        self.write('index.html', (
            '<!DOCTYPE html><html><head>\r\n'
            '<link href="doc/_static/itasca.css" rel="stylesheet">\r\n'
            '<link href="doc/_static/pygments.css" rel="stylesheet">\r\n'
            '<script src="doc/_static/MathJax/MathJax.js?config=TeX-AMS_SVG"></script>\r\n'
            '<script src="doc/_static/icgscripts.js"></script>\r\n'
            '</head><body><a href="notes.md">说明</a></body></html>\r\n'
        ))
        self.write('about.html', '<a href="notes.md">notes</a>\r\n')
        # 外部 CDN 与缺失目标：不得改写。
        self.write('external.html', (
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.2/MathJax.js?config=TeX-MML-AM_CHTML"></script>\r\n'
            '<script src="http://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>\r\n'
            '<link href="missing.css" rel="stylesheet">\r\n'
            '<a href="doc/search.html">搜索</a>\r\n'
        ))
        # 多层相对路径（doc/flac3d/deep/ -> doc/_static/）。
        self.write('doc/flac3d/deep/page.html', (
            '<link href="../../_static/itasca.css" rel="stylesheet">\r\n'
            '<script src="../../_static/icgscripts.js"></script>\r\n'
        ))
        # 目录 iframe 页（jstree 主题样式）。
        self.write('doc/navtree.html', (
            '<link href="_static/jstree/themes/default/style.min.css" rel="stylesheet">\r\n'
            '<script src="_static/jstree/jstree.min.js"></script>\r\n'
        ))
        # 搜索页：HTML 属性引用 + Search.loadIndex 动态加载。
        self.write('doc/search.html', (
            '<link href="_static/itasca.css" rel="stylesheet">\r\n'
            '<script src="_static/searchtools.js"></script>\r\n'
            '<script src="_static/zh-search.js"></script>\r\n'
            '<script>jQuery(function() { Search.loadIndex("searchindex.js"); });</script>\r\n'
        ))
        # 中文搜索脚本：动态加载 zh-search-data.js（锚点改写目标）。
        self.write('doc/_static/zh-search.js', (
            "const ownURL = document.currentScript.src;\r\n"
            "script.src = new URL('zh-search-data.js', ownURL).href;\r\n"
        ))
        # Doxygen 风格页面：同目录与子目录引用。
        self.write('doc/doxygen/html/api.html', (
            '<link href="doxygen.css" rel="stylesheet">\r\n'
            '<link href="tabs.css" rel="stylesheet">\r\n'
            '<script src="menu.js"></script>\r\n'
        ))
        self.write('doc/doxygen/html/search/all_0.html',
                   '<link href="search.css" rel="stylesheet">\r\n'
                   '<script src="search.js"></script>\r\n'
                   '<script src="variables_0.js"></script>\r\n')

        # 静态资源本体。
        self.write('doc/_static/itasca.css', 'body { color: #333; }\n')
        self.write('doc/_static/pygments.css', '.k { color: #007020; }\n')
        self.write('doc/_static/icgscripts.js', 'window.ItascaNav = {};\n')
        self.write('doc/_static/searchtools.js', 'window.Search = {};\n')
        self.write('doc/_static/MathJax/MathJax.js', 'module MathJax;\n')
        self.write('doc/_static/jstree/jstree.min.js', 'jstree;\n')
        self.write('doc/_static/jstree/themes/default/style.min.css', '.jstree{}\n')
        self.write('doc/_static/zh-search-data.js', 'window.FLAC_ZH_SEARCH_DATA={pages:[]};\n')
        self.write('doc/searchindex.js', 'Search.setIndex({});\n')
        self.write('doc/doxygen/html/doxygen.css', 'body{}\n')
        self.write('doc/doxygen/html/tabs.css', '.tabs{}\n')
        self.write('doc/doxygen/html/menu.js', 'menu;\n')
        self.write('doc/doxygen/html/search/search.css', '.s{}\n')
        self.write('doc/doxygen/html/search/search.js', 's;\n')
        self.write('doc/doxygen/html/search/variables_0.js', 'v;\n')

    def built(self, rel: str) -> str:
        return read_exact(self.base / 'build' / rel)


class BuildCacheBusting(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.fx = Fixture(Path(temp.name))

    def run_build(self, output_name='build'):
        out = self.fx.base / output_name
        result = build(self.fx.src, out)
        self.assertEqual(result.returncode, 0, result.stderr)
        return out

    # 1. HTML 正文内容零变化 -------------------------------------------------
    def test_html_content_preserved_byte_exact(self):
        self.run_build()
        for html in self.fx.src.rglob('*.html'):
            rel = html.relative_to(self.fx.src).as_posix()
            built = (self.fx.base / 'build' / rel).read_bytes()
            stripped = re.sub(rb'[?&]v=[0-9a-f]{8,16}', b'', built)
            self.assertEqual(stripped, html.read_bytes(), f'{rel} 内容被改动')

    def test_crlf_line_endings_preserved(self):
        self.run_build()
        built = (self.fx.base / 'build' / 'index.html').read_bytes()
        self.assertIn(b'\r\n', built)  # CRLF 保留，未被转换为 LF

    # 2. 版本化引用均有效 ----------------------------------------------------
    def test_versioned_references_resolve(self):
        build_dir = self.run_build()
        checked = 0
        for html in build_dir.rglob('*.html'):
            text = read_exact(html)
            for match in REF_RE.finditer(text):
                url, query = match.group(2) + match.group(3), match.group(4) or ''
                if '://' in url or url.startswith('//'):
                    continue
                if not re.search(r'[?&]v=', query):
                    continue
                target = (html.parent / url.split('?')[0]).resolve()
                self.assertTrue(target.exists(), f'{html.relative_to(build_dir)} -> {url}')
                self.assertRegex(query, r'[?&]v=[0-9a-f]{10}')
                checked += 1
        self.assertGreater(checked, 10)

    # 3. 内容变化 -> 版本变化 --------------------------------------------------
    def test_version_changes_when_content_changes(self):
        first = self.run_build('build1')
        v1 = re.search(r'itasca\.css\?v=([0-9a-f]{10})', (first / 'index.html').read_text()).group(1)
        # 模拟第二次部署：仅修改 itasca.css 内容。
        self.fx.write('doc/_static/itasca.css', 'body { color: #111; }\n')
        second = self.run_build('build2')
        v2 = re.search(r'itasca\.css\?v=([0-9a-f]{10})', (second / 'index.html').read_text()).group(1)
        self.assertNotEqual(v1, v2)
        # 未修改文件的版本号不变。
        p1 = re.search(r'pygments\.css\?v=([0-9a-f]{10})', (first / 'index.html').read_text()).group(1)
        p2 = re.search(r'pygments\.css\?v=([0-9a-f]{10})', (second / 'index.html').read_text()).group(1)
        self.assertEqual(p1, p2)

    def test_version_changes_when_search_index_changes(self):
        self.run_build('build1')
        self.fx.write('doc/_static/zh-search-data.js', 'window.FLAC_ZH_SEARCH_DATA={pages:[1]};\n')
        second = self.run_build('build2')
        data_ref = re.search(
            r"new URL\('zh-search-data\.js\?v=([0-9a-f]{10})'",
            (second / 'doc/_static/zh-search.js').read_text(),
        )
        self.assertIsNotNone(data_ref)
        # zh-search.js 自身内容随之变化，其 HTML 版本号也必须变化。
        js_v1 = re.search(r'zh-search\.js\?v=([0-9a-f]{10})',
                          (self.fx.base / 'build1' / 'doc/search.html').read_text()).group(1)
        js_v2 = re.search(r'zh-search\.js\?v=([0-9a-f]{10})',
                          (self.fx.base / 'build2' / 'doc/search.html').read_text()).group(1)
        self.assertNotEqual(js_v1, js_v2)

    # 4 + 9. 内容不变 -> 版本稳定；重复构建幂等 -------------------------------
    def test_rebuild_is_idempotent(self):
        self.run_build('build1')
        self.run_build('build2')
        for path in (self.fx.base / 'build1').rglob('*'):
            if not path.is_file():
                continue
            rel = path.relative_to(self.fx.base / 'build1')
            twin = self.fx.base / 'build2' / rel
            self.assertTrue(twin.exists(), f'{rel} 在第二次构建中缺失')
            self.assertEqual(path.read_bytes(), twin.read_bytes(), f'{rel} 两次构建不一致')

    # 5. 多层相对路径 ---------------------------------------------------------
    def test_deep_relative_paths_versioned(self):
        build_dir = self.run_build()
        text = (build_dir / 'doc/flac3d/deep/page.html').read_text()
        m = re.search(r'href="\.\./\.\./_static/itasca\.css\?v=([0-9a-f]{10})"', text)
        self.assertIsNotNone(m)
        # 与首页引用的是同一份文件，版本号必须一致。
        home = re.search(r'href="doc/_static/itasca\.css\?v=([0-9a-f]{10})"',
                         (build_dir / 'index.html').read_text())
        self.assertEqual(m.group(1), home.group(1))
        # 相对路径前缀保持不变。
        self.assertIn('../../_static/itasca.css?v=', text)

    # 6. 既有查询参数保留 -----------------------------------------------------
    def test_existing_query_params_preserved(self):
        build_dir = self.run_build()
        text = (build_dir / 'index.html').read_text()
        m = re.search(r'src="doc/_static/MathJax/MathJax\.js\?config=TeX-AMS_SVG&v=([0-9a-f]{10})"', text)
        self.assertIsNotNone(m)

    # 7. 相对路径形式保留（Pages 子路径兼容） ---------------------------------
    def test_references_stay_relative(self):
        build_dir = self.run_build()
        for html in build_dir.rglob('*.html'):
            for match in REF_RE.finditer(read_exact(html)):
                url = match.group(2) + match.group(3)
                if '://' in url or url.startswith('//'):
                    continue
                self.assertFalse(url.startswith('/'), f'{html}: {url} 变成绝对路径')

    # 8. 特殊加载点改写 --------------------------------------------------------
    def test_dynamic_loads_versioned(self):
        build_dir = self.run_build()
        search_html = (build_dir / 'doc/search.html').read_text()
        self.assertRegex(search_html, r'Search\.loadIndex\("searchindex\.js\?v=[0-9a-f]{10}"\)')
        zh_js = (build_dir / 'doc/_static/zh-search.js').read_text()
        self.assertRegex(zh_js, r"new URL\('zh-search-data\.js\?v=[0-9a-f]{10}', ownURL\)")
        # 剥离版本号后与源文件逐字节一致。
        stripped = re.sub(rb"[?&]v=[0-9a-f]{8,16}", b'',
                          (build_dir / 'doc/_static/zh-search.js').read_bytes())
        original = (self.fx.src / 'doc/_static/zh-search.js').read_bytes()
        self.assertEqual(stripped, original)

    def test_doxygen_pages_versioned(self):
        build_dir = self.run_build()
        api = (build_dir / 'doc/doxygen/html/api.html').read_text()
        self.assertRegex(api, r'href="doxygen\.css\?v=[0-9a-f]{10}"')
        search = (build_dir / 'doc/doxygen/html/search/all_0.html').read_text()
        self.assertRegex(search, r'src="variables_0\.js\?v=[0-9a-f]{10}"')

    # 10. 不误改外部链接 / 普通链接 / 缺失目标 --------------------------------
    def test_external_and_document_links_untouched(self):
        build_dir = self.run_build()
        text = (build_dir / 'external.html').read_text()
        self.assertIn('https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.2/MathJax.js?config=TeX-MML-AM_CHTML', text)
        self.assertIn('http://code.jquery.com/ui/1.12.1/jquery-ui.js', text)
        self.assertIn('href="missing.css"', text)      # 缺失目标不改写
        self.assertIn('href="doc/search.html"', text)  # 文档链接不加版本号

    def test_deploy_exclusions_and_inclusions(self):
        # worktree 中 .git 是文件，必须排除（普通 clone 中是目录，同样排除）。
        self.fx.write('.git', 'gitdir: ../.git/worktrees/demo\n')
        build_dir = self.run_build()
        self.assertFalse((build_dir / '.git').exists())
        self.assertFalse((build_dir / 'package.json').exists())
        self.assertFalse((build_dir / 'scripts').exists())
        self.assertFalse((build_dir / 'tests').exists())
        self.assertTrue((build_dir / '.nojekyll').exists())
        self.assertTrue((build_dir / 'notes.md').exists())  # about.html 引用的 md 保留
        self.assertTrue((build_dir / 'robots.txt').exists())
        self.assertTrue((build_dir / 'doc' / 'searchindex.js').exists())

    # 锚点消失时构建必须失败（防止静默失去缓存失效） ---------------------------
    def test_missing_dynamic_anchor_fails_build(self):
        self.fx.write('doc/_static/zh-search.js', 'const ownURL = 1;\r\n')
        result = build(self.fx.src, self.fx.base / 'build_x')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('zh-search-data.js 加载锚点', result.stderr)


if __name__ == '__main__':
    unittest.main()
