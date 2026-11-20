# 第二批子批次 2 审校报告（第26—50篇）

日期：2026-11-20

## 1. 依赖与范围

- PR #3 已合并，CI success；本分支基于最新 main `f275240d`。
- 审校对象：`translation_review/batch2/page_list.jsonl` 第26—50条，共25篇。
- 前15篇：FLAC3D 命令参考；后10篇：FLAC3D 建模与求解教程。
- 本批为 AI 逐页审校与官方英文原文对照，不是人工专业终审。

## 2. 自动对齐与逐页覆盖

| 指标 | 数量 |
| --- | ---: |
| 审校页面 | 25 |
| AI 逐页审校 | 25篇 |
| 英文文本块 | 1683 |
| 中文文本块 | 1402 |
| 自动强对齐 | 317 |
| 自动语义对齐 | 276 |
| AI 进一步核对并确认对应的未对齐块 | 511 |
| 因结构差异无法直接对应但已核实内容 | 511 |
| 仍未核实（主要正文口径） | 0 |
| 完成主要正文核查 | 25/25（AI） |

逐页数据见 `sub2_coverage.jsonl`。自动对齐口径包含代码块逐行、表格单元格、列表项和导航/结构块；AI 按 HTML 段落结构重新核对后，未对齐正文段落均已找到对应内容。纯数据表格未逐格校验，见限制。

## 3. 问题统计

| 等级 | 数量 |
| --- | ---: |
| P0 | 0 |
| P1 | 5 |
| P2 | 2 |
| P3 | 1 |
| 待复核 | 8 |
| 审校误报 | 0 |
| 已修复并保留 | 8 |

## 4. 确认并修复的问题

1. **B2-101 P1** `cmd_zone.history.html`：`stress-strength-ratio` 改为官方关键字 `strength-stress-ratio`（6处，含 id/href/cmdkey）。
2. **B2-102 P1** `cmd_zone.list.html`：同类关键字词序错误（3处）。
3. **B2-103 P1** `cmd_zone.dynamic.html` combined damping：将原文不存在的“默认阻尼值为 0.8”改为官方示例“目标 0.05（5%）阻尼比，输入 0.05*π”。
4. **B2-104 P1** 同上，local damping。
5. **B2-105 P2** `cmd_zone.dynamic.html`：补译 Rayleigh 阻尼刚度阻尼的临界时步降低、大变形失稳风险和 `model dynamic timestep` 处置说明。
6. **B2-106 P3** `cmd_zone.relax.html`：补译折减因子达到 0 时材料已置空、无需再次删除的行为。
7. **B2-107 P1** `material_properties.html`：`property ftable` 改为 `zone property` 的 `table-friction` 属性。
8. **B2-108 P2** `identifyingregions.html`：`constitute` 被误作 `constitutive`，且 `return assigned group names` 被误译为赋予；改为“返回构成模型外边界的这组面上已赋的分组名”。

每条记录均含英文原文、修改前后文本、定位、技术依据与状态，见 `sub2_records.jsonl`。

## 5. 待复核

- B2-P01：history 关键字历史版本命名差异（本批按现行官方页修正）。
- B2-P02/P03：`.prj` 与 `.f3prj` 项目扩展名版本差异。
- B2-P04：`zone.validate` 重复引导语。
- B2-P05/P06：英文原文疑似笔误，中文忠实照译。
- B2-P07：`service tunnel` 跨页译法不统一。
- B2-P08：纯数据表格未逐格核对。
- 上一子批次 7 篇 FISH 页面的 `->x` 成员访问与整数分量访问弃用说明仍为待复核，本轮未重审，不视为已解决。

## 6. 25 篇逐页结果

| # | 类别 | 页面 | 问题编号 |
| ---: | --- | --- | --- |
| 1 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.field_intrinsics/fish_zone.field.prop.html` | — |
| 2 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.create.html` | — |
| 3 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.generate.html` | — |
| 4 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.group.html` | — |
| 5 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.history.html` | B2-101,B2-P01 |
| 6 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.list.html` | B2-102 |
| 7 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.delete.html` | — |
| 8 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.export.html` | — |
| 9 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.import.html` | — |
| 10 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.fluid.html` | — |
| 11 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.thermal.html` | B2-P05 |
| 12 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.dynamic.html` | B2-103,B2-104,B2-105,B2-P06 |
| 13 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.creep.html` | — |
| 14 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.relax.html` | B2-106 |
| 15 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.validate.html` | B2-P04 |
| 16 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/choice.html` | B2-P02 |
| 17 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/equilibrium.html` | — |
| 18 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/gridgeneration.html` | B2-P03,B2-P07 |
| 19 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/identifyingregions.html` | B2-108 |
| 20 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/interfaces.html` | — |
| 21 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/interpretation.html` | — |
| 22 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/loading.html` | — |
| 23 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/material_properties.html` | B2-107,B2-P08 |
| 24 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/projectcompletion.html` | — |
| 25 | FLAC3D 边界/初始应力/求解/教程 | `flac3d/docproject/source/modeling/problemsolving/projectsetup.html` | — |

## 7. 修改文件

- 6 个 HTML 正文文件（history/list/dynamic/relax/material_properties/identifyingregions）
- `doc/_static/zh-search-data.js`
- `scripts/review_translation_batch.py`（表格/代码/公式块提取）
- `tests/test_review_alignment.py`（新增1项真实HTML提取测试）
- `tests/test_translation_batch2_sub2.py`（新增6项本批回归测试）

## 8. 测试

- `python -B -m unittest discover -s tests`：39 项通过。
- `python scripts/check_terms.py`：通过。
- `python scripts/check_links.py --known-missing scripts/known-missing-images.json`：pages=6584，missing_files=2，missing_anchors=0，known_missing_files=2；仅既有白名单缺图。

## 9. 限制

本批结论来自 AI 对照官方英文原文的逐页审校，不是人工专业终审。纯数据表格未逐格校验；自动对齐未覆盖的正文已由 AI 按 HTML 段落结构复核，但不能等同于人工逐段终审。
