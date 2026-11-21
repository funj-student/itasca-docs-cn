# 桌面端恢复 Itasca 官方原版体验报告

分支：`restore/official-desktop-experience`　基线：`origin/main` @ `00cfce86`（含 PR #8/#10/#12）
官方参考：`https://docs.itascacg.com/flac3d700/.../coupling/projects/tutorials/tutorials.html`
中文页面：`.../itasca-docs-cn/doc/.../coupling/projects/tutorials/tutorials.html`

## 1. 官方原版与恢复前电脑端的差异（Chromium 1280 实测）

| 项目 | 官方原版 | 恢复前（PR #12 后） |
| --- | --- | --- |
| 侧栏宽度 | 350px | 350px（一致） |
| 目录 iframe 宽度 | **390px** | 350px（被改成与侧栏同宽） |
| 正文总宽 / 内边距 | **656px / 64px 左、32px 右** | 624px / 32px、32px |
| 占位页最小高度 | **640px** | 0（被 `:has()` 规则取消） |
| 目录切换按钮 | **单字符 `⇄`，43×40，x=353** | `☰ 目录`，65×26，flex |
| 目录文字颜色 | **rgb(157,163,168)** | rgb(201,212,222) |
| 选中项背景 | **rgb(55,67,92)** | rgb(185,212,199) |
| 目录一级缩进 / 箭头 | **anchor x=32 / ocl x=8** | x=36 / x=12 |
| 目录文档宽度 | **480px（官方 navtree `width:30em`）** | 350px |
| 桌面注入样式 | 无 | `wb-toc-native-scroll` + `wb-toc-desktop-style` |
| 底部导航 y / 文档高 | 784 / 918 | 192 / 900 |

## 2. 实际恢复的官方行为

- 侧栏 350px、目录 iframe 390px（官方原版尺寸与裁切方式）。
- 正文 `max-width:35em`、`padding:1em 2em 4em 4em`、`min-height:40em`、`margin:0 auto`。
- 官方目录树：字体 `.85em`、行高、`#jstree li{width:250px}`、anchor `margin-left:24px`、箭头位置、`⇄` 展开/折叠方式。
- 官方配色：普通文字 `#9da3a8`、选中背景 `#37435c`（恢复在 `doc/navtree.html` 基础样式中）。
- 官方 `⇄` 按钮：单字符、`width:1.4em`、定点 `left:.15em`、展开时 `margin-left:350px`、收起时 0；保留 `aria-label="展开目录/收起目录"` 与键盘可操作性。
- 官方占位页布局：保留 40em 最小高度与底部导航位置，不再用 `:has()` 消除空白。
- 目录独立滚动、多级展开、当前节点自动定位行为与官方一致。

## 3. 删除的自定义桌面规则

- `itasca.css` 末尾 PR #10/#12 的全部桌面补丁：iframe `width:100%`、正文 `2em/2em` 与 `42em`、`comfishtable` 全宽换行、MathJax 桌面滚动、`z-index:210`、960–1100px 侧栏 300px、按钮 `inline-flex/nowrap`、占位页 `:has()` 最小高度。
- `icgscripts.js`：`wb-toc-desktop-style` 的创建与注入；桌面端不再注入 `wb-toc-native-scroll`（该样式仅在 `isMobileNav()` 为真时创建，切回桌面会移除）。
- 桌面按钮不再写入 `☰ 目录` DOM；桌面固定渲染官方 `⇄`，移动端保留图标 + 文字，跨断点切换时由 `renderNavButtonContent()` 更新。

仅保留两处明确标注的兼容修复：1）`960–1100px` 窄桌面下，官方固定 550px 命令表、长 token、嵌套 toctree 与 MathJax 会超出 610px 阅读列，允许局部换行/滚动；2）`navtree.html` 把 `overflow-x:hidden` 改为 `overflow-x:clip`，保持官方 480px 文档宽度与可见布局，但阻止深层节点自动定位时把整棵树水平滚动 80px。1280px 及以上其余布局完全按官方。

## 4. 修改文件

| 文件 | 说明 |
| --- | --- |
| `doc/_static/itasca.css` | 删除自定义桌面补丁；仅保留 960–1100px 兼容块 |
| `doc/_static/icgscripts.js` | 桌面 `⇄` / 移动端图标文字切换；iframe 样式按断点注入/移除；清理桌面注入 |
| `doc/navtree.html` | 恢复官方文字色 `#9da3a8` 与选中背景 `#37435c`（移动端由注入样式覆盖回现值） |
| `tests/desktop_visual_check.mjs` | 改为官方基线断言（尺寸/配色/缩进/按钮/占位页） |
| `tests/desktop_browser_check.mjs` | 冲突的自定义断言改为官方基准 |
| `tests/official_desktop_baseline.json` | 官方实测基准数据 |
| `tests/desktop_official_restore_report.md` | 本报告 |

未修改译文、术语、技术参数、公式、搜索算法；未改移动端媒体查询内部规则；未合并 PR #9/#11。

## 5. 官方与中文网站并排截图

- 官方：`_official_artifacts/cmp_official_{chromium,webkit}_{960,1280,1440,1664,1920}_{open,closed}.png`
- 中文恢复后：`_official_artifacts/cmp_restored_{chromium,webkit}_{960,1280,1440,1664,1920}_{open,closed}.png`
- 1280px 对比：侧栏宽度、目录字号/缩进/颜色、`⇄` 按钮位置、正文起点、底部导航位置均一致；中文文本更长导致换行更多，属于文字长度差异。

## 6. 原版 `⇄` 按钮

已恢复。桌面显示单字符 `⇄`（43×40，展开 x=353、收起 x=3），不再显示 `☰ 目录`；`aria-label` 仍为“收起目录/展开目录”。移动端保留 `☰ 目录/☰ 关闭` 按钮。

## 7. 目录滚动与展开

双引擎实测：多级节点连续展开 ≥3 层；目录可滚动到底再回到顶部；展开/滚动后 `scrollX=0`、文档宽保持 480px，无水平位移；`⇄` 收起/展开正常，正文宽度在 656/930 之间切换，阅读位置保持。

## 8. 手机端零回归

- 320/375/390/430/768/959 × 首页/搜索/目录/目标页 = 24 组截图：**24/24 逐像素完全一致（差异 0）**。
- 现有移动端功能测试 6 宽度 × 13 页：**632 条断言全部通过，0 失败**。
- 移动端注入样式增加 `color:#777788` 与 `selected background:#89a098` 覆盖，抵消 navtree 基础样式恢复官方配色带来的影响。

## 9. 测试结果

- 官方基线视觉测试（Chromium + WebKit，960/1280/1440/1664/1920，目标页 + 首页）：**Chromium 300 条通过、WebKit 300 通过（1 条非阻塞告警），0 失败**。
- 桌面功能测试：Chromium 530 条（526 通过 / 4 告警 / 0 失败），WebKit 532 条（528 通过 / 4 告警 / 0 失败）。告警为官方 comfishtable 固定宽度裁切与非阻塞浏览器告警。
- 原有测试中与官方冲突的自定义断言已替换为官方基准，而非删除。

## 10. CI 与 PR

GitHub Actions 链接与 PR 地址见 PR 页面（`Desktop browser smoke check` 含官方基线断言）。

## 11. 仍存在的差异与原因

1. 中文文本通常比英文长，目录与正文换行更多；未要求逐像素一致。
2. 中文页底部版权/反馈文字与官方英文不同，占位页文档高 921 vs 官方 918（3px）。
3. 两处明确标注的兼容处理：960–1100px 局部换行；navtree `overflow-x:clip` 防止深层节点自动定位产生水平滚动（不改变官方 480px 文档宽度与可见排版）。
4. 未做 Android/iOS/微信真机；移动端结论基于 Chromium 模拟与像素对比。
5. 官方 WebKit 960px 采集时出现一次 SSL 连接错误，其余 4 个宽度已成功对照；Chromium 5 个宽度全部成功。
