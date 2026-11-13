# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open(r'reports\data\20261014_matches_full_odds.json', encoding='utf-8-sig'))
ms = d['data']['matches']
out = {}
for m in ms[:7]:
    num = m['matchNumStr']
    mk = m['markets']
    crs = [(o['labelZh'], o['odds']) for o in mk['crs']['outcomes']]
    ttg = [(o['labelZh'], o['odds']) for o in mk['ttg']['outcomes']]
    hafu = [(o['labelZh'], o['odds']) for o in mk['hafu']['outcomes']]
    out[num] = {'home': m['home']['allName'], 'away': m['away']['allName'],
                'crs': crs, 'ttg': ttg, 'hafu': hafu}
    print('#'*72)
    print(num, m['home']['allName'], 'vs', m['away']['allName'])
    print('CRS:', crs)
    print('TTG:', ttg)
    print('HAFU:', hafu)

json.dump(out, open(r'reports\data\20261014_market_crs_ttg_hafu_001_007.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nsaved market odds json')
