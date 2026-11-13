# 竞彩足球分析系统（Football Analysis）

一套面向中国竞彩足球的**全流程量化分析流水线**：抓取官方赛程与赔率 → 用多模型融合计算概率 → 产出知乎风格分析报告 → 生成合规的串关方案与虚构资金模拟盘台账 → 次日以官方赛果回测并沉淀教训。

> ⚠️ **免责声明**：本项目仅用于数据分析方法与工程实践的研究，全部输出**不构成任何投注建议**。仓库中 `reports/sim/` 下的凯利模拟盘使用**虚构本金**，非真实资金，不产生真实盈亏。请遵守当地法律法规，理性看待体育竞猜。

---

## 一、项目能做什么

- **六维推荐**：胜平负方向、让球、比分 TOP5、总进球、半全场 TOP3、半场比分 TOP3，外加大小球方向与六档分档（闷战/小球/常规/大球/超大球/穿盘）。
- **模型融合**：Dixon-Coles、双变量泊松、负二项、ZIP、Skellam、蒙特卡洛，配合积分榜进失球推导攻防强度（`lottery_agent/fundamental.py`），赔率仅用于去水后对照分歧与 EV 计算。
- **报告产出**：分析报告（知乎 Markdown）、回测报告、串关方案（稳健/搏冷/娱乐三大类）。
- **风险管理**：1/4 凯利注额、单注与单日上限、串关不入模拟盘、单关上修拦截。
- **闭环回测**：每期用官方赛果复算全部维度命中率，生成教训条目并进入 `memory/lessons/`。

配套的**规则手册**是根目录的 [AGENTS.md](AGENTS.md)，包含全部 88 条流程规则、模板口径与审核标准；报告模板在 `templates/`，子 Agent 职责在 `agents/`。

---

## 二、目录结构

```
football/
├── AGENTS.md                 # 规则手册（主协调器，88 条流程规则）
├── run_agent.py              # 主入口（单场/多场批量分析）
│
├── agents/                   # 子 Agent 职责定义（信息收集/审核/建模/串关/报告/审计）
├── templates/                # 报告模板（知乎分析、知乎回测、推特）
├── docs/                     # 数学模型理论文档
│
├── lottery_agent/            # 核心代码包
│   ├── models.py             # 数学模型库（DC/NB/ZIP/Skellam/MC）
│   ├── fundamental.py        # 由基本面推导 λ（禁止赔率反解概率）
│   ├── analyzer.py           # 单场八维分析引擎
│   ├── multi_analyzer.py     # 批量分析 + 串关优化
│   └── report_generator.py   # HTML 报告生成
│
├── scripts/
│   ├── audit_report_check.js # 报告机械校验（分析 13 项 / 回测 14 项）
│   └── daily/                # 每日一次性流水脚本（取数/建模/生成/回测，按日期命名）
│
├── SportteryAPI/             # 体彩赔率服务（Cloudflare Worker + 本地 MCP）
├── sporttery_bridge/         # 赔率服务调用桥（MCP/REST/直连多路回退）
├── football_mcp/             # 足球数据 MCP 工具统一入口（CLI / Python / MCP）
│
├── reports/
│   ├── analysis/             # 分析报告（按销售日）
│   ├── backtest/             # 回测报告
│   ├── data/                 # 赔率/模型/赛果等机读底稿
│   └── sim/                  # 虚构资金模拟盘台账（kelly_sim_ledger.json / .md）
│
├── memory/
│   ├── predictions/          # 每期预测底稿（prediction.json）
│   ├── lessons/              # 回测教训（LESSONS_INDEX.md）
│   ├── leagues/              # 联赛特征知识库
│   ├── audit/                # 独立审核记录
│   └── trials/               # 试用期规则台账
│
└── archive/                  # 历史一次性产物（旧版报告/早期专题分析/临时数据）
```

---

## 三、快速开始

环境：Python 3.10+、Node.js 18+（无需额外依赖的脚本可直接运行）。

```bash
# 单场/批量分析（示例数据）
python run_agent.py --demo

# 报告机械校验（分析报告 13 项 / 回测报告 14 项）
node scripts/audit_report_check.js reports/analysis/<报告>.md

# 调用足球数据 MCP（仓库根目录执行）
node football_mcp/bin/football-mcp.mjs call <服务id> <工具名> --args-file args.json
```

> `scripts/daily/` 下的脚本为**当日一次性流水**，路径按仓库根目录解析，需在根目录执行（`.py` 用 `python`、`.js` 用 `node`，具体参数见脚本头部注释）。

---

## 四、数据来源

| 用途 | 来源 |
|:---|:---|
| 赛程、赔率、赛果 | 中国体育彩票官方接口（`SportteryAPI`），赛果以 `getUniformMatchResultV1` 快照为准 |
| 补充赛况/统计 | ESPN、football-data.co.uk、联赛官方积分榜 |
| 联赛特征 | `memory/leagues/`（半场平局率、场均进球等） |

所有赛果须来自官方接口，禁止用外部比分顶替；待结算场次必须为 0 才允许出回测结论。

---

## 五、每日流程（简版）

1. **取数**：确认销售日与在售场次，抓取赔率、积分榜、伤停、场地状态。
2. **建模**：基本面 → λ → 多模型融合 → 六维概率。
3. **出报告**：按模板写分析报告，同步落 `memory/predictions/` 机读底稿。
4. **模拟盘**：按风控参数产出注单，写入 `reports/sim/kelly_sim_ledger.json`（虚构资金）。
5. **次日回测**：官方赛果结算全部注单、复算命中率、生成教训、更新索引。

流程细节与审核标准见 `AGENTS.md`；报告审计采用**撰写方与审核方分离**，审核记录落在 `memory/audit/`。

---

## 六、仓库说明

- 本仓库随分析进度持续更新；`archive/` 中的早期产物仅作留档，不代表当前方法口径。

- 规则与口径以根目录 `AGENTS.md` 为唯一权威。
