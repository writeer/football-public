# -*- coding: utf-8 -*-
"""2026-11-11（周三）当日4场日联赛杯模型计算（DC+NB+Skellam+MC；L79 λ仅由基本面，不反解赔率）"""
import json, math, io
import numpy as np

MAXG = 11
RHO = -0.08
DRAW_INFL = 1.05
rng = np.random.default_rng(20261111)

raw = json.load(io.open('reports/data/20261111_raw.json', encoding='utf-8'))
by_num = {m['matchNumStr']: m for m in raw['matches']}


def pois_pmf(k, mu):
    return math.exp(-mu) * mu**k / math.factorial(k)


def nb_pmf(k, mu, gamma):
    r = 1 / gamma
    p = r / (r + mu)
    logc = math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
    return math.exp(logc) * p**r * (1 - p)**k


def tau(i, j, lh, la):
    if i == 0 and j == 0: return 1 - lh * la * RHO
    if i == 0 and j == 1: return 1 + lh * RHO
    if i == 1 and j == 0: return 1 + la * RHO
    if i == 1 and j == 1: return 1 - RHO
    return 1.0


def matrix(lh, la, dc=True):
    m = np.zeros((MAXG, MAXG))
    for i in range(MAXG):
        for j in range(MAXG):
            m[i, j] = pois_pmf(i, lh) * pois_pmf(j, la) * (tau(i, j, lh, la) if dc else 1)
    return m / m.sum()


def probs(m):
    h = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i > j)
    d = sum(m[i, i] for i in range(MAXG))
    return {'home': h, 'draw': d, 'away': 1 - h - d}


def analyze(key, home, away, league, lh, la, htf, single=False, tags=''):
    m = matrix(lh, la, True)
    p = probs(m)
    p['draw'] *= DRAW_INFL
    scale = (1 - p['draw']) / (p['home'] + p['away'])
    p['home'] *= scale; p['away'] *= scale

    pm = matrix(lh, la, False); pp = probs(pm)
    gamma = 0.25 / (lh + la)
    nbm = np.zeros((MAXG, MAXG))
    for i in range(MAXG):
        for j in range(MAXG):
            nbm[i, j] = nb_pmf(i, lh, gamma) * nb_pmf(j, la, gamma)
    nbm /= nbm.sum(); pnb = probs(nbm)

    sk = {}
    for i in range(MAXG):
        for j in range(MAXG):
            sk[i - j] = sk.get(i - j, 0) + m[i, j]
    sk_h = sum(v for k, v in sk.items() if k > 0); sk_d = sk.get(0, 0)
    sk_a = 1 - sk_h - sk_d

    N = 20000
    hs = rng.poisson(lh, N); as_ = rng.poisson(la, N)
    mc = {'home': float(np.mean(hs > as_)), 'draw': float(np.mean(hs == as_)), 'away': float(np.mean(hs < as_))}

    r = by_num[key]
    mk = r.get('markets', {})
    line = mk.get('hhad', {}).get('goalLine', -1)
    zhg = {
        'line': line,
        'win': float(sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i - j) + line > 0)),
        'push': float(sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i - j) + line == 0)),
        'lose': float(sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i - j) + line < 0)),
    }

    ttg = {}
    for t in range(7):
        ttg[str(t)] = float(sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i + j == t))
    ttg['7+'] = float(sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i + j >= 7))

    h1 = matrix(lh * htf, la * htf, False)
    h2 = matrix(lh * (1 - htf), la * (1 - htf), False)
    htft = {k: 0.0 for k in ['HH', 'HD', 'HA', 'DH', 'DD', 'DA', 'AH', 'AD', 'AA']}
    for i1 in range(MAXG):
        for j1 in range(MAXG):
            if h1[i1, j1] < 1e-10: continue
            r1 = 'H' if i1 > j1 else ('D' if i1 == j1 else 'A')
            for i2 in range(MAXG):
                for j2 in range(MAXG):
                    if h2[i2, j2] < 1e-10: continue
                    r2 = 'H' if (i1 + i2) > (j1 + j2) else ('D' if (i1 + i2) == (j1 + j2) else 'A')
                    htft[r1 + r2] += h1[i1, j1] * h2[i2, j2]
    ssum = sum(htft.values()); htft = {k: v / ssum for k, v in htft.items()}
    htft = dict(sorted(htft.items(), key=lambda x: -x[1]))

    ht_scores = sorted(((f"{i}-{j}", float(h1[i, j])) for i in range(6) for j in range(6)), key=lambda x: -x[1])[:5]

    kdist = {}
    for i in range(MAXG):
        for j in range(MAXG):
            kdist[i - j] = kdist.get(i - j, 0) + float(m[i, j])
    kdist = dict(sorted(kdist.items(), key=lambda x: -x[1]))
    k_dist = max(kdist.items(), key=lambda x: x[1])
    if p['home'] >= max(p['draw'], p['away']):
        k_rec = max(((k, v) for k, v in kdist.items() if k >= 1), key=lambda x: x[1])
    elif p['draw'] >= p['away']:
        k_rec = (0, kdist[0])
    else:
        k_rec = max(((k, v) for k, v in kdist.items() if k <= -1), key=lambda x: x[1])

    top_scores = sorted(((f"{i}-{j}", float(m[i, j])) for i in range(MAXG) for j in range(MAXG)), key=lambda x: -x[1])[:10]

    had_odds = {o['key']: o['odds'] for o in mk.get('had', {}).get('outcomes', [])} or None
    hhad_odds = ({'handicap': mk['hhad']['goalLine'], **{o['key']: o['odds'] for o in mk['hhad']['outcomes']}}
                 if mk.get('hhad') else None)
    market = None
    if had_odds:
        inv = [1 / had_odds['home'], 1 / had_odds['draw'], 1 / had_odds['away']]
        s = sum(inv)
        market = {'home': inv[0] / s, 'draw': inv[1] / s, 'away': inv[2] / s, 'overround': s - 1}

    return {
        'num': key, 'league': league, 'home': home, 'away': away, 'tags': tags, 'time': r['matchTime'],
        'lambda': {'home': lh, 'away': la, 'total': lh + la},
        'probs_final': p, 'poisson': pp, 'negative_binomial': pnb,
        'skellam': {'home': sk_h, 'draw': sk_d, 'away': sk_a}, 'monte_carlo': mc,
        'market': market, 'handicap': zhg,
        'ttg': ttg, 'htft': htft, 'ht_scores': ht_scores,
        'k_dist': {'k': k_dist[0], 'p': k_dist[1]}, 'k_rec': {'k': k_rec[0], 'p': k_rec[1]},
        'kdist': kdist, 'top_scores': top_scores,
        'single': {'is_single': single, 'uplift': None},
        'odds': {'had': had_odds, 'hhad': hhad_odds,
                 'crs': {o['key']: o['odds'] for o in mk.get('crs', {}).get('outcomes', [])},
                 'ttg': {o['key']: o['odds'] for o in mk.get('ttg', {}).get('outcomes', [])},
                 'hafu': {o['key']: o['odds'] for o in mk.get('hafu', {}).get('outcomes', [])}}
    }


# λ 口径：J1 2026-2027 场均每队 1.475 球（413球/280队次）→ 攻强/防弱 → 主1.12/客0.90（L79，未用赔率反解）
# 攻强 = 队均进球/1.475；防弱 = 队均失球/1.475
AVG = 413 / 280.0
GF = {'横滨水手': 21, '鹿岛鹿角': 29, '神户胜利': 23, '町田泽维': 30,
      '川崎前锋': 28, '柏太阳神': 31, '浦和红钻': 23, '大阪樱花': 16}
GA = {'横滨水手': 15, '鹿岛鹿角': 24, '神户胜利': 14, '町田泽维': 10,
      '川崎前锋': 24, '柏太阳神': 20, '浦和红钻': 29, '大阪樱花': 25}
PLAYED = 14


def lam(home, away):
    ah = (GF[home] / PLAYED) / AVG
    dh = (GA[home] / PLAYED) / AVG
    aa = (GF[away] / PLAYED) / AVG
    da = (GA[away] / PLAYED) / AVG
    return AVG * 1.12 * ah * da, AVG * 0.90 * aa * dh


cfg = [
    ('周三001', '横滨水手', '鹿岛鹿角', '日联赛杯',
     'J1第7 vs 第6（14轮）；杯赛单场、轮换不确定；场地/天气/伤停/首发信息缺失'),
    ('周三002', '神户胜利', '町田泽维', '日联赛杯',
     'J1第5 vs 第4（14轮）；町田场均失0.71联赛最少；杯赛单场、轮换不确定；场地/天气/伤停/首发信息缺失'),
    ('周三003', '川崎前锋', '柏太阳神', '日联赛杯',
     'J1第8 vs 第2（14轮）；双方场均合计失3.14；杯赛单场、轮换不确定；场地/天气/伤停/首发信息缺失'),
    ('周三004', '浦和红钻', '大阪樱花', '日联赛杯',
     'J1第9 vs 第11（14轮）；浦和场均失2.07、樱花场均进1.14；杯赛单场、轮换不确定；场地/天气/伤停/首发信息缺失；用户投注端告知为单关（L273）'),
]

# 005/006：英锦标赛（matchDate=2026-11-12），λ 沿用 11-09 同场基本面口径
# 英甲/英乙场均进失球→攻强/防弱→主1.12/客0.90；跨级对阵英乙进攻×0.85、防守×1.10（L79，未用赔率反解）
CFG_EN = [
    ('周三005', '谢周三', '阿克宁顿', '英锦标赛', 1.88, 1.01,
     '跨级（英甲9 vs 英乙9），英乙进攻×0.85；北区A组，谢周三主场；杯赛轮换不确定；场地/天气/伤停/首发信息缺失'),
    ('周三006', '巴恩斯利', '奥德汉姆', '英锦标赛', 1.25, 1.12,
     '跨级（英甲23 vs 英乙18），英乙进攻×0.85；北区G组，巴恩斯利12场2胜状态差；杯赛轮换不确定；场地/天气/伤停/首发信息缺失'),
]

out = {}
for c in cfg:
    lh, la = lam(c[1], c[2])
    r = analyze(c[0], c[1], c[2], c[3], round(lh, 3), round(la, 3), 0.45, single=False, tags=c[4])
    out[c[0]] = r
    mk = r['market']
    print(c[0], c[1], 'vs', c[2], 'λ', round(lh, 2), round(la, 2),
          '| HAD', {k: round(v * 100, 1) for k, v in r['probs_final'].items()},
          '| 市场', ({k: round(v * 100, 1) for k, v in mk.items() if k != 'overround'} if mk else None),
          '| 让', {k: round(v * 100, 1) for k, v in r['handicap'].items()},
          '| TTG', [(k, round(v * 100, 1)) for k, v in list(r['ttg'].items())[:5]],
          '| HTFT', [(k, round(v * 100, 1)) for k, v in list(r['htft'].items())[:4]])
    print('   top', [(s, round(p * 100, 1)) for s, p in r['top_scores'][:6]])
    print('   kdist', r['k_dist'], 'krec', r['k_rec'])

json.dump(out, io.open('reports/data/20261111_model_output.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

for c in CFG_EN:
    r = analyze(c[0], c[1], c[2], c[3], c[4], c[5], 0.45, single=False, tags=c[6])
    out[c[0]] = r
    mk = r['market']
    print(c[0], c[1], 'vs', c[2], 'λ', c[4], c[5],
          '| HAD', {k: round(v * 100, 1) for k, v in r['probs_final'].items()},
          '| 市场', ({k: round(v * 100, 1) for k, v in mk.items() if k != 'overround'} if mk else None),
          '| 让', {k: round(v * 100, 1) for k, v in r['handicap'].items()},
          '| TTG', [(k, round(v * 100, 1)) for k, v in list(r['ttg'].items())[:5]],
          '| HTFT', [(k, round(v * 100, 1)) for k, v in list(r['htft'].items())[:4]])
    print('   top', [(s, round(p * 100, 1)) for s, p in r['top_scores'][:6]])
    print('   kdist', r['k_dist'], 'krec', r['k_rec'])

json.dump(out, io.open('reports/data/20261111_model_output.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved reports/data/20261111_model_output.json', len(out), 'matches')
