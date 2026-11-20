# Itasca 7.0 中文手册移动端适配测试报告

分支：`fix/mobile-responsive-v2`　基线：`origin/main` @ `fe97a02b`（已含合并的 PR #5）

## 一、根因分析

1. **目录多套滚动机制互相冲突**：`icgscripts.js` 同时在侧栏绑定 `touchmove`/`preventDefault` 模拟滚动（`enableTouchScroll`）、在 iframe 内用 `translateY()` 位移目录（`attachIframeTouch`）、`sizeMobileNav()` 又向 iframe 注入 `overflow:hidden` 并强制固定高度，叠加侧栏 `overflow-y:auto` 与 iframe 自身滚动。四套机制争抢同一手势，导致卡顿、跳变和滚不到底。
2. **断点与设备判断不一致**：CSS 用 `max-width:720px`，JS 用 `innerWidth<=720 || maxTouchPoints>0 || UA`；触屏笔记本/平板会让脚本进入移动模式而布局仍是桌面端。`window.onresize` 在移动模式下无条件 `closeNav()`，地址栏收放或键盘弹出就会关闭目录。
3. **遮罩层级错误**（浏览器测试发现）：新增遮罩 `z-index:250` 高于抽屉 `z-index:200`，遮罩覆盖整个抽屉，导致目录条目无法点击/展开。
4. **iframe 高度未确定**（浏览器测试发现）：移动端 `height:auto` 使 iframe 随内容长高并被 `overflow:hidden` 的抽屉裁切，物理上无法滚到底部。
5. **正文表格截断**：`table.comfishtable` 固定 `550px`、单元格 `white-space:nowrap; overflow:hidden; width:50%`，手机上直接切断命令名；`table{display:block}` 也破坏了表格默认布局语义。
6. **搜索页固定宽度**：搜索框 `18em`、标题筛选 `25em`、弹窗 `38em`，在窄屏溢出或挤压。

## 二、实际修改文件

| 文件 | 修改内容 |
| --- | --- |
| `doc/_static/icgscripts.js` | 重写导航：统一断点、移除冲突滚动逻辑、注入语义化按钮/遮罩/关闭按钮、背景滚动锁定与位置恢复；新增表格滚动容器包裹与超长标记处理 |
| `doc/_static/itasca.css` | 统一 `959px` 断点；抽屉/iframe 单一滚动容器；表格分类适配、代码/公式/图片/警告框自适应；窄桌面过渡修正 |
| `doc/_static/icg_shutsidebar.css` | 保留原样（内容已由共用 CSS 接管，不再依赖该文件的 720px 判断） |
| `doc/search.html` | 搜索表单、筛选控件、弹窗和结果列表的自适应样式与语义标签 |
| `doc/_static/zh-search.js` | 移除 `25em` 内联宽度；移动端首批结果 50 条（桌面 100 条）；筛选框语义属性；检索算法未改 |
| `tests/mobile_browser_check.mjs` | 新增 Playwright 多宽度、多页面、双引擎验收脚本 |

### 删除的冲突逻辑

- `enableTouchScroll()` / `attachIframeTouch()` / `navTranslate` / `translateY()` 手动位移
- 侧栏与 iframe 内的 `touchmove` + `preventDefault()` 模拟滚动
- `sizeMobileNav()` 对 iframe 文档的 `overflow:hidden` 注入与 80vh 高度计算
- `window.onresize` / `orientationchange` 无条件 `closeNav()`
- 基于 `maxTouchPoints` 与 UA 的移动判断
- `table{display:block}` 与 `div.comfishtable{overflow-x:auto}`（对真正的 `table.comfishtable` 无效）

## 三、新的移动端导航实现

- 断点：`matchMedia('(max-width: 959px)')`，CSS 同为 `@media (max-width: 959px)`。
- 唯一滚动容器：目录 iframe 的文档视口；抽屉 `overflow:hidden`、iframe `flex:1 1 0; height:0` 获得确定高度，使用浏览器原生滚动。
- 打开：≥48×48 CSS px 的「☰ 目录」按钮，含 `role="button"`、`tabindex`、`aria-controls`、`aria-label`、`aria-expanded`；抽屉内另有「✕ 关闭」按钮；遮罩 `z-index:250`、抽屉 `400`、按钮 `500`。
- 关闭：按钮/关闭按钮/遮罩点击/Escape；锁定正文滚动（`position:fixed; top:-scrollY`）并在关闭后恢复阅读位置。
- 仅在 `matchMedia` 触发布局模式切换时重置目录；地址栏、键盘、轻微 resize 不再关闭目录。
- 安全区：`bottom/right: calc(... + env(safe-area-inset-*))`。
- 共享脚本注入 UI，不逐页修改六千多篇 HTML。

## 四、正文与搜索适配效果

- 命令/FISH 索引表改为自动列宽 + 完整文字；所有技术表格包在 `.table-scroll` 内局部横向滚动并给出「左右滑动」提示；术语表保持三列对应关系。
- 代码块保留缩进与原换行并独立横向滚动；MathJax 公式使用局部滚动容器，不缩小字体、不改公式内容；图片 `max-width:100%`。
- 命令关键字与 FISH 名称 `white-space:nowrap` 且 `max-width:100%; overflow-x:auto`，不会被拆字符也不会截断。
- 搜索框/按钮/筛选/弹窗在 959px 以下自适应；中英文混合检索、来源、类型、标题筛选与排除词逻辑未改；移动端首批只渲染 50 条结果以减少 DOM。

## 五、浏览器测试结果

环境：Playwright 1.65.1，Chromium 1255（移动视口 + `hasTouch`）、WebKit 27.2；本地 HTTP 服务。
宽度：320 / 375 / 390 / 430 / 768 / 960 / 1280 / 1920；测试含手机横屏（`max-height:500px`）。
页面：首页、搜索页、完整目录、FLAC3D 命令页、FISH 函数页、公式页、长代码页、技术数据表格页、3DEC 页、PFC 页、术语表页。

| 项目 | 结果 |
| --- | --- |
| 整页横向溢出（Chromium） | 通过 |
| 整页横向溢出（WebKit） | 通过（曾发现命令 token 溢出，已修复） |
| 目录打开/关闭、遮罩、Escape | 通过（双引擎） |
| 目录连续滚动到底部 | 通过：展开 8 个节点后 `scrollY` 达到 `scrollHeight-innerHeight` |
| 多级目录展开与链接跳转 | 通过：每次连续展开 8 个节点，点击条目完成导航 |
| 关闭后阅读位置恢复 | 通过：滚动 600px 后开关目录，`scrollY` 仍为 600 |
| 移动端目录按钮尺寸 | 79×48 CSS px（≥44） |
| 搜索与筛选 | 通过：中文词「固结」得到结果，移动端 50 条 / 桌面 100 条，标题筛选框宽度 226–233px（320/390px 视口内） |
| 桌面 1280 / 1920 | 无溢出，左侧目录、正文宽度与排版保持 |
| Python 回归 | 52 项 unittest 通过；`check_terms.py` 通过；`check_links.py` 通过（2 个已知缺失文件） |

### 性能实测（localhost，390px）

| 指标 | 数值 |
| --- | --- |
| 首页 DOMContentLoaded | ~0.96 s（HTML 325 KB + 目录 iframe 1.34 MB） |
| 目录首次打开 | ~0.75 s |
| 搜索页 DOMContentLoaded | ~0.05 s |
| 首次中文搜索「固结」 | ~1.12 s（含 14.66 MB 中文索引，localhost） |

中文索引已是按需加载（仅在首次中文查询时请求 `zh-search-data.js`）；目录 iframe 因六千多篇静态 HTML 内联结构仍会随页面加载，无法仅靠共用文件改为按需加载。移动端首批结果由 100 条降至 50 条。

## 六、截图

截图保存在测试产物目录（未加入发布目录）：

- `final2_chromium_320_closed.png` / `final2_chromium_390_open.png`：手机竖屏与目录打开
- `final2_chromium_1280_closed.png`：桌面端对照
- `3_chromium_320_search.png`：手机搜索页
- `2_chromium_320_closed.png`：阶段二修复后的命令索引表

## 七、尚未解决的问题与风险

1. **真机覆盖不足**：已完成 Chromium 移动视口与 WebKit 桌面版模拟；Android 真机、iOS 真机、微信内置浏览器未实测，不能等同通过。
2. **WebKit blob 访问告警**：部分含 MathJax 的技术页在 WebKit 中出现 `Cannot load blob: ... due to access control checks`，功能检查仍通过；属于测试环境/WebKit 字体加载告警，待真机确认。
3. **目录 iframe 仍随页面加载**（1.34 MB）：要真正按需加载需改动全部静态 HTML 或引入 Service Worker，超出本次共用文件修复范围。
4. **15 MB 中文索引**：首次中文搜索在慢速移动网络上的等待时间仍可能较长；已保留「正在载入搜索索引…」反馈，未重写搜索引擎。
5. **浮动目录按钮**：固定在右下角，翻页与底部链接处已留 4.5em 安全间距；滚动过程中仍会覆盖其下方文字，这是悬浮按钮的固有取舍。
