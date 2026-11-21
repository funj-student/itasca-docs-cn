# 桌面目录视觉故障基准（修改前）

目标页：`doc/common/docproject/source/manual/coupling/projects/tutorials/tutorials.html`
环境：Playwright 1.65.1，Chromium 159.0.8154.6 / WebKit 27.2，1270/1440/1664/1920px（本地 `/itasca-docs-cn/` 子路径）。
截图：`_toc_artifacts/before_chromium_1280.png` 等 8 张；原始指标：`_toc_artifacts/before_metrics.json`。

## 1280px Chromium 实测基线

- 按钮：43×78，白色空间 `normal`，图标 `(359,588)`、文字 `(366,616)` 且文字高 40px（两行竖排）。
- iframe 内：`.jstree-ocl.x=0`，一级 anchor `x=24`，`scrollX=0`，`docScrollWidth=350`，iframe 宽 350。
- 颜色：普通 anchor `rgb(119,119,136)` 对侧栏底 `rgb(15,33,67)`，对比度 3.62:1；选中项同色文字压在 `rgb(137,160,152)` 背景上，对比度 1.58:1。
- 占位页：`#mainbody` 高 720px，`min-height:640px`，底部导航 `y=784`，文档高 921px。

## 新增断言的负向验证

回退修复后运行 `tests/desktop_visual_check.mjs`，1280 目标页产生 9 条失败（按钮横向排列、文字折行、侧栏间距、目录左缘裁切、普通/选中对比度、占位页高度与底部导航、收起后按钮），退出码 1。说明新断言能捕获用户截图中的实际故障。
