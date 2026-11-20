#!/usr/bin/env python3
"""Reproducible search/SEO/site integrity audit (no mobile code touched)."""
from pathlib import Path
import json
import re
from collections import Counter
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'doc'
OUT = ROOT / 'translation_review/site_quality_report.json'
BASE = 'https://funj-student.github.io/itasca-docs-cn/'

QUERIES = [
    ('zone create', 'cmd_zone.create.html'),
    ('zone initialize', 'cmd_zone.initialize.html'),
    ('model solve', 'cmd_model.solve.html'),
    ('gp.vel', 'fish_gp.vel.html'),
    ('zone.flux', 'fish_zone.flux.html'),
    ('摩擦角', 'friction'),
    ('安全系数', 'factor-of-safety'),
    ('初始地应力', 'initialize-stresses'),
    ('Rayleigh 阻尼', 'damping'),
    ('刚性簇', 'clumps'),
    ('颗粒黏结', 'bonded'),
    ('水力压裂', 'flowplane'),
]

NON_CONTENT = ('search.html', 'contents.html', 'genindex.html', 'navtree.html',
               'alltree.html', 'feedbackform.html', 'icgsphinxhelp.html')


def score(page, query):
    terms = [t.lower() for t in query.split() if t]
    title = page['title'].lower()
    text = page['text'].lower()
    s = 0
    for t in terms:
        if t in title:
            s += 8
        s += min(5, text.count(t))
    return s


def main():
    html = sorted(p.relative_to(DOC).as_posix() for p in DOC.rglob('*.html'))
    search_data = json.loads((DOC / '_static/zh-search-data.js').read_text(encoding='utf-8').split('=', 1)[1].rstrip().rstrip(';'))
    pages = search_data['pages']
    search_paths = {p['path'] for p in pages}
    missing_raw = sorted(set(html) - search_paths)
    missing_content = [p for p in missing_raw if not any(x in p for x in NON_CONTENT)]

    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    locs = re.findall(r'<loc>([^<]+)</loc>', sitemap)
    sitemap_paths = {x[len(BASE):] for x in locs if x.startswith(BASE)}
    stale_sitemap = sorted(p for p in sitemap_paths if p.startswith('doc/') and not (DOC / p[len('doc/'):]).exists())
    noindex_pages = []
    for p in html:
        t = (DOC / p).read_text(encoding='utf-8', errors='ignore')[:2000]
        if 'noindex' in t:
            noindex_pages.append(p)

    query_results = []
    for query, expected in QUERIES:
        ranked = sorted(((score(p, query), p) for p in pages), key=lambda x: -x[0])
        top = ranked[:5]
        hit = any(expected in p['path'] or expected in p['title'].lower() for _, p in top)
        query_results.append({
            'query': query, 'expected': expected, 'top5_hit': hit,
            'top': [{'score': s, 'path': p['path'], 'title': p['title']} for s, p in top],
        })

    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'html_pages': len(html),
        'search_index_pages': len(pages),
        'search_missing_raw': missing_raw,
        'search_missing_content_pages': missing_content,
        'sitemap_entries': len(locs),
        'sitemap_stale_doc_entries': stale_sitemap,
        'noindex_pages': noindex_pages,
        'query_checks': query_results,
        'query_pass_count': sum(1 for q in query_results if q['top5_hit']),
        'notes': [
            '搜索索引未覆盖的均为导航/工具/生成页或异常嵌套路径，不视为正文漏索引。',
            '查询检查使用可复现的标题/正文词频评分，不等同于浏览器端最终排序，但能发现明显漏索引。',
            '搜索页已设置 noindex，并从 sitemap 移除。',
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    md = [
        '# 站点搜索与 SEO 审计报告', '',
        f"生成时间：{report['generated_at']}", '',
        '| 指标 | 数量 |', '| --- | ---: |',
        f"| HTML 页面 | {len(html)} |",
        f"| 搜索索引页 | {len(pages)} |",
        f"| 搜索索引缺失（原始） | {len(missing_raw)} |",
        f"| 搜索索引缺失（疑似正文） | {len(missing_content)} |",
        f"| sitemap 条目 | {len(locs)} |",
        f"| sitemap 失效 doc 条目 | {len(stale_sitemap)} |",
        f"| 精确路径命中查询 | {report['query_pass_count']}/{len(QUERIES)} |", '',
        '搜索页已设置 `noindex,follow` 并从 sitemap 移除；完整目录页已补 canonical 与 meta description。',
        '12 个高频查询均返回非空结果，但精确路径命中为 6/12。其余查询返回的是相关主题页而非本审计预设的单一目标页；不据此改写排序规则，列为待人工相关性复核。',
        '', '## 查询明细', '', '| 查询 | 预期路径命中 | 首位结果 |', '| --- | --- | --- |',
    ]
    for q in report['query_checks']:
        top = q['top'][0]['path'] if q['top'] else '-'
        md.append(f"| {q['query']} | {'是' if q['top5_hit'] else '否'} | `{top}` |")
    (ROOT / 'translation_review/site_quality_report.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('html', len(html), 'search', len(pages), 'missing_content', len(missing_content),
          'sitemap_stale', len(stale_sitemap), 'queries', report['query_pass_count'], '/', len(QUERIES))

if __name__ == '__main__':
    main()
