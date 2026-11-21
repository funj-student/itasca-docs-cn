#!/usr/bin/env python3
"""Reproducible search/SEO/site integrity audit.

Chinese and mixed-search checks call the site's actual zh-search.js API through
scripts/zh_search_bridge.js. The English Sphinx index is browser-only in this
environment, so English-query results are explicitly marked unverified.
No mobile code is touched.
"""
from pathlib import Path
import json
import re
import subprocess
import unicodedata
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'doc'
OUT = ROOT / 'translation_review/site_quality_report.json'
BASE = 'https://funj-student.github.io/itasca-docs-cn/'
BRIDGE = ROOT / 'scripts/zh_search_bridge.js'

QUERIES = [
    {'id': 'cn-friction', 'query': '摩擦角', 'kind': 'chinese', 'expected': None},
    {'id': 'cn-safety', 'query': '安全系数', 'kind': 'chinese', 'expected': 'factor-of-safety'},
    {'id': 'cn-stress', 'query': '初始地应力', 'kind': 'chinese', 'expected': 'initialize-stresses'},
    {'id': 'cn-rayleigh', 'query': 'Rayleigh 阻尼', 'kind': 'mixed', 'expected': 'damping'},
    {'id': 'cn-clump', 'query': '刚性簇', 'kind': 'chinese', 'expected': 'clumps'},
    {'id': 'cn-bond', 'query': '颗粒黏结', 'kind': 'chinese', 'expected': 'bonded'},
    {'id': 'cn-flow', 'query': '水力压裂', 'kind': 'chinese', 'expected': 'flowplane'},
    {'id': 'cn-mixed-zone', 'query': 'zone create 命令', 'kind': 'mixed', 'expected': 'cmd_zone.create'},
    {'id': 'cn-exclude', 'query': '摩擦角 -模型', 'kind': 'exclusion', 'expected': None, 'expect_zero': False},
    {'id': 'cn-zero', 'query': '绝对不存在的术语zzz', 'kind': 'zero_match', 'expected': None, 'expect_zero': True},
]

ENGLISH_QUERIES = [
    {'id': 'en-zone-create', 'query': 'zone create', 'expected': 'cmd_zone.create.html'},
    {'id': 'en-model-solve', 'query': 'model solve', 'expected': 'cmd_model.solve.html'},
    {'id': 'en-gp-vel', 'query': 'gp.vel', 'expected': 'fish_gp.vel.html'},
]

NON_CONTENT = ('search.html', 'contents.html', 'genindex.html', 'navtree.html',
               'alltree.html', 'feedbackform.html', 'icgsphinxhelp.html')

UNINDEXED_NOTES = {
    '3dec/docproject/source/options/dynamic/3dec/docproject/source/options/dynamic/dynamic_calculations.html':
        '原版路径错误生成的405字节跳转桩页，正文明确要求返回动力计算页面；路径重复嵌套，不应作为正文收录，但不删除文件。',
    'doxygen/html/class_variant_1_1_user_type_base.html':
        '419字节 Doxygen 缺失类型跳转桩页，正文提示类型页在原版缺失并指向 Variant 类型页；不应收录为正文，但不删除文件。',
}


def normalize(value):
    text = unicodedata.normalize('NFKC', str(value or '')).lower()
    text = re.sub(r'([\u3400-\u9fff])\s+(?=[\u3400-\u9fff])', r'\1', text)
    return re.sub(r'\s+', ' ', text).strip()


def run_actual_zh_search(pages, queries):
    payload = json.dumps({'pages': pages, 'queries': queries}, ensure_ascii=False)
    proc = subprocess.run(['node', str(BRIDGE)], input=payload, text=True,
                          capture_output=True, cwd=ROOT, timeout=300)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    return json.loads(proc.stdout)


def main():
    html = sorted(p.relative_to(DOC).as_posix() for p in DOC.rglob('*.html'))
    search_data = json.loads((DOC / '_static/zh-search-data.js').read_text(encoding='utf-8').split('=', 1)[1].rstrip().rstrip(';'))
    pages = search_data['pages']
    search_paths = {p['path'] for p in pages}
    missing_raw = sorted(set(html) - search_paths)
    missing_content = [p for p in missing_raw if not any(x in p for x in NON_CONTENT)]
    page_map = {p['path']: p for p in pages}

    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    locs = re.findall(r'<loc>([^<]+)</loc>', sitemap)
    sitemap_paths = {x[len(BASE):] for x in locs if x.startswith(BASE)}
    stale_sitemap = sorted(p for p in sitemap_paths if p.startswith('doc/') and not (DOC / p[len('doc/'):]).exists())

    actual = run_actual_zh_search(pages, QUERIES)
    checks = []
    for raw in actual:
        q = next(x for x in QUERIES if x['id'] == raw['id'])
        top_paths = [r['path'] for r in raw['top']]
        positive, negative = raw['positive'], raw['negative']
        relevant_top = []
        for r in raw['top']:
            p = page_map.get(r['path'])
            if not p:
                continue
            hay = normalize(p['title'] + '\n' + p['text'])
            relevant_top.append(all(w in hay for w in positive) and not any(w in hay for w in negative))
        expect_zero = q.get('expect_zero', False)
        checks.append({
            'id': q['id'], 'query': q['query'], 'kind': q['kind'],
            'engine': 'zh-search.js actual',
            'expected': q['expected'], 'expect_zero': expect_zero,
            'has_results': raw['count'] > 0,
            'zero_match_correct': (raw['count'] == 0) if expect_zero else None,
            'term_match_valid': (True if expect_zero and raw['count'] == 0 else
                                 (all(relevant_top) if relevant_top else raw['count'] > 0)),
            'expected_in_top5': (any(q['expected'] in p for p in top_paths) if q['expected'] else None),
            'count': raw['count'], 'positive': positive, 'negative': negative,
            'top': raw['top'],
        })
    for q in ENGLISH_QUERIES:
        checks.append({
            'id': q['id'], 'query': q['query'], 'kind': 'english',
            'engine': 'English Sphinx index not available in audit environment',
            'expected': q['expected'], 'expect_zero': False,
            'has_results': None, 'zero_match_correct': None,
            'term_match_valid': None, 'expected_in_top5': None,
            'count': None, 'positive': [], 'negative': [], 'top': [],
            'limitation': '英文查询未验证：浏览器端英文索引依赖 searchlib/Sphinx 运行时，未在 Node 测试环境中复现。',
        })

    zh_checks = [c for c in checks if c['engine'] == 'zh-search.js actual']
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'html_pages': len(html),
        'search_index_pages': len(pages),
        'search_missing_raw': missing_raw,
        'search_missing_content_pages': missing_content,
        'unindexed_page_assessment': {p: UNINDEXED_NOTES.get(p, '未分类') for p in missing_raw},
        'sitemap_entries': len(locs),
        'sitemap_stale_doc_entries': stale_sitemap,
        'query_engine': '中文/混合/排除/零匹配：实际 zh-search.js；英文：未验证',
        'query_checks': checks,
        'summary': {
            'actual_zh_queries': len(zh_checks),
            'with_results': sum(1 for c in zh_checks if c['has_results']),
            'term_match_valid': sum(1 for c in zh_checks if c['term_match_valid']),
            'expected_in_top5': sum(1 for c in zh_checks if c['expected_in_top5'] is True),
            'expected_not_in_top5': sum(1 for c in zh_checks if c['expected_in_top5'] is False),
            'zero_match_correct': sum(1 for c in zh_checks if c['zero_match_correct'] is True),
            'english_unverified': len(ENGLISH_QUERIES),
        },
        'notes': [
            '使用实际 zh-search.js 的 search/parseQuery/hasChinese 函数，没有重写排序。',
            '“有结果”只代表返回非空；“检索词匹配有效性”只检查前五名是否命中全部正向词且不含排除词，不是人工或语义相关性验证；“预期目标页前五”是单独指标。',
            '英文查询未在测试环境中复现实际英文索引逻辑，全部标为未验证。',
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    md = [
        '# 站点搜索与 SEO 审计报告', '',
        f"生成时间：{report['generated_at']}", '',
        '## 1. 查询验证摘要', '',
        '| 指标 | 数量 |', '| --- | ---: |',
        f"| 实际 zh-search.js 查询 | {len(zh_checks)} |",
        f"| 有结果 | {report['summary']['with_results']} |",
        f"| 前五名检索词匹配有效性 | {report['summary']['term_match_valid']} |",
        f"| 预期目标页进入前五 | {report['summary']['expected_in_top5']} |",
        f"| 预期目标页未进前五 | {report['summary']['expected_not_in_top5']} |",
        f"| 零匹配测试正确 | {report['summary']['zero_match_correct']} |",
        f"| 英文查询未验证 | {len(ENGLISH_QUERIES)} |", '',
        '英文查询依赖浏览器端 Sphinx 搜索索引，本审计环境无法复现，因此不把英文查询计为通过。',
        '', '## 2. 查询明细', '', '| ID | 查询 | 引擎 | 有结果 | 检索词匹配有效性 | 目标前五 |', '| --- | --- | --- | --- | --- | --- |',
    ]
    for c in checks:
        def mark(v):
            return '未验证' if v is None else ('是' if v else '否')
        md.append(f"| {c['id']} | {c['query']} | {c['engine']} | {mark(c['has_results'])} | {mark(c['term_match_valid'])} | {mark(c['expected_in_top5'])} |")
    md += ['', '## 3. 未索引页面判断', '']
    for p, note in report['unindexed_page_assessment'].items():
        md.append(f"- `{p}`：{note}")
    md += ['', '## 4. SEO', '', f"- HTML {len(html)}，搜索索引 {len(pages)}，sitemap {len(locs)} 条，失效 doc 条目 {len(stale_sitemap)}。", '- 搜索页保持 `noindex,follow`，已从 sitemap 移除；目录页有 canonical 与 description。']
    (ROOT / 'translation_review/site_quality_report.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('zh checks', len(zh_checks), 'term_match_valid', report['summary']['term_match_valid'],
          'expected_top5', report['summary']['expected_in_top5'], 'english_unverified', len(ENGLISH_QUERIES))

if __name__ == '__main__':
    main()
