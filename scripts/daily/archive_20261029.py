# -*- coding: utf-8 -*-
"""2026-10-29 预测归档：reports/data/20261029_predictions.json"""
import json, io

res = json.load(io.open('reports/data/20261029_model_output.json', encoding='utf-8'))
CONF_FIX = {'周四005': '★'}   # 总控裁决：杯赛轮换降级
out = []
for r in res:
    crs = []
    for a, b, p in r['top_scores']:
        o = (r['odds_crs'] or {}).get('%d:%d' % (a, b))
        crs.append({'score': '%d-%d' % (a, b), 'prob': p, 'odds': o})
    hts = [{'score': '%d-%d' % (a, b), 'prob': p} for a, b, p in r['ht_scores']]
    hhad = dict(r['odds_hhad'] or {})
    if r['hhad_line'] is not None:
        hhad['handicap'] = r['hhad_line']
    out.append({
        'num': r['num'], 'league': r['league'], 'home': r['home'], 'away': r['away'],
        'kickoff': r['time'], 'is_single': r['is_single'], 'rule63': r['rule63'],
        'value_eur': {'home': r['value']['home'], 'away': r['value']['away'],
                      'ratio': round(max(r['value']['home'], r['value']['away']) /
                                     min(r['value']['home'], r['value']['away']), 2)},
        'injuries': {'home_count': r['injury']['home_count'],
                     'away_count': r['injury']['away_count'],
                     'detail': {'home': r['injury']['home'], 'away': r['injury']['away']}},
        'venue': r['venue'], 'weather': r['weather'], 'h2h': r['h2h'],
        'stadium': r['stadium'],
        'odds_had': r['odds_had'], 'odds_hhad': hhad,
        'odds_crs': r['odds_crs'], 'odds_ttg': r['odds_ttg'], 'odds_hafu': r['odds_hafu'],
        'model': {'home': r['fused']['home'], 'draw': r['fused']['draw'], 'away': r['fused']['away'],
                  'lambda_home': r['lambda_home'], 'lambda_away': r['lambda_away'],
                  'lambda_base': r['lambda_base'], 'market': r['market'], 'shin': r['shin'],
                  'rule65': r['rule65'], 'h2h_shift': r['h2h_shift'],
                  'table_missing': r['table_missing']},
        'recommendation': {'had_primary': r['primary'], 'had_primary_prob': r['primary_prob'],
                           'had_secondary': r['secondary'], 'had_secondary_prob': r['secondary_prob'],
                           'hc_primary': r['hc_first'], 'hc_secondary': r['hc_second'],
                           'hc_line': r['hhad_line'],
                           'ttg_top2': r['ttg_top2'], 'tier': r['tier'], 'over_under': r['over_under'],
                           'htft_top3': r['htft_top3'], 'cr_top5': crs, 'ht_score': hts},
        'k_dist': r['k_dist'], 'k_dist_prob': r['k_dist_prob'],
        'k_rec': r['k_rec'], 'k_rec_prob': r['k_rec_prob'], 'k_consistent': r['k_consistent'],
        'conf': CONF_FIX.get(r['num'], r['conf']), 'conf_model': r['conf'], 'diverge': r['diverge'],
        'crs': crs, 'ht_score': hts,
    })

json.dump(out, io.open('reports/data/20261029_predictions.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved reports/data/20261029_predictions.json, matches:', len(out))
