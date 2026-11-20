#!/usr/bin/env python3
"""Build alignment and high-risk candidates for a translation review batch.

Usage:
  python scripts/review_translation_batch.py pages.txt en_dir out.jsonl

pages.txt: one repository-relative doc path per line, e.g.
  flac3d/zone/.../cmd_zone.apply.html
en_dir: directory containing official English HTML named by path with '/' -> '_'
"""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys
import difflib

ROOT = Path(__file__).resolve().parents[1]
BLOCK_TAGS = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'dt', 'dd'}

class BlockParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.blocks = []
        self.cur = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in BLOCK_TAGS and tag not in self.stack:
            self.stack.append(tag)
            self.cur = []

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if tag in BLOCK_TAGS and tag in self.stack:
            idx = len(self.stack) - 1 - self.stack[::-1].index(tag)
            if idx == len(self.stack) - 1:
                text = re.sub(r'\s+', ' ', ''.join(self.cur)).strip()
                if text:
                    self.blocks.append((tag, text))
                self.stack.pop()
                self.cur = []
            else:
                self.stack = self.stack[:idx]

    def handle_data(self, data):
        if self.stack and not self.skip:
            self.cur.append(data)


def blocks(path):
    p = BlockParser()
    p.feed(path.read_text(encoding='utf-8', errors='ignore'))
    return [t for _, t in p.blocks if len(t) >= 12]

NUM = re.compile(r'(?<![\w.])\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w.])')
IDENT = re.compile(r'\b[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_-]+)+\b')
EN_NEG = re.compile(r'\b(not|no|never|cannot|can\'t|unless|without|must not|should not|do not|does not|is not|are not)\b', re.I)
ZH_NEG = re.compile(r'不|未|无|禁止|切勿|不能|不可|除非|没有')
EN_MODAL = re.compile(r'\b(must|required|should|can|may|default|only)\b', re.I)
ZH_MODAL = re.compile(r'必须|应|可|可以|将|默认|要求|仅|只有')
EN_CMP = re.compile(r'\b(greater than|less than|at least|at most|minimum|maximum|below|above|exceed|exceeds)\b', re.I)
ZH_CMP = re.compile(r'大于|小于|至少|至多|最小|最大|低于|高于|超过')


def signature_tokens(text):
    """Return numeric/identifier features used for strong alignment."""
    nums = tuple(sorted(set(NUM.findall(text))))
    ids = tuple(sorted({x.lower() for x in IDENT.findall(text)}))
    return nums, ids


def align_pairs(en_sigs, zh_sigs):
    """Align only paragraphs with non-empty matching features.

    Paragraphs without numbers or command identifiers are deliberately not
    paired: identical empty signatures are not evidence of alignment.
    """
    def strong(sig):
        nums, ids = sig
        return bool(nums or ids)

    en_strong = [strong(s) for s in en_sigs]
    zh_strong = [strong(s) for s in zh_sigs]
    sm = difflib.SequenceMatcher(
        None,
        [s if e else object() for s, e in zip(en_sigs, en_strong)],
        [s if e else object() for s, e in zip(zh_sigs, zh_strong)],
        autojunk=False,
    )
    pairs = []
    for block in sm.get_matching_blocks():
        for k in range(block.size):
            ei, zi = block.a + k, block.b + k
            if en_strong[ei] and zh_strong[zi] and en_sigs[ei] == zh_sigs[zi]:
                pairs.append((ei, zi))
    return pairs


def flags(en, zh):
    out = []
    en_neg, zh_neg = bool(EN_NEG.search(en)), bool(ZH_NEG.search(zh))
    if en_neg != zh_neg:
        out.append('NEGATION')
    en_cmp, zh_cmp = bool(EN_CMP.search(en)), bool(ZH_CMP.search(zh))
    if en_cmp and not zh_cmp:
        out.append('COMPARISON')
    en_nums, zh_nums = set(NUM.findall(en)), set(NUM.findall(zh))
    if en_nums != zh_nums:
        out.append('NUMBER')
    en_ids = {x.lower() for x in IDENT.findall(en)}
    zh_ids = {x.lower() for x in IDENT.findall(zh)}
    if en_ids - zh_ids:
        out.append('IDENTIFIER')
    zh_chars = len(re.findall(r'[\u4e00-\u9fff]', zh))
    letters = len(re.findall(r'[A-Za-z]', zh))
    if letters > 30 and zh_chars < 8:
        out.append('UNTRANSLATED')
    return out


def main():
    pages_file, en_dir, out_file = map(Path, sys.argv[1:4])
    en_dir = en_dir.resolve()
    rels = [l.strip() for l in pages_file.read_text(encoding='utf-8').splitlines() if l.strip()]
    records = []
    stats = []
    for rel in rels:
        zh_path = ROOT / 'doc' / rel
        en_path = en_dir / rel.replace('/', '_')
        zh = blocks(zh_path)
        en = blocks(en_path)
        en_sig = [signature_tokens(x) for x in en]
        zh_sig = [signature_tokens(x) for x in zh]
        pairs = align_pairs(en_sig, zh_sig)
        cand = []
        for ei, zi in pairs:
            f = flags(en[ei], zh[zi])
            if f:
                cand.append({'en_index': ei, 'zh_index': zi, 'flags': f,
                             'en': en[ei][:800], 'zh': zh[zi][:800]})
        weak_en = sum(1 for s in en_sig if not s[0] and not s[1])
        weak_zh = sum(1 for s in zh_sig if not s[0] and not s[1])
        records.append({'path': rel, 'en_blocks': len(en), 'zh_blocks': len(zh),
                        'aligned': len(pairs), 'weak_en_blocks': weak_en,
                        'weak_zh_blocks': weak_zh, 'candidates': cand})
        stats.append((rel, len(en), len(zh), len(pairs), weak_en, weak_zh, len(cand)))
    out_file.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in records) + '\n', encoding='utf-8')
    for rel, ne, nz, na, we, wz, nc in stats:
        print(f'{rel}\ten={ne}\tzh={nz}\tstrong_aligned={na}\tweak={we}/{wz}\tcand={nc}')

if __name__ == '__main__':
    main()
