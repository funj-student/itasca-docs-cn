#!/usr/bin/env python3
"""CI guard: no missing local file targets or missing HTML anchors."""
import re
import html
from pathlib import Path
from urllib.parse import urlparse, unquote
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = [p for p in ROOT.rglob('*.html') if '.git' not in p.parts]
LINK = re.compile(r'<a\s[^>]*href="([^"]+)"', re.I)
ID = re.compile(r'\sid="([^"]+)"', re.I)
cache = {}

def ids_of(p):
    k = str(p.resolve())
    if k not in cache:
        try:
            t = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            t = ''
        cache[k] = set(ID.findall(t))
    return cache[k]

missing_files = 0
missing_anchors = 0
for p in PAGES:
    try:
        t = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for m in LINK.finditer(t):
        raw = html.unescape(m.group(1))
        if not raw or raw.startswith(('http:', 'https:', 'mailto:', 'javascript:', 'data:', '#')):
            continue
        q = urlparse(raw)
        path = unquote(q.path)
        frag = unquote(q.fragment)
        if not path and not frag:
            continue
        if not path:
            target = p
        else:
            target = (p.parent / path).resolve()
            if not target.exists():
                missing_files += 1
                continue
        if frag and target.suffix.lower() == '.html' and frag not in ids_of(target):
            missing_anchors += 1

print(f'pages={len(PAGES)} missing_files={missing_files} missing_anchors={missing_anchors}')
if missing_files or missing_anchors:
    sys.exit(1)
