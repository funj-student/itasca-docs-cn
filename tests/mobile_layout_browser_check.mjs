import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:8765';
const OUT = path.join(ROOT, process.env.REPORT_NAME || 'tests/mobile_layout_browser_report.json');
const SHOT_DIR = path.join(ROOT, 'tests/mobile_layout_screenshots');
const CANDIDATES = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/mobile_layout_candidates.json'), 'utf8'));
const ALL_WIDTHS = [320, 360, 375, 390, 430, 768, 959, 1024, 1280, 1440, 1920];
const MOBILE_WIDTHS = [320, 360, 375, 390, 430, 768, 959];
const FILTER = process.env.FILTER || '';
const MODE = process.env.MODE || 'representative';
const WIDTHS = (process.env.WIDTHS || '').split(',').filter(Boolean).map(Number);

fs.mkdirSync(SHOT_DIR, { recursive: true });

function selectPages() {
  const p1 = CANDIDATES.pages.filter(p => p.candidate_priority === 'P1').map(p => '/' + p.path);
  const representatives = new Set([
    '/', '/index.html', '/doc/search.html', '/doc/contents.html',
    '/doc/common/docproject/source/manual/scripting/fish_scripting/fish_statements.html',
    '/doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.create.html',
    '/doc/3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.create.html',
    '/doc/pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.create.html',
  ]);
  const groups = new Set();
  for (const p of CANDIDATES.pages) {
    for (const g of p.structure_groups) {
      if (g === '普通正文') continue;
      if (!groups.has(g)) {
        groups.add(g);
        representatives.add('/' + p.path);
      }
    }
  }
  let selected;
  if (MODE === 'p1') selected = p1;
  else if (MODE === 'custom') selected = [...representatives];
  else selected = [...representatives, ...p1.slice(0, 40)];
  if (FILTER) selected = selected.filter(p => p.includes(FILTER));
  return [...new Set(selected)];
}

const PAGE_PROBE = () => {
  const badAncestor = el => {
    let n = el;
    while (n && n !== document.body) {
      const id = (n.id || '').toLowerCase();
      const cls = (typeof n.className === 'string' ? n.className : '').toLowerCase();
      if (id.includes('sidebar') || id.includes('nav') || cls.includes('navbar') || cls.includes('sidebar') || cls.includes('drawer')) return true;
      n = n.parentElement;
    }
    return false;
  };
  const visible = el => {
    const cs = getComputedStyle(el);
    return cs.display !== 'none' && cs.visibility !== 'hidden' && Number(cs.opacity) > 0;
  };
  const selectorOf = el => {
    const id = el.id ? `#${el.id}` : '';
    const cls = typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).slice(0, 3).join('.') : '';
    return `${el.tagName.toLowerCase()}${id}${cls}`;
  };
  const clip = el => {
    if (el.scrollWidth <= el.clientWidth + 2) return false;
    const cs = getComputedStyle(el);
    return cs.overflowX === 'hidden' || cs.overflowX === 'clip';
  };
  const scrollable = el => {
    let n = el.parentElement;
    while (n && n !== document.body) {
      const cs = getComputedStyle(n);
      const mathHost = n.matches('.math, .MathJax, mjx-container');
      if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') &&
          (n.scrollWidth > n.clientWidth + 2 || mathHost)) return selectorOf(n);
      n = n.parentElement;
    }
    return null;
  };
  const offenders = [];
  const root = document.querySelector('#mainbody') || document.body;
  for (const el of root.querySelectorAll('*')) {
    if (!visible(el) || badAncestor(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const tag = el.tagName.toLowerCase();
    const cs = getComputedStyle(el);
    let type = null;
    if (r.right > innerWidth + 2 && cs.position !== 'fixed' && !scrollable(el)) type = 'extends-past-viewport';
    else if (clip(el)) type = 'clipped-text';
    else if ((tag === 'pre' || tag === 'code') && el.scrollWidth > el.clientWidth + 2 && !scrollable(el)) type = 'code-without-scroll';
    else if (tag === 'img' && r.width > innerWidth + 2 && !scrollable(el)) type = 'image-too-wide';
    else if (cs.whiteSpace === 'nowrap' && el.scrollWidth > el.clientWidth + 2 &&
             !['auto', 'scroll'].includes(cs.overflowX) && !scrollable(el)) type = 'nowrap-without-scroll';
    if (type) {
      offenders.push({
        type,
        selector: selectorOf(el),
        id: el.id || null,
        class: typeof el.className === 'string' ? el.className : null,
        text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 120),
        rect: { left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width) },
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        scrollableAncestor: scrollable(el),
      });
    }
  }
  const tables = [...root.querySelectorAll('table')].map((t, i) => {
    const r = t.getBoundingClientRect();
    return {
      index: i,
      id: t.id || null,
      columns: Math.max(...[...t.querySelectorAll('tr')].map(tr => tr.children.length), 0),
      right: Math.round(r.right),
      width: Math.round(r.width),
      scrollWidth: t.scrollWidth,
      clientWidth: t.clientWidth,
      scrollableAncestor: scrollable(t),
      clippedCells: [...t.querySelectorAll('td,th')].filter(clip).length,
    };
  });
  const tableIssues = tables.filter(t => t.clippedCells > 0 || ((t.right > innerWidth + 2 || t.scrollWidth > t.clientWidth + 2) && !t.scrollableAncestor));
  return {
    url: location.pathname,
    title: document.title,
    innerWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
    horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 2,
    offenders: offenders.slice(0, 30),
    offenderCount: offenders.length,
    tableCount: tables.length,
    tableIssues: tableIssues.slice(0, 20),
    confirmed: document.documentElement.scrollWidth > innerWidth + 2 || offenders.length > 0 || tableIssues.length > 0,
  };
};

const pages = selectPages();
const widths = WIDTHS.length ? WIDTHS : (MODE === 'p1' ? [360, 768] : ALL_WIDTHS);
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 360, height: 900 }, deviceScaleFactor: 1 });
const page = await context.newPage();
const results = [];
for (const p of pages) {
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(BASE_URL + p, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(120);
    const data = await page.evaluate(PAGE_PROBE);
    data.width = width;
    data.path = p;
    const safe = p.replace(/[^a-z0-9]+/gi, '_').replace(/^_|_$/g, '').slice(-90) || 'root';
    if (data.confirmed) {
      const shot = path.join(SHOT_DIR, `${safe}_${width}.png`);
      await page.screenshot({ path: shot, fullPage: false });
      data.screenshot = path.relative(ROOT, shot);
    } else if (process.env.SHOT_ALL === '1') {
      const shot = path.join(SHOT_DIR, `${safe}_after_${width}.png`);
      await page.screenshot({ path: shot, fullPage: false });
      data.screenshot = path.relative(ROOT, shot);
    }
    results.push(data);
  }
}
await browser.close();
const confirmed = results.filter(r => r.confirmed);
const summary = {
  generated_at: new Date().toISOString(),
  mode: MODE,
  widths,
  pages_checked: pages.length,
  checks: results.length,
  confirmed_checks: confirmed.length,
  confirmed_pages: [...new Set(confirmed.map(r => r.path))].length,
  by_type: confirmed.reduce((acc, r) => {
    for (const o of r.offenders) acc[o.type] = (acc[o.type] || 0) + 1;
    if (r.horizontalOverflow) acc['document-horizontal-overflow'] = (acc['document-horizontal-overflow'] || 0) + 1;
    for (const t of r.tableIssues) acc['table-layout-issue'] = (acc['table-layout-issue'] || 0) + 1;
    return acc;
  }, {}),
  results,
};
fs.writeFileSync(OUT, JSON.stringify(summary, null, 2));
console.log(JSON.stringify({ pages: pages.length, checks: results.length, confirmed: confirmed.length, by_type: summary.by_type, out: path.relative(ROOT, OUT) }, null, 2));
