# -*- coding: utf-8 -*-
"""2026-10-27 赛果抓取：ESPN summary linescores（含半场）"""
import json, io, subprocess, time

D = r'e:\VibeCoding\football\reports\data'
MAP = [
    ('周二001', '亚冠精英', 'Kyoto Sanga', 'Newcastle Jets', 'afc.champions', '401912637'),
    ('周二002', '亚冠精英', 'Daejeon Hana Citizen FC', 'Vissel Kobe', 'afc.champions', '401912636'),
    ('周二003', '亚冠精英', 'Beijing Guoan', 'Jeonbuk Hyundai Motors', 'afc.champions', '401912621'),
    ('周二004', '德国杯', 'Hamburg SV', 'Eintracht Frankfurt', 'ger.dfb_pokal', '401916920'),
    ('周二005', '意甲', 'Sassuolo', 'Lazio', 'ita.1', '401874980'),
    ('周二006', '瑞超', 'AIK', 'IF Elfsborg', 'swe.1', '401842858'),
    ('周二007', '德国杯', 'Borussia Dortmund', 'Werder Bremen', 'ger.dfb_pokal', '401917030'),
    ('周二008', '德国杯', 'FC Cologne', '1. FC Union Berlin', 'ger.dfb_pokal', '401917026'),
    ('周二009', '意甲', 'AS Roma', 'Cagliari', 'ita.1', '401874780'),
    ('周二010', '意甲', 'Torino', 'Como', 'ita.1', '401874786'),
]

out = []
for num, lg, h, a, slug, eid in MAP:
    url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/%s/summary?event=%s' % (slug, eid)
    p = subprocess.run(['curl.exe', '-s', url], capture_output=True)
    try:
        d = json.loads(p.stdout.decode('utf-8-sig'))
        comp = d['header']['competitions'][0]
        hc = [c for c in comp['competitors'] if c['homeAway'] == 'home'][0]
        ac = [c for c in comp['competitors'] if c['homeAway'] == 'away'][0]
        hls = [int(x.get('displayValue') or 0) for x in (hc.get('linescores') or [])]
        als = [int(x.get('displayValue') or 0) for x in (ac.get('linescores') or [])]
        ft = '%s-%s' % (hc.get('score'), ac.get('score'))
        ht = '%d-%d' % (hls[0], als[0]) if hls and als else None
        status = comp['status']['type'].get('detail')
        out.append({'num': num, 'league': lg, 'home': h, 'away': a, 'date': '2026-10-27',
                    'ft': ft, 'ht': ht, 'status': status, 'event_id': eid,
                    'source': 'ESPN site.api summary（header.competitions.linescores）'})
        print(num, h, a, ft, 'HT', ht, status)
    except Exception as e:
        out.append({'num': num, 'league': lg, 'home': h, 'away': a, 'date': '2026-10-27',
                    'ft': None, 'ht': None, 'error': str(e)})
        print(num, 'FAIL', e)
    time.sleep(0.4)

json.dump(out, io.open(D + r'\20261027_results_official.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved', len(out))
