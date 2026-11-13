# -*- coding: utf-8 -*-
"""2026-11-02 周一竞彩9场模型计算（通用版）"""
import json, math
import numpy as np

MAXG = 11
RHO = -0.08
DRAW_INFL = 1.05
rng = np.random.default_rng(20261102)

matches_raw = json.load(open('reports/data/20261102_matches.json', encoding='utf-8'))
raw_by_num = {m['num']: m for m in matches_raw}

cfg = [
    # num, home, away, league, lam_h, lam_a, ht_factor
    ('周一001', '国际图尔库', '赫尔辛基火花', '芬超', 1.55, 0.85, 0.38),
    ('周一002', '萨索洛', '佛罗伦萨', '意甲', 1.85, 1.45, 0.38),
    ('周一003', '哥德堡盖斯', 'AIK索尔纳', '瑞超', 1.40, 0.95, 0.38),
    ('周一004', '亚特兰大', '帕尔马', '意甲', 1.76, 0.70, 0.38),
    ('周一005', '圣旺红星', '南锡', '法乙', 1.10, 1.05, 0.38),
    ('周一006', '纽卡斯尔联', '埃弗顿', '英超', 1.35, 1.12, 0.42),
    ('周一007', '拉科鲁尼亚', '奥萨苏纳', '西甲', 1.55, 1.10, 0.38),
    ('周一008', '本菲卡', '阿尔维卡', '葡超', 2.45, 0.90, 0.38),
    ('周一009', '布拉干蒂诺RB', '桑托斯', '巴甲', 1.65, 1.05, 0.42),
]


def pois_pmf(k, mu):
    return math.exp(-mu) * mu**k / math.factorial(k)


def nb_pmf(k, mu, gamma):
    r = 1/gamma
    p = r/(r+mu)
    logc = math.lgamma(k+r) - math.lgamma(r) - math.lgamma(k+1)
    return math.exp(logc) * p**r * (1-p)**k


def tau(i, j, lh, la):
    if i == 0 and j == 0: return 1 - lh*la*RHO
    if i == 0 and j == 1: return 1 + lh*RHO
    if i == 1 and j == 0: return 1 + la*RHO
    if i == 1 and j == 1: return 1 - RHO
    return 1.0


def matrix(lh, la, dc=True):
    m = np.zeros((MAXG, MAXG))
    for i in range(MAXG):
        for j in range(MAXG):
            m[i, j] = pois_pmf(i, lh)*pois_pmf(j, la)*(tau(i, j, lh, la) if dc else 1)
    return m/m.sum()


def probs(m):
    h = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i > j)
    d = sum(m[i, i] for i in range(MAXG))
    return {'home': h, 'draw': d, 'away': 1-h-d}


def analyze(num, home, away, league, lh, la, htf):
    m = matrix(lh, la, True)
    p = probs(m)
    p['draw'] *= DRAW_INFL
    scale = (1-p['draw'])/(p['home']+p['away'])
    p['home'] *= scale; p['away'] *= scale

    pm = matrix(lh, la, False); pp = probs(pm)
    gamma = 0.25/(lh+la)
    nbm = np.zeros((MAXG, MAXG))
    for i in range(MAXG):
        for j in range(MAXG):
            nbm[i, j] = nb_pmf(i, lh, gamma)*nb_pmf(j, la, gamma)
    nbm /= nbm.sum(); pnb = probs(nbm)

    sk = {}
    for i in range(MAXG):
        for j in range(MAXG):
            sk[i-j] = sk.get(i-j, 0)+m[i, j]
    sk_h = sum(v for k, v in sk.items() if k > 0); sk_d = sk.get(0, 0)
    sk_a = 1-sk_h-sk_d

    N = 20000
    hs = rng.poisson(lh, N); as_ = rng.poisson(la, N)
    mc = {'home': float(np.mean(hs > as_)), 'draw': float(np.mean(hs == as_)), 'away': float(np.mean(hs < as_))}

    zh = {
        'win': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i-j >= 2),
        'push': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i-j == 1),
        'lose': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i-j <= 0),
    }
    line = raw_by_num[num]['hhad']['goalLine'] if raw_by_num[num].get('hhad') else -1
    zhg = {
        'line': line,
        'win': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i-j) + line > 0),
        'push': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i-j) + line == 0),
        'lose': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i-j) + line < 0),
    }

    ttg = {}
    for t in range(7):
        ttg[str(t)] = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i+j == t)
    ttg['7+'] = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i+j >= 7)

    h1 = matrix(lh*htf, la*htf, False)
    h2 = matrix(lh*(1-htf), la*(1-htf), False)
    htft = {k: 0.0 for k in ['HH', 'HD', 'HA', 'DH', 'DD', 'DA', 'AH', 'AD', 'AA']}
    for i1 in range(MAXG):
        for j1 in range(MAXG):
            if h1[i1, j1] < 1e-10: continue
            r1 = 'H' if i1 > j1 else ('D' if i1 == j1 else 'A')
            for i2 in range(MAXG):
                for j2 in range(MAXG):
                    if h2[i2, j2] < 1e-10: continue
                    r2 = 'H' if (i1+i2) > (j1+j2) else ('D' if (i1+i2) == (j1+j2) else 'A')
                    htft[r1+r2] += h1[i1, j1]*h2[i2, j2]
    ssum = sum(htft.values()); htft = {k: v/ssum for k, v in htft.items()}
    htft = dict(sorted(htft.items(), key=lambda x: -x[1]))

    ht_scores = sorted(((f"{i}-{j}", h1[i, j]) for i in range(6) for j in range(6)), key=lambda x: -x[1])[:5]

    kdist = {}
    for i in range(MAXG):
        for j in range(MAXG):
            kdist[i-j] = kdist.get(i-j, 0)+m[i, j]
    kdist = dict(sorted(kdist.items(), key=lambda x: -x[1]))
    k_dist = max(kdist.items(), key=lambda x: x[1])
    k_rec = max(((k, v) for k, v in kdist.items() if k >= 1), key=lambda x: x[1]) if p['home'] >= max(p['draw'], p['away']) else \
            (max(((k, v) for k, v in kdist.items() if k == 0), key=lambda x: x[1]) if p['draw'] >= p['away'] else
             max(((k, v) for k, v in kdist.items() if k <= -1), key=lambda x: x[1]))

    top_scores = sorted(((f"{i}-{j}", m[i, j]) for i in range(MAXG) for j in range(MAXG)), key=lambda x: -x[1])[:10]

    raw = raw_by_num[num]
    had = {o['key']: o['odds'] for o in raw['had']} if raw.get('had') else None
    hhad = ({'handicap': raw['hhad']['goalLine'], **{o['key']: o['odds'] for o in raw['hhad']['outcomes']}}
            if raw.get('hhad') else None)
    market = None
    if had:
        inv = [1/had['home'], 1/had['draw'], 1/had['away']]
        s = sum(inv)
        market = {'home': inv[0]/s, 'draw': inv[1]/s, 'away': inv[2]/s, 'overround': s-1}

    return {
        'num': num, 'league': league, 'home': home, 'away': away,
        'lambda': {'home': lh, 'away': la, 'total': lh+la},
        'probs_final': p, 'poisson': pp, 'negative_binomial': pnb,
        'skellam': {'home': sk_h, 'draw': sk_d, 'away': sk_a}, 'monte_carlo': mc,
        'market': market, 'handicap_minus1': zh, 'handicap': zhg,
        'ttg': ttg, 'htft': htft, 'ht_scores': ht_scores,
        'k_dist': {'k': k_dist[0], 'p': k_dist[1]}, 'k_rec': {'k': k_rec[0], 'p': k_rec[1]},
        'kdist': kdist, 'top_scores': top_scores,
        'odds': {'had': had, 'hhad': hhad,
                 'crs': {o['key']: o['odds'] for o in raw.get('crs', [])},
                 'ttg': {o['key']: o['odds'] for o in raw.get('ttg', [])},
                 'hafu': {o['key']: o['odds'] for o in raw.get('hafu', [])}}
    }


out = {}
for c in cfg:
    r = analyze(*c)
    out[c[0]] = r
    print(c[0], c[1], 'vs', c[2], 'λ', c[4], c[5], '总', round(c[4]+c[5], 2),
          '| HAD', {k: round(v*100, 1) for k, v in r['probs_final'].items()},
          '| 让', {k: round(v*100, 1) for k, v in r['handicap_minus1'].items()},
          '| TTG', [(k, round(v*100, 1)) for k, v in r['ttg'].items() if v > 0.12],
          '| HTFT', [(k, round(v*100, 1)) for k, v in list(r['htft'].items())[:4]])

json.dump(out, open('reports/data/20261102_model_output.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved reports/data/20261102_model_output.json')
