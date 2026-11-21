/**
 * 桌面端专项浏览器验收（Playwright）——带硬断言与非零退出码。
 *
 * BASE_URL 默认指向本地模拟的 GitHub Pages 子路径 /itasca-docs-cn/。
 * MODE=baseline 时只记录截图/指标，不做断言；默认 verify 模式任何失败断言
 * 都会设置 process.exitCode = 1。
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8770/itasca-docs-cn';
const OUT = process.env.OUT || path.resolve('_desktop_artifacts');
const PHASE = process.env.PHASE || 'desktop';
const BASELINE = process.env.MODE === 'baseline';
const WIDTHS = (process.env.WIDTHS || '960,1024,1280,1440,1920').split(',').map(Number).filter(Boolean);
const PAGES = (process.env.PAGES || [
  'index.html',
  'doc/contents.html',
  'doc/search.html',
  'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html',
  'doc/3dec/block/doc/manual/block_manual/block_fish/block/fish_block.area.html',
  'doc/flac3d/docproject/source/modeling/problemsolving/material_properties.html',
  'doc/pfc/ccfd/doc/ball_cfd_manual/ball_cfd_commands/cmd_ball.cfd.attribute.html'
].join(',')).split(',').filter(Boolean);
const ENGINES = (process.env.ENGINES || 'chromium').split(',').filter(Boolean);
if (!BASE.includes('/itasca-docs-cn')) {
  console.error('BASE_URL 必须包含 GitHub Pages 子路径 /itasca-docs-cn');
  process.exit(1);
}

fs.mkdirSync(OUT, { recursive: true });
const assertions = [];
const results = [];
const current = { engine: '', width: 0, page: '' };
let seq = 0;

function check(name, ok, detail, severity = 'fail') {
  const rec = { id: ++seq, name, ok: !!ok, severity, detail, ...current };
  assertions.push(rec);
  if (!ok && severity === 'fail' && !BASELINE) {
    console.error(`FAIL [${rec.engine}/${rec.width}/${rec.page}] ${name}: ${JSON.stringify(detail)}`);
  }
  return rec;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function openPage(browser, engine, width, pagePath) {
  const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push({ type: 'pageerror', message: String(e) }));
  page.on('console', m => { if (m.type() === 'error') errors.push({ type: 'console', message: m.text() }); });
  const response = await page.goto(`${BASE}/${pagePath}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  if (!response || response.status() >= 400) throw new Error('HTTP ' + (response && response.status()));
  await page.waitForFunction(() => !!window.ItascaNav, null, { timeout: 20000 });
  await sleep(1200);
  return { context, page, errors };
}

async function measure(page) {
  return page.evaluate(() => {
    const rect = sel => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    };
    const side = document.getElementById('mySidenav');
    const ifr = document.getElementById('toctobj2');
    const body = document.getElementById('mainbody');
    const cs = body ? getComputedStyle(body) : null;
    const clipped = [];
    if (body) {
      Array.prototype.forEach.call(body.querySelectorAll('p,li,td,th,pre,code'), function (el) {
        const s = getComputedStyle(el);
        if (el.scrollWidth > el.clientWidth + 2 && (s.overflowX === 'hidden' || s.overflowX === 'clip') && clipped.length < 5) {
          clipped.push({ tag: el.tagName, cls: String(el.className).slice(0, 40), text: (el.textContent || '').trim().slice(0, 40) });
        }
      });
    }
    const stylesheetLoaded = Array.prototype.some.call(document.styleSheets, function (s) {
      return !!s.href && s.href.includes('_static/itasca.css');
    });
    return {
      innerWidth: window.innerWidth,
      docScrollWidth: document.documentElement.scrollWidth,
      mobile: window.ItascaNav.isMobile(),
      navOpen: document.body.classList.contains('nav-open'),
      sidenav: rect('#mySidenav'),
      iframe: rect('#toctobj2'),
      iframeCssWidth: ifr ? getComputedStyle(ifr).width : null,
      main: rect('#main'),
      mainbody: rect('#mainbody'),
      mainbodyPadding: cs ? { left: cs.paddingLeft, right: cs.paddingRight } : null,
      mainbodyMinHeight: cs ? cs.minHeight : null,
      navbutton: (function () {
        var el = document.getElementById('navbutton');
        if (!el) return null;
        var r = el.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), text: el.textContent.trim() };
      })(),
      h1: rect('#mainbody h1'),
      stylesheetLoaded,
      bodyBackground: getComputedStyle(document.body).backgroundColor,
      clipped
    };
  });
}

function overlap(a, b) {
  if (!a || !b) return 0;
  const w = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
  const h = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  return w * h;
}

async function testToc(page, label, width) {
  const frame = page.frames().find(f => f.url().includes('navtree.html'));
  check('目录 iframe 已加载', !!frame, { frames: page.frames().map(f => f.url().slice(0, 90)) });
  if (!frame) return null;

  await frame.waitForSelector('.jstree-ocl', { timeout: 15000 });
  const sideWidth = await page.evaluate(() => Math.round(document.getElementById('mySidenav').getBoundingClientRect().width));
  const clippedAnchors = await frame.evaluate(function (visibleWidth) {
    return Array.prototype.filter.call(document.querySelectorAll('.jstree-anchor'), function (el) {
      return el.getBoundingClientRect().right > visibleWidth + 2;
    }).length;
  }, sideWidth);
  check('目录条目未在侧栏右缘被截断', clippedAnchors === 0, { clippedAnchors, sideWidth });

  const officialNav = await frame.evaluate(() => {
    const a = document.querySelector('.jstree-anchor');
    const o = document.querySelector('.jstree-ocl');
    const c = document.querySelector('.jstree-clicked');
    const R = e => { const r = e.getBoundingClientRect(); return { x: Math.round(r.x), w: Math.round(r.width) }; };
    return {
      docWidth: document.documentElement.scrollWidth,
      bodyColor: getComputedStyle(document.body).color,
      anchor: a ? R(a) : null,
      ocl: o ? R(o) : null,
      clickedBg: c ? getComputedStyle(c).backgroundColor : null,
      hasDesktopStyle: !!document.getElementById('wb-toc-desktop-style'),
      hasMobileStyle: !!document.getElementById('wb-toc-native-scroll')
    };
  });
  check('桌面目录文档宽度保持官方 480px', officialNav.docWidth === 480, officialNav);
  check('桌面目录文字颜色符合官方 #9da3a8', officialNav.bodyColor === 'rgb(157, 163, 168)', officialNav);
  check('桌面目录一级缩进符合官方 32px', !!officialNav.anchor && officialNav.anchor.x === 32, officialNav);
  check('桌面目录箭头位置符合官方 8px', !!officialNav.ocl && officialNav.ocl.x === 8, officialNav);
  check('桌面目录未注入自定义桌面样式', !officialNav.hasDesktopStyle, officialNav);
  check('桌面目录未误用移动端注入样式', !officialNav.hasMobileStyle, officialNav);
  if (officialNav.clickedBg) check('选中项背景符合官方 #37435c', officialNav.clickedBg === 'rgb(55, 67, 92)', officialNav);

  let expanded = 0;
  for (let i = 0; i < 8; i++) {
    const closed = frame.locator('.jstree-closed > .jstree-ocl');
    if (!await closed.count()) break;
    try { await closed.first().click({ timeout: 2500 }); expanded++; await sleep(80); } catch (e) { /* 断言判定 */ }
  }
  check('多级目录可连续展开', expanded >= 5, { expanded });

  const state = await frame.evaluate(() => ({
    sh: document.body.scrollHeight, ih: window.innerHeight, max: document.body.scrollHeight - window.innerHeight
  }));
  check('展开后目录可独立滚动', state.max > 0, state);
  const box = await page.locator('#toctobj2').boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  for (let i = 0; i < 6; i++) {
    const current = await frame.evaluate(() => ({ y: Math.round(scrollY), max: Math.round(document.body.scrollHeight - innerHeight) }));
    if (current.y >= current.max - 2) break;
    await page.mouse.wheel(0, 3000);
    await sleep(260);
  }
  const atBottom = await frame.evaluate(() => ({ y: Math.round(scrollY), max: Math.round(document.body.scrollHeight - innerHeight) }));
  check('目录可滚动到底部', atBottom.y >= atBottom.max - 2, atBottom);
  for (let i = 0; i < 3; i++) {
    const y = await frame.evaluate(() => Math.round(scrollY));
    if (y <= 2) break;
    await page.mouse.wheel(0, -3000);
    await sleep(250);
  }
  const atTop = await frame.evaluate(() => Math.round(scrollY));
  check('目录可滚回顶部', atTop <= 2, { atTop });
  const stillOpen = await page.evaluate(() => document.body.classList.contains('nav-open'));
  check('目录滚动时侧栏保持打开', stillOpen, { stillOpen });
  return { expanded, state, atBottom, atTop };
}

async function testToggle(page, m0, width) {
  const beforeScroll = await page.evaluate(() => window.scrollY);
  await page.evaluate(() => window.scrollTo(0, 500));
  const scrolled = await page.evaluate(() => window.scrollY);
  await page.locator('#navbutton').click();
  await sleep(1200);
  const closed = await measure(page);
  check('点击按钮可收起目录', !closed.navOpen && closed.sidenav.w <= 2, { navOpen: closed.navOpen, w: closed.sidenav.w });
  check('收起后正文获得合理宽度', closed.mainbody.w >= m0.mainbody.w - 1,
    { before: m0.mainbody.w, after: closed.mainbody.w });
  check('收起后按钮回到内容区左侧', closed.navbutton && closed.navbutton.x < 40, { btn: closed.navbutton });
  const keptScroll = await page.evaluate(() => window.scrollY);
  check('收起目录时阅读位置保持', Math.abs(keptScroll - scrolled) <= 3, { scrolled, keptScroll });
  await page.locator('#navbutton').click();
  await sleep(1200);
  const reopened = await measure(page);
  check('可重新展开目录', reopened.navOpen && reopened.sidenav.w >= 250,
    { navOpen: reopened.navOpen, w: reopened.sidenav.w });
  await page.evaluate(y => window.scrollTo(0, y), beforeScroll);

  // 最后验证目录链接可跳转到目标页面（会离开当前页，因此放在交互检查之后）。
  const frame = page.frames().find(f => f.url().includes('navtree.html'));
  if (frame) {
    const beforeUrl = page.url();
    try {
      await frame.locator('.jstree-anchor').nth(1).click({ timeout: 6000 });
      await sleep(900);
    } catch (e) { /* 由断言判定 */ }
    check('目录链接可跳转到目标页面', page.url() !== beforeUrl,
      { before: beforeUrl, after: page.url() });
  }
  return { closed, reopened };
}

async function testSearch(page) {
  await page.fill('#mainbody input[name="q"]', 'zone');
  await page.locator('#mainbody input[type="submit"]').click();
  let ok = true;
  try {
    await page.waitForFunction(() => {
      const s = document.getElementById('zh-search-status');
      return s && !s.textContent.includes('正在');
    }, null, { timeout: 45000 });
  } catch (e) { ok = false; }
  check('搜索完成加载', ok, {});
  const sr = await page.evaluate(() => ({
    count: document.querySelectorAll('#zh-search-list li').length,
    status: document.getElementById('zh-search-status')?.textContent || '',
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }));
  check('搜索返回正确结果', sr.count > 0 && !/失败|无法/.test(sr.status), sr);
  check('搜索结果页无整页溢出', sr.scrollWidth - sr.innerWidth <= 1, sr);
  return sr;
}

for (const engineName of ENGINES) {
  const engine = engineName === 'webkit' ? webkit : chromium;
  const launchOptions = { headless: true };
  if (engineName === 'chromium' && process.env.CHROMIUM_EXEC) launchOptions.executablePath = process.env.CHROMIUM_EXEC;
  let browser;
  try { browser = await engine.launch(launchOptions); }
  catch (error) { check('浏览器启动成功', false, { engine: engineName, error: String(error) }); continue; }

  for (const width of WIDTHS) {
    for (const pagePath of PAGES) {
      current.engine = engineName; current.width = width; current.page = pagePath;
      let context;
      try {
        const prepared = await openPage(browser, engineName, width, pagePath);
        context = prepared.context;
        const page = prepared.page;
        const m = await measure(page);
        const label = pagePath.replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 60);
        await page.screenshot({ path: path.join(OUT, `${PHASE}_${engineName}_${width}_${label}.png`), timeout: 60000, animations: 'disabled' });
        check('整页无横向溢出', m.docScrollWidth - m.innerWidth <= 1, { sw: m.docScrollWidth, iw: m.innerWidth });
        check('样式表由 Pages 子路径正确加载', m.stylesheetLoaded, { loaded: m.stylesheetLoaded });
        check('正文可见', !!m.mainbody && m.mainbody.w > 200, { mainbody: m.mainbody });
        // 官方 comfishtable 使用固定 550px + nowrap/overflow:hidden，宽桌面上会裁切
        // 自定义索引表的单元格；这是官方原版行为，记录为告警而非失败。
        check('正文没有被 overflow:hidden 裁切', m.clipped.length === 0, { clipped: m.clipped },
          m.clipped.length && m.clipped.every(c => c.tag === 'TD') ? 'warn' : 'fail');
        if (m.sidenav && m.iframe) {
          check('侧栏宽度符合官方 350px', m.sidenav.w === 350, { width: m.sidenav.w });
          check('目录 iframe 宽度符合官方 390px', m.iframe.w === 390, { width: m.iframe.w, css: m.iframeCssWidth });
        }
        if (m.navbutton) {
          check('桌面目录按钮可见内容为官方 ⇄', m.navbutton.text === '⇄', { text: m.navbutton.text });
          check('桌面目录按钮尺寸符合官方 43x40', Math.abs(m.navbutton.w - 43) <= 2 && Math.abs(m.navbutton.h - 40) <= 2,
            { w: m.navbutton.w, h: m.navbutton.h });
        }
        if (m.mainbodyMinHeight) {
          check('占位页最小高度符合官方 640px', m.mainbodyMinHeight === '640px', { minHeight: m.mainbodyMinHeight });
        }
        if (m.mainbody && m.h1) {
          check('目录按钮不遮挡正文标题', overlap(m.navbutton, m.h1) === 0,
            { button: m.navbutton, h1: m.h1 });
        }
        if (m.mainbodyPadding) {
          const pl = parseFloat(m.mainbodyPadding.left), pr = parseFloat(m.mainbodyPadding.right);
          check('正文内边距符合官方 64px/32px', pl === 64 && pr === 32, m.mainbodyPadding);
        }
        if (m.mainbody) {
          const expected = width >= 1280 ? 656 : 610;
          check('正文宽度符合官方基准', Math.abs(m.mainbody.w - expected) <= 2, { width: m.mainbody.w, expected });
        }

        let toc = null, toggle = null, search = null;
        if (pagePath === 'index.html') {
          toc = await testToc(page, pagePath, width);
          toggle = await testToggle(page, m, width);
        }
        if (pagePath === 'doc/search.html') search = await testSearch(page);
        for (const err of prepared.errors) {
          check('无意外浏览器错误', /Cannot load blob:|favicon/i.test(err.message) ? true : false,
            err, /Cannot load blob:|favicon/i.test(err.message) ? 'warn' : 'fail');
        }
        results.push({ engine: engineName, width, page: pagePath, metrics: m, toc, toggle, search });
      } catch (error) {
        check('页面测试未抛出异常', false, { error: String(error) });
      } finally {
        if (context) await context.close();
      }
    }
  }
  await browser.close();
}

fs.writeFileSync(path.join(OUT, `desktop_report_${PHASE}.json`), JSON.stringify({ assertions, results }, null, 2));
const failed = assertions.filter(a => !a.ok && a.severity === 'fail');
const warned = assertions.filter(a => !a.ok && a.severity === 'warn');
console.log(JSON.stringify({ phase: PHASE, assertions: assertions.length,
  passed: assertions.filter(a => a.ok).length, failed: failed.length, warnings: warned.length,
  report: path.join(OUT, `desktop_report_${PHASE}.json`) }, null, 2));
if (failed.length && !BASELINE) process.exitCode = 1;
