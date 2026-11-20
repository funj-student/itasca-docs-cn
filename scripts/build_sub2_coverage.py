#!/usr/bin/env python3
"""Build honest, traceable coverage records for batch 2 sub-batch 2.

Important semantics:
  * auto_strong / auto_semantic are PROGRAM results, not AI confirmation.
  * candidate_match / structure_candidate are program-found candidates only.
  * ai_confirmed is used ONLY when an explicit verified-pair evidence record
    with English text, Chinese text and a review reason exists.
  * pending means not verified. It is never silently relabelled as confirmed.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

SPEC = importlib.util.spec_from_file_location(
    'review_translation_batch', Path(__file__).with_name('review_translation_batch.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

NON_BODY_SECTIONS = ('mainbottom', 'navbutton', 'searchbox', 'maintop')
NON_BODY_PAT = re.compile(r'(Was this helpful|Updated:|Copyright|版权与免责声明)', re.I)
ALLOWED = {'auto_strong', 'auto_semantic', 'ai_confirmed', 'candidate_match',
           'structure_candidate', 'non_body', 'duplicate', 'pending'}


def norm(text):
    return re.sub(r'\s+', ' ', text).strip().lower()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sig_overlap(a, b):
    an, ai = M.signature_tokens(a['text'])
    bn, bi = M.signature_tokens(b['text'])
    return len(set(an) & set(bn)) + len(set(ai) & set(bi))


def concept_overlap(a, b):
    ec = M.concepts(a['text'], 'en') if a['_lang'] == 'en' else M.concepts(a['text'], 'zh')
    oc = M.concepts(b['text'], 'zh') if b['_lang'] == 'zh' else M.concepts(b['text'], 'en')
    return ec & oc


def candidate_score(a, b):
    """Conservative score. Same section alone is never sufficient."""
    same_section = bool(a['section']) and a['section'] == b['section']
    same_tag = a['tag'] == b['tag']
    exact = norm(a['text']) == norm(b['text'])
    sig = sig_overlap(a, b)
    concepts = len(concept_overlap(a, b))
    score = (3 if same_section else 0) + (1 if same_tag else 0) + (4 if exact else 0) + sig * 2 + concepts
    return score, {
        'same_section': same_section, 'same_tag': same_tag, 'exact_text': exact,
        'signature_overlap': sig, 'concept_overlap': concepts,
    }


def is_navigation(block):
    sec = block.get('section', '').lower()
    return any(sec.startswith(x) for x in NON_BODY_SECTIONS) or bool(NON_BODY_PAT.search(block['text']))


def is_structure(block):
    if block['tag'] in {'h1', 'h2', 'h3', 'h4', 'pre', 'div', 'td', 'th'}:
        return True
    if 'caption' in block['text'].lower():
        return True
    if any(x in block['text'].lower() for x in ('warning', 'note', '警告', '注意')):
        return True
    if block['tag'] in {'dt', 'li'}:
        return True
    return False


def apply_verified_evidence(rel, en, zh, status, pair, evidence):
    evidence_path = Path('translation_review/batch2/sub2_verified_pairs.jsonl')
    rows = [json.loads(l) for l in evidence_path.read_text(encoding='utf-8').splitlines()]
    used_e, used_z = set(), set()
    for row in rows:
        if row['path'] != rel:
            continue
        ec = [i for i, b in enumerate(en)
              if b['section'] == row['en_section'] and row['en_snippet'].lower() in b['text'].lower() and i not in used_e]
        zc = [i for i, b in enumerate(zh)
              if b['section'] == row['zh_section'] and row['zh_snippet'].lower() in b['text'].lower() and i not in used_z]
        if not ec or not zc:
            raise SystemExit(f'verified evidence {row["id"]} no longer matches current HTML: {rel}')
        for ei, zi in zip(ec, zc):
            for side, idx, other in [('en', ei, zi), ('zh', zi, ei)]:
                status[(side, idx)] = 'ai_confirmed'
                pair[(side, idx)] = other
                evidence[(side, idx)] = {
                    'type': 'verified_pair', 'evidence_id': row['id'],
                    'reason': row['reason'], 'source_record': row['source_record'],
                    'en_snippet': row['en_snippet'], 'zh_snippet': row['zh_snippet'],
                }
            used_e.add(ei); used_z.add(zi)
    return used_e, used_z


def main():
    pages_file, en_dir, page_list, out_blocks, out_summary, out_manifest = map(Path, sys.argv[1:7])
    en_dir = en_dir.resolve()
    rels = [l.strip() for l in pages_file.read_text(encoding='utf-8').splitlines() if l.strip()]
    page_map = {r['path']: r for r in map(json.loads, page_list.read_text(encoding='utf-8').splitlines())}
    issue_map = defaultdict(list)
    records_path = Path('translation_review/batch2/sub2_records.jsonl')
    for r in map(json.loads, records_path.read_text(encoding='utf-8').splitlines()):
        issue_map[r['path']].append(r['id'])

    all_blocks, summaries, manifest_files = [], [], {}
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    for rel in rels:
        en_path = en_dir / rel.replace('/', '_')
        zh_path = Path('doc') / rel
        en = M.blocks_with_context(en_path)
        zh = M.blocks_with_context(zh_path)
        for b in en: b['_lang'] = 'en'
        for b in zh: b['_lang'] = 'zh'
        zh_hash, en_hash = sha256(zh_path), sha256(en_path)
        manifest_files[rel] = {'zh_sha256': zh_hash, 'en_sha256': en_hash}

        status, pair, evidence = {}, {}, {}
        used_e, used_z = apply_verified_evidence(rel, en, zh, status, pair, evidence)

        es = [M.signature_tokens(b['text']) for b in en]
        zs = [M.signature_tokens(b['text']) for b in zh]
        strong = M.align_pairs(es, zs)
        semantic = M.semantic_align(en, zh, strong)
        for ei, zi in strong:
            if ('en', ei) in status or ('zh', zi) in status:
                continue
            for side, i, j in [('en', ei, zi), ('zh', zi, ei)]:
                status[(side, i)] = 'auto_strong'
                pair[(side, i)] = j
                evidence[(side, i)] = {'type': 'program_alignment', 'method': 'numeric/identifier signature'}
            used_e.add(ei); used_z.add(zi)
        for ei, zi, score in semantic:
            if ('en', ei) in status or ('zh', zi) in status:
                continue
            for side, i, j in [('en', ei, zi), ('zh', zi, ei)]:
                status[(side, i)] = 'auto_semantic'
                pair[(side, i)] = j
                evidence[(side, i)] = {'type': 'program_alignment', 'method': 'section/heading/concept', 'score': round(score, 2)}
            used_e.add(ei); used_z.add(zi)

        for lang, blocks, other, used_self, used_other in [
            ('en', en, zh, used_e, used_z), ('zh', zh, en, used_z, used_e)]:
            counts = Counter(norm(b['text']) for b in blocks)
            seen = Counter()
            for i, b in enumerate(blocks):
                key = (lang, i)
                if key in status:
                    continue
                seen[norm(b['text'])] += 1
                if is_navigation(b):
                    status[key] = 'non_body'
                    evidence[key] = {'type': 'structure_only', 'reason': 'navigation/footer/version block'}
                    continue
                if seen[norm(b['text'])] > 1 and counts[norm(b['text'])] > 1:
                    status[key] = 'duplicate'
                    evidence[key] = {'type': 'structure_only', 'reason': 'normalized text appears more than once'}
                    continue
                best, best_score, detail = None, 0, {}
                for j, ob in enumerate(other):
                    if j in used_other:
                        continue
                    sc, det = candidate_score(b, ob)
                    if sc > best_score:
                        best, best_score, detail = j, sc, det
                # Same section alone scores 3; require additional evidence.
                if best is None or best_score < 5:
                    status[key] = 'pending'
                    evidence[key] = {'type': 'candidate_only', 'reason': 'no reliable counterpart; not semantically verified',
                                     'best_score': best_score, 'best_detail': detail}
                    continue
                used_self.add(i); used_other.add(best)
                pair[key] = best
                if is_structure(b):
                    status[key] = 'structure_candidate'
                    evidence[key] = {'type': 'structure_candidate', 'matched_index': best,
                                     'score': best_score, 'detail': detail,
                                     'reason': 'structure correspondence only; semantic completeness not confirmed'}
                else:
                    status[key] = 'candidate_match'
                    evidence[key] = {'type': 'candidate_only', 'matched_index': best,
                                     'score': best_score, 'detail': detail,
                                     'reason': 'program candidate only; not AI-confirmed'}

        for lang, blocks in [('en', en), ('zh', zh)]:
            for i, b in enumerate(blocks):
                all_blocks.append({
                    'path': rel, 'side': lang, 'index': i, 'tag': b['tag'],
                    'section': b['section'], 'headings': [h for h in b['headings'] if h],
                    'text': b['text'], 'status': status.get((lang, i), 'pending'),
                    'matched_index': pair.get((lang, i)), 'evidence': evidence.get((lang, i), {}),
                    'input_sha256': zh_hash if lang == 'zh' else en_hash,
                    'git_head': head,
                })

        def c(lang, st):
            return sum(1 for r in all_blocks if r['path'] == rel and r['side'] == lang and r['status'] == st)
        summaries.append({
            'path': rel, 'category': page_map[rel]['category'],
            'en_blocks': len(en), 'zh_blocks': len(zh),
            'auto_strong_pairs': c('en', 'auto_strong'), 'auto_semantic_pairs': c('en', 'auto_semantic'),
            'ai_confirmed_en': c('en', 'ai_confirmed'), 'ai_confirmed_zh': c('zh', 'ai_confirmed'),
            'candidate_match_en': c('en', 'candidate_match'), 'candidate_match_zh': c('zh', 'candidate_match'),
            'structure_candidate_en': c('en', 'structure_candidate'), 'structure_candidate_zh': c('zh', 'structure_candidate'),
            'non_body_en': c('en', 'non_body'), 'non_body_zh': c('zh', 'non_body'),
            'duplicate_en': c('en', 'duplicate'), 'duplicate_zh': c('zh', 'duplicate'),
            'pending_en': c('en', 'pending'), 'pending_zh': c('zh', 'pending'),
            'issue_ids': issue_map[rel], 'en_sha256': en_hash, 'zh_sha256': zh_hash,
        })

    out_blocks.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in all_blocks) + '\n', encoding='utf-8')
    out_summary.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in summaries) + '\n', encoding='utf-8')
    out_manifest.write_text(json.dumps({
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'git_head': head, 'en_dir': str(en_dir),
        'files': manifest_files,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('blocks', len(all_blocks), 'pages', len(summaries), 'head', head[:8])

if __name__ == '__main__':
    main()
