#!/usr/bin/env python3
"""Build a reproducible project-level audit ledger.

Outputs:
  translation_review/project_master_status.json
  translation_review/project_master_report.md
"""
from pathlib import Path
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'doc'
OUT_DIR = ROOT / 'translation_review'


def rel(path):
    return path.relative_to(ROOT).as_posix()


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]


def classify(path):
    p = path.as_posix()
    low = p.lower()
    parts = p.split('/')
    product = parts[0] if parts else 'other'
    if product not in {'flac3d', '3dec', 'pfc', 'common'}:
        product = 'other'
    if '/problemsolving/' in low:
        kind = 'tutorial'
    elif '/theory/' in low:
        kind = 'theory'
    elif '/examples/' in low or '/verification/' in low:
        kind = 'example'
    elif '/python/' in low or low.endswith('.py.html'):
        kind = 'python'
    elif 'fish' in low:
        kind = 'fish'
    elif 'cmd_' in low or '_commands/' in low:
        kind = 'command'
    elif low.endswith('/contents.html') or low.endswith('/index.html') or low.endswith('search.html'):
        kind = 'navigation'
    else:
        kind = 'other'
    return product, kind


def main():
    html = sorted(DOC.rglob('*.html'))
    # Search index paths are relative to doc/, not to the repository root.
    html_rel = [p.relative_to(DOC).as_posix() for p in html]
    product_counts = Counter()
    kind_counts = Counter()
    for p in html:
        product, kind = classify(p)
        product_counts[product] += 1
        kind_counts[kind] += 1

    search_path = DOC / '_static/zh-search-data.js'
    search_text = search_path.read_text(encoding='utf-8')
    search_data = json.loads(search_text.split('=', 1)[1].rstrip().rstrip(';'))
    search_paths = {p['path'] for p in search_data['pages']}
    html_set = set(html_rel)
    missing_from_search = sorted(html_set - search_paths)
    stale_search = sorted(search_paths - html_set)

    batch2 = read_jsonl(OUT_DIR / 'batch2/page_list.jsonl')
    batch2_reviewed = [r['path'] for r in batch2[:50]]
    batch2_queue = [r['path'] for r in batch2[50:]]

    batch1_records = read_jsonl(OUT_DIR / 'batch1_records.jsonl')
    batch1_paths = sorted({r['path'] for r in batch1_records})
    batch1_confirmed = [r for r in batch1_records if r.get('confirmed_error') and r.get('final_counted')]

    sub1 = read_jsonl(OUT_DIR / 'batch2/sub1_records.jsonl')
    sub2 = read_jsonl(OUT_DIR / 'batch2/sub2_records.jsonl')
    confirmed = batch1_confirmed + [r for r in sub1 if r.get('status', '').startswith('已修复')] + [r for r in sub2 if r.get('status', '').startswith('已修复')]
    severity = Counter(r.get('severity', '?') for r in confirmed)
    pending = [r for r in sub1 + sub2 if r.get('status') == '待复核']

    status = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'base_commit': 'fe97a02bbaa78a48eba53d41ffa245b85c45d8b6',
        'scope_exclusions': ['移动端适配', 'icgscripts.js 移动端逻辑', '微信小程序'],
        'totals': {
            'html_pages': len(html),
            'products': dict(sorted(product_counts.items())),
            'document_types': dict(sorted(kind_counts.items())),
            'search_index_pages': len(search_paths),
            'missing_from_search_index': len(missing_from_search),
            'stale_search_index_entries': len(stale_search),
        },
        'reviewed': {
            'batch1_machine_readable_paths': batch1_paths,
            'batch1_machine_readable_path_count': len(batch1_paths),
            'batch1_report_claim': 30,
            'batch1_evidence_gap': '第一批报告声明30篇，但机器可读记录只覆盖出现修订的页面；完整页面清单未结构化保存。',
            'batch2_sub1': batch2[:25],
            'batch2_sub2': batch2[25:50],
            'batch2_reviewed_count_exact': len(batch2_reviewed),
        },
        'confirmed_errors': {
            'count': len(confirmed),
            'severity': dict(sorted(severity.items())),
            'ids': [r.get('id') for r in confirmed],
        },
        'pending': {
            'count': len(pending),
            'sub1': [r for r in sub1 if r.get('status') == '待复核'],
            'sub2': [r for r in sub2 if r.get('status') == '待复核'],
        },
        'history': {
            'merged_prs': [2, 3, 5],
            'closed_stale_prs': [4],
            'pr4_reason': '准备分支基于过期基线；正文修订已由 #2/#3/#5 合入 main，相对 main 的删除项不能合并。',
            'other_active_branches': ['fix/pages-quality-checks'],
        },
        'known_issues': [
            {'id': 'AUDIT-001', 'issue': 'README 声明 6,576 个 HTML，实际扫描为 %d 个' % len(html), 'status': '待修复'},
            {'id': 'AUDIT-002', 'issue': '搜索索引 %d 页，HTML %d 页，缺失 %d，陈旧 %d' % (len(search_paths), len(html), len(missing_from_search), len(stale_search)), 'status': '待修复'},
            {'id': 'AUDIT-003', 'issue': '第一批完整30篇页面清单缺少结构化记录，无法逐页机器复核', 'status': '证据缺口'},
            {'id': 'AUDIT-004', 'issue': '子批次2仍有英文482块、中文636块 pending', 'status': '待复核'},
        ],
        'next_queue': batch2_queue,
        'queue_size': len(batch2_queue),
    }
    (OUT_DIR / 'project_master_status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    lines = [
        '# 项目总账与审计报告',
        '',
        f"生成时间：{status['generated_at']}",
        f"基线提交：`{status['base_commit']}`",
        '',
        '## 1. 总览',
        '',
        '| 指标 | 数量 |',
        '| --- | ---: |',
        f"| HTML 页面 | {len(html)} |",
        f"| 搜索索引页 | {len(search_paths)} |",
        f"| 搜索索引缺失 | {len(missing_from_search)} |",
        f"| 搜索索引陈旧项 | {len(stale_search)} |",
        f"| 第二批已审校（精确清单） | {len(batch2_reviewed)} |",
        f"| 第二批待审队列 | {len(batch2_queue)} |",
        f"| 已确认修订 | {len(confirmed)} |",
        f"| 待复核记录 | {len(pending)} |",
        '',
        '## 2. 产品分布',
        '',
        '| 产品 | 页面 |',
        '| --- | ---: |',
    ]
    for k, v in status['totals']['products'].items():
        lines.append(f'| {k} | {v} |')
    lines += ['', '## 3. 文档类型分布', '', '| 类型 | 页面 |', '| --- | ---: |']
    for k, v in status['totals']['document_types'].items():
        lines.append(f'| {k} | {v} |')
    lines += [
        '',
        '## 4. 审校证据',
        '',
        '- 第一批：报告声明 30 篇，机器可读记录仅覆盖出现修订的页面；完整清单缺失，记为证据缺口。',
        '- 第二批：第 1—50 篇有精确 JSONL 清单与逐条记录；第 51—100 篇进入自动队列。',
        '- 程序候选、结构候选、AI 证据确认和待复核状态严格分离，不把自动匹配当成语义确认。',
        '',
        '## 5. 已知问题',
        '',
    ]
    for issue in status['known_issues']:
        lines.append(f"- **{issue['id']}** [{issue['status']}] {issue['issue']}")
    lines += [
        '',
        '## 6. 历史 PR',
        '',
        '- PR #2/#3/#5 已合并。',
        '- PR #4 为过期准备分支，已关闭并记录原因；无独有有效修改需要迁移。',
        '- `fix/pages-quality-checks` 为另一活跃分支，当前未纳入本轮，避免覆盖其独立工作。',
        '',
        '## 7. 下一步队列',
        '',
        f'自动队列共 {len(batch2_queue)} 篇，详见 `project_master_status.json` 的 `next_queue`。',
        '',
        '本总账只记录可复核事实；自动检查覆盖不等于语义审校完成。',
    ]
    (OUT_DIR / 'project_master_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('html', len(html), 'search', len(search_paths), 'queue', len(batch2_queue), 'confirmed', len(confirmed), 'pending', len(pending))

if __name__ == '__main__':
    main()
