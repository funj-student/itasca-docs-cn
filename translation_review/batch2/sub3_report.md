# 第二批sub3审校报告（第51—75篇）

日期：2026-11-20

本批由 AI 对照官方 Itasca 7.0 英文原文逐页审校，不是人工专业终审。程序强/语义对齐只作定位，不视为 AI 语义确认。

## 1. 统计

| 指标 | 数量 |
| --- | ---: |
| 审校页面 | 25 |
| 英文块 | 1932 |
| 中文块 | 1720 |
| 自动强对齐 | 690 |
| 自动语义对齐 | 300 |
| 已确认修复 | 2 |
| 待复核 | 4 |

## 2. 修订与待复核

- **B2-201 P1** `flac3d/docproject/source/modeling/tutorials/basicclifish.html`：命令名必须原样保留；中文链接本身指向 automatic-create。
- **B2-202 P1** `flac3d/docproject/source/options/thermalanalysis/thermal/numerical-form.html`：定性稳定性安全警告漏译，影响数值方法选择。

待复核：

- **B2-P09** `flac3d/docproject/source/modeling/problemsolving/tips.html`：英文 .prj 与中文 .f3prj 项目扩展名差异；可能是按现行软件命名本地化。
- **B2-P10** `flac3d/docproject/source/modeling/problemsolving/workinggeometricdata.html`：英文 GeometricData.prj 与中文 GeometricData.f3prj 差异。
- **B2-P11** `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.create.html`：英文主关键字含 center-1，中文概览列表缺失；正文关键字存在。
- **B2-P12** `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.cut.html`：英文主关键字含 x-local，中文概览列表缺失；正文关键字存在。

## 3. 逐页覆盖

| # | 页面 | 英/中块 | 强/语义 | AI报告核查段落 | AI报告未核实 |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `flac3d/docproject/source/modeling/problemsolving/structuralsupport.html` | 8/7 | 2/0 | 4 | 0 |
| 2 | `flac3d/docproject/source/modeling/problemsolving/tips.html` | 64/54 | 15/15 | 15 | 0 |
| 3 | `flac3d/docproject/source/modeling/problemsolving/workinggeometricdata.html` | 163/151 | 69/9 | 25 | 0 |
| 4 | `flac3d/docproject/source/modeling/tutorials/basicclifish.html` | 170/153 | 58/11 | 25 | 0 |
| 5 | `flac3d/docproject/source/modeling/tutorials/firstflac3dmodel.html` | 390/333 | 94/64 | 80 | 0 |
| 6 | `flac3d/docproject/source/modeling/tutorials/intro.html` | 12/12 | 2/0 | 4 | 0 |
| 7 | `flac3d/docproject/source/options/dynamic/solving/solving.html` | 11/10 | 2/1 | 2 | 0 |
| 8 | `flac3d/docproject/source/options/dynamic/relation/relation.html` | 44/41 | 13/10 | 25 | 0 |
| 9 | `flac3d/docproject/source/options/dynamic/verification/verification.html` | 13/12 | 2/0 | 2 | 0 |
| 10 | `flac3d/docproject/source/options/dynamic/solving/recommendedsteps.html` | 30/29 | 7/17 | 18 | 0 |
| 11 | `flac3d/docproject/source/options/dynamic/references/references.html` | 88/88 | 84/0 | 70 | 0 |
| 12 | `flac3d/docproject/source/options/dynamic/models/review.html` | 41/37 | 14/13 | 25 | 0 |
| 13 | `flac3d/docproject/source/options/thermalanalysis/thermal/math-model.html` | 103/84 | 38/18 | 45 | 0 |
| 14 | `flac3d/docproject/source/options/thermalanalysis/thermal/numerical-form.html` | 119/107 | 68/13 | 43 | 0 |
| 15 | `flac3d/docproject/source/options/thermalanalysis/hydration/hydration.html` | 9/10 | 2/1 | 1 | 0 |
| 16 | `flac3d/docproject/source/theory/fluid-mechanical/calcmodes/calcmodes.html` | 93/70 | 14/22 | 25 | 0 |
| 17 | `flac3d/docproject/source/theory/fluid-mechanical/verification_concepts/verification_concepts.html` | 156/149 | 98/31 | 35 | 3 |
| 18 | `flac3d/docproject/source/theory/fluid-mechanical/verification_examples/verification_examples.html` | 17/16 | 2/0 | 16 | 0 |
| 19 | `flac3d/docproject/source/theory/fluid-mechanical/properties_units/properties_units.html` | 68/61 | 21/17 | 20 | 0 |
| 20 | `flac3d/docproject/source/theory/fluid-mechanical/solving/solving.html` | 188/160 | 66/36 | 35 | 2 |
| 21 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.analyze-stability.html` | 30/25 | 2/9 | 25 | 0 |
| 22 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.apply.html` | 18/18 | 2/1 | 18 | 0 |
| 23 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.apply-remove.html` | 11/11 | 2/1 | 15 | 0 |
| 24 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.create.html` | 46/42 | 8/6 | 15 | 0 |
| 25 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.cut.html` | 40/40 | 5/5 | 15 | 0 |

详细证据见同目录 JSONL 记录；`ai_reviewed_paragraphs_reported` 来自 AI 审校员逐页报告，不代表人工终审。
