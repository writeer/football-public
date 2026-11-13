# -*- coding: utf-8 -*-
"""2026-10-17 周六 30 场回测（预测口径：reports/analysis/20261017_saturday_analysis_zhihu.md）"""
import json
import re
import os

BASE = os.path.dirname(os.path.abspath(__file__))

PRED = json.load(open(os.path.join(BASE, "reports/data/20261017_predictions.json"), encoding="utf-8"))
RAW = json.load(open(os.path.join(BASE, "reports/data/20261017_results_raw.json"), encoding="utf-8-sig"))

# ---------- 赛果（官方开奖接口，按 matchId 对齐；023-030 官方 matchDate=10-18） ----------
RES = {}
for r in RAW:
    if r["matchResultStatus"] != "2":
        continue
    RES[int(r["matchId"])] = dict(
        num=r["matchNumStr"], league=r["leagueNameAbbr"], home=r["homeTeam"], away=r["awayTeam"],
        ht=r["sectionsNo1"].replace(":", "-"), ft=r["sectionsNo999"].replace(":", "-"),
        date=r["matchDate"], line=r["goalLine"], win=r["winFlag"], status=r["matchResultStatus"])

DM = {"home": "主胜", "draw": "平", "away": "客胜"}
HM = {"home": "让胜", "draw": "让平", "away": "让负"}
HAFU = {("home", "home"): "胜胜", ("home", "draw"): "胜平", ("home", "away"): "胜负",
        ("draw", "home"): "平胜", ("draw", "draw"): "平平", ("draw", "away"): "平负",
        ("away", "home"): "负胜", ("away", "draw"): "负平", ("away", "away"): "负负"}


def res_of(hg, ag):
    return "home" if hg > ag else ("draw" if hg == ag else "away")


def size_tier(goals):
    if goals <= 1:
        return "闷战超小球"
    if goals == 2:
        return "小球"
    if goals == 3:
        return "常规正常球"
    if goals == 4:
        return "大球"
    if goals == 5:
        return "超大球"
    return "穿盘可能"


rows = []
miss_dir, miss_hhad = [], []
tally = dict(n=0, dirMerged=0, dirFirst=0, dirSecond=0, hhadMerged=0, hhadFirst=0, hhadSecond=0,
             ttg=0, hafu=0, hafuN=0, crs=0, htScore=0, htScoreN=0, krecBand=0, sizeHit=0)

for p in PRED:
    mid = int(p["match_id"])
    r = RES[mid]
    fh, fa = map(int, r["ft"].split("-"))
    th, ta = map(int, r["ht"].split("-"))
    actual_dir = res_of(fh, fa)
    actual_hafu = HAFU[(res_of(th, ta), actual_dir)]
    line = int(p["hhad_line"])

    # 方向
    if actual_dir == p["primary"]:
        dstat = "✅首"
        tally["dirFirst"] += 1
    elif actual_dir == p["secondary"]:
        dstat = "✅次"
        tally["dirSecond"] += 1
    else:
        dstat = "❌"
        miss_dir.append(p["match_num"][-3:])
    if dstat != "❌":
        tally["dirMerged"] += 1

    # 让球
    adj = fh + line
    hact = "home" if adj > fa else ("draw" if adj == fa else "away")
    hf = re.search(r"[胜负平]$", p["hhad_recommend"]["first"]).group()
    hs = re.search(r"[胜负平]$", p["hhad_recommend"]["second"]).group()
    hf_dir = {"胜": "home", "平": "draw", "负": "away"}[hf]
    hs_dir = {"胜": "home", "平": "draw", "负": "away"}[hs]
    if hact == hf_dir:
        hstat = "✅首"
        tally["hhadFirst"] += 1
    elif hact == hs_dir:
        hstat = "✅次"
        tally["hhadSecond"] += 1
    else:
        hstat = "❌"
        miss_hhad.append(p["match_num"][-3:])
    if hstat != "❌":
        tally["hhadMerged"] += 1

    # 总进球
    tg = fh + fa
    ttg_pick = [str(x["goals"]) for x in p["ttg_top2"]]
    ttg_actual = "7+" if tg >= 7 else str(tg)
    ttg_hit = ttg_actual in ttg_pick
    if ttg_hit:
        tally["ttg"] += 1

    # 半全场
    hafu_pick = [x["code"] for x in p["hafu_top3"]]
    hafu_hit = actual_hafu in hafu_pick
    if hafu_hit:
        tally["hafu"] += 1
    tally["hafuN"] += 1

    # 比分TOP5
    crs_pick = [x["score"] for x in p["score_top5"]]
    crs_hit = r["ft"] in crs_pick
    rank = crs_pick.index(r["ft"]) + 1 if crs_hit else 0
    if crs_hit:
        tally["crs"] += 1

    # 半场比分TOP3
    ht_pick = [x["score"] for x in p["ht_scores_top3"]]
    ht_hit = r["ht"] in ht_pick
    if ht_hit:
        tally["htScore"] += 1
    tally["htScoreN"] += 1

    # 大小球六档
    size_hit = p["size_tier"] == size_tier(tg)
    if size_hit:
        tally["sizeHit"] += 1

    # 规则67 带内
    band = [x["score"] for x in p["band_top3"]]
    krec_band = r["ft"] in band
    if krec_band:
        tally["krecBand"] += 1

    tally["n"] += 1
    rows.append(dict(
        id=p["match_num"][-3:], league=p["league"], home=p["home"], away=p["away"],
        conf=p["confidence"], single=bool(p["is_single"]), stadium=p["stadium_status"],
        ht=r["ht"], ft=r["ft"], line=line, date=r["date"], source="体彩官方 getUniformMatchResultV1",
        had=dict(first=DM[p["primary"]], second=DM[p["secondary"]], actual=DM[actual_dir], hit=dstat),
        hhad=dict(line=line, first="让" + hf, second="让" + hs,
                  actual="让" + {"home": "胜", "draw": "平", "away": "负"}[hact], hit=hstat),
        crs=dict(top5=crs_pick, actual=r["ft"], hit=crs_hit, rank=rank),
        ttg=dict(pick=ttg_pick, actual=ttg_actual, hit=ttg_hit),
        bsize=dict(tier=p["size_tier"], actual=size_tier(tg), actualGoals=tg, hit=size_hit),
        hafu=dict(top3=hafu_pick, actual=actual_hafu, hit=hafu_hit,
                  rank=(hafu_pick.index(actual_hafu) + 1 if hafu_hit else 0)),
        htScore=dict(top3=ht_pick, actual=r["ht"], hit=ht_hit,
                     rank=(ht_pick.index(r["ht"]) + 1 if ht_hit else 0)),
        k=dict(k_dist=p["k_dist"]["value"], k_rec=p["k_rec"]["value"],
               actual=fh - fa, krecBand=krec_band, consistent=bool(p["k_consistent"])),
        band=band,
    ))

# ---------- 串关（严格按分析报告 1312-1413 行原始方案） ----------
PARLAYS = [
    ("方向串A（稳健）", "方向串", 1.96, [("002", "had", "home"), ("019", "had", "home"), ("026", "had", "away")]),
    ("方向串B（价值）", "方向串", 3.28, [("003", "had", "home"), ("008", "had", "home"), ("012", "had", "home")]),
    ("方向串C（客队强打）", "方向串", 2.61, [("026", "had", "away"), ("023", "had", "away"), ("020", "had", "home")]),
    ("稳健让球串", "让球串", 4.25, [("007", "hhad", ("home", 1)), ("015", "hhad", ("home", 1)), ("029", "hhad", ("home", 1))]),
    ("价值让球串", "让球串", 39.6, [("019", "hhad", ("draw", -2)), ("025", "hhad", ("draw", -2)), ("012", "hhad", ("home", -1))]),
    ("半全场串A", "混合串", 10.8, [("019", "hafu", "胜胜"), ("021", "hafu", "平胜"), ("012", "hafu", "胜胜")]),
    ("半全场串B", "混合串", 17.9, [("020", "hafu", "胜胜"), ("008", "hafu", "平胜"), ("028", "hafu", "胜胜")]),
    ("方向+半全场A", "混合串", 1.95, [("002", "had", "home"), ("019", "hafu", "胜胜")]),
    ("方向+半全场B", "混合串", 2.80, [("003", "had", "home"), ("021", "hafu", "胜胜")]),
    ("连续编号混合串A", "混合串", 4.01, [("007", "hhad", ("home", 1)), ("008", "hafu", "胜胜")]),
    ("连续编号混合串B", "混合串", 8.58, [("017", "hhad", ("home", 1)), ("018", "hafu", "胜胜")]),
    ("总进球串A", "总进球串", 65.3, [("004", "ttg", "4"), ("010", "ttg", "4"), ("019", "ttg", "3")]),
    ("总进球串B", "总进球串", 77.5, [("012", "ttg", "4"), ("022", "ttg", "4"), ("025", "ttg", "5")]),
    ("连续编号总进球串①", "总进球串", 15.3, [("010", "ttg", "4"), ("011", "ttg", "2")]),
    ("连续编号总进球串②", "总进球串", 17.2, [("016", "ttg", "4"), ("017", "ttg", "2")]),
    ("高赔半全场串A", "高赔半全场串", 100.1, [("005", "hafu", "平胜"), ("008", "hafu", "平平"), ("017", "hafu", "平负")]),
    ("高赔半全场串B", "高赔半全场串", 13.5, [("012", "hafu", "胜胜"), ("026", "hafu", "负负"), ("021", "hafu", "平胜")]),
    ("连续编号高赔半全场串①", "高赔半全场串", 17.2, [("007", "hafu", "负负"), ("008", "hafu", "平平")]),
    ("连续编号高赔半全场串②", "高赔半全场串", 25.4, [("023", "hafu", "平负"), ("024", "hafu", "平平")]),
    ("混合串A", "半全场混合", 16.8, [("005", "hafu", "平胜"), ("012", "ttg", "4")]),
    ("混合串B", "半全场混合", 7.5, [("026", "hafu", "负负"), ("021", "ttg", "4")]),
    ("连续编号混合总进球串①", "半全场混合", 17.8, [("003", "hafu", "平胜"), ("004", "ttg", "4")]),
    ("连续编号混合总进球串②", "半全场混合", 26.7, [("024", "hafu", "平平"), ("025", "ttg", "4")]),
    ("稳健比分串", "比分串", 42.0, [("002", "crs", "2-1"), ("021", "crs", "2-1")]),
    ("搏冷比分串", "比分串", 105.0, [("007", "crs", "2-2"), ("024", "crs", "2-2")]),
    ("连续编号比分串①", "比分串", 39.0, [("002", "crs", "2-1"), ("003", "crs", "2-1")]),
    ("连续编号比分串②", "比分串", 49.0, [("021", "crs", "2-1"), ("022", "crs", "1-2")]),
    ("单挑比分①", "比分串", 8.75, [("022", "crs", "1-3")]),
    ("单挑比分②", "比分串", 8.25, [("010", "crs", "1-3")]),
]

ROW = {x["id"]: x for x in rows}


def leg_hit(pid, kind, pick):
    x = ROW[pid]
    if kind == "had":
        return x["had"]["actual"] == DM[pick]
    if kind == "hafu":
        return x["hafu"]["actual"] == pick
    if kind == "ttg":
        return x["ttg"]["actual"] == pick
    if kind == "crs":
        return x["ft"] == pick
    d, line = pick
    return x["hhad"]["actual"] == "让" + {"home": "胜", "draw": "平", "away": "负"}[d]


def leg_desc(pid, kind, pick):
    x = ROW[pid]
    if kind == "had":
        return f"{pid}{x['home']}{DM[pick]}"
    if kind == "hafu":
        return f"{pid}{x['home']}{pick}"
    if kind == "ttg":
        return f"{pid}{x['home']}{pick}球"
    if kind == "crs":
        return f"{pid}{x['home']}{pick}"
    d, line = pick
    return f"{pid}{x['home']}让({line:+d}){'胜' if d == 'home' else ('平' if d == 'draw' else '负')}"


parlays = []
pstats = {}
for name, typ, odds, legs in PARLAYS:
    results, ok = [], True
    for pid, kind, pick in legs:
        h = leg_hit(pid, kind, pick)
        ok = ok and h
        results.append(dict(id=pid, pick=leg_desc(pid, kind, pick), r="Y" if h else "N"))
    parlays.append(dict(name=name, type=typ, odds_est=odds,
                        matches=[pid for pid, _, _ in legs],
                        legs=[[pid, leg_desc(pid, kind, pick), None] for pid, kind, pick in legs],
                        results=results, hit=ok))
    pstats.setdefault(typ, dict(n=0, hit=0))
    pstats[typ]["n"] += 1
    pstats[typ]["hit"] += 1 if ok else 0

# 置信度分组
byconf = {}
for x in rows:
    c = x["conf"]
    byconf.setdefault(c, dict(n=0, hit=0))
    byconf[c]["n"] += 1
    byconf[c]["hit"] += 1 if x["had"]["hit"] != "❌" else 0

n = tally["n"]
pct = lambda a, b: f"{a}/{b} = {a / b * 100:.1f}%"
tally_out = dict(
    n=n,
    dirAll=tally["dirMerged"], dirFirst=tally["dirFirst"], dirSecond=tally["dirSecond"],
    hhadAll=tally["hhadMerged"], hhadFirst=tally["hhadFirst"], hhadSecond=tally["hhadSecond"],
    ttg=tally["ttg"], hafu=tally["hafu"], crs=tally["crs"],
    htScore=tally["htScore"], sizeHit=tally["sizeHit"], krecBand=tally["krecBand"],
)
summary = dict(
    n=n,
    dir_all=pct(tally["dirMerged"], n), dir_first_only=pct(tally["dirFirst"], n),
    hhad_all=pct(tally["hhadMerged"], n), hhad_first_only=pct(tally["hhadFirst"], n),
    ttg=pct(tally["ttg"], n), hafu=pct(tally["hafu"], n), crs=pct(tally["crs"], n),
    htScore=pct(tally["htScore"], n), size=pct(tally["sizeHit"], n),
    krec_band=pct(tally["krecBand"], n),
)
miss_dir, miss_hhad = sorted(miss_dir), sorted(miss_hhad)
parlay_total = len(parlays)
parlay_hit = sum(1 for x in parlays if x["hit"])

print("=" * 110)
print("2026-10-17 周六 30 场回测")
for x in rows:
    print(f"{x['id']} {x['league']} {x['home']}vs{x['away']} 半{x['ht']} 全{x['ft']} | "
          f"方向{x['had']['first']}/{x['had']['second']}→{x['had']['actual']} {x['had']['hit']} | "
          f"让{x['hhad']['first']}/{x['hhad']['second']}→{x['hhad']['actual']} {x['hhad']['hit']} | "
          f"TG{','.join(x['ttg']['pick'])}→{x['ttg']['actual']} {'✅' if x['ttg']['hit'] else '❌'} | "
          f"HAFU{'/'.join(x['hafu']['top3'])}→{x['hafu']['actual']} {'✅' if x['hafu']['hit'] else '❌'} | "
          f"CRS{'/'.join(x['crs']['top5'])}→{x['crs']['actual']} {('✅'+str(x['crs']['rank'])) if x['crs']['hit'] else '❌'} | "
          f"size{x['bsize']['tier']}→{x['bsize']['actual']} {'✅' if x['bsize']['hit'] else '❌'} | "
          f"k={x['k']['k_dist']}/{x['k']['k_rec']}({x['k']['actual']}) {'带内' if x['k']['krecBand'] else '-'}")
print("=" * 110)
for k, v in summary.items():
    print(k, v)
print("方向未中:", miss_dir)
print("让球未中:", miss_hhad)
print("置信度:", json.dumps(byconf, ensure_ascii=False))
print("\n串关:")
for x in parlays:
    print(f"  {x['name']}[{x['type']}] {x['odds_est']} : " + " + ".join(
        f"{r['pick']}({'✅' if r['r'] == 'Y' else '❌'})" for r in x["results"]) + f" → {'✅' if x['hit'] else '❌'}")
print("串关命中", parlay_hit, "/", parlay_total)
print("分类型:", json.dumps(pstats, ensure_ascii=False))

# ---------- 落盘 ----------
result_rows = []
for p in PRED:
    r = RES[int(p["match_id"])]
    result_rows.append(dict(num=r["num"], league=p["league"], home=p["home"], away=p["away"],
                            match_id=p["match_id"], date=r["date"], ht=r["ht"], ft=r["ft"],
                            goalLine=r["line"], winFlag=r["win"], status=r["status"],
                            source="体彩官方 getUniformMatchResultV1（/gateway/uniform/football/）"))
json.dump(result_rows, open(os.path.join(BASE, "reports/data/20261017_results_official.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

out = dict(
    backtest_id="20261017_saturday",
    date="2026-10-17", day="周六", ticket_id="261017",
    fetched_at="2026-10-18（官方 JSON lastUpdateTime 见接口）",
    result_source="体彩官方 getUniformMatchResultV1（/gateway/uniform/football/）；周六023-030 官方 matchDate=2026-10-18，按 matchId 对齐归档；30 场全部 matchResultStatus=2 已开奖",
    summary=summary, tally=tally_out, byConf=byconf,
    results=rows, hit_rates=dict(
        dir=dict(merged=tally["dirMerged"], first=tally["dirFirst"], second=tally["dirSecond"], missed=miss_dir),
        hhad=dict(merged=tally["hhadMerged"], first=tally["hhadFirst"], second=tally["hhadSecond"], missed=miss_hhad),
        ttg=dict(hit=tally["ttg"]), hafu=dict(hit=tally["hafu"]), crs=dict(hit=tally["crs"]),
        htScore=dict(hit=tally["htScore"]), size=dict(hit=tally["sizeHit"]), krecBand=dict(hit=tally["krecBand"]),
    ),
    parlays=parlays,
    parlay_stats=dict(total=parlay_total, hit=parlay_hit, rate=f"{parlay_hit / parlay_total * 100:.1f}%", by_type=pstats),
    source_files=dict(
        predictions="reports/data/20261017_predictions.json",
        analysis_report="reports/analysis/20261017_saturday_analysis_zhihu.md",
        backtest_report="reports/backtest/backtest_20261017_saturday_zhihu.md",
        results_official="reports/data/20261017_results_official.json",
        results_raw="reports/data/20261017_results_raw.json",
        lessons="memory/lessons/20261017_saturday_lessons.json"),
)
os.makedirs(os.path.join(BASE, "memory/backtests/20261017_saturday"), exist_ok=True)
json.dump(out, open(os.path.join(BASE, "memory/backtests/20261017_saturday/backtest.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n已输出 memory/backtests/20261017_saturday/backtest.json 与 reports/data/20261017_results_official.json")

