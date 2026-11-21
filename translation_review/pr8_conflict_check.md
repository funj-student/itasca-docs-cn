# PR #8 冲突检查记录

日期：2026-11-21

## 结论

PR #8 已经合并到 main，本轮没有修改、重新合并或回滚 PR #8。PR #6 只同步了合并后的最新 main，并保留自身的搜索页 `noindex,follow` 改动。

## 事实

- PR #8：`fix/mobile-responsive-v2`
- PR #8 head：`f8d05459a8196ce88dbf51ad67f1f1713758c387`
- PR #8 合并提交：`bd246d3c1f39a5c7b070c31b9de2d228d767bea8`
- 当前 main 基线（PR #7 合并后）：`d28ea7fec82f2131de4df36b177168d85bbbae49`

## 与 PR #6 的重叠文件

| 文件 | PR #6 | PR #8 | 处理结果 |
| --- | --- | --- | --- |
| `doc/search.html` | 新增 `<meta name="robots" content="noindex,follow"/>`，并从 sitemap 移除搜索页 | 修改了搜索页移动/界面相关结构 | 将最新 main 合并入 PR #6 时 Git 自动合并成功；noindex 仍在文件中。两处搜索页改动共存，建议人工复核最终页面。 |
| `doc/_static/zh-search.js` | 未修改；新增审计脚本调用其真实 API | 修改了该文件 | 无文件级写入冲突；但 PR #6 的真实搜索审计依赖该文件，需在 PR #6 合并后重跑搜索审计。 |
| 其他移动端文件 | 未修改 | 修改/新增 | PR #6 不触碰，保持原样。 |

## 自动化验证

- `git merge origin/main` 到 PR #6 分支成功，无未解决冲突。
- 合并后 `doc/search.html` 仍包含 `noindex,follow`。
- 本轮未修改 `icgscripts.js`、`itasca.css` 或触摸/iframe 逻辑。

## 仍需人工确认

- PR #8 对 `doc/search.html` 的界面改动与 PR #6 的 `noindex` 元数据是否共同满足产品预期。
- PR #8 对 `zh-search.js` 的改动是否影响后续真实搜索审计结果；PR #6 合并后应重新运行 `scripts/site_quality_audit.py`。
