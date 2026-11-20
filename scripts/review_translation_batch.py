#!/usr/bin/env python3
"""Build alignment and high-risk candidates for a translation review batch.

Usage:
  python scripts/review_translation_batch.py pages.txt en_dir out.jsonl

Alignment has two stages:
  1. strong: matching non-empty numeric/identifier signatures;
  2. semantic: same section/heading context plus shared technical concepts.

Paragraphs with no strong or semantic evidence are reported as unaligned.
"""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys
import difflib

ROOT = Path(__file__).resolve().parents[1]
BLOCK_TAGS = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'dt', 'dd'}
HEADING_TAGS = {'h1', 'h2', 'h3', 'h4'}

CONCEPT_MAP = {
    'stress': '应力', 'strain': '应变', 'displacement': '位移', 'velocity': '速度',
    'acceleration': '加速度', 'force': '力', 'pressure': '压力', 'boundary': '边界',
    'condition': '条件', 'default': '默认', 'model': '模型', 'property': '性质',
    'zone': '网格单元', 'gridpoint': '网格点', 'node': '节点', 'interface': '接触面',
    'fluid': '流体', 'pore': '孔隙', 'temperature': '温度', 'thermal': '热学',
    'dynamic': '动力', 'damping': '阻尼', 'time step': '时步', 'convergence': '收敛',
    'equilibrium': '平衡', 'yield': '屈服', 'plastic': '塑性', 'elastic': '弹性',
    'strength': '强度', 'failure': '破坏', 'block': '块体', 'joint': '节理',
    'ball': '球体', 'clump': '刚性簇', 'contact': '接触', 'bond': '黏结',
    'gravity': '重力', 'density': '密度', 'stiffness': '刚度', 'permeability': '渗透率',
    'warning': '警告', 'caution': '注意', 'note': '注意', 'example': '示例',
}


class ContextBlockParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.open = []
        self.headings = {}
        self.blocks = []
        self.cur = None
        self.skip = 0

    def _nearest_id(self):
        for tag, attrs in reversed(self.open):
            if 'id' in attrs:
                return attrs['id']
        return ''

    def _ctx(self):
        heads = tuple(self.headings.get(level, '') for level in (1, 2, 3, 4))
        return {'section': self._nearest_id(), 'headings': heads}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.open.append((tag, attrs))
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in BLOCK_TAGS and self.cur is None:
            ctx = self._ctx()
            self.cur = {'tag': tag, 'parts': [], **ctx}

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if self.cur is not None and tag == self.cur['tag']:
            # Save the text before clearing self.cur. Heading tags are also
            # blocks, so their text must be available for context update.
            text = re.sub(r'\s+', ' ', ''.join(self.cur['parts'])).strip()
            if text:
                self.cur['text'] = text
                self.blocks.append(self.cur)
            if tag in HEADING_TAGS:
                level = int(tag[1])
                self.headings[level] = text
                for deeper in range(level + 1, 5):
                    self.headings.pop(deeper, None)
            self.cur = None
        # pop matching open tag
        for idx in range(len(self.open) - 1, -1, -1):
            if self.open[idx][0] == tag:
                self.open = self.open[:idx]
                break

    def handle_data(self, data):
        if self.cur is not None and not self.skip:
            self.cur['parts'].append(data)


def blocks_with_context(path):
    p = ContextBlockParser()
    p.feed(path.read_text(encoding='utf-8', errors='ignore'))
    return [b for b in p.blocks if len(b['text']) >= 12]


def blocks(path):
    return [b['text'] for b in blocks_with_context(path)]


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
    """Align only paragraphs with non-empty matching features."""
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


def concepts(text, language):
    found = set()
    if language == 'en':
        for en, zh in CONCEPT_MAP.items():
            if re.search(r'\b' + re.escape(en) + r'\b', text, re.I):
                found.add(zh)
    else:
        for zh in CONCEPT_MAP.values():
            if zh in text:
                found.add(zh)
    return found


def context_compatible(en_block, zh_block):
    if en_block['section'] and zh_block['section']:
        return en_block['section'] == zh_block['section']
    en_heads = {h for h in en_block['headings'] if h}
    zh_heads = {h for h in zh_block['headings'] if h}
    return bool(en_heads & zh_heads)


def semantic_align(en_blocks, zh_blocks, exclude_pairs):
    """Conservative semantic alignment for blocks without strong features.

    Requires same section/heading context, at least two shared technical
    concepts, and a plausible relative position in the page.
    """
    excluded_en = {e for e, _ in exclude_pairs}
    excluded_zh = {z for _, z in exclude_pairs}
    candidates = []
    for ei, eb in enumerate(en_blocks):
        if ei in excluded_en:
            continue
        ec = concepts(eb['text'], 'en')
        if len(ec) < 2:
            continue
        for zi, zb in enumerate(zh_blocks):
            if zi in excluded_zh:
                continue
            if not context_compatible(eb, zb):
                continue
            zc = concepts(zb['text'], 'zh')
            shared = ec & zc
            if len(shared) < 2:
                continue
            pos_gap = abs(ei / max(1, len(en_blocks)) - zi / max(1, len(zh_blocks)))
            if pos_gap > 0.25:
                continue
            score = len(shared) - pos_gap
            candidates.append((score, ei, zi, shared))
    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    pairs = []
    used_en = set(excluded_en)
    used_zh = set(excluded_zh)
    for score, ei, zi, shared in candidates:
        if ei in used_en or zi in used_zh:
            continue
        pairs.append((ei, zi, score))
        used_en.add(ei)
        used_zh.add(zi)
    return sorted(pairs)


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
    for rel in rels:
        zh_path = ROOT / 'doc' / rel
        en_path = en_dir / rel.replace('/', '_')
        en_ctx = blocks_with_context(en_path)
        zh_ctx = blocks_with_context(zh_path)
        en = [b['text'] for b in en_ctx]
        zh = [b['text'] for b in zh_ctx]
        en_sig = [signature_tokens(x) for x in en]
        zh_sig = [signature_tokens(x) for x in zh]
        strong = align_pairs(en_sig, zh_sig)
        semantic = semantic_align(en_ctx, zh_ctx, strong)
        all_pairs = [(ei, zi, 'strong') for ei, zi in strong]
        all_pairs.extend((ei, zi, 'semantic') for ei, zi, _ in semantic)
        cand = []
        for ei, zi, method in all_pairs:
            f = flags(en[ei], zh[zi])
            if f:
                cand.append({'en_index': ei, 'zh_index': zi, 'method': method,
                             'flags': f, 'en': en[ei][:800], 'zh': zh[zi][:800]})
        weak_en = sum(1 for s in en_sig if not s[0] and not s[1])
        weak_zh = sum(1 for s in zh_sig if not s[0] and not s[1])
        records.append({
            'path': rel, 'en_blocks': len(en), 'zh_blocks': len(zh),
            'strong_aligned': len(strong), 'semantic_aligned': len(semantic),
            'aligned': len(all_pairs),
            'unaligned_en': len(en) - len(strong) - len(semantic),
            'unaligned_zh': len(zh) - len(strong) - len(semantic),
            'weak_en_blocks': weak_en, 'weak_zh_blocks': weak_zh,
            'candidates': cand,
        })
        print(f"{rel}\ten={len(en)}\tzh={len(zh)}\tstrong={len(strong)}\tsemantic={len(semantic)}\tunaligned={records[-1]['unaligned_en']}/{records[-1]['unaligned_zh']}")
    out_file.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in records) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
