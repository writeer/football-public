# -*- coding: utf-8 -*-
"""2026-11-03 周二11场回测：官方赛果 vs 赛前推荐，六维命中率+串关方案核对"""
import json, io, os

# 官方赛果（getUniformMatchResultV1，sectionsNo999 全场 / sectionsNo1 半场）
RESULTS = {
 '周二001': (2, 4, 0, 2),
 '周二002': (2, 0, 0, 0),
 '周二003': (7, 4, 3, 4),
 '周二004': (2, 0, 2, 0),
 '周二005': (0, 2, 0, 0),
 '周二006': (4, 0, 3, 0),
 '周二007': (0, 3, 0, 2),
 '周二008': (3, 2, 0, 2),
 '周二009': (3, 0, 1, 0),
 '周二010': (0, 6, 0, 4),
 '周二011': (0, 0, 0, 0),
}

def had_of(h, a):
    return 'home' if h > a else ('draw' if h == a else 'away')

def hc_of(h, a, line):
    d = (h - a) + line
    return 'win' if d > 0 else ('push' if d == 0 else 'lose')

def hafu_of(hh, ha, fh, fa):
    ht = 'H' if hh > ha else ('D' if hh == ha else 'A')
    ft = 'H' if fh > fa else ('D' if fh == fa else 'A')
    return ht + ft  # 体彩顺序：半场+全场（如 DH=平胜）

def ttg_label(g):
    return f'{g}球' if g <= 6 else '7+球'

def tier_hit(tier, g):
    if '常规' in tier: return 2 <= g <= 3
    if '大球' in tier: return 4 <= g <= 5
    if '超大' in tier: return 5 <= g <= 6
    if '小球' in tier: return 1 <= g <= 2
    if '闷战' in tier: return 0 <= g <= 1
    if '穿盘' in tier: return g >= 6
    return False

preds = json.load(io.open('reports/data/20261103_predictions.json', encoding='utf-8'))
rows = []
for x in preds:
    num = x['num']
    fh, fa, hh, ha = RESULTS[num]
    rc = x['recommendation']
    g = fh + fa
    r = {
      'num': num, 'match': f"{x['home']} vs {x['away']}", 'conf': x['confidence'],
      'score': f'{fh}-{fa}', 'ht': f'{hh}-{ha}', 'goals': g,
      'had_actual': had_of(fh, fa),
      'had_primary_hit': rc['had_primary'] == had_of(fh, fa),
      'had_combined_hit': rc['had_primary'] == had_of(fh, fa) or rc['had_secondary'] == had_of(fh, fa),
      'hc_actual': hc_of(fh, fa, rc['hc_line']),
      'hc_primary_hit': rc['hc_primary'] == hc_of(fh, fa, rc['hc_line']),
      'hc_combined_hit': rc['hc_primary'] == hc_of(fh, fa, rc['hc_line']) or rc['hc_secondary'] == hc_of(fh, fa, rc['hc_line']),
      'cr_top5_hit': f'{fh}-{fa}' in [c['score'] for c in rc['cr_top5']],
      'cr_top1_hit': rc['cr_top5'][0]['score'] == f'{fh}-{fa}',
      'ttg_top2_hit': ttg_label(g) in rc['ttg_top2'],
      'ttg_top1_hit': rc['ttg_top2'][0] == ttg_label(g),
      'hafu_top3_hit': hafu_of(hh, ha, fh, fa) in [h['pick'] for h in rc['hafu_top3']],
      'hafu_top1_hit': rc['hafu_top3'][0]['pick'] == hafu_of(hh, ha, fh, fa),
      'ht_top3_hit': f'{hh}-{ha}' in [s['score'] for s in rc['ht_scores_top3']],
      'ht_top1_hit': rc['ht_scores_top3'][0]['score'] == f'{hh}-{ha}',
      'tier': rc['six_tier'],
      'tier_hit': tier_hit(rc['six_tier'], g),
      'hafu_actual': hafu_of(hh, ha, fh, fa),
      'ttg_actual': ttg_label(g),
    }
    rows.append(r)

def rate(key, subset=None):
    arr = [r for r in rows if (subset is None or subset(r))]
    hit = sum(1 for r in arr if r[key])
    return hit, len(arr), (round(hit / len(arr) * 100, 1) if arr else None)

dims = ['had_primary_hit', 'had_combined_hit', 'hc_primary_hit', 'hc_combined_hit',
        'cr_top5_hit', 'cr_top1_hit', 'ttg_top2_hit', 'ttg_top1_hit',
        'hafu_top3_hit', 'hafu_top1_hit', 'ht_top3_hit', 'ht_top1_hit', 'tier_hit']
summary = {k: dict(zip(['hit', 'n', 'pct'], rate(k))) for k in dims}

buckets = {}
for c in ['★★★', '★★', '★']:
    sub = (lambda cc: (lambda r: r['conf'] == cc))(c)
    buckets[c] = {
      'n': sum(1 for r in rows if r['conf'] == c),
      'had_primary': rate('had_primary_hit', sub)[:2],
      'had_combined': rate('had_combined_hit', sub)[:2],
      'hc_primary': rate('hc_primary_hit', sub)[:2],
      'hc_combined': rate('hc_combined_hit', sub)[:2],
      'hafu_top3': rate('hafu_top3_hit', sub)[:2],
    }

# 串关方案（与 20261103 报告逐条对应）
P = [
 ('方向串A（稳健）', 2.03, [('周二009','had','home'),('周二006','had','home'),('周二010','had','away')]),
 ('方向串B（稳健）', 2.31, [('周二002','had','home'),('周二011','had','home')]),
 ('让球串A（稳健）', 3.44, [('周二008','hc','lose'),('周二004','hc','lose'),('周二005','hc','win')]),
 ('让球串B（价值）', 11.28, [('周二007','hc','win'),('周二010','hc','lose'),('周二011','hc','win')]),
 ('混合串A', 3.50, [('周二009','had','home'),('周二002','hc','win'),('周二006','had','home')]),
 ('连续混合①(004+005)', 2.31, [('周二004','hc','lose'),('周二005','hc','win')]),
 ('连续混合②(010+011)', 2.20, [('周二010','had','away'),('周二011','had','home')]),
 ('总进球串A', 44.74, [('周二001','ttg','3球'),('周二005','ttg','3球'),('周二011','ttg','3球')]),
 ('总进球串B', 103.74, [('周二002','ttg','4球'),('周二007','ttg','2球'),('周二009','ttg','5球')]),
 ('连续总进球①(004+005)', 15.27, [('周二004','ttg','4球'),('周二005','ttg','3球')]),
 ('连续总进球②(006+007)', 16.38, [('周二006','ttg','3球'),('周二007','ttg','2球')]),
 ('半全场串A', 13.31, [('周二001','hafu','AA'),('周二003','hafu','AA'),('周二010','hafu','AA')]),
 ('半全场串B', 10.65, [('周二004','hafu','HH'),('周二002','hafu','HH'),('周二009','hafu','HH')]),
 ('连续半全场①(002+003)', 19.68, [('周二002','hafu','DH'),('周二003','hafu','DA')]),
 ('连续半全场②(008+009)', 18.90, [('周二008','hafu','AA'),('周二009','hafu','DH')]),
 ('混合总进球A(005+006)', 12.60, [('周二005','hafu','AA'),('周二006','ttg','3球')]),
 ('混合总进球B(007+011)', 16.69, [('周二007','hafu','DA'),('周二011','ttg','3球')]),
 ('连续混合总进球①(009+010)', 6.17, [('周二009','hafu','HH'),('周二010','ttg','4球')]),
 ('连续混合总进球②(004+005)', 22.75, [('周二004','hafu','DA'),('周二005','hafu','AA')]),
 ('比分串A', 603.75, [('周二002','score','2-1'),('周二003','score','1-2'),('周二007','score','0-1')]),
 ('连续比分①(003+004)', 60.00, [('周二003','score','1-2'),('周二004','score','2-1')]),
 ('单挑比分①(006)', 9.00, [('周二006','score','2-0')]),
 ('单挑比分②(003)', 7.50, [('周二003','score','1-2')]),
]

def leg_hit(num, market, pick):
    fh, fa, hh, ha = RESULTS[num]
    if market == 'had':
        return had_of(fh, fa) == pick
    if market == 'hc':
        x = next(p for p in preds if p['num'] == num)
        return hc_of(fh, fa, x['recommendation']['hc_line']) == pick
    if market == 'ttg':
        return ttg_label(fh + fa) == pick
    if market == 'hafu':
        return hafu_of(hh, ha, fh, fa) == pick
    if market == 'score':
        return f'{fh}-{fa}' == pick
    return False

parlays = []
for label, odds, legs in P:
    hits = [leg_hit(*l) for l in legs]
    parlays.append({'label': label, 'odds': odds, 'legs': [f'{l[0]} {l[1]} {l[2]}' for l in legs],
                    'leg_hits': hits, 'hit': all(hits),
                    'failed_leg': next((f'{l[0]} {l[1]} {l[2]}' for l, h in zip(legs, hits) if not h), None)})

out = {'date': '2026-11-03', 'n': len(rows), 'rows': rows, 'summary': summary,
       'buckets': buckets, 'parlays': parlays}
os.makedirs('memory/backtests/20261103_tuesday', exist_ok=True)
for p in ['reports/data/20261103_backtest_summary.json', 'memory/backtests/20261103_tuesday/backtest.json']:
    io.open(p, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))

print('n=', len(rows))
for k in dims:
    print(k, summary[k])
print('buckets', json.dumps(buckets, ensure_ascii=False))
print('--- per match ---')
for r in rows:
    print(r['num'], r['score'], 'HT', r['ht'], '| HAD', r['had_actual'], 'P', r['had_primary_hit'], 'C', r['had_combined_hit'],
          '| HC', r['hc_actual'], 'P', r['hc_primary_hit'], 'C', r['hc_combined_hit'],
          '| CR5', r['cr_top5_hit'], '| TTG', r['ttg_actual'], r['ttg_top2_hit'],
          '| HAFU', r['hafu_actual'], r['hafu_top3_hit'], '| HT', r['ht_top3_hit'], '| tier', r['tier'], r['tier_hit'])
print('--- parlays ---')
for p in parlays:
    print(('HIT ' if p['hit'] else 'MISS'), p['label'], p['odds'], 'failed:', p['failed_leg'])
print('parlay hit', sum(1 for p in parlays if p['hit']), '/', len(parlays))
