# -*- coding: utf-8 -*-
"""回填 2026-11-01 比分串试用台账（7场）并更新累计"""
import json, io

path = 'memory/trials/score_parlay_trial.json'
d = json.load(io.open(path, encoding='utf-8-sig'))

REC = [
    {'match_num': '003', 'match': '町田泽维亚 vs 大阪钢巴', 'league': '日职',
     'k_dist': {'value': 2, 'pct': 0.208}, 'k_rec': {'value': 2, 'pct': 0.208},
     'band_top3': [['2-0', 0.098], ['3-1', 0.080], ['4-2', 0.025]],
     'ttg': '3球/4球', 'k_dist_dir': '主胜', 'had_dir': '主胜', 'divergent': False,
     'used_in': ['比分串B', '连续编号比分A'], 'pred_score': '2-0', 'actual': '0-0',
     'verdict': 'semi（方向中平（次选），净胜0未入带；带内TOP1为2-0）'},
    {'match_num': '004', 'match': '首尔FC vs 仁川联', 'league': '韩职',
     'k_dist': {'value': 1, 'pct': 0.236}, 'k_rec': {'value': 1, 'pct': 0.236},
     'band_top3': [['1-0', 0.109], ['2-1', 0.097], ['3-2', 0.026]],
     'ttg': '2球/3球', 'k_dist_dir': '主胜', 'had_dir': '主胜', 'divergent': False,
     'used_in': ['连续编号比分A', '单挑比分①'], 'pred_score': '1-0', 'actual': '0-1',
     'verdict': 'miss（方向未中，实际客胜；比分未入带）'},
    {'match_num': '007', 'match': '科莫 vs 威尼斯', 'league': '意甲',
     'k_dist': {'value': 2, 'pct': 0.225}, 'k_rec': {'value': 2, 'pct': 0.225},
     'band_top3': [['2-0', 0.138], ['3-1', 0.072], ['4-2', 0.014]],
     'ttg': '3球/2球', 'k_dist_dir': '主胜', 'had_dir': '主胜', 'divergent': False,
     'used_in': ['稳健比分串', '单挑比分①'], 'pred_score': '2-0', 'actual': '1-0',
     'verdict': 'semi（方向中主胜，净胜+1未入带；带内TOP1为2-0）'},
    {'match_num': '008', 'match': '赫塔费 vs 塞维利亚', 'league': '西甲',
     'k_dist': {'value': 0, 'pct': 0.305}, 'k_rec': {'value': 0, 'pct': 0.305},
     'band_top3': [['1-1', 0.145], ['0-0', 0.109], ['2-2', 0.045]],
     'ttg': '2球/3球', 'k_dist_dir': '平', 'had_dir': '平', 'divergent': False,
     'used_in': ['单挑比分②'], 'pred_score': '1-1', 'actual': '3-1',
     'verdict': 'miss（方向未中，实际主胜；比分未入带）'},
    {'match_num': '012', 'match': '弗洛西诺内 vs 都灵', 'league': '意甲',
     'k_dist': {'value': 1, 'pct': 0.202}, 'k_rec': {'value': 1, 'pct': 0.202},
     'band_top3': [['2-1', 0.091], ['3-2', 0.049], ['1-0', 0.047]],
     'ttg': '3球/4球', 'k_dist_dir': '主胜', 'had_dir': '主胜', 'divergent': False,
     'used_in': ['连续编号比分B', '单挑比分②'], 'pred_score': '2-1', 'actual': '2-0',
     'verdict': 'semi（方向中主胜，净胜+2未入带；带内TOP1为2-1）'},
    {'match_num': '013', 'match': '拉齐奥 vs 卡利亚里', 'league': '意甲',
     'k_dist': {'value': 2, 'pct': 0.226}, 'k_rec': {'value': 2, 'pct': 0.226},
     'band_top3': [['2-0', 0.142], ['3-1', 0.070], ['4-2', 0.013]],
     'ttg': '2球/3球', 'k_dist_dir': '主胜', 'had_dir': '主胜', 'divergent': False,
     'used_in': ['稳健比分串', '连续编号比分B'], 'pred_score': '2-0', 'actual': '2-1',
     'verdict': 'semi（方向中主胜，净胜+1未入带；带内TOP1为2-0）'},
    {'match_num': '020', 'match': '维塞乌 vs 里奥阿维', 'league': '葡超',
     'k_dist': {'value': 1, 'pct': 0.208}, 'k_rec': {'value': 1, 'pct': 0.208},
     'band_top3': [['2-1', 0.094], ['1-0', 0.068], ['3-2', 0.038]],
     'ttg': '3球/2球', 'k_dist_dir': '主胜', 'had_dir': '主胜', 'divergent': False,
     'used_in': ['比分串B'], 'pred_score': '2-1', 'actual': '2-1',
     'verdict': 'exact（方向中主胜，带内TOP1 2-1精确命中）'},
]

existing = {(r.get('date'), r.get('match_num')) for r in d['records']}
n = {'exact': 0, 'semi': 0, 'miss': 0}
for rec in REC:
    key = ('2026-11-01', rec['match_num'])
    if key in existing:
        continue
    row = {'date': '2026-11-01', 'caliber': '双轨制'}
    row.update(rec)
    d['records'].append(row)
    n[rec['verdict'].split('（')[0]] += 1

c = d['cumulative']
c['registered_matches'] += 7
c['exact'] += n['exact']
c['semi'] += n['semi']
c['miss'] += n['miss']
c['exact_hit_rate'] = round(c['exact'] / c['registered_matches'], 3)
c['status'] = ('维持试用，不转正（截至2026-11-01 双轨制累计%s场 exact %d/%s=%.1f%%，远低于60%%转正线；'
               '11-01 回填7场：exact 1（020）、semi 4（003/007/012/013）、miss 2（004/008））' % (
                   c['registered_matches'], c['exact'], c['registered_matches'], c['exact_hit_rate'] * 100))
c['pending_note'] = ('待回填：2026-10-27 三场（007/008/009）＋2026-10-28 两场（005/006）；'
                     '11-01 七场已于 2026-11-02 回填（1 exact / 4 semi / 2 miss）')
c['updated'] = '2026-11-02'
d['updated'] = '2026-11-02'

io.open(path, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
print('2026-11-01 backfilled', n, 'cumulative', c['registered_matches'], c['exact'], c['semi'], c['miss'])
