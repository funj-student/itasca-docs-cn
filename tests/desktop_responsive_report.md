# PC 端专项修复测试报告

分支：`fix/desktop-navigation-only`　基线：`origin/main` @ `d28ea7fe`（已含 PR #8 移动端适配、PR #7 译文修订）
**移动端断点、抽屉、触摸滚动、遮罩、焦点与背景滚动锁定逻辑未修改；未合并 PR #9，未回滚 PR #8。**

## 1. 找到的 PC 端实际问题与根因

1. **目录 iframe 与侧栏宽度不一致**：`.sidenav` 固定 350px，`iframe#toctobj2` 基础宽度 390px；iframe 右侧 40px 被侧栏裁掉，目录条目文字在右缘截断。35/35 次测量不一致，5 个宽度的首页检出被截断的 `.jstree-anchor`。
2. **正文内边距不对称**：`#mainbody` 基础 `padding: 1em 2em 4em 4em`（左 64px / 右 32px），文字块在容器内偏右。35/35 次测量不合格。
3. **大屏阅读区偏窄且命令表被截断**：`#mainbody { max-width:35em }` 使 1440/1920 下阅读区仅 656px（14 次低于合理下限）；`table.comfishtable` 固定 550px + 单元格 `white-space:nowrap; overflow:hidden` 把 `building-blocks`、`extrude`、`structure` 等命令截断（1280/1440/1920 检出）。
4. **窄桌面空间不足**：960–1100px 保留 350px 侧栏（960 下占 36% 视口），正文被挤压；材料属性页 MathJax SVG 公式宽 637px，造成 960/1024 下 15px 整页横向溢出。
5. **目录滚动**：展开多级后 iframe 文档可滚动，但原测试单次滚轮步长不足导致假阴性；测试已改为最多 3 次滚轮后判定，并在双引擎下验证顶部↔底部完整滚动。

## 2. 修改的文件

| 文件 | 说明 |
| --- | --- |
| `doc/_static/itasca.css` | 仅在文件末尾追加 3 个 `@media (min-width: 960px)` 规则块；**未修改任何 `max-width: 959px` 内部规则** |
| `tests/desktop_browser_check.mjs` | 新增桌面断言验收（失败时退出码 1） |
| `tests/capture_screens.mjs` / `tests/compare_screens.py` | 前后截图采集与逐像素对比 |
| `tests/pages_server.py` | 本地/CI 模拟 GitHub Pages 子路径 `/itasca-docs-cn/` |
| `.github/workflows/desktop-browser-check.yml` | 桌面 CI 冒烟矩阵 |
| `tests/desktop_issue_baseline.md` / 本报告 | 问题定位与结果记录 |

`doc/_static/icgscripts.js`、`doc/search.html`、`doc/_static/zh-search.js` **未修改**。

## 3. 关键 CSS 修改与适用宽度

| 规则 | 宽度范围 | 原因 |
| --- | --- | --- |
| `.sidenav iframe, iframe#toctobj2 { width:100% !important }` | ≥960px | iframe 继承侧栏实际宽度，消除 40px 裁切；移动端 iframe 布局保持原样 |
| `#mainbody { padding-left:2em; padding-right:2em }` | ≥960px | 纠正 4em/2em 不对称内边距，文字块居中 |
| `table.comfishtable { width:100%; table-layout:auto }` + 单元格 `white-space:normal; overflow:visible; overflow-wrap:anywhere` | ≥960px | 命令名完整换行，不再被固定 550px 表格截断 |
| MathJax 容器 `max-width:100%; overflow-x:auto` | ≥960px | 窄桌面公式局部滚动，不撑宽整页 |
| `div#navbutton { z-index:210 }` | ≥960px | 保证切换按钮在内容边缘之上，不遮挡标题 |
| `body.nav-open .sidenav/#main/#navbutton` 宽度与边距 300px | 960–1100px | 窄桌面减少侧栏占比，正文更可用；关闭时仍由原逻辑置 0 |
| `#mainbody { max-width:42em }` | ≥1440px | 大屏阅读区从 656px 增至 736px，仍保持舒适行宽而非填满屏幕 |

## 4. 修改前后桌面截图对比

截图目录：`_desktop_artifacts/before_desktop_chromium_*` 与 `after_desktop_chromium_*`（各 30 张，960/1024/1280/1440/1920 × 7 页）。

- **1280px 首页**：修复前侧栏 350px / iframe 390px，右侧命令 `building-`、`extrude`、`structu` 被截断；修复后侧栏与 iframe 同为 350px，`building-blocks`、`extrude`、`structure` 完整换行显示，正文左移 32px。
- **960px 首页**：修复前侧栏 350px，正文被挤压；修复后侧栏 300px、正文增加约 48px 可用宽度，表格文字完整换行。
- **1920px 首页**：修复前正文总宽 656px 且表格截断；修复后正文 736px、表格完整，仍保留两侧留白。
- 逐像素对比：30/30 桌面截图发生变化（预期），差异集中在侧栏宽度、正文位置与表格换行区域。

## 5. 手机端截图差异与功能回归

- 截图：`_desktop_artifacts/before_mobile_chromium_*` / `after_mobile_chromium_*`，宽度 320/375/390/430/768/959 × 4 页 = 24 组。
- 逐像素对比结果：**24/24 完全一致，差异像素 0**（`compare_before_mobile_after_mobile.json`）。
- 功能回归：运行现有 `tests/mobile_browser_check.mjs`，6 个移动宽度 × 13 个页面，**632 条断言，632 通过，0 失败**，覆盖目录打开/关闭、连续滚动、节点展开与跳转、阅读位置恢复、搜索、代码/表格/公式与横向溢出。
- 结论：移动端视觉与功能零回归。

## 6. 桌面端浏览器测试结果

Playwright 1.65.1；Chromium **159.0.8154.6**、WebKit **27.2**。
视口 960/1024/1280/1440/1920；页面：首页、完整目录、搜索页、FLAC3D 命令页、FISH 页、3DEC 页、材料属性表页、PFC 页。
断言包括：整页横向溢出、Pages 子路径样式加载、正文可见性与裁切、iframe 与侧栏宽度一致、目录条目不被截断、目录多级展开（≥5 节点）、目录独立滚动到底再回顶、目录按钮不遮挡标题、内边距对称、大屏/窄桌面阅读区宽度、导航收起/展开与阅读位置保持、目录链接跳转、搜索结果与溢出、浏览器错误。

**结果：707 条断言，707 通过，0 失败，0 告警，退出码 0。**
本地 CI 冒烟矩阵（960/1280/1920 + Chromium/WebKit + 3 页）亦通过。

## 7. 移动端浏览器测试结果

见第 5 节：632 条断言全部通过，24/24 截图完全一致。

## 8. Python 与 CI

- `python -B -m unittest discover -s tests -v`：62 项通过
- `python scripts/check_terms.py`：通过（terms=125, html_rows=125）
- `python scripts/check_links.py --known-missing scripts/known-missing-images.json`：通过（6584 页，2 个已知缺失文件，0 缺失锚点）
- GitHub Actions 运行链接与 PR 地址：见 PR 页面（推送后补充）。

## 9. 尚未解决的限制

1. 未在 Android/iOS 真机或微信内置浏览器验证；移动端零回归结论基于 Chromium 模拟与像素对比。
2. Firefox 未安装，桌面双引擎为 Chromium + WebKit。
3. 桌面目录 iframe 仍随页面加载约 1.34MB；按需加载需改动静态 HTML，超出本轮范围。
4. 窄桌面（960–1100px）命令表格虽然不再截断，但中文与英文括号仍会出现较密的换行；这是空间有限下的可读性权衡，未改字体或配色。
5. 本地 CI 使用模拟的 `/itasca-docs-cn/` 子路径；线上 Pages 行为需在 PR 环境再次确认。
