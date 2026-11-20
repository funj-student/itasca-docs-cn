# 站点搜索与 SEO 审计报告

生成时间：2026-11-20T15:41:11.372128+00:00

## 1. 查询验证摘要

| 指标 | 数量 |
| --- | ---: |
| 实际 zh-search.js 查询 | 10 |
| 有结果 | 9 |
| 前五名结果相关 | 10 |
| 预期目标页进入前五 | 3 |
| 预期目标页未进前五 | 4 |
| 零匹配测试正确 | 1 |
| 英文查询未验证 | 3 |

英文查询依赖浏览器端 Sphinx 搜索索引，本审计环境无法复现，因此不把英文查询计为通过。

## 2. 查询明细

| ID | 查询 | 引擎 | 有结果 | 相关 | 目标前五 |
| --- | --- | --- | --- | --- | --- |
| cn-friction | 摩擦角 | zh-search.js actual | 是 | 是 | 未验证 |
| cn-safety | 安全系数 | zh-search.js actual | 是 | 是 | 否 |
| cn-stress | 初始地应力 | zh-search.js actual | 是 | 是 | 否 |
| cn-rayleigh | Rayleigh 阻尼 | zh-search.js actual | 是 | 是 | 是 |
| cn-clump | 刚性簇 | zh-search.js actual | 是 | 是 | 是 |
| cn-bond | 颗粒黏结 | zh-search.js actual | 是 | 是 | 否 |
| cn-flow | 水力压裂 | zh-search.js actual | 是 | 是 | 否 |
| cn-mixed-zone | zone create 命令 | zh-search.js actual | 是 | 是 | 是 |
| cn-exclude | 摩擦角 -模型 | zh-search.js actual | 是 | 是 | 未验证 |
| cn-zero | 绝对不存在的术语zzz | zh-search.js actual | 否 | 是 | 未验证 |
| en-zone-create | zone create | English Sphinx index not available in audit environment | 未验证 | 未验证 | 未验证 |
| en-model-solve | model solve | English Sphinx index not available in audit environment | 未验证 | 未验证 | 未验证 |
| en-gp-vel | gp.vel | English Sphinx index not available in audit environment | 未验证 | 未验证 | 未验证 |

## 3. 未索引页面判断

- `3dec/docproject/source/options/dynamic/3dec/docproject/source/options/dynamic/dynamic_calculations.html`：原版路径错误生成的405字节跳转桩页，正文明确要求返回动力计算页面；路径重复嵌套，不应作为正文收录，但不删除文件。
- `alltree.html`：未分类
- `common/docproject/utilities/icgsphinxhelp/icgsphinxhelp.html`：未分类
- `contents.html`：未分类
- `docproject/source/manual/utilities/feedbackform.html`：未分类
- `doxygen/html/class_variant_1_1_user_type_base.html`：419字节 Doxygen 缺失类型跳转桩页，正文提示类型页在原版缺失并指向 Variant 类型页；不应收录为正文，但不删除文件。
- `genindex.html`：未分类
- `navtree.html`：未分类
- `search.html`：未分类

## 4. SEO

- HTML 6577，搜索索引 6568，sitemap 6577 条，失效 doc 条目 0。
- 搜索页保持 `noindex,follow`，已从 sitemap 移除；目录页有 canonical 与 description。
