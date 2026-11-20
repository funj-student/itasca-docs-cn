<div align="center">

# Itasca 7.0 手册 · 中文校订版

**免费 · 无需登录 · 支持中文与中英混合全文检索**

[![Deploy to GitHub Pages](https://github.com/funj-student/itasca-docs-cn/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/funj-student/itasca-docs-cn/actions/workflows/deploy-pages.yml)
[![术语与警示校验](https://github.com/funj-student/itasca-docs-cn/actions/workflows/term-check.yml/badge.svg)](https://github.com/funj-student/itasca-docs-cn/actions/workflows/term-check.yml)
![语言](https://img.shields.io/badge/语言-简体中文-blue)
![覆盖](https://img.shields.io/badge/覆盖-FLAC3D%20%2F%203DEC%20%2F%20PFC-orange)

**[在线阅读](https://funj-student.github.io/itasca-docs-cn/)** · 
**[完整目录](doc/contents.html)** · 
**[全文检索](doc/search.html)** · 
**[术语速查](terms.html)** · 
**[模块词库](glossary.html)** · 
**[警示汇总](warnings.html)**

</div>

---

## 项目简介

这是一份面向中文使用者的 **Itasca 7.0 文档翻译整理站**，覆盖 FLAC3D、3DEC、PFC 等分册。站点保留原版手册的章节结构与交互方式，在此基础上补充中文检索、术语对照与校订说明。

> **重要**：本项目是民间翻译整理成果，不是 Itasca Consulting Group 官方网站，也未获官方授权。实际工程应用请以原版英文手册为准。

## 亮点

| 功能 | 说明 |
| --- | --- |
| 全文检索 | 中文、英文及中英混合关键词；支持排除词、来源、类型与标题筛选 |
| 术语体系 | [核心术语对照](terms.html) 125 条 + [模块词库](glossary.html) 306 条，按 5 大模块拆分 |
| 警示层级 | 与官方英文版逐页对齐；[警示汇总页](warnings.html) 汇总 94 条风险提示 |
| 移动端 | 竖屏与横屏适配，目录可开合、可拖动 |
| 质量门禁 | CI 自动检查术语一致性、警示层级与页面部署 |

## 快速开始

### 在线使用

直接打开 <https://funj-student.github.io/itasca-docs-cn/>，无需安装任何软件。

### 本地查看

```powershell
git clone https://github.com/funj-student/itasca-docs-cn.git
cd itasca-docs-cn
```

然后用浏览器打开 `index.html`。请保留 `doc` 文件夹的完整结构，否则页面之间的链接、图片和附件会失效。

由于中文搜索索引约 15 MB，首次检索需要等待索引加载完成；后续检索会使用浏览器缓存。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `index.html` | 站点首页：分册导航与搜索入口 |
| `doc/` | 完整手册（6,576 个 HTML 页面及配套图片、脚本、索引） |
| `doc/contents.html` | 完整目录 |
| `doc/search.html` | 全文检索页；中文索引为 `doc/_static/zh-search-data.js`，按需加载 |
| `terms.html` | 核心术语对照（125 条） |
| `glossary.html` | 模块术语词库（306 条，5 个分区，带筛选） |
| `warnings.html` | 警示与适用边界汇总（94 条） |
| `about.html` | 校订范围、验证结果与使用边界 |
| `disclaimer.html` | 网页版版权与免责声明 |
| `术语词库.md` | 模块词库数据源；修改后运行 `python scripts/generate_glossary.py` 重新生成 |
| `核心术语对照.md` | 核心术语数据源，全站术语一致性的基准 |
| `scripts/check_terms.py` | 术语与警示层级自动校验脚本 |
| `scripts/check_links.py` | 校验已发布页面的本地链接、页内与跨页锚点，以及 HTML 和 CSS 引用的静态资源 |

## 检索用法

- 中文、英文及中英混合关键词均可搜索，多个关键词用空格分隔。
- 中文／混合查询中，排除词前加减号，例如 `摩擦角 -模型`。
- 可使用来源、类型与标题筛选。
- 示例：
  - `安全系数`
  - `刚性簇`
  - `quiet boundary`
  - `水力压裂 flowplane.vertex`
  - `摩擦角 -模型`

## 质量保障

在仓库根目录使用 Python 3.11 可运行与 CI 相同的检查。回归测试会在临时目录重新生成模块词库，并核对提交的页面。

```sh
python -m pip install -r scripts/requirements-checks.txt
python -B -m unittest discover -s tests -v
python scripts/check_terms.py
python scripts/check_links.py --known-missing scripts/known-missing-images.json
```

PFC 7.0 的两个 Python 示例使用了缺少源图的通配符路径。CI 会逐条报告这两处已知缺图，并按页面、原始 URL 和出现次数精确匹配。新增缺失、坏锚点或已过期的例外都会使检查失败。运行 `python scripts/check_links.py` 可查看严格检查结果。

- 全量扫描 93,911 个正文及标题单元，记录 1,572 个修订条目，重新渲染 432 页。
- 6,573 个 HTML 页面通过结构、公式、锚点及引用身份核验，错误数 0。
- 术语 CI 检查：核心术语 125 条与官方术语表全部覆盖、禁用译字变体、警示块与官网逐页一致。
- 警示层级按官方英文版逐页比对，mismatch = 0。
- 全书逐页的人工专业终审尚未进行，详见 [校订说明](about.html)。

## 部署

仓库根目录包含 `.nojekyll`，确保以下划线开头的 `_static`、`_images` 目录能够正常发布。

提交到 `main` 的 Pull Request 会运行质量检查。推送到 `main` 或手动触发 Pages 工作流时，只有同一提交通过全部检查，才会上传仓库根目录并发布到现有站点。

如需改为分支部署，在仓库 Settings → Pages → Build and deployment 中，将 Source 选为 **Deploy from a branch**，分支选 `main`、目录选 `/ (root)`。

## 参与校订

欢迎提交 Issue 或 Pull Request。请尽量提供：

1. 页面地址或文件路径；
2. 原文；
3. 当前译文；
4. 建议译法与依据（教材、规范或上下文）。

## 版权与免责声明

本项目为民间翻译整理成果，非 Itasca Consulting Group 官方网站或授权产品。FLAC3D、3DEC、PFC 及相关文档、图片和标识的版权归原出版方所有。本站仅供中文学习者免费查询与学习使用，不对软件使用结果承担责任。

详见 [网页版免责声明](disclaimer.html) 或 `DISCLAIMER.md`。
