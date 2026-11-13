# -*- coding: utf-8 -*-
"""2026-11-05 周四竞彩13场模型计算（DC + NB + Skellam + MC；规则79：λ 仅由基本面推导）"""
import json, math
import numpy as np

MAXG = 11
RHO = -0.08
DRAW_INFL = 1.05
rng = np.random.default_rng(20261105)

raw = json.load(open('reports/data/20261105_raw.json', encoding='utf-8'))
by_num = {m['matchNumStr']: m for m in raw['matches']}
NUM = {m['matchNumStr']: '周四' + m['matchNumStr'][-3:] for m in raw['matches']}


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


# λ 口径：国内联赛场均进失球/联赛等级差/伤停（规则32、76），未使用赔率反解（规则79）
cfg = [
    ('周四001', '町田泽维亚', '上海申花', '亚冠乙', 2.05, 0.85, 0.44, 'J1第3主场对中超第6；申花4主力伤缺（陈晋一赛季报销/朱辰杰/盖伊/李可）'),
    ('周四002', '水晶宫', '霍芬海姆', '欧罗巴', 1.60, 1.20, 0.43, '水晶宫英超第18（场均1.00/2.33）；霍村德甲第12（1.75/2.00）；萨尔+富安+里亚德缺阵'),
    ('周四003', '布拉格斯巴达', '伯恩茅斯', '欧罗巴', 0.90, 1.55, 0.43, '英超第8 vs 捷甲；伯恩茅斯5人未报名+3伤（斯科特/阿劳霍/米洛舍维奇等）'),
    ('周四004', '奈梅亨', '奥莫尼亚', '欧罗巴', 1.65, 1.10, 0.43, '奈梅亨荷甲第13、塔迪奇伤缺；奥莫尼亚欧联6分、客场3-0采列'),
    ('周四005', '皇家社会', '里昂', '欧罗巴', 1.55, 0.95, 0.43, '皇社西甲第5（1.82/1.82）；里昂法甲第3（1.67/0.78）但5人伤+尼亚卡特停赛'),
    ('周四006', 'AC米兰', '费伦茨瓦罗斯', '欧罗巴', 2.10, 0.72, 0.43, '米兰意甲第5（2.10/1.20）；费伦茨匈甲第3（1.82/0.91）；托莫里/丘库埃泽伤、迈尼昂停赛'),
    ('周四007', '特拉布宗体育', '弗赖堡', '欧协联', 1.30, 1.20, 0.43, '特拉布宗11人伤病+3人未报名（残阵）；弗赖堡德甲第3、3人伤'),
    ('周四008', '桑德兰', '萨格勒布迪纳摩', '欧罗巴', 2.00, 0.78, 0.43, '桑德兰英超第20但身价4.59亿；迪纳摩4人伤；桑德兰迪亚拉/蒙德尔/巴拉德伤缺'),
    ('周四009', '维戈塞尔塔', '圣吉尔联合', '欧罗巴', 1.00, 1.15, 0.43, '塞尔塔西甲第11（0.91/0.91）、5人伤；圣吉罗斯比甲第2不败（2.90/0.70）'),
    ('周四010', '本菲卡', '波兹南莱赫', '欧罗巴', 2.20, 0.72, 0.43, '本菲卡葡超第2（2.70/0.80）；莱赫波甲第1但6人伤缺；HAD未开售'),
    ('周四011', '阿尔克马尔', '尤文图斯', '欧罗巴', 1.20, 1.50, 0.43, 'AZ荷甲第5（1.82/1.18）；尤文8人伤+斯帕莱蒂明确轮换（3天后联赛）'),
    ('周四012', '勒沃库森', '马赛', '欧罗巴', 1.80, 0.90, 0.43, '勒沃库森8人伤（迪亚比/泰里耶/本塞吉尔/科法内/巴代等），仅希克一名中锋；马赛2人伤'),
    ('周四013', '帕尔梅拉斯', '里莫', '巴甲', 2.30, 0.60, 0.45, '帕尔梅拉斯巴甲第2（1.73/0.73）争冠；里莫第19（1.10/1.60）6+人缺阵'),
]

out = {}
for c in cfg:
    r = analyze(*c)
    out[c[0]] = r
    mk = r['market']
    print(c[0], c[1], 'vs', c[2], 'λ', c[4], c[5],
          '| HAD', {k: round(v * 100, 1) for k, v in r['probs_final'].items()},
          '| 市场', ({k: round(v * 100, 1) for k, v in mk.items() if k != 'overround'} if mk else None),
          '| 让', {k: round(v * 100, 1) for k, v in r['handicap'].items()},
          '| TTG', [(k, round(v * 100, 1)) for k, v in list(r['ttg'].items())[:5]],
          '| HTFT', [(k, round(v * 100, 1)) for k, v in list(r['htft'].items())[:4]])

json.dump(out, open('reports/data/20261105_model_output.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved reports/data/20261105_model_output.json')
