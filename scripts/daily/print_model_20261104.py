# -*- coding: utf-8 -*-
import json, io
mo = json.load(io.open('reports/data/20261104_model_output.json', encoding='utf-8'))
for num, r in mo.items():
    kd = list(r['kdist'].items())[:3]
    print(num, r['home'], 'vs', r['away'], 'λ=%.2f' % r['lambda']['total'])
    print('  kdist', [(k, round(v*100, 1)) for k, v in kd], 'k_dist', r['k_dist']['k'], 'k_rec', r['k_rec'])
    print('  scores', [(s, round(v*100, 2)) for s, v in r['top_scores'][:5]])
    print('  htt', [(s, round(v*100, 2)) for s, v in r['ht_scores']])
    print('  ttg', [(k, round(v*100, 1)) for k, v in r['ttg'].items()])
    hafu = r['odds']['hafu']
    print('  HAFU', {k: hafu.get(k) for k in ['HH','HD','HA','DH','DD','DA','AH','AD','AA']})
    crs = r['odds']['crs']
    print('  CRS(top)', {s: crs.get(s) for s, v in r['top_scores'][:5]})
