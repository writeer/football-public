# -*- coding: utf-8 -*-
"""2026-10-31 比分串试用台账登记（规则67，双轨制；赛果待回填）"""
import json, io, os

R = {r['num'][-3:]: r for r in json.load(io.open('reports/data/20261031_model_output.json', encoding='utf-8'))}
INFO = json.load(io.open('reports/data/20261031_info.json', encoding='utf-8'))

USE = {
    '003': ['连续编号比分串①'], '004': ['连续编号比分串①'],
    '005': ['稳健比分串'], '017': ['连续编号比分串②'], '018': ['连续编号比分串②'],
    '024': ['稳健比分串', '单挑比分①'], '027': ['单挑比分②'],
}
PRED = {'003': '2:1', '004': '1:2', '005': '1:1', '017': '2:1', '018': '1:0',
        '024': '2:0', '027': '3:0'}
NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}

jp = 'memory/trials/score_parlay_trial.json'
d = json.load(io.open(jp, encoding='utf-8'))
for k in ('003', '004', '005', '017', '018', '024', '027'):
    r = R[k]
    info = INFO['周六' + k]
    band = [['%d-%d' % (a, b), p] for a, b, p in r['band']]
    d['records'].append({
        'date': '2026-10-31', 'caliber': '双轨制', 'match_num': k,
        'match': '%s vs %s' % (r['home'], r['away']), 'league': r['league'],
        'k_dist': {'value': r['k_dist'], 'pct': r['k_dist_prob']},
        'k_rec': {'value': r['k_rec'], 'pct': r['k_rec_prob']},
        'band_top3': band, 'ttg': '%d球/%d球' % (r['ttg_top2'][0], r['ttg_top2'][1]),
        'k_dist_dir': NAME_CN['draw'] if r['k_dist'] == 0 else (NAME_CN['home'] if r['k_dist'] > 0 else NAME_CN['away']),
        'had_dir': NAME_CN[r['primary']], 'divergent': not r['k_consistent'],
        'used_in': USE[k], 'pred_score': PRED[k], 'actual': None, 'verdict': 'pending',
    })
d['updated'] = '2026-10-31'
d['cumulative']['pending_matches'] = d['cumulative'].get('pending_matches', 0) + 7
d['cumulative']['pending_note'] = d['cumulative'].get('pending_note', '') + '；2026-10-31 新增7场（003/004/005/017/018/024/027），赛果待回填'
json.dump(d, io.open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

lines = ['', '## 2026-10-31（周六，28场）登记（赛果待回填）', '',
         '| 编号 | 对阵 | 联赛 | 分布众数 k_dist | 推荐众数 k_rec | 带内候选TOP3 | 首推总进球档 | k_dist方向 | HAD首推方向 | 是否分歧 | 实际比分 | 判定 |',
         '|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---:|:---|:---|']
for k in ('003', '004', '005', '017', '018', '024', '027'):
    r = R[k]
    band = ' > '.join('%s(%.1f%%)' % (s, p * 100) for s, p in
                      [['%d-%d' % (a, b), p] for a, b, p in r['band']])
    kdir = '平' if r['k_dist'] == 0 else ('主胜' if r['k_dist'] > 0 else '客胜')
    lines.append('| %s | %s vs %s | %s | %+d（%.1f%%） | %+d（%.1f%%） | %s | %d球/%d球 | %s | %s | %s | — | 待回填 |' % (
        k, r['home'], r['away'], r['league'], r['k_dist'], r['k_dist_prob'] * 100,
        r['k_rec'], r['k_rec_prob'] * 100, band, r['ttg_top2'][0], r['ttg_top2'][1],
        kdir, NAME_CN[r['primary']], '**分歧**' if not r['k_consistent'] else '一致'))
lines += ['',
          '> 本轮用于**正向流程比分串**的场次：024、005（稳健比分串）；003、004（连续编号比分串①）；017、018（连续编号比分串②）；024（单挑比分①）、027（单挑比分②）。',
          '> 去重后计入 **7 场**：003／004／005／017／018／024／027。搏冷比分串（006、022）按口径不计入。',
          '> 累计口径见 `memory/trials/score_parlay_trial.json`（pending +7）。', '']
with io.open('memory/trials/score_parlay_trial.md', 'a', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('appended 7 records')
