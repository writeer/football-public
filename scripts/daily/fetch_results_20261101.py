# -*- coding: utf-8 -*-
"""2026-11-01 周日 25场：ESPN summary 抓全场/半场比分，韩职两场另行补齐"""
import json, io, subprocess, time

# 编号 -> (ESPN slug, event_id, 主队中文, 客队中文)
MAP = {
    '周日001': ('jpn.1', '401877578', '长崎航海', '东京绿茵'),
    '周日003': ('jpn.1', '401877581', '町田泽维亚', '大阪钢巴'),
    '周日005': ('aus.1', '401892145', '珀斯光荣', '阿德莱德联'),
    '周日006': ('ned.1', '401875560', '兹沃勒', '海牙'),
    '周日007': ('ita.1', '401875002', '科莫', '威尼斯'),
    '周日008': ('esp.1', '401882821', '赫塔费', '塞维利亚'),
    '周日009': ('swe.1', '401842868', '马尔默', '哈马比'),
    '周日010': ('ned.1', '401875559', 'SBV精英', '特温特'),
    '周日011': ('nor.1', '401843474', '布兰', '莫尔德'),
    '周日012': ('ita.1', '401874782', '弗洛西诺内', '都灵'),
    '周日013': ('ita.1', '401874983', '拉齐奥', '卡利亚里'),
    '周日014': ('ger.1', '401884750', '柏林联合', '科隆'),
    '周日015': ('ned.1', '401875557', '格罗宁根', '鹿特丹斯巴达'),
    '周日016': ('eng.1', '401879246', '利物浦', '阿森纳'),
    '周日017': ('ger.1', '401884752', '法兰克福', '汉堡'),
    '周日018': ('ita.1', '401874968', '莱切', '热那亚'),
    '周日019': ('esp.1', '401882823', '埃尔切', '巴伦西亚'),
    '周日020': ('por.1', '401885411', '维塞乌', '里奥阿维'),
    '周日021': ('ita.1', '401874949', '尤文图斯', '那不勒斯'),
    '周日022': ('fra.1', '401876417', '马赛', '图卢兹'),
    '周日023': ('esp.1', '401882826', '毕尔巴鄂竞技', '皇家社会'),
    '周日024': ('bra.copa_do_brazil', '401913109', '格雷米奥', '米内罗竞技'),
    '周日025': ('usa.1', '761932', '新英格兰革命', '迈阿密国际'),
}

# 韩职两场：ESPN 无覆盖，用 football-charts / 公开赛果补齐
MANUAL = {
    '周日002': {'home': '蔚山现代', 'away': '江原FC', 'ft': None, 'ht': None,
                'source': '待核（football-charts 韩职数据截至10-31，需公开赛果核验）'},
    '周日004': {'home': '首尔FC', 'away': '仁川联', 'ft': None, 'ht': None,
                'source': '待核（football-charts 韩职数据截至10-31，需公开赛果核验）'},
}

out = []
for num in sorted(set(list(MAP) + list(MANUAL))):
    if num in MANUAL:
        rec = {'num': num}
        rec.update(MANUAL[num])
        out.append(rec)
        print(num, 'MANUAL', rec['ft'])
        continue
    slug, eid, home, away = MAP[num]
    url = ('https://site.api.espn.com/apis/site/v2/sports/soccer/%s/summary?event=%s' % (slug, eid))
    p = subprocess.run(['curl.exe', '-s', '--compressed', '--max-time', '30', url], capture_output=True)
    rec = {'num': num, 'home': home, 'away': away, 'slug': slug, 'event_id': eid}
    try:
        d = json.loads(p.stdout.decode('utf-8-sig', 'ignore'))
        comp = d['header']['competitions'][0]
        cs = comp['competitors']
        hc = [c for c in cs if c['homeAway'] == 'home'][0]
        ac = [c for c in cs if c['homeAway'] == 'away'][0]
        hls = [int(x.get('displayValue') or 0) for x in (hc.get('linescores') or [])]
        als = [int(x.get('displayValue') or 0) for x in (ac.get('linescores') or [])]
        rec['espn_home'] = hc['team'].get('displayName')
        rec['espn_away'] = ac['team'].get('displayName')
        rec['ft'] = '%s-%s' % (hc.get('score'), ac.get('score'))
        rec['ht'] = ('%d-%d' % (hls[0], als[0])) if hls and als else None
        rec['status'] = comp['status']['type'].get('detail')
        rec['completed'] = comp['status']['type'].get('completed')
        rec['source'] = 'ESPN summary linescores'
    except Exception as ex:
        rec['ft'] = None
        rec['ht'] = None
        rec['error'] = str(ex)
    out.append(rec)
    print(num, home, rec.get('ft'), away, 'HT', rec.get('ht'), rec.get('status'), rec.get('error', ''))
    time.sleep(0.25)

json.dump(out, io.open('reports/data/20261101_results_official.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved', len(out))
