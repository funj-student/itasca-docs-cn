/**
 * 移动端浏览器验收脚本（Playwright）。
 *
 * 用法：
 *   NODE_PATH=<playwright 安装目录>/node_modules \
 *   BASE_URL=http://127.0.0.1:8765 SHOT_DIR=<截图目录> PHASE=1 \
 *   node tests/mobile_browser_check.mjs
 *
 * 该脚本只做浏览器验收，不修改站点文件；结果输出为 JSON 与截图。
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8765';
const OUT = process.env.SHOT_DIR || path.resolve('_mobile_artifacts');
const PHASE = process.env.PHASE || 'all';
const WIDTHS = (process.env.WIDTHS || '320,375,390,430,768,960,1280,1920').split(',').map(Number);
const PAGES = (process.env.PAGES || [
  'index.html',
  'doc/search.html',
  'glossary.html',
  'terms.html',
  'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html',
  'doc/3dec/block/doc/manual/block_manual/block_fish/block/fish_block.area.html',
  'doc/flac3d/body/doc/manual/buildingblocks_manual/building-blocks_commands/cmd_building-blocks.block.transform.html',
  'doc/pfc/ccfd/doc/ball_cfd_manual/ball_cfd_commands/cmd_ball.cfd.attribute.html',
  'doc/3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.analyze-stability.html',
  'doc/common/docproject/source/manual/coupling/couplingpfcandflac3d.html'
].join(',')).split(',').filter(Boolean);

fs.mkdirSync(OUT, { recursive: true });
const results = [];
const errors = [];

function record(page, label, data) {
  results.push({ engine: page._engine, width: page._width, page: label, ...data });
}

async function preparePage(browser, engine, width, height, pagePath) {
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 1,
    isMobile: width <= 960,
    hasTouch: width <= 960
  });
  const page = await context.newPage();
  page._engine = engine;
  page._width = width;
  page.on('pageerror', e => errors.push({ engine, width, page: pagePath, type: 'pageerror', message: String(e) }));
  page.on('console', m => {
    if (m.type() === 'error') errors.push({ engine, width, page: pagePath, type: 'console', message: m.text() });
  });
  await page.goto(`${BASE}/${pagePath}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForFunction(() => !!window.ItascaNav, null, { timeout: 20000 });
  await page.waitForTimeout(250);
  return { context, page };
}

async function measure(page) {
  return page.evaluate(() => {
    const btn = document.getElementById('navbutton');
    const r = btn && btn.getBoundingClientRect();
    const side = document.getElementById('mySidenav');
    return {
      innerWidth: window.innerWidth,
      docScrollWidth: document.documentElement.scrollWidth,
      mobile: window.ItascaNav.isMobile(),
      navOpen: document.body.classList.contains('nav-open'),
      button: btn ? {
        width: Math.round(r.width), height: Math.round(r.height),
        role: btn.getAttribute('role'), label: btn.getAttribute('aria-label'),
        expanded: btn.getAttribute('aria-expanded'), text: btn.textContent.trim()
      } : null,
      drawerWidth: side ? Math.round(side.getBoundingClientRect().width) : null
    };
  });
}

async function measureContent(page) {
  return page.evaluate(() => {
    const main = document.getElementById('mainbody');
    if (!main) return null;
    const overflowing = [];
    Array.prototype.forEach.call(main.querySelectorAll('*'), function (el) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.right > window.innerWidth + 2 &&
          getComputedStyle(el).position !== 'fixed' && overflowing.length < 6) {
        overflowing.push({ tag: el.tagName, cls: String(el.className).slice(0, 60), right: Math.round(r.right) });
      }
    });
    const wrappers = Array.prototype.slice.call(main.querySelectorAll('.table-scroll'));
    return {
      tableScrollers: wrappers.length,
      scrollableTables: wrappers.filter(e => e.scrollWidth > e.clientWidth + 2).length,
      codeScrollers: Array.prototype.slice.call(main.querySelectorAll('div.highlight, div.highlight-fish, div.highlight-python, pre'))
        .filter(e => e.scrollWidth > e.clientWidth + 2).length,
      mathCount: main.querySelectorAll('.math, .MathJax, mjx-container').length,
      clippedImages: Array.prototype.slice.call(main.querySelectorAll('img'))
        .filter(e => e.getBoundingClientRect().width > window.innerWidth + 2).length,
      overflowing
    };
  });
}

async function testDrawer(page, label) {
  const btn = page.locator('#navbutton');
  await btn.click();
  await page.waitForTimeout(280);
  const opened = await measure(page);
  const backdrop = await page.locator('#nav-backdrop').evaluate(el => getComputedStyle(el).display);

  const frame = page.frames().find(f => f.url().includes('navtree.html'));
  if (frame) {
    try {
      await frame.waitForSelector('.jstree-ocl', { timeout: 12000 });
    } catch (e) { /* 目录树未就绪时如实记录 */ }
  }

  // 连续展开多个目录节点，验证多级目录可用
  let expandedNodes = 0;
  for (let i = 0; i < 8; i++) {
    const closed = frame ? frame.locator('.jstree-closed > .jstree-ocl') : null;
    if (!closed || !await closed.count()) break;
    try {
      await closed.first().click({ timeout: 2500 });
      expandedNodes++;
      await page.waitForTimeout(80);
    } catch (e) { /* 不可见节点跳过 */ }
  }

  // 目录内部原生滚动到底部
  let toc = null;
  if (frame) {
    toc = await frame.evaluate(() => {
      // navtree.html 为 quirks mode，滚动量以 window.scrollY 为准
      const contentHeight = document.body.scrollHeight;
      const viewportHeight = window.innerHeight;
      const max = Math.max(0, contentHeight - viewportHeight);
      window.scrollTo(0, max);
      return {
        scrollHeight: contentHeight, clientHeight: viewportHeight, max,
        after: Math.round(window.scrollY), reachedBottom: max > 0 && window.scrollY >= max - 1
      };
    });
  }

  // 关闭后恢复阅读位置（先关闭，再滚动正文，然后打开并关闭）
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  await page.evaluate(() => window.scrollTo(0, 600));
  const beforeY = await page.evaluate(() => window.scrollY);
  await btn.click();
  await page.waitForTimeout(250);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  const afterY = await page.evaluate(() => window.scrollY);
  const scrollRestored = { before: beforeY, after: afterY, ok: Math.abs(beforeY - afterY) <= 3 };

  // 遮罩点击关闭
  await btn.click();
  await page.waitForTimeout(250);
  // 点击抽屉外侧的可见遮罩区域（避开抽屉与关闭按钮）
  await page.mouse.click(page.viewportSize().width - 16, 120);
  await page.waitForTimeout(350);
  const closed = await measure(page);

  // 点击目录链接后能导航（放在最后，避免导航打断后续状态检查）
  let navigated = false;
  if (frame) {
    try {
      await btn.click();
      await page.waitForTimeout(250);
      const before = page.url();
      const anchor = frame.locator('.jstree-anchor').nth(1);
      await anchor.click({ timeout: 5000 });
      await page.waitForTimeout(800);
      navigated = page.url() !== before;
    } catch (e) { navigated = false; }
  }

  record(page, label, {
    check: 'drawer', opened, backdrop, toc,
    expandedNodes, navigated, scrollRestored,
    closedState: { navOpen: closed.navOpen, drawerWidth: closed.drawerWidth, ariaExpanded: closed.button && closed.button.expanded }
  });
}

async function runEngine(engineType) {
  const launchOptions = { headless: true };
  if (engineType.name() === 'chromium' && process.env.CHROMIUM_EXEC) {
    launchOptions.executablePath = process.env.CHROMIUM_EXEC;
  }
  const browser = await engineType.launch(launchOptions);
  for (const width of WIDTHS) {
    const height = width <= 960 && width > 600 ? 720 : 800;
    for (const pagePath of PAGES) {
      let context;
      try {
        const prepared = await preparePage(browser, engineType.name(), width, height, pagePath);
        context = prepared.context;
        const page = prepared.page;
        const m = await measure(page);
        const content = await measureContent(page);
        const overflow = m.docScrollWidth - m.innerWidth;
        record(page, pagePath, {
          check: 'layout', ...m, content, overflow,
          overflowOK: overflow <= 1,
          buttonOK: !m.button || !m.mobile || (m.button.width >= 44 && m.button.height >= 44)
        });
        if (pagePath === 'index.html' && (width === 320 || width === 390 || width === 960 || width === 1280)) {
          await page.screenshot({ path: path.join(OUT, `${PHASE}_${engineType.name()}_${width}_closed.png`) });
          if (m.mobile) {
            await page.locator('#navbutton').click();
            await page.waitForTimeout(280);
            await page.screenshot({ path: path.join(OUT, `${PHASE}_${engineType.name()}_${width}_open.png`) });
            await page.keyboard.press('Escape');
          }
          if (m.mobile) await testDrawer(page, pagePath);
        }
        if (pagePath === 'doc/search.html' && (width === 320 || width === 390 || width === 1280)) {
          await page.fill('#mainbody input[name="q"]', 'zone');
          await page.locator('#mainbody input[type="submit"]').click();
          try {
            await page.waitForFunction(() => {
              const s = document.getElementById('zh-search-status');
              return s && !s.textContent.includes('正在');
            }, null, { timeout: 30000 });
          } catch (e) { /* 索引加载失败会在下方记录 */ }
          const sr = await page.evaluate(() => {
            const list = document.querySelectorAll('#zh-search-list li');
            const f = document.getElementById('zh-title-filter');
            const s = document.getElementById('zh-search-status');
            return {
              count: list.length,
              status: s ? s.textContent : '',
              titleFilterWidth: f ? Math.round(f.getBoundingClientRect().width) : null,
              innerWidth: window.innerWidth,
              docScrollWidth: document.documentElement.scrollWidth
            };
          });
          record(page, pagePath, { check: 'search', ...sr, overflow: sr.docScrollWidth - sr.innerWidth });
          await page.screenshot({ path: path.join(OUT, `${PHASE}_${engineType.name()}_${width}_search.png`) });
        }
      } catch (e) {
        errors.push({ engine: engineType.name(), width, page: pagePath, type: 'test', message: String(e) });
      } finally {
        if (context) await context.close();
      }
    }
  }
  await browser.close();
}

const engines = [chromium];
if (process.env.WITH_WEBKIT === '1') engines.push(webkit);
for (const engine of engines) {
  try { await runEngine(engine); }
  catch (e) { errors.push({ engine: engine.name(), type: 'launch', message: String(e) }); }
}

fs.writeFileSync(path.join(OUT, `report_${PHASE}.json`), JSON.stringify({ results, errors }, null, 2));

const layout = results.filter(r => r.check === 'layout');
const drawer = results.filter(r => r.check === 'drawer');
const search = results.filter(r => r.check === 'search');
console.log(JSON.stringify({
  phase: PHASE,
  layout: { total: layout.length, overflowFail: layout.filter(r => !r.overflowOK).length, buttonFail: layout.filter(r => !r.buttonOK).length },
  drawer: drawer.length,
  search: search.length,
  errors: errors.length,
  report: path.join(OUT, `report_${PHASE}.json`)
}, null, 2));
if (errors.length) console.log(errors.slice(0, 20));
