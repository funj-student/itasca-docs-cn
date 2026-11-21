# Itasca 7.0 中文手册移动端适配测试报告（PR #8 第二轮修订）

分支：`fix/mobile-responsive-v2`　基线：`origin/main` @ `fe97a02b`（已含合并的 PR #5）

本轮复核确认移动端导航重构方向正确，重点修正**验收真实性**：让 Playwright 具备失败判定能力，补充真实手势、iframe 键盘焦点与重复监听器回归，并接入可复现的 CI 冒烟测试。

## 一、本轮新增根因与修复

| 问题 | 修复 |
| --- | --- |
| 测试脚本只记录结果，从不设置非零退出码；异常被捕获后继续运行 | 引入带 `severity` 的断言系统；`fail` 断言失败或异常统一计入失败数，脚本末尾设置 `process.exitCode = 1`；负向验证（错误 BASE_URL）确认退出码为 1 |
| 目录滚动仅用 `window.scrollTo()`，不能证明手势可用 | 新增 Chromium CDP 真实 `touchStart/touchMove/touchEnd` 手势与 WebKit 滚轮交互；程序化滚动保留但明确标注为“非手势基线” |
| Escape 监听只在父页面，焦点进入 iframe 后事件不冒泡 | 在同源 iframe 内注入一次性 keydown 监听，调用 `parent.ItascaNav.closeFromIframe()`；关闭时先 blur iframe 内焦点并延迟恢复焦点到目录按钮 |
| 打开目录后焦点未进入抽屉；关闭后内部元素仍可被 Tab 聚焦 | 打开时聚焦关闭按钮；关闭时设置 `inert`/`aria-hidden`/`tabindex=-1`，焦点恢复至目录按钮 |
| `prepareTocFrame()` 在初始化、打开、布局切换时重复注册 iframe `load` 监听 | 以 `tocBoundFrame` 记录已绑定元素，只安装一次；`ItascaNav.tocListenerInstalls()` 暴露计数，并在 959↔960 反复切换后断言仍为 1 |
| 测试未覆盖 959/960 分界、完整目录页、复杂公式、长代码、多列数据表格 | 默认页面清单扩至 14 个，宽度含 959/960；增加正文裁切/遮挡检测 |
| CI 只跑 Python 检查 | 新增 `.github/workflows/mobile-browser-check.yml`，Playwright 版本由 `package-lock.json` 固定，Chromium+WebKit，5 个视口、3 类页面，失败使 CI 失败 |

## 二、断言分类规则（非阻塞告警 vs 真正失败）

**失败（severity=fail，`process.exitCode=1`）：**
- 页面 HTTP >=400、页面加载/关键交互抛异常、浏览器启动失败
- 非预期整页横向溢出（`documentElement.scrollWidth - innerWidth > 1`）
- 移动端目录按钮 <44×44 或缺少 `role/aria-expanded/aria-label`
- 目录打不开/关不上（遮罩、Escape、关闭按钮任一失效）、遮罩不可见
- 目录节点展开数 <3、目录链接无法导航
- 目录手势/滚轮无法滚到底或无法回到顶部；滑动误触条目；背景滚动位置变化；滑动中抽屉关闭
- iframe 内 Escape 不能关闭目录或焦点未恢复；抽屉关闭后仍可聚焦
- 阅读位置恢复失败
- 搜索索引加载失败、无结果、标题筛选框溢出、搜索页整页溢出
- 移动端正文被 CSS 裁切、图片超出视口
- `load` 监听器重复安装

**非阻塞告警（severity=warn）：**
- WebKit 已知 `Cannot load blob: ... due to access control checks`（MathJax，功能检查仍通过）
- favicon / `.ico` 404
- 截图因字体加载超时（截图仅为证据，不参与功能判定）
- **桌面端** `table.comfishtable` 单元格 `nowrap/overflow:hidden` 造成的裁切（既有桌面设计，本轮不改动桌面排版；移动端同类情况为硬失败）

## 三、真实触摸/滚轮测试说明

- **Chromium**：通过 CDP `Input.dispatchTouchEvent` 在 iframe 区域派发 `touchStart → 10×touchMove → touchEnd`，手指上滑到底、下滑回顶；断言滚动位置达到 `scrollHeight-innerHeight`、回顶 `scrollY<=2`、抽屉保持打开、父页面 `window.scrollY` 不变、iframe 内 `.jstree-anchor` click 计数为 0。
- **WebKit**：移动端 WebKit 的 `isMobile:true` 会禁用 `mouse.wheel`，因此测试上下文仅设置 `hasTouch`，由视口宽度触发同一套 `matchMedia` 移动布局；用 `mouse.wheel` 完成相同的双向滚动断言。
- 程序化 `window.scrollTo()` 结果**不再**被描述为真实手势通过，报告中单列为能力基线。

## 四、修改文件

- `doc/_static/icgscripts.js`：iframe Escape / 焦点 / inert / 监听器去重
- `tests/mobile_browser_check.mjs`：断言系统、真实手势、焦点与监听器回归、扩展页面与裁切检测
- `.github/workflows/mobile-browser-check.yml`：Playwright CI 冒烟矩阵
- `package.json` / `package-lock.json`：固定 Playwright 1.65.1，浏览器版本可复现
- `tests/mobile_responsive_report.md`：本报告

前一轮已完成且本轮未重新设计的共用样式/搜索适配文件：`doc/_static/itasca.css`、`doc/search.html`、`doc/_static/zh-search.js`。

## 五、测试结果

浏览器：Playwright 1.65.1；Chromium **159.0.8154.6**（Playwright build 1255）、WebKit **27.2**（Playwright build 2388）。
本地测试使用仓库外安装的 Playwright 模块；CI 使用 `npm ci` + `npx playwright install --with-deps chromium webkit`，不依赖私人路径。

### CI 冒烟矩阵（MODE=smoke，本地等价运行）

| 项目 | 数值 |
| --- | --- |
| 引擎 | Chromium、WebKit |
| 视口 | 375、390、959、960、1280 |
| 页面 | 首页、搜索页、典型 FLAC3D 命令页 |
| 断言数 | 342 |
| 通过 / 失败 / 告警 | 340 / 0 / 2 |

### 全量本地验收（MODE=full）

视口：320、375、390、430、768、959、960、1280、1920（含 959/960 分界与手机横屏）。
页面（13 个）：`index.html`、`doc/search.html`、`doc/contents.html`、`glossary.html`、`terms.html`、
`doc/flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html`、
`doc/flac3d/docproject/source/modeling/problemsolving/material_properties.html`、
`doc/flac3d/body/doc/manual/buildingblocks_manual/building-blocks_commands/cmd_building-blocks.block.transform.html`、
`doc/3dec/block/doc/manual/block_manual/block_fish/block/fish_block.area.html`、
`doc/3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.analyze-stability.html`、
`doc/3dec/block/test3d/Theory_and_Background/Factor_of_Safety/MC_Slope/mcslope.html`、
`doc/pfc/ccfd/doc/ball_cfd_manual/ball_cfd_commands/cmd_ball.cfd.attribute.html`、
`doc/common/docproject/source/manual/coupling/couplingpfcandflac3d.html`。
`doc/navtree.html` 是 iframe 目录片段（固定 30em 宽），不作为独立阅读页测试；它通过首页抽屉的展开/滚动/导航断言覆盖。

结果（`report_final6.json`）：**1831 条断言，1822 通过，0 失败，9 条非阻塞告警，脚本退出码 0**。
告警构成：4 条桌面 1280/1920 首页 `comfishtable` 既有裁切（按规则降级为 warn）、5 条 WebKit MathJax blob 访问告警。

真实手势结果（Chromium 触摸 / WebKit 滚轮）：各视口均从 `scrollY=0` 滚到底部（320:1664、390:1054/995、959:1118/1059），再回到 0；误触条目数 0；背景滚动位置不变；抽屉未关闭；每次成功展开 8 个节点并完成链接导航。

### 最终验收结果

| 项目 | 结果 |
| --- | --- |
| 浏览器 | Chromium 159.0.8154.6 / WebKit 27.2（Playwright 1.65.1） |
| CI 冒烟视口 | 375 / 390 / 959 / 960 / 1280 |
| CI 冒烟页面 | 首页、搜索页、典型 FLAC3D 命令页 |
| CI 冒烟断言 | 342 条：340 通过，0 失败，2 告警，退出码 0 |
| 全量视口 | 320 / 375 / 390 / 430 / 768 / 959 / 960 / 1280 / 1920 |
| 全量页面 | 13 个（含完整目录、术语表、公式页、长代码页、多列表格页、3DEC/PFC 页） |
| 全量断言 | 1831 条：1822 通过，0 失败，9 告警，退出码 0 |
| 负向验证 | 错误 BASE_URL 时断言失败，脚本退出码 1 |
| Python 回归 | 52 项 unittest 通过；术语检查通过；链接检查通过（2 个已知缺失文件） |

以上为**实际断言运行结果**，不是“生成测试记录即视为通过”。

CI 首轮 `browser-smoke` 曾失败：WebKit 390px 在较慢 runner 上读取到抽屉 0.2s 宽度过渡的中间帧（`drawerWidth=22`），断言“目录可以打开”失败。已将打开操作改为等待 `getBoundingClientRect().width > 40` 后再断言，本地同矩阵复跑通过；修复后的 CI 结果见 PR checks。

### Python 与静态检查

- `python -B -m unittest discover -s tests -v`：52 项通过
- `python scripts/check_terms.py`：通过（terms=125, html_rows=125）
- `python scripts/check_links.py --known-missing scripts/known-missing-images.json`：通过（6584 页，2 个已知缺失文件，0 个缺失锚点）

## 六、与 PR #6 的兼容性

- PR #6（`project/quality-automation`）在 `doc/search.html` 的 `<title>` 后新增一行：`<meta name="robots" content="noindex,follow"/>`。
- PR #8 对同一文件的修改集中在 `<style>` 块、搜索表单与结果控件，**不触及 `<head>` 顶部 title/meta 区域**；两处改动文本上无重叠，SEO 设置与移动端样式可共存。
- 合并依赖：PR #6 与 PR #8 均基于 `fe97a02b`，互不依赖；若先合并 PR #6，PR #8 只需常规三方合并，无需人工改写。`doc/contents.html` 的 canonical/description 同样不在本分支修改范围内。
- 本轮**未**把 `noindex,follow` 复制到 PR #8，也**未**合并任何 PR；仅记录上述依赖关系。

## 七、限制与风险

1. Android 真机、iOS 真机、微信内置浏览器未实测；Chromium 移动视口与 WebKit 模拟通过**不等同于**真机通过。尤其 iOS Safari 原生触摸惯性未在真机验证。
2. WebKit 的 `mouse.wheel` 是在非 `isMobile` 模拟模式下运行的（仍为 375/390/959px 移动布局，`hasTouch` 开启）；真正的移动端 WebKit 触摸滚动仍需真机确认。
3. WebKit 个别页面存在 MathJax blob 访问告警，已归类为非阻塞告警，功能断言仍通过。
4. 目录 iframe（约 1.34 MB）仍随页面加载：六千多篇静态 HTML 内联 iframe，无法仅靠共用文件改为按需加载。
5. 15 MB 中文索引首次搜索仍需下载（已按需加载）；慢速移动网络体验待真机评估。
6. 桌面 1280px 首页 `comfishtable` 单元格存在既有裁切，本轮按“不重新设计桌面端”原则仅记录为告警，未修改。
