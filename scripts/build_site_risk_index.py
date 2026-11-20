#!/usr/bin/env python3
"""Build a reproducible whole-site review index with heuristic priorities.

review_priority_candidate is P0/P1/P2/P3 only for work ordering. It is NOT an
actually confirmed error severity; severity_confirmed stays null without evidence.
"""
from pathlib import Path
import json
from collections import Counter
from datetime import datetime, timezone

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
    reviewed = {json.loads(l)['path'] for l in
                (ROOT / 'translation_review/batch2/page_list.jsonl').read_text(encoding='utf-8').splitlines()[:50]}
    queued = {json.loads(l)['path'] for l in
              (ROOT / 'translation_review/batch2/page_list.jsonl').read_text(encoding='utf-8').splitlines()[50:]}
    rows = []
    for p in sorted(DOC.rglob('*.html')):
        rel = p.relative_to(DOC).as_posix()
        product, kind, risk = classify(rel)
        status = 'reviewed_batch2_1_50' if rel in reviewed else ('queued_batch2_51_100' if rel in queued else 'not_reviewed')
        rows.append({
            'path': rel,
            'source_url': 'https://docs.itascacg.com/flac3d700/' + rel,
            'product': product, 'type': kind,
            'review_priority_candidate': risk,
            'risk_basis': 'heuristic_path_keywords',
            'severity_confirmed': None,
            'review_status': status,
            'semantic_status': 'unknown' if status.startswith('not_reviewed') else 'see_batch_records',
            'generated_at': datetime.now(timezone.utc).isoformat(),
        })
    OUT.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8')
    c = Counter((r['review_priority_candidate'], r['review_status']) for r in rows)
    print('rows', len(rows), 'reviewed', len(reviewed), 'queued', len(queued))
    for k, v in sorted(c.items()):
        print(k, v)

if __name__ == '__main__':
    main()
