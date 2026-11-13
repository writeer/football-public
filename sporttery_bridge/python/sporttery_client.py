# -*- coding: utf-8 -*-
"""sporttery_bridge Python 客户端 — 统一封装 sporttery 赔率服务（四方法自动回退）。

供 lottery_agent / 各子 Agent 直接 import 使用，无需关心底层是 MCP、REST 还是直接库调用。

用法：
    from sporttery_client import get_matches, derive, calc_parlay, meta, parlay_types, value, self_test

回退链：mcp -> rest -> direct（可用环境变量 SPORTTERY_METHOD 覆盖，如 mcp,direct）。
命令行直接跑：python sporttery_client.py matches --pools had,hhad,crs,ttg,hafu
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BRIDGE_DIR = Path(__file__).resolve().parent.parent
CLI = BRIDGE_DIR / "bin" / "sporttery.mjs"
NODE = os.environ.get("NODE_BIN", "node")
NODE_FLAGS = ["--no-warnings", "--experimental-strip-types"]

# 默认全玩法（规则15要求收集5类赔率）
DEFAULT_POOLS = "had,hhad,crs,ttg,hafu"


class SportteryError(RuntimeError):
    """所有方法均失败时抛出，附各方法错误详情。"""

    def __init__(self, errors):
        self.errors = errors
        detail = "; ".join("{}: {}".format(e["method"], e["error"]) for e in errors)
        super().__init__("SportteryAPI 所有调用方法均失败: " + detail)


def _run_cli(args, timeout=180):
    cmd = [NODE] + NODE_FLAGS + [str(CLI)] + args
    proc = subprocess.run(
        cmd,
        cwd=str(BRIDGE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    try:
        out = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        raise RuntimeError(
            "CLI 输出非 JSON: {} | stderr: {}".format(proc.stdout[:500], proc.stderr[:500])
        )
    return out


def _call(args, method=None, timeout=180):
    if method:
        args = args + ["--method", method]
    out = _run_cli(args, timeout=timeout)
    if not out.get("success"):
        raise SportteryError(out.get("errors", [{"method": "?", "error": out.get("error", "?")}]))
    return out["data"]


def _body_file(obj):
    """把中文 JSON body 写临时文件，避免 Windows 命令行编码问题。"""
    fd, path = tempfile.mkstemp(suffix=".json", prefix="sporttery_body_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return path
    finally:
        pass  # 文件由 CLI 读取后删除


def get_matches(pools=DEFAULT_POOLS, date=None, league=None, match_id=None, method=None, timeout=180):
    """获取竞彩足球最新赔率（含衍生指标：返还率/去水概率/真实赔率/趋势）。

    Args:
        pools: 逗号分隔玩法，如 "had,hhad,crs,ttg,hafu"
        date: 赛程日期，如 "260821"
        league: 联赛名子串，如 "英超"
        match_id: 单场上游 matchId
    """
    args = ["matches", "--pools", pools]
    if date:
        args += ["--date", str(date)]
    if league:
        args += ["--league", league]
    if match_id is not None:
        args += ["--matchId", str(match_id)]
    return _call(args, method, timeout)


def get_match(match_id, method=None, timeout=180):
    """按 matchId 获取单场（全玩法）。"""
    return _call(["match", str(match_id)], method, timeout)


def meta(method=None, timeout=60):
    """玩法标签 / 过关表 / 公式参考。"""
    return _call(["meta"], method, timeout)


def parlay_types(matches=None, method=None, timeout=60):
    """过关方式对照表。"""
    args = ["parlay-types"]
    if matches is not None:
        args += ["--matches", str(matches)]
    return _call(args, method, timeout)


def derive(odds=None, h=None, d=None, a=None, method=None, timeout=60):
    """赔率推导：隐含/去水概率、返还率、真实赔率。odds 或 (h,d,a) 二选一。"""
    if odds:
        args = ["derive", "--odds", ",".join(str(o) for o in odds)]
    else:
        args = ["derive", "--h", str(h), "--d", str(d), "--a", str(a)]
    return _call(args, method, timeout)


def value(offered, reference, labels=None, method=None, timeout=60):
    """凯利指数 / 价值对比。offered 与 reference 为等长赔率列表。"""
    args = [
        "value",
        "--offered", ",".join(str(o) for o in offered),
        "--reference", ",".join(str(o) for o in reference),
    ]
    if labels:
        args += ["--labels", ",".join(labels)]
    return _call(args, method, timeout)


def calc_parlay(legs, pass_type=None, folds=None, multiplier=1, method=None, timeout=60):
    """单关 / 过关奖金计算。

    Args:
        legs: [{"odds": 1.44, "result": "win|lose|void", "label": "..."}]
        pass_type: "单关" / "3串1" 等标签
        folds: 显式组合尺寸，如 [2, 3]
        multiplier: 倍数
    """
    body = {"legs": legs, "multiplier": multiplier}
    if pass_type:
        body["passType"] = pass_type
    if folds:
        body["folds"] = folds
    path = _body_file(body)
    try:
        return _call(["parlay", "--body-file", path], method, timeout)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def self_test(method=None, chain=None, timeout=600):
    """全方法自测，返回报告 dict。"""
    args = ["self-test"]
    if method:
        args += ["--method", method]
    if chain:
        args += ["--chain", chain]
    out = _run_cli(args, timeout=timeout)
    return out


def methods(timeout=30):
    """快速可用性探测。"""
    out = _run_cli(["methods"], timeout=timeout)
    return out.get("methods", [])


def main():
    """命令行直跑：python sporttery_client.py <cli args...>"""
    args = sys.argv[1:]
    out = _run_cli(args)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("success") else 2)


if __name__ == "__main__":
    main()
