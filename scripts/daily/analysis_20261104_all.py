# -*- coding: utf-8 -*-
"""2026-11-04 周三竞彩12场模型计算（DC + NB + Skellam + MC；规则79：λ 仅由基本面推导）"""
import json, math
import numpy as np

MAXG = 11
RHO = -0.08
DRAW_INFL = 1.05
rng = np.random.default_rng(20261104)

matches_raw = json.load(open('reports/data/20261104_matches.json', encoding='utf-8'))
raw_by_num = {m['num']: m for m in matches_raw}


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


def analyze(num, home, away, league, lh, la, htf, single=False, tags=''):
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

    line = raw_by_num[num]['hhad']['goalLine'] if raw_by_num[num].get('hhad') else -1
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

    raw = raw_by_num[num]
    had = {o['key']: o['odds'] for o in raw['had']} if raw.get('had') else None
    hhad = ({'handicap': raw['hhad']['goalLine'], **{o['key']: o['odds'] for o in raw['hhad']['outcomes']}}
            if raw.get('hhad') else None)
    market = None
    if had:
        inv = [1 / had['home'], 1 / had['draw'], 1 / had['away']]
        s = sum(inv)
        market = {'home': inv[0] / s, 'draw': inv[1] / s, 'away': inv[2] / s, 'overround': s - 1}

    return {
        'num': num, 'league': league, 'home': home, 'away': away, 'tags': tags,
        'lambda': {'home': lh, 'away': la, 'total': lh + la},
        'probs_final': p, 'poisson': pp, 'negative_binomial': pnb,
        'skellam': {'home': sk_h, 'draw': sk_d, 'away': sk_a}, 'monte_carlo': mc,
        'market': market, 'handicap': zhg,
        'ttg': ttg, 'htft': htft, 'ht_scores': ht_scores,
        'k_dist': {'k': k_dist[0], 'p': k_dist[1]}, 'k_rec': {'k': k_rec[0], 'p': k_rec[1]},
        'kdist': kdist, 'top_scores': top_scores,
        'single': {'is_single': single, 'uplift': None},
        'single_match': {'applicable': False, 'reason': '官方接口 bettingSingle 全为 false 且用户未告知单关场次'},
        'odds': {'had': had, 'hhad': hhad,
                 'crs': {o['key']: o['odds'] for o in raw.get('crs', [])},
                 'ttg': {o['key']: o['odds'] for o in raw.get('ttg', [])},
                 'hafu': {o['key']: o['odds'] for o in raw.get('hafu', [])}}
    }


# λ 口径：国内联赛场均进失球 → 跨联赛等级校准（规则76），未使用任何赔率反解（规则79）
cfg = [
    ('周三001', '浦项制铁', '大阪钢巴', '亚冠精英', 1.10, 1.30, 0.42, '主队亚冠3连败0球；客队6人伤停'),
    ('周三002', '布里兰', '鹿岛鹿角', '亚冠精英', 1.15, 1.55, 0.42, '鹿岛J1第1、客场强'),
    ('周三003', '雷恩', '奥林匹亚科斯', '欧罗巴', 1.55, 1.15, 0.42, '雷恩场均2.22/2.11；奥林匹亚科斯防守强但客场'),
    ('周三004', '费内巴切', '利物浦', '欧冠', 1.30, 1.75, 0.43, '利物浦7人缺阵+格拉芬贝赫未随队'),
    ('周三005', '莱比锡红牛', '曼彻斯特城', '欧冠', 1.60, 1.85, 0.43, '双方攻强；莱比锡4人缺阵、城全员'),
    ('周三006', '波尔图', '那不勒斯', '欧冠', 1.55, 0.95, 0.41, '那不勒斯10人缺阵（规则32残阵）'),
    ('周三007', 'PSV埃因霍温', '布鲁日', '欧冠', 2.20, 1.85, 0.45, 'PSV场均3.18球、布鲁日2.6球'),
    ('周三008', '多特蒙德', '皇家贝蒂斯', '欧冠', 1.85, 1.05, 0.42, '多特主场强、贝蒂斯客场平多'),
    ('周三009', '维京', '萨巴赫', '欧冠', 2.10, 0.95, 0.44, '维京5人伤停但主场强；萨巴赫身价19M'),
    ('周三010', '朗斯', '科莫', '欧冠', 1.20, 1.60, 0.42, '朗斯5人伤停、科莫身价568M'),
    ('周三011', '布拉格斯拉维亚', '阿森纳', '欧冠', 0.90, 1.75, 0.42, '斯拉维亚门将+前锋伤缺；阿森纳萨卡缺阵'),
    ('周三012', '布里斯托尔城', '伍尔弗汉普顿', '英冠', 1.05, 1.45, 0.40, '布里斯托场均1.15球；狼队4人伤停'),
]

out = {}
for c in cfg:
    r = analyze(*c)
    out[c[0]] = r
    mk = r['market']
    print(c[0], c[1], 'vs', c[2], 'λ', c[4], c[5],
          '| HAD', {k: round(v * 100, 1) for k, v in r['probs_final'].items()},
          '| 市场', {k: round(v * 100, 1) for k, v in mk.items()},
          '| 让', {k: round(v * 100, 1) for k, v in r['handicap'].items()},
          '| TTG', [(k, round(v * 100, 1)) for k, v in r['ttg'].items()][:5],
          '| HTFT', [(k, round(v * 100, 1)) for k, v in list(r['htft'].items())[:3]])

json.dump(out, open('reports/data/20261104_model_output.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved reports/data/20261104_model_output.json')
