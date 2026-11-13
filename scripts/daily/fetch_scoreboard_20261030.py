import json, io, subprocess, time

SLUGS = ['aus.1', 'ger.2', 'fra.1', 'nor.1', 'ned.2', 'ger.1', 'eng.2', 'esp.1', 'por.1', 'bra.1']
out = {}
for s in SLUGS:
    url = ('https://site.api.espn.com/apis/site/v2/sports/soccer/%s/scoreboard?dates=20261030' % s)
    p = subprocess.run(['curl.exe', '-s', url], capture_output=True)
    try:
        d = json.loads(p.stdout.decode('utf-8-sig'))
        evs = []
        for e in d.get('events', []):
            comp = e['competitions'][0]
            cs = comp['competitors']
            hc = [c for c in cs if c['homeAway'] == 'home'][0]
            ac = [c for c in cs if c['homeAway'] == 'away'][0]
            hls = [int(x.get('displayValue') or 0) for x in (hc.get('linescores') or [])]
            als = [int(x.get('displayValue') or 0) for x in (ac.get('linescores') or [])]
            evs.append({
                'id': e['id'],
                'home': hc['team'].get('displayName'),
                'away': ac['team'].get('displayName'),
                'ft': '%s-%s' % (hc.get('score'), ac.get('score')),
                'ht': ('%d-%d' % (hls[0], als[0])) if hls and als else None,
                'status': comp['status']['type'].get('detail'),
            })
        out[s] = evs
        print('==' + s, len(evs))
        for e in evs:
            print('  ', e['home'], e['ft'], e['away'], 'HT', e['ht'], '|', e['status'], '|', e['id'])
    except Exception as ex:
        print(s, 'FAIL', ex)
    time.sleep(0.3)

json.dump(out, io.open('reports/data/20261030_espn_scoreboard.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
