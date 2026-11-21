/**
 * 官方桌面基线验收：侧栏/iframe 尺寸、⇄ 按钮、目录配色与缩进、占位页高度。
 * 失败时 process.exitCode = 1。BASE_URL 必须包含 /itasca-docs-cn/。
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8772/itasca-docs-cn';
const OUT = process.env.OUT || path.resolve('_official_artifacts');
const PHASE = process.env.PHASE || 'official';
const WIDTHS = (process.env.WIDTHS || '960,1280,1440,1664,1920').split(',').map(Number).filter(Boolean);
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

async function openPage(browser, engineName, width, pagePath) {
  const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  const response = await page.goto(`${BASE}/${pagePath}`, { waitUntil: 'load', timeout: 60000 });
  if (!response || response.status() >= 400) throw new Error('HTTP ' + (response && response.status()));
  await page.waitForFunction(() => !!window.ItascaNav, null, { timeout: 20000 });
  await sleep(1400);
  return { context, page, errors };
}

async function shot(page, suffix) {
  const label = current.page.replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 50);
  const file = path.join(OUT, `${PHASE}_${current.engine}_${current.width}_${label}_${suffix}.png`);
  try { await page.screenshot({ path: file, timeout: 60000, animations: 'disabled' }); }
  catch (e) { check('screenshot evidence captured', false, { file, error: String(e) }, 'warn'); }
  return file;
}

async function inspectParent(page) {
  const data = await page.evaluate(() => {
    const R = e => { const r = e.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
    const btn = document.getElementById('navbutton');
    const mb = document.getElementById('mainbody');
    const cs = getComputedStyle(mb);
    const h1 = document.querySelector('#mainbody h1');
    return {
      side: R(document.getElementById('mySidenav')),
      iframe: R(document.getElementById('toctobj2')),
      mainbody: { ...R(mb), padding: `${cs.paddingLeft}/${cs.paddingRight}`, minHeight: cs.minHeight, maxWidth: cs.maxWidth },
      button: { ...R(btn), text: btn.textContent.trim(), childCount: btn.children.length, aria: btn.getAttribute('aria-label') },
      h1: h1 ? R(h1) : null,
      navOpen: document.body.classList.contains('nav-open'),
      bottom: R(document.getElementById('mainbottom1')),
      docHeight: document.documentElement.scrollHeight,
      docWidth: document.documentElement.scrollWidth
    };
  });
  check('侧栏宽度为官方 350px', data.side.w === 350, data.side);
  check('目录 iframe 宽度为官方 390px', data.iframe.w === 390, data.iframe);
  check('正文宽度符合官方值', data.mainbody.w === (current.width >= 1280 ? 656 : 610), data.mainbody);
  check('正文内边距为官方 64px/32px', data.mainbody.padding === '64px/32px', data.mainbody);
  check('占位页最小高度为官方 640px', data.mainbody.minHeight === '640px', data.mainbody);
  check('桌面目录按钮显示官方 ⇄', data.button.text === '⇄' && data.button.childCount === 0, data.button);
  check('桌面目录按钮尺寸为官方 43x40', Math.abs(data.button.w - 43) <= 2 && Math.abs(data.button.h - 40) <= 2, data.button);
  check('目录展开时按钮位于官方 353px', Math.abs(data.button.x - 353) <= 2, data.button);
  check('目录展开时按钮可访问名称为“收起目录”', data.button.aria === '收起目录', data.button);
  if (/tutorials\.html$/.test(current.page)) {
    check('占位页底部导航位置符合官方 y≈784', Math.abs(data.bottom.y - 784) <= 3, data.bottom);
    check('占位页文档高度符合官方 y≈918', Math.abs(data.docHeight - 918) <= 30, { docHeight: data.docHeight });
  }
  check('页面无横向溢出', data.docWidth === current.width, { docWidth: data.docWidth });
  if (data.h1) {
    const overlap = Math.max(0, Math.min(data.button.x + data.button.w, data.h1.x + data.h1.w) - Math.max(data.button.x, data.h1.x)) *
      Math.max(0, Math.min(data.button.y + data.button.h, data.h1.y + data.h1.h) - Math.max(data.button.y, data.h1.y));
    check('目录按钮不遮挡标题', overlap === 0, { button: data.button, h1: data.h1 });
  }
  return data;
}

async function inspectFrame(page) {
  const frame = page.frames().find(f => f.url().includes('navtree.html'));
  check('目录 iframe 已加载', !!frame, {});
  if (!frame) return null;
  await frame.waitForSelector('.jstree-anchor', { timeout: 15000 });
  const info = await frame.evaluate(() => {
    const R = e => { const r = e.getBoundingClientRect(); return { x: Math.round(r.x), w: Math.round(r.width), right: Math.round(r.right) }; };
    const a = document.querySelector('.jstree-anchor');
    const o = document.querySelector('.jstree-ocl');
    const c = document.querySelector('.jstree-clicked');
    return {
      innerWidth, scrollX: Math.round(window.scrollX), docWidth: document.documentElement.scrollWidth,
      bodyColor: getComputedStyle(document.body).color,
      anchor: a ? { ...R(a), color: getComputedStyle(a).color } : null,
      ocl: o ? R(o) : null,
      clicked: c ? { ...R(c), color: getComputedStyle(c).color, bg: getComputedStyle(c).backgroundColor } : null,
      hasDesktopStyle: !!document.getElementById('wb-toc-desktop-style'),
      hasMobileStyle: !!document.getElementById('wb-toc-native-scroll')
    };
  });
  check('目录文档宽度保持官方 480px', info.docWidth === 480, info);
  check('目录文字颜色为官方 #9da3a8', info.bodyColor === 'rgb(157, 163, 168)', info);
  check('目录一级文字缩进为官方 32px', !!info.anchor && info.anchor.x === 32, info.anchor);
  check('目录箭头位置为官方 8px', !!info.ocl && info.ocl.x === 8, info.ocl);
  check('桌面端未注入自定义目录样式', !info.hasDesktopStyle, info);
  check('桌面端未误用移动端目录样式', !info.hasMobileStyle, info);
  check('目录初始无水平滚动', info.scrollX === 0, info);
  if (info.clicked) {
    check('选中项背景为官方 #37435c', info.clicked.bg === 'rgb(55, 67, 92)', info.clicked);
    check('选中项文字颜色为官方 #9da3a8', info.clicked.color === 'rgb(157, 163, 168)', info.clicked);
  }

  let expanded = 0;
  for (let i = 0; i < 6; i++) {
    const closed = frame.locator('.jstree-closed > .jstree-ocl');
    if (!await closed.count()) break;
    try { await closed.first().click({ timeout: 2500 }); expanded++; await sleep(100); } catch (e) { /* 断言判定 */ }
  }
  check('多级目录可连续展开', expanded >= 3, { expanded });
  const before = await frame.evaluate(() => ({ max: document.body.scrollHeight - window.innerHeight, sh: document.body.scrollHeight }));
  check('展开后目录内容可滚动', before.max > 0, before);
  const box = await page.locator('#toctobj2').boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  for (let i = 0; i < 6; i++) {
    const cur = await frame.evaluate(() => ({ y: Math.round(scrollY), max: Math.round(document.body.scrollHeight - innerHeight) }));
    if (cur.y >= cur.max - 2) break;
    await page.mouse.wheel(0, 3000); await sleep(260);
  }
  const bottom = await frame.evaluate(() => ({ y: Math.round(scrollY), max: Math.round(document.body.scrollHeight - innerHeight) }));
  check('目录可滚动到底部', bottom.y >= bottom.max - 2, bottom);
  for (let i = 0; i < 3; i++) {
    const y = await frame.evaluate(() => Math.round(scrollY));
    if (y <= 2) break;
    await page.mouse.wheel(0, -3000); await sleep(220);
  }
  const top = await frame.evaluate(() => Math.round(scrollY));
  check('目录可滚回顶部', top <= 2, { top });
  const after = await frame.evaluate(() => ({ scrollX: Math.round(scrollX), docWidth: document.documentElement.scrollWidth }));
  check('展开/滚动后无水平位移', after.scrollX === 0 && after.docWidth === 480, after);
  return { info, expanded, bottom, top };
}

async function inspectClosed(page) {
  await page.locator('#navbutton').click();
  await sleep(900);
  const data = await page.evaluate(() => {
    const R = e => { const r = e.getBoundingClientRect(); return { x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height) }; };
    const btn = document.getElementById('navbutton');
    return {
      navOpen: document.body.classList.contains('nav-open'),
      side: R(document.getElementById('mySidenav')),
      button: { ...R(btn), text: btn.textContent.trim(), childCount: btn.children.length, aria: btn.getAttribute('aria-label') },
      mainbody: R(document.getElementById('mainbody'))
    };
  });
  check('目录可收起', !data.navOpen && data.side.w <= 2, data);
  check('收起后按钮仍为官方 ⇄', data.button.text === '⇄' && data.button.childCount === 0, data.button);
  check('收起后按钮位于官方 3px', Math.abs(data.button.x - 3) <= 2, data.button);
  check('收起后按钮可访问名称为“展开目录”', data.button.aria === '展开目录', data.button);
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
        const prepared = await openPage(browser, engineName, width, pagePath);
        context = prepared.context;
        const page = prepared.page;
        await shot(page, 'open');
        const parent = await inspectParent(page);
        const frame = await inspectFrame(page);
        const closed = await inspectClosed(page);
        await shot(page, 'closed');
        for (const err of prepared.errors) {
          check('无意外页面错误', false, { error: err }, /Cannot load blob:|favicon/i.test(err) ? 'warn' : 'fail');
        }
        samples.push({ engine: engineName, width, page: pagePath, parent, frame, closed });
      } catch (e) {
        check('页面基线测试未抛出异常', false, { error: String(e) });
      } finally { if (context) await context.close(); }
    }
  }
  await browser.close();
}

fs.writeFileSync(path.join(OUT, `official_report_${PHASE}.json`), JSON.stringify({ assertions, samples }, null, 2));
const failed = assertions.filter(a => !a.ok && a.severity === 'fail');
console.log(JSON.stringify({ phase: PHASE, assertions: assertions.length,
  passed: assertions.filter(a => a.ok).length, failed: failed.length,
  warnings: assertions.filter(a => !a.ok && a.severity === 'warn').length }, null, 2));
if (failed.length) process.exitCode = 1;
