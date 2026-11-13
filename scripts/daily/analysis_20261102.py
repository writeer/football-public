# -*- coding: utf-8 -*-
"""2026-11-02 周一006 纽卡斯尔联 vs 埃弗顿（英超）单场模型计算"""
import json, math
import numpy as np


def pois_pmf(k, mu):
    return math.exp(-mu) * mu**k / math.factorial(k)


def nb_pmf(k, mu, gamma):
    r = 1/gamma
    p = r/(r+mu)
    logc = math.lgamma(k+r) - math.lgamma(r) - math.lgamma(k+1)
    return math.exp(logc) * p**r * (1-p)**k

MAXG = 11
LAM_H, LAM_A = 1.35, 1.12   # 修正后lambda（含xG回归/伤停/H2H）
RHO = -0.08                 # DC低比分修正
DRAW_INFL = 1.05            # Platt平局上修

def dc_tau(i, j, lh, la, rho=RHO):
    if i == 0 and j == 0: return 1 - lh*la*rho
    if i == 0 and j == 1: return 1 + lh*rho
    if i == 1 and j == 0: return 1 + la*rho
    if i == 1 and j == 1: return 1 - rho
    return 1.0

def matrix(lh, la, rho=RHO):
    m = np.zeros((MAXG, MAXG))
    for i in range(MAXG):
        for j in range(MAXG):
            m[i, j] = pois_pmf(i, lh)*pois_pmf(j, la)*dc_tau(i, j, lh, la, rho)
    return m/m.sum()

def probs(m):
    h = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i > j)
    d = sum(m[i, i] for i in range(MAXG))
    a = 1-h-d
    return {'home': h, 'draw': d, 'away': a}

m = matrix(LAM_H, LAM_A)
p = probs(m)
# 平局上修并等比例压缩胜负
p['draw'] *= DRAW_INFL
scale = (1-p['draw'])/(p['home']+p['away'])
p['home'] *= scale; p['away'] *= scale

# 标准泊松（无DC）
def pois_matrix(lh, la):
    mm = np.zeros((MAXG, MAXG))
    for i in range(MAXG):
        for j in range(MAXG):
            mm[i, j] = pois_pmf(i, lh)*pois_pmf(j, la)
    return mm/mm.sum()
pm = pois_matrix(LAM_H, LAM_A)
pp = probs(pm)

# 负二项（VMR=1.25 -> gamma=(VMR-1)/lambda）
VMR = 1.25
gamma = (VMR-1)/(LAM_H+LAM_A)
nbm = np.zeros((MAXG, MAXG))
for i in range(MAXG):
    for j in range(MAXG):
        nbm[i, j] = nb_pmf(i, LAM_H, gamma)*nb_pmf(j, LAM_A, gamma)
nbm /= nbm.sum()
pnb = probs(nbm)

# Skellam
sk = {k: 0.0 for k in range(-8, 9)}
for i in range(MAXG):
    for j in range(MAXG):
        k = i-j
        if -8 <= k <= 8:
            sk[k] += m[i, j]
sk_h = sum(v for k, v in sk.items() if k > 0)
sk_d = sk[0]
sk_a = sum(v for k, v in sk.items() if k < 0)

# 蒙特卡洛
rng = np.random.default_rng(20261102)
N = 20000
hs = rng.poisson(LAM_H, N); as_ = rng.poisson(LAM_A, N)
mc_h = np.mean(hs > as_); mc_d = np.mean(hs == as_); mc_a = np.mean(hs < as_)
scores = {}
for h, a in zip(hs, as_):
    key = f"{h}-{a}"
    scores[key] = scores.get(key, 0)+1
mc_scores = sorted(((k, v/N) for k, v in scores.items()), key=lambda x: -x[1])[:12]

# 让球 -1
zh_sheng = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i-j >= 2)
zh_ping = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i-j == 1)
zh_fu = 1-zh_sheng-zh_ping

# 总进球
ttg = {}
for t in range(0, 8):
    if t < 7:
        ttg[str(t)] = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i+j == t)
    else:
        ttg['7+'] = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i+j >= 7)

# 半场/全场：半场lambda系数0.42（英超中高半场平局档）
F = 0.42
h1 = pois_matrix(LAM_H*F, LAM_A*F)
h2 = pois_matrix(LAM_H*(1-F), LAM_A*(1-F))
htft = {k: 0.0 for k in ['HH','HD','HA','DH','DD','DA','AH','AD','AA']}
for i1 in range(MAXG):
    for j1 in range(MAXG):
        p1 = h1[i1, j1]
        if p1 < 1e-9: continue
        r1 = 'H' if i1 > j1 else ('D' if i1 == j1 else 'A')
        for i2 in range(MAXG):
            for j2 in range(MAXG):
                p2 = h2[i2, j2]
                if p2 < 1e-9: continue
                r2 = 'H' if (i1+i2) > (j1+j2) else ('D' if (i1+i2) == (j1+j2) else 'A')
                htft[r1+r2] += p1*p2
s = sum(htft.values()); htft = {k: v/s for k, v in htft.items()}

# 半场比分
ht_scores = []
for i in range(6):
    for j in range(6):
        ht_scores.append((f"{i}-{j}", h1[i, j]))
ht_scores.sort(key=lambda x: -x[1])

# 净胜球分布
kdist = {}
for i in range(MAXG):
    for j in range(MAXG):
        kdist[i-j] = kdist.get(i-j, 0)+m[i, j]
kdist = dict(sorted(kdist.items(), key=lambda x: -x[1]))
k_dist = max(kdist.items(), key=lambda x: x[1])
# 推荐众数：主胜区间 k>=1
k_rec = max(((k, v) for k, v in kdist.items() if k >= 1), key=lambda x: x[1])

# 比分TOP12（按最终方向概率缩放不影响比分内部）
top_scores = sorted(((f"{i}-{j}", m[i, j]) for i in range(MAXG) for j in range(MAXG)), key=lambda x: -x[1])[:12]

# Shin 去水
odds = [2.14, 3.25, 2.75]
def shin(odds):
    def f(z):
        return sum(math.sqrt(z+(1-z)*(1/o)**2) for o in odds)-1
    lo, hi = 1e-12, 0.5
    for _ in range(200):
        mid = (lo+hi)/2
        if f(mid) > 0: hi = mid
        else: lo = mid
    z = (lo+hi)/2
    ps = [math.sqrt(z+(1-z)*(1/o)**2) for o in odds]
    return z, [x/sum(ps) for x in ps]
z, shin_p = shin(odds)

out = {
    'match': '周一006 纽卡斯尔联 vs 埃弗顿（英超第9轮）',
    'lambda': {'home': LAM_H, 'away': LAM_A, 'total': LAM_H+LAM_A},
    'dc_rho': RHO, 'draw_inflate': DRAW_INFL, 'vmr': VMR,
    'probs_final': p,
    'poisson': pp,
    'negative_binomial': pnb,
    'skellam': {'home': sk_h, 'draw': sk_d, 'away': sk_a},
    'monte_carlo': {'home': mc_h, 'draw': mc_d, 'away': mc_a},
    'shin': {'z': z, 'home': shin_p[0], 'draw': shin_p[1], 'away': shin_p[2]},
    'handicap_minus1': {'win': zh_sheng, 'push': zh_ping, 'lose': zh_fu},
    'ttg': ttg,
    'htft': dict(sorted(htft.items(), key=lambda x: -x[1])),
    'ht_scores': ht_scores[:6],
    'k_dist': {'k': k_dist[0], 'p': k_dist[1]},
    'k_rec': {'k': k_rec[0], 'p': k_rec[1]},
    'kdist': kdist,
    'top_scores': top_scores,
    'mc_scores': mc_scores,
}
print(json.dumps(out, ensure_ascii=False, indent=1))
json.dump(out, open('reports/data/20261102_006_model.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
