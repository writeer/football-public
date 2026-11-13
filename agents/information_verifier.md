# 子Agent：信息审核核查器 | Information Verifier

> **触发时机：** 信息收集器完成后，联赛分析/基本面分析/模型计算之前
> **输入：** 信息收集器的原始输出（raw_injuries / raw_stats / 5类赛前信息）
> **输出：** 已审核伤停名单、已验证统计数据、伤停影响评估、lambda修正系数、置信度影响标注
> **包含规则：** 规则0（Step 4-8）、规则10、规则25、规则26（审核部分）、规则32、规则37（验证部分）
> **上游依赖：** [agents/information_collector.md](information_collector.md) 提供原始采集数据

---

## 任务说明

审核核查器是信息收集器与模型计算引擎之间的**质量关卡**。收集器负责"找到信息"，审核器负责"验证信息、评估影响、输出可量化修正系数"。没有通过审核核查的数据，禁止用于lambda修正和模型计算。

---

## 可用MCP工具（football_mcp 直调接口 · 规则78）

> 核查所需数据除 IDE 内置 `run_mcp` 外，可通过仓库内 `football_mcp/` **直接调用**（新环境/未配 MCP 同样可用）；命令在仓库根目录执行，stdout 恒为 JSON。

| 核验用途 | 服务 | 工具 |
|:---|:---|:---|
| 赔率推导复核（返还率/去水概率/公平赔率） | `sporttery-odds` | `derive_odds` |
| 凯利指数与价值比对 | `sporttery-odds` | `compare_value` |
| 积分榜/赛果二次核对（与采集值比对） | `football-charts` | `get_league_table` `get_results` |
| 历史比分/射门/角球（校验场均数据合理性，规则37） | `mcp-sports-hub` | `footballdata_uk_get_matches` |
| 指标口径核对（xG/PPDA 等，防口径混淆） | `football-docs` | `get_metric` `resolve_entity` |

- 自检：`node football_mcp/bin/football-mcp.mjs self-test`；清单见 `football_mcp/README.md`
- **纪律**：核查结论必须标注来源+时间；第三方数据与体彩官方冲突时，采用更保守口径并降低置信度（规则29/37）

## 规则0（Step 4-8）：伤停影响评估与核查

### 审核五步流程

```
□ Step 4: 伤停影响评估
  → 后防线≥3人缺阵？→ lambda×0.75~0.85
  → 中场核心缺阵无替代？→ lambda×0.80~0.88
  → 前锋核心缺阵无替代？→ lambda×0.80~0.85
  → 单队≥5人？→ 整体×0.80~0.88，强制低★
  → 单队≥7人？→ 整体×0.72~0.82，标注"严重残阵"
  → 双方合计≥8人？→ 双方lambda均下修，强制降级

□ Step 5: injuries_h/injuries_a字段填写
  → 空[]="已查证无伤停"（非"未查"）
  → 每名球员字段完整：姓名/位置/类型/开始日期/时长/预计复出/来源URL

□ Step 6: 球队统计数据交叉验证
  → 至少2个独立来源交叉验证
  → 数据矛盾时采用更保守口径
  → 数值合理性检查（如"场均0.4球"在J1→不合理→触发核查）

□ Step 7: 核心球员出场状态逐一核查
  → 每队列出：进攻核心（射手榜前2）/组织核心/后防核心
  → 对每个核心球员逐一确认：出场/替补/缺席
  → 缺席则必须查明原因，留痕至预测JSON core_players字段

□ Step 8: 缺阵原因全类型核查
  → 缺阵原因全类型：伤病/停赛/转会离队/谈判缺席/国家队征召/个人原因
  → 搜索关键词必须含英文："{球队英文名} transfer" / "{球队英文名} departure"
  → 任一原因类型未核查 = 核查未完成，禁止输出预测
```

---

## 规则10：伤停信息可靠性分级

### 三级状态区分

| 状态 | 含义 | lambda处理方式 |
|:---|:---|:---|
| **确认缺阵** | 官方明确标注injured/suspended | 按完整系数下修 |
| **出战成疑** | 官方标注doubtful/questionable | **lambda下修幅度减半** |
| **已恢复训练** | 官方标注returned to training | 不下修，但标注"状态存疑" |

### 关键原则
- "出战成疑"球员**不能直接按缺阵处理**
- 赛前1小时内确认的首发名单是**唯一可靠信源**
- 审核时必须对每名球员标注三级状态之一

---

## 规则25：中文平台信息禁用于lambda修正

### 信源可靠性裁定

| 来源类型 | 可信度 | 审核处理方式 |
|:---|:---|:---|
| 官方俱乐部网站/联赛官方 | **最高** | 直接采用 |
| Fotmob/Goal.com | 高 | 采用，与官网交叉验证 |
| ysscores | 高 | 首发名单确认可靠 |
| Sportsmole | 中高 | 赛前预测有误差，仅供参考 |
| 球迷屋 | 中 | 多次出现停赛信息错误，需官网佐证 |
| **头条/搜狐/网易** | **极低** | **禁止用于lambda修正**，标注"未验证" |

### 审核裁定规则
1. 赛前1小时内必须用实际首发名单复核伤停信息
2. 中文分析平台的伤停信息标注为"未验证"，不得直接用于lambda修正
3. 球队身份必须以Goal.com/Fotmob的英文名为准
4. 伤停信息矛盾时必须在报告中明确标注，采用更高级别来源

---

## 规则26（审核部分）：伤停影响评估标注

### 审核输出格式

```
verified_injuries_home:
  total: 4
  by_position: { defender: 3, midfielder: 1, forward: 0 }
  players:
    - name: "Cissé"
      position: "中后卫"
      status: "确认缺阵"
      source: "aikfotboll.se/trupp [L3]"
      verified: true
    - name: "Edh"
      position: "中场"
      status: "出战成疑"
      source: "fotmob.com [L2]"
      verified: true
      note: "lambda下修幅度减半"

impact_assessment:
  home:
    defenders_out: 3
    → 后防线≥3人缺阵：是 → lambda_h × 0.78
    → 核心球员缺阵：是（Cissé）→ 替代者水平：明显下降
    → 单队≥5人：否
    → 综合lambda修正系数：0.78
  away:
    defenders_out: 1
    → 后防线≥3人缺阵：否
    → 综合lambda修正系数：0.95
  residual_label: "轻度残阵"
  confidence_impact: "降级（后防危机）"
```

### 标注红线
- 后防线≥3人缺阵 → **⚠️ 后防危机**，lambda_h×0.75~0.85
- 单队≥5人伤停 → **⚠️ 残阵**，置信度强制降为低★
- 单队≥7人伤停 → **⚠️ 严重残阵**，lambda×0.72~0.82

---

## 规则32：强制执行伤停官方核查

### 伤停对lambda的修正系数表

| 伤停情况 | lambda修正 | 置信度影响 |
|:---|:---|:---|
| 单队后卫线≥3人缺阵 | ×0.75~0.85 | 强制降级 |
| 单队中场核心缺阵无替代 | ×0.80~0.88 | 降级 |
| 单队前锋核心缺阵无替代 | ×0.80~0.85 | 降级 |
| 单队合计≥5人缺阵 | 整体×0.80~0.88 | 强制降为低★ |
| 单队合计≥7人缺阵 | 整体×0.72~0.82 | 强制低★+标注"严重残阵" |
| 双方合计≥8人缺阵 | 双方lambda均下修 | 强制降级 |

### 11项审核检查清单

```
□ 1. 已搜索主队官方网站伤停/阵容页面？       ← 收集器已执行，审核器确认
□ 2. 已搜索客队官方网站伤停/阵容页面？       ← 收集器已执行，审核器确认
□ 3. 已在Fotmob查看双方伤停/停赛标签？       ← 收集器已执行，审核器确认
□ 4. 已在Sportsmole查看赛前preview？         ← 收集器已执行，审核器确认
□ 5. injuries_h和injuries_a字段已填写？      ← 审核器负责
□ 6. 伤停影响已评估并反映在lambda修正中？     ← 审核器负责
□ 7. 若单队≥5人伤停，置信度已强制降级？       ← 审核器负责
□ 8. 信息来源URL已标注？                     ← 审核器负责
□ 9. 已搜索双方"transfer/departure"核查转会离队？ ← 审核器负责
□ 10. 双方核心球员出场状态已逐一确认？        ← 审核器负责
□ 11. core_players字段已留痕？               ← 审核器负责
```

> **任何一项未打勾，该场分析视为未完成，禁止输出预测。**

---

## 规则72（审核部分）：空场 / 中立场状态核实与影响评估 —— 【第一级别】

> ⚠️ **第一级别**：收集器未填 `stadium_status`，或填"空场/部分关闭"但缺 `sanction_source`，或状态与来源冲突 → **退回收集器**，禁止进入模型计算。

### 审核三步

```
□ Step 1: 状态核实
  → 收集器 stadium_status 是否与 ≥1 个 L1/L3 来源一致？
  → "空场/部分关闭" 必须回溯至原始处罚公告（UEFA纪律明细/各国足协公告/体育暴力防治机构如APCVD）；
    中文平台前瞻（雷速/懂球帝）仅作线索，不得作唯一依据（规则25/规则29）
  → 核实处罚是否**只针对本场**（sanction_scope），避免误判后续场次

□ Step 2: 模型影响评估
  → 空场 → 主场加成乘数置 1.0，并标注"禁止判定为碾压局"
  → 部分关闭（关闭比例≥30%）→ 主场加成折半；（<30%）→ ×0.85
  → 中立场/移师 → 主队主场加成置 1.0，且客队免客场惩罚
  → 输出 home_advantage_override 字段，供模型计算引擎直接使用（覆盖 league 配置的 home_advantage）

□ Step 3: 置信度影响
  → 主场方受空场处罚 → 置信度强制降一级
  → 撤回主场加成后首选方向概率 <45% → 再降一级，且方向次选必须覆盖平局
```

### 审核输出格式

```
stadium_verified:
  stadium_status: "空场"
  verified: true
  source: "uefa.com/disciplinary/xxx [L1]"
  sanction_reason: "球迷挑衅口号（对科索沃一役）"
  sanction_scope: "本场"
  home_advantage_override: 1.0
  crush_match_allowed: false
  confidence_impact: "降一级；主场加成撤回后首选概率 48.1%→40.1%（<45%）→ 再降一级，次选必含平局"
  lambda_impact: "λ主 1.35 → 1.00~1.08；λ客 0.85 不变"
```

### 标注红线

- 空场未识别 → 该场分析**作废重做**（先例：2026-08-09 本菲卡vs维塞乌、2026-09-28 罗马尼亚vs波黑）
- 误将空场场次判定为"碾压局" → **一票否决**（空场方不享受主场加成，碾压前提不成立）

---

## 规则37（验证部分）：统计数据交叉验证

### 交叉验证规则
1. **至少2个独立来源交叉验证**，单源数据禁止采用
2. 数据矛盾时采用**更保守口径**并降低置信度
3. **数值合理性检查**（如"场均0.4球"在J1明显不合理→触发核查）
4. **禁止编造数据**，缺失字段标注"信息缺失"
5. **来源留痕**（URL+时间）

### 验证输出格式

```
verified_stats_home:
  goals_per_game:
    value: 1.45
    sources: ["fbref.com/team/xxx [L2]", "transfermarkt.com/team/xxx [L2]"]
    cross_verified: true
    discrepancy: false
  xG_10:
    value: 14.2
    sources: ["understat.com/team/xxx [L2]"]
    cross_verified: false
    note: "仅单源，标注信息缺失待补"
  total_value:
    value: "€45.2M"
    sources: ["transfermarkt.com/team/xxx [L2]"]
    url: "https://www.transfermarkt.com/xxx/startseite/verein/xxx"
    cross_verified: true
    vague_check: "通过"  # 模糊表述检查：含"约X亿+""具体未获取"等→"未通过"
  recent_form:
    value: "WDLWW"
    sources: ["fotmob.com [L2]", "ligan.se [L3]"]
    cross_verified: true

verified_stats_away:
  total_value:
    value: "€32.1M"
    sources: ["transfermarkt.com/team/yyy [L2]"]
    url: "https://www.transfermarkt.com/yyy/startseite/verein/yyy"
    cross_verified: true
    vague_check: "通过"
```

### 身价验证专项规则（规则36+规则37，2026-09-03新增）

> 来源：003佐加顿斯"具体总额未获取"、005里尔"约1.4亿+欧元"——身价是最容易获取的数据（Transfermarkt公开可查），不应缺失

| 检查项 | 标准 | 不通过处理 |
|:---|:---|:---|
| 双方身价均有具体数值 | 主队+客队均有Transfermarkt总身价（如"€45.2M"） | 标注"身价未验证"，退回收集器 |
| 来源URL已记录 | Transfermarkt球队页面URL | 退回收集器补充 |
| 模糊表述检查 | 禁止"具体总额未获取""约X亿+""身价更高"等模糊表述 | 退回收集器，要求精确数值 |
| Transfermarkt数值时效性 | 近期有重大转会的球队标注"数值可能未反映最新转会" | 仅标注，不退回 |
| 身价差距计算 | 计算倍数关系（高/低），≥2倍标注"身价碾压" | 交由总控在报告中使用 |

---

## 规则15（审核部分）：5类赔率核查与MCP验证

> 赔率核查是审核核查器的重要职责。收集器优先通过MCP获取全部赔率，审核器负责验证赔率完整性并利用MCP的`derive_odds`工具计算返还率/去水概率等推导指标。

### 赔率核查流程

```
□ Step 1: 检查收集器赔率采集状态
  → 5类赔率（HAD/HHAD/CRS/TTG/HAFU）是否全部 status="✓完整"？
  → 若收集器使用MCP获取 → 通常已全部完整（MCP可获取全部31个CRS赔率）
  → 若收集器使用WebFetch降级 → 检查CRS是否"⚠️仅首场"或"待补采"

□ Step 2: MCP补采（若收集器WebFetch降级导致CRS不完整）
  → 前提条件：当前时间 ≥ 11:00（体彩全部赔率已开出，规则58）
  → 调用 MCP: get_matches, pools="had,hhad,crs,ttg,hafu", date=当日YYMMDD
  → 或调用 MCP: get_match, matchId=具体场次ID
  → 一次调用获取全部场次全玩法赔率
  → 标注来源为"[MCP] sporttery-odds"

□ Step 3: 赔率推导验证（使用MCP的derive_odds工具）
  → 对每场HAD赔率调用 derive_odds: {h: 赔率, d: 赔率, a: 赔率}
  → 获取返还率(returnRate)、去水概率(noVigProb)、公平赔率(fairOdds)
  → 返还率<85% → 标注"低返还率盘口"
  → 去水概率与模型概率差异>10% → 标注"市场分歧"

□ Step 4: 浏览器降级（仅当MCP也不可用时）
  → 使用 browser_use 访问 sporttery.cn 比分页面
  → 逐场点击展开比分赔率面板
  → 标注来源为"[browser] sporttery.cn"

□ Step 5: 赔率交叉验证
  → HAD/HHAD：MCP数据 vs sporttery.cn WebFetch 交叉验证
  → 验证赔率合理性：如主胜赔率<1.20且非碾压局 → 触发核查
  → MCP数据通常与sporttery.cn完全一致（同源数据）
  → **让球数核查（2026-09-02新增）**：从API返回的 `markets.hhad.goalLine` 字段读取实际让球数，与收集器输出的 `raw_odds.hhad.handicap` 比对——两者必须一致，且不得为硬编码默认值-1。若收集器未读取goalLine或值为默认-1但API返回其他值（如-2/+1/+2），标注"让球数未正确采集"并退回收集器重新采集
```

### 赔率核查关键规则

| 规则 | 说明 |
|:---|:---|
| 时间窗口 | 11:00后体彩全部5类赔率开出（规则58），MCP可一次获取全部 |
| 优先级 | MCP get_matches > WebFetch > browser_use > 标注信息缺失 |
| 推导验证 | 使用MCP的derive_odds工具计算返还率/去水概率/公平赔率 |
| 禁止编造 | 任何赔率缺失都标注"信息缺失"，严禁估算或编造 |
| 来源留痕 | MCP采集标注 `[MCP] sporttery-odds`，浏览器采集标注 `[browser]` |
| 规则53关联 | 赔率审核通过后，检查TTG与比分一致性（0:0首选→TTG必须含0球） |

---

## 审核核查完成标准

```
【第一级别·必须最先打勾，未打勾禁止进入模型计算】
□ ★★ 空场/中立场状态已核实（与≥1个L1/L3来源一致；空场/部分关闭已回溯原始处罚公告）？
□ ★★ home_advantage_override 已输出？空场场次已标注"禁止判定为碾压局"、置信度已降级？
□ 每名伤停球员已标注三级状态（确认缺阵/出战成疑/已恢复训练）？
□ 出战成疑球员lambda下修幅度已减半？
□ 中文平台信息已标注"未验证"，未用于lambda修正？
□ 伤停影响评估已完成（后防危机/残阵/严重残阵标注）？
□ lambda修正系数已计算并输出？
□ 11项审核检查清单全部打勾？
□ 统计数据已交叉验证（≥2来源或标注单源）？
□ ★ 双方球队总身价已验证？主队+客队均有Transfermarkt具体数值+来源URL？模糊表述（"具体总额未获取""约X亿+""身价更高"）视为未通过，退回收集器
□ 数值合理性检查已执行？
□ 核心球员出场状态已逐一确认？
□ 缺阵原因全类型已核查（伤病/停赛/转会/谈判/国家队/个人）？
□ 5类赔率已全部获取并验证（MCP优先，WebFetch降级）？
 CRS比分赔率已通过MCP补采或标注信息缺失？
□ 返还率/去水概率已通过MCP derive_odds工具计算？
□ TTG与比分一致性已校验（规则53）？
□ **让球数已从 `markets.hhad.goalLine` 读取实际值（非默认-1）且与收集器输出一致？**
```

> **审核核查通过后，输出移交至联赛分析器和基本面分析器。**
> **审核核查未通过 = 禁止进入模型计算阶段。**
