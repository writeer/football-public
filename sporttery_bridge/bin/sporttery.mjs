#!/usr/bin/env node
// sporttery_bridge 统一 CLI
//
// 用法：
//   node bin/sporttery.mjs <command> [options] [--method <id> | --chain a,b,c]
//
// 命令：
//   matches      [--pools had,hhad,crs,ttg,hafu] [--date 260821] [--league 英超] [--matchId N]
//   match        <matchId>
//   meta
//   parlay-types [--matches N]
//   derive       --odds 1.44,3.9,5.6 | --h 1.44 --d 3.9 --a 5.6 | --body-file x.json
//   value        --offered 2.1,3.4,3.8 --reference 2.0,3.5,4.0 [--labels 主胜,平,主负]
//   parlay       --body '{"legs":[{"odds":1.44},{"odds":2.1}]}' | --body-file x.json
//   self-test    [--chain a,b,c]   每个方法跑一组代表性命令并出报告
//   methods                       快速可用性探测
//   help
//
// 输出：JSON 到 stdout（机器可读）；诊断走 stderr。退出码 0=成功，2=全部方法失败。

import { readFile } from "node:fs/promises";
import { dispatch, resolveChain, probeMethods, METHODS } from "../lib/dispatch.mjs";
import { runSelfTest } from "../lib/selftest.mjs";

function parseArgs(argv) {
  const flags = {};
  const positionals = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--") {
      positionals.push(...argv.slice(i + 1));
      break;
    }
    if (a.startsWith("--")) {
      const eq = a.indexOf("=");
      if (eq > 0) {
        flags[a.slice(2, eq)] = a.slice(eq + 1);
        continue;
      }
      const key = a.slice(2);
      const nxt = argv[i + 1];
      if (nxt !== undefined && !nxt.startsWith("--")) {
        flags[key] = nxt;
        i++;
      } else {
        flags[key] = true;
      }
    } else if (a.startsWith("-") && a.length > 1) {
      flags[a.slice(1)] = true;
    } else {
      positionals.push(a);
    }
  }
  return { flags, positionals };
}

function num(v, name) {
  const n = Number(v);
  if (!Number.isFinite(n)) throw new Error(`${name} must be a number, got "${v}"`);
  return n;
}

function numList(v, name) {
  return String(v)
    .split(",")
    .map((s) => {
      const n = Number(s.trim());
      if (!Number.isFinite(n)) throw new Error(`${name}: bad number "${s}"`);
      return n;
    });
}

async function bodyFromFlags(flags) {
  if (flags["body-file"]) return JSON.parse(await readFile(flags["body-file"], "utf8"));
  if (flags.body) return JSON.parse(flags.body);
  return undefined;
}

const COMMANDS = {
  async matches(flags) {
    const params = {};
    if (flags.pools !== undefined) params.pools = flags.pools;
    if (flags.date !== undefined) params.date = flags.date;
    if (flags.league !== undefined) params.league = flags.league;
    if (flags.matchId !== undefined) params.matchId = num(flags.matchId, "matchId");
    return params;
  },
  async match(flags, pos) {
    if (!pos.length) throw new Error("match: need <matchId>");
    return { matchId: num(pos[0], "matchId") };
  },
  async meta() {
    return {};
  },
  async "parlay-types"(flags) {
    const params = {};
    if (flags.matches !== undefined) params.matches = num(flags.matches, "matches");
    return params;
  },
  async derive(flags) {
    const body = await bodyFromFlags(flags);
    if (body) return body;
    const params = {};
    if (flags.odds !== undefined) params.odds = numList(flags.odds, "odds");
    else {
      if (flags.h === undefined || flags.d === undefined || flags.a === undefined) {
        throw new Error("derive: 需要 --odds 1.44,3.9,5.6 或 --h/--d/--a 或 --body/--body-file");
      }
      params.h = num(flags.h, "h");
      params.d = num(flags.d, "d");
      params.a = num(flags.a, "a");
    }
    return params;
  },
  async value(flags) {
    const body = await bodyFromFlags(flags);
    if (body) return body;
    if (flags.offered === undefined || flags.reference === undefined) {
      throw new Error("value: 需要 --offered 与 --reference（逗号分隔赔率）或 --body/--body-file");
    }
    const params = {
      offered: numList(flags.offered, "offered"),
      reference: numList(flags.reference, "reference"),
    };
    if (flags.labels !== undefined) params.labels = String(flags.labels).split(",").map((s) => s.trim());
    return params;
  },
  async parlay(flags) {
    const body = await bodyFromFlags(flags);
    if (!body) throw new Error("parlay: 需要 --body '{\"legs\":[...]}' 或 --body-file x.json");
    return body;
  },
};

const USAGE = `sporttery_bridge — SportteryAPI 统一调用桥（回退链: mcp -> rest -> direct）

用法:
  node bin/sporttery.mjs <command> [options] [--method <id> | --chain a,b,c]

命令:
  matches      [--pools had,hhad,crs,ttg,hafu] [--date 260821] [--league 英超] [--matchId N]
  match        <matchId>
  meta
  parlay-types [--matches N]
  derive       --odds 1.44,3.9,5.6 | --h 1.44 --d 3.9 --a 5.6 | --body-file x.json
  value        --offered 2.1,3.4,3.8 --reference 2.0,3.5,4.0 [--labels 主胜,平,主负]
  parlay       --body '{"legs":[{"odds":1.44},{"odds":2.1}]}' | --body-file x.json
  self-test    [--chain a,b,c]   全方法自测报告
  methods                       快速可用性探测
  help

方法:
  mcp      MCP stdio 服务（spawn mcp/server.ts，7 工具）
  rest     本地 REST（默认 http://127.0.0.1:8787；REST_BASE 可指向线上 Worker）
  direct   直接 Node 库调用（零服务，本机直连上游）

环境变量:
  SPORTTERY_METHOD=mcp,rest,direct   自定义默认回退链
  REST_BASE=...                      切换 REST 目标（本地/线上 Worker）
  API_KEY=...                        服务端开启鉴权时携带`;

async function main() {
  const { flags, positionals } = parseArgs(process.argv.slice(2));
  const command = positionals[0];
  const opts = {};
  if (flags.method) opts.method = flags.method;
  if (flags.chain) opts.chain = flags.chain;

  try {
    if (command === "help" || !command) {
      console.log(USAGE);
      process.exitCode = 0;
      return;
    }
    if (command === "methods") {
      const list = await probeMethods();
      console.log(JSON.stringify({ success: true, methods: list }, null, 2));
      return;
    }
    if (command === "self-test") {
      const chain = resolveChain(opts);
      const report = await runSelfTest(chain);
      console.log(JSON.stringify({ success: true, report }, null, 2));
      process.exitCode = report.ok ? 0 : 2;
      return;
    }
    const handler = COMMANDS[command];
    if (!handler) {
      console.error(`未知命令: ${command}\n`);
      console.log(USAGE);
      process.exitCode = 1;
      return;
    }
    const params = await handler(flags, positionals.slice(1));
    const result = await dispatch(command, params, opts);
    if (!result.success) {
      const detail = result.errors.map((e) => `${e.method}: ${e.error}`).join("\n  ");
      console.log(
        JSON.stringify({ success: false, command, errors: result.errors }, null, 2),
      );
      console.error(`全部方法失败:\n  ${detail}`);
      process.exitCode = 2;
      return;
    }
    console.log(
      JSON.stringify({ success: true, method: result.method, data: result.data }, null, 2),
    );
  } catch (e) {
    console.log(JSON.stringify({ success: false, error: e.message }, null, 2));
    console.error(String(e.message));
    process.exitCode = 1;
  }
}

await main();
