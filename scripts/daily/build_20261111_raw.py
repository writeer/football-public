# -*- coding: utf-8 -*-
"""由体彩计算器原始 payload 构建 20261111_raw.json（仅比赛日期=2026-11-11 的4场）"""
import json, io

calc = json.load(io.open('reports/data/20261111_calc_raw.json', encoding='utf-8'))
list_ = (calc.get('value') or {}).get('matchInfoList') or []

HAD = {'h': 'home', 'd': 'draw', 'a': 'away'}
HAFU = {'hh': 'HH', 'hd': 'HD', 'ha': 'HA', 'dh': 'DH', 'dd': 'DD',
        'da': 'DA', 'ah': 'AH', 'ad': 'AD', 'aa': 'AA'}

matches = []
for day in list_:
    for m in day.get('subMatchList') or []:
        if m.get('matchDate') not in ('2026-11-11', '2026-11-12'):
            continue
        hh = m.get('hhad') or {}
        crs = m.get('crs') or {}
        crs_out = []
        for k, v in crs.items():
            if not k.startswith('s') or k.endswith('f'):
                continue
            if k.startswith('s1s'):
                key = {'sh': '胜其他', 'sd': '平其他', 'sa': '负其他'}.get(k[2:])
            else:
                key = '%d-%d' % (int(k[1:3]), int(k[4:6]))
            if key:
                crs_out.append({'key': key, 'odds': float(v)})
        ttg = m.get('ttg') or {}
        ttg_out = []
        for n in range(8):
            k = 's%d' % n
            if k in ttg:
                ttg_out.append({'key': '7+' if n == 7 else str(n), 'odds': float(ttg[k])})
        hafu = m.get('hafu') or {}
        hafu_out = [{'key': HAFU[k], 'odds': float(v)} for k, v in hafu.items()
                    if k in HAFU and not k.endswith('f')]
        matches.append({
            'matchNumStr': m['matchNumStr'],
            'matchDate': m['matchDate'],
            'matchTime': m['matchTime'],
            'league': m.get('leagueAbbName'),
            'home': m.get('homeTeamAbbName'),
            'away': m.get('awayTeamAbbName'),
            'bettingSingle': m.get('bettingSingle'),
            'markets': {
                'had': {'outcomes': [{'key': HAD[k], 'odds': float(m['had'][k])} for k in ('h', 'd', 'a')]},
                'hhad': {'goalLine': int(float(hh.get('goalLineValue') or hh.get('goalLine') or 0)),
                         'outcomes': [{'key': HAD[k], 'odds': float(hh[k])} for k in ('h', 'd', 'a')]},
                'crs': {'outcomes': crs_out},
                'ttg': {'outcomes': ttg_out},
                'hafu': {'outcomes': hafu_out},
            },
        })

matches.sort(key=lambda x: x['matchNumStr'])
io.open('reports/data/20261111_raw.json', 'w', encoding='utf-8').write(
    json.dumps({'date': '2026-11-11', 'matches': matches}, ensure_ascii=False, indent=1))
print('matches', len(matches))
for m in matches:
    print(m['matchNumStr'], m['league'], m['home'], 'vs', m['away'], m['matchTime'],
          'line', m['markets']['hhad']['goalLine'], 'single', m['bettingSingle'],
          'HAD', [(o['key'], o['odds']) for o in m['markets']['had']['outcomes']])
