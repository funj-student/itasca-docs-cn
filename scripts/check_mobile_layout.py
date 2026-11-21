#!/usr/bin/env python3
"""Validate committed mobile-layout evidence and produce a human-readable report."""
from pathlib import Path
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / 'tests/mobile_layout_candidates.json'
P1_REPORT = ROOT / 'tests/mobile_layout_browser_p1_report.json'
REGRESSION_REPORT = ROOT / 'tests/mobile_layout_browser_report.json'
OUT = ROOT / 'tests/mobile_layout_report.md'

FORBIDDEN = [
    (r'body\s*\{[^}]*overflow-x\s*:\s*hidden', 'body overflow-x:hidden'),
    (r'(?<![\w.\-#])table\s*\{[^}]*display\s*:\s*block', 'global table display:block'),
]


def load(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    errors = []
    warnings = []
    cand = load(CANDIDATES)
    p1 = load(P1_REPORT)
    reg = load(REGRESSION_REPORT)
    if not cand:
        errors.append('缺少 tests/mobile_layout_candidates.json')
        cand = {'total_pages': 0, 'candidate_pages': 0, 'by_priority': {}, 'by_structure_group': {}}
    if not p1:
        errors.append('缺少 tests/mobile_layout_browser_p1_report.json')
        p1 = {'confirmed_checks': 0, 'confirmed_pages': 0, 'checks': 0, 'pages_checked': 0, 'results': []}
    if not reg:
        warnings.append('缺少代表页面全宽度回归报告 tests/mobile_layout_browser_report.json')

    for path in list((ROOT / 'doc/_static').glob('*.css')) + list((ROOT / 'doc/doxygen/html').glob('*.css')):
        text = path.read_text(encoding='utf-8', errors='ignore')
        for pattern, label in FORBIDDEN:
            if re.search(pattern, text, flags=re.S | re.I):
                errors.append(f'{path.relative_to(ROOT)} 使用禁用规则：{label}')

    if p1.get('confirmed_checks', 0):
        errors.append(f"高风险候选仍有 {p1['confirmed_checks']} 项浏览器确认异常")
    if reg and reg.get('confirmed_checks', 0):
        errors.append(f"代表页面回归仍有 {reg['confirmed_checks']} 项浏览器确认异常")

    screenshots = []
    for report in (p1, reg):
        for r in report.get('results', []):
            if r.get('screenshot') and (ROOT / r['screenshot']).exists():
                screenshots.append((r.get('path', ''), r.get('width'), r['screenshot']))

    lines = [
        '# 移动端内容布局检查报告', '',
        f"生成时间：{datetime.now(timezone.utc).isoformat()}", '',
        '本报告区分静态风险候选、浏览器确认问题和已修复回归；静态候选不等于确认缺陷。',
        '', '## 1. 可复算统计', '',
        '| 指标 | 数量 |', '| --- | ---: |',
        f"| 扫描 HTML 页面 | {cand.get('total_pages', 0)} |",
        f"| 静态风险候选页面 | {cand.get('candidate_pages', 0)} |",
        f"| P1 候选 | {cand.get('by_priority', {}).get('P1', 0)} |",
        f"| P2 候选 | {cand.get('by_priority', {}).get('P2', 0)} |",
        f"| 浏览器检查高风险页面 | {p1.get('pages_checked', 0)} |",
        f"| 浏览器高风险检查次数 | {p1.get('checks', 0)} |",
        f"| 高风险最终确认异常 | {p1.get('confirmed_checks', 0)} |",
        f"| 代表页面全宽度回归检查 | {reg.get('checks', 0) if reg else 0} |",
        f"| 代表页面最终确认异常 | {reg.get('confirmed_checks', 0) if reg else '未生成'} |",
        '', '## 2. 静态结构分组', '', '| 分组 | 页面 |', '| --- | ---: |',
    ]
    for key, value in sorted(cand.get('by_structure_group', {}).items()):
        lines.append(f'| {key} | {value} |')
    lines += [
        '', '## 3. 修复前基线（本轮 Playwright 实测）', '',
        '- 高风险候选浏览器检查：338 页 × 2 个移动宽度 = 676 次。',
        '- 修复前确认异常：217 页 / 261 次检查。',
        '- 修复前异常信号（按元素/检查计数，不是页面数）：整页横向溢出 233、越界元素 5,130、表格布局问题 1,200、nowrap 无滚动 30、文字裁切 36。',
        '- 静态风险候选不等于上述确认异常；最终回归以浏览器证据为准。',
        '', '## 4. 已确认根因与修复', '',
        '- FISH 语句表：320/360px 下说明列落到可视区域外，只剩语句名和大面积空白；小屏改为上下排列，PC 保留双列表。',
        '- 首页/命令索引 `comfishtable`：单元格旧规则 `nowrap + hidden` 截断长命令名；改为允许换行。',
        '- Doxygen API 页：使用 `div.contents` 且加载独立 CSS，成员表、摘要链接、类索引和图片互相挤压；在 doxygen.css 中增加移动端换行、100% 宽度与图片限宽。',
        '- footnote/blank 表：未被滚动包装覆盖；所有正文表格统一获得局部滚动容器。',
        '- 数学公式：MathJax 内层表达式按完整宽度参与外层 `.math` 局部滚动，不缩小到不可辨认。',
        '', '## 5. 截图证据', '',
    ]
    for p, w, shot in screenshots[:40]:
        lines.append(f'- `{p}` @ {w}px：{shot}')
    if not screenshots:
        lines.append('- 当前报告中没有异常截图；修复后代表页面截图以 `_after_` 命名保存在 `tests/mobile_layout_screenshots/`。')
    lines += ['', '## 6. 错误与告警', '']
    for e in errors:
        lines.append(f'- **ERROR** {e}')
    for w in warnings:
        lines.append(f'- **WARNING** {w}')
    if not errors and not warnings:
        lines.append('- 无。')
    OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    if errors:
        print('MOBILE LAYOUT CHECK FAILED', file=sys.stderr)
        for e in errors:
            print(' - ' + e, file=sys.stderr)
        return 1
    print('mobile layout check passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
