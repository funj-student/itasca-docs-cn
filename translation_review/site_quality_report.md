# 站点搜索与 SEO 审计报告

生成时间：2026-11-20T15:27:17.093747+00:00

| 指标 | 数量 |
| --- | ---: |
| HTML 页面 | 6577 |
| 搜索索引页 | 6568 |
| 搜索索引缺失（原始） | 9 |
| 搜索索引缺失（疑似正文） | 2 |
| sitemap 条目 | 6577 |
| sitemap 失效 doc 条目 | 0 |
| 精确路径命中查询 | 6/12 |

搜索页已设置 `noindex,follow` 并从 sitemap 移除；完整目录页已补 canonical 与 meta description。
12 个高频查询均返回非空结果，但精确路径命中为 6/12。其余查询返回的是相关主题页而非本审计预设的单一目标页；不据此改写排序规则，列为待人工相关性复核。

## 查询明细

| 查询 | 预期路径命中 | 首位结果 |
| --- | --- | --- |
| zone create | 是 | `flac3d/zone/doc/manual/zone_manual/zone_commands/cmd_zone.create.html` |
| zone initialize | 是 | `3dec/block/doc/manual/block_manual/block_commands/block.zone/cmd_block.zone.initialize.html` |
| model solve | 是 | `common/kernel/doc/manual/model/commands/cmd_model.solve.html` |
| gp.vel | 是 | `3dec/block/doc/manual/block_manual/block_fish/block.gridpoint/fish_block.gridpoint.vel.app.html` |
| zone.flux | 是 | `flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.flux.html` |
| 摩擦角 | 否 | `3dec/docproject/source/examples/FallingWedge.html` |
| 安全系数 | 否 | `3dec/block/test3d/Theory_and_Background/Factor_of_Safety/FOS_Contours/FOSContours.html` |
| 初始地应力 | 否 | `3dec/docproject/source/examples/AssessmentOfFaultSlip.html` |
| Rayleigh 阻尼 | 是 | `3dec/docproject/source/options/dynamic/dynamic_damping.html` |
| 刚性簇 | 否 | `common/docproject/source/manual/program_guide/mechanics/plotting/views/plotitems/items/clump.html` |
| 颗粒黏结 | 否 | `common/docproject/source/manual/program_guide/methodology/pfcparticleshape.html` |
| 水力压裂 | 否 | `3dec/docproject/source/examples/HydraulicFractureDFN.html` |
