# -*- coding: utf-8 -*-
"""
2026-10-09 周五回测验证脚本
预测口径：reports/analysis/20261009_friday_analysis_zhihu.md（报告公布推荐）
赛果来源：直播吧/Sportradar/Fotmob/俱乐部官网/bundesliga.com/LaLiga官网/zerozero 等，≥2源交叉验证
"""
import json

# ---------- 预测（报告公布口径） ----------
# dir_first/dir_second: home/draw/away; hhad: (line, first, second); ttg: [top1, top2]
# htft_top3: 依报告排序（首选在前）; top5: 报告比分TOP5
P = {
    "周五001": dict(league="韩职", home="仁川联", away="浦项制铁",
        dir_first="home", dir_second="draw", df_p=0.400, ds_p=0.310,
        hhad=(-1, "away", "draw"), hhad_p=(0.587, 0.235),
        ttg=("2", "1"), ttg_p=(0.287, 0.217),
        htft=["平平", "胜胜", "平胜"], htft_p=(0.220, 0.209, 0.177),
        top5=["1-0", "2-0", "2-1", "3-0", "3-1"], k_consistent=False),
    "周五002": dict(league="日职", home="柏太阳神", away="神户胜利船",
        dir_first="draw", dir_second="home", df_p=0.379, ds_p=0.365,
        hhad=(-1, "away", "draw"), hhad_p=(0.556, 0.224),
        ttg=("2", "3"), ttg_p=(0.260, 0.221),
        htft=["平平", "负负", "胜胜"], htft_p=(0.170, 0.193, 0.193),
        top5=["1-1", "0-0", "2-2", "3-3", "1-0"], k_consistent=True),
    "周五003": dict(league="德乙", home="海登海姆", away="凯泽斯劳滕",
        dir_first="home", dir_second="away", df_p=0.522, ds_p=0.244,
        hhad=(-1, "away", "home"), hhad_p=(0.454, 0.320),
        ttg=("3", "2"), ttg_p=(0.222, 0.220),
        htft=["胜胜", "平胜", "负负"], htft_p=(0.334, 0.176, 0.129),
        top5=["2-1", "2-0", "1-0", "3-1", "3-0"], k_consistent=False),
    "周五004": dict(league="瑞超", home="IFK哥德堡", away="韦斯特罗斯",
        dir_first="home", dir_second="draw", df_p=0.597, ds_p=0.212,
        hhad=(-1, "away", "home"), hhad_p=(0.383, 0.391),
        ttg=("3", "2"), ttg_p=(0.220, 0.209),
        htft=["平胜", "胜胜", "平平"], htft_p=(0.205, 0.366, 0.119),
        top5=["2-1", "2-0", "3-1", "1-0", "3-0"], k_consistent=False),
    "周五005": dict(league="挪超", home="布兰", away="维京",
        dir_first="away", dir_second="home", df_p=0.429, ds_p=0.342,
        hhad=(+1, "home", "away"), hhad_p=(0.576, 0.227),
        ttg=("3", "2"), ttg_p=(0.217, 0.201),
        htft=["负负", "胜胜", "平负"], htft_p=(0.260, 0.211, 0.132),
        top5=["1-2", "0-2", "1-3", "0-1", "2-3"], k_consistent=False),
    "周五006": dict(league="荷甲", home="PSV埃因霍温", away="海伦芬",
        dir_first="home", dir_second="draw", df_p=0.772, ds_p=0.130,
        hhad=(-2, "draw", "home"), hhad_p=(0.194, 0.445),
        ttg=("4", "3"), ttg_p=(0.191, 0.171),
        htft=["胜胜", "平胜", "平平"], htft_p=(0.576, 0.186, 0.054),
        top5=["3-1", "3-0", "2-1", "4-1", "2-0"], k_consistent=True),
    "周五007": dict(league="荷乙", home="赫拉克勒斯", away="瓦尔韦克",
        dir_first="home", dir_second="draw", df_p=0.653, ds_p=0.191,
        hhad=(-1, "draw", "home"), hhad_p=(0.221, 0.456),
        ttg=("3", "2"), ttg_p=(0.216, 0.197),
        htft=["胜胜", "平胜", "平平"], htft_p=(0.441, 0.197, 0.096),
        top5=["2-1", "2-0", "3-1", "3-0", "1-0"], k_consistent=True),
    "周五008": dict(league="德甲", home="多特蒙德", away="云达不来梅",
        dir_first="home", dir_second="draw", df_p=0.722, ds_p=0.160,
        hhad=(-1, "home", "away"), hhad_p=(0.560, 0.241),
        ttg=("3", "4"), ttg_p=(0.203, 0.195),
        htft=["胜胜", "平胜", "平平"], htft_p=(0.519, 0.199, 0.074),
        top5=["2-0", "2-1", "3-0", "3-1", "4-0"], k_consistent=True),
    "周五009": dict(league="法甲", home="朗斯", away="里昂",
        dir_first="draw", dir_second="home", df_p=0.456, ds_p=0.318,
        hhad=(-1, "away", "home"), hhad_p=(0.533, 0.258),
        ttg=("3", "2"), ttg_p=(0.219, 0.208),
        htft=["平胜", "负负", "胜胜"], htft_p=(0.131, 0.225, 0.225),
        top5=["1-1", "2-2", "0-0", "3-3", "2-1"], k_consistent=True),
    "周五010": dict(league="英冠", home="西汉姆联", away="女王公园巡游者",
        dir_first="home", dir_second="draw", df_p=0.638, ds_p=0.196,
        hhad=(-1, "draw", "home"), hhad_p=(0.221, 0.445),
        ttg=("3", "2"), ttg_p=(0.216, 0.196),
        htft=["平胜", "胜胜", "平平"], htft_p=(0.212, 0.406, 0.107),
        top5=["2-1", "2-0", "3-1", "3-0", "1-0"], k_consistent=True),
    "周五011": dict(league="西甲", home="马拉加", away="西班牙人",
        dir_first="away", dir_second="home", df_p=0.373, ds_p=0.352,
        hhad=(+1, "home", "draw"), hhad_p=(0.619, 0.207),
        ttg=("2", "3"), ttg_p=(0.263, 0.220),
        htft=["平平", "负负", "胜胜"], htft_p=(0.173, 0.199, 0.186),
        top5=["1-2", "0-1", "0-2", "1-3", "0-3"], k_consistent=False),
    "周五012": dict(league="葡超", home="布拉加", away="里斯本竞技",
        dir_first="away", dir_second="home", df_p=0.457, ds_p=0.287,
        hhad=(+1, "home", "away"), hhad_p=(0.538, 0.243),
        ttg=("2", "3"), ttg_p=(0.241, 0.224),
        htft=["平负", "负负", "胜胜"], htft_p=(0.172, 0.253, 0.153),
        top5=["1-2", "0-2", "0-1", "1-3", "0-3"], k_consistent=False),
}

# ---------- 赛果（多源交叉验证） ----------
R = {
    "周五001": {"ht": "3-0", "ft": "3-0", "hg": 3, "ag": 0, "result": "home", "htft": "胜胜"},
    "周五002": {"ht": "1-0", "ft": "4-2", "hg": 4, "ag": 2, "result": "home", "htft": "胜胜"},
    "周五003": {"ht": "0-0", "ft": "0-0", "hg": 0, "ag": 0, "result": "draw", "htft": "平平"},
    "周五004": {"ht": "1-0", "ft": "1-0", "hg": 1, "ag": 0, "result": "home", "htft": "胜胜"},
    "周五005": {"ht": "0-2", "ft": "0-2", "hg": 0, "ag": 2, "result": "away", "htft": "负负"},
    "周五006": {"ht": "1-0", "ft": "2-0", "hg": 2, "ag": 0, "result": "home", "htft": "胜胜"},
    "周五007": {"ht": "0-0", "ft": "3-0", "hg": 3, "ag": 0, "result": "home", "htft": "平胜"},
    "周五008": {"ht": "0-0", "ft": "2-2", "hg": 2, "ag": 2, "result": "draw", "htft": "平平"},
    "周五009": {"ht": "1-0", "ft": "2-1", "hg": 2, "ag": 1, "result": "home", "htft": "胜胜"},
    "周五010": {"ht": "0-1", "ft": "1-1", "hg": 1, "ag": 1, "result": "draw", "htft": "负平"},
    "周五011": {"ht": "0-1", "ft": "1-1", "hg": 1, "ag": 1, "result": "draw", "htft": "负平"},
    "周五012": {"ht": "1-0", "ft": "1-3", "hg": 1, "ag": 3, "result": "away", "htft": "胜负"},
}

dm = {"home": "主胜", "draw": "平", "away": "客胜"}
hm = {"home": "让胜", "draw": "让平", "away": "让负"}

stats = dict(n=0, dir_first=0, dir_second=0, hhad_first=0, hhad_second=0,
             ttg_hit=0, htft_hit=0, htft_first=0, score_hit=0,
             div_first=0, div_n=0, div_draw=0, cons_first=0, cons_n=0, cons_draw=0)

detail = []
for mn, p in P.items():
    r = R[mn]
    # 方向
    dstat = "✅首" if r["result"] == p["dir_first"] else ("✅次" if r["result"] == p["dir_second"] else "❌")
    if dstat == "✅首": stats["dir_first"] += 1
    if dstat == "✅次": stats["dir_second"] += 1
    if not p["k_consistent"]:
        stats["div_n"] += 1
        if dstat == "✅首": stats["div_first"] += 1
        if r["result"] == "draw": stats["div_draw"] += 1
    else:
        stats["cons_n"] += 1
        if dstat == "✅首": stats["cons_first"] += 1
        if r["result"] == "draw": stats["cons_draw"] += 1
    # 让球
    line, hfirst, hsecond = p["hhad"]
    adj_h, adj_a = r["hg"] + line, r["ag"]
    hact = "home" if adj_h > adj_a else ("draw" if adj_h == adj_a else "away")
    hstat = "✅首" if hact == hfirst else ("✅次" if hact == hsecond else "❌")
    if hstat == "✅首": stats["hhad_first"] += 1
    if hstat == "✅次": stats["hhad_second"] += 1
    # 总进球
    tg = r["hg"] + r["ag"]
    tstat = "✅首" if str(tg) == p["ttg"][0] else ("✅(2)" if str(tg) == p["ttg"][1] else "❌")
    if tstat != "❌": stats["ttg_hit"] += 1
    # 半全场
    if r["htft"] == p["htft"][0]:
        fstat = "✅首"
    elif r["htft"] in p["htft"][1:]:
        fstat = f"✅({p['htft'].index(r['htft'])+1})"
    else:
        fstat = "❌"
    if fstat != "❌": stats["htft_hit"] += 1
    if fstat == "✅首": stats["htft_first"] += 1
    # 比分
    actual_score = r["ft"]
    if actual_score in p["top5"]:
        sstat = f"✅({p['top5'].index(actual_score)+1})"
        stats["score_hit"] += 1
    else:
        sstat = "❌"
    stats["n"] += 1
    detail.append(dict(num=mn, league=p["league"], match=f'{p["home"]} vs {p["away"]}',
        pred_dir=f'{dm[p["dir_first"]]}/{dm[p["dir_second"]]}', actual_dir=dm[r["result"]], dir_stat=dstat,
        pred_hhad=f'让({line:+d}){hm[hfirst]}/让({line:+d}){hm[hsecond]}', actual_hhad=f'让({line:+d}){hm[hact]}', hhad_stat=hstat,
        pred_ttg=f'{p["ttg"][0]}球/{p["ttg"][1]}球', actual_ttg=f"{tg}球", ttg_stat=tstat,
        pred_htft="/".join(p["htft"]), actual_htft=r["htft"], htft_stat=fstat,
        pred_top5=",".join(p["top5"]), actual_score=actual_score, score_stat=sstat,
        ht=r["ht"], ft=r["ft"]))

n = stats["n"]
summary = dict(
    n=n,
    dir_all=f"{stats['dir_first']+stats['dir_second']}/{n} = {(stats['dir_first']+stats['dir_second'])/n*100:.1f}%",
    dir_first_only=f"{stats['dir_first']}/{n} = {stats['dir_first']/n*100:.1f}%",
    hhad_all=f"{stats['hhad_first']+stats['hhad_second']}/{n} = {(stats['hhad_first']+stats['hhad_second'])/n*100:.1f}%",
    hhad_first_only=f"{stats['hhad_first']}/{n} = {stats['hhad_first']/n*100:.1f}%",
    ttg=f"{stats['ttg_hit']}/{n} = {stats['ttg_hit']/n*100:.1f}%",
    htft=f"{stats['htft_hit']}/{n} = {stats['htft_hit']/n*100:.1f}%",
    htft_first=f"{stats['htft_first']}/{n} = {stats['htft_first']/n*100:.1f}%",
    score=f"{stats['score_hit']}/{n} = {stats['score_hit']/n*100:.1f}%",
    div_first=f"{stats['div_first']}/{stats['div_n']} = {stats['div_first']/stats['div_n']*100:.1f}%",
    div_draw=f"{stats['div_draw']}/{stats['div_n']} = {stats['div_draw']/stats['div_n']*100:.1f}%",
    cons_first=f"{stats['cons_first']}/{stats['cons_n']} = {stats['cons_first']/stats['cons_n']*100:.1f}%",
    cons_draw=f"{stats['cons_draw']}/{stats['cons_n']} = {stats['cons_draw']/stats['cons_n']*100:.1f}%",
)

print("=" * 100)
print("周五12场回测")
for d in detail:
    print(f"\n{d['num']} {d['match']} ({d['league']}) 半场{d['ht']} 全场{d['ft']}")
    print(f"  方向 {d['pred_dir']} → 实际{d['actual_dir']} {d['dir_stat']} | 让球 {d['pred_hhad']} → 实际{d['actual_hhad']} {d['hhad_stat']}")
    print(f"  总进球 {d['pred_ttg']} → 实际{d['actual_ttg']} {d['ttg_stat']} | 半全场 {d['pred_htft']} → 实际{d['actual_htft']} {d['htft_stat']}")
    print(f"  比分 [{d['pred_top5']}] → 实际{d['actual_score']} {d['score_stat']}")
print("\n" + "=" * 100)
for k, v in summary.items():
    if k != "n":
        print(f"{k}: {v}")

# ---------- 规则67带内判定 ----------
band = {
    "周五002": ["1-1", "0-0", "2-2"], "周五006": ["3-1", "2-0", "4-2"],
    "周五007": ["2-1", "1-0", "3-2"], "周五008": ["2-0", "3-1", "4-2"],
    "周五010": ["2-1", "1-0", "3-2"], "周五009": ["1-1", "2-2", "0-0"],
}
print("\n规则67带内判定（正向5场+单关009）:")
for mn, b in band.items():
    hit = R[mn]["ft"] in b
    print(f"  {mn}: 实际{R[mn]['ft']} 带内{b} → {'✅exact' if hit else '❌'}")

# ---------- 串关回测 ----------
parlays = [
    ("稳健方向串", "方向", [("周五008", "home"), ("周五007", "home"), ("周五010", "home")]),
    ("价值方向串", "方向", [("周五004", "home"), ("周五003", "home"), ("周五012", "away")]),
    ("单关方向串", "方向", [("周五002", "draw"), ("周五009", "draw")]),
    ("稳健让球串", "让球", [("周五011", ("home", +1)), ("周五005", ("home", +1))]),
    ("价值让球串", "让球", [("周五001", ("away", -1)), ("周五003", ("away", -1)), ("周五009", ("away", -1))]),
    ("半全场串A", "半全场", [("周五007", "胜胜"), ("周五008", "胜胜"), ("周五010", "平胜")]),
    ("半全场串B", "半全场", [("周五005", "负负"), ("周五012", "负负"), ("周五011", "负负")]),
    ("方向+半全场A", "混合", [("周五003", "home"), ("周五008", "home"), ("周五010", "胜胜")]),
    ("方向+半全场B", "混合", [("周五004", "home"), ("周五007", "home"), ("周五012", "负负")]),
    ("连续编号混合串A", "混合", [("周五001", "home"), ("周五002", "draw")]),
    ("连续编号混合串B", "混合", [("周五003", "home"), ("周五004", "胜胜")]),
    ("总进球串A", "娱乐", [("周五007", ("ttg", "3")), ("周五008", ("ttg", "3")), ("周五010", ("ttg", "2"))]),
    ("总进球串B", "娱乐", [("周五006", ("ttg", "4")), ("周五002", ("ttg", "2")), ("周五005", ("ttg", "3"))]),
    ("连续编号总进球串①", "娱乐", [("周五001", ("ttg", "2")), ("周五002", ("ttg", "3"))]),
    ("连续编号总进球串②", "娱乐", [("周五004", ("ttg", "2")), ("周五005", ("ttg", "3"))]),
    ("高赔半全场串A", "娱乐", [("周五006", "胜胜"), ("周五008", "胜胜"), ("周五010", "平胜")]),
    ("高赔半全场串B", "娱乐", [("周五005", "负负"), ("周五011", "负负"), ("周五012", "平负")]),
    ("连续编号高赔半全场串①", "娱乐", [("周五007", "胜胜"), ("周五008", "平胜")]),
    ("连续编号高赔半全场串②", "娱乐", [("周五003", "胜胜"), ("周五004", "平胜")]),
    ("混合串A", "娱乐", [("周五008", "胜胜"), ("周五010", ("ttg", "3"))]),
    ("混合串B", "娱乐", [("周五012", "负负"), ("周五006", ("ttg", "4"))]),
    ("连续编号混合总进球串①", "娱乐", [("周五010", "胜胜"), ("周五011", ("ttg", "2"))]),
    ("连续编号混合总进球串②", "娱乐", [("周五002", "平平"), ("周五003", ("ttg", "3"))]),
    ("稳健比分串", "娱乐", [("周五002", "1-1"), ("周五010", "2-1")]),
    ("搏冷比分串(4注)", "娱乐", [("周五008", ["1-1", "2-2"]), ("周五007", ["1-1", "2-2"])]),
    ("连续编号比分串①", "娱乐", [("周五007", "2-1"), ("周五008", "2-0")]),
    ("连续编号比分串②", "娱乐", [("周五006", "3-1"), ("周五007", "2-1")]),
    ("单挑比分①", "娱乐", [("周五008", "3-1")]),
    ("单挑比分②", "娱乐", [("周五002", "0-0")]),
]

def leg_hit(mn, cond):
    r = R[mn]
    if isinstance(cond, list):
        return any(leg_hit(mn, c) for c in cond)  # 搏冷串逐场2选1
    if isinstance(cond, str):
        if cond in ("home", "draw", "away"):
            return r["result"] == cond
        if len(cond) == 2:  # 半全场
            return r["htft"] == cond
        if len(cond) == 3 and "-" in cond:  # 比分
            return r["ft"] == cond
        return False
    kind, v = cond
    if kind == "home":
        return r["result"] == "home"
    if kind == "away":
        return r["result"] == "away"
    if kind == "draw":
        return r["result"] == "draw"
    if kind == "ttg":
        return str(r["hg"] + r["ag"]) == v
    # 让球 (dir, line)
    d, line = v if isinstance(v, tuple) else (cond, 0)
    adj = r["hg"] + line
    act = "home" if adj > r["ag"] else ("draw" if adj == r["ag"] else "away")
    return act == d

parlay_out = []
p_hit = 0
for name, typ, legs in parlays:
    res = []
    ok = True
    for mn, cond in legs:
        h = leg_hit(mn, cond)
        res.append((mn, h))
        ok = ok and h
    if ok: p_hit += 1
    parlay_out.append(dict(name=name, type=typ, legs=[f"{m}:{'✅' if h else '❌'}" for m, h in res], hit=ok))

# 让球串单独判定（稳健让球串/价值让球串）
def hhad_leg(mn, want_dir, line):
    r = R[mn]
    adj = r["hg"] + line
    act = "home" if adj > r["ag"] else ("draw" if adj == r["ag"] else "away")
    return act == want_dir

parlay_out[3]["legs"] = [f"011:{'✅' if hhad_leg('周五011','home',+1) else '❌'}", f"005:{'✅' if hhad_leg('周五005','home',+1) else '❌'}"]
parlay_out[3]["hit"] = all(hhad_leg(m, d, l) for m, (d, l) in [("周五011", ("home", +1)), ("周五005", ("home", +1))])
parlay_out[4]["legs"] = [f"001:{'✅' if hhad_leg('周五001','away',-1) else '❌'}", f"003:{'✅' if hhad_leg('周五003','away',-1) else '❌'}", f"009:{'✅' if hhad_leg('周五009','away',-1) else '❌'}"]
parlay_out[4]["hit"] = all(hhad_leg(m, d, l) for m, (d, l) in [("周五001", ("away", -1)), ("周五003", ("away", -1)), ("周五009", ("away", -1))])
p_hit = sum(1 for x in parlay_out if x["hit"])

print("\n串关回测:")
for x in parlay_out:
    print(f"  {x['name']}({x['type']}): {'+'.join(x['legs'])} → {'✅' if x['hit'] else '❌'}")
print(f"\n串关命中: {p_hit}/{len(parlay_out)} = {p_hit/len(parlay_out)*100:.1f}%")

# ---------- 输出JSON ----------
out = dict(date="2026-10-09", day="friday", summary=summary, stats=stats, detail=detail,
           parlay=dict(total=len(parlay_out), hit=p_hit, rate=f"{p_hit/len(parlay_out)*100:.1f}%", schemes=parlay_out),
           rule67=dict(band={k: v for k, v in band.items()}, results={k: R[k]["ft"] for k in band}))
with open(r"e:\VibeCoding\football\reports\data\20261009_friday_backtest_computed.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n已输出 reports/data/20261009_friday_backtest_computed.json")
