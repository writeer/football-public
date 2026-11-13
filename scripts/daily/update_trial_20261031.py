# -*- coding: utf-8 -*-
"""回填 2026-10-31 比分串试用台账（7场）并更新累计"""
import json, io

path = 'memory/trials/score_parlay_trial.json'
d = json.load(io.open(path, encoding='utf-8-sig'))

ACT = {
    '003': ('4-0', 'semi（方向中主胜，净胜+4未入带；带内TOP1为2-1）'),
    '004': ('1-1', 'miss（方向未中，实际平局；比分未入带）'),
    '005': ('0-0', 'semi（方向中平，0-0为带内#3，未精确）'),
    '017': ('2-2', 'miss（方向未中，实际平局；比分未入带）'),
    '018': ('2-0', 'semi（方向中主胜，净胜+2未入带；带内TOP1为1-0）'),
    '024': ('2-1', 'semi（方向中主胜，净胜+1未入带；带内TOP1为2-0）'),
    '027': ('6-1', 'semi（方向中主胜，净胜+5未入带；带内TOP1为2-0）'),
}

n = {'exact': 0, 'semi': 0, 'miss': 0}
for r in d['records']:
    if r['date'] == '2026-10-31' and r['match_num'] in ACT:
        act, verdict = ACT[r['match_num']]
        r['actual'] = act
        r['verdict'] = verdict
        key = verdict.split('（')[0]
        n[key] += 1

c = d['cumulative']
c['registered_matches'] = c.get('registered_matches', 29) + 7
c['exact'] += n['exact']
c['semi'] += n['semi']
c['miss'] += n['miss']
c['exact_hit_rate'] = round(c['exact'] / c['registered_matches'], 3)
c['pending_matches'] = max(0, c.get('pending_matches', 12) - 7)
c['status'] = ('维持试用，不转正（截至2026-10-31 双轨制累计%s场 exact %d/%s=%.1f%%，远低于60%%转正线；'
               '10-31 回填7场：exact 0、semi 5（003/005/018/024/027）、miss 2（004/017））' % (
                   c['registered_matches'], c['exact'], c['registered_matches'], c['exact_hit_rate'] * 100))
c['pending_note'] = ('待回填：2026-10-27 三场（007/008/009）＋2026-10-28 两场（005/006）；'
                     '10-31 七场已于 2026-11-01 回填（0 exact / 5 semi / 2 miss）')
c['updated'] = '2026-11-01'
d['updated'] = '2026-11-01'

io.open(path, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1))
print('10-31 backfilled', n, 'cumulative', c['registered_matches'], c['exact'], c['semi'], c['miss'])
