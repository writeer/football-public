// 足球相关 MCP 服务器注册表
//
// 每项描述一个可被程序直接拉起的 MCP 服务：
//   id       程序内唯一标识（CLI / Python 都用它）
//   title    中文名
//   category 分类（用于文档归组）
//   command/args/env/cwd  stdio 启动参数
//   ide      写进 IDE mcp.json 的条目（**只允许相对路径**，便于仓库迁移）
//   localFile repo 内被 IDE 直接引用的文件（相对仓库根），`print-config --resolve` 时展开为绝对路径
//   note     备注（依赖、密钥、数据范围）
//   tools    工具中文速查（仅文档用途，实时清单以 tools/list 为准）
//
// 仓库内所有配置文件一律不含绝对路径；绝对路径只在运行时由本文件按自身位置推导。

import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, "..");
export const PROJECT_ROOT = path.resolve(ROOT, "..");
const SPORTTERY_DIR = path.join(PROJECT_ROOT, "SportteryAPI");
const SPORTTERY_SERVER = "SportteryAPI/mcp/server.ts";

export const SERVERS = [
  {
    id: "sporttery-odds",
    title: "体彩竞彩官方赔率（本地服务）",
    category: "core",
    command: "node",
    args: ["--no-warnings", "--experimental-strip-types", "mcp/server.ts"],
    cwd: SPORTTERY_DIR,
    ide: {
      command: "node",
      args: ["--no-warnings", "--experimental-strip-types", SPORTTERY_SERVER],
    },
    localFile: SPORTTERY_SERVER,
    env: {},
    note: "本地 stdio 服务，需 Node>=22.6 且 SportteryAPI 已 npm install；体彩5类赔率首选数据源。",
    tools: {
      get_matches: "当日/指定日期全部竞彩场次 + 全玩法赔率（had/hhad/crs/ttg/hafu）",
      get_match: "按 matchId 取单场全玩法赔率",
      derive_odds: "赔率推导：隐含/去水概率、返还率、公平赔率",
      compare_value: "凯利指数与价值对比",
      calc_parlay: "单关/过关奖金计算（M串N）",
      list_parlay_types: "过关方式对照表",
      get_meta: "玩法标签、公式参考",
    },
  },
  {
    id: "football-charts",
    title: "football-charts 联赛图表数据",
    category: "league-data",
    command: "npx",
    args: ["-y", "footballcharts-mcp"],
    env: {},
    note: "覆盖93个联赛（含低级别），提供积分榜/赛果/赛程/赛季投影/进球时间/战绩记录；不含实时比分、球员和赔率。",
    tools: {
      about_football_charts: "数据覆盖范围与联赛 key / season 写法说明（首次使用建议先调）",
      list_leagues: "可用联赛清单",
      get_league_table: "联赛积分榜",
      get_results: "已完赛结果",
      get_fixtures: "赛程",
      get_match: "单场详情",
      get_team: "球队资料",
      get_goal_timing: "进球时间分布",
      get_season_projection: "赛季走势/最终排名投影",
      get_track_record: "历史预测命中记录",
    },
  },
  {
    id: "betbetter-odds",
    title: "betbetter 模型选场（模型推算）",
    category: "model",
    command: "npx",
    args: ["-y", "betbetter-mcp"],
    env: {},
    note: "仅为模型输出（估算胜率/公平赔率/置信标签），不含博彩公司真实价格；足球支持 epl/la-liga/serie-a/bundesliga/ligue-1/world-cup。",
    tools: {
      get_model_picks: "联赛模型评级选场（胜率、公平赔率、HIGH/LEAN/LONG-SHOT）",
      list_leagues: "支持的联赛",
      find_fixture: "按球队/联赛查找比赛",
    },
  },
  {
    id: "football-docs",
    title: "足球数据源文档库",
    category: "docs",
    command: "npx",
    args: ["-y", "football-docs"],
    env: {},
    note: "足球数据供应商文档检索（Opta/StatsBomb/Sofascore/TheSportsDB 等），用于核对指标定义、事件类型、坐标系；含论文与网页来源。",
    tools: {
      search_docs: "检索数据源文档（事件类型、qualifier、接口、坐标体系）",
      list_providers: "已索引数据源清单",
      get_provider_docs: "某数据源文档全文",
      compare_providers: "数据源对比",
      resolve_provider_id: "数据源别名解析",
      list_metrics: "指标清单",
      get_metric: "指标定义（xG、PPDA 等）",
      resolve_entity: "球队/球员实体解析",
      search_papers: "论文检索",
      get_paper: "论文详情",
      read_paper: "读取论文全文或指定章节（arXiv/开放获取/SportRxiv，本地库命中不再联网）",
      add_local_paper: "登记本地论文（用户自备文件）",
      forget_paper: "从本地论文库移除",
      match_quote: "原文引用定位",
      get_web_source: "网页来源内容",
      purge_cache: "清理文档/论文缓存",
      request_update: "提交文档新增/重爬/过时标记请求",
    },
  },
  {
    id: "odds-api",
    title: "The Odds API 外围赔率",
    category: "odds",
    command: "npx",
    args: ["-y", "@pipeworx/mcp-odds-api"],
    env: { ODDS_API_KEY: process.env.ODDS_API_KEY ?? "test" },
    note: "外围盘口赔率（用于市场情绪参考，规则28：不作为决策依据）。必须配置真实 ODDS_API_KEY，否则调用会鉴权失败；每次 get_odds 消耗配额。",
    tools: {
      list_sports: "运动项目清单（找 soccer_* key）",
      get_odds: "某联赛当前赔率（h2h/spreads/totals）",
      get_event_odds: "单场赔率",
      get_scores: "比分",
      get_events: "赛事清单",
      odds_api_quota: "剩余配额查询",
    },
  },
  {
    id: "mcp-sports-hub",
    title: "Sports Hub 综合体育数据",
    category: "sports-data",
    command: "npx",
    args: ["-y", "mcp-sports-hub"],
    env: {},
    note: "聚合 ESPN / TheSportsDB / sportsrc / openLiga / football-data.co.uk 等公开数据，足球相关的积分榜、赛程、球队、阵容均可用。",
    tools: {
      espn_get_scoreboard: "ESPN 比分板（含足球联赛）",
      espn_get_standings: "ESPN 积分榜",
      espn_get_team_schedule: "ESPN 球队赛程",
      espn_get_team_roster: "ESPN 球队阵容",
      espn_get_event_summary: "ESPN 单场摘要",
      espn_get_news: "ESPN 新闻",
      sportsdb_get_standings: "TheSportsDB 积分榜",
      sportsdb_get_events_by_date: "TheSportsDB 按日期取赛程",
      sportsdb_get_last_events: "TheSportsDB 最近比赛",
      sportsdb_get_next_events: "TheSportsDB 未来赛程",
      sportsdb_search_teams: "TheSportsDB 球队搜索",
      sportsrc_get_table: "sportsrc 积分榜",
      sportsrc_get_matches: "sportsrc 赛程/赛果",
      sportsrc_get_live: "sportsrc 实时比赛",
      openliga_get_table: "openLiga 积分榜（德系联赛）",
      openliga_get_matches_by_league_season: "openLiga 按赛季取比赛",
      openliga_get_top_scorers: "openLiga 射手榜",
      openliga_get_next_match_by_team: "openLiga 球队下一场",
      footballdata_uk_get_matches: "football-data.co.uk 历史比赛（含赔率列，适合回测）",
      footballdata_uk_list_leagues: "football-data.co.uk 联赛清单",
    },
  },
];

export function getServer(id) {
  const s = SERVERS.find((x) => x.id === id);
  if (!s) {
    throw new Error(`未知 MCP 服务: ${id}（可用: ${SERVERS.map((x) => x.id).join(", ")}）`);
  }
  return s;
}

/**
 * 生成标准 mcp.json 片段：**全部相对路径，可直接提交/迁移**。
 * 前提：MCP 客户端以仓库根目录为工作目录启动服务（多数客户端的默认行为）。
 */
export function toMcpJson(servers = SERVERS) {
  const mcpServers = {};
  for (const s of servers) {
    const entry = s.ide ?? { command: s.command, args: [...s.args] };
    mcpServers[s.id] = { command: entry.command, args: [...entry.args], env: { ...s.env } };
  }
  return { mcpServers };
}

/**
 * 本机绝对路径版：只用于「客户端不支持相对路径 / 工作目录不是仓库根」的兜底场景。
 * 由运行时按本文件位置推导，不入库、可随时重新生成。
 */
export function toResolvedMcpJson(servers = SERVERS) {
  const mcpServers = {};
  for (const s of servers) {
    const entry = s.ide ?? { command: s.command, args: [...s.args] };
    const args = entry.args.map((a) =>
      s.localFile && a === s.localFile ? path.join(PROJECT_ROOT, a) : a,
    );
    mcpServers[s.id] = { command: entry.command, args, env: { ...s.env } };
  }
  return { mcpServers };
}

/** 生成 VS Code Copilot 专用格式（顶层键为 servers，且需 type: stdio） */
export function toVsCodeMcpJson(servers = SERVERS) {
  const out = {};
  for (const s of servers) {
    const entry = s.ide ?? { command: s.command, args: [...s.args] };
    out[s.id] = {
      type: "stdio",
      command: entry.command,
      args: entry.args.map((a) => (s.localFile && a === s.localFile ? `\${workspaceFolder}/${a}` : a)),
      env: { ...s.env },
    };
  }
  return { servers: out };
}
