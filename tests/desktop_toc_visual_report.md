# 桌面目录视觉缺陷紧急修复报告

分支：`fix/desktop-toc-visual`　基线：`origin/main` @ `55a299f4`（已含 PR #8 与 PR #10）
目标页：`doc/common/docproject/source/manual/coupling/projects/tutorials/tutorials.html`（PFC-FLAC3D 耦合教程）

## 1. 复现到的三个实际缺陷

| 问题 | 修改前实测（Chromium 1280） | 根因 |
| --- | --- | --- |
| A 左侧目录 | `.jstree-ocl.x=0`，一级 anchor `x=24`；普通文字对比度 3.62:1，选中项文字/背景对比度 **1.58:1** | iframe 内 jsTree 容器左缘无内边距；选中项沿用普通灰字，压在浅绿背景上 |
| B 按钮竖排 | 按钮 43×78；图标 `(x=359,y=588)`、文字 `(x=366,y=616)`，文字高 40px（两行） | 基础 CSS `div#navbutton{width:1.4em}` 仍按单字符按钮设计，但脚本注入了图标 + “目录”文字 |
| C 占位页空白 | `#mainbody` 高 720px（`min-height:640px`），底部导航 `y=784`，文档高 921px | 基础 `#mainbody{min-height:40em}` 对只有标题的目录占位页同样生效 |

修改前截图：`_toc_artifacts/before_chromium_1280.png`（另有 1440/1664/1920 与 WebKit）。

## 2. 修改内容（最小范围）

- `doc/_static/icgscripts.js`：在 `prepareTocFrame()` 的 `inject()` 内，**仅当 `!isMobileNav()`** 时向 iframe 注入 `wb-toc-desktop-style`：
  - `#jstree` 左右各 12px 内边距 → 箭头、图标、文字不再贴 iframe 左缘；
  - 普通 anchor 颜色 `#c9d4de`、hover `#fff`；选中项深蓝字 `#0b1b33` + 浅绿底 `#b9d4c7`；
  - 切换回移动端时移除该样式，移动端注入样式保持原样。
- `doc/_static/itasca.css`：仅追加 `min-width:960px` 规则：
  - `#navbutton` 改为 `inline-flex`、`white-space:nowrap`、`width:auto`，图标与文字同行；按钮左右边距与侧栏保持 0.5em 间距；
  - 仅对“单一 section 仅含 h1 且无 p/ul/ol/table/pre/figure/highlight”的占位页设 `min-height:0`，底部导航自然上移。
- `tests/desktop_visual_check.mjs`：新增针对上述视觉故障的硬断言测试。
- `.github/workflows/desktop-browser-check.yml`：新增视觉断言步骤。
- 未修改技术译文、公式、命令、搜索算法；未改移动端媒体查询；未回滚 PR #8；未合并 PR #9；未覆盖 PR #6。

## 3. 三个问题的修复结果（Chromium 1280）

| 指标 | 修改前 | 修改后 |
| --- | --- | --- |
| `.jstree-ocl.x` | 0 | **12** |
| 一级 anchor `x` | 24 | **36** |
| 普通目录文字对比度 | 3.62:1 | **10.58:1** |
| 选中项对比度 | 1.58:1 | **10.92:1** |
| 展开后第一个可见 anchor `x` / `scrollX` | — | **36 / 0** |
| 目录文档宽 / iframe 宽 | 350 / 350 | 350 / 350（无水平滚动） |
| 按钮尺寸 | 43×78（竖排） | **65×26（横向）** |
| 占位页 `#mainbody` 高 | 720 | **128** |
| 底部导航 `y` | 784 | **192** |

修改后截图：`_toc_artifacts/after_chromium_1280.png`；视觉断言截图：`_toc_artifacts/visual_final2_*_open.png` / `*_closed.png`（1280/1440/1664/1920 × Chromium/WebKit × 2 页）。

视觉检查确认：一级节点与深层节点缩进正常，展开箭头与文字完整，长名称换行，选中项深字浅底清晰；按钮显示为单行 `☰ 目录`，打开/关闭后均正常且不遮挡标题；占位页标题下方不再有大片空白，上一页/下一页与反馈条紧随标题出现。

## 4. 桌面浏览器测试

Playwright 1.65.1；Chromium 159.0.8154.6、WebKit 27.2；视口 1280/1440/1664/1920；目标深层目录页 + 首页。

新增视觉断言覆盖：按钮图标与文字同排、文字不折行、按钮宽度自适应、与侧栏间距、不遮挡标题、展开/收起后仍正常；iframe 内一级节点左缘不被裁切、展开后图标文字仍可见、选中项不造成横向滚动、普通与选中文字对比度 ≥4.5:1；占位页高度与底部导航可达性。

**结果：264 条断言全部通过，0 失败**（负向验证：回退修复后同脚本在 1280 目标页产生 9 条失败，退出码 1，证明断言确实能捕获截图中的问题）。
原有桌面测试同矩阵：**234 条断言全部通过，0 失败**。

## 5. 移动端零回归

- 截图：320/375/390/430/768/959 × 首页/搜索/目录/目标页 = 24 组，`before_mobile` 与 `after_mobile` **24/24 逐像素完全一致**。
- 功能：现有 `tests/mobile_browser_check.mjs` 六宽度 × 13 页，**632 条断言全部通过，0 失败**。
- 桌面专用 iframe 样式在 `isMobileNav()` 为真时被移除，移动端抽屉、触摸滚动、遮罩与焦点逻辑未改动。

## 6. Python 与 CI

- 62 项 unittest、`check_terms.py`、`check_links.py` 均通过（2 个已知缺失文件）。
- GitHub Actions：链接见 PR 页面；工作流 `Desktop browser smoke check` 已包含新增视觉断言。

## 7. 限制

1. 未在 Android/iOS 真机或微信内置浏览器验证；移动端结论基于 Chromium 模拟与像素对比。
2. WebKit 偶发 MathJax blob 访问告警，已按既有规则归为非阻塞告警；不影响布局与交互断言。
3. 占位页底部以下区域仍显示站点原始棕色 body 背景（既有设计），但空白主体已消除。
