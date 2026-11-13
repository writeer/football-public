// 方式 1：MCP stdio 服务客户端（最小化 JSON-RPC 实现，无外部依赖）
//
// 直接 spawn `node mcp/server.ts`（SportteryAPI 的 MCP stdio 服务），按 MCP 协议
// 走 newline-delimited JSON-RPC：
//   initialize -> notifications/initialized -> tools/call
// 暴露 7 个工具：get_matches / get_match / derive_odds / compare_value /
//                calc_parlay / list_parlay_types / get_meta
//
// 失败原因排查：
//   - node < 22.6            -> --experimental-strip-types 不可用，spawn 直接报错
//   - node_modules 缺失       -> @modelcontextprotocol/sdk import 失败
//   - 本机无法访问体彩上游     -> get_matches 等实时类工具报 HTTP 567/502（计算类不受影响）

import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const API_DIR = path.resolve(HERE, "..", "..", "SportteryAPI");
const SERVER_PATH = path.join(API_DIR, "mcp", "server.ts");

const PROTOCOL_CANDIDATES = ["2025-06-18", "2025-03-26", "2024-11-05"];

const TOOL = {
  matches: "get_matches",
  match: "get_match",
  meta: "get_meta",
  "parlay-types": "list_parlay_types",
  derive: "derive_odds",
  value: "compare_value",
  parlay: "calc_parlay",
};

class McpClient {
  constructor() {
    this.id = 0;
    this.pending = new Map();
    this.buf = "";
  }

  connect() {
    return new Promise((resolve, reject) => {
      let settled = false;
      const fail = (e) => {
        if (!settled) {
          settled = true;
          reject(e);
        }
      };

      this.proc = spawn(
        process.execPath,
        ["--no-warnings", "--experimental-strip-types", SERVER_PATH],
        { cwd: API_DIR, stdio: ["pipe", "pipe", "inherit"], windowsHide: true },
      );

      this.proc.stdout.setEncoding("utf8");
      this.proc.stdout.on("data", (chunk) => {
        this.buf += chunk;
        let idx;
        while ((idx = this.buf.indexOf("\n")) >= 0) {
          const line = this.buf.slice(0, idx).trim();
          this.buf = this.buf.slice(idx + 1);
          if (!line) continue;
          let msg;
          try {
            msg = JSON.parse(line);
          } catch {
            continue;
          }
          this.#handle(msg);
        }
      });

      this.proc.on("error", fail);
      this.proc.on("exit", (code) => {
        const err = new Error(`mcp server exited (code ${code})`);
        for (const p of this.pending.values()) p.reject(err);
        this.pending.clear();
        fail(err);
      });

      this.#init().then(
        () => {
          if (!settled) {
            settled = true;
            resolve();
          }
        },
        fail,
      );
    });
  }

  async #init() {
    const tried = new Set();
    const queue = [...PROTOCOL_CANDIDATES];
    while (queue.length) {
      const ver = queue.shift();
      if (tried.has(ver)) continue;
      tried.add(ver);
      try {
        await this.request("initialize", {
          protocolVersion: ver,
          capabilities: {},
          clientInfo: { name: "sporttery-bridge", version: "1.0.0" },
        });
        this.notify("notifications/initialized", {});
        return;
      } catch (e) {
        if (Array.isArray(e.supportedProtocolVersions)) {
          for (const v of e.supportedProtocolVersions) {
            if (!tried.has(v)) queue.push(v);
          }
        }
        if (queue.every((v) => tried.has(v))) throw e;
      }
    }
    throw new Error("mcp initialize failed: no compatible protocol version");
  }

  #handle(msg) {
    if (msg.id === undefined || msg.id === null) return; // 通知/无 id 消息忽略
    const p = this.pending.get(msg.id);
    if (!p) return;
    this.pending.delete(msg.id);
    if (msg.error) {
      const err = new Error(msg.error.message || "mcp error");
      err.supportedProtocolVersions = msg.error.data?.supportedProtocolVersions;
      p.reject(err);
    } else {
      p.resolve(msg.result);
    }
  }

  request(method, params) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.proc.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
    });
  }

  notify(method, params) {
    this.proc.stdin.write(JSON.stringify({ jsonrpc: "2.0", method, params }) + "\n");
  }

  async toolsCall(name, args) {
    return this.request("tools/call", { name, arguments: args });
  }

  dispose() {
    try {
      this.proc.stdin.end();
    } catch {
      /* ignore */
    }
    setTimeout(() => {
      try {
        this.proc.kill();
      } catch {
        /* ignore */
      }
    }, 300);
  }
}

/** 命令 -> 数据。params 为 CLI 规范化后的统一参数对象。 */
export async function call(command, params = {}) {
  const name = TOOL[command];
  if (!name) throw new Error(`mcp: no tool for command "${command}"`);
  const client = new McpClient();
  try {
    await client.connect();
    const result = await client.toolsCall(name, params);
    const text = (result.content ?? [])
      .filter((c) => c.type === "text")
      .map((c) => c.text)
      .join("\n");
    if (result.isError) throw new Error(`mcp tool ${name} error: ${text}`);
    const data = JSON.parse(text);
    // 输出结构统一：与 rest/direct 保持一致
    if (command === "matches" && data && typeof data === "object") {
      data.source = "mcp";
    } else if (command === "value" && data && Array.isArray(data.outcomes) && data.outcomes.length) {
      const best = data.outcomes
        .map((o, i) => ({ i, kelly: Number(o.kelly) }))
        .sort((x, y) => y.kelly - x.kelly)[0];
      data.bestValue = best ? best.i : null;
    }
    return data;
  } finally {
    client.dispose();
  }
}
