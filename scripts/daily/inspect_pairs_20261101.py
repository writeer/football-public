# -*- coding: utf-8 -*-
"""按今日对阵打印主客队积分榜行（用于撰写信息与核查）"""
import json, io

PAIRS = [
    ('日职', 'V-Varen Nagasaki', 'Verdy'), ('韩职', 'Ulsan HD', 'Gangwon'),
    ('日职', 'Machida', 'Gamba Osaka'), ('韩职', 'Seoul', 'Incheon'),
    ('澳超', 'Perth Glory', 'Adelaide United'), ('荷甲', 'Zwolle', 'Den Haag'),
    ('意甲', 'Como', 'Venezia'), ('西甲', 'Getafe', 'Sevilla'),
    ('瑞超', 'Malmo FF', 'Hammarby'), ('荷甲', 'Excelsior', 'Twente'),
    ('挪超', 'Brann', 'Molde'), ('意甲', 'Frosinone', 'Torino'),
    ('意甲', 'Lazio', 'Cagliari'), ('德甲', 'Union Berlin', 'FC Koln'),
    ('荷甲', 'Groningen', 'Sparta Rotterdam'), ('英超', 'Liverpool', 'Arsenal'),
    ('德甲', 'Eintracht Frankfurt', 'Hamburger SV'), ('意甲', 'Lecce', 'Genoa'),
    ('西甲', 'Elche', 'Valencia'), ('葡超', 'Academico Viseu', 'Rio Ave'),
    ('意甲', 'Juventus', 'Napoli'), ('法甲', 'Marseille', 'Toulouse'),
    ('西甲', 'Ath Bilbao', 'Real Sociedad'), ('巴西', 'Gremio', 'Atletico-MG'),
    ('美职', 'New England Revolution', 'Inter Miami'),
]
KEY = {'日职': 'japan1', '韩职': 'korea1', '澳超': 'australia', '荷甲': 'holland1',
       '意甲': 'italy1', '西甲': 'spain1', '瑞超': 'sweden1', '挪超': 'norway',
       '德甲': 'germany1', '英超': 'premier', '葡超': 'portugal1', '法甲': 'france1',
       '巴西': 'brazil1', '美职': 'usa1'}
CACHE = {}
for lg in set(KEY.values()):
    CACHE[lg] = json.load(io.open('reports/data/table_{}.json'.format(lg), encoding='utf-8'))['table']

for i, (lg, h, a) in enumerate(PAIRS, 1):
    rows = {r['team']: r for r in CACHE[KEY[lg]]}
    def fmt(t):
        r = rows.get(t)
        if not r:
            return '{} MISSING'.format(t)
        return '{} P{} {}场 {}胜{}平{}负 {}-{} {}分 场均{:.2f}/{:.2f}'.format(
            t, r['position'], r['played'], r['won'], r['drawn'], r['lost'],
            r['goals_for'], r['goals_against'], r['points'],
            r['avg_goals_scored'], r['avg_goals_conceded'])
    print('{:03d} {}: {} | {}'.format(i, lg, fmt(h), fmt(a)))
