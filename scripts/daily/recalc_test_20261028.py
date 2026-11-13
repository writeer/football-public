# -*- coding: utf-8 -*-
"""2026-10-28 重算测试（仅 001/002/003 + 意甲5场）

测试两项改动：
  A. λ_total 校准：λ_new = λ_old × CAL（CAL 由 10-19/10-27 两期 18 场的 实际进球/λ 中位比值 1.41 收缩 60% 得到）
  B. 比分候选池 P90 覆盖：池内最大总进球必须 ≥ 总进球分布 P90，否则用最低概率位替换

输出：reports/data/20261028_recalc_test.json + reports/analysis/20261028_recalc_test.md
"""
import sys, json, io, os
sys.path.insert(0, r'e:\VibeCoding\football')
from scipy import stats as sp_stats
from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, HTFTModel)

D = r'e:\VibeCoding\football'
ADD = 0.30                      # λ 加法校准（测试值，见报告"校准口径"）
Q_CAP = 0.75                    # 比分池上限保障分位（P75）
TARGETS = ['周三001', '周三002', '周三003', '周三005', '周三006', '周三007', '周三013', '周三014']

HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}
ORDER = ['home', 'draw', 'away']
CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
W = {'dc': 0.34, 'nb': 0.22, 'zip': 0.13, 'sk': 0.14, 'mc': 0.17}


def tier_of(top1, p01, p6):
    """档位 = 众数总进球所在档（与总进球TOP2同源，不做 p6/p01 越级覆盖）"""
    if top1 <= 1:
        return '闷战超小球(0-1球)' if top1 == 0 else '小球(1-2球)'
    if top1 in (2, 3):
        return '常规正常球(2-3球)'
    if top1 == 4:
        return '大球(4-5球)'
    if top1 == 5:
        return '超大球(5-6球)'
    return '穿盘可能(6-7+球)'


def quantile(tg, q):
    cum = 0.0
    for t in sorted(tg):
        cum += tg[t]
        if cum >= q:
            return t
    return max(tg)


def pool_with_coverage(raw, tg, dir_allowed, n=5, q=Q_CAP):
    """概率取前5，并保证池内最大总进球 ≥ 总进球分布 P75（避免池子上限压住大球）"""
    pool = list(raw[:n])
    tq = quantile(tg, q)
    cap = max(a + b for a, b, _ in pool)
    replaced = None
    if cap < tq:
        cand = [x for x in raw if x[0] + x[1] >= tq and x not in pool]
        if cand:
            replaced = pool[-1]
            pool = pool[:n - 1] + [cand[0]]
    return pool, tq, cap, replaced


def recompute(m, lam_old_total, dirs):
    base_h, base_a = m['lambda_home'], m['lambda_away']
    tot = base_h + base_a
    lh = base_h + ADD * base_h / tot
    la = base_a + ADD * base_a / tot

    dc = DixonColesModel(); nb = NegativeBinomialModel(); zp = ZIPModel()
    sk = SkellamModel(); mc = MonteCarloSimulator(n_sim=20000)
    p = {
        'dc': dc.outcome_probs(lh, la), 'nb': nb.outcome_probs(lh, la),
        'zip': zp.outcome_probs(lh, la), 'sk': sk.outcome_probs(lh, la),
    }
    r = mc.simulate(lh, la)
    p['mc'] = {'home': r['home_win'], 'draw': r['draw'], 'away': r['away_win']}
    fused = {k: sum(W[x] * p[x][k] for x in W) for k in ORDER}
    s = sum(fused.values())
    fused = {k: v / s for k, v in fused.items()}

    n = 17 if (lh + la) > 3.4 else 14
    dc.max_goals = n
    mat = dc.compute_matrix(lh, la)
    tg, gd = {}, {}
    for i in range(n):
        for j in range(n):
            tg[i + j] = tg.get(i + j, 0.0) + mat[i, j]
            gd[i - j] = gd.get(i - j, 0.0) + mat[i, j]
    tg = {k: v for k, v in tg.items() if v > 1e-6}
    p01 = sum(v for k, v in tg.items() if k <= 1)
    p23 = sum(v for k, v in tg.items() if k in (2, 3))
    p45 = sum(v for k, v in tg.items() if k in (4, 5))
    p6 = sum(v for k, v in tg.items() if k >= 6)
    ttg = sorted(tg.items(), key=lambda x: -x[1])[:6]
    top2 = [ttg[0][0], ttg[1][0]]
    raw = sorted([(i, j, mat[i, j]) for i in range(n) for j in range(n)], key=lambda x: -x[2])
    pool, tq, cap_old, rep = pool_with_coverage(raw, tg, fused, 5, Q_CAP)

    prim = max(fused.items(), key=lambda x: x[1])[0]
    k_dist = max(gd.items(), key=lambda x: x[1])
    if prim == 'home':
        cand = {k: v for k, v in gd.items() if k >= 1}
    elif prim == 'away':
        cand = {k: v for k, v in gd.items() if k <= -1}
    else:
        cand = {k: v for k, v in gd.items() if k == 0}
    k_rec = max(cand.items(), key=lambda x: x[1])

    htft = HTFTModel(dc)
    htft.ht_ratio = 0.38
    ht = [(HAFU_CN.get(str(x['code']).replace('/', ''), x['htft']), x['probability'])
          for x in htft.predict(lh, la)]
    ht = sorted(ht, key=lambda x: -x[1])

    def probs(tp):
        out = []
        for a, b, _ in tp:
            lab = '%d-%d' % (a, b)
            out.append((lab, mat[a, b]))
        return out

    return {
        'lambda_home': lh, 'lambda_away': la, 'lambda_total': lh + la,
        'fused': fused, 'primary': prim, 'rank': sorted(fused.items(), key=lambda x: -x[1]),
        'tier': tier_of(top2[0], p01, p6),
        'ttg_top2': top2, 'ttg_probs': {k: v for k, v in ttg},
        'pool': pool, 'p75': tq, 'cap_before': cap_old, 'replaced': rep,
        'pool_mass': sum(x[2] for x in pool),
        'k_dist': k_dist, 'k_rec': k_rec,
        'htft_top3': ht[:3], 'p01': p01, 'p23': p23, 'p45': p45, 'p6': p6,
        'over25': sum(v for k, v in tg.items() if k >= 3),
    }


def main():
    ms = json.load(io.open(os.path.join(D, 'reports/data/20261028_matches.json'), encoding='utf-8-sig'))
    old = {m['num']: m for m in json.load(io.open(
        os.path.join(D, 'reports/data/20261028_model_output.json'), encoding='utf-8-sig'))}
    info = json.load(io.open(os.path.join(D, 'reports/data/20261028_info.json'), encoding='utf-8-sig'))
    info = info if isinstance(info, dict) else {x['num']: x for x in info}

    out = []
    for m in ms:
        if m['num'] not in TARGETS:
            continue
        o = old[m['num']]
        r = recompute(o, o['lambda_total'], None)
        inf = info.get(m['num']) or {}
        gl = (m.get('hhad') or {}).get('goalLine')
        hh = None
        if gl is not None:
            th = -gl
            lh, la = r['lambda_home'], r['lambda_away']
            hh = {'home': float(sp_stats.skellam.sf(th, lh, la)),
                  'draw': float(sp_stats.skellam.pmf(th, lh, la)),
                  'away': float(sp_stats.skellam.cdf(th - 1, lh, la))}
        out.append({
            'num': m['num'], 'league': m['league'], 'home': m['home'], 'away': m['away'],
            'time': m['time'], 'goalLine': gl,
            'venue': (inf.get('venue') or {}).get('name'),
            'old': {'lam': [o['lambda_home'], o['lambda_away']], 'total': o['lambda_total'],
                    'tier': o['tier'], 'ttg_top2': o['ttg_top2'],
                    'pool': ['%d-%d' % (a, b) for a, b, _ in o['top_scores']],
                    'primary': o['primary'], 'prob': o['primary_prob'],
                    'fused': o['fused'], 'htft': [k for k, _ in o['htft_top3']]},
            'new': {
                'lam': [round(r['lambda_home'], 3), round(r['lambda_away'], 3)],
                'total': round(r['lambda_total'], 3), 'tier': r['tier'],
                'ttg_top2': r['ttg_top2'],
                'ttg_probs': {str(k): round(v, 4) for k, v in r['ttg_probs'].items()},
                'pool': ['%d-%d' % (a, b) for a, b, _ in r['pool']],
                'pool_probs': [round(x[2], 4) for x in r['pool']],
                'pool_mass': round(r['pool_mass'], 4), 'p75': r['p75'],
                'cap_before': r['cap_before'],
                'replaced': ('%d-%d' % (r['replaced'][0], r['replaced'][1])) if r['replaced'] else None,
                'primary': r['primary'], 'prob': round(r['rank'][0][1], 4),
                'second': r['rank'][1][0], 'second_prob': round(r['rank'][1][1], 4),
                'fused': {k: round(v, 4) for k, v in r['fused'].items()},
                'k_dist': r['k_dist'][0], 'k_rec': r['k_rec'][0],
                'htft': [k for k, _ in r['htft_top3']],
                'htft_probs': [round(v, 4) for _, v in r['htft_top3']],
                'hhad': ({k: round(v, 4) for k, v in hh.items()} if hh else None),
                'p01': round(r['p01'], 4), 'p23': round(r['p23'], 4),
                'p45': round(r['p45'], 4), 'p6': round(r['p6'], 4),
                'over25': round(r['over25'], 4),
            },
        })
    json.dump({'add': ADD, 'q': Q_CAP, 'rows': out},
              io.open(os.path.join(D, 'reports/data/20261028_recalc_test.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for x in out:
        print('%s %s vs %s' % (x['num'][2:], x['home'], x['away']))
        print('   λ %.2f→%.2f ｜ 档位 %s → %s' % (x['old']['total'], x['new']['total'], x['old']['tier'], x['new']['tier']))
        print('   池 %s → %s（上限 %d→%d, P75=%d）' % (' '.join(x['old']['pool']), ' '.join(x['new']['pool']),
                                                     max(sum(int(t) for t in s.split('-')) for s in x['old']['pool']),
                                                     max(sum(int(t) for t in s.split('-')) for s in x['new']['pool']), x['new']['p75']))
        print('   总进球TOP2 %s → %s ｜ 首选 %s %.1f%%→%.1f%%' % (
            x['old']['ttg_top2'], x['new']['ttg_top2'], CN[x['new']['primary']],
            x['old']['prob'] * 100, x['new']['prob'] * 100))
    print('saved')


if __name__ == '__main__':
    main()

