# -*- coding: utf-8 -*-
"""2026-10-31 周六 28场：ESPN summary 抓半场比分（linescores），J2/K1 用公开赛果补齐"""
import json, io, subprocess, time

RAW = json.load(io.open('reports/data/20261031_scoreboard_raw.json', encoding='utf-8-sig'))

# 中文队名 → ESPN 英文名（仅本日 28 场）
MAP = {
    '周六001': ('jpn.1', 'Fagiano Okayama', 'FC Tokyo'),
    '周六002': (None, 'Vegalta Sendai', 'RB Omiya Ardija'),
    '周六003': ('jpn.1', 'Kashiwa Reysol', 'Urawa Red Diamonds'),
    '周六004': (None, 'Gwangju FC', 'Gimcheon Sangmu'),
    '周六005': ('aus.1', 'Macarthur FC', 'Western Sydney Wanderers FC'),
    '周六006': ('eng.1', 'Chelsea', 'Manchester United'),
    '周六007': ('eng.2', 'Lincoln City', 'Birmingham City'),
    '周六008': ('esp.1', 'Levante', 'Atlético Madrid'),
    '周六009': ('ita.1', 'Bologna', 'Monza'),
    '周六010': ('ger.1', 'Bayer Leverkusen', 'VfB Stuttgart'),
    '周六011': ('ger.1', 'Schalke 04', 'RB Leipzig'),
    '周六012': ('ger.1', 'FC Augsburg', 'SC Freiburg'),
    '周六013': ('ger.1', 'Borussia Mönchengladbach', 'SC Paderborn 07'),
    '周六014': ('ger.1', 'Werder Bremen', 'TSG Hoffenheim'),
    '周六015': ('eng.1', 'Coventry City', 'Sunderland'),
    '周六016': ('eng.1', 'AFC Bournemouth', 'Leeds United'),
    '周六017': ('eng.1', 'Hull City', 'Ipswich Town'),
    '周六018': ('eng.1', 'Brentford', 'Nottingham Forest'),
    '周六019': ('nor.1', 'Fredrikstad', 'Rosenborg'),
    '周六020': ('esp.1', 'Rayo Vallecano', 'Celta Vigo'),
    '周六021': ('ita.1', 'Udinese', 'AS Roma'),
    '周六022': ('eng.1', 'Tottenham Hotspur', 'Crystal Palace'),
    '周六023': ('ger.1', 'Bayern Munich', 'Borussia Dortmund'),
    '周六024': ('esp.1', 'Real Betis', 'Málaga'),
    '周六025': ('ita.1', 'AC Milan', 'Internazionale'),
    '周六026': ('eng.1', 'Aston Villa', 'Fulham'),
    '周六027': ('esp.1', 'Barcelona', 'Alavés'),
    '周六028': ('ned.1', 'Ajax Amsterdam', 'AZ Alkmaar'),
}

# 无 ESPN 覆盖的两场（WebSearch 公开赛果）
MANUAL = {
    '周六002': {'ft': '1-2', 'ht': '0-1',
                'source': 'Jリーグ公式 jleague.jp + zerozero.pt（Vegalta Sendai 1-2 RB Omiya Ardija，半场0-1）'},
    '周六004': {'ft': '1-1', 'ht': '0-0',
                'source': 'Transfermarkt/WhoScored（Gwangju FC 1-1 Gimcheon Sangmu，半场0-0）'},
}

out = []
for num, (slug, home, away) in MAP.items():
    rec = {'num': num, 'home': home, 'away': away, 'slug': slug}
    if num in MANUAL:
        rec.update(MANUAL[num])
        rec['event_id'] = None
        out.append(rec)
        continue
    ev = None
    for e in RAW.get(slug, []):
        if e['home'] == home and e['away'] == away:
            ev = e
            break
    if not ev:
        rec['ft'] = None
        rec['error'] = 'scoreboard 未匹配'
        out.append(rec)
        print('MISS', num, home, away)
        continue
    rec['event_id'] = ev['event_id']
    rec['ft_scoreboard'] = ev['ft']
    # summary 取半场
    url = ('https://site.api.espn.com/apis/site/v2/sports/soccer/%s/summary?event=%s' % (slug, ev['event_id']))
    p = subprocess.run(['curl.exe', '-s', '--compressed', '--max-time', '30', url], capture_output=True)
    try:
        d = json.loads(p.stdout.decode('utf-8-sig', 'ignore'))
        comp = d['header']['competitions'][0]
        cs = comp['competitors']
        hc = [c for c in cs if c['homeAway'] == 'home'][0]
        ac = [c for c in cs if c['homeAway'] == 'away'][0]
        hls = [int(x.get('displayValue') or 0) for x in (hc.get('linescores') or [])]
        als = [int(x.get('displayValue') or 0) for x in (ac.get('linescores') or [])]
        rec['ft'] = '%s-%s' % (hc.get('score'), ac.get('score'))
        rec['ht'] = ('%d-%d' % (hls[0], als[0])) if hls and als else None
        rec['status'] = comp['status']['type'].get('detail')
        rec['source'] = 'ESPN summary linescores'
    except Exception as ex:
        rec['ft'] = ev['ft']
        rec['ht'] = None
        rec['error'] = str(ex)
    out.append(rec)
    print(num, rec['home'], rec.get('ft'), rec['away'], 'HT', rec.get('ht'), rec.get('error', ''))
    time.sleep(0.25)

json.dump(out, io.open('reports/data/20261031_results_official.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved', len(out))
