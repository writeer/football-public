# -*- coding: utf-8 -*-
"""2026-11-09（周一）在售4场英锦标赛模型计算（DC+NB+Skellam+MC；规则79 λ仅由基本面）"""
import json, math, io
import numpy as np

MAXG = 11
RHO = -0.08
DRAW_INFL = 1.05
rng = np.random.default_rng(20261109)

raw = json.load(io.open('reports/data/20261109_raw.json', encoding='utf-8'))
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
        'win': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i - j) + line > 0),
        'push': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i - j) + line == 0),
        'lose': sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if (i - j) + line < 0),
    }

    ttg = {}
    for t in range(7):
        ttg[str(t)] = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i + j == t)
    ttg['7+'] = sum(m[i, j] for i in range(MAXG) for j in range(MAXG) if i + j >= 7)

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
            kdist[i - j] = kdist.get(i - j, 0) + m[i, j]
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


# λ 口径：League One/Two 场均进失球 → 攻击/防守强度 → 主1.12/客0.90；跨级对阵低级别进攻×0.85、防守×1.10（规则79，未用赔率反解）
cfg = [
    ('周二001', '伯顿', '诺茨郡', '英锦标赛', 1.21, 1.05, 0.45, '同联赛（英甲15 vs 英甲17）；EFL Trophy 北区F组，轮换不确定，伤停/首发信息缺失'),
    ('周二002', '布罗姆利', '米尔顿', '英锦标赛', 1.24, 2.77, 0.45, '同联赛（英甲24 vs 英甲12）；布罗姆利场均失2.54，米尔顿近5场4胜；南区H组'),
    ('周三005', '谢周三', '阿克宁顿', '英锦标赛', 1.88, 1.01, 0.45, '跨级（英甲9 vs 英乙9），英乙进攻×0.85；北区A组，谢周三主场；轮换不确定'),
    ('周三006', '巴恩斯利', '奥德汉姆', '英锦标赛', 1.25, 1.12, 0.45, '跨级（英甲23 vs 英乙18），英乙进攻×0.85；北区G组，巴恩斯利12场2胜状态差'),
]

out = {}
for c in cfg:
    r = analyze(c[0], c[1], c[2], c[3], c[4], c[5], c[6], single=False, tags=c[7])
    out[c[0]] = r
    mk = r['market']
    print(c[0], c[1], 'vs', c[2], 'λ', round(c[4], 2), round(c[5], 2),
          '| HAD', {k: round(v * 100, 1) for k, v in r['probs_final'].items()},
          '| 市场', ({k: round(v * 100, 1) for k, v in mk.items() if k != 'overround'} if mk else None),
          '| 让', {k: round(v * 100, 1) for k, v in r['handicap'].items()},
          '| TTG', [(k, round(v * 100, 1)) for k, v in list(r['ttg'].items())[:5]],
          '| HTFT', [(k, round(v * 100, 1)) for k, v in list(r['htft'].items())[:4]])
    print('   top', [(s, round(p * 100, 1)) for s, p in r['top_scores'][:6]])
    print('   kdist', r['k_dist'], 'krec', r['k_rec'])

json.dump(out, io.open('reports/data/20261109_model_output.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved reports/data/20261109_model_output.json')
