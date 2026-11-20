'use strict';
// Bridge for reproducible audits. It calls the site's actual zh-search.js API.
const api = require('../doc/_static/zh-search.js');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  const payload = JSON.parse(input);
  const pages = payload.pages || [];
  const queries = payload.queries || [];
  const output = queries.map(item => {
    const parsed = api.parseQuery(item.query);
    const results = api.search(pages, item.query);
    return {
      query: item.query,
      id: item.id,
      kind: item.kind,
      expected: item.expected || null,
      hasChinese: api.hasChinese(item.query),
      positive: parsed.positive,
      negative: parsed.negative,
      count: results.length,
      top: results.slice(0, 5).map(r => ({
        path: r.path, title: r.title, score: r.score, snippet: r.snippet,
      })),
    };
  });
  process.stdout.write(JSON.stringify(output));
});
