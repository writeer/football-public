// 通用 MCP stdio 客户端（零外部依赖）
//
// 面向 stdio 类 MCP 服务（npx 包或本地 node 脚本），按 MCP 协议走
// newline-delimited JSON-RPC：
//   initialize -> notifications/initialized -> tools/list / tools/call
//
// 用法：
//   import { McpClient } from "./mcp-client.mjs";
//   const c = new McpClient({ command: "npx", args: ["-y", "footballcharts-mcp"] });
//   await c.connect();
//   const tools = await c.listTools();
//   const data = await c.callTool("get_league_table", { league: "epl" });
//   c.dispose();

import { spawn } from "node:child_process";

const PROTOCOL_CANDIDATES = ["2025-06-18", "2025-03-26", "2024-11-05"];

export class McpClientError extends Error {
  constructor(message, extra = {}) {
    super(message);
    Object.assign(this, extra);
  }
}

/**
 * Windows 下 npx / npm 等 .cmd 包装器不能直接 spawn，必须经 cmd.exe 执行。
 * 这里显式拼命令行并转义，避免 spawn({shell:true}) 的参数拼接告警。
 */
function buildSpawn(server) {
  const command = server.command;
  const args = server.args ?? [];
  if (process.platform !== "win32") return { exe: command, args };
  const quote = (v) => (/[\s"]/.test(v) ? `"${String(v).replace(/"/g, '\\"')}"` : String(v));
  const line = [command, ...args].map(quote).join(" ");
  return { exe: process.env.ComSpec || "cmd.exe", args: ["/d", "/s", "/c", line] };
}

export class McpClient {
  /**
   * @param {object} server 服务定义 { command, args, env, cwd }
   * @param {object} [opts] { name, version, requestTimeout, connectTimeout }
   */
  constructor(server, opts = {}) {
    this.server = server;
    this.clientInfo = { name: opts.name ?? "football-mcp", version: opts.version ?? "1.0.0" };
    this.requestTimeout = opts.requestTimeout ?? 120000;
    this.connectTimeout = opts.connectTimeout ?? 90000;
    this.id = 0;
    this.pending = new Map();
    this.buf = "";
    this.stderr = "";
    this.exited = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      let settled = false;
      const fail = (e) => {
        if (!settled) {
          settled = true;
          this.dispose();
          reject(e);
        }
      };

      const { exe, args } = buildSpawn(this.server);
      this.proc = spawn(exe, args, {
        cwd: this.server.cwd,
        env: { ...process.env, ...(this.server.env ?? {}) },
        stdio: ["pipe", "pipe", "pipe"],
        windowsHide: true,
      });

      this.timer = setTimeout(
        () => fail(new McpClientError(`connect timeout (${this.connectTimeout}ms)`)),
        this.connectTimeout,
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
            continue; // 非 JSON 噪声（如 npx 提示）忽略
          }
          this.#handle(msg);
        }
      });

      this.proc.stderr.setEncoding("utf8");
      this.proc.stderr.on("data", (chunk) => {
        this.stderr += chunk;
        if (this.stderr.length > 4000) this.stderr = this.stderr.slice(-4000);
      });

      this.proc.on("error", fail);
      this.proc.on("exit", (code) => {
        const err = new McpClientError(
          `mcp server exited (code ${code})${this.stderr ? ` | stderr: ${this.stderr.trim().slice(0, 400)}` : ""}`,
        );
        this.exited = err;
        for (const p of this.pending.values()) p.reject(err);
        this.pending.clear();
        fail(err);
      });

      this.#init().then(
        () => {
          clearTimeout(this.timer);
          if (!settled) {
            settled = true;
            resolve();
          }
        },
        (e) => {
          clearTimeout(this.timer);
          fail(e);
        },
      );
    });
  }

  async #init() {
    const tried = new Set();
    const queue = [...PROTOCOL_CANDIDATES];
    let lastErr;
    while (queue.length) {
      const ver = queue.shift();
      if (tried.has(ver)) continue;
      tried.add(ver);
      try {
        await this.request("initialize", {
          protocolVersion: ver,
          capabilities: {},
          clientInfo: this.clientInfo,
        });
        this.notify("notifications/initialized", {});
        return;
      } catch (e) {
        lastErr = e;
        if (Array.isArray(e.supportedProtocolVersions)) {
          for (const v of e.supportedProtocolVersions) if (!tried.has(v)) queue.push(v);
        }
      }
    }
    throw new McpClientError(`mcp initialize failed: ${lastErr?.message ?? "unknown"}`);
  }

  #handle(msg) {
    if (msg.id === undefined || msg.id === null) return;
    const p = this.pending.get(msg.id);
    if (!p) return;
    this.pending.delete(msg.id);
    clearTimeout(p.timer);
    if (msg.error) {
      const err = new McpClientError(msg.error.message || "mcp error");
      err.supportedProtocolVersions = msg.error.data?.supportedProtocolVersions;
      err.data = msg.error.data;
      p.reject(err);
    } else {
      p.resolve(msg.result);
    }
  }

  request(method, params) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new McpClientError(`request timeout: ${method} (${this.requestTimeout}ms)`));
      }, this.requestTimeout);
      this.pending.set(id, { resolve, reject, timer });
      this.proc.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
    });
  }

  notify(method, params) {
    this.proc.stdin.write(JSON.stringify({ jsonrpc: "2.0", method, params }) + "\n");
  }

  /** 列出该服务全部工具 */
  async listTools() {
    const res = await this.request("tools/list", {});
    return res?.tools ?? [];
  }

  /** 原始 tools/call 结果（MCP 原生结构） */
  async rawCall(name, args = {}) {
    return this.request("tools/call", { name, arguments: args });
  }

  /** 调用工具并尽量把 text 内容解析为 JSON（失败则原样返回字符串） */
  async callTool(name, args = {}) {
    const result = await this.rawCall(name, args);
    const text = (result?.content ?? [])
      .filter((c) => c.type === "text")
      .map((c) => c.text)
      .join("\n");
    if (result?.isError) throw new McpClientError(`tool ${name} error: ${text}`, { raw: result });
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  dispose() {
    try {
      this.proc?.stdin?.end();
    } catch {
      /* ignore */
    }
    if (this.proc && !this.proc.killed) {
      const p = this.proc;
      setTimeout(() => {
        try {
          p.kill();
        } catch {
          /* ignore */
        }
      }, 300);
    }
  }
}

/** 一次性调用：连接 -> 执行 fn -> 断开 */
export async function withClient(server, fn, opts = {}) {
  const client = new McpClient(server, opts);
  try {
    await client.connect();
    return await fn(client);
  } finally {
    client.dispose();
  }
}
