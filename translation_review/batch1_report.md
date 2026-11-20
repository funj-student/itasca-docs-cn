# 第一批翻译质量审校报告

审校日期：2026-11-20

## 1. 范围与依据

- 审校对象：30 篇 FLAC3D 高价值文档。
  - 常用命令参考 10 篇。
  - 边界条件与初始应力 10 篇。
  - 本构模型与力学参数 10 篇。
- 英文依据：Itasca 7.0 官方站点 `https://docs.itascacg.com/flac3d700/` 对应路径。30 篇英文原文抓取状态均为 HTTP 200，原文件保存在仓库外的工作目录，仅将证据摘录写入审校记录。
- 中英对照：先用脚本按数字、命令标识符等标记对齐段落，再对每篇主要正文逐段人工复核。脚本提取英文块 1,708 个、中文块 1,456 个，自动对齐 1,245 对；结构合并导致部分段落无法自动一一对应，未将自动对齐数量等同于实际逐字审校数量。

## 2. 结果概览

| 项目 | 数量 |
| --- | ---: |
| 审校页面 | 30 |
| 有确认问题的页面 | 11 |
| 未发现可确认问题的页面 | 19 |
| 确认问题 | 22 |
| P0 严重技术错误 | 13 |
| P1 明显专业误译 | 5 |
| P2 术语与表达问题 | 4 |
| 已修复 | 22 |
| 待复核 | 0 |
| 误报 | 0 |

结构化记录见 `translation_review/batch1_records.jsonl`。每条记录含页面路径、英文来源 URL、英文摘录、原中文、修订中文、问题类型、严重程度、理由与状态。

## 3. 主要修订类型

### P0：13 项

- 补齐 3 处命令前置条件/模型选项限制。
- 补齐 `zone gridpoint fix` 被整节漏译的关键字块，并恢复 `[gridpointfixblock]` 标记。
- 修正边界应力章节 3 段示例命令错配：恢复 `servo ramp`、FISH 正弦加载、table ramp 三段官方示例。
- 修正 Hoek-Brown 公式 (4) 的变量替换错误。
- 修正 `table-mb` 属性关键字误写为 `table-m`。
- 修正 `zone property-distribution` 语法被错误限定为 `density`。
- 修正 DLL 版本号 `007` 误写为 `006`。
- 修正 `model configure plugins` 漏掉复数 `s`。

### P1：5 项

- 修正 `zone gridpoint free` 页面自指式交叉引用，应为 `zone gridpoint fix`。
- 修正 `fy` 参数含义：应力比而非尺寸。
- 补齐 `zone fluid zone-based-pp on` 自动初始化孔压的说明。
- 补齐 Hoek-Brown 正则化因子 `L_c / ∛(V_z)` 及 `V_z` 定义。
- 补齐 `zone property-distribution` 使用示例。

### P2：4 项

- 修正非法 LaTeX 写法 `\ν`。
- 将流体分析语境中的 `zone.flux` 由“热通量”改为“平均流量”。
- 将 `relaxation` 统一为“松弛开挖”，避免与卸荷混淆。
- 将 `thermomechanical analyses` 改为“热-力耦合分析”。

## 4. 未发现可确认问题的页面

以下页面经逐段复核，未发现可确认的翻译错误：

- `cmd_zone.apply-remove.html`
- `cmd_zone.property.html`
- `cmd_zone.gridpoint.initialize.html`
- `cmd_zone.face.apply.html`
- `cmd_zone.face.apply-remove.html`
- `flac3d/docproject/source/theory/fluid-mechanical/boundary_conditions/boundary_conditions.html`
- `cmd_zone.face.westergaard.html`
- `cmd_zone.face.westergaard-remove.html`
- `options/dynamic/considerations/considerations.html`
- `options/dynamic/formulation/formulation.html`
- `options/dynamic/wizard/wizard.html`
- `theory/interfaces/modelingguidelines.html`
- `cmd_zone.mechanical.html`
- `common/models/mohr/doc/modelmohr.html`
- `common/models/ubiquit/doc/modelubiquit.html`
- `common/models/ssoft/doc/modelssoft.html`
- `common/models/elastic/doc/modelelastic.html`
- `common/models/camclay/doc/modelcamclay.html`
- `fish_zone.model.html`

说明：部分英文原文自身存在编辑批注或明显原版笔误，例如 Mohr 页的疑问批注、Hoek 页 `ψ_c = k × ψ_c`、Cam-Clay 页公式 (46) 的分母写法等；中文忠实照译，未计为翻译错误。

## 5. 测试与验证

已执行：

1. `python -B -m unittest discover -s tests -v`
   - 21 项测试全部通过，其中 12 项为本批新增的翻译回归测试。
2. `python scripts/check_terms.py`
   - 通过；术语表 125 项、模块词库 306 项与网页同步，禁用译法与警示层级检查通过。
3. `python scripts/check_links.py --known-missing scripts/known-missing-images.json`
   - `pages=6584 missing_files=2 missing_anchors=0 known_missing_files=2`
   - 两处缺失文件均为既有白名单中的 PFC Python 示例通配符图片路径，未新增缺失。
4. 中文搜索索引已按本次修订逐条更新，搜索索引回归测试通过。

## 6. 边界与后续

- 本批是“有官方英文原文依据的审校与修订”，不构成全书人工专业终审。
- 自动对齐之外未能可靠一一对应的段落未逐字确认；后续批次应改进结构对齐后继续覆盖。
- 下一批建议继续扩大到 FISH 函数页、边界/初始应力相关教程，以及 3DEC/PFC 高频命令页。
- 不得将本报告的“未发现可确认问题”表述为“全部准确”。
