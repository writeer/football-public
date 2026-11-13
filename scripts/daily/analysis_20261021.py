# -*- coding: utf-8 -*-
"""
2026-10-21（周三）竞彩13场 模型计算
AGENTS.md 第3-5步：联赛特征 → 基本面 → 模型

规则口径：
- 规则79：λ 只由基本面（积分榜场均进失球）计算，赔率不参与概率生成，仅做去水对照
- 规则76：跨联赛等级差 —— 低等级方攻击 λ 打折（005/008/009/012）
- 规则80：欧冠联赛阶段基准3.9（前3轮187球/45场=4.16，0.7×4.16+0.3×3.2）
- 规则72：008 维拉公园北看台部分关闭（非处罚）→ 主场加成 ×0.90
- 规则63：单关平局上修（008、010，用户赛前告知；按 L218 上限 +6pp）
- 规则65：实力差距大 → 总进球上修（dt 已写入 ADJ）
- 规则66：欧冠/杯赛不适用半场平局联赛修正，半场 λ 比例 0.45；日职/西甲 0.38
- 规则67：双轨制（k_dist 记录 / k_rec 推荐锚点）
- 规则52a：让球首选 = 无条件净胜球众数
- 规则74：大小球六档
输出：reports/data/20261021_model_output.json
"""
import sys, json, io, os
sys.path.insert(0, r'e:\VibeCoding\football')
import numpy as np
from scipy import stats as sp_stats
from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, OddsCalibrator, HTFTModel)

SRC = 'reports/data/20261021_matches.json'
OUT = 'reports/data/20261021_model_output.json'

# 规则66：日职 ht_draw 0.534、西甲 0.441 → 0.38；日乙/欧冠/解放者杯 → 0.45
HT_RATIO = {'日职': 0.38, '日乙': 0.45, '欧冠': 0.45, '西甲': 0.38, '解放者杯': 0.45}
TIER65 = {'日职': 3, '日乙': 3, '欧冠': 3, '西甲': 2, '解放者杯': 3}

# ---------------- 基本面：各队所属国内联赛积分榜 ----------------
TEAM_TABLE = {
    '东京FC': ('日职', 'table_japan1.json', 'FC Tokyo'),
    '柏太阳神': ('日职', 'table_japan1.json', 'Kashiwa Reysol'),
    '川崎前锋': ('日职', 'table_japan1.json', 'Kawasaki Frontale'),
    '神户胜利': ('日职', 'table_japan1.json', 'Vissel Kobe'),
    '大宫松鼠': ('日乙', 'table_japan2.json', 'Omiya Ardija'),
    '富山胜利': ('日乙', 'table_japan2.json', 'Toyama'),
    '科莫': ('意甲', 'table_italy1.json', 'Como'),
    '曼联': ('英超', 'table_premier.json', 'Manchester Utd'),
    '里尔': ('法甲', 'table_france1.json', 'Lille'),
    '加拉塔萨': ('土超', 'table_turkey1.json', 'Galatasaray'),
    '莱万特': ('西甲', 'table_spain1.json', 'Levante'),
    '毕尔巴鄂': ('西甲', 'table_spain1.json', 'Ath Bilbao'),
    '皇马': ('西甲', 'table_spain1.json', 'Real Madrid'),
    '莱红牛': ('德甲', 'table_germany1.json', 'RB Leipzig'),
    '维拉': ('英超', 'table_premier.json', 'Aston Villa'),
    '维京': ('挪超', 'table_norway.json', 'Viking'),
    '贝蒂斯': ('西甲', 'table_spain1.json', 'Betis'),
    '费耶诺德': ('荷甲', 'table_holland1.json', 'Feyenoord'),
    '拜仁': ('德甲', 'table_germany1.json', 'Bayern Munich'),
    '阿森纳': ('英超', 'table_premier.json', 'Arsenal'),
    '里斯本': ('葡超', 'table_portugal1.json', 'Sporting CP'),
    'LASK林茨': ('奥甲', 'table_austria1.json', 'LASK'),
    '布鲁日': ('比甲', 'table_belgium1.json', 'Club Brugge KV'),
    '朗斯': ('法甲', 'table_france1.json', 'Lens'),
    '帕梅拉斯': ('巴甲', 'table_brazil1.json', 'Palmeiras'),
    '弗鲁米嫩': ('巴甲', 'table_brazil1.json', 'Fluminense'),
}

LEVEL = {'日职': 3, '日乙': 4, '意甲': 1, '英超': 1, '法甲': 1, '土超': 2,
         '西甲': 1, '德甲': 1, '挪超': 3, '荷甲': 2, '葡超': 2, '奥甲': 2,
         '比甲': 2, '巴甲': 2}
# 规则76：跨联赛等级差（低等级方攻击 λ 乘数）
RULE76 = {
    '周三005': dict(side='away', mult=0.95, gap=1, note='土超L2 vs 法甲L1，等级差1档，加拉塔萨雷攻击λ×0.95'),
    '周三008': dict(side='away', mult=0.85, gap=2, note='挪超L3 vs 英超L1，等级差2档（跨级），维京攻击λ×0.85'),
    '周三009': dict(side='away', mult=0.97, gap=1, note='荷甲L2 vs 西甲L1，等级差1档，费耶诺德攻击λ×0.97'),
    '周三012': dict(side='home', mult=0.94, gap=1, note='比甲L2 vs 法甲L1，等级差1档，布鲁日攻击λ×0.94'),
}

# 总控人工修正（第1-2步信息裁决后）：lh/la=攻击λ乘数；dt=规则65大球上修总进球增量
ADJ = {
    '周三001': dict(lh=1.03, la=1.08, dt=0.10, note='FC东京左侧防线结构崩（长友ACL/桥本腓骨骨折/室屋比目鱼肌/本间大腿/瓦利斯ACL），但5连胜5零封；柏马场ACL+熊坂MCL、门将若原脑震荡成疑；柏14天5赛'),
    '周三002': dict(lh=1.00, la=0.88, dt=0.05, note='川崎野田/谷口/绀野缺阵且8连战官方预告轮换；神户中2日连战+10-27亚冠客场，体能劣势最大；神户扇原/佐佐木/富永长期伤号'),
    '周三003': dict(lh=0.97, la=1.08, dt=0.05, note='大宫11轮不败刚被鸟栖终结、J2最多21球、身价2.05倍；富山7轮不败仅差1分（模型初算低估富山攻击，按基本面回调），龟田步梦全治10个月；大宫伤停公告缺失'),
    '周三004': dict(lh=1.05, la=0.92, dt=0.10, note='科莫Diao确认缺阵、Kean/Chalobah成疑；曼联Yoro停赛+Ugarte ACL+Dorgu/Šeško/Shaw缺阵、Martínez/Mainoo/Heaven成疑，5场不胜且英超第13；科莫意甲第5、主场4-1莱比锡'),
    '周三005': dict(lh=0.90, la=0.90, dt=0.05, note='里尔Ueda足底+Tiago Santos ACL+Mbappé停赛+Igamane ACL，锋线只剩吉鲁；加拉Leão内收肌缺阵、Torreira/Singo成疑，5天后费内巴切德比轮换动机强；按回测教训对客队跨联赛数据再压5%'),
    '周三006': dict(lh=0.95, la=0.92, dt=-0.10, note='莱万特Etta Eyong+Sotelo缺阵、5场不胜、主场1胜；毕尔巴鄂Guruzeta ACL赛季报销+Sancet缺阵+Nico Williams成疑，3连0-0、8轮仅7球、22天6赛'),
    '周三007': dict(lh=1.02, la=0.85, dt=0.20, note='皇马Rodrygo ACL+Asencio缺阵、Mendy成疑，但Vinícius欧冠可首发；10-25国家德比轮换动机强；莱比锡Baumgartner/Ouédraogo/Guiu缺阵、客场4连败且刚1-6拜仁'),
    '周三008': dict(lh=1.10, la=0.65, dt=0.55, note='维拉Onana ACL+Ruggeri+Wan-Bissaka缺阵、Maatsen成疑，10-24对曼城轮换；维京Askildsen停赛+Bærtelsen/Bjørshol/D_Agostino/Berisha/Roseth缺阵（两名前锋+后腰+中卫全缺）、1分第27、10-25挪超争冠战；身价差11.3倍→规则65 Tier3上修，按10-20回测教训对≥10倍身价差额外+0.20球'),
    '周三009': dict(lh=1.10, la=0.72, dt=0.15, note='贝蒂斯Cucho（左比目鱼肌）+Firpo+J.Hernández缺阵、Ruibal成疑，但欧冠2连胜；费耶诺德Beelen骨折+Bos+Moder/Nelson等多人缺阵/成疑，欧冠客场1-5巴萨、4天后客战PSV；按10-20回测教训对客队跨联赛数据再压一档（0.97×0.85×0.85）'),
    '周三010': dict(lh=0.94, la=0.92, dt=0.20, note='拜仁Olise停赛（德甲第一身价€180m）+Musiala大腿撕裂+Neuer成疑；阿森纳Saliba背伤至12-11+Hincapié/Tzolis缺阵，Zubimendi复出；拜仁主场对阿森纳近3次全胜'),
    '周三011': dict(lh=1.10, la=0.78, dt=0.30, note='里斯本Zalazar/Debast/Nuno Santos缺阵但休8天、欧冠6分第6、主场；LASK Usor/Harakaté/Smakaj缺阵+Bello成疑、0分第33、刚3-6利物浦'),
    '周三012': dict(lh=1.08, la=0.85, dt=0.10, note='布鲁日5连胜（含客场4-3国米），仅Ordóñez缺阵；朗斯Nawrocki ACL+Sima+Gradit+Aguilar缺阵、Todibo成疑，欧冠客场两战全败；按回测教训对客队跨联赛数据再压3%；低温湿滑+阵风52km/h'),
    '周三013': dict(lh=1.00, la=0.88, dt=-0.05, note='解放者杯半决赛次回合，帕尔梅拉斯首回合客场2-1领先（无客场进球规则），Gómez/Giay/主帅解禁；Vitor Roque脚踝成疑。弗鲁米嫩必须净胜2球，Martinelli成疑+Cano/Alisson体能过渡，马拉卡纳三连败但联赛轮换留力'),
}
SINGLE = {'周三008', '周三010'}   # 规则63：用户赛前告知开单关
# 10-20回测教训：双方合计伤停≥10人时，若次选与平局差距≤3pp，次选强制改平局
DRAW_GUARD = {'周三004'}

# 规则36身价（Transfermarkt，2026-10-20，单位百万欧）
VALUE = {'东京FC': 17.65, '柏太阳神': 18.33, '川崎前锋': 20.55, '神户胜利': 17.35,
         '大宫松鼠': 11.20, '富山胜利': 5.45, '科莫': 568.15, '曼联': 928.80,
         '里尔': 253.30, '加拉塔萨': 411.60, '莱万特': 87.50, '毕尔巴鄂': 229.80,
         '皇马': 1500.0, '莱红牛': 514.95, '维拉': 633.70, '维京': 56.00,
         '贝蒂斯': 258.10, '费耶诺德': 245.23, '拜仁': 1040.0, '阿森纳': 1380.0,
         '里斯本': 413.70, 'LASK林茨': 62.40, '布鲁日': 238.20, '朗斯': 243.00,
         '帕梅拉斯': 218.58, '弗鲁米嫩': 121.13}
# 跨联赛身价先验指数：gap≥2→0.18；gap=1→0.12；gap=0→0.06；同联赛不启用
VALUE_EXP = {'周三004': 0.06, '周三005': 0.12, '周三007': 0.06, '周三008': 0.18,
             '周三009': 0.12, '周三010': 0.06, '周三011': 0.06, '周三012': 0.12}

HAD_ORDER = ['home', 'draw', 'away']
NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}

SHRINK_K = 6.0
# 欧冠当季基准（规则80：前3轮187球/45场=4.16，0.7×4.16+0.3×3.2=3.87，取3.9）
LEAGUE_PROFILE = {'日职': dict(base=2.52, home=1.25), '日乙': dict(base=2.49, home=1.22),
                  '欧冠': dict(base=3.90, home=1.25), '西甲': dict(base=2.48, home=1.16),
                  '解放者杯': dict(base=1.78, home=1.35)}
# 规则：联赛平局率>28% → 平局上修
DRAW_UP = {'西甲': 0.03, '解放者杯': 0.02}

_TABLE_CACHE = {}


def load_table(fn):
    if fn is None:
        return None
    if fn in _TABLE_CACHE:
        return _TABLE_CACHE[fn]
    path = os.path.join('reports/data', fn)
    rows = json.load(io.open(path, encoding='utf-8-sig')).get('table') if os.path.exists(path) else None
    _TABLE_CACHE[fn] = rows
    return rows


def league_avg(rows):
    goals = games = 0
    for r in rows or []:
        p = r.get('played') or 0
        if p <= 0:
            continue
        goals += r.get('goals_for') or 0
        games += p
    return 2.0 * goals / games if games else None


def strength(row, per_side):
    played = row.get('played') or 0
    scored = row.get('avg_goals_scored') or 0.0
    conceded = row.get('avg_goals_conceded') or 0.0
    w = played / (played + SHRINK_K) if played > 0 else 0.0
    atk = 1.0 + (scored / per_side - 1.0) * w
    dfn = 1.0 + (conceded / per_side - 1.0) * w
    return max(atk, 0.30), max(dfn, 0.30)


def get_row(name):
    key, fn, en = TEAM_TABLE[name]
    rows = load_table(fn)
    if rows is None:
        return None, key, None, True
    for r in rows:
        if r.get('team', '').lower() == en.lower():
            return r, key, league_avg(rows), False
    for r in rows:
        if en.lower() in r.get('team', '').lower():
            return r, key, league_avg(rows), False
    return None, key, league_avg(rows), True


def de_vig(odds):
    inv = {k: 1.0 / v for k, v in odds.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}


def had_from_crs(crs):
    h = d = a = 0.0
    for o in crs:
        k = str(o.get('key', ''))
        if ':' not in k:
            continue
        i, j = [int(t) for t in k.split(':')]
        p = o.get('noVig') or 0
        if i > j:
            h += p
        elif i == j:
            d += p
        else:
            a += p
    t = h + d + a
    return {'home': h / t, 'draw': d / t, 'away': a / t}


def tier_of(p01, p23, p45, p6, top1, top2b):
    if top1 >= 6:
        return '穿盘可能(6-7+球)'
    if top1 == 5:
        return '超大球(5-6球)'
    if top1 == 4:
        return '大球(4-5球)'
    if top1 == 3:
        return '常规正常球(2-3球)'
    if top1 == 2:
        return '常规正常球(2-3球)' if p23 >= 0.40 else '小球(1-2球)'
    if p01 >= 0.40:
        return '闷战超小球(0-1球)'
    return '小球(1-2球)'


def analyze(m):
    num, league = m['num'], m['league']
    # 市场概率仅作对照（规则79）
    if m.get('had'):
        odds = {o['key']: o['odds'] for o in m['had']}
        market = de_vig(odds)
        shin = OddsCalibrator(odds['home'], odds['draw'], odds['away']).shin()
        shin_probs = [shin['home'], shin['draw'], shin['away']]
        src = 'HAD去水'
    else:
        market = had_from_crs(m['crs'])
        shin_probs = [market['home'], market['draw'], market['away']]
        src = 'CRS聚合(无HAD盘)'

    prof = LEAGUE_PROFILE[league]
    base = prof['base']
    H = prof['home']
    if num == '周三008':
        H *= 0.90   # 规则72：北看台部分关闭（非处罚），主场加成下调10%

    hrow, hlg, havg, hmiss = get_row(m['home'])
    arow, alg, aavg, amiss = get_row(m['away'])
    missing = []
    if hmiss:
        missing.append(m['home'])
    if amiss:
        missing.append(m['away'])
    if hrow is None:
        hrow = dict(team=m['home'] + '(无榜数据)', played=0,
                    avg_goals_scored=base / 2, avg_goals_conceded=base / 2)
        havg = base
    if arow is None:
        arow = dict(team=m['away'] + '(无榜数据)', played=0,
                    avg_goals_scored=base / 2, avg_goals_conceded=base / 2)
        aavg = base

    atk_h, def_h = strength(hrow, havg / 2.0)
    atk_a, def_a = strength(arow, aavg / 2.0)

    r76 = RULE76.get(num)
    if r76:
        if r76['side'] == 'away':
            atk_a *= r76['mult']
        else:
            atk_h *= r76['mult']

    share_h = H / (1.0 + H)
    lh = base * share_h * atk_h * def_a
    la = base * (1.0 - share_h) * atk_a * def_h

    # 跨联赛身价先验（规则36）
    v_exp = VALUE_EXP.get(num)
    value_mult = None
    if v_exp:
        ratio = VALUE[m['home']] / VALUE[m['away']]
        mh = min(max(ratio ** v_exp, 0.55), 1.55)
        lh *= mh
        la *= 1.0 / mh
        value_mult = round(mh, 3)

    adj = ADJ[num]
    lh *= adj['lh']
    la *= adj['la']
    if adj['dt']:
        tot = lh + la
        lh += adj['dt'] * lh / tot
        la += adj['dt'] * la / tot
    lh = min(max(lh, 0.25), 4.5)
    la = min(max(la, 0.25), 4.5)

    dc = DixonColesModel(); nb = NegativeBinomialModel(); zp = ZIPModel(); sk = SkellamModel()
    mc = MonteCarloSimulator(n_sim=20000)
    dc_p = dc.outcome_probs(lh, la); nb_p = nb.outcome_probs(lh, la)
    zip_p = zp.outcome_probs(lh, la); skp = sk.outcome_probs(lh, la)
    mcr = mc.simulate(lh, la)
    mc_p = {'home': mcr['home_win'], 'draw': mcr['draw'], 'away': mcr['away_win']}
    W = {'dc': 0.34, 'nb': 0.22, 'zip': 0.13, 'sk': 0.14, 'mc': 0.17}
    fused = {}
    for k in HAD_ORDER:
        fused[k] = (W['dc'] * dc_p[k] + W['nb'] * nb_p[k] + W['zip'] * zip_p[k]
                    + W['sk'] * skp[k] + W['mc'] * mc_p[k])
    for k in HAD_ORDER:
        fused[k] = max(fused[k], 0.01)
    s = sum(fused.values())
    fused = {k: v / s for k, v in fused.items()}

    # 联赛平局率>28%上修（西甲/解放者杯）
    draw_note = ''
    if league in DRAW_UP:
        add = DRAW_UP[league]
        nd = fused['home'] + fused['away']
        fused['draw'] += add
        fused['home'] -= add * fused['home'] / nd
        fused['away'] -= add * fused['away'] / nd
        s = sum(fused.values()); fused = {k: v / s for k, v in fused.items()}
        draw_note = '联赛平局上修+%.0fpp' % (add * 100)

    # 规则63 单关平局上修（L218：上限+6pp）
    single_note = ''
    if num in SINGLE:
        sf0 = sorted(fused.items(), key=lambda x: -x[1])
        gap = (sf0[0][1] - fused['draw']) * 100
        add = 0.06 if gap <= 10 else (0.05 if gap <= 20 else 0.04)
        old = fused['draw']; new = min(old + add, 0.55); add = new - old
        nd = fused['home'] + fused['away']
        fused['draw'] = new
        if nd > 0:
            fused['home'] -= add * fused['home'] / nd
            fused['away'] -= add * fused['away'] / nd
        s = sum(fused.values())
        fused = {k: v / s for k, v in fused.items()}
        single_note = '单关平局上修+%.1fpp（首选-平差距%.1fpp）' % (add * 100, gap)

    sf = sorted(fused.items(), key=lambda x: -x[1])
    primary, secondary = sf[0][0], sf[1][0]
    if num in DRAW_GUARD and secondary != 'draw' and (fused[secondary] - fused['draw']) <= 0.03:
        secondary = 'draw'

    n = 17 if (lh + la) > 3.4 else 14
    dc.max_goals = n
    matrix = dc.compute_matrix(lh, la)
    tg, gd = {}, {}
    for i in range(n):
        for j in range(n):
            tg[i + j] = tg.get(i + j, 0.0) + matrix[i, j]
            gd[i - j] = gd.get(i - j, 0.0) + matrix[i, j]
    k_dist = max(gd.items(), key=lambda x: x[1])
    if primary == 'home':
        cand = {k: v for k, v in gd.items() if k >= 1}
    elif primary == 'away':
        cand = {k: v for k, v in gd.items() if k <= -1}
    else:
        cand = {k: v for k, v in gd.items() if k == 0}
    k_rec = max(cand.items(), key=lambda x: x[1])
    consistent = ((primary == 'home' and k_dist[0] >= 1) or (primary == 'away' and k_dist[0] <= -1)
                  or (primary == 'draw' and k_dist[0] == 0))
    kr = k_rec[0]
    band = sorted([(i, i - kr, matrix[i, i - kr]) for i in range(n)
                   if 0 <= i - kr < n], key=lambda x: -x[2])

    gl = (m.get('hhad') or {}).get('goalLine')
    hh_model = hh_market = hh_odds = None
    hc_first = hc_second = ''
    if m.get('hhad'):
        th = -gl
        hh_model = {'home': float(sp_stats.skellam.sf(th, lh, la)),
                    'draw': float(sp_stats.skellam.pmf(th, lh, la)),
                    'away': float(sp_stats.skellam.cdf(th - 1, lh, la))}
        hh_odds = {o['key']: o['odds'] for o in m['hhad']['outcomes']}
        hh_market = {o['key']: (o['noVig'] or 0) for o in m['hhad']['outcomes']}
        kd = k_dist[0]
        adj_net = kd + gl
        hc_first = 'home' if adj_net > 0 else ('draw' if adj_net == 0 else 'away')
        hh_draw_prob = gd.get(-gl, 0.0)
        combo = {k: 0.5 * hh_model[k] + 0.5 * hh_market[k] for k in HAD_ORDER}
        rest = sorted([k for k in HAD_ORDER if k != hc_first], key=lambda k: -combo[k])
        hc_second = rest[0]
        if hh_draw_prob >= 0.20 and 'draw' not in (hc_first, hc_second):
            hc_second = 'draw'  # L216 硬校验
        if abs(gl) >= 2:
            rest_model = sorted([k for k in HAD_ORDER if k != hc_first], key=lambda k: -hh_model[k])
            hc_second = rest_model[0]

    hr = HT_RATIO[league]
    htft = HTFTModel(dc); htft.ht_ratio = hr
    ht_res = htft.predict(lh, la)
    htft_cn = [(HAFU_CN.get(r['code'].replace('/', ''), r['htft']), r['probability']) for r in ht_res]
    mat_ht = dc.compute_matrix(lh * hr, la * hr)
    ht_scores = sorted([(i, j, mat_ht[i, j]) for i in range(4) for j in range(4)], key=lambda x: -x[2])[:4]

    p01 = sum(v for k, v in tg.items() if k <= 1)
    p23 = sum(v for k, v in tg.items() if k in (2, 3))
    p45 = sum(v for k, v in tg.items() if k in (4, 5))
    p6 = sum(v for k, v in tg.items() if k >= 6)

    ttg_top = sorted(tg.items(), key=lambda x: -x[1])[:6]
    top2 = [ttg_top[0][0], ttg_top[1][0]]
    if p01 >= 0.25 and not any(k <= 1 for k in top2):
        alt = max([(k, v) for k, v in tg.items() if k <= 1], key=lambda x: x[1])
        top2 = [top2[0], alt[0]]
    if p6 >= 0.25 and not any(k >= 5 for k in top2):
        alt = max([(k, v) for k, v in tg.items() if k >= 5], key=lambda x: x[1])
        top2 = [top2[0], alt[0]]
    top2 = sorted(set(top2), key=lambda k: -tg[k])[:2]
    tier = tier_of(p01, p23, p45, p6, top2[0], top2[-1])

    ttg_odds = {o['key']: o['odds'] for o in m.get('ttg', [])}
    hafu_odds = {o['key']: o['odds'] for o in m.get('hafu', [])}
    crs_odds = {o['key']: o['odds'] for o in m.get('crs', [])}

    top_scores = sorted([(i, j, matrix[i, j]) for i in range(n) for j in range(n)], key=lambda x: -x[2])[:8]
    ht3 = htft_cn[:3]

    return {
        'num': num, 'league': league, 'home': m['home'], 'away': m['away'],
        'home_rank': m.get('home_rank'), 'away_rank': m.get('away_rank'), 'time': m.get('time'),
        'is_single': num in SINGLE, 'had_source': src,
        'odds_had': ({o['key']: o['odds'] for o in m['had']} if m.get('had') else None),
        'odds_hhad': hh_odds, 'hhad_line': gl, 'odds_ttg': ttg_odds, 'odds_hafu': hafu_odds,
        'odds_crs': crs_odds, 'crs_raw': m.get('crs'),
        'market': {k: round(v, 4) for k, v in market.items()},
        'shin': [round(p, 4) for p in shin_probs],
        'lambda_home': round(lh, 3), 'lambda_away': round(la, 3), 'lambda_total': round(lh + la, 3),
        'lambda_source': 'fundamental(rule79)',
        'base_league_avg': round(base, 3), 'home_adv': round(H, 3),
        'own_league_home': hlg, 'own_league_away': alg,
        'atk_home': round(atk_h, 3), 'def_home': round(def_h, 3),
        'atk_away': round(atk_a, 3), 'def_away': round(def_a, 3),
        'table_missing': missing, 'rule76': r76, 'value_mult': value_mult,
        'adj_note': adj['note'], 'dc': {k: round(v, 4) for k, v in dc_p.items()},
        'nb': {k: round(v, 4) for k, v in nb_p.items()},
        'mc': {k: round(v, 4) for k, v in mc_p.items()},
        'fused': {k: round(v, 4) for k, v in fused.items()},
        'primary': primary, 'secondary': secondary,
        'primary_prob': round(sf[0][1], 4), 'secondary_prob': round(fused[secondary], 4),
        'third': sf[2][0], 'third_prob': round(sf[2][1], 4),
        'draw_note': draw_note, 'single_note': single_note,
        'hhad_model': {k: round(v, 4) for k, v in hh_model.items()} if hh_model else None,
        'hhad_market': {k: round(v, 4) for k, v in hh_market.items()} if hh_market else None,
        'hhad_draw_prob': round(gd.get(-gl, 0.0), 4) if gl is not None else None,
        'hc_first': hc_first, 'hc_second': hc_second,
        'k_dist': k_dist[0], 'k_dist_prob': round(k_dist[1], 4),
        'k_rec': k_rec[0], 'k_rec_prob': round(k_rec[1], 4), 'k_consistent': bool(consistent),
        'band': [(a, b, round(p, 4)) for a, b, p in band[:5]],
        'top_scores': [(a, b, round(p, 4)) for a, b, p in top_scores],
        'tg': {str(k): round(v, 4) for k, v in sorted(tg.items()) if v > 0.0005},
        'ttg_top': [(k, round(v, 4)) for k, v in ttg_top],
        'ttg_top2': top2,
        'p01': round(p01, 4), 'p23': round(p23, 4), 'p45': round(p45, 4), 'p6': round(p6, 4),
        'tier': tier, 'rule65_tier': TIER65[league], 'dt': adj['dt'],
        'htft': [(k, round(v, 4)) for k, v in htft_cn[:9]],
        'htft_top3': [(k, round(v, 4)) for k, v in ht3],
        'ht_scores': [(a, b, round(p, 4)) for a, b, p in ht_scores],
        'ht_ratio': hr,
    }


def main():
    ms = json.load(io.open(SRC, encoding='utf-8'))
    res = [analyze(m) for m in ms]
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    json.dump(res, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    lines = []
    for r in res:
        lines.append('%s %s vs %s [%s] 单关=%s λ%.2f/%.2f(总%.2f) 基准%.2f H%.2f %s' % (
            r['num'], r['home'], r['away'], r['league'], r['is_single'],
            r['lambda_home'], r['lambda_away'], r['lambda_total'], r['base_league_avg'], r['home_adv'], r['had_source']))
        lines.append('   融合 主%.1f/平%.1f/客%.1f → 首选%s(%.1f) 次选%s(%.1f) %s %s' % (
            r['fused']['home'] * 100, r['fused']['draw'] * 100, r['fused']['away'] * 100,
            NAME_CN[r['primary']], r['primary_prob'] * 100, NAME_CN[r['secondary']], r['secondary_prob'] * 100,
            r['draw_note'], r['single_note']))
        lines.append('   让(%s) 首选%s 次选%s｜模型%s 市场%s 让平%.1f%%' % (
            r['hhad_line'], r['hc_first'], r['hc_second'], r['hhad_model'], r['hhad_market'],
            (r['hhad_draw_prob'] or 0) * 100))
        lines.append('   k_dist=%+d(%.1f%%) k_rec=%+d(%.1f%%) %s 带内=%s' % (
            r['k_dist'], r['k_dist_prob'] * 100, r['k_rec'], r['k_rec_prob'] * 100,
            '一致' if r['k_consistent'] else '分歧',
            [('%d-%d' % (a, b), round(p * 100, 1)) for a, b, p in r['band'][:3]]))
        lines.append('   TTG %s | 0-1球%.0f%% 2-3球%.0f%% 4-5球%.0f%% 6+球%.0f%% | %s' % (
            r['ttg_top2'], r['p01'] * 100, r['p23'] * 100, r['p45'] * 100, r['p6'] * 100, r['tier']))
        lines.append('   半全场 %s | 半场比分 %s' % (
            [(k, round(v * 100, 1)) for k, v in r['htft_top3']],
            [('%d-%d' % (a, b), round(p * 100, 1)) for a, b, p in r['ht_scores'][:3]]))
        lines.append('   比分TOP5 %s' % [('%d-%d' % (a, b), round(p * 100, 1)) for a, b, p in r['top_scores'][:5]])
    io.open('reports/data/20261021_model_log.txt', 'w', encoding='utf-8').write('\n'.join(lines))
    print('\n'.join(lines))
    print('saved', out)


if __name__ == '__main__':
    main()
