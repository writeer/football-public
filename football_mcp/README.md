# football_mcp — 足球相关 MCP 服务统一配置与直调接口

> 版本 1.1.0 | 建立 2026-10-15
> 作用：把本项目用到的 **6 个足球相关 MCP 服务** 集中登记在一处，并提供一个 **不依赖任何 IDE 配置** 的程序直调入口。
> 换句话说：**换电脑、换 IDE、换 Agent，只要克隆本仓库 + 装好 Node，就能直接调用这些 MCP 工具。**
>
> **全模块零绝对路径**：所有配置文件、代码、文档里都不出现任何盘符开头的本机路径；需要真实路径的地方一律在运行时按"文件自身所在位置"推导，因此整个仓库可以随意移动、改名、换盘符。

---

## 一、为什么需要这个目录

MCP 工具以往只能在 IDE 的 `mcp.json` 里配置，再由 IDE 的 Agent 调用。问题有三个：

1. 换 IDE（Trae / Cursor / Claude Code / VS Code）就要重新配一遍，路径写错就静默失效；
2. Python 脚本、定时任务、CI 无法使用这些工具，因为没人替它拉起 MCP 服务进程；
3. 服务清单散落在各处，忘记某个服务的用途和数据边界，容易用错数据源。

本目录用三层结构解决：

| 层 | 文件 | 作用 |
|:---|:---|:---|
| 配置层 | [`mcp.json`](mcp.json) | 标准 `mcpServers` 片段（**纯相对路径**），可直接粘贴进任意 IDE |
| 注册层 | [`lib/registry.mjs`](lib/registry.mjs) | 6 个服务的启动参数 + 中文用途 + 工具速查（唯一事实来源） |
| 调用层 | [`bin/football-mcp.mjs`](bin/football-mcp.mjs)、[`python/football_mcp_client.py`](python/football_mcp_client.py) | CLI / Python 直调，自建 MCP 客户端，无需 IDE |

配置由注册表生成，二者不会漂移（命令均在仓库根目录执行）：

```powershell
node football_mcp/bin/football-mcp.mjs print-config            # 相对路径版（默认，入库/迁移用这个）
node football_mcp/bin/football-mcp.mjs print-config --vscode   # VS Code 格式（${workspaceFolder}）
node football_mcp/bin/football-mcp.mjs print-config --resolve  # 本机绝对路径版，兜底用，勿提交
```

**相对路径的前提**：MCP 客户端以仓库根目录为工作目录启动服务（多数客户端如此）。除 `sporttery-odds` 这个本地服务外，其余 5 个走 `npx`，本身与路径无关，放哪都能跑。

---

## 二、已登记的 6 个足球 MCP 服务

| id | 名称 | 数据范围 | 关键工具 | 备注 |
|:---|:---|:---|:---|:---|
| `sporttery-odds` | 体彩竞彩官方赔率（本地） | 中国体彩竞彩 5 类玩法赔率 + 衍生指标 | `get_matches` `get_match` `derive_odds` `compare_value` `calc_parlay` `list_parlay_types` `get_meta` | 本项目**首选赔率源**；需 Node≥22.6 且 `SportteryAPI/` 已 `npm install` |
| `football-charts` | football-charts 联赛图表 | 93 个联赛（含低级别）积分榜/赛果/赛程/赛季投影/进球时间/历史命中记录 | `get_league_table` `get_results` `get_fixtures` `get_goal_timing` `get_season_projection` `get_track_record` `list_leagues` | 不含实时比分、球员、伤停、赔率 |
| `betbetter-odds` | betbetter 模型选场 | 模型估算胜率/公平赔率/置信标签（足球含 epl/la-liga/serie-a/bundesliga/ligue-1/world-cup） | `get_model_picks` `find_fixture` `list_leagues` | **仅模型输出，不含真实盘口**；可作模型对照 |
| `football-docs` | 足球数据源文档库 | Opta/StatsBomb/Sofascore/TheSportsDB 等供应商文档、指标定义、论文 | `search_docs` `list_providers` `get_metric` `resolve_entity` `search_papers` `read_paper` | 用于核对指标口径（xG/PPDA）、事件类型、坐标系 |
| `odds-api` | The Odds API 外围赔率 | 外围盘口赔率、比分、赛事 | `list_sports` `get_odds` `get_event_odds` `get_scores` `get_events` `odds_api_quota` | 需真实 `ODDS_API_KEY`；按规则28**仅作市场情绪参考，不作决策依据**；调用消耗配额 |
| `mcp-sports-hub` | Sports Hub 综合体育数据 | ESPN / TheSportsDB / sportsrc / openLiga / football-data.co.uk 聚合（共 165 个工具） | `espn_get_standings` `sportsdb_get_standings` `sportsrc_get_table` `openliga_get_table` `footballdata_uk_get_matches` `espn_get_team_schedule` `espn_get_team_roster` … | 足球相关约 20 个工具；`footballdata_uk_*` 含历史赔率列，**适合回测** |

> 数据源优先级仍按项目规则29：**比赛统计以体彩/sporttery.cn、雷速为首选**；本目录的 npx 服务属于第三方公开数据，用于交叉验证，冲突时以更权威信源为准并降到较低置信度。

---

## 三、配置方法（IDE 侧）

### 3.1 一键拿到配置

```powershell
node football_mcp/bin/football-mcp.mjs print-config   # 在仓库根目录执行
```

输出即可直接用；也可以直接复制本目录的 [`mcp.json`](mcp.json)（内容一致，**只含相对路径**）。若客户端要求绝对路径，见 3.3 第 2 条。

### 3.2 各 IDE 的配置文件位置

| IDE / 客户端 | 文件位置 | 顶层键 |
|:---|:---|:---|
| **Trae / Trae CN**（本机已用） | `%APPDATA%\Trae CN\User\mcp.json`（国际版为 `%APPDATA%\Trae\User\mcp.json`） | `mcpServers` |
| Cursor | 全局 `%USERPROFILE%\.cursor\mcp.json`；项目级 `<仓库>\.cursor\mcp.json` | `mcpServers` |
| Claude Code | 项目级 `<仓库>\.mcp.json`；或 `claude mcp add` | `mcpServers` |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` | `mcpServers` |
| Windsurf | `%USERPROFILE%\.codeium\windsurf\mcp_config.json` | `mcpServers` |
| VS Code（Copilot Agent） | `<仓库>\.vscode\mcp.json` | **`servers`**，每项带 `"type": "stdio"`，路径用 `${workspaceFolder}` |

> **合并而不是覆盖**：这些文件可能已存在其他服务（本机 Trae 里就有"发现报告"），请把本模块的条目**追加**进去，不要整文件替换。
> 表里的 `%APPDATA%` / `%USERPROFILE%` 是系统环境变量，跟着系统走，不是写死的本机路径，迁移后照旧有效。

### 3.3 迁移与相对路径说明

1. **仓库内零绝对路径**：`mcp.json`、注册表、CLI、Python 客户端、本 README 都不含盘符路径。注册表在运行时按自身位置算出真实路径（`fileURLToPath(import.meta.url)`），Python 客户端同理（`Path(__file__).resolve().parent`）。所以把仓库挪到别的盘、改个目录名，一切照旧。
2. **只有两种情况需要把路径“固定”下来**（都是客户端限制，不是本模块要求）：
   - 客户端不支持相对路径（表现为 `sporttery-odds` 一连接就报 `ENOENT` / `Cannot find module`）：运行 `print-config --resolve` 生成**本机绝对路径版**，粘贴进该客户端的配置即可。此文件**不入库**，换机器重新生成一次。
   - VS Code：用 `print-config --vscode`，里面用官方变量 `${workspaceFolder}/SportteryAPI/mcp/server.ts`，仍是可迁移写法。
3. **更省事的做法**：IDE 配置只对 IDE 内的 Agent 有用。脚本 / 定时任务 / 其它 IDE 里的代码，直接用第四节的三套接口（CLI / Python / Node import），完全绕开 IDE 配置，也就不存在路径问题。
4. **npx 首次启动会下载包**：第一次调用 `football-charts` 等会等几秒到几十秒（之后走 npm 缓存），IDE 里表现为"连接慢"，属正常。`odds-api` 若没配真实 `ODDS_API_KEY` 会鉴权失败，非连接故障。

---

## 四、程序直接调用（核心：不用配任何 IDE）

### 4.1 CLI（任意语言都能调，输入输出都是 JSON）

```powershell
# 以下命令在仓库根目录执行（也可先 cd football_mcp，再把前缀换成 bin/）

node football_mcp/bin/football-mcp.mjs servers                            # 列出全部服务（--json 输出机器可读）
node football_mcp/bin/football-mcp.mjs ping football-charts               # 连通性 + 工具数
node football_mcp/bin/football-mcp.mjs tools football-charts              # 实时工具清单（名称/描述/参数/必填）
node football_mcp/bin/football-mcp.mjs call football-charts get_league_table --args-file args.json
node football_mcp/bin/football-mcp.mjs call sporttery-odds get_matches --args "{\"pools\":\"had,hhad,crs,ttg,hafu\"}"
node football_mcp/bin/football-mcp.mjs self-test                          # 6 个服务全量自测（--quick 只测 core）
```

约定：

- stdout 恒为单行 JSON：`{"success":true,"server":...,"tool":...,"ms":...,"data":...}`；失败时 `success:false` 且 **退出码 2**，可直接被脚本判断。
- 含中文或复杂嵌套的参数**一律用 `--args-file`**（Windows 命令行引号/编码极易出错）；文件带 UTF-8 BOM 也能解析。
- `--timeout` 单位为毫秒，默认 120000；npx 冷启动建议给到 180000。

### 4.2 Python（推荐，lottery_agent / 脚本 / 定时任务直接 import）

```python
import sys
from pathlib import Path

# 脚本放在仓库根目录下运行 → 直接用相对路径
sys.path.insert(0, str(Path("football_mcp/python").resolve()))
# 脚本在子目录里（如 lottery_agent/xxx.py）→ 相对本文件定位，仍不写死绝对路径
# sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "football_mcp" / "python"))

from football_mcp_client import list_servers, list_tools, call_tool, ping, self_test, print_config

list_servers()                                                   # 服务清单
ping("sporttery-odds")                                           # {"success":True,"toolCount":7,...}
list_tools("football-charts")                                    # 实时工具清单
print_config()                                                   # 生成相对路径版 mcp.json（迁移用）
# print_config(vscode=True)                                      # VS Code 格式
# print_config(resolve=True)                                     # 本机绝对路径版（兜底，勿入库）

# 体彩赔率 + 赔率推导（去水概率 / 公平赔率）
res = call_tool("sporttery-odds", "get_matches", {"pools": "had,hhad,crs,ttg,hafu"})
d = call_tool("sporttery-odds", "derive_odds", {"odds": [1.44, 3.90, 5.60]})

# 联赛数据交叉验证（football-charts 的联赛 key 用 'premier' 这类，不是 'epl'）
table = call_tool("football-charts", "get_league_table", {"league": "premier"})

# 历史比赛+赔率（回测用；season 为 4 位赛季码，"2425" = 2024-25）
hist = call_tool("mcp-sports-hub", "footballdata_uk_get_matches",
                 {"league": "E0", "season": "2425", "limit": 30})
```

命令行直跑（调试用，仓库根目录执行）：`python football_mcp/python/football_mcp_client.py ping football-charts`

失败时抛出 `FootballMcpError`，含 `server` / `tool` / `message`（原始错误来自 MCP 服务，例如参数不合法会明确说 `No data for league "epl"`）。

### 4.3 Node / ESM 直接 import

```js
// 位于仓库内的脚本：用相对路径 import
import { McpClient } from "./football_mcp/lib/mcp-client.mjs";
import { getServer } from "./football_mcp/lib/registry.mjs";

const client = new McpClient(getServer("football-charts"));
await client.connect();
console.log((await client.listTools()).map((t) => t.name));
console.log(await client.callTool("get_league_table", { league: "premier" }));
client.dispose();
```

同一个 client 对象可连续调用多个工具（长连接），比每次走 CLI 更快。

---

## 五、实测记录（2026-10-15）

`node bin/football-mcp.mjs self-test` 结果：

| 服务 | 连接 | 工具数 | 耗时 |
|:---|:---:|:---:|:---:|
| sporttery-odds | OK | 7 | 686 ms |
| football-charts | OK | 10 | 2666 ms |
| betbetter-odds | OK | 3 | 2578 ms |
| football-docs | OK | 17 | 3372 ms |
| odds-api | OK | 6 | 2921 ms |
| mcp-sports-hub | OK | 165 | 2971 ms |

真实调用验证：
- `sporttery-odds.derive_odds([1.44,3.90,5.60])` → 返还率 88.54%，公平赔率 1.6264 / 4.4048 / 6.3248
- `football-charts.get_league_table({league:"premier"})` → 返回 2026-2027 赛季英超积分榜（已过 6 轮）
- `mcp-sports-hub.footballdata_uk_get_matches({league:"E0",season:"2425"})` → 返回 380 场英超历史比赛（含比分、半场比分、射门、角球、赔率列）
- Python 接口：`list_servers / ping / list_tools / call_tool / print_config` 全部实测通过
- 配置可迁移性：默认 `print-config` 输出**只含相对路径**，与仓库内 `mcp.json` 完全一致；`--vscode` 输出 `${workspaceFolder}/SportteryAPI/mcp/server.ts`；`--resolve` 才产生本机绝对路径并在 stderr 提示不得入库

---

## 六、故障排查

| 现象 | 原因 | 处理 |
|:---|:---|:---|
| `mcp server exited` / `Cannot find module` | `SportteryAPI/node_modules` 缺失 | `cd ..\SportteryAPI && npm install` |
| `--experimental-strip-types` 报错 | Node < 22.6 | 升级 Node（本机 v24.15.0 正常） |
| npx 服务长时间卡住 | 首次下载包 / 网络受限 | 先手动预装：`npx -y footballcharts-mcp --help`；或配 npm 代理 |
| `odds-api` 报鉴权/配额 | `ODDS_API_KEY` 无效或额度用尽 | 设置真实 key（注册层面 `env: {"ODDS_API_KEY":"..."}`），或用 `odds_api_quota` 查额度 |
| 中文参数解析失败 | Windows 命令行编码 | 改用 `--args-file` |
| 工具返回 `No data for league "xxx"` | 联赛 key 写错 | 先 `list_leagues`（football-charts 的 key 形如 `premier`/`spain1`，不是 `epl`） |
| 全部服务失败 | Node 版本/网络/依赖全挂 | `self-test` 看逐项错误，按上表定位 |

---

## 七、与其他模块的关系

- [`SportteryAPI/`](../SportteryAPI)：体彩赔率服务本体（本地 MCP server 的源码所在）。
- [`sporttery_bridge/`](../sporttery_bridge)：针对 **SportteryAPI 一家** 的多方法回退桥（mcp → rest → direct）。**赔率类调用继续走它**（有回退链，更稳）。
- **本目录**：面向 **全部足球 MCP 服务** 的配置 + 直调入口，并补上 `sporttery_bridge` 未覆盖的联赛数据、数据源文档、外围赔率三大类。
- 使用这些数据时仍受 `AGENTS.md` 规则约束：规则28（基本面优先，市场赔率仅参考）、规则29（统计以体彩/雷速为首选）、规则37（统计数据需≥2 个独立来源交叉验证）。
