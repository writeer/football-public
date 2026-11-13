#!/usr/bin/env node
// football-mcp — 足球相关 MCP 服务器统一 CLI
//
// 让任何程序（脚本 / 其他 IDE 的 Agent / CI）不必配置 MCP，也能直接调用足球 MCP 工具：
//   node bin/football-mcp.mjs servers
//   node bin/football-mcp.mjs print-config [--vscode | --resolve]
//   node bin/football-mcp.mjs tools football-charts
//   node bin/football-mcp.mjs ping sporttery-odds
//   node bin/football-mcp.mjs call football-charts get_league_table --args '{"league":"epl"}'
//   node bin/football-mcp.mjs call sporttery-odds get_matches --args-file body.json
//   node bin/football-mcp.mjs self-test
//
// 所有命令输出单行 JSON 到 stdout：
//   成功 {"success":true, "server":..., "tool":..., "data":...}
//   失败 {"success":false, "server":..., "error":...}  退出码 2

import fs from "node:fs";
import { McpClient } from "../lib/mcp-client.mjs";
import {
  SERVERS,
  getServer,
  toMcpJson,
  toResolvedMcpJson,
  toVsCodeMcpJson,
  ROOT,
} from "../lib/registry.mjs";

function parseArgv(argv) {
  const positional = [];
  const flags = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--args-file") flags.argsFile = argv[++i];
    else if (a === "--args") flags.args = argv[++i];
    else if (a === "--server") (flags.servers ??= []).push(argv[++i]);
    else if (a === "--timeout") flags.timeout = Number(argv[++i]);
    else if (a.startsWith("--")) flags[a.slice(2)] = true;
    else positional.push(a);
  }
  return { positional, flags };
}

function out(obj, code = 0) {
  process.stdout.write(JSON.stringify(obj, null, 2) + "\n");
  process.exit(code);
}

function readArgs(flags) {
  // 兼容 Windows 常见编码问题：PowerShell Out-File 会在文件头写入 UTF-8 BOM
  if (flags.argsFile) {
    const text = fs.readFileSync(flags.argsFile, "utf8").replace(/^\uFEFF/, "");
    return JSON.parse(text);
  }
  if (flags.args) {
    return JSON.parse(flags.args.replace(/^\uFEFF/, ""));
  }
  return {};
}

async function withServer(server, fn, timeout) {
  const client = new McpClient(server, timeout ? { requestTimeout: timeout } : {});
  try {
    await client.connect();
    return await fn(client);
  } finally {
    client.dispose();
  }
}

async function cmdServers(flags) {
  const list = SERVERS.map((s) => ({
    id: s.id,
    title: s.title,
    category: s.category,
    command: `${s.command} ${s.args.join(" ")}`,
    cwd: s.cwd ?? null,
    note: s.note,
    tools: s.tools,
  }));
  if (flags.json) out({ success: true, count: list.length, servers: list });
  for (const s of list) {
    process.stdout.write(`\n[${s.id}] ${s.title}  (${s.category})\n`);
    process.stdout.write(`  启动: ${s.command}${s.cwd ? `  [cwd=${s.cwd}]` : ""}\n`);
    process.stdout.write(`  说明: ${s.note}\n`);
    process.stdout.write(
      `  工具(${Object.keys(s.tools).length}): ${Object.keys(s.tools).join(", ")}\n`,
    );
  }
  process.stdout.write("\n");
  process.exit(0);
}

async function cmdPing(id, flags) {
  const server = getServer(id);
  const t0 = Date.now();
  try {
    const tools = await withServer(server, (c) => c.listTools(), flags.timeout);
    out({
      success: true,
      server: id,
      toolCount: tools.length,
      tools: tools.map((t) => t.name),
      ms: Date.now() - t0,
    });
  } catch (e) {
    out({ success: false, server: id, error: e.message, ms: Date.now() - t0 }, 2);
  }
}

async function cmdTools(id, flags) {
  const server = getServer(id);
  try {
    const tools = await withServer(server, (c) => c.listTools(), flags.timeout);
    out({
      success: true,
      server: id,
      count: tools.length,
      tools: tools.map((t) => ({
        name: t.name,
        description: t.description,
        params: Object.keys(t.inputSchema?.properties ?? {}),
        required: t.inputSchema?.required ?? [],
      })),
    });
  } catch (e) {
    out({ success: false, server: id, error: e.message }, 2);
  }
}

async function cmdCall(id, tool, flags) {
  const server = getServer(id);
  let args;
  try {
    args = readArgs(flags);
  } catch (e) {
    out({ success: false, server: id, tool, error: `参数解析失败: ${e.message}` }, 2);
    return;
  }
  const t0 = Date.now();
  try {
    const data = await withServer(
      server,
      (c) => (flags.raw ? c.rawCall(tool, args) : c.callTool(tool, args)),
      flags.timeout,
    );
    out({ success: true, server: id, tool, args, ms: Date.now() - t0, data });
  } catch (e) {
    out({ success: false, server: id, tool, args, error: e.message, ms: Date.now() - t0 }, 2);
  }
}

async function cmdSelfTest(flags) {
  const targets = flags.servers?.length
    ? flags.servers.map(getServer)
    : SERVERS.filter((s) => !flags.quick || s.category === "core");
  const results = [];
  let ok = 0;
  for (const server of targets) {
    const t0 = Date.now();
    try {
      const tools = await withServer(server, (c) => c.listTools(), flags.timeout);
      ok++;
      results.push({ id: server.id, ok: true, toolCount: tools.length, ms: Date.now() - t0 });
      process.stderr.write(`  OK   ${server.id} (${tools.length} tools, ${Date.now() - t0}ms)\n`);
    } catch (e) {
      results.push({ id: server.id, ok: false, error: e.message, ms: Date.now() - t0 });
      process.stderr.write(`  FAIL ${server.id}: ${e.message}\n`);
    }
  }
  out({ success: ok > 0, ok, total: targets.length, results }, ok > 0 ? 0 : 2);
}

function usage() {
  process.stdout.write(
    [
      "football-mcp — 足球 MCP 统一 CLI",
      "",
      "  servers [--json]                        列出全部已注册足球 MCP 服务",
      "  print-config                            输出 mcp.json（相对路径版，可直接迁移/提交）",
      "  print-config --vscode                   VS Code 格式（顶层 servers + ${workspaceFolder}）",
      "  print-config --resolve                  本机绝对路径版（仅客户端不支持相对路径时临时用）",
      "  ping <server> [--timeout ms]            连通性探测（返回工具清单）",
      "  tools <server>                          列出该服务全部工具（实时）",
      "  call <server> <tool> [--args json | --args-file path] [--raw]",
      "                                          调用工具，结果输出为 JSON",
      "  self-test [--quick] [--server id ...]   全服务自测",
      "",
      `服务目录: ${ROOT}`,
      "",
    ].join("\n"),
  );
  process.exit(1);
}

const { positional, flags } = parseArgv(process.argv.slice(2));
const [cmd, a, b] = positional;

switch (cmd) {
  case "servers":
    await cmdServers(flags);
    break;
  case "print-config": {
    // 默认输出相对路径版（可直接落库/迁移）；--vscode 输出 VS Code 格式；--resolve 仅本机兜底
    let cfg;
    if (flags.vscode) cfg = toVsCodeMcpJson();
    else if (flags.resolve) {
      cfg = toResolvedMcpJson();
      process.stderr.write(
        "注意：--resolve 输出的是本机绝对路径，仅用于客户端不支持相对路径时临时使用，请勿提交到仓库。\n",
      );
    } else cfg = toMcpJson();
    if (flags.json) out({ success: true, config: cfg });
    process.stdout.write(JSON.stringify(cfg, null, 2) + "\n");
    process.exit(0);
  }
  case "ping":
    if (!a) usage();
    await cmdPing(a, flags);
    break;
  case "tools":
    if (!a) usage();
    await cmdTools(a, flags);
    break;
  case "call":
    if (!a || !b) usage();
    await cmdCall(a, b, flags);
    break;
  case "self-test":
    await cmdSelfTest(flags);
    break;
  default:
    usage();
}
