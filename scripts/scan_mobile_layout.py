#!/usr/bin/env python3
"""Static structure scan for mobile content-layout risk.

This produces candidates only. Nothing here is marked as a confirmed visual
defect; confirmation requires Playwright checks and screenshot evidence.
"""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import json
import re
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'doc'
OUT = ROOT / 'tests/mobile_layout_candidates.json'
ROOT_PAGES = ('index.html', 'terms.html', 'glossary.html', 'warnings.html',
              'about.html', 'disclaimer.html')
LONG_TOKEN = re.compile(r'[A-Za-z0-9_.:/\-]{24,}')


class StructureParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = 0
        self.max_cols = 0
        self.table_ids = []
        self.colgroup_info = []
        self.inline_widths = []
        self.nowrap = 0
        self.overflow_hidden = 0
        self.pre_blocks = 0
        self.pre_max_line = 0
        self.math = 0
        self.images = 0
        self.fixed_images = 0
        self.svg = 0
        self.iframes = 0
        self.objects = 0
        self.fixed_embeds = 0
        self.list_stack = []
        self.max_list_depth = 0
        self.footer_links = 0
        self._in_footer = 0
        self._in_pre = False
        self._pre_lines = []
        self._in_script_style = 0
        self._table_stack = []
        self._row_cols = None
        self._colgroup = None
        self._text_chunks = []
        self._selectors = set()

    def _attrs(self, attrs):
        return dict(attrs)

    def handle_starttag(self, tag, attrs):
        a = self._attrs(attrs)
        style = a.get('style', '') or ''
        if tag in ('script', 'style'):
            self._in_script_style += 1
        if self._in_script_style:
            return
        if tag == 'table':
            self.tables += 1
            tid = a.get('id')
            if tid:
                self.table_ids.append(tid)
                self._selectors.add(f'table#{tid}')
            self._table_stack.append({'id': tid, 'class': a.get('class', '')})
        if tag == 'colgroup' and self._table_stack:
            self._colgroup = {'widths': []}
        if tag == 'col' and self._colgroup is not None:
            width = a.get('width') or (re.search(r'width\s*:\s*([^;]+)', style).group(1) if 'width' in style else None)
            if width:
                self._colgroup['widths'].append(width.strip())
        if tag == 'tr' and self._table_stack:
            self._row_cols = 0
        if tag in ('td', 'th') and self._table_stack:
            if self._row_cols is not None:
                self._row_cols += 1
        if a.get('width') or re.search(r'(min-)?width\s*:', style):
            value = a.get('width') or re.search(r'(min-)?width\s*:\s*([^;]+)', style).group(2)
            if value:
                self.inline_widths.append(value.strip())
        if 'nowrap' in style or a.get('nowrap') is not None or tag == 'nobr':
            self.nowrap += 1
        if 'overflow: hidden' in style.replace(' ', '') or 'overflow-x: hidden' in style.replace(' ', ''):
            self.overflow_hidden += 1
        if tag == 'pre':
            self.pre_blocks += 1
            self._in_pre = True
            self._pre_lines = []
        if tag == 'math' or 'math' in (a.get('class', '') or '').lower():
            self.math += 1
        if tag == 'img':
            self.images += 1
            width = a.get('width')
            if width and re.sub(r'\D', '', width).isdigit() and int(re.sub(r'\D', '', width)) > 320:
                self.fixed_images += 1
        if tag == 'svg':
            self.svg += 1
        if tag == 'iframe':
            self.iframes += 1
        if tag == 'object':
            self.objects += 1
        if tag in ('iframe', 'object'):
            width_value = a.get('width') or (re.search(r'width\s*:\s*([^;]+)', style).group(1) if 'width' in style else '')
            number = re.search(r'(\d+(?:\.\d+)?)px?', str(width_value))
            if number and float(number.group(1)) > 320:
                self.fixed_embeds += 1
        if tag in ('ul', 'ol'):
            self.list_stack.append(tag)
            self.max_list_depth = max(self.max_list_depth, len(self.list_stack))
        if tag in ('footer',) or 'footer' in (a.get('class', '') or '').lower():
            self._in_footer += 1
        if tag == 'a' and self._in_footer:
            self.footer_links += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self._in_script_style:
            self._in_script_style -= 1
            return
        if self._in_script_style:
            return
        if tag == 'tr' and self._row_cols is not None:
            self.max_cols = max(self.max_cols, self._row_cols)
            self._row_cols = None
        if tag == 'colgroup' and self._colgroup is not None:
            if self._colgroup['widths']:
                self.colgroup_info.append(self._colgroup['widths'])
            self._colgroup = None
        if tag == 'table' and self._table_stack:
            self._table_stack.pop()
        if tag == 'pre':
            self._in_pre = False
            self.pre_max_line = max(self.pre_max_line, max((len(x) for x in self._pre_lines), default=0))
        if tag in ('ul', 'ol') and self.list_stack:
            self.list_stack.pop()
        if tag in ('footer',) or (tag == 'div' and self._in_footer):
            if self._in_footer:
                self._in_footer -= 1

    def handle_data(self, data):
        if self._in_script_style:
            return
        if self._in_pre:
            self._pre_lines.extend(data.splitlines())
        else:
            self._text_chunks.append(data)


def scan_file(path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    p = StructureParser()
    try:
        p.feed(text)
    except Exception:
        pass
    visible = ' '.join(p._text_chunks)
    long_tokens = sorted(set(LONG_TOKEN.findall(visible)), key=len, reverse=True)[:8]
    fixed_gt_viewport = []
    for value in p.inline_widths:
        num = re.search(r'(\d+(?:\.\d+)?)px', value)
        if num and float(num.group(1)) > 320:
            fixed_gt_viewport.append(value)
    groups = []
    if 'tableoffishstatements' in p.table_ids:
        groups.append('FISH语句双列表')
    if p.tables and p.max_cols >= 4:
        groups.append('宽数据表格')
    if p.tables and p.max_cols == 2 and (long_tokens or any('fish' in x.lower() for x in p.table_ids)):
        groups.append('双列技术对照表')
    if p.tables and any('fish' in x.lower() for x in p.table_ids):
        groups.append('FISH函数参考表')
    if p.pre_blocks and (p.pre_max_line > 100 or long_tokens):
        groups.append('长代码/长标识符')
    if p.math >= 5:
        groups.append('复杂数学公式')
    if p.max_list_depth >= 4:
        groups.append('多层目录列表')
    if p.fixed_images or p.svg:
        groups.append('图片/SVG')
    if p.fixed_embeds:
        groups.append('内嵌对象')
    if p.footer_links >= 8:
        groups.append('复杂页脚')
    if p.nowrap or p.overflow_hidden:
        groups.append('nowrap/隐藏溢出')
    if not groups:
        groups.append('普通正文')

    risk = []
    priority = 'P3'
    if 'tableoffishstatements' in p.table_ids or p.max_cols >= 4 or p.fixed_images or p.fixed_embeds:
        risk.append('固定列宽或宽表格可能超过移动视口')
        priority = 'P1'
    if p.nowrap or p.overflow_hidden or fixed_gt_viewport:
        risk.append('nowrap/固定宽度/隐藏溢出可能裁切内容')
        priority = 'P1'
    if p.pre_max_line > 100 or len(long_tokens) >= 3:
        risk.append('长代码或长标识符可能撑破容器')
        priority = 'P2' if priority == 'P3' else priority
    if p.max_list_depth >= 4:
        risk.append('多层列表逐层缩进压缩正文')
        priority = 'P2' if priority == 'P3' else priority
    if p.math >= 5:
        risk.append('复杂公式可能需要局部滚动')
        priority = 'P2' if priority == 'P3' else priority

    selectors = sorted(p._selectors)
    for label, cond in [
        ('table with fixed colgroup', bool(p.colgroup_info)),
        ('[style*="min-width"]', any('min-width' in x for x in p.inline_widths)),
        ('[style*="white-space: nowrap"]', p.nowrap > 0),
        ('[style*="overflow: hidden"]', p.overflow_hidden > 0),
        ('pre', p.pre_blocks > 0),
        ('img[width]', p.images > 0),
        ('iframe, object', bool(p.iframes or p.objects)),
    ]:
        if cond:
            selectors.append(label)
    return {
        'path': path.relative_to(ROOT).as_posix(),
        'product': path.relative_to(DOC).parts[0] if path.is_relative_to(DOC) else 'root',
        'table_count': p.tables,
        'max_table_columns': p.max_cols,
        'table_ids': p.table_ids[:20],
        'colgroup_widths': p.colgroup_info[:20],
        'inline_widths': p.inline_widths[:30],
        'fixed_width_over_320px': fixed_gt_viewport[:20],
        'long_identifiers': long_tokens,
        'nowrap_elements': p.nowrap,
        'overflow_hidden_elements': p.overflow_hidden,
        'pre_blocks': p.pre_blocks,
        'max_pre_line_length': p.pre_max_line,
        'math_elements': p.math,
        'images': p.images,
        'fixed_width_images': p.fixed_images,
        'svg': p.svg,
        'iframes': p.iframes,
        'objects': p.objects,
        'fixed_width_embeds': p.fixed_embeds,
        'max_list_depth': p.max_list_depth,
        'footer_links': p.footer_links,
        'structure_groups': groups,
        'risk_reasons': risk,
        'candidate_priority': priority if risk else None,
        'selectors': selectors,
        'status': 'static_candidate_only',
    }


def main():
    files = sorted(DOC.rglob('*.html')) + [ROOT / x for x in ROOT_PAGES if (ROOT / x).exists()]
    rows = [scan_file(p) for p in files]
    groups = Counter(g for r in rows for g in r['structure_groups'])
    priorities = Counter(r['candidate_priority'] for r in rows)
    candidates = [r for r in rows if r['candidate_priority']]
    out = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'scan_scope': 'all doc/**/*.html and root entry pages',
        'total_pages': len(rows),
        'candidate_pages': len(candidates),
        'by_structure_group': dict(sorted(groups.items())),
        'by_priority': dict(sorted((k, v) for k, v in priorities.items() if k)),
        'note': '静态结构风险，不等于浏览器确认的排版缺陷。',
        'pages': rows,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('pages', len(rows), 'candidates', len(candidates), 'out', OUT.relative_to(ROOT))

if __name__ == '__main__':
    main()
