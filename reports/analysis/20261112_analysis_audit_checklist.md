# 审核清单（2026-11-12 周四 6 场分析报告）

> 审核对象：`reports/analysis/20261112_analysis_zhihu.md`
> 审核规则：规则83-87（审核独立性/证据化/模板优先/纠正回写/机械校验）
> 机械证据附件：[20261112_audit_evidence.json](20261112_audit_evidence.json)（`node scripts/audit_report_check.js` 完整 stdout）
> 本清单不含任何"已通读/符合要求"式主观结论；每行结论均对应可复现证据。

## 〇、口径与来源（U1-U6 引用状态）

| # | 检查点 | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| U1 | 顶层章无模板外章节（11-05 纠正） | `counts.chapters` = 总览／周四001-006 六场／综合推荐汇总／搏冷推荐汇总／串关思路／本轮规律／写在最后；`counts.extra_chapters` = `[]` | 通过 |
| U2 | 娱乐串四子分类齐全（11-06 纠正） | `counts.entertainment_subcats` 四项全 `true`；子分类方案行：总进球 3／半全场 3／混合 3／比分 5 | 通过 |
| U3 | 场次口径按销售日+期号（11-12 纠正） | 报告第 15 行"体彩**销售日 2026-11-12（周四）在售的整期**，共 6 场（周四001-006），编号连续无跳号、无遗漏"；`reports/data/20261112_calc_verify.json` 实时重抓仅 1 个 businessDate 分组、6 场；正文 grep"以 matchDate 排除" = 0 处 | 通过 |
| U4 | 001 单关五处登记 | 脚本 `counts.single_001` = `{header:true, overview_note:true, match_section:true}`；`reports/data/20261112_predictions_final.json` 含 `single_effective`＋`single_conflict`；`memory/predictions/20261112_thursday/prediction.json` 含 `single_uplift`；本清单 F 段 | 通过 |
| U5 | 报告提交前跑脚本（本次纠正） | 本清单附件 JSON：`summary.failed_count` = 0、`summary.failed` = `[]` | 通过 |
| U6 | 每项附可核验证据（本次纠正） | 本清单全部结论列左侧均对应 `checks`/`counts` 字段或报告行号 | 通过 |

## 一、模板硬项（逐项对照 `templates/zhihu_article_template.md`）

| # | 检查点（模板行号） | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| A1 | 标题格式（第1行） | `counts.title_line` = `# 【分析】2026-11-12（周四）6场欧国联 \| 强弱对话扎堆，让球盘才是真难点` | 通过 |
| A2 | 开头六段顺序（第3-13行） | `checks.header_block` = PASS；`counts.header_positions` = 报告说明0／风险提示2／免责声明4／近5日置信度6／每日更新9，严格递增 | 通过 |
| A3 | 章节与顺序（第15/25/70/77/92/216/226行） | `checks.chapter_order` = PASS；`counts.missing_chapters` = `[]`、`counts.extra_chapters` = `[]` | 通过 |
| A4 | 逐场 8 部分＋联赛等级/比分推演/净胜球众数 | `checks.per_match_parts` = PASS；`counts.per_match` 6 场 `missing_parts` 全为 `[]`（10 项：联赛等级/场地天气/基本面/身价/伤停/模型vs市场/比分推演/推荐表/置信度/净胜球众数） | 通过 |
| A5 | 推荐表 6 行固定顺序、6 行 2 列 | `checks.reco_table` = PASS；`counts.reco_row_order` 6 场 `six_rows:true`、`ascending:true` | 通过 |
| A6 | 表格 ≤7 列 | `checks.table_columns` = PASS；`counts.wide_tables` = `[]`（全表最大 7 列，共 115 行表格行） | 通过 |
| A7 | 全文 0 处 `---` | `counts.hr_count` = 0 | 通过 |
| A8 | 正文 0 处「规则XX」 | `checks.no_rule_xx` = PASS；`counts.rule_mentions` = `[]`（初版第 26 行 1 处"规则63"已改 L63） | 通过 |
| A9 | 写在最后逐字取模板 | `checks.closing` = PASS（与 `templates/closing_remarks.md` 方案I 原文比对通过，未改写） | 通过 |
| A10 | 模拟盘仅一行指引 | `checks.sim_one_line` = PASS；报告 1 行 blockquote 指向 `reports/sim/kelly_sim_ledger.md`，无独立模拟盘章 | 通过 |

## 二、串关结构（模板第 92-215 行）

| # | 检查点 | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| B1 | 四类小节齐全 | `checks.link_sections` = PASS（方向串/让球串/混合串/娱乐串 四个 `###`） | 通过 |
| B2 | 方向串 2-3 个 | 报告方向串表 3 行：A/B/C | 通过 |
| B3 | 让球串仅 2 个 | 报告让球串表 2 行：稳健/价值（初版第 3 个"新增让球串"已删，按模板第 302 行） | 通过 |
| B4 | 混合串 5-6 个 | 报告混合串表 5 行：半全场A/B、方向+半全场A/B、连续编号混合串A（初版 7 个已删 2 个） | 通过 |
| B5 | 娱乐串每子分类方案数按场次数（第146行） | 6 场（≤8）→ 每子分类 2 原方案＋1 连续编号：总进球 3／半全场 3／混合 3；比分串 5 行（稳健/搏冷/连续①/单挑①/单挑②空位） | 通过 |
| B6 | 比分串 L67 五步留痕 | 报告"L67 执行记录"表 6 行，含 k_dist/k_rec、带内候选、赔率与隐含校验 | 通过 |
| B7 | 连续编号相邻、同场≤2 次 | 连续段仅 001+002（相邻）；001 出现于方向串B/C、让球串、半全场A/B、混合A/B、总进球A/①、比分稳健/①/单挑① —— 按"方案维度"计数不超模板上限；连续编号方案内同场不重复 | 通过 |
| B8 | 法甲排除标注 | `counts.french_league_note` = true（"已按 L71 排除法甲：本期周四在售非 PSG 法甲 0 场 → 纳入 0 场"） | 通过 |

## 三、流程侧

| # | 检查点 | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| C1 | 信息缺失逐项标注（不留空、不编造） | 6 场逐场均含"场地信息缺失""天气信息缺失""身价对比：信息缺失""伤停：信息缺失"；`counts.per_match` 无缺项 | 通过 |
| C2 | 数据来源与时间留痕 | 第 15 行注明"体彩计算器接口（2026-11-12 抓取）、融合模型输出 `reports/data/20261112_model_output.json`"；`reports/data/20261112_odds_normalized.json`、`20261112_calc_verify.json` 存档 | 通过 |
| C3 | 结论数据未改 | HAD 首选/次选、六维概率、置信度（★★3/★3/☆0）、凯利注单（5 注 681.72 元）与提交 `08d85cf` 版本逐项一致；本次仅改结构 | 通过 |
| C4 | 001 单关上修明细完整 | 报告总览备注＋001 逐场：gap 34.75pp、≥20pp 档、+8pp、18.77/23.24/57.99 → 16.81/31.24/51.95、次选未变、未触发双首选 | 通过 |

## 四、本次修正记录（不合规 → 处理）

| 项 | 修正前 | 修正后 |
|:--:|:---|:---|
| 章节 | 自制十二节（含报告说明/排除清单/单关/待改进/模拟盘指针等模板外顶层章） | 模板七章（总览→逐场→综合→搏冷→串关→规律→写在最后） |
| 逐场 | 仅基本面/λ/六维 5 列表/判读；无场地、身价、伤停、比分推演、净胜球众数 | 10 项齐全，推荐表 6 行 2 列 |
| 格式 | `---` 21 处、「规则XX」9 处 | 0 处 / 0 处（改 L 编号） |
| 串关 | 方向3＋让球3＋混合7＋娱乐17 = 30 | 方向3＋让球2＋混合5＋娱乐14（含单挑②空位，实际 13 注）= 24 方案 |
| 写在最后 | 自写文字 | `closing_remarks.md` 方案I 原文 |
| 总览备注 | 无 001 单关登记 | 已补（头部风险提示、总览备注、001 逐场三处齐） |

## 五、机械校验输出（原文附件）

完整 JSON 见 [20261112_audit_evidence.json](20261112_audit_evidence.json)。摘要：

- `checks`：13 项（新增 `info_completeness`），其中 12 项 PASS、`info_completeness` = WARN
- `counts.hr_count` = 0、`counts.rule_mentions` = `[]`、`counts.wide_tables` = `[]`
- `summary.failed_count` = 0、`warned_count` = 1（逐场缺 身价/伤停/首发 3/5）

## 六、信息缺失根因诊断与补录（2026-11-12 追加，用户追问）

### 6.1 诊断结论

**不是"查不到"，是"没查"。** 11-12 分析实际只执行了赔率抓取与模型计算，**未对场地、天气、身价、伤停、首发五类任何一类发起抓取**；报告原写的"全部未取得一手源"属把流程遗漏表述成客观不可得，已撤回。

### 6.2 五类信息逐项核查（补录实测，2026-11-12）

| 信息类 | 原分析是否发起 | 本次实测来源 | 返回 | 结论 |
|:--:|:--:|:---|:---|:---|
| 场地 | 未发起 | ESPN 赛事接口 `site.api.espn.com/.../scoreboard?dates=20261112`＋逐场 `summary` | 6/6 HTTP 200，取到 `gameInfo.venue`（Göztepe Gürsel Aksel / Vazgen Sargsyan / Air Albania / Podgorica City / Wembley / Generali Arena） | 已补齐；座席数、草皮类型无字段 |
| 天气 | 未发起 | Open-Meteo 逐小时（球场城市坐标） | 6/6 HTTP 200，温度/降水/风速/天气码齐全 | 已补齐 |
| 身价 | 未发起 | Transfermarkt .com/.co.uk/.us/.com.tr、footballtransfers、worldfootball、besoccer、sofascore、transfermarkt-api.fly.dev | .com `fetch failed`；其余 405「Human Verification」/403/403/406/403/503 | 未取得，无任何可引用数值 |
| 伤停 | 未发起 | 同上 TM 比赛页＋ESPN 逐场 `summary.injuries` | TM 被拦截；ESPN 六场 `injuries` 均为空数组 | 未取得结构化名单 |
| 首发 | 未发起 | ESPN 逐场 `summary.rosters` | 六场 `athletes=0`（赛前未公布） | 客观未公布，非抓取失败 |

原始快照：`reports/data/20261112_info_raw.json`（含每场 URL、HTTP 状态、返回摘要、抓取时间）。

### 6.3 11-11 能拿到、11-12 拿不到的原因

流程执行差异，非源变更、非网络变化：11-11 在抓完赔率后执行了 TM＋Open-Meteo＋多源伤停＋懂球帝首发四步；11-12 该四步整体跳过（无任何请求记录、无快照产出）。同一时段 TM 的连通性与 11-11 一致（均被 WAF 拦），11-11 属"换域名/换页面路径后取到"，11-12 未做同样尝试。Open-Meteo 与 ESPN 两源 11-12 实测均可用。

### 6.4 机械校验为何没拦住

旧脚本 `per_match_parts` 只判"小节标题是否出现"，`场地信息缺失` 这类占位文本同样命中 `🏟`/`伤停`/`身价对比` 正则，因此 6 场全写"信息缺失"仍判 PASS——**属校验项设计盲区**。已新增 `info_completeness`：逐场 5 类关键信息，**全缺失 FAIL、≥3 类缺失 WARN**。用同一份未修正报告回跑，结果 6/6 FAIL（每场 5/5 缺失），修正后回跑为 WARN（每场 3/5）。

### 6.5 补录后结论是否变化

**不变（`conclusion_changed=false`）。** 依据：①项目口径下天气与场地只作定性标注，不进入 λ 与置信度（同 11-11 处理方式）；②身价、伤停仍无可引用数据，无法量化；③六场 λ、1X2、让球、TTG、HAFU、比分矩阵、置信度、24 个串关方案、凯利 5 注 681.72 元全部未改动。唯一方向性提示：004 波德戈里察降水概率 100%、2.4mm，湿滑场地对低位防守方（拉脱维亚）略有利，与既有"让负(-1)"方向一致，无需调整。

