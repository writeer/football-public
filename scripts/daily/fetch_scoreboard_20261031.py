# -*- coding: utf-8 -*-
"""2026-10-31 周六：按联赛抓 ESPN scoreboard(dates=20261031)，落盘原始赛果"""
import json, io, subprocess, time

SLUGS = ['jpn.1', 'jpn.2', 'kor.1', 'aus.1', 'eng.1', 'eng.2', 'esp.1', 'ita.1', 'ger.1', 'nor.1', 'ned.1']
out = {}
for slug in SLUGS:
    url = ('https://site.api.espn.com/apis/site/v2/sports/soccer/%s/scoreboard?dates=20261031' % slug)
    p = subprocess.run(['curl.exe', '-s', '--max-time', '30', url], capture_output=True)
    try:
        d = json.loads(p.stdout.decode('utf-8-sig'))
    except Exception as ex:
        out[slug] = {'error': str(ex)}
        print(slug, 'ERROR', ex)
        continue
    evs = []
    for e in d.get('events', []):
        comp = e['competitions'][0]
        cs = comp['competitors']
        hc = [c for c in cs if c['homeAway'] == 'home'][0]
        ac = [c for c in cs if c['homeAway'] == 'away'][0]
        hls = [int(x.get('displayValue') or 0) for x in (hc.get('linescores') or [])]
        als = [int(x.get('displayValue') or 0) for x in (ac.get('linescores') or [])]
        evs.append({
            'event_id': e['id'],
            'home': hc['team'].get('displayName'),
            'away': ac['team'].get('displayName'),
            'ft': '%s-%s' % (hc.get('score'), ac.get('score')),
            'ht': ('%d-%d' % (hls[0], als[0])) if hls and als else None,
            'status': comp['status']['type'].get('detail'),
            'completed': comp['status']['type'].get('completed'),
            'date': e.get('date'),
        })
    out[slug] = evs
    print(slug, len(evs))
    for x in evs:
        print('   ', x['home'], x['ft'], x['away'], 'HT', x['ht'], x['status'])
    time.sleep(0.3)

json.dump(out, io.open('reports/data/20261031_scoreboard_raw.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved')
