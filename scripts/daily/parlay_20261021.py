# -*- coding: utf-8 -*-
"""2026-10-21（周三）串关方案计算：方向串/让球串/混合串 + 娱乐串18方案"""
import io, json, sys
sys.path.insert(0, r'e:\VibeCoding\football')
sys.stdout.reconfigure(encoding='utf-8')
from lottery_agent.models import DixonColesModel

SRC = 'reports/data/20261021_model_output.json'
OUT = 'reports/data/20261021_parlay.json'
RS = {r['num']: r for r in json.load(io.open(SRC, encoding='utf-8'))}

HAFU_CN = {'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD',
           '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA'}


def crs_prob(r, score):
    i, j = [int(x) for x in score.split('-')]
    dc = DixonColesModel()
    lh, la = r['lambda_home'], r['lambda_away']
    dc.max_goals = 17 if lh + la > 3.4 else 14
    m = dc.compute_matrix(lh, la)
    return float(m[i, j])


def leg(r, market, pick):
    if market == 'had':
        return r['odds_had'][pick], r['fused'][pick]
    if market == 'hhad':
        return r['odds_hhad'][pick], r['hhad_model'][pick]
    if market == 'ttg':
        key = str(pick)
        return r['odds_ttg'][key], r['tg'][key]
    if market == 'hafu':
        code = HAFU_CN[pick]
        p = dict(r['htft']).get(pick, 0)
        return r['odds_hafu'][code], p
    if market == 'crs':
        return r['odds_crs'][pick.replace('-', ':')], crs_prob(r, pick)
    raise ValueError(market)


SCHEMES = [
    # 串关思路：方向串
    dict(name='方向串A', cat='方向串', legs=[('周三007', 'had', 'home', '皇马主胜'),
                                          ('周三013', 'had', 'home', '帕尔梅拉斯主胜')]),
    dict(name='方向串B', cat='方向串', legs=[('周三010', 'had', 'home', '拜仁主胜'),
                                          ('周三009', 'had', 'home', '贝蒂斯主胜'),
                                          ('周三005', 'had', 'home', '里尔主胜')]),
    # 让球串
    dict(name='稳健让球串', cat='让球串', legs=[('周三008', 'hhad', 'away', '维拉让(-2)负'),
                                            ('周三013', 'hhad', 'away', '帕尔梅拉斯让(-1)负')]),
    dict(name='价值让球串', cat='让球串', legs=[('周三004', 'hhad', 'away', '科莫让(-1)负'),
                                            ('周三009', 'hhad', 'away', '贝蒂斯让(-1)负')]),
    # 混合串（串关思路）
    dict(name='半全场串A', cat='混合串', legs=[('周三010', 'hafu', '胜胜', '拜仁胜胜'),
                                            ('周三004', 'hafu', '平胜', '科莫平胜'),
                                            ('周三011', 'hafu', '胜胜', '里斯本胜胜')]),
    dict(name='半全场串B', cat='混合串', legs=[('周三008', 'hafu', '胜胜', '维拉胜胜'),
                                            ('周三003', 'hafu', '平胜', '大宫平胜'),
                                            ('周三004', 'hafu', '胜胜', '科莫胜胜')]),
    dict(name='方向+半全场A', cat='混合串', legs=[('周三002', 'had', 'home', '川崎主胜'),
                                               ('周三003', 'hafu', '平胜', '大宫平胜')]),
    dict(name='方向+半全场B', cat='混合串', legs=[('周三005', 'had', 'home', '里尔主胜'),
                                               ('周三009', 'hafu', '胜胜', '贝蒂斯胜胜')]),
    dict(name='连续编号混合串A', cat='混合串', legs=[('周三006', 'hafu', '平平', '莱万特平平'),
                                                 ('周三007', 'hafu', '胜胜', '皇马胜胜')]),
    dict(name='连续编号混合串B', cat='混合串', legs=[('周三012', 'hafu', '胜胜', '布鲁日胜胜'),
                                                 ('周三013', 'hafu', '平平', '帕尔梅拉斯平平')]),
    # 娱乐串：高赔总进球
    dict(name='总进球串A', cat='高赔总进球串', legs=[('周三007', 'ttg', 4, '皇马4球'),
                                                  ('周三003', 'ttg', 2, '大宫2球'),
                                                  ('周三005', 'ttg', 3, '里尔3球')]),
    dict(name='总进球串B', cat='高赔总进球串', legs=[('周三011', 'ttg', 5, '里斯本5球'),
                                                  ('周三002', 'ttg', 2, '川崎2球'),
                                                  ('周三008', 'ttg', 4, '维拉4球')]),
    dict(name='连续编号总进球串①', cat='高赔总进球串', legs=[('周三006', 'ttg', 2, '莱万特2球'),
                                                         ('周三007', 'ttg', 4, '皇马4球')]),
    dict(name='连续编号总进球串②', cat='高赔总进球串', legs=[('周三010', 'ttg', 4, '拜仁4球'),
                                                         ('周三011', 'ttg', 5, '里斯本5球')]),
    # 高赔半全场
    dict(name='高赔半全场串A', cat='高赔半全场串', legs=[('周三010', 'hafu', '胜胜', '拜仁胜胜'),
                                                     ('周三009', 'hafu', '胜胜', '贝蒂斯胜胜'),
                                                     ('周三005', 'hafu', '胜胜', '里尔胜胜')]),
    dict(name='高赔半全场串B', cat='高赔半全场串', legs=[('周三012', 'hafu', '胜胜', '布鲁日胜胜'),
                                                     ('周三006', 'hafu', '平平', '莱万特平平'),
                                                     ('周三001', 'hafu', '平胜', 'FC东京平胜')]),
    dict(name='连续编号高赔半全场串①', cat='高赔半全场串', legs=[('周三010', 'hafu', '胜胜', '拜仁胜胜'),
                                                             ('周三011', 'hafu', '平胜', '里斯本平胜')]),
    dict(name='连续编号高赔半全场串②', cat='高赔半全场串', legs=[('周三003', 'hafu', '平胜', '大宫平胜'),
                                                             ('周三004', 'hafu', '胜胜', '科莫胜胜')]),
    # 半全场混合总进球
    dict(name='混合串A', cat='半全场混合总进球串', legs=[('周三007', 'hafu', '胜胜', '皇马胜胜'),
                                                     ('周三005', 'ttg', 3, '里尔3球')]),
    dict(name='混合串B', cat='半全场混合总进球串', legs=[('周三013', 'hafu', '平平', '帕尔梅拉斯平平'),
                                                     ('周三012', 'ttg', 4, '布鲁日4球')]),
    dict(name='连续编号混合总进球串①', cat='半全场混合总进球串', legs=[('周三010', 'hafu', '平胜', '拜仁平胜'),
                                                                ('周三011', 'ttg', 5, '里斯本5球')]),
    dict(name='连续编号混合总进球串②', cat='半全场混合总进球串', legs=[('周三008', 'hafu', '胜胜', '维拉胜胜'),
                                                                ('周三009', 'ttg', 4, '费耶诺德4球')]),
    # 比分串
    dict(name='稳健比分串', cat='比分串', legs=[('周三006', 'crs', '0-0', '莱万特0-0'),
                                             ('周三012', 'crs', '3-1', '布鲁日3-1')]),
    dict(name='搏冷比分串（反向推理）', cat='比分串', legs=[('周三001', 'crs', '0-2', '柏太阳神客胜0-2'),
                                                     ('周三013', 'crs', '0-2', '弗鲁米嫩客胜0-2')],
         note='冷门剧本：001柏太阳神0平局高波动+FC东京左侧防线残→客队反击打穿；013弗鲁米嫩必须净胜2球+联赛轮换留力→客场搏命'),
    dict(name='连续编号比分串①', cat='比分串', legs=[('周三006', 'crs', '0-0', '莱万特0-0'),
                                                 ('周三007', 'crs', '3-1', '皇马3-1')]),
    dict(name='连续编号比分串②', cat='比分串', legs=[('周三011', 'crs', '3-1', '里斯本3-1'),
                                                 ('周三012', 'crs', '3-1', '布鲁日3-1')]),
    dict(name='单挑比分①', cat='单挑比分', legs=[('周三012', 'crs', '3-1', '布鲁日3-1')]),
    dict(name='单挑比分②', cat='单挑比分', legs=[('周三006', 'crs', '0-0', '莱万特0-0')]),
]

out = []
count = {}
for s in SCHEMES:
    odds = 1.0
    prob = 1.0
    legs = []
    for num, market, pick, label in s['legs']:
        o, p = leg(RS[num], market, pick)
        odds *= o
        prob *= p
        legs.append(dict(num=num, market=market, pick=pick, label=label,
                         odds=round(o, 2), prob=round(p, 4)))
        count[num] = count.get(num, 0) + 1
    out.append(dict(name=s['name'], cat=s['cat'], legs=legs,
                    odds=round(odds, 2), prob=round(prob, 5), note=s.get('note', '')))

json.dump(out, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for x in out:
    print('%-22s %-12s %6.2f倍  联合%6.2f%%  %s' % (
        x['name'], x['cat'], x['odds'], x['prob'] * 100,
        ' × '.join('%s%s@%.2f' % (l['num'][-3:], l['label'], l['odds']) for l in x['legs'])))
print('\n单场牵连数：', dict(sorted(count.items())))
print('最大牵连：', max(count.items(), key=lambda kv: kv[1]))
