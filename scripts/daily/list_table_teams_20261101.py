# -*- coding: utf-8 -*-
"""打印各联赛积分榜球队名（用于 TEAM_ALIAS 映射核对）"""
import json, io
FNS = ['japan1', 'korea1', 'australia', 'holland1', 'italy1', 'spain1',
       'sweden1', 'norway', 'germany1', 'premier', 'portugal1', 'france1',
       'usa1', 'brazil1']
for k in FNS:
    d = json.load(io.open('reports/data/table_{}.json'.format(k), encoding='utf-8'))
    print(k, [r['team'] for r in d['table']])
