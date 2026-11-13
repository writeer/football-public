# -*- coding: utf-8 -*-
"""2026-10-21 周三13场：抓赛果(含半场) + 匹配竞彩场次"""
import json
import urllib.request

BASE = 'https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/{ep}?{q}'
LEAGUES = ['uefa.champions', 'jpn.1', 'esp.1', 'conmebol.libertadores']
DATES = ['20261020', '20261021']

ALIAS = {
    '东京FC': 'FC Tokyo', '柏太阳神': 'Kashiwa Reysol',
    '川崎前锋': 'Kawasaki Frontale', '神户胜利': 'Vissel Kobe',
    '大宫松鼠': 'Omiya', '富山胜利': 'Toyama',
    '科莫': 'Como', '曼联': 'Manchester United',
    '里尔': 'Lille', '加拉塔萨': 'Galatasaray',
    '莱万特': 'Levante', '毕尔巴鄂': 'Athletic',
    '皇马': 'Real Madrid', '莱红牛': 'RB Leipzig',
    '维拉': 'Aston Villa', '维京': 'Viking',
    '贝蒂斯': 'Real Betis', '费耶诺德': 'Feyenoord',
    '拜仁': 'Bayern Munich', '阿森纳': 'Arsenal',
    '里斯本': 'Sporting', 'LASK林茨': 'LASK',
    '布鲁日': 'Club Brugge', '朗斯': 'Lens',
    '帕梅拉斯': 'Palmeiras', '弗鲁米嫩': 'Fluminense',
}


def get(url):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8'))


events = []
for lg in LEAGUES:
    for d in DATES:
        try:
            js = get(BASE.format(lg=lg, ep='scoreboard', q='dates=' + d))
        except Exception as e:
            print(lg, d, 'ERR', str(e)[:60])
            continue
        for ev in js.get('events') or []:
            comp = (ev.get('competitions') or [{}])[0]
            st = ((comp.get('status') or {}).get('type') or {})
            if not st.get('completed'):
                continue
            cs = comp.get('competitors') or []
            h = next((c for c in cs if c.get('homeAway') == 'home'), None)
            a = next((c for c in cs if c.get('homeAway') == 'away'), None)
            if not h or not a:
                continue
            events.append({'lg': lg, 'id': ev['id'], 'date': (ev.get('date') or '')[:10],
                           'home': (h.get('team') or {}).get('displayName'),
                           'away': (a.get('team') or {}).get('displayName'),
                           'ft': '%s-%s' % (h.get('score'), a.get('score'))})

# 补半场
for e in events:
    try:
        sm = get(BASE.format(lg=e['lg'], ep='summary', q='event=' + str(e['id'])))
        comp = ((sm.get('header') or {}).get('competitions') or [{}])[0]
        cs = comp.get('competitors') or []
        h = next((c for c in cs if c.get('homeAway') == 'home'), None)
        a = next((c for c in cs if c.get('homeAway') == 'away'), None)
        hh = (h.get('linescores') or [{}])[0].get('displayValue') if h else None
        ha = (a.get('linescores') or [{}])[0].get('displayValue') if a else None
        e['ht'] = '%s-%s' % (hh, ha) if hh is not None and ha is not None else None
    except Exception as ex:
        e['ht'] = None

# 匹配
matches = json.load(open(r'e:\VibeCoding\football\reports\data\20261021_matches.json', encoding='utf-8-sig'))


def norm(s):
    return (s or '').lower().replace('.', '').replace('-', ' ').strip()


def find(name, side):
    key = norm(ALIAS.get(name, name))
    for e in events:
        t = norm(e[side])
        if key and (key in t):
            return e
    return None


out, miss = [], []
for m in matches:
    h = find(m['home'], 'home')
    a = find(m['away'], 'away')
    if h and a and h is a:
        out.append({'num': m['num'], 'league': m['league'], 'home': m['home'], 'away': m['away'],
                    'date': h['date'], 'ft': h['ft'], 'ht': h.get('ht'),
                    'source': 'ESPN site.api（scoreboard + summary linescores）'})
    else:
        miss.append((m['num'], m['home'], m['away'], m['league']))

json.dump(out, open(r'e:\VibeCoding\football\reports\data\20261021_results_official.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('matched %d/%d' % (len(out), len(matches)))
for x in miss:
    print('MISS', x)
for r in out:
    print('%-9s %-8s %-16s %s  %-18s HT %s' % (r['num'], r['league'], r['home'], r['ft'], r['away'], r['ht']))
