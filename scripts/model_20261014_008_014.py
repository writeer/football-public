# -*- coding: utf-8 -*-
"""
261014 第5步模型计算 — 场次008-014
DC/Poisson比分矩阵(n=16) + Skellam净胜球分布 + 双轨众数(k_dist/k_rec) +
让球三方向(规则52a) + TTG + 半全场(规则66) + 单关平局上修(规则63)
输出: reports/data/20261014_model_008_014.json
"""
import json, math, os

BASE = r"E:\VibeCoding\football\reports\data"

def pois(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)

N = 16  # 矩阵阶数(极端实力差强制>=16)

def score_matrix(lh, la, n=N):
    M = [[pois(i, lh) * pois(j, la) for j in range(n)] for i in range(n)]
    s = sum(sum(r) for r in M)
    return [[v / s for v in r] for r in M]

def analyze(lh, la, ht_coef, goal_line, single_boost=0.0, notes=""):
    M = score_matrix(lh, la)
    n = N
    # HAD
    pH = pD = pA = 0.0
    # net goal distribution d[k], k=i-j, k in [-(n-1), n-1]
    d = {}
    # TTG
    ttg = [0.0] * (2 * n)
    for i in range(n):
        for j in range(n):
            v = M[i][j]
            if i > j: pH += v
            elif i == j: pD += v
            else: pA += v
            k = i - j
            d[k] = d.get(k, 0.0) + v
            ttg[i + j] += v
    # rule 63 single-match draw boost (additive pp, H/A rescale)
    had_raw = {"H": pH, "D": pD, "A": pA}
    had = dict(had_raw)
    if single_boost > 0:
        had["D"] = pD + single_boost
        rest = 1.0 - had["D"]
        old_rest = pH + pA
        had["H"] = pH / old_rest * rest
        had["A"] = pA / old_rest * rest
    # k_dist: global mode, no bucket merging
    k_dist = max(d.keys(), key=lambda k: d[k])
    # HAD first direction (post-boost)
    dir_first = max(had, key=had.get)
    # k_rec: mode within direction interval
    if dir_first == "H":
        interval = [k for k in d if k >= 1]
    elif dir_first == "A":
        interval = [k for k in d if k <= -1]
    else:
        interval = [0]
    k_rec = max(interval, key=lambda k: d[k])
    # in-band candidates fixed net = k_rec
    band = []
    i = 0 if k_rec <= 0 else k_rec
    while True:
        j = i - k_rec
        if j < 0: break
        if i >= n or j >= n:
            i += 1
            if i > n: break
            continue
        band.append((f"{i}-{j}", M[i][j]))
        i += 1
        if i > n: break
    band.sort(key=lambda x: -x[1])
    # HHAD three directions: adjusted net = net + goal_line (goal_line>0 = home +1)
    rH = rD = rA = 0.0  # 让胜/让平/让负
    for k, v in d.items():
        adj = k + goal_line
        if adj > 0: rH += v
        elif adj == 0: rD += v
        else: rA += v
    # TTG top2
    ttg_items = sorted([(k, ttg[k]) for k in range(2*n)], key=lambda x: -x[1])
    # over/under 2.5
    p_over25 = sum(ttg[k] for k in range(3, 2*n))
    p_under25 = 1.0 - p_over25
    p_6plus = sum(ttg[k] for k in range(6, 2*n))
    # HT matrix
    lh2, la2 = lh * ht_coef, la * ht_coef
    M2 = score_matrix(lh2, la2)
    htH = htD = htA = 0.0
    for i in range(n):
        for j in range(n):
            v = M2[i][j]
            if i > j: htH += v
            elif i == j: htD += v
            else: htA += v
    # HT top scores
    ht_scores = sorted(((f"{i}-{j}", M2[i][j]) for i in range(n) for j in range(n)),
                       key=lambda x: -x[1])[:3]
    # HTFT independent approx: P(ht,ft) = P_HT(ht) * P_FT(ft)
    ft = {"H": had["H"], "D": had["D"], "A": had["A"]}
    ht_res = {"H": htH, "D": htD, "A": htA}
    hta = {}
    for hk, hv in ht_res.items():
        for fk, fv in ft.items():
            hta[(hk, fk)] = hv * fv
    # 平平 boost for high/mid-high ht draw tiers
    if ht_coef <= 0.40:
        hta[("D", "D")] *= 1.10
    elif ht_coef <= 0.42:
        hta[("D", "D")] *= 1.06
    # normalize
    s = sum(hta.values())
    hta = {k: v/s for k, v in hta.items()}
    hta_sorted = sorted(hta.items(), key=lambda x: -x[1])
    LABEL = {("H","H"):"胜胜",("H","D"):"胜平",("H","A"):"胜负",
             ("D","H"):"平胜",("D","D"):"平平",("D","A"):"平负",
             ("A","H"):"负胜",("A","D"):"负平",("A","A"):"负负"}
    hta_top3 = [(LABEL[k], v) for k, v in hta_sorted[:3]]
    # score TOP5 from full matrix
    top5 = sorted(((f"{i}-{j}", M[i][j]) for i in range(n) for j in range(n)),
                  key=lambda x: -x[1])[:5]
    # net mode raw proportions
    return {
        "lh": lh, "la": la, "lambda_total": lh + la,
        "had_raw": had_raw, "had": had, "had_boost": single_boost,
        "dir_first": dir_first,
        "d": {str(k): v for k, v in sorted(d.items())},
        "k_dist": k_dist, "k_dist_pct": d[k_dist],
        "k_rec": k_rec, "k_rec_pct": d[k_rec],
        "band": band[:3],
        "hhad": {"让胜": rH, "让平": rD, "让负": rA},
        "goal_line": goal_line,
        "ttg_top2": ttg_items[:2],
        "ttg_6plus": p_6plus,
        "over25": p_over25, "under25": p_under25,
        "ttg_dist": {str(k): ttg[k] for k in range(8)},
        "ht_top3": ht_scores,
        "htft_top3": hta_top3,
        "score_top5": top5,
        "ht_coef": ht_coef,
    }

# ---------- 逐场参数(取自verified.md区间中点 + 修正项) ----------
MATCHES = [
    {"num": "008", "home": "罗马", "away": "皇家马德里", "league": "欧冠",
     "lh": 1.10, "la": 1.62, "ht_coef": 0.45, "goal_line": +1, "single": True, "boost": 0.08,
     "size_override": "常规正常球(2-3)下沿·偏小球", "size_first": 2, "size_second": 3},
    {"num": "009", "home": "博德闪耀", "away": "多特蒙德", "league": "欧冠",
     "lh": 1.425, "la": 1.375, "ht_coef": 0.45, "goal_line": +1, "single": False, "boost": 0.0,
     "size_override": "常规正常球(2-3)上沿·候选大球下沿", "size_first": 3, "size_second": 2},
    {"num": "010", "home": "皇家贝蒂斯", "away": "波尔图", "league": "欧冠",
     "lh": 1.60, "la": 1.15, "ht_coef": 0.45, "goal_line": -1, "single": False, "boost": 0.0,
     "size_override": "常规正常球(2-3)", "size_first": 2, "size_second": 3},
    {"num": "011", "home": "曼城", "away": "巴黎圣日耳曼", "league": "欧冠",
     "lh": 1.775, "la": 1.325, "ht_coef": 0.42, "goal_line": -1, "single": True, "boost": 0.11,
     "size_override": "常规正常球(2-3)上沿·大球(4-5)下沿", "size_first": 3, "size_second": 4},
    {"num": "012", "home": "阿斯顿维拉", "away": "费内巴切", "league": "欧冠",
     "lh": 1.625, "la": 1.125, "ht_coef": 0.42, "goal_line": -1, "single": False, "boost": 0.0,
     "size_override": "常规正常球(2-3)上沿", "size_first": 2, "size_second": 3},
    {"num": "013", "home": "弗鲁米嫩塞", "away": "帕尔梅拉斯", "league": "解放者杯",
     "lh": 0.80, "la": 0.80, "ht_coef": 0.40, "goal_line": +1, "single": False, "boost": 0.0,
     "size_override": "闷战超小球(0-1)→小球(1-2)", "size_first": 1, "size_second": 2},
    {"num": "014", "home": "圣路易斯城", "away": "温哥华白帽", "league": "美职",
     "lh": 1.55, "la": 1.025, "ht_coef": 0.42, "goal_line": -1, "single": False, "boost": 0.0,
     "size_override": "常规正常球(2-3)", "size_first": 2, "size_second": 3},
]

# ---------- 市场去水概率(来自verified.md/raw) ----------
MARKET = {
    "008": {"H": 0.255, "D": 0.224, "A": 0.521},
    "009": {"H": 0.286, "D": 0.230, "A": 0.484},
    "010": {"H": 0.484, "D": 0.253, "A": 0.263},
    "011": {"H": 0.439, "D": 0.243, "A": 0.319},
    "012": {"H": 0.594, "D": 0.221, "A": 0.184},
    "013": {"H": 0.328, "D": 0.331, "A": 0.341},
    "014": {"H": 0.422, "D": 0.241, "A": 0.338},
}

results = []
for m in MATCHES:
    r = analyze(m["lh"], m["la"], m["ht_coef"], m["goal_line"], m["boost"])
    mk = MARKET[m["num"]]
    div = {k: round((r["had"][k] - mk[k]) * 100, 1) for k in "HDA"}
    r["market"] = mk
    r["model_vs_market_div_pp"] = div
    r.update({k: m[k] for k in ("num","home","away","league","single","size_override","size_first","size_second")})
    results.append(r)

out = {"date": "2026-10-14", "sale_day": "261014", "step": "5_model",
       "matches_covered": "008-014", "matches": results}
with open(os.path.join(BASE, "20261014_model_008_014.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# 打印摘要
for r in results:
    print(f"=== {r['num']} {r['home']} vs {r['away']} ===")
    print(f"  λ {r['lh']:.3f}/{r['la']:.3f} total={r['lambda_total']:.2f}")
    print(f"  HAD(raw): H{r['had_raw']['H']*100:.1f} D{r['had_raw']['D']*100:.1f} A{r['had_raw']['A']*100:.1f}",
          f"| boosted: H{r['had']['H']*100:.1f} D{r['had']['D']*100:.1f} A{r['had']['A']*100:.1f}",
          f"| market: H{r['market']['H']*100:.1f} D{r['market']['D']*100:.1f} A{r['market']['A']*100:.1f}",
          f"| div{list(r['model_vs_market_div_pp'].values())}")
    print(f"  k_dist={r['k_dist']}({r['k_dist_pct']*100:.1f}%) k_rec={r['k_rec']}({r['k_rec_pct']*100:.1f}%) first={r['dir_first']}")
    print(f"  band: {[(b[0], round(b[1]*100,1)) for b in r['band']]}")
    h = r['hhad']
    print(f"  HHAD(line{r['goal_line']}): 让胜{h['让胜']*100:.1f} 让平{h['让平']*100:.1f} 让负{h['让负']*100:.1f}")
    print(f"  TTG top2: {[(t[0], round(t[1]*100,1)) for t in r['ttg_top2']]} O2.5={r['over25']*100:.1f}% 6+={r['ttg_6plus']*100:.1f}%")
    print(f"  score TOP5: {[(s[0], round(s[1]*100,1)) for s in r['score_top5']]}")
    print(f"  HTFT: {[(s[0], round(s[1]*100,1)) for s in r['htft_top3']]} | HT scores: {[(s[0], round(s[1]*100,1)) for s in r['ht_top3']]}")
