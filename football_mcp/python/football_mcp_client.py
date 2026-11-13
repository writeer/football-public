# -*- coding: utf-8 -*-
"""football_mcp Python 客户端 — 直接调用足球相关 MCP 工具（无需先配置 IDE 的 MCP）。

原理：本模块只调用同目录的 Node CLI（`bin/football-mcp.mjs`），由 CLI 负责拉起 MCP stdio 服务、
完成 MCP 握手并调用工具，再把结果作为 JSON 返回。因此任何 Python 程序（lottery_agent、脚本、定时任务）
都能在没有 IDE MCP 配置的环境里使用这些工具。

用法（不写死绝对路径，按本文件位置定位）：
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path("football_mcp/python").resolve()))   # 或 str(Path(__file__).parent / "football_mcp" / "python")
    from football_mcp_client import list_servers, list_tools, call_tool, ping, self_test

    list_servers()                                       # 全部已注册足球 MCP 服务
    ping("football-charts")                              # 连通性 + 工具数
    list_tools("sporttery-odds")                         # 实时工具清单
    data = call_tool("football-charts", "get_league_table", {"league": "premier"})
    data = call_tool("sporttery-odds", "get_matches", {"pools": "had,hhad,crs,ttg,hafu"})

命令行直跑：
    python football_mcp/python/football_mcp_client.py servers
    python football_mcp/python/football_mcp_client.py ping football-charts
    python football_mcp/python/football_mcp_client.py call football-charts get_league_table --args '{"league":"premier"}'

本模块内部只用「本文件所在目录」推导路径（HERE / ROOT），不依赖仓库位置，可整体搬迁。
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CLI = ROOT / "bin" / "football-mcp.mjs"
NODE = os.environ.get("NODE_BIN", "node")


class FootballMcpError(RuntimeError):
    """CLI 返回 success=false 时抛出。"""

    def __init__(self, server, tool, message):
        self.server = server
        self.tool = tool
        self.message = message
        super().__init__("[{}] {}: {}".format(server, tool or "cli", message))


def _run(args, timeout=300):
    proc = subprocess.run(
        [NODE, str(CLI)] + args,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    stdout = (proc.stdout or "").strip()
    if not stdout:
        raise FootballMcpError("?", None, "CLI 无输出 | stderr: {}".format((proc.stderr or "")[:500]))
    # CLI 在 stdout 末尾追加 JSON；错误信息可能先落到 stderr
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        start = stdout.find("{")
        if start >= 0:
            try:
                return json.loads(stdout[start:])
            except json.JSONDecodeError:
                pass
        raise FootballMcpError(
            "?", None, "CLI 输出非 JSON: {} | stderr: {}".format(stdout[:300], (proc.stderr or "")[:300])
        )


def _args_file(args):
    """参数写临时文件，避免 Windows 命令行引号/编码问题。"""
    fd, path = tempfile.mkstemp(suffix=".json", prefix="football_mcp_args_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(args, f, ensure_ascii=False)
    return path


def list_servers(timeout=60):
    """返回已注册的足球 MCP 服务清单（id/启动命令/说明/工具速查）。"""
    out = _run(["servers", "--json"], timeout=timeout)
    return out.get("servers", [])


def print_config(resolve=False, vscode=False, timeout=60):
    """返回可直接写入 IDE 的 mcp.json。

    Args:
        resolve: True 时生成本机绝对路径版（仅客户端不支持相对路径时兜底，勿入库）
        vscode:  True 时生成 VS Code 格式（顶层 servers + ${workspaceFolder}）
    """
    args = ["print-config", "--json"]
    if resolve:
        args.append("--resolve")
    if vscode:
        args.append("--vscode")
    out = _run(args, timeout=timeout)
    return out.get("config", {})


def ping(server, timeout=300):
    """连通性探测，返回 {success, toolCount, tools, ms}；不可用返回 success=False。"""
    return _run(["ping", server, "--timeout", str(timeout * 1000)], timeout=timeout + 30)


def list_tools(server, timeout=300):
    """实时工具清单（名称/描述/参数/必填），失败抛 FootballMcpError。"""
    out = _run(["tools", server, "--timeout", str(timeout * 1000)], timeout=timeout + 30)
    if not out.get("success"):
        raise FootballMcpError(server, None, out.get("error", "unknown"))
    return out["tools"]


def call_tool(server, tool, args=None, raw=False, timeout=300):
    """调用某个 MCP 工具，返回其数据（dict / list / str）。

    Args:
        server: 服务 id，见 list_servers()
        tool:   工具名，见 list_tools(server)
        args:   工具入参 dict
        raw:    True 时返回 MCP 原生 result（含 content 数组）
        timeout: 秒；npx 首次冷启动会下载包，建议 >= 180
    """
    cli_args = ["call", server, tool]
    path = _args_file(args or {})
    try:
        cli_args += ["--args-file", path, "--timeout", str(timeout * 1000)]
        if raw:
            cli_args.append("--raw")
        out = _run(cli_args, timeout=timeout + 30)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if not out.get("success"):
        raise FootballMcpError(server, tool, out.get("error", "unknown"))
    return out["data"]


def self_test(servers=None, quick=False, timeout=300):
    """全服务自测，返回 {success, ok, total, results}。"""
    args = ["self-test"]
    if quick:
        args.append("--quick")
    for s in servers or []:
        args += ["--server", s]
    args += ["--timeout", str(timeout * 1000)]
    return _run(args, timeout=(timeout + 30) * max(1, len(servers or [None])))


def main():
    """命令行直跑：python football_mcp_client.py <cli args...>"""
    out = _run(sys.argv[1:])
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("success") else 2)


if __name__ == "__main__":
    main()
