# -*- coding: utf-8 -*-
"""2026-11-08 数据同步完整性校验：场次数、玩法完整度、队名映射、积分榜一致性、时间戳
输出：reports/data/20261108_sync_check.json
"""
import json, io, os

D = 'reports/data'
TABLE_FILE = {
    '西甲': 'table_spain1.json', '芬超': 'table_finland1.json', '荷甲': 'table_holland1.json',
    '挪超': 'table_norway.json', '英超': 'table_premier.json', '意甲': 'table_italy1.json',
    '德甲': 'table_germany1.json', '瑞超': 'table_sweden1.json', '法甲': 'table_france1.json',
    '葡超': 'table_portugal1.json',
}
TEAM_ALIAS = {
    # 西甲
    '埃尔切': 'Elche', '皇家贝蒂斯': 'Betis', '皇家社会': 'Real Sociedad',
    '巴列卡诺': 'Rayo Vallecano', '比利亚雷亚尔': 'Villarreal', '赫塔费': 'Getafe',
    '维戈塞尔塔': 'Celta Vigo', '莱万特': 'Levante', '马德里竞技': 'Atl. Madrid',
    '巴塞罗那': 'Barcelona',
    # 芬超
    '库奥皮奥': 'KuPS', '国际图尔库': 'Inter Turku',
    # 荷甲
    '特温特': 'Twente', '阿贾克斯': 'Ajax', '阿尔克马尔': 'AZ Alkmaar',
    '格罗宁根': 'Groningen',
    # 挪超
    '特罗姆瑟': 'Tromso', '博德闪耀': 'Bodo/Glimt',
    # 英超
    '桑德兰': 'Sunderland', '切尔西': 'Chelsea', '伊普斯维奇': 'Ipswich',
    '伯恩茅斯': 'Bournemouth', '水晶宫': 'Crystal Palace', '利物浦': 'Liverpool',
    '曼彻斯特联': 'Manchester Utd', '阿斯顿维拉': 'Aston Villa',
    # 意甲
    '蒙扎': 'Monza', '亚特兰大': 'Atalanta', '热那亚': 'Genoa', 'AC米兰': 'AC Milan',
    '国际米兰': 'Inter', '科莫': 'Como', '佛罗伦萨': 'Fiorentina', '尤文图斯': 'Juventus',
    # 德甲
    '科隆': 'FC Koln', '勒沃库森': 'Bayer Leverkusen', '弗赖堡': 'Freiburg',
    '柏林联合': 'Union Berlin', '霍芬海姆': 'Hoffenheim', '沙尔克04': 'Schalke',
    # 瑞超
    'AIK索尔纳': 'AIK', '赫根': 'Hacken',
    # 法甲
    '勒芒': 'Le Mans', '摩纳哥': 'Monaco', '朗斯': 'Lens', '马赛': 'Marseille',
    # 葡超
    '吉马良斯': 'Vitoria Guimaraes', '波尔图': 'FC Porto',
}
POOL_OUTCOMES = {'had': 3, 'hhad': 3, 'ttg': 8, 'hafu': 9, 'crs': 31}


def load(fn):
    s = io.open(os.path.join(D, fn), encoding='utf-8-sig').read()
    return json.loads(s)


def main():
    raw = load('20261108_raw.json')
    matches = load('20261108_matches.json')
    report = {'fetched_at': raw.get('fetched_at'), 'upstream_updated_at': raw.get('updatedAt'),
              'match_count_raw': len(raw.get('matches') or []), 'match_count_parsed': len(matches),
              'missing_fields': [], 'missing_pools': [], 'team_issues': [], 'rank_issues': [],
              'table_info': {}, 'single_marked': [m['num'] for m in matches if m.get('betting_single')]}

    # 1) 字段与玩法完整度
    for m in matches:
        for k in ('num', 'league', 'home', 'away', 'time', 'match_date'):
            if not m.get(k):
                report['missing_fields'].append('%s:%s' % (m['num'], k))
        for pool, n in POOL_OUTCOMES.items():
            v = m.get(pool)
            if not v:
                report['missing_pools'].append('%s:无%s' % (m['num'], pool))
            else:
                outs = v['outcomes'] if pool == 'hhad' else v
                if len(outs) != n:
                    report['missing_pools'].append('%s:%s仅%d项' % (m['num'], pool, len(outs)))

    # 2) 队名映射 + 积分榜一致性
    tables = {}
    for lg, fn in TABLE_FILE.items():
        if not os.path.exists(os.path.join(D, fn)):
            report['team_issues'].append('%s:缺少积分榜文件%s' % (lg, fn))
            continue
        t = load(fn)
        tables[lg] = {r['team'].lower(): r for r in t['table']}
        report['table_info'][lg] = {'file': fn, 'season': t.get('season'), 'rows': len(t['table']),
                                    'played': sorted({r['played'] for r in t['table']})}

    for m in matches:
        lg = m['league']
        if lg not in tables:
            report['team_issues'].append('%s:联赛无对应积分榜(%s)' % (m['num'], lg))
            continue
        for side in ('home', 'away'):
            cn = m[side]
            en = TEAM_ALIAS.get(cn)
            if not en:
                report['team_issues'].append('%s:%s无队名映射' % (m['num'], cn))
                continue
            row = tables[lg].get(en.lower())
            if not row:
                report['team_issues'].append('%s:%s(%s)积分榜未找到' % (m['num'], cn, en))
                continue
            rank_field = m.get(side + '_rank') or ''
            digits = ''.join(ch for ch in rank_field if ch.isdigit())
            if digits and int(digits) != int(row['position']):
                report['rank_issues'].append('%s %s:赔率页名次%s vs 积分榜第%s' % (
                    m['num'], cn, rank_field, row['position']))

    # 3) 时间戳
    times = sorted({m['num']: m['time'] for m in matches}.items())
    report['first_kickoff'] = times[0][1] if times else None
    report['last_kickoff'] = times[-1][1] if times else None

    json.dump(report, io.open(os.path.join(D, '20261108_sync_check.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print('抓取时间', report['fetched_at'], '| 上游更新时间', report['upstream_updated_at'])
    print('场次 raw/parsed', report['match_count_raw'], '/', report['match_count_parsed'])
    print('缺失字段', len(report['missing_fields']), report['missing_fields'][:10])
    print('玩法缺失', len(report['missing_pools']), report['missing_pools'][:10])
    print('队名问题', len(report['team_issues']), report['team_issues'][:10])
    print('名次不一致', len(report['rank_issues']), report['rank_issues'][:20])
    print('单关标记', report['single_marked'] or '全部 false（上游未回传单关标记）')
    for lg, v in report['table_info'].items():
        print('榜', lg, v['rows'], '轮次', v['played'])


if __name__ == '__main__':
    main()
