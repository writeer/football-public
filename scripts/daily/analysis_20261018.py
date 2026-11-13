# -*- coding: utf-8 -*-
"""
2026-10-18（周日）竞彩33场 模型计算
AGENTS.md 第3-5步：联赛特征 → 基本面 → 模型

⚠️ 规则79（2026-10-18 用户裁决）：**已改为纯基本面口径**
   - 删除原 `fit_lambdas`（从市场去水概率反解 λ）
   - λ 改由 `lottery_agent.fundamental.fundamental_lambdas()` 用积分榜场均进失球计算
   - 融合权重中 mkt / shin 归零，赔率只做去水对照（分歧度、EV）
   - 注：本脚本产出的 `20261018_model_output.json` 与当日报告为**旧口径历史存档**，
     重跑将得到基本面口径结果，两者不可混用。

规则：63单关平局上修（001/010/021）、65大球上修、66半场平局、67双轨制、
      68英超主场下调、69法甲平局上修、52a让球无条件众数、74大小球六档、79禁止赔率反解
输出：reports/data/20261018_model_output.json
"""
import sys, json, io, os
sys.path.insert(0, r'e:\VibeCoding\football')
import numpy as np
from scipy import stats as sp_stats
from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, OddsCalibrator, HTFTModel)
from lottery_agent.fundamental import fundamental_lambdas

SRC = 'reports/data/20261018_matches.json'
OUT = 'reports/data/20261018_model_output.json'

# 联赛 -> (ht_draw_rate, 半场lambda比例)  规则66
LEAGUE_HT = {
    '日职': (0.534, 0.38), '韩职': (0.512, 0.38), '荷甲': (0.387, 0.42), '意甲': (0.409, 0.38),
    '西甲': (0.441, 0.38), '瑞超': (0.413, 0.38), '芬超': (0.418, 0.38), '挪超': (0.325, 0.45),
    '英超': (0.384, 0.42), '法甲': (0.393, 0.42), '德甲': (0.359, 0.42), '巴甲': (None, 0.45),
    '法乙': (0.451, 0.38), '葡超': (0.414, 0.38),
}
LEAGUE_AVG = {'日职': 2.52, '韩职': 2.48, '荷甲': 3.18, '意甲': 2.63, '西甲': 2.48, '瑞超': 3.05,
              '芬超': 2.55, '挪超': 2.82, '英超': 2.86, '法甲': 2.68, '德甲': 3.21, '巴甲': 2.72,
              '法乙': 2.45, '葡超': 2.62}

# 总控人工修正表（第1-2步信息裁决后）：lh/la=攻击λ乘数；dt=规则65大球上修总进球增量
ADJ = {
    '周日001': dict(lh=0.97, la=1.00, dt=0.00, note='町田10-15亚冠二级客场72小时内两赛+往返新加坡，预计轮换；下田北斗停赛。福冈3人缺阵、客场3战全败'),
    '周日002': dict(lh=0.96, la=0.95, dt=0.00, note='江原10-15亚冠全替补1-2负，近10场2胜6平2负；仁川5人伤停（穆戈沙存疑）、客场近4场1平3负'),
    '周日003': dict(lh=0.97, la=0.98, dt=0.20, note='首尔榜首+主场4连胜，但10-14亚冠0-3负墨尔本、赛程密集；金泉为其苦主（近5次交锋不败）'),
    '周日004': dict(lh=1.00, la=1.05, dt=0.30, note='兹沃勒垫底+换帅首战、8轮丢21球；前进之鹰近4连平、场均总进球4.50（荷甲大球）'),
    '周日005': dict(lh=0.92, la=1.00, dt=0.20, note='乌迪内斯5人伤停且锋线三人全缺（扎尼奥洛/巴约/盖耶）；莱切3人缺阵、双方场均失2球'),
    '周日006': dict(lh=0.96, la=1.02, dt=0.30, note='奥萨苏纳5人伤停+5轮不胜；桑坦德客场0胜、6轮丢23球、场均总进球4.50'),
    '周日007': dict(lh=1.02, la=1.00, dt=0.30, note='天狼星榜首近4轮全胜、主场7胜2平2负；埃尔夫斯堡近3轮全胜但少休3天，双方进攻效率高'),
    '周日008': dict(lh=0.95, la=0.95, dt=0.00, note='KuPS中场3人停赛+1人长伤、10-15欧协联2-4负；VPS客场近6战2胜4负'),
    '周日009': dict(lh=1.00, la=0.96, dt=0.20, note='罗森博格3名主力停赛+1伤、阵容被迫轮换；萨普斯堡人造草主场'),
    '周日010': dict(lh=1.02, la=0.95, dt=0.00, note='曼联4人缺阵（谢什科/多古/马兹拉维/乌加特）+卢克肖梅努存疑、5场不胜帅位危机；利兹仅罗顿缺阵'),
    '周日011': dict(lh=0.97, la=0.97, dt=0.00, note='伯恩茅斯5人伤停、主场未胜；桑德兰头号前锋布罗贝缺阵+4人伤停，双方均缺终结点'),
    '周日012': dict(lh=0.94, la=1.00, dt=0.15, note='佛罗伦萨第19+弗兰基Curva Fiesole部分关闭、主场氛围打折；科莫欧战2-3负费耶诺德、轮换存疑'),
    '周日013': dict(lh=1.00, la=0.97, dt=0.30, note='昂热上轮1-5惨败、后防核心勒福尔停赛；马赛欧冠0-1负+霍伊别尔缺阵、客场不稳（法甲平局上修）'),
    '周日014': dict(lh=0.95, la=0.96, dt=0.20, note='勒沃库森换帅磨合+6人伤停；弗赖堡榜首但10-16刚踢欧协联、双线体能透支'),
    '周日015': dict(lh=0.95, la=0.93, dt=0.00, note='塞尔塔5人伤停含两名前锋+Balaidos部分关闭；阿拉维斯3人缺阵，双方均缺终结点'),
    '周日016': dict(lh=1.03, la=0.98, dt=0.40, note='阿贾克斯5名后卫伤缺+多尔贝里赛季报销；格罗宁根上轮3-0、场均总进球4.25，荷甲对攻'),
    '周日017': dict(lh=1.00, la=0.94, dt=0.15, note='摩纳哥10-16欧协联客场远征、仅隔2天+3人缺阵；洛里昂近4次交锋2胜2平不败（法甲平局上修）'),
    '周日018': dict(lh=0.92, la=0.97, dt=0.10, note='诺丁汉2确认+2存疑、仅进5球；阿森纳3缺1疑（萨利巴/因卡皮耶/佐利斯），周中欧冠轮休主力'),
    '周日019': dict(lh=0.93, la=1.00, dt=0.40, note='门兴7人伤停+5战0分+新帅首秀失利；霍芬海姆4人缺阵+4连败，双方场均失球均超2.5'),
    '周日020': dict(lh=0.94, la=0.94, dt=0.15, note='米兰一周三赛+计划大轮换；亚特兰大8人伤停+7天3赛，双方均减员'),
    '周日021': dict(lh=0.90, la=0.96, dt=0.00, note='马拉加垫底0胜、场均0.5球+4人伤停；皇社5人缺阵+欧联轮换（单关平局上修）'),
    '周日022': dict(lh=0.90, la=0.98, dt=0.00, note='尤文7人伤停（伊尔迪兹/米利克/博加/埃卡托全缺）+主帅停赛；拉齐奥6轮不败、无欧战以逸待劳'),
    '周日023': dict(lh=0.95, la=0.93, dt=0.10, note='里昂欧联3-2水晶宫后体能损耗+左后卫缺人；尼斯7人伤停、客场2战0球'),
    '周日024': dict(lh=1.00, la=1.00, dt=0.30, note='皇马缺维尼修斯（停赛）/罗德里戈/门迪/阿森西奥；塞维利亚5人缺阵但客场4轮不败'),
    '周日025': dict(lh=0.90, la=1.02, dt=0.10, note='弗鲁米嫩塞10-21解放者杯半决赛次回合、本场几乎全替补；桑托斯内马尔回归首发'),
    '周一001': dict(lh=0.94, la=1.00, dt=0.10, note='蒙扎5人伤停+主帅皮萨卡内停赛；卡利亚里6轮13分、客场4连胜、仅失3球'),
    '周一002': dict(lh=0.98, la=0.98, dt=0.00, note='保级6分战：代格福什13位20分 vs 卡尔马14位19分，双方伤停信息缺失、低温闷战'),
    '周一003': dict(lh=0.95, la=0.95, dt=0.00, note='帕尔马4人伤停+第18；都灵4人伤停含萨帕塔，双方进攻效率低'),
    '周一004': dict(lh=0.98, la=1.00, dt=0.00, note='罗德兹5轮不胜、已失18球；蒙彼利埃全季仅1负、5场零封、场均总进球1.62'),
    '周一005': dict(lh=0.90, la=0.95, dt=0.10, note='热刺7-10人缺阵（西蒙斯/奥多贝尔重伤+本坦库尔停赛）、20位场均0.5球；考文垂客场0胜'),
    '周一006': dict(lh=0.95, la=0.97, dt=0.00, note='赫塔费2确认+5存疑、上轮0-3负巴萨；巴列卡诺3人伤停，赫塔费近10次交锋不胜'),
    '周一007': dict(lh=0.93, la=0.93, dt=0.00, note='布拉加周中欧协联0-3负哥本哈根+2人伤停；吉维森特场均总进球1.57、客场仅负本菲卡'),
    '周一008': dict(lh=0.95, la=0.93, dt=0.10, note='科林蒂安保级生死战、德佩停赛+拉涅莱伤；维多利亚9人伤停、必死守'),
}
SINGLE = {'周日001', '周日010', '周日021'}
# 联赛概率平移（百分点）：规则68英超 / 规则22意甲·西甲·韩职 / 规则69法甲
LEAGUE_SHIFT = {'英超': (-4, +5), '意甲': (0, +3), '西甲': (0, +4), '韩职': (0, +3), '法甲': (0, +5)}

HAD_ORDER = ['home', 'draw', 'away']
NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}


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
        try:
            i, j = [int(t) for t in k.split(':')]
        except Exception:
            continue
        p = o.get('noVig') or 0
        if i > j:
            h += p
        elif i == j:
            d += p
        else:
            a += p
    t = h + d + a
    return {'home': h / t, 'draw': d / t, 'away': a / t}


# 规则79：联赛 → 积分榜文件
TABLE_FILE = {
    '日职': 'table_japan1.json', '韩职': 'table_korea1.json', '荷甲': 'table_holland1.json',
    '意甲': 'table_italy1.json', '西甲': 'table_spain1.json', '瑞超': 'table_sweden1.json',
    '芬超': 'table_finland1.json', '挪超': 'table_norway.json', '英超': 'table_premier.json',
    '法甲': 'table_france1.json', '德甲': 'table_germany1.json', '巴甲': 'table_brazil1.json',
    '法乙': 'table_france2.json', '葡超': 'table_portugal1.json',
}

# 中文队名 → 积分榜英文名关键词（按当日场次维护；新的一天需重建）
TEAM_ALIAS = {
    '町田泽维': 'Machida', '福冈黄蜂': 'Fukuoka', '江原FC': 'Gangwon', '仁川联': 'Incheon',
    '首尔FC': 'Seoul', '金泉尚武': 'Gimcheon', '兹沃勒': 'Zwolle', '前进之鹰': 'G.A. Eagles',
    '乌迪内斯': 'Udinese', '莱切': 'Lecce', '奥萨苏纳': 'Osasuna', '桑坦德': 'Santander',
    '天狼星': 'Sirius', '埃夫斯堡': 'Elfsborg', '库奥皮奥': 'KuPS', '瓦萨': 'VPS',
    '萨普斯堡': 'Sarpsborg', '罗森博格': 'Rosenborg', '利兹联': 'Leeds', '曼联': 'Manchester Utd',
    '伯恩茅斯': 'Bournemouth', '桑德兰': 'Sunderland', '佛罗伦萨': 'Fiorentina', '科莫': 'Como',
    '昂热': 'Angers', '马赛': 'Marseille', '勒沃库森': 'Leverkusen', '弗赖堡': 'Freiburg',
    '塞尔塔': 'Celta', '阿拉维斯': 'Alaves', '格罗宁根': 'Groningen', '阿贾克斯': 'Ajax',
    '洛里昂': 'Lorient', '摩纳哥': 'Monaco', '诺丁汉': 'Nottingham', '阿森纳': 'Arsenal',
    '门兴': 'Monchengladbach', '霍芬海姆': 'Hoffenheim', 'AC米兰': 'AC Milan', '亚特兰大': 'Atalanta',
    '马拉加': 'Malaga', '皇家社会': 'Real Sociedad', '尤文图斯': 'Juventus', '拉齐奥': 'Lazio',
    '里昂': 'Lyon', '尼斯': 'Nice', '皇马': 'Real Madrid', '塞维利亚': 'Sevilla',
    '弗鲁米嫩': 'Fluminense', '桑托斯': 'Santos', '蒙扎': 'Monza', '卡利亚里': 'Cagliari',
    '代格福什': 'Degerfors', '卡尔马': 'Kalmar', '帕尔马': 'Parma', '都灵': 'Torino',
    '罗德兹': 'Rodez', '蒙彼利埃': 'Montpellier', '热刺': 'Tottenham', '考文垂': 'Coventry',
    '赫塔费': 'Getafe', '巴列卡诺': 'Rayo', '布拉加': 'Braga', '吉维森特': 'Gil Vicente',
    '科林蒂安': 'Corinthians', '维多利亚': 'Vitoria',
}

_TABLE_CACHE = {}


def load_table(league):
    """读取该联赛积分榜（缺失返回 None）"""
    if league in _TABLE_CACHE:
        return _TABLE_CACHE[league]
    fn = TABLE_FILE.get(league)
    rows = None
    if fn and os.path.exists(os.path.join('reports/data', fn)):
        with open(os.path.join('reports/data', fn), encoding='utf-8-sig') as f:
            rows = json.load(f).get('table')
    _TABLE_CACHE[league] = rows
    return rows


def match_row(name, rows):
    """中文队名 → 积分榜行；匹配不到返回 None"""
    if not rows:
        return None
    key = TEAM_ALIAS.get(name, name)
    for r in rows:
        if r.get('team', '').lower() == key.lower():
            return r
    for r in rows:
        if key.lower() in r.get('team', '').lower():
            return r
    return None


def fundamental_pair(m, league):
    """规则79：纯基本面 λ。积分榜缺失时退化为联赛平均队，绝不回流赔率。"""
    rows = load_table(league)
    hrow = match_row(m['home'], rows)
    arow = match_row(m['away'], rows)
    missing = []
    prof_side = LEAGUE_AVG.get(league, 2.6) / 2.0
    if hrow is None:
        missing.append(m['home'])
        hrow = {'team': m['home'] + '(无榜数据)', 'played': 0,
                'avg_goals_scored': prof_side, 'avg_goals_conceded': prof_side}
    if arow is None:
        missing.append(m['away'])
        arow = {'team': m['away'] + '(无榜数据)', 'played': 0,
                'avg_goals_scored': prof_side, 'avg_goals_conceded': prof_side}
    res = fundamental_lambdas(hrow, arow, league, table_rows=rows)
    res['missing'] = missing
    return res


def tier_of(p01, p23, p45, p6, top1, top2b):
    # 规则74 六档：以TOP2覆盖区间落档，保证"档位与TOP2自洽"
    if p6 >= 0.25:
        return '穿盘可能(6-7+球)'
    if p01 >= 0.40:
        return '闷战超小球(0-1球)'
    if top2b >= 6:
        return '穿盘可能(6-7+球)'
    if top2b == 5:
        return '超大球(5-6球)'
    if top2b == 4:
        return '大球(4-5球)'
    if top2b == 3 and p23 >= 0.40:
        return '常规正常球(2-3球)'
    if top2b <= 2:
        return '小球(1-2球)'
    return '常规正常球(2-3球)'


def analyze(m):
    num, league = m['num'], m['league']
    if m['had']:
        odds = {o['key']: o['odds'] for o in m['had']}
        market = de_vig(odds)
        shin = OddsCalibrator(odds['home'], odds['draw'], odds['away']).shin()
        shin_probs = [shin['home'], shin['draw'], shin['away']]
        src = 'HAD去水'
    else:
        market = had_from_crs(m['crs'])
        shin_probs = [market['home'], market['draw'], market['away']]
        src = 'CRS聚合(无HAD盘)'

    # 规则79：λ 只来自基本面（积分榜场均进失球），market 仅作对照
    fund = fundamental_pair(m, league)
    lh, la = fund['lambda_home'], fund['lambda_away']
    adj = ADJ.get(num, dict(lh=1.0, la=1.0, dt=0.0, note=''))
    lh *= adj['lh']
    la *= adj['la']
    if adj['dt']:
        tot = lh + la
        lh += adj['dt'] * lh / tot
        la += adj['dt'] * la / tot

    dc = DixonColesModel(); nb = NegativeBinomialModel(); zp = ZIPModel(); sk = SkellamModel()
    mc = MonteCarloSimulator(n_sim=20000)
    dc_p = dc.outcome_probs(lh, la); nb_p = nb.outcome_probs(lh, la)
    zip_p = zp.outcome_probs(lh, la); skp = sk.outcome_probs(lh, la)
    mcr = mc.simulate(lh, la)
    mc_p = {'home': mcr['home_win'], 'draw': mcr['draw'], 'away': mcr['away_win']}
    # 规则79：mkt / shin 权重归零，融合只由统计模型构成
    W = {'dc': 0.34, 'nb': 0.22, 'zip': 0.13, 'sk': 0.14, 'mc': 0.17, 'shin': 0.0, 'mkt': 0.0}
    fused = {}
    for k in HAD_ORDER:
        fused[k] = (W['dc'] * dc_p[k] + W['nb'] * nb_p[k] + W['zip'] * zip_p[k] + W['sk'] * skp[k]
                    + W['mc'] * mc_p[k] + W['shin'] * shin_probs[HAD_ORDER.index(k)] + W['mkt'] * market[k])

    if league in LEAGUE_SHIFT:
        dh, dd = LEAGUE_SHIFT[league]
        fused['home'] += dh / 100.0
        fused['draw'] += dd / 100.0
        fused['away'] -= (dh + dd) / 100.0
    for k in HAD_ORDER:
        fused[k] = max(fused[k], 0.01)
    s = sum(fused.values())
    fused = {k: v / s for k, v in fused.items()}

    # 规则63 单关平局上修（L218：上限+8pp，避免压过真实非平信号）
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
        single_note = '单关平局上修+%.1fpp（首选-平差距%.1fpp，按L218上限8pp执行）' % (add * 100, gap)

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
    band = sorted([(i, i - kr, matrix[i, i - kr]) for i in range(26)
                   if 0 <= i - kr < 26 and i < n and 0 <= i - kr < n], key=lambda x: -x[2])

    # 让球（规则52a：无条件净胜球众数）
    gl = (m['hhad'] or {}).get('goalLine')
    hh_model = hh_market = hh_odds = None
    hc_first = hc_second = ''
    if m['hhad']:
        th = -gl
        hh_model = {'home': float(sp_stats.skellam.sf(th, lh, la)),
                    'draw': float(sp_stats.skellam.pmf(th, lh, la)),
                    'away': float(sp_stats.skellam.cdf(th - 1, lh, la))}
        hh_odds = {o['key']: o['odds'] for o in m['hhad']['outcomes']}
        hh_market = {o['key']: (o['noVig'] or 0) for o in m['hhad']['outcomes']}
        kd = k_dist[0]
        adj_net = kd + gl
        if adj_net > 0:
            hc_first = 'home'
        elif adj_net == 0:
            hc_first = 'draw'
        else:
            hc_first = 'away'
        # 让平概率（无条件）：调整后净胜=0 的概率
        hh_draw_prob = gd.get(-gl, 0.0)
        combo = {k: 0.5 * hh_model[k] + 0.5 * hh_market[k] for k in HAD_ORDER}
        rest = sorted([k for k in HAD_ORDER if k != hc_first], key=lambda k: -combo[k])
        hc_second = rest[0]
        if hh_draw_prob >= 0.20 and 'draw' not in (hc_first, hc_second):
            hc_second = 'draw'  # L216 硬校验

    hr = LEAGUE_HT.get(league, (None, 0.45))[1]
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
    # L215：两端概率≥25%时必须占TOP2一席
    top2 = [ttg_top[0][0], ttg_top[1][0]]
    if p01 >= 0.25 and not any(k <= 1 for k in top2):
        alt = max([(k, v) for k, v in tg.items() if k <= 1], key=lambda x: x[1])
        top2 = sorted(top2 + [alt[0]], key=lambda k: -tg[k])[:2] if tg[alt[0]] > tg[top2[1]] else [top2[0], alt[0]]
    if p6 >= 0.25 and not any(k >= 5 for k in top2):
        alt = max([(k, v) for k, v in tg.items() if k >= 5], key=lambda x: x[1])
        top2 = [top2[0], alt[0]]  # L215：5球以上合计≥25% 强制占TOP2一席
    top2 = sorted(set(top2), key=lambda k: -tg[k])[:2]
    tier = tier_of(p01, p23, p45, p6, min(top2), max(top2))

    ttg_odds = {o['key']: o['odds'] for o in m['ttg']}
    hafu_odds = {o['key']: o['odds'] for o in m['hafu']}
    crs_odds = {o['key']: o['odds'] for o in m['crs']}

    top_scores = sorted([(i, j, matrix[i, j]) for i in range(n) for j in range(n)], key=lambda x: -x[2])[:8]

    # 半全场：规则66 高半场平局联赛（ht_draw_rate≥0.40）首选必须含"平"
    ht3 = htft_cn[:]
    if LEAGUE_HT.get(league, (None, 0.45))[0] is not None and LEAGUE_HT[league][0] >= 0.40:
        draw_codes = [(k, v) for k, v in htft_cn if k in ('平胜', '平平', '平负')]
        rest = [(k, v) for k, v in htft_cn if k not in ('平胜', '平平', '平负')]
        ht3 = sorted(draw_codes, key=lambda x: -x[1])[:1] + sorted(rest, key=lambda x: -x[1])[:2]
    else:
        ht3 = htft_cn[:3]

    return {
        'num': num, 'league': league, 'home': m['home'], 'away': m['away'],
        'home_rank': m['home_rank'], 'away_rank': m['away_rank'], 'time': m['time'],
        'is_single': num in SINGLE, 'had_source': src,
        'odds_had': ({o['key']: o['odds'] for o in m['had']} if m['had'] else None),
        'odds_hhad': hh_odds, 'hhad_line': gl, 'odds_ttg': ttg_odds, 'odds_hafu': hafu_odds,
        'odds_crs': crs_odds, 'crs_raw': m['crs'],
        'market': {k: round(v, 4) for k, v in market.items()},
        'shin': [round(p, 4) for p in shin_probs],
        'lambda_home': round(lh, 3), 'lambda_away': round(la, 3), 'lambda_total': round(lh + la, 3),
        # 规则79：λ 来源留痕（基本面口径）
        'lambda_source': 'fundamental(rule79)',
        'lambda_basis': fund['basis'], 'league_avg_goals': round(fund['league_avg'], 3),
        'atk_home': round(fund['atk_home'], 3), 'def_home': round(fund['def_home'], 3),
        'atk_away': round(fund['atk_away'], 3), 'def_away': round(fund['def_away'], 3),
        'table_missing': fund['missing'],
        'adj_note': adj['note'], 'dc': {k: round(v, 4) for k, v in dc_p.items()},
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
        'tier': tier,
        'htft': [(k, round(v, 4)) for k, v in htft_cn[:9]],
        'htft_top3': [(k, round(v, 4)) for k, v in ht3],
        'ht_scores': [(a, b, round(p, 4)) for a, b, p in ht_scores],
    }


def main():
    ms = json.load(io.open(SRC, encoding='utf-8'))
    res = [analyze(m) for m in ms]
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    json.dump(res, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    lines = []
    for r in res:
        lines.append('%s %s vs %s [%s] 单关=%s λ%.2f/%.2f(总%.2f) %s' % (
            r['num'], r['home'], r['away'], r['league'], r['is_single'],
            r['lambda_home'], r['lambda_away'], r['lambda_total'], r['had_source']))
        lines.append('   融合 主%.1f/平%.1f/客%.1f → 首选%s(%.1f) 次选%s(%.1f) %s' % (
            r['fused']['home'] * 100, r['fused']['draw'] * 100, r['fused']['away'] * 100,
            NAME_CN[r['primary']], r['primary_prob'] * 100, NAME_CN[r['secondary']], r['secondary_prob'] * 100,
            r['single_note']))
        lines.append('   让(%s) 首选%s 次选%s｜模型%s 市场%s 让平%.1f%%' % (
            r['hhad_line'], r['hc_first'], r['hc_second'], r['hhad_model'], r['hhad_market'],
            (r['hhad_draw_prob'] or 0) * 100))
        lines.append('   k_dist=%+d(%.1f%%) k_rec=%+d(%.1f%%) %s 带内=%s' % (
            r['k_dist'], r['k_dist_prob'] * 100, r['k_rec'], r['k_rec_prob'] * 100,
            '一致' if r['k_consistent'] else '分歧', [('%d-%d' % (a, b), round(p * 100, 1)) for a, b, p in r['band'][:3]]))
        lines.append('   TTG %s | 0-1球%.0f%% 2-3球%.0f%% 4-5球%.0f%% 6+球%.0f%% | %s' % (
            r['ttg_top2'], r['p01'] * 100, r['p23'] * 100, r['p45'] * 100, r['p6'] * 100, r['tier']))
        lines.append('   半全场 %s | 半场比分 %s' % (
            [(k, round(v * 100, 1)) for k, v in r['htft_top3']],
            [('%d-%d' % (a, b), round(p * 100, 1)) for a, b, p in r['ht_scores'][:3]]))
    io.open('reports/data/20261018_model_log.txt', 'w', encoding='utf-8').write('\n'.join(lines))
    print('\n'.join(lines))
    print('saved', OUT)


if __name__ == '__main__':
    main()
