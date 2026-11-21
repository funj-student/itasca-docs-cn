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

from review_status import build_review_status_map, summarize
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
    # Accept a doc-relative path (preferred) or a repo-relative/absolute path.
    p = Path(path).as_posix()
    if p.startswith('doc/'):
        p = p[4:]
    elif p.startswith('/') or re.match(r'^[A-Za-z]:/', p):
        if '/doc/' in p:
            p = p.split('/doc/', 1)[1]
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
    for rel_path in html_rel:
        product, kind = classify(rel_path)
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
    review_map = build_review_status_map(batch2)
    review_summary = summarize(review_map)
    batch2_reviewed = [r['path'] for r in batch2 if review_map[r['path']]['review_status'] == 'completed_ai_review_report']
    batch2_queue = [r['path'] for r in batch2 if review_map[r['path']]['review_status'] == 'not_reviewed']

    batch1_records = read_jsonl(OUT_DIR / 'batch1_records.jsonl')
    batch1_paths = sorted({r['path'] for r in batch1_records})
    batch1_confirmed = [r for r in batch1_records if r.get('confirmed_error') and r.get('final_counted')]

    record_names = ('sub1_records.jsonl', 'sub2_records.jsonl',
                    'sub3_records.jsonl', 'sub4_records.jsonl')
    batch2_records = [r for name in record_names for r in read_jsonl(OUT_DIR / 'batch2' / name)]
    confirmed = batch1_confirmed + [r for r in batch2_records if r.get('status', '').startswith('已修复')]
    severity = Counter(r.get('severity', '?') for r in confirmed)
    pending = [r for r in batch2_records if r.get('status') == '待复核']
    pr7_records = [r for name in ('sub3_records.jsonl', 'sub4_records.jsonl')
                   for r in read_jsonl(OUT_DIR / 'batch2' / name)]
    pr7_confirmed = [r for r in pr7_records if r.get('status', '').startswith('已修复')]
    pr7_pending = [r for r in pr7_records if r.get('status') == '待复核']

    status = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'base_commit': 'd28ea7fec82f2131de4df36b177168d85bbbae49',
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
            'batch2_report_reviewed_count': review_summary['reviewed_pages'],
            'batch2_unreviewed_count': review_summary['unreviewed_pages'],
            'batch2_evidence_backed_pages': review_summary['evidence_backed_pages'],
            'batch2_report_only_pages': review_summary['report_only_pages'],
            'full_text_confirmed_claim': False,
            'status_note': '“已完成本批 AI 审校报告”仅表示有报告/记录；除 evidence_ids 对应内容外，不表示全文语义确认。',
            'page_status': {p: review_map[p] for p in sorted(review_map)},
        },
        'pr7_integration': {
            'confirmed_count': len(pr7_confirmed),
            'confirmed_ids': [r['id'] for r in pr7_confirmed],
            'pending_count': len(pr7_pending),
            'pending_records': pr7_pending,
            'note': 'PR #7 的10项确认修订与8项待复核记录均从实际记录文件读取。',
        },
        'confirmed_errors': {
            'count': len(confirmed),
            'severity': dict(sorted(severity.items())),
            'ids': [r.get('id') for r in confirmed],
        },
        'pending': {
            'count': len(pending),
            'qualified_ids': review_summary['pending_revision_ids'],
            'by_subbatch': {
                name: [r for r in read_jsonl(OUT_DIR / 'batch2' / name) if r.get('status') == '待复核']
                for name in record_names
            },
        },
        'history': {
            'merged_prs': [2, 3, 5],
            'closed_stale_prs': [4],
            'pr4_reason': '准备分支基于过期基线；正文修订已由 #2/#3/#5 合入 main，相对 main 的删除项不能合并。',
            'other_active_branches': ['fix/pages-quality-checks'],
        },
        'merge_dependency': {
            'pr7_merged': True,
            'pr7_merge_commit': 'd28ea7fec82f2131de4df36b177168d85bbbae49',
            'reason': '本总账基于 PR #7 合并后的 main 重新生成；第51—100篇状态与10项修订已从实际记录文件读取。',
            'current_queue_status': '第二批100篇均有报告或记录；未审校页面仅存在于全站其余页面。',
        },
        'known_issues': [
            {'id': 'AUDIT-001', 'issue': 'README 页面数已由6,576修正为实际扫描值 %d' % len(html), 'status': '已修复'},
            {'id': 'AUDIT-002', 'issue': '搜索索引 %d 页，HTML %d 页，原始缺失 %d、陈旧 %d；缺失项需区分导航/工具页与疑似正文' % (len(search_paths), len(html), len(missing_from_search), len(stale_search)), 'status': '已分类'},
            {'id': 'AUDIT-003', 'issue': '第一批完整30篇页面清单缺少结构化记录，无法逐页机器复核', 'status': '证据缺口'},
            {'id': 'AUDIT-004', 'issue': '子批次2仍有英文482块、中文636块 pending', 'status': '待复核'},
            {'id': 'AUDIT-005', 'issue': '风险索引中的P0为路径关键词启发式审校优先级；29篇未审校P0表示自动判定为高风险、尚待复核，不代表已确认错误严重程度', 'status': '表述已修正'},
            {'id': 'AUDIT-006', 'issue': 'PR #8 已合并且同样改动 doc/search.html 与 zh-search.js；PR #6 仅保留搜索页 noindex，未触碰移动逻辑，合并 main 后自动合并成功，仍需人工复核两处搜索改动共存结果', 'status': '需人工复核'},
        ],
        'next_queue': batch2_queue,
        'queue_size': len(batch2_queue),
        'unreviewed_pages_count': max(0, len(html) - review_summary['reviewed_pages']),
        'unreviewed_count_note': '全站页面数减去第二批有报告的页面数；未把第一批旧报告声明追加为机器确认覆盖。',
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
        f"| 第二批已完成 AI 审校报告 | {review_summary['reviewed_pages']} |",
        f"| 其中部分有证据支持 | {review_summary['evidence_backed_pages']} |",
        f"| 第二批未审校 | {review_summary['unreviewed_pages']} |",
        f"| 全站未审校页面（保守估计） | {status['unreviewed_pages_count']} |",
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
        '- 第二批：状态从实际存在的报告、记录、覆盖与证据文件读取；100 篇均有 AI 审校报告，但未把报告等同于全文语义确认。',
        f"- PR #7 新增：10 项确认修订、8 项待复核记录已纳入总账；其中 {review_summary['evidence_backed_pages']} 页有部分证据支持。",
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
        '- PR #2/#3/#5/#7/#8 已合并。',
        '- PR #4 为过期准备分支，已关闭并记录原因；无独有有效修改需要迁移。',
        '- PR #7 合并提交：`d28ea7fec82f2131de4df36b177168d85bbbae49`。',
        '- PR #8 已合并且涉及 `doc/search.html` 与移动搜索脚本；PR #6 未修改其移动代码，只保留自身的搜索页 noindex。',
        '',
        '## 7. 合并依赖',
        '',
        '- PR #7 已合并，本总账基于其后的最新 main 生成。',
        '- PR #6 仍保持 open，未自动合并。',
        '- PR #8 已合并，未在本轮修改或重新合并。',
        '',
        '## 8. 下一步队列',
        '',
        f'第二批自动队列共 {len(batch2_queue)} 篇。全站保守未审校页面 {status["unreviewed_pages_count"]} 篇，需按风险优先级继续。',
        '',
        '本总账只记录可复核事实；自动检查覆盖不等于语义审校完成。',
    ]
    (OUT_DIR / 'project_master_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('html', len(html), 'search', len(search_paths), 'queue', len(batch2_queue), 'confirmed', len(confirmed), 'pending', len(pending))

if __name__ == '__main__':
    main()
