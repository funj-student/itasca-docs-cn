/**
 * 移动端浏览器验收脚本（Playwright）——带硬断言与非零退出码。
 *
 * 用法：
 *   BASE_URL=http://127.0.0.1:8765 SHOT_DIR=<目录> PHASE=final \
 *   node tests/mobile_browser_check.mjs
 *
 * 环境变量：
 *   MODE=smoke      使用 CI 冒烟矩阵（默认 full）
 *   WIDTHS          覆盖视口，逗号分隔
 *   PAGES           覆盖页面清单，逗号分隔
 *   ENGINES         chromium,webkit 或仅一个
 *   CHROMIUM_EXEC   可选：本机已安装的 chromium 可执行文件
 *   PLAYWRIGHT_MODULE 可选：playwright 模块名/路径
 *
 * 失败判定：任何 severity=fail 的断言失败，或出现未分类异常，最终 process.exitCode=1。
 * 非阻塞告警（severity=warn）：WebKit MathJax blob 访问告警、favicon 404 等已知环境问题；
 * 其余 pageerror / console error / HTTP >=400 一律计为失败。
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
let chromium, webkit;
try {
  ({ chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright'));
} catch (error) {
  console.error('无法加载 playwright：' + String(error));
  process.exitCode = 1;
  process.exit(1);
}

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8765';
const OUT = process.env.SHOT_DIR || path.resolve('_mobile_artifacts');
const PHASE = process.env.PHASE || 'all';
const SMOKE = process.env.MODE === 'smoke';

const DEFAULT_WIDTHS = SMOKE
  ? [375, 390, 959, 960, 1280]
  : [320, 375, 390, 430, 768, 959, 960, 1280, 1920];
const DEFAULT_PAGES = SMOKE
  ? ['index.html', 'doc/search.html', 'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html']
  : [
      'index.html',
      'doc/search.html',
      'doc/contents.html',
      // navtree.html 是 iframe 用的目录片段（html 固定 30em），不是独立阅读页；
      // 它通过首页目录抽屉的加载/展开/滚动/导航断言覆盖，不作为独立页面测试。
      'glossary.html',
      'terms.html',
      'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html',
      'doc/flac3d/docproject/source/modeling/problemsolving/material_properties.html',
      'doc/flac3d/body/doc/manual/buildingblocks_manual/building-blocks_commands/cmd_building-blocks.block.transform.html',
      'doc/3dec/block/doc/manual/block_manual/block_fish/block/fish_block.area.html',
      'doc/3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.analyze-stability.html',
      'doc/3dec/block/test3d/Theory_and_Background/Factor_of_Safety/MC_Slope/mcslope.html',
      'doc/pfc/ccfd/doc/ball_cfd_manual/ball_cfd_commands/cmd_ball.cfd.attribute.html',
      'doc/common/docproject/source/manual/coupling/couplingpfcandflac3d.html'
    ];

const WIDTHS = (process.env.WIDTHS || DEFAULT_WIDTHS.join(',')).split(',').map(Number).filter(Boolean);
const PAGES = (process.env.PAGES || DEFAULT_PAGES.join(',')).split(',').filter(Boolean);
const engineNames = (process.env.ENGINES || 'chromium,webkit').split(',').filter(Boolean);
const engines = [];
if (engineNames.includes('chromium')) engines.push({ name: 'chromium', type: chromium });
if (engineNames.includes('webkit')) engines.push({ name: 'webkit', type: webkit });

fs.mkdirSync(OUT, { recursive: true });

const assertions = [];
const results = [];
const current = { engine: '', width: 0, page: '' };
let sequence = 0;

function check(name, ok, detail, severity = 'fail') {
  const record = {
    id: ++sequence, name, ok: !!ok, severity, detail,
    engine: current.engine, width: current.width, page: current.page
  };
  assertions.push(record);
  if (!ok && severity === 'fail') {
    console.error(`FAIL [${record.engine}/${record.width}/${record.page}] ${name}: ${JSON.stringify(detail)}`);
  }
  return record;
}

function warnOrFail(name, ok, detail, warnPattern) {
  const isWarn = !ok && warnPattern && warnPattern.test(JSON.stringify(detail || ''));
  return check(name, ok, detail, isWarn ? 'warn' : 'fail');
}

function isKnownWarning(message) {
  return /Cannot load blob:|favicon|\.ico.*404|404.*\.ico/i.test(message);
}

function record(page, label, data) {
  results.push({ engine: current.engine, width: current.width, page: label, ...data });
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

// 截图只是证据材料，不参与功能判定；字体加载超时记为非阻塞告警。
async function safeScreenshot(page, file) {
  try {
    await page.screenshot({ path: file, timeout: 60000, animations: 'disabled' });
  } catch (error) {
    check('screenshot evidence captured', false, { file, error: String(error) }, 'warn');
  }
}

async function preparePage(browser, engine, width, height, pagePath) {
  // isMobile 是 Chromium 专用模拟选项；在 WebKit 中会禁用 mouse.wheel，
  // 因此 WebKit 仅启用 hasTouch，布局仍由视口宽度与 matchMedia 决定。
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 1,
    isMobile: engine === 'chromium' && width <= 960,
    hasTouch: width <= 960
  });
  const page = await context.newPage();
  page._pageErrors = [];
  page._consoleErrors = [];
  page.on('pageerror', e => page._pageErrors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') page._consoleErrors.push(m.text()); });
  let response;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      response = await page.goto(`${BASE}/${pagePath}`, { waitUntil: 'domcontentloaded', timeout: 90000 });
      break;
    } catch (error) {
      if (attempt === 1) throw error;
      await sleep(500);
    }
  }
  check('HTTP response is successful', !!response && response.status() < 400, { status: response && response.status() });
  // navtree.html 是被 iframe 嵌入的目录片段，本身不加载 icgscripts.js，
  // 因此用目录树节点作为就绪条件，而不是 ItascaNav。
  if (/navtree\.html$/.test(pagePath)) {
    await page.waitForSelector('.jstree-anchor', { timeout: 20000 });
  } else {
    await page.waitForFunction(() => !!window.ItascaNav, null, { timeout: 20000 });
  }
  await page.waitForTimeout(250);
  return { context, page };
}

function classifyPageMessages(page, label) {
  const all = page._pageErrors.map(m => ({ type: 'pageerror', message: m }))
    .concat(page._consoleErrors.map(m => ({ type: 'console', message: m })));
  for (const item of all) {
    warnOrFail('no unexpected browser error', false, { ...item, page: label },
      isKnownWarning(item.message) ? /.*/ : null);
  }
}

async function measure(page) {
  return page.evaluate(() => {
    const btn = document.getElementById('navbutton');
    const r = btn && btn.getBoundingClientRect();
    const side = document.getElementById('mySidenav');
    return {
      innerWidth: window.innerWidth,
      docScrollWidth: document.documentElement.scrollWidth,
      mobile: window.ItascaNav ? window.ItascaNav.isMobile() : window.innerWidth <= 959,
      navOpen: document.body.classList.contains('nav-open'),
      button: btn ? {
        width: Math.round(r.width), height: Math.round(r.height),
        role: btn.getAttribute('role'), label: btn.getAttribute('aria-label'),
        expanded: btn.getAttribute('aria-expanded'), text: btn.textContent.trim()
      } : null,
      drawerWidth: side ? Math.round(side.getBoundingClientRect().width) : null,
      drawerInert: window.ItascaNav ? window.ItascaNav.isDrawerInert() : null,
      listenerInstalls: window.ItascaNav ? window.ItascaNav.tocListenerInstalls() : null
    };
  });
}

async function measureContent(page) {
  return page.evaluate(() => {
    const main = document.getElementById('mainbody');
    if (!main) return null;
    const insideAllowedScroller = el => {
      for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
        const st = getComputedStyle(p);
        if ((st.overflowX === 'auto' || st.overflowX === 'scroll') && p.scrollWidth > p.clientWidth + 2) return true;
      }
      return false;
    };
    const clipped = [];
    Array.prototype.forEach.call(
      main.querySelectorAll('p,li,td,th,span,a,code,h1,h2,h3,h4,pre'),
      function (el) {
        // MathJax 的辅助 MathML 用 1px 裁剪隐藏，属于可访问性实现，不是正文裁切。
        if (el.closest('.MJX_Assistive_MathML, mjx-assistive-mml') ||
            el.getAttribute('aria-hidden') === 'true') return;
        const st = getComputedStyle(el);
        if (el.scrollWidth > el.clientWidth + 2 &&
            (st.overflowX === 'hidden' || st.overflowX === 'clip' || st.textOverflow === 'ellipsis') &&
            !insideAllowedScroller(el) && clipped.length < 8) {
          clipped.push({ tag: el.tagName, cls: String(el.className).slice(0, 60),
            scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, text: (el.textContent || '').trim().slice(0, 50) });
        }
      }
    );
    const occluded = [];
    const btn = document.getElementById('navbutton');
    if (btn && !document.body.classList.contains('nav-open')) {
      const br = btn.getBoundingClientRect();
      Array.prototype.forEach.call(main.querySelectorAll('a,button,input,select,textarea'), function (el) {
        const r = el.getBoundingClientRect();
        if (r.width < 8 || r.height < 8 || r.bottom < 0 || r.top > window.innerHeight) return;
        const ix = Math.max(0, Math.min(r.right, br.right) - Math.max(r.left, br.left));
        const iy = Math.max(0, Math.min(r.bottom, br.bottom) - Math.max(r.top, br.top));
        if (ix * iy > 0.5 * r.width * r.height && occluded.length < 8) {
          occluded.push({ tag: el.tagName, cls: String(el.className).slice(0, 50), text: (el.textContent || '').trim().slice(0, 40) });
        }
      });
    }
    const wrappers = Array.prototype.slice.call(main.querySelectorAll('.table-scroll'));
    return {
      tableScrollers: wrappers.length,
      scrollableTables: wrappers.filter(e => e.scrollWidth > e.clientWidth + 2).length,
      codeScrollers: Array.prototype.slice.call(main.querySelectorAll('div.highlight, div.highlight-fish, div.highlight-python, pre'))
        .filter(e => e.scrollWidth > e.clientWidth + 2).length,
      mathCount: main.querySelectorAll('.math, .MathJax, mjx-container').length,
      oversizedImages: Array.prototype.slice.call(main.querySelectorAll('img'))
        .filter(e => e.getBoundingClientRect().width > window.innerWidth + 2).length,
      clipped, occluded
    };
  });
}

async function tocState(frame) {
  return frame.evaluate(() => {
    const max = Math.max(0, document.body.scrollHeight - window.innerHeight);
    return {
      y: Math.round(window.scrollY),
      max: Math.round(max),
      bodyHeight: document.body.scrollHeight,
      viewport: window.innerHeight,
      navOpenInParent: document.body.classList.contains('nav-open')
    };
  });
}

async function chromiumSwipe(page, fromRatio, toRatio) {
  const box = await page.locator('#toctobj2').boundingBox();
  if (!box) throw new Error('目录 iframe 不可见');
  const cdp = await page.context().newCDPSession(page);
  try {
    const x = Math.round(box.x + box.width / 2);
    const yStart = Math.round(box.y + box.height * fromRatio);
    const yEnd = Math.round(box.y + box.height * toRatio);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y: yStart }] });
    for (let i = 1; i <= 10; i++) {
      const y = Math.round(yStart + (yEnd - yStart) * i / 10);
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y }] });
      await sleep(18);
    }
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  } finally {
    await cdp.detach();
  }
  await sleep(180);
}

async function webkitWheel(page, deltaY) {
  const box = await page.locator('#toctobj2').boundingBox();
  if (!box) throw new Error('目录 iframe 不可见');
  await page.mouse.move(Math.round(box.x + box.width / 2), Math.round(box.y + box.height / 2));
  await page.mouse.wheel(0, deltaY);
  await sleep(180);
}

async function testGestureScroll(page, frame, engine) {
  await frame.evaluate(() => {
    window.__wbAnchorClicks = 0;
    document.addEventListener('click', function (e) {
      if (e.target && e.target.closest && e.target.closest('.jstree-anchor')) window.__wbAnchorClicks++;
    }, true);
    window.scrollTo(0, 0);
  });
  const start = await tocState(frame);
  const parentBefore = await page.evaluate(() => window.scrollY);
  let bottomReached = false;
  for (let i = 0; i < 12; i++) {
    if (engine === 'chromium') await chromiumSwipe(page, 0.78, 0.18);
    else await webkitWheel(page, Math.round(page.viewportSize().height * 0.65));
    const state = await tocState(frame);
    if (state.max > 0 && state.y >= state.max - 2) { bottomReached = true; break; }
  }
  const atBottom = await tocState(frame);
  const stillOpen = await page.evaluate(() => document.body.classList.contains('nav-open'));
  const parentAfter = await page.evaluate(() => window.scrollY);
  const anchorClicks = await frame.evaluate(() => window.__wbAnchorClicks || 0);

  check('真实手势/滚轮可将目录滚到底部', bottomReached,
    { engine, start, atBottom });
  check('目录手势滚动时抽屉保持打开', stillOpen, { stillOpen });
  check('目录手势滚动不改变页面背景滚动位置', parentBefore === parentAfter,
    { parentBefore, parentAfter });
  check('目录滑动不会误触目录条目', anchorClicks === 0, { anchorClicks });

  for (let i = 0; i < 12; i++) {
    if (engine === 'chromium') await chromiumSwipe(page, 0.18, 0.82);
    else await webkitWheel(page, -Math.round(page.viewportSize().height * 0.65));
    const state = await tocState(frame);
    if (state.y <= 2) break;
  }
  const backAtTop = await tocState(frame);
  check('目录可从底部手势滚回顶部', backAtTop.y <= 2, { backAtTop });
  return { start, atBottom, backAtTop, anchorClicks, parentBefore, parentAfter };
}

async function testDrawer(page, label) {
  const btn = page.locator('#navbutton');
  await btn.click();
  await page.waitForTimeout(350);
  const opened = await measure(page);
  check('目录可以打开', opened.navOpen && opened.drawerWidth > 40,
    { navOpen: opened.navOpen, drawerWidth: opened.drawerWidth });
  check('打开后遮罩可见', await page.locator('#nav-backdrop').evaluate(el => getComputedStyle(el).display !== 'none'), {});
  check('打开后 aria-expanded 为 true', opened.button.expanded === 'true', { expanded: opened.button.expanded });
  check('打开后抽屉可被聚焦', opened.drawerInert === false, { inert: opened.drawerInert });
  check('打开后焦点落在关闭按钮', await page.evaluate(() => document.activeElement && document.activeElement.id) === 'nav-close',
    { active: await page.evaluate(() => document.activeElement && document.activeElement.id) });

  const frame = page.frames().find(f => f.url().includes('navtree.html'));
  check('目录 iframe 已加载', !!frame, { frames: page.frames().map(f => f.url()) });
  if (!frame) return;

  await frame.waitForSelector('.jstree-anchor', { timeout: 15000 });
  const anchorCount = await frame.locator('.jstree-anchor').count();
  check('目录树包含可点击条目', anchorCount > 0, { anchorCount });

  let expandedNodes = 0;
  for (let i = 0; i < 8; i++) {
    const closed = frame.locator('.jstree-closed > .jstree-ocl');
    if (!await closed.count()) break;
    try {
      await closed.first().click({ timeout: 2500 });
      expandedNodes++;
      await sleep(90);
    } catch (e) { /* 逐个记录，统一断言 */ }
  }
  check('目录节点可以连续展开', expandedNodes >= 3, { expandedNodes });

  // 程序化滚动仅作为能力基线，不冒充真实手势
  const programmatic = await frame.evaluate(() => {
    const max = Math.max(0, document.body.scrollHeight - window.innerHeight);
    window.scrollTo(0, max);
    return { max, y: Math.round(window.scrollY), reached: max > 0 && window.scrollY >= max - 1 };
  });
  check('程序化滚动基线可达目录底部（非手势测试）', programmatic.reached, programmatic);
  await frame.evaluate(() => window.scrollTo(0, 0));

  const gesture = await testGestureScroll(page, frame, current.engine);

  // iframe 内 Escape：焦点在 iframe 时应关闭目录并恢复焦点
  await frame.locator('.jstree-anchor').first().focus();
  const focusInFrame = await page.evaluate(() => document.activeElement && document.activeElement.id) === 'toctobj2';
  check('焦点可进入目录 iframe', focusInFrame, { active: await page.evaluate(() => document.activeElement && document.activeElement.id) });
  await frame.locator('.jstree-anchor').first().press('Escape');
  await page.waitForTimeout(400);
  const afterFrameEscape = await measure(page);
  const activeAfterEscape = await page.evaluate(() => document.activeElement && document.activeElement.id);
  check('iframe 内 Escape 可关闭目录', !afterFrameEscape.navOpen, { navOpen: afterFrameEscape.navOpen });
  check('iframe 内 Escape 后焦点恢复至目录按钮', activeAfterEscape === 'navbutton', { active: activeAfterEscape });
  check('关闭后抽屉不可被意外聚焦', afterFrameEscape.drawerInert === true, { inert: afterFrameEscape.drawerInert });

  // 关闭按钮键盘可达
  await btn.focus();
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  check('目录按钮可用键盘打开', (await measure(page)).navOpen, {});
  await page.locator('#nav-close').focus();
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  check('关闭按钮可通过键盘关闭目录', !(await measure(page)).navOpen, {});

  // 阅读位置恢复
  await page.evaluate(() => window.scrollTo(0, 600));
  const beforeY = await page.evaluate(() => window.scrollY);
  await btn.click();
  await page.waitForTimeout(250);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(350);
  const afterY = await page.evaluate(() => window.scrollY);
  check('关闭目录后恢复阅读位置', Math.abs(beforeY - afterY) <= 3, { before: beforeY, after: afterY });

  // 遮罩关闭
  await btn.click();
  await page.waitForTimeout(250);
  await page.mouse.click(page.viewportSize().width - 16, 120);
  await page.waitForTimeout(350);
  const closed = await measure(page);
  check('点击遮罩可关闭目录', !closed.navOpen, { navOpen: closed.navOpen });

  check('目录 load 监听器只安装一次', closed.listenerInstalls === 1,
    { installs: closed.listenerInstalls });

  // 链接导航放在最后
  await btn.click();
  await page.waitForTimeout(250);
  const before = page.url();
  try {
    await frame.locator('.jstree-anchor').nth(1).click({ timeout: 6000 });
    await page.waitForTimeout(900);
  } catch (e) { /* 由下面的断言判定 */ }
  const navigated = page.url() !== before;
  check('点击目录条目可以导航', navigated, { before, after: page.url() });

  record(page, label, {
    check: 'drawer', opened, gesture, programmatic, expandedNodes,
    frameEscape: { activeAfterEscape }, scrollRestored: { before: beforeY, after: afterY },
    closed, navigated
  });
}

async function testListenerRegression(browser, engine) {
  const width = 390;
  const { context, page } = await preparePage(browser, engine.name, width, 800, 'index.html');
  current.engine = engine.name; current.width = width; current.page = 'index.html(listener-regression)';
  const before = await measure(page);
  for (const w of [960, 959, 960, 390]) {
    await page.setViewportSize({ width: w, height: 800 });
    await sleep(200);
  }
  const after = await measure(page);
  check('布局模式反复切换后 load 监听器仍只安装一次',
    before.listenerInstalls === 1 && after.listenerInstalls === 1,
    { before: before.listenerInstalls, after: after.listenerInstalls });
  await context.close();
}

async function testSearch(page, label) {
  await page.fill('#mainbody input[name="q"]', 'zone');
  await page.locator('#mainbody input[type="submit"]').click();
  let loaded = true;
  try {
    await page.waitForFunction(() => {
      const s = document.getElementById('zh-search-status');
      return s && !s.textContent.includes('正在');
    }, null, { timeout: 45000 });
  } catch (e) { loaded = false; }
  check('搜索索引加载完成', loaded, {});
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
  check('搜索返回正确结果', sr.count > 0 && !/失败|无法|没有找到/.test(sr.status), sr);
  check('标题筛选框不超出视口', sr.titleFilterWidth !== null && sr.titleFilterWidth <= sr.innerWidth, sr);
  check('搜索结果页无整页横向溢出', sr.docScrollWidth - sr.innerWidth <= 1, sr);
  record(page, label, { check: 'search', ...sr, overflow: sr.docScrollWidth - sr.innerWidth });
}

async function runEngine(engine) {
  const launchOptions = { headless: true };
  if (engine.name === 'chromium' && process.env.CHROMIUM_EXEC) {
    launchOptions.executablePath = process.env.CHROMIUM_EXEC;
  }
  let browser;
  try {
    browser = await engine.type.launch(launchOptions);
  } catch (error) {
    check('浏览器启动成功', false, { engine: engine.name, error: String(error) });
    return;
  }

  for (const width of WIDTHS) {
    const height = width <= 960 && width > 600 ? 720 : 800;
    for (const pagePath of PAGES) {
      current.engine = engine.name; current.width = width; current.page = pagePath;
      let context;
      try {
        const prepared = await preparePage(browser, engine.name, width, height, pagePath);
        context = prepared.context;
        const page = prepared.page;
        const m = await measure(page);
        const content = await measureContent(page);
        const overflow = m.docScrollWidth - m.innerWidth;
        check('页面无预期外的整页横向溢出', overflow <= 1, { overflow, innerWidth: m.innerWidth, docScrollWidth: m.docScrollWidth });
        check('移动端目录按钮触摸目标不小于 44px',
          !m.button || !m.mobile || (m.button.width >= 44 && m.button.height >= 44), m.button || {});
        check('目录按钮具有完整语义属性',
          !m.button || !m.mobile || (m.button.role === 'button' && !!m.button.expanded && !!m.button.label), m.button || {});
        if (content) {
          // 移动端为硬断言；桌面端 comfishtable 的 nowrap/overflow:hidden 是既有设计，
          // 不属于本轮移动端修复范围，记为告警并在报告中记录。
          check('正文没有被 CSS 裁切', content.clipped.length === 0,
            { clipped: content.clipped }, m.mobile ? 'fail' : 'warn');
          check('正文交互元素未被目录按钮严重遮挡', content.occluded.length === 0, { occluded: content.occluded });
          check('图片未超出视口', content.oversizedImages === 0, { count: content.oversizedImages });
        }
        record(page, pagePath, { check: 'layout', ...m, content, overflow });

        if (pagePath === 'index.html' && (width === 320 || width === 390 || width === 959 || width === 960 || width === 1280)) {
          await safeScreenshot(page, path.join(OUT, `${PHASE}_${engine.name}_${width}_closed.png`));
          if (m.mobile) {
            await page.locator('#navbutton').click();
            await page.waitForTimeout(350);
            await safeScreenshot(page, path.join(OUT, `${PHASE}_${engine.name}_${width}_open.png`));
            await page.keyboard.press('Escape');
            await page.waitForTimeout(250);
            await testDrawer(page, pagePath);
            if (width === 390) await testListenerRegression(browser, engine);
          }
        }
        if (pagePath === 'doc/search.html' && (width === 320 || width === 390 || width === 959 || width === 960 || width === 1280)) {
          await testSearch(page, pagePath);
          await safeScreenshot(page, path.join(OUT, `${PHASE}_${engine.name}_${width}_search.png`));
        }
        classifyPageMessages(page, pagePath);
      } catch (error) {
        check('页面测试未抛出异常', false, { error: String(error) });
      } finally {
        if (context) await context.close();
      }
    }
  }
  await browser.close();
}

for (const engine of engines) {
  try { await runEngine(engine); }
  catch (error) { check('浏览器测试流程完成', false, { engine: engine.name, error: String(error) }); }
}

fs.writeFileSync(path.join(OUT, `report_${PHASE}.json`),
  JSON.stringify({ phase: PHASE, assertions, results }, null, 2));

const failed = assertions.filter(a => !a.ok && a.severity === 'fail');
const warned = assertions.filter(a => !a.ok && a.severity === 'warn');
const passed = assertions.filter(a => a.ok);
console.log(JSON.stringify({
  phase: PHASE,
  engines: engines.map(e => e.name),
  widths: WIDTHS,
  pages: PAGES.length,
  assertions: assertions.length,
  passed: passed.length,
  failed: failed.length,
  warnings: warned.length,
  report: path.join(OUT, `report_${PHASE}.json`)
}, null, 2));
if (failed.length) console.error(failed.slice(0, 25).map(a => `#${a.id} ${a.name} [${a.engine}/${a.width}/${a.page}]`).join('\n'));
if (failed.length) process.exitCode = 1;
