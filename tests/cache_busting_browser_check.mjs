/**
 * 静态资源缓存失效的浏览器验收。
 *
 * 两种模式：
 *   MODE=regression（默认）  对构建产物做 PC/移动端功能回归，验证 ?v= 资源不 404、
 *                            样式确实生效、目录/搜索/文档页可用。需 BASE_URL。
 *   MODE=two-deploy          模拟两次连续部署：同一端口、同一持久化浏览器配置
 *                            （保留磁盘 HTTP 缓存），静态服务器发送与 GitHub Pages
 *                            一致的 Cache-Control: max-age=600。验证：
 *                            - itasca.css 的 ?v= 随内容变化；
 *                            - 未修改资源（pygments.css）版本号保持稳定；
 *                            - 新 HTML 到达后页面实际拿到新 CSS（探针变量 deploy2）；
 *                            - 页面功能无回归。
 *
 * 任何阻塞性失败都会使进程以非零退出码结束。
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium, webkit } = require('playwright');

const MODE = process.env.MODE || 'regression';
const BASE = process.env.BASE_URL || 'http://127.0.0.1:8773/itasca-docs-cn';
const OUT = process.env.OUT || '.';
const ENGINES = (process.env.ENGINES || 'chromium').split(',');
const CHROMIUM_EXEC = process.env.CHROMIUM_EXEC || undefined;

const PAGES = [
  { path: 'index.html', name: '首页', kind: 'manual' },
  { path: 'doc/search.html', name: '搜索页', kind: 'manual', search: true },
  {
    path: 'doc/3dec/block/doc/manual/block_manual/block_fish/block/fish_block.area.html',
    name: 'FISH 语句页',
    kind: 'manual',
  },
  {
    path: 'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html',
    name: 'FLAC3D 命令页',
    kind: 'manual',
  },
  {
    path: 'doc/doxygen/html/3dec_2block_2interface_2igpdata_8h.html',
    name: 'Doxygen 页',
    kind: 'doxygen',
  },
];
const DESKTOP_WIDTHS = [1280, 1920];
const MOBILE_WIDTHS = [375, 390, 430];

const assertions = [];
fs.mkdirSync(OUT, { recursive: true });
function check(name, ok, detail) {
  assertions.push({ name, ok: !!ok, severity: 'fail', detail });
  if (!ok) console.log(`FAIL  ${name}  ${detail ? JSON.stringify(detail).slice(0, 300) : ''}`);
  return ok;
}
/** 明确的非阻塞告警：记录但不影响退出码（仅限已文档化的 WebKit/MathJax 限制）。 */
function warn(name, detail) {
  assertions.push({ name, ok: true, severity: 'warn', detail });
  console.log(`WARN  ${name}  ${detail ? JSON.stringify(detail).slice(0, 200) : ''}`);
}

function engineLaunchOptions(name) {
  const opts = { headless: true };
  if (name === 'chromium' && CHROMIUM_EXEC) opts.executablePath = CHROMIUM_EXEC;
  return opts;
}

/** 从页面读取资源版本：返回 { 相对路径: version|null } */
async function collectVersions(page) {
  return page.evaluate(() => {
    const out = {};
    for (const el of document.querySelectorAll('link[href], script[src]')) {
      const raw = el.getAttribute('href') || el.getAttribute('src') || '';
      if (!/\.(css|js)(\?|$)/.test(raw) || /^https?:|^\/\//.test(raw)) continue;
      const abs = new URL(raw, location.href);
      const params = new URLSearchParams(abs.search);
      const key = abs.pathname.replace(/^\/itasca-docs-cn\//, '');
      out[key] = params.get('v');
    }
    return out;
  });
}

async function testPage(browser, engineName, width, pageDef) {
  const label = `${engineName} ${width}px ${pageDef.name}`;
  const isMobile = width <= 959;
  const context = await browser.newContext({
    viewport: { width, height: 900 },
    deviceScaleFactor: 1,
    isMobile,
    hasTouch: isMobile,
  });
  const page = await context.newPage();
  const cssJsResponses = [];
  const pageErrors = [];
  const consoleErrors = [];
  page.on('response', (res) => {
    const url = res.url();
    if (/\.(css|js)(\?|$)/.test(url)) cssJsResponses.push({ url, status: res.status() });
  });
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));
  page.on('console', (m) => {
    if (m.type() === 'error') {
      const loc = m.location ? m.location() : null;
      consoleErrors.push({ text: m.text().slice(0, 200), url: (loc && loc.url) || '' });
    }
  });

  try {
    const url = `${BASE}/${pageDef.path}`;
    const response = await page.goto(url, { waitUntil: 'load', timeout: 90000 });
    check(`${label}: HTTP 200`, response && response.status() === 200, {
      status: response && response.status(),
    });

    // 1) 版本化资源必须全部成功（?v= 不能造成 404）。
    const failed = cssJsResponses.filter((r) => r.status >= 400);
    check(`${label}: CSS/JS 无 4xx/5xx`, failed.length === 0, failed.slice(0, 5));

    // 2) 确实发起了带版本号的本地资源请求。
    const versioned = cssJsResponses.filter((r) => /[?&]v=[0-9a-f]{10}/.test(r.url));
    check(`${label}: 存在版本化 CSS/JS 请求`, versioned.length >= 2, { count: versioned.length });

    // 3) HTML 内本地 CSS/JS 引用全部带版本号。
    const versions = await collectVersions(page);
    const missingV = Object.entries(versions).filter(([, v]) => !v);
    check(`${label}: HTML 引用全部带版本号`, Object.keys(versions).length > 0 && missingV.length === 0,
      missingV.slice(0, 5));

    // 4) 样式确实生效（body 字体来自 itasca.css 首条规则；Doxygen 页用自身样式表）。
    const styleState = await page.evaluate(() => ({
      font: getComputedStyle(document.body).fontFamily,
      sheets: document.styleSheets.length,
      probe: getComputedStyle(document.documentElement).getPropertyValue('--cache-bust-probe').trim(),
    }));
    check(`${label}: 样式表已加载生效`, styleState.sheets >= 2, styleState);
    if (pageDef.kind === 'manual') {
      check(`${label}: itasca.css 生效（Lato 字体）`, /Lato/.test(styleState.font), styleState);
      const hasMain = await page.evaluate(() => !!document.getElementById('mainbody'));
      check(`${label}: 正文容器存在`, hasMain, styleState);
    } else {
      const hasDoc = await page.evaluate(() => !!document.querySelector('.contents, #top'));
      check(`${label}: Doxygen 内容容器存在`, hasDoc, styleState);
    }

    if (pageDef.kind === 'manual') {
      // 5) 目录 iframe 可用。
      let navtree = null;
      for (let i = 0; i < 40 && !navtree; i++) {
        navtree = page.frames().find((f) => f.url().includes('navtree'));
        if (!navtree) await page.waitForTimeout(250);
      }
      check(`${label}: 目录 iframe 已加载`, !!navtree, { frames: page.frames().length });
      if (navtree) {
        // jstree 初始化耗时因页面与引擎而异（WebKit 搜索页明显更慢），必须等待。
        let anchors = 0;
        for (let i = 0; i < 60 && anchors === 0; i++) {
          anchors = await navtree.locator('.jstree-anchor').count().catch(() => 0);
          if (!anchors) await page.waitForTimeout(250);
        }
        check(`${label}: 目录节点存在`, anchors > 0, { anchors });
      }

      // 6) 按钮与开合交互（移动端：默认收起，点击打开、Escape 关闭；
      //    桌面端：默认展开，点击收起、再次点击展开）。
      const btn = page.locator('#navbutton');
      if (await btn.count()) {
        if (isMobile) {
          await btn.click();
          // 抽屉目标宽度为 min(85vw, 340px)，需等待 0.2s 过渡完成再断言。
          await page
            .waitForFunction(
              () => {
                const w = document.getElementById('mySidenav').getBoundingClientRect().width;
                return Math.abs(w - Math.min(window.innerWidth * 0.85, 340)) < 2;
              },
              null,
              { timeout: 8000 }
            )
            .catch(() => {});
          const opened = await page.evaluate(() => ({
            navOpen: document.body.classList.contains('nav-open'),
            sideWidth: Math.round(document.getElementById('mySidenav').getBoundingClientRect().width),
            expected: Math.round(Math.min(window.innerWidth * 0.85, 340)),
          }));
          check(`${label}: 目录可打开`,
            opened.navOpen && Math.abs(opened.sideWidth - opened.expected) <= 2, opened);
          await page.keyboard.press('Escape');
          await page
            .waitForFunction(() => document.getElementById('mySidenav').getBoundingClientRect().width <= 10, null, { timeout: 8000 })
            .catch(() => {});
          const closed = await page.evaluate(() => ({
            navOpen: document.body.classList.contains('nav-open'),
            sideWidth: Math.round(document.getElementById('mySidenav').getBoundingClientRect().width),
          }));
          check(`${label}: 目录可关闭`, !closed.navOpen && closed.sideWidth <= 10, closed);
        } else {
          const initiallyOpen = await page.evaluate(() =>
            document.body.classList.contains('nav-open'));
          await btn.click();
          await page
            .waitForFunction(() => document.getElementById('mySidenav').getBoundingClientRect().width <= 10, null, { timeout: 8000 })
            .catch(() => {});
          const collapsed = await page.evaluate(() => ({
            navOpen: document.body.classList.contains('nav-open'),
            sideWidth: Math.round(document.getElementById('mySidenav').getBoundingClientRect().width),
          }));
          await btn.click();
          await page
            .waitForFunction(() => Math.abs(document.getElementById('mySidenav').getBoundingClientRect().width - 350) < 2, null, { timeout: 8000 })
            .catch(() => {});
          const expanded = await page.evaluate(() => ({
            navOpen: document.body.classList.contains('nav-open'),
            sideWidth: Math.round(document.getElementById('mySidenav').getBoundingClientRect().width),
          }));
          check(`${label}: 桌面目录可收起`,
            initiallyOpen && !collapsed.navOpen && collapsed.sideWidth <= 10, { initiallyOpen, collapsed });
          check(`${label}: 桌面目录可重新展开`,
            expanded.navOpen && Math.abs(expanded.sideWidth - 350) <= 2, expanded);
        }
      } else {
        check(`${label}: 目录按钮存在`, false, {});
      }

      // 7) 搜索页：Search 对象、版本化索引请求与实际检索。
      if (pageDef.search) {
        const searchState = await page.evaluate(() => ({
          hasSearch: typeof window.Search === 'object' && !!window.Search,
        }));
        check(`${label}: Search 对象存在`, searchState.hasSearch, searchState);
        const indexReq = await page.evaluate(() =>
          performance
            .getEntriesByType('resource')
            .map((e) => e.name)
            .filter((n) => n.includes('searchindex.js'))
        );
        check(`${label}: searchindex.js 带版本号加载`,
          indexReq.some((n) => /searchindex\.js\?v=[0-9a-f]{10}/.test(n)), indexReq);
        // 用 ?q= 查询地址直接验证搜索管线（索引加载 + 检索 + 渲染），
        // 避免表单提交与页面导航的时序竞争；表单本身由既有移动/桌面套件覆盖。
        await page.goto(`${BASE}/${pageDef.path}?q=zone`, { waitUntil: 'load', timeout: 90000 });
        await page
          .waitForFunction(() => document.querySelectorAll('#zh-search-list li').length > 0, null, {
            timeout: 60000,
          })
          .catch(() => {});
        const sr = await page.evaluate(() => ({
          count: document.querySelectorAll('#zh-search-list li').length,
          status: (document.getElementById('zh-search-status') || {}).textContent || '',
          indexed: (performance.getEntriesByType('resource') || [])
            .map((e) => e.name)
            .some((n) => /searchindex\.js\?v=[0-9a-f]{10}/.test(n)),
        }));
        check(`${label}: 搜索返回结果`, sr.count > 0 && !/失败|无法|没有找到/.test(sr.status), sr);
        check(`${label}: 索引请求带版本号`, sr.indexed, sr);
      }
    }

    // 8) 无阻塞性脚本错误（浏览器自动请求 favicon 的 404 与已知 MathJax blob 告警不计）。
    //    「Cannot load blob: … due to access control checks」是 WebKit + MathJax 2.7
    //    的已知限制（既有移动端测试报告已记录），功能不受影响，明确归类为非阻塞告警。
    const benignBlob = pageErrors.filter((e) => /Cannot load blob:.*due to access control checks/i.test(e));
    const realPageErrors = pageErrors.filter((e) => !/Cannot load blob:.*due to access control checks/i.test(e));
    if (benignBlob.length) warn(`${label}: WebKit MathJax blob 告警（已知非阻塞）`, benignBlob.slice(0, 2));
    check(`${label}: 无页面异常`, realPageErrors.length === 0, realPageErrors);
    const realConsoleErrors = consoleErrors.filter(
      (e) => !/favicon/i.test(e.url) && !/MathJax.*blob/i.test(e.text) && !/favicon/i.test(e.text)
    );
    check(`${label}: 无控制台错误`, realConsoleErrors.length === 0, realConsoleErrors.slice(0, 3));

    return { label, versions, probe: styleState.probe, cssJsRequests: cssJsResponses.length };
  } catch (e) {
    check(`${label}: 页面流程完整执行`, false, String(e).slice(0, 300));
    return { label, error: String(e) };
  } finally {
    await context.close();
  }
}

async function runRegression() {
  const results = [];
  for (const engineName of ENGINES) {
    const browser = await (engineName === 'webkit' ? webkit : chromium).launch(
      engineLaunchOptions(engineName)
    );
    for (const width of [...DESKTOP_WIDTHS, ...MOBILE_WIDTHS]) {
      for (const pageDef of PAGES) {
        results.push(await testPage(browser, engineName, width, pageDef));
      }
    }
    await browser.close();
  }

  // 跨页面一致性：同一资源在所有页面必须使用同一版本号（相对路径解析正确）。
  const byAsset = new Map();
  for (const r of results) {
    if (!r.versions) continue;
    for (const [asset, v] of Object.entries(r.versions)) {
      if (!byAsset.has(asset)) byAsset.set(asset, new Set());
      byAsset.get(asset).add(v);
    }
  }
  const inconsistent = [...byAsset.entries()].filter(([, set]) => set.size > 1);
  check('同一资源在所有页面版本号一致', inconsistent.length === 0, inconsistent.slice(0, 5));

  fs.writeFileSync(path.join(OUT, 'cache_regression.json'),
    JSON.stringify({ assertions, results }, null, 2));
}

/** 忠实模拟 GitHub Pages 的静态服务器：子路径 + Cache-Control: max-age=600。 */
function startServer(rootRef, port) {
  const MIME = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.gif': 'image/gif', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
    '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject', '.txt': 'text/plain; charset=utf-8',
    '.md': 'text/plain; charset=utf-8', '.pdf': 'application/pdf',
    '.dic': 'text/plain; charset=utf-8',
  };
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    let p = decodeURIComponent(url.pathname);
    if (p === '/itasca-docs-cn') p = '/';
    if (!p.startsWith('/itasca-docs-cn/')) {
      res.statusCode = 404;
      return res.end('not found');
    }
    const rel = p.slice('/itasca-docs-cn/'.length) || 'index.html';
    const resolvedRoot = path.resolve(rootRef.root);
    const file = path.resolve(resolvedRoot, rel);
    if (path.relative(resolvedRoot, file).startsWith('..')) {
      res.statusCode = 403;
      return res.end('forbidden');
    }
    let data;
    try {
      data = fs.readFileSync(file);
    } catch (e) {
      res.statusCode = 404;
      return res.end('not found');
    }
    const stat = fs.statSync(file);
    res.setHeader('Content-Type', MIME[path.extname(file).toLowerCase()] || 'application/octet-stream');
    res.setHeader('Cache-Control', 'max-age=600'); // 与 GitHub Pages 一致
    res.setHeader('Last-Modified', stat.mtime.toUTCString());
    res.setHeader('ETag', `"${stat.size.toString(16)}-${stat.mtimeMs.toString(16)}"`);
    res.setHeader('Content-Length', data.length);
    if (req.method === 'HEAD') return res.end();
    res.end(data);
  });
  return new Promise((resolve) => {
    server.listen(port, '127.0.0.1', () => resolve(server));
  });
}

async function runTwoDeploy() {
  const port = 8773;
  const base = `http://127.0.0.1:${port}/itasca-docs-cn`;
  const profileDir = path.join(OUT, 'cache_profile');
  fs.rmSync(profileDir, { recursive: true, force: true });
  const state = {};

  const rootRef = { root: path.resolve(process.env.DEPLOY1) };
  const server = await startServer(rootRef, port);
  const launch = () =>
    chromium.launchPersistentContext(profileDir, {
      headless: true,
      viewport: { width: 1280, height: 900 },
      executablePath: CHROMIUM_EXEC,
    });

  // ---- 部署一：首次访问（浏览器把 HTML 与 CSS/JS 按 max-age=600 缓存）----
  let context = await launch();
  let page = await context.newPage();
  await page.goto(`${base}/index.html`, { waitUntil: 'load', timeout: 90000 });
  await page.waitForTimeout(800);
  state.deploy1 = {
    versions: await collectVersions(page),
    probe: await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--cache-bust-probe').trim()),
  };
  check('部署一: itasca.css 带版本号', !!state.deploy1.versions['doc/_static/itasca.css'],
    state.deploy1.versions);
  check('部署一: 探针为空（旧 CSS）', state.deploy1.probe === '', { probe: state.deploy1.probe });
  await context.close();

  // ---- 切换为部署二（同端口、同浏览器配置，磁盘缓存仍在）----
  rootRef.root = path.resolve(process.env.DEPLOY2);

  context = await launch();
  page = await context.newPage();
  // 以带独立查询串的 HTML 地址访问，确保主文档必然从服务器重新获取
  // （模拟用户拿到新 HTML；HTML 自身缓存窗口见说明文档）。
  await page.goto(`${base}/index.html?cachetest=2`, { waitUntil: 'load', timeout: 90000 });
  await page.waitForTimeout(800);
  state.deploy2 = {
    versions: await collectVersions(page),
    probe: await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--cache-bust-probe').trim()),
  };

  const v1 = state.deploy1.versions['doc/_static/itasca.css'];
  const v2 = state.deploy2.versions['doc/_static/itasca.css'];
  const pyg1 = state.deploy1.versions['doc/_static/pygments.css'];
  const pyg2 = state.deploy2.versions['doc/_static/pygments.css'];

  check('两次部署: itasca.css 版本号发生变化', !!v1 && !!v2 && v1 !== v2, { v1, v2 });
  check('两次部署: 未修改的 pygments.css 版本号保持稳定', !!pyg1 && pyg1 === pyg2, { pyg1, pyg2 });
  check('两次部署: 新 HTML 到达后实际加载新 CSS（探针=deploy2）', state.deploy2.probe === 'deploy2',
    { probe: state.deploy2.probe });

  // 旧 URL 的缓存内容仍是旧 CSS —— 证明若 HTML 未带新版本号就会拿到旧资源。
  const staleProbe = await page.evaluate(async (oldUrl) => {
    const res = await fetch(oldUrl, { cache: 'force-cache' });
    const text = await res.text();
    return /--cache-bust-probe:\s*deploy2/.test(text) ? 'new' : 'old';
  }, `/itasca-docs-cn/doc/_static/itasca.css?v=${v1}`);
  check('两次部署: 旧版本 URL 命中缓存旧内容（说明版本号必要性）', staleProbe === 'old',
    { staleProbe });

  // 功能无回归：桌面端默认展开，点击应收起、再次点击应展开。
  const navInitiallyOpen = await page.evaluate(() => document.body.classList.contains('nav-open'));
  await page.locator('#navbutton').click();
  await page.waitForTimeout(700);
  const navAfterFirst = await page.evaluate(() => ({
    navOpen: document.body.classList.contains('nav-open'),
    sideWidth: Math.round(document.getElementById('mySidenav').getBoundingClientRect().width),
  }));
  await page.locator('#navbutton').click();
  await page
    .waitForFunction(() => Math.abs(document.getElementById('mySidenav').getBoundingClientRect().width - 350) < 2, null, { timeout: 8000 })
    .catch(() => {});
  const navAfterSecond = await page.evaluate(() => ({
    navOpen: document.body.classList.contains('nav-open'),
    sideWidth: Math.round(document.getElementById('mySidenav').getBoundingClientRect().width),
  }));
  check(
    '两次部署: 目录开关功能正常',
    navInitiallyOpen && !navAfterFirst.navOpen && navAfterFirst.sideWidth <= 10 &&
      navAfterSecond.navOpen && navAfterSecond.sideWidth > 100,
    { navInitiallyOpen, navAfterFirst, navAfterSecond }
  );

  await context.close();
  server.close();
  fs.writeFileSync(path.join(OUT, 'cache_two_deploy.json'),
    JSON.stringify({ assertions, state }, null, 2));
}

async function main() {
  if (MODE === 'two-deploy') {
    await runTwoDeploy();
  } else {
    await runRegression();
  }
  const failed = assertions.filter((a) => !a.ok);
  const warnings = assertions.filter((a) => a.severity === 'warn');
  const passed = assertions.filter((a) => a.ok && a.severity !== 'warn').length;
  console.log(`\n断言 ${assertions.length} 条：${passed} 通过，${failed.length} 失败，${warnings.length} 告警`);
  if (failed.length) {
    for (const f of failed.slice(0, 15)) console.log(`  - ${f.name}`);
    process.exitCode = 1;
  }
}

main().catch((e) => {
  console.error('测试脚本异常:', e);
  process.exitCode = 1;
});
