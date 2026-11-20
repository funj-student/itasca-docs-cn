# 第二批sub4审校报告（第76—100篇）

日期：2026-11-20

本批由 AI 对照官方 Itasca 7.0 英文原文逐页审校，不是人工专业终审。程序强/语义对齐只作定位，不视为 AI 语义确认。

## 1. 统计

| 指标 | 数量 |
| --- | ---: |
| 审校页面 | 25 |
| 英文块 | 887 |
| 中文块 | 761 |
| 自动强对齐 | 232 |
| 自动语义对齐 | 115 |
| 已确认修复 | 8 |
| 待复核 | 4 |

## 2. 修订与待复核

- **B2-203 P0** `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.initialize.html`：官方定义四类初始转动速度关键字，中文整类功能漏译。
- **B2-204 P1** `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.generate.html`：英文明确只有四个顶层关键字，子关键字列入首关键字会误导命令用法。
- **B2-205 P1** `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.mechanical.html`：原文要求仅保留质量比例阻尼，原译语义反转。
- **B2-206 P1** `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.mechanical.html`：原文要求仅保留刚度比例阻尼，原译语义反转。
- **B2-207 P2** `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.mechanical.html`：现行官方段无 bcmass/zcmass 参数要求，旧内容会误导用户。
- **B2-208 P3** `pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.tractions.html`：参数符号 bx/by/bz/fy 被误译为普通中文词。
- **B2-209 P2** `pfc/docproject/source/manual/examples/tutorials/generating_a_bonded_assembly/generating_a_bonded_assembly.html`：英文指不逸出容器，不是不运动。
- **B2-210 P3** `pfc/pfcmodule/doc/manual/measure_manual/command_reference/cmd_measure/cmd_measure.create.html`：fh 对应 highest bin edge，不是高度系数。

待复核：

- **B2-P13** `pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.fix.html`：英文 Usage Examples 三段在中文缺失；关键字正文完整，需评估补译。
- **B2-P14** `pfc/docproject/source/manual/examples/tutorials/generating_a_bonded_assembly/generating_a_bonded_assembly.html`：2020 中文与 2024 英文数据文件存在 kn/porosity/calm/proximity/timestep 等成批差异，疑为官方版本更新。
- **B2-P15** `pfc/docproject/source/manual/examples/tutorials/using_cmat/using_cmat.html`：hz_shear 译作“剪切滞回”，英文为 shear modulus property hz_shear，术语待统一。
- **B2-P16** `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.mechanical.html`：中文多出“在动力分析中不应使用全局缩放”，英文相应段为 Global Damping，需独立确认是否旧版残留。

## 3. 逐页覆盖

| # | 页面 | 英/中块 | 强/语义 | AI报告核查段落 | AI报告未核实 |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.excavate.html` | 8/8 | 2/1 | 4 | 0 |
| 2 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.finite-element.html` | 14/12 | 3/0 | 8 | 0 |
| 3 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.fix.html` | 15/15 | 3/3 | 9 | 0 |
| 4 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.fluid.html` | 62/54 | 6/7 | 40 | 0 |
| 5 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.generate.html` | 44/43 | 7/2 | 30 | 0 |
| 6 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.group.html` | 9/9 | 2/1 | 5 | 0 |
| 7 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.initialize.html` | 33/25 | 3/1 | 17 | 0 |
| 8 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.insitu.html` | 50/47 | 5/5 | 31 | 0 |
| 9 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.joint-plane.html` | 10/10 | 3/1 | 4 | 0 |
| 10 | `3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.mechanical.html` | 55/42 | 8/21 | 103 | 0 |
| 11 | `pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.create.html` | 28/27 | 9/0 | 56 | 0 |
| 12 | `pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.distribute.html` | 40/37 | 12/5 | 148 | 0 |
| 13 | `pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.generate.html` | 44/40 | 14/3 | 176 | 0 |
| 14 | `pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.fix.html` | 29/17 | 2/0 | 41 | 0 |
| 15 | `pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.property.html` | 10/9 | 2/1 | 26 | 0 |
| 16 | `pfc/pfcmodule/doc/manual/ball_manual/ball_commands/cmd_ball.tractions.html` | 34/33 | 5/10 | 45 | 0 |
| 17 | `pfc/docproject/source/manual/pfc_model_components/balls/balls.html` | 9/10 | 3/1 | 25 | 0 |
| 18 | `pfc/docproject/source/manual/pfc_model_components/clumps/clumps.html` | 11/12 | 5/1 | 5 | 0 |
| 19 | `pfc/docproject/source/manual/pfc_model_components/walls/walls.html` | 10/11 | 3/1 | 3 | 0 |
| 20 | `pfc/docproject/source/manual/examples/tutorials/callbacks/callbacks.html` | 160/102 | 37/13 | 57 | 3 |
| 21 | `pfc/docproject/source/manual/examples/tutorials/generating_a_bonded_assembly/generating_a_bonded_assembly.html` | 56/52 | 31/11 | 42 | 0 |
| 22 | `pfc/pfcmodule/doc/manual/measure_manual/command_reference/cmd_measure/cmd_measure.create.html` | 25/24 | 8/2 | 19 | 0 |
| 23 | `pfc/pfcmodule/doc/manual/measure_manual/command_reference/cmd_measure/cmd_measure.dump.html` | 13/13 | 3/0 | 12 | 0 |
| 24 | `pfc/docproject/source/manual/examples/tutorials/using_cmat/using_cmat.html` | 95/87 | 51/22 | 68 | 6 |
| 25 | `pfc/docproject/source/manual/numerical_simulations_with_pfc/material_modeling_support_for_pfc.html` | 23/22 | 5/3 | 9 | 0 |

详细证据见同目录 JSONL 记录；`ai_reviewed_paragraphs_reported` 来自 AI 审校员逐页报告，不代表人工终审。
