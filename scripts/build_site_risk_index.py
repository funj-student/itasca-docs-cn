#!/usr/bin/env python3
"""Build a reproducible whole-site review index with heuristic priorities.

review_priority_candidate is P0/P1/P2/P3 only for work ordering. It is NOT an
actually confirmed error severity; severity_confirmed stays null without evidence.
"""
from pathlib import Path
import json
from collections import Counter
from datetime import datetime, timezone

from review_status import build_review_status_map

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'doc'
OUT = ROOT / 'translation_review/site_risk_index.jsonl'


def classify(path):
    low = path.lower()
    product = path.split('/')[0]
    if product not in {'flac3d', '3dec', 'pfc', 'common'}:
        product = 'other'
    if '/cmd_' in low or '_commands/' in low:
        kind, risk = 'command', 'P1'
    elif '/fish' in low:
        kind, risk = 'fish', 'P1'
    elif '/problemsolving/' in low or '/tutorials/' in low:
        kind, risk = 'tutorial', 'P2'
    elif '/theory/' in low:
        kind, risk = 'theory', 'P2'
    elif '/examples/' in low or '/verification/' in low:
        kind, risk = 'example', 'P3'
    elif '/python/' in low or low.endswith('.py.html'):
        kind, risk = 'python', 'P2'
    elif low.endswith(('contents.html', 'genindex.html', 'search.html', 'navtree.html', 'alltree.html')):
        kind, risk = 'navigation', 'P3'
    else:
        kind, risk = 'other', 'P3'
    if any(word in low for word in ('warning', 'stability', 'timestep', 'damping', 'initial-stress', 'initialize-stresses')):
        risk = 'P0'
    return product, kind, risk


def main():
    page_list = [json.loads(l) for l in
                 (ROOT / 'translation_review/batch2/page_list.jsonl').read_text(encoding='utf-8').splitlines()]
    review_map = build_review_status_map(page_list)
    rows = []
    for p in sorted(DOC.rglob('*.html')):
        rel = p.relative_to(DOC).as_posix()
        product, kind, risk = classify(rel)
        info = review_map.get(rel)
        if info:
            status = info['review_status']
            status_label = info['status_label']
            evidence_status = info['evidence_status']
            evidence_ids = info['evidence_ids']
            pending_ids = info['pending_ids']
            semantic_status = ('partial_evidence_backed' if evidence_ids else 'report_only_not_verified')
        else:
            status = 'not_reviewed'
            status_label = '未审校'
            evidence_status = 'none'
            evidence_ids = []
            pending_ids = []
            semantic_status = 'unknown'
        rows.append({
            'path': rel,
            'source_url': 'https://docs.itascacg.com/flac3d700/' + rel,
            'product': product, 'type': kind,
            'review_priority_candidate': risk,
            'risk_basis': 'heuristic_path_keywords',
            'severity_confirmed': None,
            'review_status': status,
            'status_label': status_label,
            'evidence_status': evidence_status,
            'evidence_ids': evidence_ids,
            'pending_ids': pending_ids,
            'full_text_confirmed': False,
            'semantic_status': semantic_status,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        })
    OUT.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8')
    c = Counter((r['review_priority_candidate'], r['review_status']) for r in rows)
    reviewed = sum(1 for r in rows if r['review_status'] == 'completed_ai_review_report')
    queued = sum(1 for r in rows if r['review_status'] == 'not_reviewed')
    print('rows', len(rows), 'reviewed', reviewed, 'not_reviewed', queued)
    for k, v in sorted(c.items()):
        print(k, v)

if __name__ == '__main__':
    main()
