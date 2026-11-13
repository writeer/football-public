# -*- coding: utf-8 -*-
import json, io
m = json.load(io.open('reports/data/20261103_model_output.json', encoding='utf-8'))
for k, v in m.items():
    print(k, v['home'], 'vs', v['away'])
    print('  λ', v['lambda'], 'HAD', {a: round(b*100,1) for a,b in v['probs_final'].items()},
          'k_dist', v['k_dist'], 'k_rec', v['k_rec'], '让', {a: round(b*100,1) for a,b in v['handicap'].items()},
          '单关', v['single']['uplift'])
    print('  TTG', {a: round(b*100,1) for a,b in v['ttg'].items()})
    print('  TOP10', [(s, round(p*100,1)) for s,p in v['top_scores'][:7]])
    print('  HTFT', {a: round(b*100,1) for a,b in v['htft'].items()})
    print('  半场', [(s, round(p*100,1)) for s,p in v['ht_scores'][:3]])
