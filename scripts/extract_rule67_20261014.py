# -*- coding: utf-8 -*-
"""从模型输出提取2026-10-14的6场规则67登记字段"""
import json

files = [r'E:\VibeCoding\football\reports\data\20261014_model_001_007.json',
         r'E:\VibeCoding\football\reports\data\20261014_model_008_014.json']
need = ['001', '002', '003', '005', '006', '013']
for f in files:
    raw = open(f, encoding='utf-8').read()
    d = json.loads(raw[raw.find('{'):])
    matches = d['matches']
    for num in need:
        m = matches.get(num)
        if not m:
            continue
        print('====', num, m['home'], 'vs', m['away'], '|', m['league'], '| gl=', m['goalLine'])
        print('fused_had:', m['fused_had'], '| first:', m['had_first'], '| second:', m['had_second'])
        print('handicap:', m['handicap'])
        print('ttg_top2:', m['ttg_top2'], '| 6+:', m.get('ttg_6plus'))
        print('crs_top5:', m['crs_top5'])
        print('hafu_top3:', m['hafu_top3'])
        for key in ('k_dist', 'k_rec', 'band_top3', 'band_candidates', 'double_track', 'size_ball', 'size_line', '博分', 'bo_score'):
            if key in m:
                print(key, '=', m[key])
        print()
