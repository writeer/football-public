import json, io, subprocess, time

D = 'reports/data'
PB = json.load(io.open(D + '/20261030_predictions.json', encoding='utf-8-sig'))
EV = {
    '周五001': ('aus.1', '401892150'),
    '周五002': ('ger.2', '401885066'),
    '周五003': ('fra.1', '401876416'),
    '周五004': ('fra.1', '401876421'),
    '周五005': ('nor.1', '401843468'),
    '周五006': ('ned.2', '401875873'),
    '周五007': ('ger.1', '401884746'),
    '周五008': ('eng.2', '401880190'),
    '周五009': ('esp.1', '401882817'),
    '周五010': ('fra.1', '401876420'),
    '周五011': ('por.1', '401885408'),
    '周五012': ('bra.1', '401841295'),
}

out = []
for m in PB:
    num = m['num']
    slug, eid = EV[num]
    url = ('https://site.api.espn.com/apis/site/v2/sports/soccer/%s/summary?event=%s' % (slug, eid))
    p = subprocess.run(['curl.exe', '-s', url], capture_output=True)
    rec = {'num': num, 'league': m['league'], 'home': m['home'], 'away': m['away'],
           'date': '2026-10-30', 'event_id': eid,
           'source': 'ESPN site.api summary（header.competitions.linescores）'}
    try:
        d = json.loads(p.stdout.decode('utf-8-sig'))
        comp = d['header']['competitions'][0]
        cs = comp['competitors']
        hc = [c for c in cs if c['homeAway'] == 'home'][0]
        ac = [c for c in cs if c['homeAway'] == 'away'][0]
        hls = [int(x.get('displayValue') or 0) for x in (hc.get('linescores') or [])]
        als = [int(x.get('displayValue') or 0) for x in (ac.get('linescores') or [])]
        rec['ft'] = '%s-%s' % (hc.get('score'), ac.get('score'))
        rec['ht'] = ('%d-%d' % (hls[0], als[0])) if hls and als else None
        rec['status'] = comp['status']['type'].get('detail')
    except Exception as ex:
        rec['ft'] = None
        rec['ht'] = None
        rec['error'] = str(ex)
    out.append(rec)
    print(num, rec['home'], rec.get('ft'), rec['away'], 'HT', rec.get('ht'), rec.get('error', ''))
    time.sleep(0.3)

json.dump(out, io.open(D + '/20261030_results_official.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved', len(out))
