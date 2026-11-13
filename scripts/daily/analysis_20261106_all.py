# -*- coding: utf-8 -*-
"""2026-11-06 周五竞彩14场模型计算（DC + NB + Skellam + MC；规则79：λ 仅由基本面推导）"""
import json, math
import numpy as np

MAXG = 11
RHO = -0.08
DRAW_INFL = 1.05
rng = np.random.default_rng(20261106)

raw = json.load(open('reports/data/20261106_raw.json', encoding='utf-8'))
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


# λ 口径：联赛场均进失球/联赛等级/排名/伤停（规则32、76），未使用赔率反解（规则79）
cfg = [
    ('周五001', '悉尼FC', '中央海岸水手', '澳超', 1.85, 0.80, 0.44, '悉尼澳超5、主场；水手澳超10且赛季未胜，队长塞恩斯伯里伤缺，悉尼瓦拉蒂/霍尔曼伤'),
    ('周五002', '不伦瑞克', '科特布斯', '德乙', 1.60, 1.05, 0.43, '德乙14vs15保级六分战；主队5人伤，客队3人伤，双方近5轮均低迷'),
    ('周五003', '哈马比', '埃夫斯堡', '瑞超', 2.20, 0.85, 0.43, '哈马比瑞超2、剩3轮争冠、4胜1负；埃夫斯堡第5但客场一般，维克斯特伦赛季报销'),
    ('周五004', '蒙彼利埃', '梅斯', '法乙', 1.45, 0.85, 0.43, '蒙彼利埃法乙2、4胜1平11:2；梅斯第10、客场未胜，N门迪等伤缺'),
    ('周五005', '威廉二世', '兹沃勒', '荷甲', 1.15, 1.50, 0.43, '威廉二世18、5连败4:20且中卫/中场/前锋停伤；兹沃勒14、近5场2胜1平2负'),
    ('周五006', '奥斯', '瓦尔韦克', '荷乙', 1.15, 1.85, 0.43, '奥斯15、近5场2胜1平2负；瓦尔韦克12、5轮不胜但客场被让，双方无确认伤停'),
    ('周五007', '汉堡', '门兴格拉德巴赫', '德甲', 1.50, 1.10, 0.43, '汉堡15、4人伤+Vušković停赛；门兴18、门将Nicolas与Diks伤缺，客队垫底'),
    ('周五008', '威尼斯', '乌迪内斯', '意甲', 1.20, 1.05, 0.43, '威尼斯20、1胜4负2:7；乌迪内斯19、1平4负3:12，双方保级直接对话且多人伤缺'),
    ('周五009', '图卢兹', '斯特拉斯堡', '法甲', 1.50, 1.10, 0.43, '图卢兹12、Dønnum停赛+2伤；斯特拉斯堡13、1胜4负但Godo/Doukouré复出'),
    ('周五010', '埃弗顿', '考文垂', '英超', 1.90, 0.90, 0.43, '埃弗顿7、主场、近5场2胜1平2负；考文垂16、5人伤缺，客战乏力'),
    ('周五011', '德比郡', '博尔顿', '英冠', 1.35, 1.25, 0.43, '德比郡23、0胜1平4负3:12且6人伤、帅位承压；博尔顿17、刚1-0胜查尔顿'),
    ('周五012', '塞维利亚', '阿拉维斯', '西甲', 1.60, 1.00, 0.43, '塞维利亚6、争欧战、Isaac Romero复出但Manu Bueno停赛；阿拉维斯11、0胜2平3负4:11'),
    ('周五013', '法马利康', '阿罗卡', '葡超', 1.40, 1.15, 0.43, '法马利康11、主场4场不胜且临时主帅、2伤1停；阿罗卡5、四连胜冲欧战'),
    ('周五014', '维多利亚', '弗鲁米嫩塞', '巴甲', 1.20, 1.40, 0.45, '维多利亚15、保级、4轮不胜且换帅、7人伤2停；弗鲁米嫩塞4、争解放者杯但4人伤1停'),
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

json.dump(out, open('reports/data/20261106_model_output.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved reports/data/20261106_model_output.json')
