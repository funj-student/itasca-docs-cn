#!/usr/bin/env python3
"""Evidence-driven review status for the batch-2 page list.

Review status is derived from files that actually exist in the repository.
A page with a review report is NOT the same as a page whose full text has
been semantically confirmed. Only explicitly stored evidence IDs count as
evidence-backed; all other reviewed pages remain report-only.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'translation_review/batch2'

RECORD_FILES = ('sub1_records.jsonl', 'sub2_records.jsonl',
                'sub3_records.jsonl', 'sub4_records.jsonl')
COVERAGE_FILES = ('sub2_block_coverage.jsonl', 'sub3_coverage.jsonl', 'sub4_coverage.jsonl')
VERIFIED_FILES = ('sub2_verified_pairs.jsonl',)


def _read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]


def build_review_status_map(page_list=None):
    if page_list is None:
        page_list = _read_jsonl(BATCH / 'page_list.jsonl')
    paths = {r['path'] for r in page_list}
    status = {p: {
        'review_status': 'not_reviewed',
        'status_label': '未审校',
        'full_text_confirmed': False,
        'evidence_status': 'none',
        'evidence_ids': [],
        'pending_ids': [],
        'record_sources': [],
        'record_count': 0,
    } for p in paths}

    for name in RECORD_FILES:
        for rec in _read_jsonl(BATCH / name):
            path = rec.get('path')
            if path not in status:
                continue
            s = status[path]
            s['record_count'] += 1
            if name not in s['record_sources']:
                s['record_sources'].append(name)
            rid = rec.get('id')
            if str(rec.get('status', '')).startswith('已修复'):
                if rid and rid not in s['evidence_ids']:
                    s['evidence_ids'].append(rid)
            elif rec.get('status') == '待复核':
                # Pending IDs are reused across sub-batches; qualify them.
                qualified = f'{name.split("_")[0]}:{rid}' if rid else None
                if qualified and qualified not in s['pending_ids']:
                    s['pending_ids'].append(qualified)

    report_by_subbatch = {1: 'sub1_report.md', 2: 'sub2_report.md',
                          3: 'sub3_report.md', 4: 'sub4_report.md'}
    for row in page_list:
        path = row.get('path')
        name = report_by_subbatch.get(row.get('subbatch'))
        if path in status and name and (BATCH / name).exists():
            sources = status[path]['record_sources']
            if name not in sources:
                sources.append(name)

    for name in VERIFIED_FILES:
        for rec in _read_jsonl(BATCH / name):
            path = rec.get('path')
            if path not in status:
                continue
            s = status[path]
            rid = rec.get('id')
            if rid and rid not in s['evidence_ids']:
                s['evidence_ids'].append(rid)
            if name not in s['record_sources']:
                s['record_sources'].append(name)

    for name in COVERAGE_FILES:
        for rec in _read_jsonl(BATCH / name):
            path = rec.get('path')
            if path not in status:
                continue
            s = status[path]
            if name not in s['record_sources']:
                s['record_sources'].append(name)
            for ev in rec.get('verified_evidence', []):
                rid = ev.get('id')
                if rid and rid not in s['evidence_ids']:
                    s['evidence_ids'].append(rid)

    for path, s in status.items():
        if s['record_sources']:
            s['review_status'] = 'completed_ai_review_report'
            s['status_label'] = '已完成本批 AI 审校报告'
            s['evidence_status'] = 'partial_evidence_backed' if s['evidence_ids'] else 'report_only'
        s['full_text_confirmed'] = False
    return status


def summarize(status_map):
    from collections import Counter
    c = Counter(s['review_status'] for s in status_map.values())
    return {
        'reviewed_pages': c['completed_ai_review_report'],
        'unreviewed_pages': c['not_reviewed'],
        'evidence_backed_pages': sum(1 for s in status_map.values() if s['evidence_status'] == 'partial_evidence_backed'),
        'report_only_pages': sum(1 for s in status_map.values() if s['evidence_status'] == 'report_only'),
        'confirmed_revision_ids': sorted({rid for s in status_map.values() for rid in s['evidence_ids']}),
        'pending_revision_ids': sorted({rid for s in status_map.values() for rid in s['pending_ids']}),
    }
