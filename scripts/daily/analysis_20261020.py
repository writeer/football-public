# -*- coding: utf-8 -*-
"""
2026-10-20（周二）竞彩10场 模型计算
AGENTS.md 第3-5步：联赛特征 → 基本面 → 模型

规则口径：
- 规则79：λ 只由基本面（积分榜场均进失球）计算，赔率不参与概率生成，仅做去水对照
- 规则76：跨联赛等级差 —— 低等级方攻击 λ 打折（001/002/004/005/008）
- 规则63：单关平局上修（006、007，用户赛前告知）
- 规则65：实力差距大 → 总进球上修（dt 已写入 ADJ）
- 规则66：欧冠/杯赛不适用半场平局联赛修正，半场 λ 比例 0.45（英冠 003 用 0.425）
- 规则67：双轨制（k_dist 记录 / k_rec 推荐锚点）
- 规则52a：让球首选 = 无条件净胜球众数
- 规则74：大小球六档
输出：reports/data/20261020_model_output.json
"""
import sys, json, io, os
sys.path.insert(0, r'e:\VibeCoding\football')
import numpy as np
from scipy import stats as sp_stats
from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, OddsCalibrator, HTFTModel)

SRC = 'reports/data/20261020_matches.json'
OUT = 'reports/data/20261020_model_output.json'

# 规则66：欧冠/杯赛不适用联赛半场平局修正 → 0.45；英冠 ht_draw_rate=0.425 → 0.42
HT_RATIO = {'欧冠': 0.45, '英冠': 0.42}
TIER65 = {'欧冠': 3, '英冠': 3}   # 规则65：欧战/次级联赛按 Tier3 处理

# ---------------- 基本面：各队所属国内联赛积分榜 ----------------
# (俱乐部中文名 → (联赛键, 积分榜文件, 榜内英文名))
TEAM_TABLE = {
    '费内巴切': ('土超', 'table_turkey1.json', 'Fenerbahce'),
    '斯拉维亚': ('捷甲', 'table_czech1.json', 'Slavia Prague'),
    '萨巴赫': ('阿塞拜疆', 'table_azer.json', 'Sabah Baku'),
    '多特蒙德': ('德甲', 'table_germany1.json', 'Dortmund'),
    '伍尔弗': ('英冠', 'table_championship.json', 'Wolves'),
    '朴次茅斯': ('英冠', 'table_championship.json', 'Portsmouth'),
    '那不勒斯': ('意甲', 'table_italy1.json', 'Napoli'),
    '博德闪耀': ('挪超', 'table_norway.json', 'Bodo/Glimt'),
    '罗马': ('意甲', 'table_italy1.json', 'AS Roma'),
    '布拉迪斯': ('斯洛伐克超', None, 'Slovan Bratislava'),   # 无积分榜源 → 信息缺失
    '巴黎圣曼': ('法甲', 'table_france1.json', 'PSG'),
    '巴萨': ('西甲', 'table_spain1.json', 'Barcelona'),
    '利物浦': ('英超', 'table_premier.json', 'Liverpool'),
    '比利亚雷': ('西甲', 'table_spain1.json', 'Villarreal'),
    '曼城': ('英超', 'table_premier.json', 'Manchester City'),
    '雅典AEK': ('希腊超', 'table_greece1.json', 'AEK Athens'),
    '斯图加特': ('德甲', 'table_germany1.json', 'Stuttgart'),
    '马竞': ('西甲', 'table_spain1.json', 'Atletico Madrid'),
    '波尔图': ('葡超', 'table_portugal1.json', 'FC Porto'),
    '埃因霍温': ('荷甲', 'table_holland1.json', 'PSV'),
}

# 规则76：跨联赛等级差（L1英超/西甲/意甲/德甲/法甲，L2荷甲/葡超/土超，L3挪超/希腊超/捷甲?，L4阿塞拜疆/斯洛伐克/英冠）
# 注：捷甲按 L3 边缘处理，取等级差 1 档 → 轻度打折
LEVEL = {'土超': 2, '捷甲': 3, '阿塞拜疆': 4, '德甲': 1, '英冠': 4, '意甲': 1, '挪超': 3,
         '斯洛伐克超': 4, '法甲': 1, '西甲': 1, '英超': 1, '希腊超': 3, '葡超': 2, '荷甲': 2}
RULE76 = {   # 低等级方攻击 λ 乘数（≥1档 ×0.90-0.95；≥2档 再×0.90；累计下限 ×0.85）
    '周二001': dict(side='away', mult=0.93, gap=1, note='捷甲L3 vs 土超L2，等级差1档，斯拉维亚攻击λ×0.93'),
    '周二002': dict(side='home', mult=0.85, gap=3, note='阿塞拜疆L4 vs 德甲L1，等级差3档（跨级），萨巴赫攻击λ×0.85'),
    '周二004': dict(side='away', mult=0.85, gap=2, note='挪超L3 vs 意甲L1，等级差2档（跨级），博德闪耀攻击λ×0.85'),
    '周二005': dict(side='away', mult=0.85, gap=3, note='斯洛伐克L4 vs 意甲L1，等级差3档（跨级），斯拉万攻击λ×0.85'),
    '周二008': dict(side='away', mult=0.85, gap=2, note='希腊超L3 vs 英超L1，等级差2档（跨级），AEK攻击λ×0.85'),
}

# 总控人工修正（第1-2步信息裁决后）：lh/la=攻击λ乘数；dt=规则65大球上修总进球增量
ADJ = {
    '周二001': dict(lh=0.97, la=1.00, dt=0.10, note='费内巴切4人缺阵（阿森西奥/米尔迪尔/奥斯特沃尔德/迪乌夫），其中阿森西奥为组织核心；斯拉维亚7人缺阵含3名后卫，防线残缺；斯拉维亚7天3赛'),
    '周二002': dict(lh=0.95, la=1.00, dt=0.30, note='萨巴赫0人缺阵但"主场"为6.9万座巴库奥林匹克（非惯用1.3万小场）；多特仅卡雷察斯伤缺（另3人未报名），客场5小时飞行+三线作战；身价差30.9倍→规则65 Tier3上修'),
    '周二003': dict(lh=1.12, la=0.82, dt=0.20, note='朴次茅斯10人确认缺阵（锋线5人+2中卫+左后卫）+毕晓普成疑，锋线真空；狼队希门尼斯长伤、阿姆斯特朗成疑且主帅暗示轮换；身价差6倍→规则65 Tier3上修'),
    '周二004': dict(lh=0.90, la=0.95, dt=0.10, note='那不勒斯5人缺阵（内雷斯/阿利松·桑托斯/维尔加拉/布翁乔尔诺/法瓦苏利），两翼+中卫受损；博德闪耀4人缺阵但比约尔图夫解禁，近4连胜、10-14主场1-0胜多特'),
    '周二005': dict(lh=0.95, la=0.95, dt=0.35, note='罗马4人缺阵（斯维拉尔/科内/克里斯坦特/迪巴拉），二门戈利尼首发、佩莱格里尼顶替迪巴拉；斯拉万2人缺阵（什波拉尔/切雷普卡）、仅休2天+长途飞行、欧冠1进9失；身价差12.9倍→规则65 Tier3上修'),
    '周二006': dict(lh=1.05, la=1.00, dt=0.15, note='PSG门德斯（左大腿）缺阵、左路对位亚马尔真空；巴萨孔德/埃里克·加西亚/克里斯滕森/巴尔德吉缺阵（2中卫+右后卫），德容回归；双方进攻核心健康，历史交锋场均3.8球'),
    '周二007': dict(lh=0.94, la=0.93, dt=0.10, note='利物浦5人缺阵（弗林蓬/索博斯洛伊/布拉德利/莱奥尼/埃基蒂克）右路与锋线减员，奇耶萨/远藤未报名；黄潜佩佩缺阵、布坎南成疑；利物浦Anfield对黄潜2战全胜零封'),
    '周二008': dict(lh=0.96, la=0.98, dt=0.30, note='曼城塞梅尼奥伤缺8周，哈兰德/科瓦契奇/努内斯/奥赖利赛前评估、轮换动机强（10-24维拉、10-27杯赛）；AEK仅替补门将缺阵、上周末联赛延期获整周备战；身价差17.4倍→规则65 Tier3上修'),
    '周二009': dict(lh=0.97, la=0.97, dt=0.10, note='斯图加特3人确认缺阵（扎加杜/蒂亚戈·托马斯/迪尔），米特尔施泰特回归，6天3赛；马竞罗梅罗/科克缺阵、卡多索回归；双方均无历史正式交锋'),
    '周二010': dict(lh=1.08, la=0.80, dt=0.20, note='PSV伤兵9人（三名中锋佩皮/拉默斯/普莱亚全缺+范博梅尔/瓦纳/绍滕/西尔迪利亚/纳加洛/瓦伊萨），蒂尔成疑，锋线真空；波尔图仅2人缺阵、贝德纳雷克解禁、联赛8战全胜'),
}
SINGLE = {'周二006', '周二007'}   # 规则63：用户赛前告知开单关

# 规则76补充校准 + 规则36身价先验（跨联赛）：低等级/低身价方国内极端数据不可直接迁移
# 身价（Transfermarkt，2026-10-20，单位百万欧）
VALUE = {'费内巴切': 261.2, '斯拉维亚': 111.2, '萨巴赫': 19.0, '多特蒙德': 587.9,
         '伍尔弗': 247.65, '朴次茅斯': 41.35, '那不勒斯': 424.5, '博德闪耀': 79.18,
         '罗马': 498.4, '布拉迪斯': 38.68, '巴黎圣曼': 1360.0, '巴萨': 1300.0,
         '利物浦': 1030.0, '比利亚雷': 368.05, '曼城': 1500.0, '雅典AEK': 86.45,
         '斯图加特': 399.45, '马竞': 703.5, '波尔图': 471.5, '埃因霍温': 306.5}
# 指数随等级差递增：gap≥2 → 0.18；gap=1 → 0.12；gap=0（同档跨联赛）→ 0.06；同联赛不启用
VALUE_EXP = {'周二001': 0.12, '周二002': 0.18, '周二004': 0.18, '周二005': 0.18,
             '周二006': 0.06, '周二007': 0.06, '周二008': 0.18, '周二009': 0.06, '周二010': 0.06}

# 规则76 的"信息缺失"处理：斯拉万无国内积分榜 → 用"联赛平均队"起步，再叠加UCL 2轮证据（1进9失）
SLOVAN_PROXY = dict(team='Slovan Bratislava(无榜数据)', played=10,
                    avg_goals_scored=1.35, avg_goals_conceded=1.10)

HAD_ORDER = ['home', 'draw', 'away']
NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}

SHRINK_K = 6.0
# 2026-10-20 用户指定"新口径"临时重算（未写入规则）：
# 欧冠当季基准 = 前两轮 147球/36场 = 4.08，向常态3.2收缩50% → 3.6
LEAGUE_PROFILE = {'欧冠': dict(base=3.60, home=1.25), '英冠': dict(base=None, home=1.33)}

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
    """返回 (row, league_key, league_avg, missing_flag)"""
    key, fn, en = TEAM_TABLE[name]
    rows = load_table(fn)
    if rows is None:
        if name == '布拉迪斯':
            return dict(SLOVAN_PROXY), key, 2.70, True
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
    # 规则74 六档：以首推球数落档，并保证与TOP2自洽（同档或相邻档）
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
    if base is None:
        rows = load_table(TEAM_TABLE[m['home']][1])
        base = league_avg(rows)
    H = prof['home']

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

    # 规则76补充：跨联赛身价先验（规则36），防止弱联赛极端防守数据直接迁移
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

    # 规则63 单关平局上修（上限 +8pp）
    single_note = ''
    if num in SINGLE:
        sf0 = sorted(fused.items(), key=lambda x: -x[1])
        gap = (sf0[0][1] - fused['draw']) * 100
        add = 0.08 if gap <= 10 else (0.06 if gap <= 20 else 0.04)
        old = fused['draw']; new = min(old + add, 0.58); add = new - old
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
        # 深盘（|让球|≥2）次选按模型概率最高项取，让平优先于低概率让负
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

    # 半全场：欧冠不适用规则66，直接取模型TOP3；英冠按0.42比例
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
        'base_league_avg': round(base, 3), 'home_adv': H,
        'own_league_home': hlg, 'own_league_away': alg,
        'atk_home': round(atk_h, 3), 'def_home': round(def_h, 3),
        'atk_away': round(atk_a, 3), 'def_away': round(def_a, 3),
        'table_missing': missing, 'rule76': r76, 'value_mult': value_mult,
        'adj_note': adj['note'], 'dc': {k: round(v, 4) for k, v in dc_p.items()},
        'nb': {k: round(v, 4) for k, v in nb_p.items()},
        'mc': {k: round(v, 4) for k, v in mc_p.items()},
        'fused': {k: round(v, 4) for k, v in fused.items()},
        'primary': primary, 'secondary': secondary,
        'primary_prob': round(sf[0][1], 4), 'secondary_prob': round(sf[1][1], 4),
        'third': sf[2][0], 'third_prob': round(sf[2][1], 4),
        'single_note': single_note,
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
        lines.append('   融合 主%.1f/平%.1f/客%.1f → 首选%s(%.1f) 次选%s(%.1f) %s' % (
            r['fused']['home'] * 100, r['fused']['draw'] * 100, r['fused']['away'] * 100,
            NAME_CN[r['primary']], r['primary_prob'] * 100, NAME_CN[r['secondary']], r['secondary_prob'] * 100,
            r['single_note']))
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
    io.open('reports/data/20261020_model_log.txt', 'w', encoding='utf-8').write('\n'.join(lines))
    print('\n'.join(lines))
    print('saved', out)


if __name__ == '__main__':
    main()
