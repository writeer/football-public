# -*- coding: utf-8 -*-
"""
2026-10-22（周四）竞彩13场 模型计算
AGENTS.md 第3-5步：联赛特征 → 基本面 → 模型

⚠️ 规则79：纯基本面口径（禁止赔率反解 λ）
   λ = fundamental_lambdas() 用积分榜场均进失球 + 守恒式
   融合权重 shin/mkt = 0，赔率仅 de_vig 对照分歧

特殊规则：
  - 全部为跨联赛赛事（欧罗巴/欧协联/解放者杯）→ 规则22-REF：跳过全部联赛特化
    （规则68英超主场下调、规则69法甲平局上修 均不适用）
  - 规则76：跨联赛等级差校准（在 ADJ 中用 lh/la 体现）
  - 规则63：单关场次 006/009 平局上修（上限+8pp）
  - 规则66：半场平局修正（按各队所属联赛 ht_draw_rate，跨联赛取较高一方修正）
  - 规则52a：让球无条件净胜球众数
  - 规则67：比分双轨制
  - 规则74：大小球六档
输出：reports/data/20261022_model_output.json
"""
import sys, json, io, os
sys.path.insert(0, r'e:\VibeCoding\football')
import numpy as np
from scipy import stats as sp_stats
from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, OddsCalibrator, HTFTModel)
from lottery_agent.fundamental import fundamental_lambdas

SRC = 'reports/data/20261022_matches.json'
OUT = 'reports/data/20261022_model_output.json'

# 跨联赛赛事用欧冠级别主场加成（欧战主场优势低于联赛）
LEAGUE_PROFILE_KEY = {'欧罗巴': '欧冠', '欧协联': '欧冠', '解放者杯': 'default'}

# 规则66 半场平局率：按各队所属国内联赛取较高一方 ht_draw_rate
# （跨联赛无单一联赛值，取两队联赛中较高者偏保守）
TEAM_HT = {
    '格拉茨风暴': 0.380, '马赛': 0.393, '波兹南莱赫': 0.390, '桑德兰': 0.384,
    '萨格勒布迪纳摩': 0.390, '奈梅亨': 0.387, '尤文图斯': 0.409, '雷恩': 0.393,
    '克里特': 0.409, '勒沃库森': 0.359, '伯恩茅斯': 0.384, 'AC米兰': 0.409,
    '凯尔特人': 0.370, '维戈塞尔塔': 0.441, '贝西克塔斯': 0.395, '水晶宫': 0.384,
    '霍芬海姆': 0.359, '里昂': 0.393, '利勒斯特罗姆': 0.325, '皇家社会': 0.441,
    '阿贾克斯': 0.387, '亚特兰大': 0.409, '摩纳哥': 0.393, '弗赖堡': 0.359,
    '弗拉门戈': 0.350, '拉普拉塔大学生': 0.350,
}

# 总控人工修正表（跨联赛等级差 + 赛程 + 已知伤停，纯基本面性质）
ADJ = {
    '周四001': dict(lh=1.00, la=1.00, dt=0.0, note='格拉茨风暴奥超中游主场强；马赛法甲榜首实力占优但欧战客场不稳，跨联赛等级差法甲>奥超约1档'),
    '周四002': dict(lh=1.00, la=1.00, dt=0.0, note='波兹南波兰超榜首主场强；桑德兰英超升班马，跨联赛英超>波超约2档但客场欧战经验少'),
    '周四003': dict(lh=1.00, la=1.00, dt=0.0, note='萨格勒布迪纳摩克甲班霸欧战常客主场极强；奈梅亨荷甲中游，克甲≈荷甲等级接近'),
    '周四004': dict(lh=1.00, la=1.00, dt=0.0, note='尤文图斯意甲豪门主场；雷恩法甲中游，跨联赛意甲≈法甲，尤文底蕴占优'),
    '周四005': dict(lh=1.00, la=1.00, dt=0.2, note='克里特希超弱旅；勒沃库森德甲豪门实力碾压（等级差2档+），大球倾向'),
    '周四006': dict(lh=1.00, la=1.00, dt=0.0, note='伯恩茅斯英超中游主场；AC米兰意甲豪门，英超≈意甲等级接近，米兰阵容稍优（单关）'),
    '周四007': dict(lh=1.02, la=1.00, dt=0.0, note='凯尔特人苏超班霸主场胜率极高（凯尔特人公园主场优势欧战著名）；塞尔塔西甲中游客场弱'),
    '周四008': dict(lh=1.00, la=1.00, dt=0.0, note='贝西克塔斯土超豪门主场魔鬼；水晶宫英超中游，土超英超等级接近，主场加成关键'),
    '周四009': dict(lh=1.00, la=1.00, dt=0.0, note='霍芬海姆德甲中上游主场；里昂法甲榜首，德甲≈法甲等级接近，双方近期状态好（单关）'),
    '周四010': dict(lh=1.00, la=1.00, dt=0.0, note='利勒斯特罗姆挪超主场；皇家社会西甲中上游实力占优，西甲>挪超约1-2档'),
    '周四011': dict(lh=1.00, la=1.00, dt=0.1, note='阿贾克斯荷甲豪门主场；亚特兰大意甲劲旅，荷甲≈意甲等级接近，对攻倾向'),
    '周四012': dict(lh=1.00, la=1.00, dt=0.0, note='摩纳哥法甲中上游主场；弗赖堡德甲榜首状态火热，法甲≈德甲等级接近'),
    '周四013': dict(lh=1.02, la=1.00, dt=0.1, note='弗拉门戈巴甲豪门主场解放者杯经验丰富；拉普拉塔大学生阿甲中游，巴甲≈阿甲'),
}
SINGLE = {'周四006', '周四009'}

# 跨联赛不做国内联赛概率平移（规则22-REF）
LEAGUE_SHIFT = {}

HAD_ORDER = ['home', 'draw', 'away']
NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}

# 积分榜文件（国内联赛）
TABLE_FILE = {
    '法甲': 'table_france1.json', '英超': 'table_premier.json', '德甲': 'table_germany1.json',
    '意甲': 'table_italy1.json', '西甲': 'table_spain1.json', '荷甲': 'table_holland1.json',
    '土超': 'table_turkey1.json', '希超': 'table_greece1.json', '奥超': 'table_austria1.json',
    '挪超': 'table_norway.json', '英冠': 'table_championship.json', '巴甲': 'table_brazil1.json',
    '苏超': 'table_scotland1.json', '波兰超': 'table_poland1.json',
}

# 中文队名 → 所属国内联赛（用于取积分榜）
TEAM_LEAGUE = {
    '格拉茨风暴': '奥超', '马赛': '法甲', '波兹南莱赫': '波兰超', '桑德兰': '英超',
    '萨格勒布迪纳摩': None, '奈梅亨': '荷甲', '尤文图斯': '意甲', '雷恩': '法甲',
    '克里特': '希超', '勒沃库森': '德甲', '伯恩茅斯': '英超', 'AC米兰': '意甲',
    '凯尔特人': '苏超', '维戈塞尔塔': '西甲', '贝西克塔斯': '土超', '水晶宫': '英超',
    '霍芬海姆': '德甲', '里昂': '法甲', '利勒斯特罗姆': '挪超', '皇家社会': '西甲',
    '阿贾克斯': '荷甲', '亚特兰大': '意甲', '摩纳哥': '法甲', '弗赖堡': '德甲',
    '弗拉门戈': '巴甲', '拉普拉塔大学生': None,
}

# 中文队名 → 积分榜英文名
TEAM_ALIAS = {
    '格拉茨风暴': 'Sturm Graz', '马赛': 'Marseille', '波兹南莱赫': 'Lech Poznan',
    '桑德兰': 'Sunderland', '萨格勒布迪纳摩': None, '奈梅亨': 'Nijmegen',
    '尤文图斯': 'Juventus', '雷恩': 'Rennes', '克里特': 'OFI Crete',
    '勒沃库森': 'Bayer Leverkusen', '伯恩茅斯': 'Bournemouth', 'AC米兰': 'AC Milan',
    '凯尔特人': 'Celtic', '维戈塞尔塔': 'Celta Vigo', '贝西克塔斯': 'Besiktas',
    '水晶宫': 'Crystal Palace', '霍芬海姆': 'Hoffenheim', '里昂': 'Lyon',
    '利勒斯特罗姆': 'Lillestrom', '皇家社会': 'Real Sociedad', '阿贾克斯': 'Ajax',
    '亚特兰大': 'Atalanta', '摩纳哥': 'Monaco', '弗赖堡': 'Freiburg',
    '弗拉门戈': 'Flamengo RJ', '拉普拉塔大学生': None,
}

_TABLE_CACHE = {}


def load_table(league):
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
    if not rows:
        return None
    key = TEAM_ALIAS.get(name, name)
    if key is None:
        return None
    for r in rows:
        if r.get('team', '').lower() == key.lower():
            return r
    for r in rows:
        if key.lower() in r.get('team', '').lower():
            return r
    return None


def team_row(name):
    """返回该队在国内联赛的积分榜行（缺失返回 None）"""
    lg = TEAM_LEAGUE.get(name)
    if not lg:
        return None
    rows = load_table(lg)
    return match_row(name, rows)


def fundamental_pair(m, league):
    """规则79：跨联赛用欧冠级别基准，λ 只来自各队国内积分榜。"""
    prof_key = LEAGUE_PROFILE_KEY.get(league, 'default')
    from lottery_agent.config import LEAGUE_PROFILES
    prof = LEAGUE_PROFILES[prof_key]
    per_side = prof['avg_goals'] / 2.0

    hrow = team_row(m['home'])
    arow = team_row(m['away'])
    missing = []
    if hrow is None:
        missing.append(m['home'])
        hrow = {'team': m['home'], 'played': 0,
                'avg_goals_scored': per_side, 'avg_goals_conceded': per_side}
    if arow is None:
        missing.append(m['away'])
        arow = {'team': m['away'], 'played': 0,
                'avg_goals_scored': per_side, 'avg_goals_conceded': per_side}
    # 跨联赛：table_rows=None，用赛事级别 avg_goals 作基准
    res = fundamental_lambdas(hrow, arow, prof_key, table_rows=None,
                              home_advantage=prof['home_advantage'])
    res['missing'] = missing
    return res


def de_vig(odds):
    inv = {k: 1.0 / v for k, v in odds.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}


def tier_of(p01, p23, p45, p6, top2b):
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
        market = {'home': 1/3, 'draw': 1/3, 'away': 1/3}
        shin_probs = [1/3, 1/3, 1/3]
        src = '无HAD盘'

    # 规则79：λ 只来自基本面
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
    # 规则79：shin/mkt 权重归零
    W = {'dc': 0.34, 'nb': 0.22, 'zip': 0.13, 'sk': 0.14, 'mc': 0.17, 'shin': 0.0, 'mkt': 0.0}
    fused = {}
    for k in HAD_ORDER:
        fused[k] = (W['dc'] * dc_p[k] + W['nb'] * nb_p[k] + W['zip'] * zip_p[k] + W['sk'] * skp[k]
                    + W['mc'] * mc_p[k])

    if league in LEAGUE_SHIFT:
        dh, dd = LEAGUE_SHIFT[league]
        fused['home'] += dh / 100.0
        fused['draw'] += dd / 100.0
        fused['away'] -= (dh + dd) / 100.0
    for k in HAD_ORDER:
        fused[k] = max(fused[k], 0.01)
    s = sum(fused.values())
    fused = {k: v / s for k, v in fused.items()}

    # 规则63 单关平局上修
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
    band = sorted([(i, i - kr, matrix[i, i - kr]) for i in range(26)
                   if 0 <= i - kr < 26 and i < n and 0 <= i - kr < n], key=lambda x: -x[2])

    # 让球（规则52a：无条件净胜球众数）
    gl = (m['hhad'] or {}).get('goalLine')
    hh_model = hh_market = hh_odds = None
    hc_first = hc_second = ''
    if m['hhad'] and gl is not None:
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
        hh_draw_prob = gd.get(-gl, 0.0)
        combo = {k: 0.5 * hh_model[k] + 0.5 * (hh_market.get(k, 0)) for k in HAD_ORDER}
        rest = sorted([k for k in HAD_ORDER if k != hc_first], key=lambda k: -combo[k])
        hc_second = rest[0]
        if hh_draw_prob >= 0.20 and 'draw' not in (hc_first, hc_second):
            hc_second = 'draw'

    # 规则66 半场平局率：取两队国内联赛较高一方
    ht_home = TEAM_HT.get(m['home'], 0.40)
    ht_away = TEAM_HT.get(m['away'], 0.40)
    ht_draw = max(ht_home, ht_away)
    hr = 0.38 if ht_draw >= 0.40 else (0.42 if ht_draw >= 0.35 else 0.45)
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
        top2 = sorted(top2 + [alt[0]], key=lambda k: -tg[k])[:2] if tg[alt[0]] > tg[top2[1]] else [top2[0], alt[0]]
    if p6 >= 0.25 and not any(k >= 5 for k in top2):
        alt = max([(k, v) for k, v in tg.items() if k >= 5], key=lambda x: x[1])
        top2 = [top2[0], alt[0]]
    top2 = sorted(set(top2), key=lambda k: -tg[k])[:2]
    tier = tier_of(p01, p23, p45, p6, max(top2))

    ttg_odds = {o['key']: o['odds'] for o in m['ttg']}
    hafu_odds = {o['key']: o['odds'] for o in m['hafu']}
    crs_odds = {o['key']: o['odds'] for o in m['crs']}

    top_scores = sorted([(i, j, matrix[i, j]) for i in range(n) for j in range(n)], key=lambda x: -x[2])[:8]

    # 规则66：高半场平局联赛首选必须含"平"
    ht3 = htft_cn[:]
    if ht_draw >= 0.40:
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
        'ht_draw_rate': round(ht_draw, 3),
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
        lines.append('   让(%s) 首选%s 次选%s｜让平%.1f%%' % (
            r['hhad_line'], r['hc_first'], r['hc_second'],
            (r['hhad_draw_prob'] or 0) * 100))
        lines.append('   k_dist=%+d(%.1f%%) k_rec=%+d(%.1f%%) %s 带内=%s' % (
            r['k_dist'], r['k_dist_prob'] * 100, r['k_rec'], r['k_rec_prob'] * 100,
            '一致' if r['k_consistent'] else '分歧', [('%d-%d' % (a, b), round(p * 100, 1)) for a, b, p in r['band'][:3]]))
        lines.append('   TTG %s | 0-1球%.0f%% 2-3球%.0f%% 4-5球%.0f%% 6+球%.0f%% | %s' % (
            r['ttg_top2'], r['p01'] * 100, r['p23'] * 100, r['p45'] * 100, r['p6'] * 100, r['tier']))
        lines.append('   半全场 %s' % [(k, round(v * 100, 1)) for k, v in r['htft_top3']])
    io.open('reports/data/20261022_model_log.txt', 'w', encoding='utf-8').write('\n'.join(lines))
    print('\n'.join(lines))
    print('saved', OUT)


if __name__ == '__main__':
    main()
