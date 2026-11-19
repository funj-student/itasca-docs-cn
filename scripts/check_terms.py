#!/usr/bin/env python3
"""CI guard for terminology consistency and admonition visibility."""
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / '核心术语对照.md'
HTML = ROOT / 'terms.html'
errors = []
warnings = []

# 1. glossary size and HTML sync
rows = [l for l in MD.read_text(encoding='utf-8').splitlines()
        if re.match(r'^\|\s*[^|]+\s*\|\s*[^|]+\s*\|\s*[^|]+\s*\|$', l)
        and not l.startswith('| English') and not l.startswith('| ---')]
if len(rows) < 100:
    errors.append(f'术语表条目不足 100：{len(rows)}')
html_text = HTML.read_text(encoding='utf-8')
html_rows = len(re.findall(r'<tr><td><code class="docutils literal">', html_text))
if html_rows != len(rows):
    errors.append(f'terms.html 行数 {html_rows} 与 Markdown 行数 {len(rows)} 不一致')

# 2. banned variants
banned = {
    '粘结': '统一为“黏结”',
    '刚性团簇': '统一为“刚性簇”',
    '历史曲线': 'history 曲线应为“时程曲线”',
    '发展历程': None,  # allowed
}
exts = {'.html', '.js', '.md'}
hits = {}
for p in ROOT.rglob('*'):
    if not p.is_file() or '.git' in p.parts or '逐项校订记录.json' in p.name:
        continue
    if p.suffix.lower() not in exts:
        continue
    try:
        t = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for bad, hint in banned.items():
        if not hint:
            continue
        n = t.count(bad)
        if n:
            hits.setdefault(bad, []).append((p.relative_to(ROOT).as_posix(), n))
for bad, places in hits.items():
    total = sum(n for _, n in places)
    errors.append(f'禁用译法“{bad}”出现 {total} 次（{banned[bad]}），示例：{places[0][0]}')

# 3. untranslated warning titles
untranslated = []
for p in ROOT.rglob('*.html'):
    if '.git' in p.parts:
        continue
    try:
        t = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for m in re.finditer(r'<p class="first admonition-title">(Warning|Caution|Important)</p>', t):
        untranslated.append(p.relative_to(ROOT).as_posix())
        break
if untranslated:
    errors.append(f'仍有未翻译的警示标题：{untranslated[:5]}')

# 4. admonition parity with official English docs
import json
BASE = Path(__file__).resolve().parent
ref = BASE / 'official_admonitions.jsonl'
if ref.exists():
    ad_pat = re.compile(r'<div class="([^"]*admonition[^"]*)">\s*<p class="first admonition-title">(.*?)</p>', re.S)
    def ad_kind(cls, title):
        c = cls.lower()
        for k in ('warning', 'caution', 'important', 'tip', 'seealso', 'note'):
            if k in c: return k
        tt = re.sub(r'<[^>]+>', '', title).strip().lower()
        return tt if tt in ('warning', 'caution', 'important', 'tip', 'note') else 'other'
    official = {}
    for line in ref.read_text(encoding='utf-8').splitlines():
        d = json.loads(line)
        official[d['path']] = d['counts'] or {}
    bad = []
    for rel, oc in official.items():
        f = ROOT / 'doc' / rel
        if not f.exists(): continue
        txt = f.read_text(encoding='utf-8', errors='ignore')
        lc = {}
        for m in ad_pat.finditer(txt):
            k = ad_kind(m.group(1), m.group(2))
            lc[k] = lc.get(k, 0) + 1
        if lc != oc:
            bad.append(rel)
    if bad:
        errors.append(f'警示块与官网不一致的页面 {len(bad)} 个，示例：{bad[:5]}')

print(f'terms={len(rows)} html_rows={html_rows}')
if errors:
    for e in errors:
        print('ERROR:', e, file=sys.stderr)
    sys.exit(1)
print('terminology checks passed')
