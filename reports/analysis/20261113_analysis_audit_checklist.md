# 审核清单（2026-11-13 周五 11 场分析报告）

> 审核对象：`reports/analysis/20261113_analysis_zhihu.md`（33,411 字符）
> 机械证据附件：[20261113_audit_evidence.json](20261113_audit_evidence.json)（`node scripts/audit_report_check.js reports/analysis/20261113_analysis_zhihu.md` 完整 stdout）
> 本清单不写"已通读/符合要求"式主观结论；每行结论均对应 `checks`/`counts` 字段、报告行号或 `reports/data/` 下的原始快照。

## 〇、口径与来源

| # | 检查点 | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| U1 | 场次口径＝当日销售日全量 | `reports/data/20261113_calc_raw.json` 抓取 `poolCode=hhad,had,crs,ttg,hafu&channel=c`，接口仅返回 1 个 `businessDate` 分组 2026-11-13，`matchNumStr` 周五001-011 连续无跳号；报告第 13 行写明 11 场构成（001 友谊赛＋002-009 欧国联第 5 轮＋010/011 友谊赛） | 通过：11 场，无遗漏、无增补 |
| U2 | 单关口径以投注端为准 | `counts.single_001` = `{no_single_declared: true}`，即报告全文出现 `bettingSingle=0` 且出现 `未开单关`；11 场接口字段 `bettingSingle` 全为 0（`20261113_calc_raw.json` 逐场可核）；001 逐场另写"若你的投注端显示 001 可单关，以你的端为准并触发平局上修" | 通过：本期无单关，上修规则未触发 |
| U3 | 顶层章无模板外章节 | `counts.chapters` = 总览／周五001-011 十一场／综合推荐汇总／搏冷推荐汇总／串关思路／本轮规律／写在最后；`counts.extra_chapters` = `[]`、`counts.missing_chapters` = `[]` | 通过 |
| U4 | 提交前跑审计脚本 | `summary.failed_count` = 0、`summary.failed` = `[]`、`summary.total_checks` = 13 | 通过 |
| U5 | 每项结论附可核验证据 | 本清单每行"机械证据"列均指向 `checks`/`counts` 字段、报告行号或具体快照文件路径 | 通过 |

## 一、模板硬项（对照 `templates/zhihu_article_template.md`）

| # | 检查点 | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| A1 | 标题格式（第 1 行） | `counts.title_line` = `# 【分析】2026-11-13（周五）11场欧国联+国际赛 \| 强弱分化明显，让球盘与总进球定成败`；`checks.title` = PASS | 通过 |
| A2 | 开头固定块顺序 | `checks.header_block` = PASS；`counts.header_positions` = 报告说明2／风险提示4／免责声明6／近5日置信度8／每日更新10，严格递增 | 通过 |
| A3 | 章节齐全且顺序一致 | `checks.chapter_order` = PASS；`counts.weekday` = 周五（脚本按标题解析周几，不再硬编码周四） | 通过 |
| A4 | 逐场 10 部分 | `checks.per_match_parts` = PASS；`counts.per_match` 11 场 `missing_parts` 全为 `[]`（联赛等级／场地天气／基本面／身价／伤停／模型vs市场／比分推演／推荐表／置信度／净胜球众数） | 通过 |
| A5 | 推荐表 6 行固定顺序 | `checks.reco_table` = PASS；`counts.reco_row_order` 11 场均为 `six_rows:true` + `ascending:true` | 通过 |
| A6 | 表格 ≤7 列 | `checks.table_columns` = PASS；`counts.wide_tables` = `[]`（全表 164 行表格行，无一行超 7 列） | 通过 |
| A7 | 全文 0 处 `---` | `counts.hr_count` = 0 | 通过 |
| A8 | 正文 0 处「规则XX」 | `checks.no_rule_xx` = PASS；`counts.rule_mentions` = `[]` | 通过 |
| A9 | 写在最后逐字取模板 | `checks.closing` = PASS（与 `templates/closing_remarks.md` 方案C 原文归一化比对通过） | 通过 |
| A10 | 模拟盘仅一行指引 | `checks.sim_one_line` = PASS；报告第 460 行单条 blockquote 指向 `reports/sim/kelly_sim_20261113.md`，无独立模拟盘章 | 通过 |

## 二、串关结构（模板串关章）

| # | 检查点 | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| B1 | 四类小节齐全 | `checks.link_sections` = PASS（方向串／让球串／混合串／娱乐串 四个 `###`） | 通过 |
| B2 | 方向串 3 个 | 报告 478-486 行，方案 A/B/C 三行 | 通过 |
| B3 | 让球串 2 个 | 报告 490-496 行，稳健／价值两行 | 通过 |
| B4 | 混合串 6 个 | 报告 500-509 行，半全场A/B、方向+半全场A/B、连续编号①② | 通过 |
| B5 | 娱乐串四子分类齐全 | `counts.entertainment_subcats` 四项全 `true`；方案数 4（高赔总进球）＋4（高赔半全场）＋4（半全场混合总进球）＋6（比分串）＝18；11 场 >8 场，故按模板"多场"档给 A/B 三串一并强制档位/路径差异化 | 通过 |
| B6 | 比分串含连续编号与单挑 | 比分串标题写明"6 个方案：2串 + 2连续编号 + 2单挑"；L67 双轨制 `k_dist`（全局众数，仅记录）与 `k_rec`（方向内众数，唯一带内锚点）在逐场"净胜球众数"段留痕 | 通过 |
| B7 | 法甲排除 | `counts.french_league_note` = false，原因是该字段按字面串 `已按 L71 排除法甲` 匹配；报告第 517 行实际写的是"🚫 法甲排除：本期 11 场无任何法甲场次（欧国联 8 场＋国际友谊赛 3 场），非 PSG 法甲场次 N=0 → 纳入 0 场"。语义已登记，仅措辞与脚本匹配串不一致 | 通过（语义已声明；`french_league_note` 属非检查项计数，不影响 `checks`） |

## 三、信息采集五类逐项落实（用户要求第 3 条）

| 信息类 | 覆盖 | 一手来源与证据 | 缺失说明（具体失败证据） |
|:--:|:--:|:---|:---|
| 场地 | 11/11 | ESPN 逐场 `summary` → `gameInfo.venue.fullName`；结构化落盘 `reports/data/20261113_espn_events.json`（11 条，含 `venue`/`city`/`country`）与 `reports/data/20261113_espn_detail.json`（11 条） | 座席数、草皮类型：ESPN 场馆对象无 `capacity`/`surface` 字段（逐场对象键可核），报告逐场写明"信息缺失"而非留空 |
| 天气 | 11/11 | `wttr.in/{city}?format=j1` 逐小时，落盘 `reports/data/20261113_weather.json`；报告逐场给出开球时段温度／降水概率／风速与生效判读 | 单源、非场馆实测，已在逐场句末标注"单源" |
| 身价 | 0/11 | 无可用一手源 | `reports/data/20261113_tm_probe.txt`：transfermarkt.com／.us 均 `HTTP 405 | SERVER CloudFront | TITLE Human Verification`（2289 字节验证页）；`api.sofascore.com` `HTTP 403 Varnish {"error":{"code":403}}`；`footballtransfers.com` `HTTP 403 Cloudflare "Attention Required!"`；football-charts MCP 仅覆盖俱乐部联赛，`list_leagues` 无任何国家队条目 |
| 伤停 | 10/11 | Sports Mole 赛前预览页，落盘 `reports/data/20261113_sm_previews.json`（10 个 slug 均 `HTTP 200`）＋原文 `reports/data/raw_sm_*.txt` 10 份 | 周五010 阿根廷 vs 乌拉圭：`sm_previews.json` 该条 `{"found": false, "evidence": "index pages scanned: 28 preview links, no slug match"}`；索引页 28 条预览链接中仅存在 `argentina-vs-benin`（另一场次），无本场预览 |
| 首发 | 10/11 | 同上 Sports Mole "预计首发"（报告中逐场标注"预计首发，非官方"） | 周五010：同上一行证据（预览页未发布 → 无预计首发可引） |

- 机械校验 `checks.info_completeness` = WARN：`counts.info_completeness` 中 10 场 `level` = PASS（仅缺身价 1/5），周五010 为 WARN（缺身价／伤停／首发 3/5）。该 WARN 与上表缺失证据一一对应，属如实记录，非校验放水。
- 报告全文不使用"客观取不到"这类笼统表述：`grep 客观` = 0 处；缺失处均落到具体源＋具体 HTTP 状态或字段缺失。

## 四、虚拟本金凯利模拟盘（用户要求第 5 条）

| # | 检查点 | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| D1 | 参数为收紧版 | `reports/sim/kelly_sim_ledger.json` 2026-11-13 day：单注上限 2%、单日上限 10%（余额 9,230.60 → 923.06 元）、连输 3 注停、单关上修后全凯利为负直接拦截 | 通过 |
| D2 | 注单数量与金额 | 5 注：20261113-01 周五004 HHAD 让(-2)负 @2.23 / -02 周五010 HAFU 胜胜 @2.05 / -03 周五005 TTG 2球 @4.55 / -04 周五009 TTG 2球 @4.05 / -05 周五001 TTG 2球 @5.25；逐注 184.61＋150.01＋164.51＋66.45＋181.08 = **746.66 元**（占余额 8.09% ≤ 10%） | 通过 |
| D3 | 2% 单注截断 | 仅 20261113-01 触发：原始 ¼ 凯利约 693.2 元 → 截断为 184.61 元（2% × 9,230.60） | 通过 |
| D4 | 候选池与星级门槛 | 5 注全取自六维推荐池；004 为 ★★ 走方向性 HHAD，010/005/009/001 为 ★ 走非方向玩法；落选 3 注（002 HAFU 负负 23.73%／006 HAFU 平平 22.86%／007 TTG 1球 20.82%）按模型概率降序排在 5 注之后 | 通过 |
| D5 | 串关未入盘 | `kelly_sim_ledger.json` 该 day `bets` 5 条全为单场玩法（HHAD/HAFU/TTG），无 parlay 类型；`reports/sim/kelly_sim_20261113.md` 明写"串关不进模拟盘" | 通过 |
| D6 | 单关上修拦截 | 全期 `bettingSingle=0` → 无上修注单，规则88 第 4 条未触发（非"跳过校验"） | 通过 |
| D7 | 待结算状态 | 5 注 `settled=false`，`settlement_audit` 记 `bets_total 14 / settled 9 / unsettled 5`；按规则82 于 2026-11-14 用体彩官方 `getUniformMatchResultV1` 回填 | 通过（待次日结算） |

## 五、预测底稿双份一致性（用户要求第 6 条）

| # | 检查点 | 机械证据 | 结论 |
|:--:|:---|:---|:---|
| E1 | 两份逐字节一致 | `memory/predictions/20261113_friday/prediction.json` 与 `reports/data/20261113_predictions.json` 比对：`bytes_equal True`，均 51,494 字节 | 通过 |
| E2 | 字段完整 | 11 条记录，每条含 num／league／home／away／time／is_single／single_note／confidence／probs／first／second／firstProb／secondProb／lambda／market／divergence／band／scoreTop5／hafuTop3／htScoreTop3／ttgTop2／over25／under25／handicap／odds／kDist／kRec／divergence_flag／score_parlay_*／top_scores_raw／kdist／tags／info_supplement／actual | 通过 |

## 六、机械校验摘要

完整 JSON 见 [20261113_audit_evidence.json](20261113_audit_evidence.json)。

- `summary`：`total_checks` = 13、`failed_count` = **0**、`failed` = `[]`、`warned_count` = 1、`warned` = `["info_completeness"]`
- `counts.hr_count` = 0、`counts.rule_mentions` = `[]`、`counts.wide_tables` = `[]`、`counts.tables` = 164
- `counts.weekday` = 周五（脚本改动：从标题解析周几，替换原硬编码 `周四`；单关校验改为条件化——本期无单关时校验 `bettingSingle=0` + `未开单关`）
- 唯一 WARN 来源：周五010 缺身价／伤停／首发 3/5，证据见第三节表格

## 七、本轮已知不足（不改结论，仅登记）

| 项 | 现状 | 影响面 |
|:--:|:---|:---|
| 身价全期缺失 | 3 个源全部被 WAF/403 拦截，MCP 无国家队覆盖 | 置信度上限压到 ★★；已逐场写明失败证据，不做任何倍数推断 |
| 周五010 伤停/首发缺失 | Sports Mole 未发布该场预览（28 条索引内无 slug） | 该场置信度已按缺信息下调为 ★；模型仅用 Elo＋友谊赛 prior λ |
| 周五001 无 HAD 池 | 接口该场 `had` 字段为空，仅 HHAD(+3) 在售 | 无法做胜平负市场对齐，让球端分歧 +28.03pp 无法用市场校准，已由 ★★ 降为 ★ |
| 11-13 注单待结算 | 5 注 `settled=false` | 余额曲线停在 9,230.60，次日回填后方可判规则88 滚动 ROI 是否触发暂停 |
