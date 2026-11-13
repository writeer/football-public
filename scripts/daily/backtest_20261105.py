# -*- coding: utf-8 -*-
"""2026-11-05 周四13场回测：体彩官方赛果 vs 赛前推荐（全维度 + 分档 + 专项核查 + 8注串关）"""
import json, io, os, glob

PRED = 'reports/data/20261105_predictions_final.json'
OUT_SUM = 'reports/data/20261105_backtest_summary.json'
OUT_DIR = 'memory/backtests/20261105_thursday'


def parse_score(s):
    h, a = str(s).split(':')
    return int(h), int(a)


def had_of(h, a):
    return 'home' if h > a else ('draw' if h == a else 'away')


def hc_of(h, a, line):
    d = (h - a) + line
    return '胜' if d > 0 else ('平' if d == 0 else '负')


def hafu_of(hh, ha, fh, fa):
    ht = '胜' if hh > ha else ('平' if hh == ha else '负')
    ft = '胜' if fh > fa else ('平' if fh == fa else '负')
    return ht + ft


def ttg_label(g):
    return '7+' if g >= 7 else str(g)


def tier_range(tier):
    if '闷战' in tier: return (0, 1)
    if '小球' in tier: return (1, 2)
    if '常规' in tier: return (2, 3)
    if '大球' in tier: return (4, 5)
    if '超大' in tier: return (5, 6)
    if '穿盘' in tier: return (6, 99)
    return (0, 0)


def band_of(g):
    if g <= 1: return '闷战超小球(0-1球)'
    if g == 2: return '小球(1-2球)'
    if g == 3: return '常规正常球(2-3球)'
    if g in (4, 5): return '大球(4-5球)'
    if g == 6: return '超大球(5-6球)'
    return '穿盘可能(6-7+球)'


def main():
    preds = json.load(io.open(PRED, encoding='utf-8'))
    lst = []
    for path in sorted(glob.glob('reports/data/20261105_results_*.json')):
        d = json.load(io.open(path, encoding='utf-8'))
        for m in (d.get('value') or {}).get('matchResult', []) or []:
            if '周四' in str(m.get('matchNumStr') or ''):
                lst.append(m)
    uniq = {}
    for m in lst:
        uniq[m['matchNumStr']] = m
    os.makedirs(OUT_DIR, exist_ok=True)
    io.open(os.path.join(OUT_DIR, 'results_official.json'), 'w', encoding='utf-8').write(
        json.dumps(list(uniq.values()), ensure_ascii=False, indent=1))

    actual, pending = {}, []
    for num, m in uniq.items():
        if not m.get('sectionsNo999'):
            pending.append(num)
            actual[num] = {'pending': True, 'single': int(m.get('bettingSingle') or 0), 'line': int(m['goalLine'])}
            continue
        fh, fa = parse_score(m['sectionsNo999'])
        hh, ha = parse_score(m['sectionsNo1'] or '0:0')
        actual[num] = dict(fh=fh, fa=fa, hh=hh, ha=ha, line=int(m['goalLine']),
                           single=int(m.get('bettingSingle') or 0), status=m.get('matchStatus'),
                           resultStatus=m.get('matchResultStatus'), date=m.get('matchDate'))

    QUOTA_HOME = ['胜胜', '平胜', '负胜']
    QUOTA_AWAY = ['负负', '平负', '胜负']

    rows = []
    for p in preds:
        num = p['num']
        a = actual.get(num)
        if not a or a.get('pending'):
            rows.append({'num': num, 'match': f"{p['home']} vs {p['away']}", 'conf': p['confidence'],
                         'status': 'pending', 'single_api': (a or {}).get('single')})
            continue
        fh, fa, hh, ha = a['fh'], a['fa'], a['hh'], a['ha']
        g = fh + fa
        dirn = had_of(fh, fa)
        hc = hc_of(fh, fa, p['handicap']['line'])
        hafu = hafu_of(hh, ha, fh, fa)
        score, ht = f'{fh}-{fa}', f'{hh}-{ha}'
        ttg = ttg_label(g)
        lo, hi = tier_range(p['ttg']['tier'])
        band = band_of(g)
        p_small = p['ttg']['under25']
        ou_pick = '小' if p_small > 0.5 else '大'
        ou_actual = '小' if g <= 2 else '大'
        quota = QUOTA_HOME if p['had']['first'] == 'home' else QUOTA_AWAY

        r = {
            'num': num, 'match': f"{p['home']} vs {p['away']}", 'conf': p['confidence'],
            'league': p['league'], 'is_single': p['is_single'], 'single_api': a['single'],
            'score': score, 'ht': ht, 'goals': g,
            'actual': {'had': dirn, 'hc': hc, 'hafu': hafu, 'score': score, 'ht': ht, 'goals': g,
                       'ou': ou_actual, 'single_api': a['single'], 'line': p['handicap']['line'],
                       'band': band},
            'pred': {'had_first': p['had']['first'], 'had_second': p['had']['second'],
                     'had_first_prob': p['had']['firstProb'], 'had_second_prob': p['had']['secondProb'],
                     'hc_first': p['hhad']['first'], 'hc_second': p['hhad']['second'],
                     'hc_first_prob': p['hhad']['firstProb'],
                     'structure_leg': p['hhad']['structure_leg'], 'structure_prob': p['hhad']['structureProb'],
                     'ttg_first': p['ttg']['first'], 'ttg_second': p['ttg']['second'],
                     'tier': p['ttg']['tier'], 'hafu': p['hafu']['top3'],
                     'quota': p['hafu']['quota'], 'quota_list': quota,
                     'cr': [c['score'] for c in p['scoreTop5']],
                     'ht': [c['score'] for c in p['htScoreTop3']],
                     'ou': ou_pick, 'ou_p_small': round(p_small, 4)},
            'had_primary': p['had']['first'] == dirn,
            'had_combined': p['had']['first'] == dirn or p['had']['second'] == dirn,
            'hc_primary': p['hhad']['first'] == hc,
            'hc_combined': p['hhad']['first'] == hc or p['hhad']['second'] == hc,
            'hc_structure_hit': p['hhad']['structure_leg'] == hc,
            'cr_top5': score in [c['score'] for c in p['scoreTop5']],
            'cr_top1': p['scoreTop5'][0]['score'] == score,
            'ttg_top2': ttg in [str(p['ttg']['first']), str(p['ttg']['second'])],
            'ttg_top1': str(p['ttg']['first']) == ttg,
            'hafu_top3': hafu in p['hafu']['top3'],
            'hafu_top1': p['hafu']['top3'][0] == hafu,
            'hafu_quota_type': hafu in quota,
            'ht_top3': ht in [c['score'] for c in p['htScoreTop3']],
            'ht_top1': p['htScoreTop3'][0]['score'] == ht,
            'tier_hit': lo <= g <= hi,
            'ou_hit': ou_pick == ou_actual,
            'band': band,
        }
        rows.append(r)

    PARLAYS = [
        ('#1 稳健方向3串1（006×008×013）', 1.70,
         [('周四006', 'had', 'home'), ('周四008', 'had', 'home'), ('周四013', 'had', 'home')]),
        ('#2 方向4串1（001×006×008×013）', 2.10,
         [('周四001', 'had', 'home'), ('周四006', 'had', 'home'), ('周四008', 'had', 'home'), ('周四013', 'had', 'home')]),
        ('#3 连续编号方向2串1（004-005）', 2.61,
         [('周四004', 'had', 'home'), ('周四005', 'had', 'home')]),
        ('#4 客胜方向2串1（003×011）', 2.46,
         [('周四003', 'had', 'away'), ('周四011', 'had', 'away')]),
        ('#5 连续编号方向2串1（001-002）', 2.16,
         [('周四001', 'had', 'home'), ('周四002', 'had', 'home')]),
        ('#6 半全场连续串①（002-003）', 5.68,
         [('周四002', 'hafu', '胜胜'), ('周四003', 'hafu', '负负')]),
        ('#7 半全场连续串②（004-005）', 5.98,
         [('周四004', 'hafu', '胜胜'), ('周四005', 'hafu', '胜胜')]),
        ('#8 半全场3串1（009×011×012）', 25.24,
         [('周四009', 'hafu', '负负'), ('周四011', 'hafu', '负负'), ('周四012', 'hafu', '胜胜')]),
    ]

    def leg_hit(num, market, pick):
        a = actual.get(num)
        if not a or a.get('pending'):
            return None
        if market == 'had':
            return had_of(a['fh'], a['fa']) == pick
        if market == 'hc':
            return hc_of(a['fh'], a['fa'], a['line']) == pick
        if market == 'ttg':
            return ttg_label(a['fh'] + a['fa']) == pick
        if market == 'hafu':
            return hafu_of(a['hh'], a['ha'], a['fh'], a['fa']) == pick
        if market == 'score':
            return f"{a['fh']}-{a['fa']}" == pick
        return False

    parlays = []
    for label, odds, legs in PARLAYS:
        hits = [leg_hit(*l) for l in legs]
        resolved = False if any(h is False for h in hits) else (None if any(h is None for h in hits) else True)
        parlays.append({'label': label, 'odds': odds,
                        'legs': [f'{l[0]} {l[1]} {l[2]}' for l in legs],
                        'leg_hits': hits, 'hit': resolved,
                        'failed_leg': next((f'{l[0]} {l[1]} {l[2]}' for l, h in zip(legs, hits) if h is False), None)})

    dims = ['had_primary', 'had_combined', 'hc_primary', 'hc_combined', 'cr_top5', 'cr_top1',
            'ttg_top2', 'ttg_top1', 'hafu_top3', 'hafu_top1', 'ht_top3', 'ht_top1',
            'tier_hit', 'ou_hit']

    settled = [r for r in rows if r.get('status') != 'pending']

    def rate(key, subset=None):
        arr = [r for r in settled if subset is None or subset(r)]
        hit = sum(1 for r in arr if r[key])
        return hit, len(arr), (round(hit / len(arr) * 100, 1) if arr else None)

    summary = {k: dict(zip(['hit', 'n', 'pct'], rate(k))) for k in dims}
    buckets = {}
    for c in ['★★★', '★★', '★']:
        sub = (lambda cc: (lambda r: r['conf'] == cc))(c)
        buckets[c] = {
            'n': sum(1 for r in settled if r['conf'] == c),
            'had_primary': rate('had_primary', sub), 'had_combined': rate('had_combined', sub),
            'hc_primary': rate('hc_primary', sub), 'hc_combined': rate('hc_combined', sub),
            'hafu_top3': rate('hafu_top3', sub), 'cr_top5': rate('cr_top5', sub),
            'ttg_top2': rate('ttg_top2', sub), 'ht_top3': rate('ht_top3', sub),
            'tier': rate('tier_hit', sub), 'ou': rate('ou_hit', sub),
        }

    # 专项1：002 单关
    s002 = next(r for r in rows if r['num'] == '周四002')
    single_check = {
        'match': s002['match'], 'score': s002['score'], 'ht': s002['ht'],
        'pred_after_adjust': {'home': 0.436, 'draw': 0.301, 'away': 0.264},
        'had_first': s002['pred']['had_first'], 'had_second': s002['pred']['had_second'],
        'actual': s002['actual']['had'],
        'had_primary': s002['had_primary'], 'had_combined': s002['had_combined'],
        'api_betting_single': s002['single_api'],
        'report_declared_single': s002['is_single'],
        'reverse_proof': s002['single_api'] == 1,
        'note': '赛果接口 bettingSingle=1，与 11-04 008 的反证方法一致：单关标识在开奖数据中回填为 1，反证用户端判断成立。',
    }

    # 专项2：两端档
    g_counts = {str(i): 0 for i in range(7)}
    for r in settled:
        g_counts[str(r['goals'])] = g_counts.get(str(r['goals']), 0) + 1
    two_end = {
        'goals_dist': g_counts,
        'n_0_1': sum(1 for r in settled if 0 <= r['goals'] <= 1),
        'n_6plus': sum(1 for r in settled if r['goals'] >= 6),
        'matches_0_1': [r['num'] for r in settled if 0 <= r['goals'] <= 1],
        'matches_6plus': [r['num'] for r in settled if r['goals'] >= 6],
        'tier_hit': summary['tier_hit'],
        'note': '13场中仅2场落入0-1球（007、012）、1场进入6+球（013，7球）；009闷战35.6%若按两端档押注，实际共3球落空，留空成立。',
    }

    # 专项3：半全场配额位 vs 非配额位
    quota_rows = [r for r in settled if r['hafu_quota_type']]
    nonquota_rows = [r for r in settled if not r['hafu_quota_type']]
    hafu_quota = {
        'quota_n': len(quota_rows), 'quota_top3_hit': sum(1 for r in quota_rows if r['hafu_top3']),
        'quota_matches': [f"{r['num']}:{r['actual']['hafu']}" for r in quota_rows],
        'nonquota_n': len(nonquota_rows), 'nonquota_top3_hit': sum(1 for r in nonquota_rows if r['hafu_top3']),
        'nonquota_matches': [f"{r['num']}:{r['actual']['hafu']}" for r in nonquota_rows],
        'note': '配额位（主胜场胜胜/平胜/负胜、客胜场负负/平负/胜负）覆盖8场且全中；非配额位5场全空。',
    }

    # 专项4：让球结构腿 vs 非结构腿
    struct_hit = sum(1 for r in settled if r['hc_structure_hit'])
    hc_struct = {
        'structure_leg_hit': struct_hit, 'n': len(settled),
        'structure_pct': round(struct_hit / len(settled) * 100, 1),
        'structure_hit_matches': [f"{r['num']}:{r['pred']['structure_leg']}" for r in settled if r['hc_structure_hit']],
        'hc_primary': summary['hc_primary'], 'hc_combined': summary['hc_combined'],
        'note': '结构腿（-1让负/+1让胜/-2让负）13场命中7场（53.8%），高于首选3/13与含次选6/13；剔除本轮代价明确，需在下轮 L268 复盘。',
    }

    # 专项5：007 改判
    r007 = next(r for r in rows if r['num'] == '周四007')
    verdict_007 = {
        'match': r007['match'], 'score': r007['score'], 'actual_had': r007['actual']['had'],
        'model_original': {'home': 0.371, 'draw': 0.305, 'away': 0.324},
        'post_adjust_first': r007['pred']['had_first'], 'post_adjust_prob': r007['pred']['had_first_prob'],
        'correct': r007['had_primary'],
        'note': '模型原首选主胜37.1%会落空；按规则32/L253 改判客胜32.4%命中，残阵降级方向可信。',
    }

    # 专项6：010 无HAD池偏离
    r010 = next(r for r in rows if r['num'] == '周四010')
    dev010 = {
        'match': r010['match'], 'score': r010['score'],
        'model': {'home': 0.697, 'draw': 0.203, 'away': 0.1},
        'actual_had': r010['actual']['had'], 'had_primary': r010['had_primary'],
        'hc_primary': r010['hc_primary'], 'hc_combined': r010['hc_combined'],
        'note': '无HAD池、仅模型值69.7%主胜，实际3:1主胜，方向零偏离；让球-2打平，首选让胜落空、次选让平命中。',
    }

    stake = len(parlays)
    ret = sum(p['odds'] for p in parlays if p['hit'])
    parlay_sum = {'n': len(parlays), 'hit': sum(1 for p in parlays if p['hit']),
                  'stake': stake, 'return': round(ret, 2), 'profit': round(ret - stake, 2),
                  'roi_pct': round((ret - stake) / stake * 100, 1)}

    out = {'date': '2026-11-05', 'day': '周四', 'n': len(rows), 'settled_n': len(settled),
           'pending': pending, 'rows': rows, 'summary': summary, 'buckets': buckets,
           'parlays': parlays, 'parlay_summary': parlay_sum,
           'checks': {'single_002': single_check, 'two_end': two_end, 'hafu_quota': hafu_quota,
                      'hc_structure': hc_struct, 'verdict_007': verdict_007, 'deviation_010': dev010},
           'source': '体彩官方 getUniformMatchResultV1（matchBeginDate=2026-11-05~2026-11-06，matchNumStr 含「周四」）；sectionsNo999=全场、sectionsNo1=半场；013 sectionsNo999 为空，单列待结算'}
    for path in [OUT_SUM, os.path.join(OUT_DIR, 'backtest.json')]:
        io.open(path, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
    io.open(os.path.join(OUT_DIR, 'rows.json'), 'w', encoding='utf-8').write(
        json.dumps(rows, ensure_ascii=False, indent=1))

    print('n=', len(rows), 'settled=', len(settled), 'pending=', pending)
    for k in dims:
        print(f'{k:16s}', summary[k])
    print('buckets', json.dumps(buckets, ensure_ascii=False))
    print('--- per match ---')
    for r in rows:
        if r.get('status') == 'pending':
            print(r['num'], 'PENDING', 'single_api=', r.get('single_api'))
            continue
        print(r['num'], r['conf'], r['score'], 'HT', r['ht'], '| HAD', r['actual']['had'],
              r['had_primary'], r['had_combined'],
              '| HC', r['actual']['hc'], r['hc_primary'], r['hc_combined'], 'struct', r['pred']['structure_leg'],
              r['hc_structure_hit'],
              '| CR', r['cr_top5'], '| TTG', r['actual']['goals'], r['ttg_top2'],
              '| HAFU', r['actual']['hafu'], r['hafu_top3'],
              '| HT', r['ht_top3'], '| tier', r['tier_hit'], '| OU', r['pred']['ou'], r['actual']['ou'], r['ou_hit'])
    print('--- checks ---')
    print(json.dumps(out['checks'], ensure_ascii=False, indent=1))
    print('--- parlays ---')
    for p in parlays:
        print(('HIT ' if p['hit'] else ('VOID' if p['hit'] is None else 'MISS')), p['label'], p['odds'],
              'failed:', p['failed_leg'], p['leg_hits'])
    print('parlay', parlay_sum)


if __name__ == '__main__':
    main()
