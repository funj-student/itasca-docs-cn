/**
 * Generic screenshot/metrics capture for before/after visual comparison.
 * MODE=baseline|after, PHASE=<label>, WIDTHS=..., PAGES=..., OUT=<dir>
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium, webkit } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8770/itasca-docs-cn';
const OUT = process.env.OUT || path.resolve('_desktop_artifacts');
const PHASE = process.env.PHASE || 'baseline';
const WIDTHS = (process.env.WIDTHS || '960,1024,1280,1440,1920').split(',').map(Number).filter(Boolean);
const PAGES = (process.env.PAGES || [
  'index.html',
  'doc/contents.html',
  'doc/search.html',
  'doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html',
  'doc/3dec/block/doc/manual/block_manual/block_fish/block/fish_block.area.html',
  'doc/pfc/ccfd/doc/ball_cfd_manual/ball_cfd_commands/cmd_ball.cfd.attribute.html'
].join(',')).split(',').filter(Boolean);
const ENGINES = (process.env.ENGINES || 'chromium').split(',').filter(Boolean);

fs.mkdirSync(OUT, { recursive: true });
const entries = [];

for (const engineName of ENGINES) {
  const engine = engineName === 'webkit' ? webkit : chromium;
  const launchOptions = { headless: true };
  if (engineName === 'chromium' && process.env.CHROMIUM_EXEC) launchOptions.executablePath = process.env.CHROMIUM_EXEC;
  const browser = await engine.launch(launchOptions);
  for (const width of WIDTHS) {
    const height = width <= 959 ? 800 : 900;
    const context = await browser.newContext({
      viewport: { width, height },
      isMobile: engineName === 'chromium' && width <= 959,
      hasTouch: width <= 959,
      deviceScaleFactor: 1
    });
    const page = await context.newPage();
    for (const pagePath of PAGES) {
      const label = pagePath.replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 70);
      const file = path.join(OUT, `${PHASE}_${engineName}_${width}_${label}.png`);
      try {
        const response = await page.goto(`${BASE}/${pagePath}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
        if (!response || response.status() >= 400) throw new Error('HTTP ' + (response && response.status()));
        await page.waitForFunction(() => !!window.ItascaNav, null, { timeout: 20000 });
        // MathJax 的 "Processing math" 加载提示会造成截图时序差异。
        await page.waitForFunction(() => !document.body.innerText.includes('Processing math'), null, { timeout: 20000 }).catch(() => {});
        await page.evaluate(() => document.fonts && document.fonts.ready);
        await page.waitForTimeout(width <= 959 ? 400 : 1400);
        const metrics = await page.evaluate(() => {
          const rect = sel => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
          };
          const ifr = document.getElementById('toctobj2');
          return {
            innerWidth: window.innerWidth,
            docScrollWidth: document.documentElement.scrollWidth,
            sidenav: rect('#mySidenav'),
            iframe: rect('#toctobj2'),
            iframeCssWidth: ifr ? getComputedStyle(ifr).width : null,
            main: rect('#main'),
            mainbody: rect('#mainbody'),
            navbutton: rect('#navbutton'),
            navOpen: document.body.classList.contains('nav-open'),
            mobile: window.ItascaNav.isMobile(),
            searchInput: rect('#mainbody input[name="q"]'),
            searchSubmit: rect('#mainbody input[type="submit"]')
          };
        });
        await page.screenshot({ path: file, timeout: 60000, animations: 'disabled' });
        entries.push({ engine: engineName, width, page: pagePath, file, metrics });
      } catch (error) {
        entries.push({ engine: engineName, width, page: pagePath, file, error: String(error) });
      }
    }
    await context.close();
  }
  await browser.close();
}
fs.writeFileSync(path.join(OUT, `capture_${PHASE}.json`), JSON.stringify(entries, null, 2));
console.log(JSON.stringify({ phase: PHASE, entries: entries.length,
  errors: entries.filter(e => e.error).length, out: OUT }, null, 2));
