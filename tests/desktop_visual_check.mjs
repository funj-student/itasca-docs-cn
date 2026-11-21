/**
 * Desktop visual-defect assertions for the TOC iframe, toggle button and
 * title-only placeholder pages. Failures set process.exitCode = 1.
 *
 * BASE_URL must include the GitHub Pages subpath /itasca-docs-cn/.
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8771/itasca-docs-cn';
const OUT = process.env.OUT || path.resolve('_toc_artifacts');
const PHASE = process.env.PHASE || 'visual';
const WIDTHS = (process.env.WIDTHS || '1280,1440,1664,1920').split(',').map(Number).filter(Boolean);
const PAGES = (process.env.PAGES || [
  'doc/common/docproject/source/manual/coupling/projects/tutorials/tutorials.html',
  'index.html'
].join(',')).split(',').filter(Boolean);
const ENGINES = (process.env.ENGINES || 'chromium,webkit').split(',').filter(Boolean);
if (!BASE.includes('/itasca-docs-cn')) { console.error('BASE_URL 必须包含 /itasca-docs-cn'); process.exit(1); }
fs.mkdirSync(OUT, { recursive: true });

const assertions = [];
const samples = [];
const current = { engine: '', width: 0, page: '' };

function check(name, ok, detail, severity = 'fail') {
  const rec = { id: assertions.length + 1, name, ok: !!ok, severity, detail, ...current };
  assertions.push(rec);
  if (!ok && severity === 'fail') console.error(`FAIL [${rec.engine}/${rec.width}/${rec.page}] ${name}: ${JSON.stringify(detail)}`);
  return rec;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

function luminance(rgb) {
  const parts = String(rgb).match(/[\d.]+/g);
  if (!parts || parts.length < 3) return null;
  const c = parts.slice(0, 3).map(Number).map(v => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function contrast(a, b) {
  const la = luminance(a), lb = luminance(b);
  if (la === null || lb === null) return null;
  return Math.round(((Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)) * 100) / 100;
}

async function open(browser, engineName, width, pagePath) {
  const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  const response = await page.goto(`${BASE}/${pagePath}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  if (!response || response.status() >= 400) throw new Error('HTTP ' + (response && response.status()));
  await page.waitForFunction(() => !!window.ItascaNav, null, { timeout: 20000 });
  await sleep(1400);
  return { context, page, errors };
}

async function shot(page, suffix) {
  const label = current.page.replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 55);
  const file = path.join(OUT, `${PHASE}_${current.engine}_${current.width}_${label}_${suffix}.png`);
  try { await page.screenshot({ path: file, timeout: 60000, animations: 'disabled' }); }
  catch (e) { check('screenshot evidence captured', false, { file, error: String(e) }, 'warn'); }
  return file;
}

async function inspectIframe(page) {
  const frame = page.frames().find(f => f.url().includes('navtree.html'));
  check('目录 iframe 已加载', !!frame, {});
  if (!frame) return null;
  await frame.waitForSelector('.jstree-anchor', { timeout: 15000 });
  const sidebarBg = await page.evaluate(() => getComputedStyle(document.getElementById('mySidenav')).backgroundColor);
  const info = await frame.evaluate(sidebarBackground => {
    const q = s => document.querySelector(s);
    const rect = e => { const r = e.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), right: Math.round(r.right) }; };
    const ocl = q('.jstree-ocl');
    const anchor = q('.jstree-anchor');
    const clicked = q('.jstree-clicked');
    const anchors = [...document.querySelectorAll('.jstree-anchor')];
    return {
      innerWidth, scrollX: Math.round(window.scrollX),
      docScrollWidth: document.documentElement.scrollWidth,
      ocl: ocl ? { ...rect(ocl), color: getComputedStyle(ocl).color } : null,
      anchor: anchor ? { ...rect(anchor), color: getComputedStyle(anchor).color, bg: getComputedStyle(anchor).backgroundColor } : null,
      clicked: clicked ? { ...rect(clicked), color: getComputedStyle(clicked).color, bg: getComputedStyle(clicked).backgroundColor, text: clicked.textContent.trim().slice(0, 50) } : null,
      sidebarBackground,
      clippedLeft: anchors.filter(a => a.getBoundingClientRect().x < 6).length,
      clippedRight: anchors.filter(a => a.getBoundingClientRect().right > innerWidth + 2).length
    };
  }, sidebarBg);

  check('一级目录图标未从 iframe 左侧被裁切', !!info.ocl && info.ocl.x >= 6, { ocl: info.ocl });
  check('一级目录文字未从 iframe 左侧被裁切', !!info.anchor && info.anchor.x >= 20, { anchor: info.anchor });
  check('目录条目未从 iframe 右侧被裁切', info.clippedRight === 0 && info.docScrollWidth <= info.innerWidth + 2,
    { clippedRight: info.clippedRight, docScrollWidth: info.docScrollWidth, innerWidth: info.innerWidth });
  check('目录文字与侧栏背景对比度充足', contrast(info.anchor && info.anchor.color, sidebarBg) >= 4.5,
    { color: info.anchor && info.anchor.color, bg: sidebarBg, ratio: contrast(info.anchor && info.anchor.color, sidebarBg) });
  // 只有当前页在目录树中有对应节点时才存在选中项；首页没有选中节点属正常。
  check('选中项文字与背景对比度充足', !info.clicked || contrast(info.clicked.color, info.clicked.bg) >= 4.5,
    { clicked: info.clicked, ratio: info.clicked && contrast(info.clicked.color, info.clicked.bg) });

  // 展开多级节点后再次检查边界与水平滚动
  for (let i = 0; i < 6; i++) {
    const closed = frame.locator('.jstree-closed > .jstree-ocl');
    if (!await closed.count()) break;
    try { await closed.first().click({ timeout: 2500 }); await sleep(90); } catch (e) { /* 断言判定 */ }
  }
  const after = await frame.evaluate(() => {
    const anchors = [...document.querySelectorAll('.jstree-anchor')];
    const visible = anchors.filter(a => { const r = a.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < window.innerHeight; });
    return {
      scrollX: Math.round(window.scrollX),
      docScrollWidth: document.documentElement.scrollWidth,
      innerWidth,
      firstX: visible.length ? Math.round(visible[0].getBoundingClientRect().x) : null,
      clippedLeft: visible.filter(a => a.getBoundingClientRect().x < 6).length,
      clippedRight: visible.filter(a => a.getBoundingClientRect().right > window.innerWidth + 2).length,
      nodeCount: anchors.length
    };
  });
  check('展开后图标与文字仍完整可见', after.clippedLeft === 0 && after.clippedRight === 0, after);
  check('展开与选中不产生水平滚动', after.scrollX === 0 && after.docScrollWidth <= after.innerWidth + 2, after);
  return { before: info, after };
}

async function inspectButton(page) {
  const data = await page.evaluate(() => {
    const btn = document.getElementById('navbutton');
    const r = btn.getBoundingClientRect();
    const cs = getComputedStyle(btn);
    const kids = [...btn.children].map(c => {
      const kr = c.getBoundingClientRect();
      return { text: c.textContent.trim(), cls: c.className, x: Math.round(kr.x), y: Math.round(kr.y), w: Math.round(kr.width), h: Math.round(kr.height) };
    });
    const h1 = document.querySelector('#mainbody h1');
    const hr = h1 ? h1.getBoundingClientRect() : null;
    return {
      rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      whiteSpace: cs.whiteSpace, display: cs.display, kids,
      h1: hr ? { x: Math.round(hr.x), y: Math.round(hr.y), w: Math.round(hr.width), h: Math.round(hr.height) } : null
    };
  });
  const icon = data.kids.find(k => k.cls.includes('wb-nav-icon'));
  const label = data.kids.find(k => k.cls.includes('wb-nav-label'));
  check('目录按钮图标与文字为横向排列', !!icon && !!label && icon.x < label.x && Math.abs(icon.y - label.y) <= 12, data);
  check('目录按钮文字未折成多行', !!label && label.h <= 26 && data.whiteSpace === 'nowrap', { label, whiteSpace: data.whiteSpace });
  check('目录按钮宽度自适应内容', data.rect.w >= (icon ? icon.w : 0) + (label ? label.w : 0), { rect: data.rect, kids: data.kids });
  check('目录按钮与侧栏边界保持间距', data.rect.x >= 355, { x: data.rect.x });
  if (data.h1) {
    const overlap = Math.max(0, Math.min(data.rect.x + data.rect.w, data.h1.x + data.h1.w) - Math.max(data.rect.x, data.h1.x)) *
      Math.max(0, Math.min(data.rect.y + data.rect.h, data.h1.y + data.h1.h) - Math.max(data.rect.y, data.h1.y));
    check('目录按钮不遮挡正文标题', overlap === 0, { overlap, button: data.rect, h1: data.h1 });
  }
  return data;
}

async function inspectPlaceholder(page) {
  const data = await page.evaluate(() => {
    const mb = document.getElementById('mainbody');
    const bottom = document.getElementById('mainbottom1');
    return {
      mainbodyHeight: Math.round(mb.getBoundingClientRect().height),
      minHeight: getComputedStyle(mb).minHeight,
      bottomY: Math.round(bottom.getBoundingClientRect().y),
      docHeight: document.documentElement.scrollHeight,
      viewportHeight: window.innerHeight,
      bottomLinks: bottom.querySelectorAll('a').length
    };
  });
  check('占位页正文最小高度已取消', data.mainbodyHeight < 300, data);
  check('占位页底部导航出现在首屏', data.bottomY < 400, data);
  check('占位页底部导航链接仍存在且可达', data.bottomLinks > 0 && data.docHeight >= data.bottomY, data);
  return data;
}

for (const engineName of ENGINES) {
  const engine = engineName === 'webkit' ? webkit : chromium;
  const launchOptions = { headless: true };
  if (engineName === 'chromium' && process.env.CHROMIUM_EXEC) launchOptions.executablePath = process.env.CHROMIUM_EXEC;
  let browser;
  try { browser = await engine.launch(launchOptions); }
  catch (e) { check('浏览器启动成功', false, { engine: engineName, error: String(e) }); continue; }

  for (const width of WIDTHS) {
    for (const pagePath of PAGES) {
      current.engine = engineName; current.width = width; current.page = pagePath;
      let context;
      try {
        const prepared = await open(browser, engineName, width, pagePath);
        context = prepared.context;
        const page = prepared.page;
        await shot(page, 'open');
        const buttonOpen = await inspectButton(page);
        const toc = await inspectIframe(page);
        let placeholder = null;
        if (/tutorials\.html$/.test(pagePath)) placeholder = await inspectPlaceholder(page);

        // 关闭目录后截图并确认按钮仍正常
        await page.locator('#navbutton').click();
        await sleep(900);
        const closedOpen = await page.evaluate(() => !document.body.classList.contains('nav-open'));
        check('目录可收起', closedOpen, {});
        await shot(page, 'closed');
        const buttonClosed = await page.evaluate(() => {
          const btn = document.getElementById('navbutton');
          const r = btn.getBoundingClientRect();
          const kids = [...btn.children].map(c => { const kr = c.getBoundingClientRect(); return { text: c.textContent.trim(), x: Math.round(kr.x), y: Math.round(kr.y), h: Math.round(kr.height) }; });
          return { x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height), kids };
        });
        check('收起后按钮仍为横向且尺寸正常', buttonClosed.w >= 50 && buttonClosed.h <= 40 &&
          buttonClosed.kids.length === 2 && Math.abs(buttonClosed.kids[0].y - buttonClosed.kids[1].y) <= 12, buttonClosed);
        for (const err of prepared.errors) {
          check('无意外页面错误', false, { error: err }, /Cannot load blob:|favicon/i.test(err) ? 'warn' : 'fail');
        }
        samples.push({ engine: engineName, width, page: pagePath, buttonOpen, toc, placeholder, buttonClosed });
      } catch (e) {
        check('页面视觉测试未抛出异常', false, { error: String(e) });
      } finally { if (context) await context.close(); }
    }
  }
  await browser.close();
}

fs.writeFileSync(path.join(OUT, `visual_report_${PHASE}.json`), JSON.stringify({ assertions, samples }, null, 2));
const failed = assertions.filter(a => !a.ok && a.severity === 'fail');
console.log(JSON.stringify({ phase: PHASE, assertions: assertions.length,
  passed: assertions.filter(a => a.ok).length, failed: failed.length,
  warnings: assertions.filter(a => !a.ok && a.severity === 'warn').length }, null, 2));
if (failed.length) process.exitCode = 1;
