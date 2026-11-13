# 子Agent：信息收集器 | Information Collector

> **触发时机：** 每场比赛分析的第一步，在联赛分析、基本面分析、模型计算之前
> **输入：** 主队名称、客队名称、联赛、比赛时间
> **输出：** 原始伤停名单、球队统计数据、场地天气新闻、核心球员名单（未审核）
> **包含规则：** 规则0（Step 1-3）、规则26（收集部分）、规则29、规则37（收集部分）
> **下游依赖：** [agents/information_verifier.md](information_verifier.md) 对收集结果进行审核核查

---

## 任务说明

信息收集是分析的第一生命线。本子Agent专注于**原始数据的搜索与采集**，不负责可信度评估和lambda修正——那是审核核查器的职责。收集器只管"找到信息、记录来源"，审核器管"验证信息、评估影响"。

---

## 可用MCP工具（football_mcp 直调接口 · 规则78）

> 赔率采集见下方「规则15（收集部分）」的 `sporttery-odds`。以下第三方服务用于补齐赛程/积分/阵容/历史数据；**命令在仓库根目录执行，stdout 恒为 JSON（失败退出码 2）**，Python 侧用 `call_tool("<服务id>","<工具名>",{...})`。

| 用途 | 服务 | 工具 |
|:---|:---|:---|
| 积分榜 / 赛果 / 赛程 / 进球时间分布 | `football-charts` | `get_league_table` `get_results` `get_fixtures` `get_goal_timing` |
| 球队阵容 / 球队赛程 / 积分榜 | `mcp-sports-hub` | `espn_get_team_roster` `espn_get_team_schedule` `espn_get_standings` `sportsdb_get_standings` |
| 即时比赛 / 最近赛果核验 | `mcp-sports-hub` | `sportsrc_get_live` `sportsdb_get_last_events` |
| 历史比赛+赔率（趋势/场均数据） | `mcp-sports-hub` | `footballdata_uk_get_matches`（`season` 用4位码如 `2425`；`league` 如 `E0`） |

```powershell
node football_mcp/bin/football-mcp.mjs call football-charts get_league_table --args-file args.json
node football_mcp/bin/football-mcp.mjs self-test   # 采集前自检，6服务连通性
```

- 服务清单与故障排查：`football_mcp/README.md`
- **纪律**：第三方数据仅作交叉验证与补充，**不替代体彩官方赔率**；采集输出必须标注来源+获取时间+来源等级（规则26/29/37）

## 规则72（收集部分）：空场 / 中立场处罚 —— 【第一级别 · 必查】

> ⚠️ **第一级别**：优先级**高于本文件其余全部规则**；未确认或字段留空 → 该场分析视为**未完成** → **禁止输出预测**。
> 来源：2026-08-09 本菲卡 vs 维塞乌（光明球场空场执行处罚 → 碾压局 2-2 爆 9 倍冷平）、2026-09-28 罗马尼亚 vs 波黑（欧足联空场处罚 → 2-4 被爆冷）

### 逐场四选一（禁止留空）

```
□ Step 1: 确认本场是否处于空场/部分关闭/中立场状态
  → 关键词（中文）："{主队名} 空场" / "{主队名} 闭门" / "{主队名} 禁止球迷" /
                    "{主队名} 看台关闭" / "{主队名} 纪律处罚" / "{主队名} 足协罚单"
  → 关键词（英文）："{主队英文名} behind closed doors" / "{主队英文名} empty stadium" /
                    "{主队英文名} stadium ban" / "{主队英文名} partial closure" /
                    "{主队英文名} UEFA sanction" / "{主队英文名} fined + stadium"
  → 客队同法搜索一遍（客队亦可为受罚方或被移师）
  → 优先来源：UEFA官网纪律处分明细 / 各国体育暴力防治机构（如葡萄牙APCVD）/
              各国足协纪律公告 / 俱乐部官网公告
  → 中文平台（雷速/懂球帝）前瞻仅作线索，**必须回溯至原始处罚公告**方可采信（规则29信源分级）
```

### 输出格式（第一级别字段，禁止留空）

```
stadium_status: "正常" | "空场" | "部分关闭" | "中立场"
closure_ratio: 0.30            # 仅"部分关闭"时填：关闭看台座位占比
actual_venue: "兰德斯球场"      # 仅"中立场/移师"时填：实际比赛场地
sanction_source: "uefa.com/disciplinary [L1]"   # "空场/部分关闭"时必填（URL+等级）
sanction_reason: "球迷烟火 / 球迷挑衅口号"       # "空场/部分关闭"时必填
sanction_scope: "本场" | "未来N场"               # "空场"时必填：处罚是否只针对本场
```

### 判定红线

| 状态 | 后续强制处置（移交审核器与总控） |
|:---|:---|
| `空场` | 主场方**撤回主场加成**（乘数置 1.0）；**禁止判定为"碾压局"**；置信度**强制降一级** |
| `部分关闭` | 关闭比例≥30% → 主场加成**折半**；<30% → 按 0.85 计 |
| `中立场/移师` | 主队主场加成置 1.0，且**客队不承担客场惩罚** |
| `正常` | 无额外处置，正常进入后续流程 |

> **报告披露要求**：场地行必须显式标注 `⚠️空场（处罚原因；处罚方）` / `⚠️部分关闭（区域/比例）` / `⚠️中立场（实际场地）`，禁止只写"容量XX"。

---

## 规则0（Step 1-3）：伤停信息官方搜索

> 来源：008索尔纳8人伤停遗漏导致用户损失800元

### 收集三步流程

```
□ Step 1: 搜索主队官方网站伤停/阵容页面
  → 关键词："{主队英文名} official website squad" / "{主队英文名} injuries"
  → 记录：所有标注为injured/suspended/absent的球员

□ Step 2: 搜索客队官方网站伤停/阵容页面
  → 关键词："{客队英文名} official website squad" / "{客队英文名} injuries"
  → 记录：同上

□ Step 3: Fotmob/Sportsmole交叉采集
  → Fotmob：查看双方球队页面的"Injuries & Suspensions"标签
  → Sportsmole：查看赛前preview的"Team News"部分
  → 记录：与官网信息对比，标注异同
```

### 收集输出格式

```
raw_injuries_home:
  - player: "Cissé"
    position: "中后卫"
    source: "aikfotboll.se/trupp"
    source_type: "official"
    raw_status: "injured"
  - player: "Wilson"
    position: "右后卫"
    source: "fotmob.com"
    source_type: "fotmob"
    raw_status: "injured"

raw_injuries_away:
  - player: "..."
    ...
```

---

## 规则26（收集部分）：5类赛前信息采集

### 必须收集的5类信息

| 类别 | 具体内容 | 数据源 |
|:---|:---|:---|
| 比赛场地 | 体育场名称、城市、草皮类型、容量、**`stadium_status`（空场/部分关闭/中立场 —— 第一级别·规则72）** | 联赛官网/Wikipedia + UEFA纪律明细/足协公告/APCVD |
| 天气情况 | 温度、天气状况、风力 | weather.com/accuweather |
| 球队近期新闻 | 转会动态、伤停恢复、战术调整、俱乐部动态、赛程因素 | 官网/Goal.com |
| 伤停详情 | 球员姓名、位置、类型、开始日期、已伤停时长、预计复出、来源URL | 官网/Fotmob/Sportsmole |
| 实际首发阵容 | 阵型、11人名单、替补席、轮换对比 | ysscores/官网（开球前1小时内） |

### 伤停详情采集字段（每名球员）

| 字段 | 说明 | 示例 |
|:---|:---|:---|
| 球员姓名 | 英文名+中文译名 | Cissé（西塞） |
| 位置 | 具体位置（后卫/中场/前锋） | 中后卫 |
| 伤停类型 | 伤病/停赛/出战成疑 | 伤病 |
| 开始日期 | 伤停开始时间 | 2026-07-20 |
| 已伤停时长 | 截至比赛日的天数 | 12天 |
| 预计复出 | 如有则填，无则填"未知" | 预计8月中旬 |
| 信息来源 | 采集URL（必须可追溯） | aikfotboll.se/trupp |
| 信息矛盾标注 | 多来源冲突时记录各方说法 | 官网称伤，球迷屋未列出 |

---

## 规则29：数据来源优先级

### 信源分级（采集时标注来源等级）

| 优先级 | 来源类型 | 标注方式 |
|:---|:---|:---|
| Level 1 | 雷速体育/sporttery.cn | `[L1]` |
| Level 1 | Goal.com/Sofascore/UEFA官网 | `[L1]` |
| Level 2 | Fotmob/fbref/footystats | `[L2]` |
| Level 3 | 球队官网/联赛官方 | `[L3]` |
| Level 4 | Sportsmole/球迷屋 | `[L4]` |
| Level 5 | 头条/搜狐/网易 | `[L5-未验证]` |

### 采集原则
1. 每条信息必须标注来源URL和来源等级
2. 优先从Level 1-3采集，Level 4仅作补充
3. Level 5来源信息也采集但标注"未验证"，交由审核核查器处理
4. 多来源采集同一信息时，全部记录，由审核核查器裁定

---

## 规则37（收集部分）：球队统计数据采集

### 必须采集的统计数据

```
□ 主客队场均进球/场均失球
  → 来源：Opta/WhoScored/Transfermarkt
  → 至少采集2个来源的数值

□ 主客队近10场xG与xGA（★ 每场必采，xG是λ校准核心输入，跳过则模型计算无效）
  → 来源：Understat / FBref / Opta（优先级递减）
  → 必须采集：近10场xG均值、实际进球均值、偏离幅度
  → 搜索关键词："{球队英文名} xG stats" / "{球队英文名} understat" / "{球队英文名} fbref"
  → 偏离>30%标注"状态不可持续信号"

□ 主客队近期战绩（近5-10场 W/D/L）
  → 来源：联赛官网/Fotmob
  → 区分主客场记录

□ ★ 双方球队总身价（独立必采字段，规则36，禁止模糊估算）
  → 来源：Transfermarkt（唯一口径）
  → 搜索方式：访问 transfermarkt.com 搜索双方球队英文名，进入俱乐部页面，记录"Total market value"字段
  → 搜索关键词："{球队英文名} transfermarkt" → 点击球队页面 → 记录总身价+来源URL
  → 必须记录：主队总身价（欧元）、客队总身价（欧元）、Transfermarkt球队页面URL
  → 禁止输出"具体总额未获取""约X亿+"等模糊表述——找不到则标注"信息缺失"并记录已搜索的平台
  → 近期有重大转会的球队：标注"Transfermarkt数值可能尚未反映最新转会"

□ 历史交锋记录
  → 来源： Transfermarkt/Fotmob
  → 总交锋+近5次，区分主客场

□ 联赛排名/积分
  → 来源：联赛官网/Fotmob
  → 当前排名、积分、距降级区/欧战区差距
```

### 采集输出格式

```
raw_stats_home:
  goals_per_game: { value: 1.45, sources: ["fbref.com/...", "transfermarkt.com/..."] }
  goals_conceded_per_game: { value: 1.12, sources: ["fbref.com/...", "transfermarkt.com/..."] }
  xG_10: { value: 14.2, sources: ["understat.com/..."] }
  xGA_10: { value: 11.8, sources: ["understat.com/..."] }
  recent_form: "WDLWW"
  home_record: "WWDWL"
  total_value: { value: "€45.2M", source: "transfermarkt.com/team/xxx [L2]", url: "https://www.transfermarkt.com/xxx/startseite/verein/xxx" }
  league_position: 6
  h2h_last5: ["2-1", "0-0", "1-2", "3-1", "0-1"]

raw_stats_away:
  goals_per_game: { value: 1.08, sources: ["fbref.com/...", "transfermarkt.com/..."] }
  goals_conceded_per_game: { value: 1.30, sources: ["fbref.com/...", "transfermarkt.com/..."] }
  xG_10: { value: 10.5, sources: ["understat.com/..."] }
  xGA_10: { value: 12.2, sources: ["understat.com/..."] }
  recent_form: "DLWDL"
  away_record: "LDWLL"
  total_value: { value: "€32.1M", source: "transfermarkt.com/team/yyy [L2]", url: "https://www.transfermarkt.com/yyy/startseite/verein/yyy" }
  league_position: 9
```

---

## 规则15（收集部分）：5类赔率采集

> 赔率是模型计算和市场分析的核心输入，必须完整采集5类玩法赔率

### 首选方式：SportteryAPI MCP服务

> **优先使用MCP服务获取全部5类赔率，一次调用即可获取所有场次的全玩法赔率数据。**
> 部署位置：本仓库 `SportteryAPI/` 子目录（相对仓库根，不写本机绝对路径），MCP服务名：`sporttery-odds`

调用方式（通过 run_mcp）：

```
server_name: sporttery-odds
tool_name: get_matches
args: { "pools": "had,hhad,crs,ttg,hafu", "date": "260815" }
```

- `pools` 参数固定为 `"had,hhad,crs,ttg,hafu"` 确保全玩法覆盖
- `date` 参数为YYMMDD格式（如周六=260815）
- 返回数据包含每场的全部31个比分赔率、8个总进球赔率、9个半全场赔率
- 11:00后所有赔率全部可获取，不存在"未开售"情况（规则58）

按matchId获取单场：
```
tool_name: get_match
args: { "matchId": 2040864 }
```

### 5类赔率及数据源（MCP为主，WebFetch为降级备选）

| 玩法 | MCP字段 | 降级数据源 | 备注 |
|:---|:---|:---|:---|
| HAD（胜平负） | `markets.had.outcomes` | sporttery.cn/jc/jsq/zqspf/ | MCP一次获取全部场次 |
| HHAD（让球胜平负） | `markets.hhad.outcomes` + `markets.hhad.goalLine` | sporttery.cn/jc/jsq/zqspf/ | **必须读取goalLine字段获取让球数**，常见值-1/-2/+1/+2/-3等 |
| CRS（比分） | `markets.crs.outcomes` | ~~sporttery.cn/jc/jsq/zqbf/~~ | **MCP可获取全部31个比分赔率，WebFetch仅首场** |
| TTG（总进球） | `markets.ttg.outcomes` | jc.zhcw.com/?act=zqjsq_zjqs | MCP一次获取全部场次 |
| HAFU（半全场） | `markets.hafu.outcomes` | sporttery.cn/jc/jsq/zqbqc/ | 9个半全场组合 |

### 采集降级策略（MCP优先）

```
□ Step 1: 优先使用 SportteryAPI MCP 获取全部5类赔率
  → 调用 get_matches，pools="had,hhad,crs,ttg,hafu"，date=当日YYMMDD
  → 一次调用获取全部场次的全玩法赔率（含31个CRS、8个TTG、9个HAFU）
  → 记录来源为"[MCP] sporttery-odds"
  → 11:00后所有赔率全部可获取（规则58）

□ Step 2: 若 MCP 不可用（未注册/服务异常），降级为 WebFetch
  → 先抓 sporttery.cn（HAD/HAFU/HTFT/TTG）
  → 再抓 jc.zhcw.com（TTG补充）
  → CRS 抓取受限：WebFetch只能获取首场，标注"待MCP/浏览器补采"

□ Step 3: 浏览器操控降级（仅当MCP和WebFetch均失败时）
  → 使用 browser_use 工具访问 sporttery.cn 比分页面
  → 逐场点击展开比分赔率面板
  → 标注来源为"[browser] sporttery.cn"
```

### 赔率采集输出格式

> **字段命名与API映射（重要！禁止混淆）：**
> | 输出字段名 | API pool代码 | 含义 | 让球数字段 |
> |:---|:---|:---|:---|
> | `had` | `had` | 胜平负 | — |
> | `hhad` | `hhad` | 让球胜平负 | `markets.hhad.goalLine` |
> | `crs` | `crs` | 比分 | — |
> | `ttg` | `ttg` | 总进球 | — |
> | `hafu` | `hafu` | 半全场 | — |
>
> **让球数（handicap）必须从API返回的 `markets.hhad.goalLine` 字段读取实际值，禁止使用默认值-1。** 常见值：-1（主让1球）、-2（主让2球）、+1（主受1球）、+2（主受2球）、-3（主让3球）等。

```
raw_odds:
  had:
    home: 1.85
    draw: 3.30
    away: 4.00
    source: "sporttery.cn [L1]"
    status: "✓完整"
  hhad:
    handicap: -1  # ← 必须从 markets.hhad.goalLine 读取实际值！-1=主让1球, -2=主让2球, +1=主受1球, +2=主受2球, -3=主让3球
    home: 3.75
    draw: 3.45
    away: 1.80
    source: "sporttery.cn [L1]"
    status: "✓完整"
  hafu:
    top3: [{ combo: "胜胜", odds: 1.26 }, { combo: "平胜", odds: 4.70 }, { combo: "平平", odds: 40.00 }]
    source: "sporttery.cn [L1]"
    status: "✓完整"
  ttg:
    top2: [{ goals: 3, odds: 4.30 }, { goals: 2, odds: 6.20 }]
    source: "jc.zhcw.com [L1]"
    status: "✓完整"
  crs:
    top5: [{ score: "2:0", odds: 4.20 }, { score: "3:0", odds: 4.30 }, ...]
    source: "sporttery.cn [browser]"
    status: "✓完整（浏览器采集）"
    # 或 status: "⚠️仅首场（WebFetch限制）" → 交由审核器在11:00后浏览器补采
  single_match: true   # 该场HAD是否开放"单关"（规则63，v2.3.4）：**由用户赛前告知填充，不再自动检测**；用户明确告知某场开单关才置true，未告知一律false
```

### 赔率采集时间窗口

| 时间段 | 可采集玩法 | 说明 |
|:---|:---|:---|
| 赛前一天 上午 | HAD / HAFU | sporttery.cn 通常上午已更新 |
| 赛前一天 下午 | + HTFT | 半全场赔率更新稍晚 |
| 赛前一天 11:00后 | + TTG / CRS | 总进球和比分赔率最晚更新 |
| 赛前1小时 | 全部5类 | 最终确认赔率，可能微调 |

> **注意：** 11:00以前 TTG 和 CRS 可能尚未更新，应在11:00后重新采集。

---

## 采集完成标准

```
【第一级别·必须最先打勾，未打勾禁止输出预测】
□ ★★ 空场/中立场状态已逐场确认（stadium_status 四选一，禁止留空；空场/部分关闭须有 sanction_source+sanction_reason）？
□ ★ 主客队伤停信息已从≥2个来源采集？
□ ★ 5类赛前信息（场地/天气/新闻/伤停/首发）全部已采集？
□ 每条信息均标注了来源URL和来源等级？
□ 球队统计数据（场均进球/失球/xG/战绩/交锋/排名）已采集？
□ ★ 双方球队总身价已从Transfermarkt采集？主队+客队均有具体数值和来源URL？——禁止"具体总额未获取""约X亿+"等模糊表述，找不到标注"信息缺失"
□ ★ xG数据已采集（近10场xG均值+实际进球均值+偏离幅度）？——跳过则模型计算无效
□ 多来源矛盾信息已全部记录（不裁定，交由审核核查器）？
□ 缺失字段已标注"信息缺失"（禁止编造）？
□ 5类赔率（HAD/HHAD/CRS/TTG/HAFU）已采集并标注状态？
□ 该场HAD是否开"单关"（single_match字段，规则63）：**由用户赛前告知填充，不再自动检测**？
□ 赔率采集优先使用MCP（sporttery-odds），MCP不可用时降级WebFetch？
□ 网友意见已从≥3个平台采集并过滤不可靠内容？
```

---

## 信息过滤规则（来自 football_SKILL.md，采集时同步执行）

> 信息收集不只是"找到信息"，还要"过滤噪音"。以下内容在采集阶段同步标记过滤。

### 必须过滤的内容

| 类型 | 识别特征 | 处理方式 |
|:---|:---|:---|
| 小编类不可靠建议 | 标题含"小编推荐""独家内幕""稳胆""必中""带飞" | 标记不可靠，排除 |
| 假博彩引流贴 | 含不明链接/二维码/微信号/"加群""私聊推单""包赔""充值送彩金" | 一律过滤 |
| 纯情绪化内容 | 仅有"冲冲冲""干就完了"等无分析实质的水帖 | 标记但不完全排除，仅供情绪参考 |
| 洗稿回音壁内容 | 多个中文平台内容高度雷同（互相洗稿） | 标注"回音壁"，降权 |

### 来源可靠性评级

| 等级 | 标注 | 来源类型 |
|:---|:---|:---|
| A | `[A-官方]` | 联赛官网/俱乐部官网/UEFA官网 |
| B | `[B-专业]` | Opta/WhoScored/Transfermarkt/FBref/Understat |
| C | `[C-平台]` | 懂球帝/雷速/Fotmob/Goal.com |
| D | `[D-个人]` | 个人分析/自媒体/知乎个人 |
| E | `[E-可疑]` | 头条/搜狐/球迷屋（标注"未验证"） |

### 网友意见采集规范

```
□ 至少采集3个不同平台的观点（虎扑/知乎/微博等）
□ 过滤小编类和博彩引流类内容
□ 记录球迷情绪倾向比例（如"主胜60%/平局25%/客胜15%"）
□ 标注采集时间和来源URL
□ 中文平台内容互相洗稿时标注"回音壁"，仅取独立信源
```

> **采集完成后，输出移交至 [agents/information_verifier.md](information_verifier.md) 进行审核核查。**
