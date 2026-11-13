# -*- coding: utf-8 -*-
"""2026-10-20（周二）10场：从体彩全玩法赔率文件生成模型输入 matches.json"""
import json, io, sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = 'reports/data/20261020_matches_full.json'
OUT = 'reports/data/20261020_matches.json'

LEAGUE_CN = {'欧冠': '欧冠', '英冠': '英冠'}

d = json.load(io.open(SRC, encoding='utf-8-sig'))
out = []
for m in d['data']['matches']:
    mk = m['markets']
    lg = LEAGUE_CN.get(m['league']['abbName'], m['league']['abbName'])
    rec = {
        'num': m['matchNumStr'], 'matchId': str(m['matchId']),
        'time': m['matchDate'] + ' ' + m['matchTime'],
        'league': lg, 'league_all': m['league']['allName'],
        'home': m['home']['abbName'], 'away': m['away']['abbName'],
        'home_all': m['home']['allName'], 'away_all': m['away']['allName'],
        'home_rank': m['home'].get('rank'), 'away_rank': m['away'].get('rank'),
        'betting_single': bool(m.get('bettingSingle')),
    }
    for pool in ('had', 'hhad', 'crs', 'ttg', 'hafu'):
        if pool in mk:
            if pool == 'hhad':
                rec['hhad'] = {'goalLine': mk['hhad'].get('goalLine'),
                               'outcomes': [{'key': o['key'], 'odds': o['odds'], 'noVig': o.get('noVigProb')}
                                            for o in mk['hhad']['outcomes']]}
            else:
                rec[pool] = [{'key': o['key'], 'odds': o['odds'], 'noVig': o.get('noVigProb')}
                             for o in mk[pool]['outcomes']]
    out.append(rec)

json.dump(out, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved', OUT, len(out))
for r in out:
    print(r['num'], r['league'], r['home'], 'vs', r['away'], '| pools:', [k for k in ('had', 'hhad', 'crs', 'ttg', 'hafu') if k in r])
