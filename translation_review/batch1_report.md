# 第一批翻译质量审校报告

审校日期：2026-11-20  
独立复核更新：2026-11-20（用户复核指出 B1-013 误译）

## 1. 范围与依据

- 审校对象：30 篇 FLAC3D 高价值文档。
  - 常用命令参考 10 篇。
  - 边界条件与初始应力 10 篇。
  - 本构模型与力学参数 10 篇。
- 英文依据：Itasca 7.0 官方站点 `https://docs.itascacg.com/flac3d700/` 对应路径。30 篇英文原文抓取状态均为 HTTP 200，原文件保存在仓库外的工作目录，仅将证据摘录写入审校记录。
- 初始自动对齐提取英文块 1,708 个、中文块 1,467 个。初版脚本把没有数字或命令标识符的段落也按相同空特征对齐，产生过 1,245 对“弱对齐”。该做法已被纠正。
- 现行严格对齐仅配对具有非空数字/命令标识符特征且特征一致的段落：317 对；无特征段落 1,293（英文）/ 1,066（中文）不再被误判为已对齐。人工逐段复核仍独立进行，不以自动对齐数量代替审校覆盖。
- 审校脚本 `scripts/review_translation_batch.py` 已增加回归测试，确保空特征段落不会仅因特征相同而配对。

## 2. 结果概览

| 项目 | 初版统计 | 独立复核后最终统计 |
| --- | ---: | ---: |
| 审校页面 | 30 | 30 |
| 初版标记问题 | 22 | 22 |
| 确认问题 | 22 | **21** |
| 审校误报 | 0 | **1（B1-013）** |
| P0 严重技术错误 | 13 | 13 |
| P1 明显专业误译 | 5 | 5 |
| P2 术语与表达问题 | 4 | **3** |
| 已修复并保留 | 22 | **21** |
| 待复核 | 0 | 0 |

结构化记录见 `translation_review/batch1_records.jsonl`。每条记录现已包含页面路径、官方来源 URL、明确定位、英文原文、修改前文本、修改后文本、严重程度、理由、状态与独立复核结果。

## 3. 独立复核发现的误报

### B1-013：zone.flux 术语

- 初版将 `input.html` 中“单元平均热通量（zone.flux）”改为“单元平均流量（zone.flux）”。
- 用户指出该函数官方定义为“Get the zone average heat flux vector.”，位于：
  `https://docs.itascacg.com/flac3d700/flac3d/zone/doc/manual/zone_manual/zone_fish/zone_intrinsics/fish_zone.flux.html`
- 独立复核确认用户判断正确：即使该函数出现在流体分析章节，也必须以函数本身官方定义为准。
- 已撤销该改动，恢复“单元平均热通量（zone.flux）”；测试断言与中文搜索索引同步恢复。
- B1-013 已标记为“审校误报（已撤销）”，不再计入确认问题与修复数量。

## 4. 其余 21 项复核结果

其余 21 项均按官方英文页面重新核对，特别是命令关键字、FISH 函数、参数名、示例命令和数学公式：

- B1-001 至 B1-007：7 项确认正确。前置条件、警示、`[gridpointfixblock]` 标记、`fy` 参数含义及 `zone gridpoint fix` 交叉引用均有官方依据。
- B1-008 至 B1-012、B1-014：6 项确认正确。三段边界应力示例命令与官方原文逐字符一致，FISH `define/end`、table 名称、`time dynamic`、区间与坐标范围均吻合；孔压初始化漏译、公式 `ν/(1-ν)`、`relaxation → 松弛开挖` 均确认正确。
- B1-015 至 B1-022：8 项确认正确。Hoek-Brown 公式、`table-mb`、`L_c/∛(V_z)`、`zone property-distribution` 语法与示例、`modelname007.dll`、`model configure plugins`、`thermomechanical analyses → 热-力耦合分析` 均有官方英文直接依据。

复核中记录了两项非阻断细节：B1-002 的警示内容正确但结构位置在英文 admonition 框外；B1-005 的 gradient/vary 链接被简化但命令关键字与参数标记保留。这两项属既有结构或链接简化，不是本次修订引入的技术错误，不改动。

## 5. 保留的 21 项修订类型

### P0：13 项

- 补齐 3 处命令前置条件/模型选项限制。
- 补齐 `zone gridpoint fix` 被整节漏译的关键字块，并恢复 `[gridpointfixblock]` 标记。
- 修正边界应力章节 3 段示例命令错配。
- 修正 Hoek-Brown 公式 (4) 的变量替换错误。
- 修正 `table-mb` 属性关键字误写为 `table-m`。
- 修正 `zone property-distribution` 语法被错误限定为 `density`。
- 修正 DLL 版本号 `007` 误写为 `006`。
- 修正 `model configure plugins` 漏掉复数 `s`。

### P1：5 项

- 修正 `zone gridpoint free` 页面自指式交叉引用。
- 修正 `fy` 参数含义：应力比而非尺寸。
- 补齐 `zone fluid zone-based-pp on` 自动初始化孔压说明。
- 补齐 Hoek-Brown 正则化因子 `L_c / ∛(V_z)` 及 `V_z` 定义。
- 补齐 `zone property-distribution` 使用示例。

### P2：3 项

- 修正非法 LaTeX 写法 `\ν`。
- 将 `relaxation` 统一为“松弛开挖”。
- 将 `thermomechanical analyses` 改为“热-力耦合分析”。

## 6. 未发现可确认问题的页面

以下 19 篇页面经逐段复核，未发现可确认的翻译错误：

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

说明：部分英文原文自身存在编辑批注或明显原版笔误，中文忠实照译，未计为翻译错误。

## 7. 测试与验证

修订后的测试结果：

1. `python -B -m unittest discover -s tests -v`：24 项全部通过，其中 12 项翻译回归测试、3 项段落对齐回归测试。
2. `python scripts/check_terms.py`：通过。
3. `python scripts/check_links.py --known-missing scripts/known-missing-images.json`：`pages=6584 missing_files=2 missing_anchors=0 known_missing_files=2`。两处缺失文件均为既有白名单条目，未新增。

## 8. 边界与后续

- 本批是“有官方英文原文依据的审校与修订”，不构成全书人工专业终审。
- 无数字/命令标识符特征的段落不再被自动判为对齐；这些段落依赖人工复核，未逐字覆盖的部分不得表述为已核查。
- 未发现可确认问题的页面不表述为“全部准确”。
- 下一批建议继续扩大到 FISH 函数页、边界/初始应力教程，以及 3DEC/PFC 高频命令页。
