#!/usr/bin/env python3
"""Annotate sub3/sub4 coverage with honest evidence semantics."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

def raw_counts(path):
    t = (ROOT / 'doc' / path).read_text(encoding='utf-8', errors='ignore')
    pre_lines = 0
    for block in re.findall(r'<pre\b[^>]*>(.*?)</pre>', t, flags=re.S | re.I):
        pre_lines += len([x for x in re.split(r'\r?\n', block) if x.strip()])
    return {
        'p_elements': len(re.findall(r'<p\b', t, flags=re.I)),
        'dt_elements': len(re.findall(r'<dt\b', t, flags=re.I)),
        'dd_elements': len(re.findall(r'<dd\b', t, flags=re.I)),
        'li_elements': len(re.findall(r'<li\b', t, flags=re.I)),
        'pre_lines': pre_lines,
    }

for sub in ('sub3', 'sub4'):
    cov_path = ROOT / 'translation_review/batch2' / f'{sub}_coverage.jsonl'
    rec_path = ROOT / 'translation_review/batch2' / f'{sub}_records.jsonl'
    records = [json.loads(l) for l in rec_path.read_text(encoding='utf-8').splitlines()]
    rows = []
    for line in cov_path.read_text(encoding='utf-8').splitlines():
        r = json.loads(line)
        r.pop('main_body_checked_by_ai_reported', None)
        fixed = [x for x in records if x['path'] == r['path'] and x['status'].startswith('已修复')]
        ids = [x['id'] for x in fixed]
        r['ai_report_claim'] = True
        r['ai_review_count_basis'] = (
            'AI 审校员报告中的段落计数，粒度为更细的正文段/关键字说明/公式或代码行；'
            '与 alignment 的文本块不是同一计数单位，不能作为逐块语义确认。'
        )
        r['count_unit_comparison'] = {
            'alignment_en_blocks': r['en_blocks'],
            'alignment_zh_blocks': r['zh_blocks'],
            'ai_reported_paragraphs': r['ai_reviewed_paragraphs_reported'],
            'raw_html_elements': raw_counts(r['path']),
        }
        r['semantic_confirmation_status'] = 'evidence_backed' if fixed else 'report_only_not_verified'
        r['evidence_ids'] = ids
        r['verified_evidence'] = [{
            'id': x['id'], 'source_url': x['source_url'], 'english_text': x['english_text'],
            'before_text': x['before_text'], 'after_text': x['after_text'],
            'locator': x['locator'], 'reason': x['technical_basis'],
        } for x in fixed]
        r['pending_semantic_blocks_en'] = max(0, r['en_blocks'] - len(fixed))
        r['review_basis'] = 'AI 审校员报告 + 证据记录；非人工专业终审'
        rows.append(r)
    cov_path.write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in rows) + '\n', encoding='utf-8')
    print(sub, 'rows', len(rows), 'evidence-backed', sum(1 for x in rows if x['semantic_confirmation_status'] == 'evidence_backed'))
