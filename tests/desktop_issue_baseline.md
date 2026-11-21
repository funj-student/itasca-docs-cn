# 桌面端问题定位与基准记录（修改前）

分支：`fix/desktop-navigation-only`，基线：`origin/main` @ `d28ea7fe`（已含 PR #8 移动端适配与 PR #7 译文修订）。

## 测试环境

- 本地服务器映射 GitHub Pages 子路径：`http://127.0.0.1:8770/itasca-docs-cn/`
- Playwright 1.65.1 + Chromium 159.0.8154.6
- 桌面视口：960 / 1024 / 1280 / 1440 / 1920（高 900）
- 页面：首页、完整目录、搜索页、FLAC3D 命令页、FISH 页、3DEC 页、材料属性表页、PFC 页
- 修改前截图：`_desktop_artifacts/before_desktop_chromium_*`（30 张）
- 手机基准截图：`_desktop_artifacts/before_mobile_chromium_*`（24 张，320/375/390/430/768/959）

## 实测问题与根因

1. **侧栏与 iframe 宽度不一致**：`.sidenav` 固定 350px，`iframe#toctobj2` 基础宽度 390px；35 次测量全部不一致。iframe 右侧 40px 被 `overflow-x:hidden` 的侧栏裁掉。修复方向：桌面端让 iframe 宽度继承侧栏实际宽度。
2. **目录条目在侧栏右缘被截断**：5 个宽度的首页均检出 `.jstree-anchor` 超出可见侧栏宽度。
3. **正文左右内边距不对称**：`#mainbody` 基础 `padding: 1em 2em 4em 4em`（左 64px / 右 32px），35 次测量全部不对称，文字块在容器内偏右。
4. **大屏阅读区偏窄**：1440/1920 下 `#mainbody` 总宽仅 656px（内容 560px），14 次测量低于 720px 合理下限；首页命令表格被 `table.comfishtable` 固定 550px + `white-space:nowrap; overflow:hidden` 截断，1280/1440/1920 均检出。
5. **窄桌面（960–1100px）侧栏占比过大**：350px 侧栏在 960px 视口占 36%，正文被挤压；材料属性页存在 MathJax SVG 公式宽 637px 造成的 15px 整页横向溢出（960/1024）。
6. **目录滚动断言在基线未达底**：滚轮单次 4000px 只滚到约 770/828，已把测试改为最多 3 次滚轮后再判定，避免测试步长不足导致的假阴性。

## 基准断言结果

`tests/desktop_browser_check.mjs` 以 `MODE=baseline` 运行：348 条断言，249 通过，99 失败（仅记录，不设退出码）。失败分类：
- 35 × iframe 宽度与侧栏不一致
- 35 × 正文内边距不对称
- 14 × 大屏阅读区宽度不足
- 5 × 目录条目被截断
- 5 × 目录滚动未达底（测试步长问题，见上）
- 3 × 表格单元格被裁切
- 2 × 窄桌面整页溢出

上述基准用于修复后逐项复测；修复提交见后续 commit。
