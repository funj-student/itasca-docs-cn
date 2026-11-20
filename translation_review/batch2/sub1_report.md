# 第二批子批次 1 审校报告（25 篇）

日期：2026-11-20

## 1. 执行状态

- 已基于最新 main 合并提交 `cebd6187` 建立正式分支 `review/translation-batch2-sub1`。
- 准备成果只迁移新增文件：`scripts/review_translation_batch.py`、`tests/test_review_alignment.py`、`translation_review/batch2/*`；未重复提交第一批正文修改。
- PR #2 已合并，CI `44733077827` 已 success。

## 2. 审校范围与对齐统计

| 指标 | 数量 |
| --- | ---: |
| 审校页面 | 25 |
| 完成逐页人工复核 | 25 |
| 英文段落块 | 218 |
| 中文段落块 | 188 |
| 自动强对齐 | 106 |
| 自动语义对齐 | 4 |
| 程序未对齐（英文侧） | 108 |
| 程序未对齐（中文侧） | 78 |

自动对齐仅作辅助；未对齐段落由人工按章节与英文原文继续核查。7 篇页面因官方英文页含 2024 版成员访问/弃用说明，而中文页脚标注 2020-10-08 版，相关新增段落记为版本结构差异、未核实，不擅自按新版重排语法。

## 3. 确认问题统计

| 等级 | 数量 |
| --- | ---: |
| P0 | 0 |
| P1 | 0 |
| P2 | 3 |
| P3 | 0 |
| 待复核 | 7 |
| 审校误报 | 0 |
| 已修复并保留 | 3 |

## 4. 已修复问题

1. **B2-001 P2**：`fish_zone.flux.html` 的 x/y/z 分量正文与 Returns/Accepts 原本写成“网格单元通量向量”，丢失官方定义中的“平均热通量向量”。已改为“网格单元平均热通量向量”。官方依据：`Get the zone average heat flux vector` / `x-component of the zone average heat flux vector`。
2. **B2-002 P2**：`fish_gp.vel.html` 的 Returns/Accepts 原写“x 分量速度向量”，已改为“速度矢量的 x 分量”。官方依据：`x-component of the velocity vector`；与同批 `gp.disp`、`gp.accel` 译法一致。
3. **B2-003 P2**：`fish_zone.plane.traction.html` 将 `arr - an optional pointer to an array` 增译为“裂隙参数数组”，已改为“参数数组”。官方定义未含 “fracture/裂隙”。

逐条证据见 `sub1_records.jsonl`，含英文原文、修改前后文本、HTML 定位和验证状态。

## 5. 待复核（未修改）

以下页面存在 2024 英文页与 2020 中文页的版本结构差异：成员访问 `->x` 与整数分量访问 deprecated 说明在中文页无对应内容。它们是源版本差异，不是已确认翻译错误，故保留原译文：

- fish_gp.accel.html
- fish_gp.disp.html
- fish_gp.force.unbal.html
- fish_gp.vel.html
- fish_zone.flux.html
- fish_zone.face.normal.html
- fish_zone.face.pos.html

## 6. 25 篇逐页结果

| # | 类别 | 页面 | 结果 |
| ---: | --- | --- | --- |
| 1 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.accel.html` | 未发现翻译错误；版本结构差异待复核 |
| 2 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.convergence.html` | 未发现可确认问题 |
| 3 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.copy.html` | 未发现可确认问题 |
| 4 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.create.html` | 未发现可确认问题 |
| 5 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.delete.html` | 未发现可确认问题 |
| 6 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.disp.html` | 未发现翻译错误；版本结构差异待复核 |
| 7 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.fluid.app.html` | 未发现可确认问题 |
| 8 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.force.unbal.html` | 未发现翻译错误；版本结构差异待复核 |
| 9 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.mass.gravity.html` | 未发现可确认问题 |
| 10 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.pp.html` | 未发现可确认问题 |
| 11 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.vel.html` | B2-002 |
| 12 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.zones.html` | 未发现可确认问题 |
| 13 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.flux.html` | B2-001 |
| 14 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.fluid.prop.html` | 未发现可确认问题 |
| 15 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.mech.ratio.html` | 未发现可确认问题 |
| 16 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.dynamic.timestep.html` | 未发现可确认问题 |
| 17 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.creep.timestep.html` | 未发现可确认问题 |
| 18 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.plane.traction.html` | B2-003 |
| 19 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.gp.html` | 未发现可确认问题 |
| 20 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.near.map.html` | 未发现可确认问题 |
| 21 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.face_intrinsics/fish_zone.face.area.html` | 未发现可确认问题 |
| 22 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.face_intrinsics/fish_zone.face.normal.html` | 未发现翻译错误；版本结构差异待复核 |
| 23 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.face_intrinsics/fish_zone.face.pos.html` | 未发现翻译错误；版本结构差异待复核 |
| 24 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.field_intrinsics/fish_zone.field.get.html` | 未发现可确认问题 |
| 25 | FLAC3D FISH 函数与命令参考 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone.field_intrinsics/fish_zone.field.init.html` | 未发现可确认问题 |

## 7. 修改文件

- `doc/flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.flux.html`
- `doc/flac3d/zone/doc/manual/zone_manual/zone_fish/zone.gridpoint_intrinsics/fish_gp.vel.html`
- `doc/flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.plane.traction.html`
- `doc/_static/zh-search-data.js`
- `tests/test_translation_batch2_sub1.py`

## 8. 测试

- `python -B -m unittest discover -s tests`：30 项通过（新增 4 项第二批子批次 1 回归测试）。
- `python scripts/check_terms.py`：通过。
- `python scripts/check_links.py --known-missing scripts/known-missing-images.json`：pages=6584，missing_files=2，missing_anchors=0，known_missing_files=2；两处为既有白名单缺图。

## 9. 边界

本批为 AI 辅助逐页核查与官方英文原文对照，不等同于人工专业终审。7 篇版本结构差异标为待复核，未虚报完整覆盖；未使用“全部准确”等绝对表述。
