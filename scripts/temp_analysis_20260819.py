# -*- coding: utf-8 -*-
# 2026-08-19 周三6场 模型计算（步骤5：模型计算引擎）
import json, math

ODDS_FILE = r"C:\Users\admin\AppData\Local\Temp\trae\toolcall-output\f8c26ce4-932a-4018-84b2-21db0420eae5.txt"

raw = open(ODDS_FILE, encoding="utf-8").read()
s = raw.split("The MCP server responded with: ", 1)[1].strip()
arr = json.loads(s)
data = json.loads(arr[0]["text"])

# 每场lambda（步骤2-4基本面+联赛修正后确定）
# lh/la: 主/客进球lambda; hcp: 体彩让球线(主队+, 让球为负)
CFG = {
    "周三001": dict(lh=1.15, la=1.30, hcp=+1),
    "周三002": dict(lh=2.00, la=0.55, hcp=-1),
    "周三003": dict(lh=1.10, la=1.18, hcp=+1),
    "周三006": dict(lh=1.85, la=0.95, hcp=-1),
    "周三007": dict(lh=1.25, la=1.55, hcp=-1),
    "周三008": dict(lh=1.75, la=0.95, hcp=-1),
}

def pois(l, k):
    return math.exp(-l) * l**k / math.factorial(k)

def dc_matrix(lh, la, rho=-0.10, maxg=9):
    m = [[pois(lh, i) * pois(la, j) for j in range(maxg+1)] for i in range(maxg+1)]
    m[0][0] *= 1 - lh*la*rho
    m[0][1] *= 1 + lh*rho
    m[1][0] *= 1 + la*rho
    m[1][1] *= 1 - rho
    tot = sum(sum(r) for r in m)
    return [[v/tot for v in row] for row in m]

def sign(x):
    return (x > 0) - (x < 0)

def result_probs(mat):
    h = d = a = 0.0
    for i in range(len(mat)):
        for j in range(len(mat)):
            s = sign(i - j)
            if s > 0: h += mat[i][j]
            elif s == 0: d += mat[i][j]
            else: a += mat[i][j]
    return h, d, a

def hcp_probs(mat, hcp):
    w = dr = l = 0.0
    for i in range(len(mat)):
        for j in range(len(mat)):
            adj = i + hcp - j
            s = sign(adj)
            if s > 0: w += mat[i][j]
            elif s == 0: dr += mat[i][j]
            else: l += mat[i][j]
    return w, dr, l

def ttg_dist(mat, maxg=8):
    dist = [0.0]*9
    for i in range(len(mat)):
        for j in range(len(mat)):
            t = i + j
            dist[t if t <= 8 else 8] += mat[i][j]
    return dist

def htft_probs(lh, la, frac1=0.45):
    m1 = dc_matrix(lh*frac1, la*frac1, rho=-0.10)
    m2 = dc_matrix(lh*(1-frac1), la*(1-frac1), rho=-0.05)
    r1 = result_probs(m1)
    out = {(x, y): 0.0 for x in (-1, 0, 1) for y in (-1, 0, 1)}
    for i1 in range(len(m1)):
        for j1 in range(len(m1)):
            h1 = sign(i1 - j1)
            p1 = m1[i1][j1]
            for i2 in range(len(m2)):
                for j2 in range(len(m2)):
                    ft = sign(i1 + i2 - (j1 + j2))
                    out[(h1, ft)] += p1 * m2[i2][j2]
    return out

ZH = {1: "胜", 0: "平", -1: "负"}

def blend(model, market, w=0.78):
    return tuple(w*m + (1-w)*mk for m, mk in zip(model, market))

for m in data["matches"]:
    key = m["matchNumStr"]
    if key not in CFG: continue
    c = CFG[key]
    lh, la, hcp = c["lh"], c["la"], c["hcp"]
    mat = dc_matrix(lh, la)
    # 市场noVig
    had = m["markets"]["had"]["outcomes"]
    mkt = tuple(x["noVigProb"] for x in had)  # h,d,a
    mod = result_probs(mat)
    fus = blend(mod, mkt)
    hp = hcp_probs(mat, hcp)
    hhhad = m["markets"].get("hhad", {}).get("outcomes")
    mkt_h = tuple(x.get("noVigProb", 0) for x in hhhad) if hhhad else (0,0,0)
    fus_h = blend(hp, mkt_h) if hhhad else hp
    ttg = ttg_dist(mat)
    # 比分TOP6
    sc = []
    for i in range(7):
        for j in range(7):
            sc.append((mat[i][j], i, j))
    sc.sort(reverse=True)
    crs_odds = {}
    if "crs" in m["markets"]:
        for o in m["markets"]["crs"]["outcomes"]:
            crs_odds[o["labelZh"]] = o["odds"]
    print("=" * 80)
    print(f"{key} {m['league']['abbName']} {m['home']['abbName']} vs {m['away']['abbName']}")
    print(f"lambda: 主{lh:.2f}/客{la:.2f} (总{lh+la:.2f})")
    print(f"模型HAD: 胜{mod[0]*100:.1f}% 平{mod[1]*100:.1f}% 负{mod[2]*100:.1f}%")
    print(f"市场noVig: 胜{mkt[0]*100:.1f}% 平{mkt[1]*100:.1f}% 负{mkt[2]*100:.1f}%")
    print(f"融合HAD: 胜{fus[0]*100:.1f}% 平{fus[1]*100:.1f}% 负{fus[2]*100:.1f}%")
    print(f"让球({hcp:+d}) 模型: 让胜{hp[0]*100:.1f}% 让平{hp[1]*100:.1f}% 让负{hp[2]*100:.1f}%")
    if hhhad:
        print(f"让球({hcp:+d}) 融合: 让胜{fus_h[0]*100:.1f}% 让平{fus_h[1]*100:.1f}% 让负{fus_h[2]*100:.1f}%  赔率: {[x['odds'] for x in hhhad]}")
    print("比分TOP6:", " > ".join(f"{i}-{j}({p*100:.1f}%)" for p, i, j in sc[:6]))
    ttg_top = sorted(range(9), key=lambda k: -ttg[k])[:3]
    print("总进球:", " ".join(f"{k if k<8 else '7+'}球{ttg[k]*100:.1f}%" for k in ttg_top))
    hf = htft_probs(lh, la)
    hf_sorted = sorted(hf.items(), key=lambda kv: -kv[1])[:5]
    print("半全场TOP5:", " > ".join(f"{ZH[a]}{ZH[b]}({p*100:.1f}%)" for (a, b), p in hf_sorted))
    m1 = dc_matrix(lh*0.45, la*0.45)
    hs = sorted(((m1[i][j], i, j) for i in range(5) for j in range(5)), reverse=True)[:3]
    print("半场比分TOP3:", " > ".join(f"{i}-{j}({p*100:.1f}%)" for p, i, j in hs))
    # 甜蜜区比分：模型概率>=8%且赔率>=8.0
    sweet = []
    for p, i, j in sc[:20]:
        lab = f"{'胜' if i>j else '平' if i==j else '负'}{'其它' if max(i,j)>=4 else str(max(i,j)+1 if i==j else '')}"
        for o_name, o_odds in crs_odds.items():
            pass
    if crs_odds:
        sweet = []
        for p, i, j in sc[:25]:
            o_key = f"{i}:{j}"
            # 体彩CRS label格式: "0:0" 或 "胜其它"等
            od = crs_odds.get(o_key) or crs_odds.get(f"{j}:{i}")
            if od and p >= 0.08 and od >= 8.0:
                sweet.append((i, j, p, od))
        print("甜蜜区(概率>=8%&赔率>=8):", ", ".join(f"{i}-{j}({p*100:.1f}% @{od})" for i, j, p, od in sweet[:6]) or "无")
    hafu = m["markets"].get("hafu", {}).get("outcomes")
    if hafu:
        h_sorted = sorted(hafu, key=lambda x: x["odds"])[:6]
        print("HAFU赔率低6(最可能):", " ".join(f"{x['labelZh']}@{x['odds']}" for x in h_sorted))
    ttg_mkt = m["markets"].get("ttg", {}).get("outcomes")
    if ttg_mkt:
        t_sorted = sorted(ttg_mkt, key=lambda x: x["odds"])[:4]
        print("总进球赔率低4:", " ".join(f"{x['labelZh']}@{x['odds']}" for x in t_sorted))
