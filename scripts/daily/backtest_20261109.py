# -*- coding: utf-8 -*-
"""2026-11-09 分析报告回测：仅用体彩官方赛果结算已开奖场次，其余单列待结算。"""
import json, io, pathlib, os

BASE = pathlib.Path(r"e:\VideCoding\football") if False else pathlib.Path(r"e:\VibeCoding\football")
PRED = BASE / "memory/predictions/20261109_monday/prediction.json"
OUT_DIR = BASE / "memory/backtests/20261109_monday"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 官方赛果接口实取（fetch_results_20261109_backtest.js）
OFFICIAL = {
    "周二001": {"no999": "0:3", "no1": "0:1", "goalLine": -1, "status": "已开奖", "single": 0},
    "周二002": {"no999": "1:2", "no1": "1:1", "goalLine": 1, "status": "已开奖", "single": 0},
    "周三005": {"no999": None, "no1": None, "goalLine": -1, "status": "未开赛/未开奖", "single": 0},
    "周三006": {"no999": None, "no1": None, "goalLine": -1, "status": "未开赛/未开奖", "single": 0},
}

HAFU_CN = {"HH": "胜胜", "HD": "胜平", "HA": "胜负", "DH": "平胜",
           "DD": "平平", "DA": "平负", "AH": "负胜", "AD": "负平", "AA": "负负"}


def score(s):
    h, a = str(s).split(":")
    return int(h), int(a)


def had(h, a):
    return "home" if h > a else ("draw" if h == a else "away")


def hc(h, a, line):
    d = (h - a) + line
    return "win" if d > 0 else ("push" if d == 0 else "lose")


def hafu(hh, ha, fh, fa):
    t = "H" if hh > ha else ("D" if hh == ha else "A")
    f = "H" if fh > fa else ("D" if fh == fa else "A")
    return t + f


def band_range(name):
    if "闷战" in name: return (0, 1)
    if name == "小球": return (1, 2)
    if "常规" in name: return (2, 3)
    if name == "大球": return (4, 5)
    if "超大" in name: return (5, 6)
    if "穿盘" in name: return (6, 99)
    return (0, 0)


def band_name_of(g):
    if g <= 1: return "闷战超小球(0-1球)"
    if g == 2: return "小球(1-2球)"
    if g == 3: return "常规正常球(2-3球)"
    if g in (4, 5): return "大球(4-5球)"
    if g == 6: return "超大球(5-6球)"
    return "穿盘可能(6-7+球)"


preds = {p["num"]: p for p in json.load(io.open(PRED, encoding="utf-8"))}
rows, actuals = [], {}

for num, p in preds.items():
    o = OFFICIAL[num]
    if not o["no999"]:
        actuals[num] = {"pending": True, "status": o["status"], "single": o["single"],
                        "line": o["goalLine"]}
        rows.append({"num": num, "match": p["home"] + " vs " + p["away"],
                     "league": p["league"], "conf": p["confidence"], "status": "pending",
                     "pending_reason": "体彩官方赛果接口无 sectionsNo999（未开赛/未开奖）"})
        continue
    fh, fa = score(o["no999"])
    hh, ha = score(o["no1"])
    g = fh + fa
    d = had(fh, fa)
    hcr = hc(fh, fa, p["handicap"]["line"])
    hf = hafu(hh, ha, fh, fa)
    sc = "%d-%d" % (fh, fa)
    hts = "%d-%d" % (hh, ha)
    lo, hi = band_range(p["band"]["name"])
    ou_pick = "大" if p["over25"] > 50 else "小"
    ou_act = "大" if g >= 3 else "小"

    crs = [x["score"] for x in p["scoreTop5"]]
    hafu_list = [x["key"] for x in p["hafuTop3"]]
    hts_list = [x["score"] for x in p["htScoreTop3"]]
    ttg_list = [x["goals"] for x in p["ttgTop2"]]

    actuals[num] = dict(fh=fh, fa=fa, hh=hh, ha=ha, goals=g, had=d, hc=hcr, hafu=hf,
                        score=sc, ht=hts, ou=ou_act, band=band_name_of(g),
                        line=p["handicap"]["line"], single=o["single"], status=o["status"])

    rows.append({
        "num": num, "match": p["home"] + " vs " + p["away"], "league": p["league"],
        "conf": p["confidence"], "status": "settled",
        "actual": actuals[num],
        "pred": {
            "first": p["first"], "second": p["second"],
            "firstProb": p["firstProb"], "secondProb": p["secondProb"],
            "hc_first": p["handicap"]["first"], "hc_second": p["handicap"]["second"],
            "hc_firstProb": p["handicap"]["firstProb"],
            "hc_win": p["handicap"]["win"], "hc_push": p["handicap"]["push"],
            "hc_lose": p["handicap"]["lose"],
            "ttg": ttg_list, "crs": crs, "hafu": hafu_list, "ht": hts_list,
            "band": p["band"]["name"], "band_side": p["band"]["side"],
            "ou_pick": ou_pick, "over25": p["over25"], "under25": p["under25"],
        },
        "hit": {
            "had_primary": p["first"] == {"home": "主胜", "draw": "平", "away": "客胜"}[d],
            "had_combined": p["first"] == {"home": "主胜", "draw": "平", "away": "客胜"}[d]
                            or p["second"] == {"home": "主胜", "draw": "平", "away": "客胜"}[d],
            "hc_primary": p["handicap"]["first"] == {"win": "让胜", "push": "让平", "lose": "让负"}[hcr],
            "hc_combined": p["handicap"]["first"] == {"win": "让胜", "push": "让平", "lose": "让负"}[hcr]
                           or p["handicap"]["second"] == {"win": "让胜", "push": "让平", "lose": "让负"}[hcr],
            "ttg_top2": str(g) in ttg_list,
            "ttg_top1": ttg_list[0] == str(g),
            "crs_top5": sc in crs,
            "crs_top1": crs[0] == sc,
            "hafu_top3": hf in hafu_list,
            "hafu_top1": hafu_list[0] == hf,
            "ht_top3": hts in hts_list,
            "ht_top1": hts_list[0] == hts,
            "band": lo <= g <= hi,
            "ou": ou_pick == ou_act,
        },
    })

# 串关逐注（与 reports/analysis/20261109_analysis_zhihu.md 完全一致）
PARLAYS = [
    ("方向串A", "稳健组", 3.01, [("周二001", "had", "主胜"), ("周三005", "had", "主胜")]),
    ("方向串B", "稳健组", 3.43, [("周二002", "had", "客胜"), ("周二001", "had", "主胜")]),
    ("方向串C", "稳健组", 2.14, [("周三005", "had", "主胜"), ("周二002", "had", "客胜")]),
    ("稳健让球串", "稳健组", 3.75, [("周二001", "hc", "让(-1)负"), ("周三005", "hc", "让(-1)负")]),
    ("价值让球串", "稳健组", 8.50, [("周二002", "hc", "让(+1)负"), ("周三006", "hc", "让(-1)胜")]),
    ("半全场串A", "稳健组", 8.70, [("周二001", "hafu", "HH"), ("周二002", "hafu", "AA")]),
    ("半全场串B", "稳健组", 25.20, [("周三005", "hafu", "DH"), ("周三006", "hafu", "AA")]),
    ("方向+半全场A", "稳健组", 5.17, [("周二001", "had", "主胜"), ("周二002", "hafu", "AA")]),
    ("方向+半全场B", "稳健组", 3.63, [("周三005", "had", "主胜"), ("周三006", "hafu", "HH")]),
    ("连续编号混合串A", "稳健组", 9.36, [("周二001", "hafu", "DD"), ("周二002", "had", "客胜")]),
    ("连续编号混合串B", "稳健组", 3.34, [("周三005", "hafu", "HH"), ("周三006", "had", "主胜")]),
    ("总进球串A", "娱乐组", 16.88, [("周二001", "ttg", "2"), ("周二002", "ttg", "4")]),
    ("总进球串B", "娱乐组", 15.05, [("周三005", "ttg", "2"), ("周三006", "ttg", "3")]),
    ("连续编号总进球串①", "娱乐组", 13.13, [("周二001", "ttg", "2"), ("周二002", "ttg", "3")]),
    ("连续编号总进球串②", "娱乐组", 14.53, [("周三005", "ttg", "3"), ("周三006", "ttg", "2")]),
    ("高赔半全场串A", "娱乐组", 8.70, [("周二001", "hafu", "HH"), ("周二002", "hafu", "AA")]),
    ("高赔半全场串B", "娱乐组", 25.20, [("周三005", "hafu", "DH"), ("周三006", "hafu", "AA")]),
    ("连续编号高赔半全场串①", "娱乐组", 19.27, [("周二001", "hafu", "AA"), ("周二002", "hafu", "DA")]),
    ("连续编号高赔半全场串②", "娱乐组", 11.46, [("周三005", "hafu", "HH"), ("周三006", "hafu", "AA")]),
    ("混合串A", "娱乐组", 16.65, [("周二001", "hafu", "HH"), ("周二002", "ttg", "4")]),
    ("混合串B", "娱乐组", 17.43, [("周三005", "hafu", "DH"), ("周三006", "ttg", "2")]),
    ("连续编号混合总进球串①", "娱乐组", 21.00, [("周二001", "hafu", "DD"), ("周二002", "ttg", "3")]),
    ("连续编号混合总进球串②", "娱乐组", 13.85, [("周三005", "hafu", "HH"), ("周三006", "ttg", "1")]),
    ("稳健比分串", "娱乐组", 43.88, [("周二002", "crs", "1-2"), ("周三005", "crs", "2-1")]),
    ("搏冷比分串", "娱乐组", 231.00, [("周二001", "crs", "0-1"), ("周三006", "crs", "0-0")]),
    ("连续编号比分串①", "娱乐组", 65.00, [("周二001", "crs", "1-0"), ("周二002", "crs", "1-2")]),
    ("连续编号比分串②", "娱乐组", 74.25, [("周三005", "crs", "2-1"), ("周三006", "crs", "1-0")]),
    ("单挑比分①", "娱乐组", 9.75, [("周二002", "crs", "1-3")]),
    ("单挑比分②", "娱乐组", 11.00, [("周三006", "crs", "1-0")]),
]

HITMAP = {
    "had": {"主胜": "home", "平": "draw", "客胜": "away"},
    "hc": {"让胜": "win", "让平": "push", "让负": "lose"},
}


def leg_ok(num, kind, val):
    a = actuals.get(num)
    if not a or a.get("pending"):
        return None, "⏳"
    if kind == "had":
        return HITMAP["had"][val] == a["had"], "✅" if HITMAP["had"][val] == a["had"] else "❌"
    if kind == "hc":
        key = "让" + val[-1]  # 让(-1)负 -> 让负
        return HITMAP["hc"][key] == a["hc"], "✅" if HITMAP["hc"][key] == a["hc"] else "❌"
    if kind == "hafu":
        return val == a["hafu"], "✅" if val == a["hafu"] else "❌"
    if kind == "ttg":
        return str(a["goals"]) == str(val), "✅" if str(a["goals"]) == str(val) else "❌"
    if kind == "crs":
        return val == a["score"], "✅" if val == a["score"] else "❌"
    raise ValueError(kind)


def leg_text(num, kind, val):
    a = actuals.get(num)
    if kind == "hafu":
        v = HAFU_CN[val]
    elif kind == "ttg":
        v = val + "球"
    else:
        v = val
    if not a or a.get("pending"):
        return "%s %s(⏳未开赛)" % (num, v)
    if kind == "hafu":
        act = HAFU_CN[a["hafu"]]
        return "%s %s(%s实际%s)" % (num, v, "✅" if val == a["hafu"] else "❌", act)
    if kind == "ttg":
        return "%s %s(%s实际%d球)" % (num, v, "✅" if str(a["goals"]) == str(val) else "❌", a["goals"])
    if kind == "crs":
        return "%s %s(%s实际%s)" % (num, v, "✅" if val == a["score"] else "❌", a["score"])
    if kind == "had":
        act = {"home": "主胜", "draw": "平", "away": "客胜"}[a["had"]]
        return "%s %s(%s实际%s %s)" % (num, v, "✅" if HITMAP["had"][val] == a["had"] else "❌", act, a["score"])
    act = {"win": "让胜", "push": "让平", "lose": "让负"}[a["hc"]]
    return "%s %s(%s实际%s)" % (num, v, "✅" if HITMAP["hc"]["让" + v[-1]] == a["hc"] else "❌", act)


parlay_rows = []
for name, group, odds, legs in PARLAYS:
    flags = [leg_ok(n, k, v)[0] for n, k, v in legs]
    if any(f is False for f in flags):
        res = "miss"
    elif all(f is True for f in flags):
        res = "hit"
    else:
        res = "pending"
    parlay_rows.append({"name": name, "group": group, "odds": odds, "result": res,
                        "legs": [leg_text(n, k, v) for n, k, v in legs],
                        "leg_flags": [leg_ok(n, k, v)[1] for n, k, v in legs]})

settled = [r for r in parlay_rows if r["result"] != "pending"]
hits = [r for r in settled if r["result"] == "hit"]
ret = sum(2 * r["odds"] for r in hits)
stake = 2 * len(settled)

summary = {
    "date": "2026-11-09",
    "day": "周一",
    "source_report": "reports/analysis/20261109_analysis_zhihu.md",
    "official_api": "webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry",
    "settled_matches": 2,
    "pending_matches": 2,
    "rows": rows,
    "parlays": parlay_rows,
    "parlay_stats": {
        "total": len(parlay_rows),
        "settled": len(settled),
        "hit": len(hits),
        "pending": len(parlay_rows) - len(settled),
        "stable_settled": len([r for r in settled if r["group"] == "稳健组"]),
        "stable_hit": len([r for r in hits if r["group"] == "稳健组"]),
        "fun_settled": len([r for r in settled if r["group"] == "娱乐组"]),
        "fun_hit": len([r for r in hits if r["group"] == "娱乐组"]),
        "stake_per_bet": 2,
        "stake_total": stake,
        "return_total": round(ret, 2),
        "roi_pct": round((ret - stake) / stake * 100, 1) if stake else 0,
    },
}

io.open(OUT_DIR / "backtest.json", "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=1))
io.open(BASE / "reports/data/20261109_backtest_summary.json", "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=1))

print(json.dumps(summary["parlay_stats"], ensure_ascii=False, indent=1))
for r in rows:
    print(r["num"], r["status"], json.dumps(r.get("hit", {}), ensure_ascii=False))
for r in parlay_rows:
    print(r["result"], r["group"], r["name"], " | ".join(r["legs"]))
