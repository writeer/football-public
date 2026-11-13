# -*- coding: utf-8 -*-
"""2026-11-03 周二竞彩11场模型计算（DC + NB + Skellam + MC）"""
import json, math
import numpy as np

MAXG = 11
RHO = -0.08
DRAW_INFL = 1.05
rng = np.random.default_rng(20261103)

matches_raw = json.load(open('reports/data/20261103_matches.json', encoding='utf-8'))
raw_by_num = {m['num']: m for m in matches_raw}


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


def single_uplift(gap):
    """规则63：平局上修（相对增幅）。gap=首选与平局概率差(pp)"""
    if gap <= 10: return 1.13
    if gap <= 20: return 1.11
    return 1.08


def analyze(num, home, away, league, lh, la, htf, single=False):
    m = matrix(lh, la, True)
    p = probs(m)
    p['draw'] *= DRAW_INFL
    scale = (1-p['draw'])/(p['home']+p['away'])
    p['home'] *= scale; p['away'] *= scale
    first = max(p, key=p.get)
    uplift_note = None
    if single:
        gap = (p[first]-p['draw'])*100
        f = single_uplift(gap)
        p['draw'] *= f
        s2 = (1-p['draw'])/(p['home']+p['away'])
        p['home'] *= s2; p['away'] *= s2
        uplift_note = {'applied': True, 'gap_pp': round(gap, 1), 'factor': f,
                       'draw_after': p['draw']}

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
    if p['home'] >= max(p['draw'], p['away']):
        k_rec = max(((k, v) for k, v in kdist.items() if k >= 1), key=lambda x: x[1])
    elif p['draw'] >= p['away']:
        k_rec = (0, kdist[0])
    else:
        k_rec = max(((k, v) for k, v in kdist.items() if k <= -1), key=lambda x: x[1])

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
        'market': market, 'handicap': zhg,
        'ttg': ttg, 'htft': htft, 'ht_scores': ht_scores,
        'k_dist': {'k': k_dist[0], 'p': k_dist[1]}, 'k_rec': {'k': k_rec[0], 'p': k_rec[1]},
        'kdist': kdist, 'top_scores': top_scores,
        'single': {'is_single': single, 'uplift': uplift_note},
        'odds': {'had': had, 'hhad': hhad,
                 'crs': {o['key']: o['odds'] for o in raw.get('crs', [])},
                 'ttg': {o['key']: o['odds'] for o in raw.get('ttg', [])},
                 'hafu': {o['key']: o['odds'] for o in raw.get('hafu', [])}}
    }


cfg = [
    ('周二001', '纽卡斯尔喷气机', '上海海港', '亚冠精英', 1.25, 2.05, 0.40, False),
    ('周二002', '柏太阳神', '大田市民', '亚冠精英', 2.25, 1.40, 0.40, False),
    ('周二003', '曼谷港务', '北京国安', '亚冠精英', 1.30, 1.85, 0.40, True),
    ('周二004', '加拉塔萨雷', '斯图加特', '欧冠', 2.25, 1.80, 0.42, False),
    ('周二005', '马德里竞技', '拜仁慕尼黑', '欧冠', 1.55, 1.70, 0.42, True),
    ('周二006', 'LASK林茨', '布拉迪斯拉发', '欧冠', 2.40, 0.95, 0.42, False),
    ('周二007', '费耶诺德', '国际米兰', '欧冠', 1.25, 1.50, 0.42, False),
    ('周二008', '曼彻斯特联', '罗马', '欧冠', 1.60, 1.55, 0.42, False),
    ('周二009', '巴塞罗那', '阿斯顿维拉', '欧冠', 3.15, 1.25, 0.42, False),
    ('周二010', '比利亚雷亚尔', '巴黎圣日尔曼', '欧冠', 1.45, 2.35, 0.42, False),
    ('周二011', '博德闪耀', '里尔', '欧冠', 2.05, 1.15, 0.42, False),
]

out = {}
for c in cfg:
    r = analyze(*c)
    out[c[0]] = r
    mk = r['market']
    print(c[0], c[1], 'vs', c[2], 'λ', c[4], c[5], '总', round(c[4]+c[5], 2),
          '| HAD', {k: round(v*100, 1) for k, v in r['probs_final'].items()},
          '| 市场', {k: round(v*100, 1) for k, v in mk.items()},
          '| 让', {k: round(v*100, 1) for k, v in r['handicap'].items()},
          '| TTG', [(k, round(v*100, 1)) for k, v in r['ttg'].items() if v > 0.15],
          '| HTFT', [(k, round(v*100, 1)) for k, v in list(r['htft'].items())[:4]])

json.dump(out, open('reports/data/20261103_model_output.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved reports/data/20261103_model_output.json')
