#!/usr/bin/env python3
"""Generate the module-split comprehensive glossary from 术语词库.md."""
from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / '术语词库.md'
OUT = ROOT / 'glossary.html'
TPL = ROOT / 'disclaimer.html'

sections = []
current = None
for line in SRC.read_text(encoding='utf-8').splitlines():
    if line.startswith('## '):
        current = {'name': line[3:].strip(), 'rows': []}
        sections.append(current)
    elif line.startswith('| ') and current is not None and not line.startswith('| ---') and not line.startswith('| English'):
        parts = [p.strip() for p in line.strip().strip('|').split('|')]
        if len(parts) >= 3:
            current['rows'].append((parts[0], parts[1], parts[2]))

parts = [
    '<div id="mainbody" role="main">',
    '<div class="section" id="glossary">',
    '<h1>模块术语词库</h1>',
    '<p>本词库按通用基础、FLAC3D、3DEC、PFC 与 FISH 五个模块拆分，收录约 250 条高频术语。与 <a href="terms.html">核心术语对照</a> 冲突时，以核心术语表为准；命令、变量与函数名保留英文原文。</p>',
    '<p><label for="glossary-filter">筛选术语：</label><input id="glossary-filter" type="search" placeholder="输入中文或英文术语" style="width:100%;max-width:24em;padding:.4em;box-sizing:border-box;"/></p>',
]
for sec in sections:
    parts.append(f'<h2>{html.escape(sec["name"])}</h2>')
    parts.append('<table class="docutils glossary-table" border="1"><thead><tr><th>English</th><th>中文名称</th><th>说明</th></tr></thead><tbody>')
    for en, zh, note in sec['rows']:
        parts.append('<tr><td><code class="docutils literal"><span class="pre">' + html.escape(en) + '</span></code></td><td>' + html.escape(zh) + '</td><td>' + html.escape(note) + '</td></tr>')
    parts.append('</tbody></table>')
parts.append('</div>')
content = '\n'.join(parts)

s = TPL.read_text(encoding='utf-8')
s = s.replace('<title>版权与免责声明 — Itasca 7.0 手册</title>', '<title>模块术语词库 — Itasca 7.0 手册</title>', 1)
s = s.replace('<link rel="canonical" href="https://funj-student.github.io/itasca-docs-cn/disclaimer.html"/>', '<link rel="canonical" href="https://funj-student.github.io/itasca-docs-cn/glossary.html"/>', 1)
start = s.index('<div id="mainbody" role="main">')
end = s.index('</div>\n</div>\n<div id="navbutton">', start)
script = '''
<script>
(function () {
  var input = document.getElementById('glossary-filter');
  if (!input) { return; }
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase();
    var rows = document.querySelectorAll('.glossary-table tbody tr');
    for (var i = 0; i < rows.length; i++) {
      rows[i].style.display = rows[i].textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
    }
  });
}());
</script>
'''
s = s[:start] + content + '\n' + script + '\n' + s[end:]
OUT.write_text(s, encoding='utf-8')
print('generated', OUT, 'sections', len(sections), 'terms', sum(len(x['rows']) for x in sections))
