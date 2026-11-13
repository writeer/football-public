# -*- coding: utf-8 -*-
"""
2026-10-30（周五）竞彩12场 模型计算

链路（规则79）：积分榜场均进失球 → 攻击/防守强度（按场次收缩）→ 守恒式 λ → DC/NB/ZIP/Skellam/MC → 加权融合
赔率只做 de-vig 对照、分歧，不参与 λ 求解。

本日要点：
  1. 规则63：用户告知周五007 埃尔沃斯堡vs美因茨 开胜平负单关 → 平局上修
  2. 规则65：实力差距大球上修（德甲/法甲/西甲 Tier1，挪超/葡超/巴甲 Tier2，德乙/荷乙/英冠/澳超 Tier3）
  3. 规则66：半场平局率按联赛 ht_draw_rate
  4. 规则69：法甲非PSG场次平局上修（003尼斯vs雷恩、010里尔vs朗斯；004涉PSG不上修）
  5. 规则74：大小球六档自洽
  6. 规则72：12场均无空场/中立场公告 → 主场加成全额

输出：reports/data/20261030_model_output.json + 20261030_model_log.txt
"""
import sys, json, io, os
sys.path.insert(0, r'e:\VibeCoding\football')
import numpy as np
from scipy import stats as sp_stats
from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, OddsCalibrator, HTFTModel)
from lottery_agent.fundamental import fundamental_lambdas
from lottery_agent.config import LEAGUE_PROFILES, resolve_home_advantage

SRC = 'reports/data/20261030_matches.json'
INFO = 'reports/data/20261030_info.json'
OUT = 'reports/data/20261030_model_output.json'
LOG = 'reports/data/20261030_model_log.txt'

LEAGUE_PROFILE_KEY = {
    '澳超': 'default', '德乙': 'default', '荷乙': 'default',
    '法甲': '法甲', '挪超': '挪超', '德甲': '德甲',
    '英冠': '英冠', '西甲': '西甲', '葡超': '葡超', '巴甲': '巴甲',
}

# 规则65 层级：0=不上修（英超例外）/1=Big5 /2=顶级非Big5 /3=次级·跨联赛
LEAGUE_TIER65 = {
    '德甲': 1, '法甲': 1, '西甲': 1,
    '挪超': 2, '葡超': 2, '巴甲': 2,
    '澳超': 3, '德乙': 3, '荷乙': 3, '英冠': 3,
}

# 规则66 半场平局率（按联赛/赛事）
HT_RATE = {
    '澳超': 0.40, '德乙': 0.392, '法甲': 0.393, '挪超': 0.325,
    '荷乙': 0.358, '德甲': 0.359, '英冠': 0.425, '西甲': 0.441,
    '葡超': 0.414, '巴甲': 0.40,
}

SINGLE = {'周五007'}   # 规则63：用户告知开胜平负单关
# 规则69：法甲非PSG场次平局上修（按场次），值为平局上修比例（主/客按原比例压缩）
LEAGUE_SHIFT = {'周五003': 0.06, '周五010': 0.07}

# 规则9/28/27：基本面修正（伤停/战意/体能/等级差）——乘数作用于攻击λ
ADJUST = {
    '周五001': {'lh': 0.98, 'la': 1.03},   # 奥克兰卫冕冠军+交锋4战不败，狮吼1人伤缺
    '周五002': {'lh': 0.98, 'la': 0.88},   # 波鸿5人缺阵含3名后场，科特布斯2人缺阵
    '周五003': {'lh': 0.90, 'la': 0.93},   # 尼斯后防4缺1疑；雷恩失头号射手Lepaul、门将成疑
    '周五004': {'lh': 0.95, 'la': 0.97},   # HAC 5人缺阵含两中卫+门将；PSG 3主力缺阵但深度足
    '周五005': {'lh': 1.00, 'la': 1.00},   # 双方各4人长期伤号，均接近最强
    '周五006': {'lh': 1.03, 'la': 0.98},   # 福伦丹主场强、格拉夫夏普客场防守失误多
    '周五007': {'lh': 0.92, 'la': 0.92},   # 埃尔沃斯堡4缺(右后卫/中卫/边锋/前腰)；美因茨3缺+Amiri成疑
    '周五008': {'lh': 0.96, 'la': 0.90},   # 雷克斯汉姆5人缺阵(两左路+两前锋+中场)，谢菲联3缺
    '周五009': {'lh': 1.00, 'la': 0.95},   # 西班牙人换帅动荡+2人缺阵；黄潜2缺2疑
    '周五010': {'lh': 0.93, 'la': 0.92, 'dt': -0.10},  # 双方各4人缺阵、德比低比分
    '周五011': {'lh': 0.98, 'la': 0.96},   # 卡萨皮亚1缺；葡体3缺+双线两连败
    '周五012': {'lh': 0.88, 'la': 0.95, 'dt': -0.10},  # 科林蒂安6人缺阵含锋线双核停伤+保级闷战
}

HAD_ORDER = ['home', 'draw', 'away']
NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}

TABLE_FILE = {
    '澳超': 'table_australia.json', '德乙': 'table_germany2.json',
    '法甲': 'table_france1.json', '挪超': 'table_norway.json',
    '荷乙': 'table_holland2.json', '德甲': 'table_germany1.json',
    '英冠': 'table_championship.json', '西甲': 'table_spain1.json',
    '葡超': 'table_portugal1.json', '巴甲': 'table_brazil1.json',
}

TEAM_LEAGUE = {
    '布里斯班狮吼': '澳超', '奥克兰FC': '澳超',
    '科特布斯': '德乙', '波鸿': '德乙',
    '尼斯': '法甲', '雷恩': '法甲',
    '勒阿弗尔': '法甲', '巴黎圣日尔曼': '法甲',
    '博德闪耀': '挪超', '维京': '挪超',
    '福伦丹': '荷乙', '格拉夫夏普': '荷乙',
    '埃尔沃斯堡': '德甲', '美因茨': '德甲',
    '谢菲尔德联': '英冠', '雷克斯汉姆': '英冠',
    '比利亚雷亚尔': '西甲', '西班牙人': '西甲',
    '里尔': '法甲', '朗斯': '法甲',
    '卡萨皮亚': '葡超', '里斯本竞技': '葡超',
    '科林蒂安': '巴甲', '米拉索尔': '巴甲',
}

TEAM_ALIAS = {
    '布里斯班狮吼': 'Brisbane Roar', '奥克兰FC': 'Auckland FC',
    '科特布斯': 'Cottbus', '波鸿': 'Bochum',
    '尼斯': 'Nice', '雷恩': 'Rennes',
    '勒阿弗尔': 'Le Havre', '巴黎圣日尔曼': 'PSG',
    '博德闪耀': 'Bodo/Glimt', '维京': 'Viking',
    '福伦丹': 'FC Volendam', '格拉夫夏普': 'De Graafschap',
    '埃尔沃斯堡': 'Elversberg', '美因茨': 'Mainz',
    '谢菲尔德联': 'Sheffield Utd', '雷克斯汉姆': 'Wrexham',
    '比利亚雷亚尔': 'Villarreal', '西班牙人': 'Espanyol',
    '里尔': 'Lille', '朗斯': 'Lens',
    '卡萨皮亚': 'Casa Pia', '里斯本竞技': 'Sporting CP',
    '科林蒂安': 'Corinthians', '米拉索尔': 'Mirassol',
}

_TABLE_CACHE = {}


def load_table(league):
    if league in _TABLE_CACHE:
        return _TABLE_CACHE[league]
    fn = TABLE_FILE.get(league)
    rows = None
    p = os.path.join('reports/data', fn) if fn else None
    if p and os.path.exists(p):
        with open(p, encoding='utf-8-sig') as f:
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
    lg = TEAM_LEAGUE.get(name)
    if not lg:
        return None
    return match_row(name, load_table(lg))


def fundamental_pair(m, league, info):
    prof_key = LEAGUE_PROFILE_KEY.get(league, league)
    if prof_key not in LEAGUE_PROFILES:
        prof_key = 'default'
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

    lg_h, lg_a = TEAM_LEAGUE.get(m['home']), TEAM_LEAGUE.get(m['away'])
    table_rows = None
    if lg_h and lg_a and lg_h == lg_a and lg_h in TABLE_FILE:
        table_rows = load_table(lg_h)

    # 规则72：场地状态 → 主场加成覆盖
    status = (info.get('venue') or {}).get('status', '正常')
    ratio = 0.5 if status == '部分关闭' else None
    ha = resolve_home_advantage(prof_key, stadium_status=status, closure_ratio=ratio)

    res = fundamental_lambdas(hrow, arow, prof_key, table_rows=table_rows,
                              home_advantage=ha['factor'])
    res['missing'] = missing
    res['profile_key'] = prof_key
    res['stadium'] = ha
    return res


def de_vig(odds):
    inv = {k: 1.0 / v for k, v in odds.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}


def rule65(lh, la, info, m, league):
    vh, va = info['value']['home'], info['value']['away']
    ratio = max(vh, va) / min(vh, va)
    lam_gap = abs(lh - la)
    gl = (m.get('hhad') or {}).get('goalLine')
    hr = m.get('home_rank') or ''
    ar = m.get('away_rank') or ''
    rank_gap = 0
    try:
        rh = int(''.join(ch for ch in hr if ch.isdigit()) or 0)
        ra = int(''.join(ch for ch in ar if ch.isdigit()) or 0)
        if rh and ra:
            rank_gap = abs(rh - ra)
    except Exception:
        rank_gap = 0

    triggers = []
    if ratio >= 2.0:
        triggers.append('身价差%.2f倍' % ratio)
    if lam_gap >= 0.8:
        triggers.append('λ差%.2f' % lam_gap)
    if gl is not None and abs(gl) >= 1:
        triggers.append('让球盘%.0f球' % abs(gl))
    if rank_gap >= 8:
        triggers.append('排名差%d位' % rank_gap)

    if not triggers:
        return lh, la, None

    tier = LEAGUE_TIER65.get(league, 1)
    if tier == 0:
        return lh, la, '触发（%s）但英超系按规则65例外不上修' % '、'.join(triggers)
    bump = {1: 0.15, 2: 0.30, 3: 0.40}[tier]
    if ratio >= 2.0:
        bump += 0.05
    share_h = vh / (vh + va)
    lh2 = lh + bump * share_h
    la2 = la + bump * (1 - share_h)
    note = 'Tier%d +%.2f球；触发项：%s；按身价份额分配（主%.0f%%/客%.0f%%）' % (
        tier, bump, '、'.join(triggers), share_h * 100, (1 - share_h) * 100)
    return lh2, la2, note


def tier_of(top1, p01, p6, p_over25):
    if p6 >= 0.25:
        name = '穿盘可能(6-7+球)'
    elif p01 >= 0.40:
        name = '闷战超小球(0-1球)'
    elif top1 <= 1:
        name = '小球(1-2球)'
    elif top1 in (2, 3):
        name = '常规正常球(2-3球)'
    elif top1 == 4:
        name = '大球(4-5球)'
    elif top1 == 5:
        name = '超大球(5-6球)'
    else:
        name = '穿盘可能(6-7+球)'
    return name, ('大' if p_over25 > 0.5 else '小')


def conf_stars(p, div, h2h_blank, inj_sum):
    score = 0
    if p >= 0.60:
        score += 2
    elif p >= 0.50:
        score += 1
    if div <= 0.08:
        score += 1
    elif div > 0.20:
        score -= 1
    if h2h_blank:
        score -= 1
    if inj_sum >= 10:
        score -= 1
    if score >= 3:
        return '★★★'
    if score >= 1:
        return '★★'
    if score >= 0:
        return '★'
    return '☆'


def analyze(m, info):
    num, league = m['num'], m['league']
    if m['had']:
        odds = {o['key']: o['odds'] for o in m['had']}
        market = de_vig(odds)
        shin = OddsCalibrator(odds['home'], odds['draw'], odds['away']).shin()
        shin_probs = [shin['home'], shin['draw'], shin['away']]
        src = 'HAD去水'
    else:
        market = {'home': 1 / 3, 'draw': 1 / 3, 'away': 1 / 3}
        shin_probs = [1 / 3, 1 / 3, 1 / 3]
        src = '无HAD盘'

    fund = fundamental_pair(m, league, info)
    lh, la = fund['lambda_home'], fund['lambda_away']

    adj = ADJUST.get(num, {})
    lh *= adj.get('lh', 1.0)
    la *= adj.get('la', 1.0)
    if adj.get('dt'):
        tot = lh + la
        lh += adj['dt'] * lh / tot
        la += adj['dt'] * la / tot

    lh, la, r65 = rule65(lh, la, info, m, league)
    dsh, dsa = info['h2h'].get('lam_shift', [0.0, 0.0])
    lh = max(0.15, lh + dsh)
    la = max(0.15, la + dsa)

    dc = DixonColesModel()
    nb = NegativeBinomialModel()
    zp = ZIPModel()
    sk = SkellamModel()
    mc = MonteCarloSimulator(n_sim=20000)
    dc_p = dc.outcome_probs(lh, la)
    nb_p = nb.outcome_probs(lh, la)
    zip_p = zp.outcome_probs(lh, la)
    skp = sk.outcome_probs(lh, la)
    mcr = mc.simulate(lh, la)
    mc_p = {'home': mcr['home_win'], 'draw': mcr['draw'], 'away': mcr['away_win']}

    W = {'dc': 0.34, 'nb': 0.22, 'zip': 0.13, 'sk': 0.14, 'mc': 0.17}
    fused = {k: (W['dc'] * dc_p[k] + W['nb'] * nb_p[k] + W['zip'] * zip_p[k]
                 + W['sk'] * skp[k] + W['mc'] * mc_p[k]) for k in HAD_ORDER}

    # 规则69：法甲非PSG场次平局上修（上修量来自平局，主胜/客胜按原比例压缩）
    r69 = None
    if num in LEAGUE_SHIFT:
        base = dict(fused)
        add = base['draw'] * LEAGUE_SHIFT[num]
        fused['draw'] = base['draw'] + add
        rest = base['home'] + base['away']
        fused['home'] = base['home'] * (1 - add / rest)
        fused['away'] = base['away'] * (1 - add / rest)
        r69 = '法甲平局上修 %.0f%%（平 %.1f%%→%.1f%%）' % (
            LEAGUE_SHIFT[num] * 100, base['draw'] * 100, fused['draw'] * 100)

    # 规则63：单关平局上修
    r63 = None
    if num in SINGLE:
        base = dict(fused)
        gap = max(base['home'], base['away']) - base['draw']
        if gap <= 0.10:
            amp = 0.13
        elif gap <= 0.20:
            amp = 0.11
        else:
            amp = 0.08
        add = base['draw'] * amp
        fused['draw'] = base['draw'] + add
        rest = base['home'] + base['away']
        fused['home'] = base['home'] * (1 - add / rest)
        fused['away'] = base['away'] * (1 - add / rest)
        r63 = '单关平局上修 %.0f%%（原平%.1f%%→%.1f%%，距首选%.1fpp）' % (
            amp * 100, base['draw'] * 100, fused['draw'] * 100, gap * 100)

    fused = {k: max(v, 0.01) for k, v in fused.items()}
    s = sum(fused.values())
    fused = {k: v / s for k, v in fused.items()}
    if r63:
        r63 = '单关平局上修 %.0f%%（原平%.1f%%→%.1f%%，距首选%.1fpp）' % (
            amp * 100, base['draw'] * 100, fused['draw'] * 100, gap * 100)

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
        adj_net = k_dist[0] + gl
        hc_first = 'home' if adj_net > 0 else ('draw' if adj_net == 0 else 'away')
        combo = {k: 0.5 * hh_model[k] + 0.5 * (hh_market.get(k, 0)) for k in HAD_ORDER}
        if hc_first == 'home':
            pool = ['draw']
        elif hc_first == 'away':
            pool = ['draw']
        else:
            pool = ['home', 'away']
        hc_second = sorted(pool, key=lambda k: -combo[k])[0]
        if gd.get(-gl, 0.0) >= 0.20 and 'draw' not in (hc_first, hc_second):
            hc_second = 'draw'

    ht_draw = HT_RATE.get(league, 0.40)
    hr = 0.38 if ht_draw >= 0.40 else (0.42 if ht_draw >= 0.35 else 0.45)
    htft = HTFTModel(dc)
    htft.ht_ratio = hr
    ht_res = htft.predict(lh, la)
    htft_cn = [(HAFU_CN.get(str(r['code']).replace('/', ''), r['htft']), r['probability'])
               for r in ht_res]
    htft_cn = sorted(htft_cn, key=lambda x: -x[1])
    dest = ('平胜', '平平', '平负')
    if ht_draw >= 0.40 and not any(k in dest for k, _ in htft_cn[:3]):
        best_draw = max([(k, v) for k, v in htft_cn if k in dest], key=lambda x: x[1])
        htft_cn = sorted(htft_cn[:2] + [best_draw], key=lambda x: -x[1])
    ht3 = htft_cn[:3]

    mat_ht = dc.compute_matrix(lh * hr, la * hr)
    ht_scores = sorted([(i, j, mat_ht[i, j]) for i in range(4) for j in range(4)],
                       key=lambda x: -x[2])[:3]

    p01 = sum(v for k, v in tg.items() if k <= 1)
    p23 = sum(v for k, v in tg.items() if k in (2, 3))
    p45 = sum(v for k, v in tg.items() if k in (4, 5))
    p6 = sum(v for k, v in tg.items() if k >= 6)
    p_over25 = sum(v for k, v in tg.items() if k >= 3)

    ttg_top = sorted(tg.items(), key=lambda x: -x[1])[:6]
    top2 = [ttg_top[0][0], ttg_top[1][0]]
    raw_scores = sorted([(i, j, matrix[i, j]) for i in range(n) for j in range(n)],
                        key=lambda x: -x[2])
    if raw_scores[0][0] == 0 and raw_scores[0][1] == 0 and 0 not in top2:
        top2 = [0, top2[0]]
    tier, over = tier_of(top2[0], p01, p6, p_over25)

    top5 = raw_scores[:5]
    for dname in HAD_ORDER:
        if fused[dname] >= 0.15:
            ok = False
            for a, b, _ in top5:
                dv = 'home' if a > b else ('away' if a < b else 'draw')
                if dv == dname:
                    ok = True
                    break
            if not ok:
                cand_s = [x for x in raw_scores if
                          (('home' if x[0] > x[1] else ('away' if x[0] < x[1] else 'draw')) == dname)]
                if cand_s:
                    top5 = top5[:4] + [cand_s[0]]

    ttg_odds = {o['key']: o['odds'] for o in m['ttg']} if m['ttg'] else {}
    hafu_odds = {o['key']: o['odds'] for o in m['hafu']} if m['hafu'] else {}
    crs_odds = {o['key']: o['odds'] for o in m['crs']} if m['crs'] else {}

    div = max(abs(fused[k] - market[k]) for k in HAD_ORDER)
    inj_sum = info['injury']['home_count'] + info['injury']['away_count']
    h2h_blank = '空白' in info['h2h']['summary'] or '首次' in info['h2h']['summary']
    stars = conf_stars(sf[0][1], div, h2h_blank, inj_sum)

    return {
        'num': num, 'league': league, 'home': m['home'], 'away': m['away'],
        'home_rank': m['home_rank'], 'away_rank': m['away_rank'], 'time': m['time'],
        'is_single': num in SINGLE, 'rule63': r63, 'rule69': r69,
        'had_source': src,
        'value': info['value'], 'injury': info['injury'],
        'venue': info['venue'], 'weather': info['weather'], 'h2h': info['h2h'],
        'rule65': r65, 'h2h_shift': [dsh, dsa],
        'stadium': fund['stadium'],
        'odds_had': ({o['key']: o['odds'] for o in m['had']} if m['had'] else None),
        'odds_hhad': hh_odds, 'hhad_line': gl, 'odds_ttg': ttg_odds,
        'odds_hafu': hafu_odds, 'odds_crs': crs_odds,
        'market': {k: round(v, 4) for k, v in market.items()},
        'shin': [round(p, 4) for p in shin_probs],
        'lambda_home': round(lh, 3), 'lambda_away': round(la, 3),
        'lambda_total': round(lh + la, 3),
        'lambda_base': [round(fund['lambda_home'], 3), round(fund['lambda_away'], 3)],
        'lambda_source': 'fundamental(rule79)',
        'lambda_basis': fund['basis'], 'league_avg_goals': round(fund['league_avg'], 3),
        'atk_home': round(fund['atk_home'], 3), 'def_home': round(fund['def_home'], 3),
        'atk_away': round(fund['atk_away'], 3), 'def_away': round(fund['def_away'], 3),
        'table_missing': fund['missing'], 'profile_key': fund.get('profile_key', ''),
        'dc': {k: round(v, 4) for k, v in dc_p.items()},
        'fused': {k: round(v, 4) for k, v in fused.items()},
        'primary': primary, 'secondary': secondary,
        'primary_prob': round(sf[0][1], 4), 'secondary_prob': round(sf[1][1], 4),
        'third': sf[2][0], 'third_prob': round(sf[2][1], 4),
        'hhad_model': {k: round(v, 4) for k, v in hh_model.items()} if hh_model else None,
        'hhad_market': {k: round(v, 4) for k, v in hh_market.items()} if hh_market else None,
        'hhad_draw_prob': round(gd.get(-gl, 0.0), 4) if gl is not None else None,
        'hc_first': hc_first, 'hc_second': hc_second,
        'k_dist': k_dist[0], 'k_dist_prob': round(k_dist[1], 4),
        'k_rec': k_rec[0], 'k_rec_prob': round(k_rec[1], 4), 'k_consistent': bool(consistent),
        'band': [(a, b, round(p, 4)) for a, b, p in band[:3]],
        'top_scores': [(a, b, round(p, 4)) for a, b, p in top5],
        'tg': {str(k): round(v, 4) for k, v in sorted(tg.items()) if v > 0.0005},
        'ttg_top': [(k, round(v, 4)) for k, v in ttg_top],
        'ttg_top2': top2, 'tier': tier, 'over_under': over,
        'p01': round(p01, 4), 'p23': round(p23, 4), 'p45': round(p45, 4),
        'p6': round(p6, 4), 'p_over25': round(p_over25, 4),
        'htft': [(k, round(v, 4)) for k, v in htft_cn[:9]],
        'htft_top3': [(k, round(v, 4)) for k, v in ht3],
        'ht_scores': [(a, b, round(p, 4)) for a, b, p in ht_scores],
        'ht_draw_rate': round(ht_draw, 3),
        'diverge': round(div, 4), 'conf': stars,
    }


def main():
    ms = json.load(io.open(SRC, encoding='utf-8'))
    infos = json.load(io.open(INFO, encoding='utf-8'))
    res = [analyze(m, infos[m['num']]) for m in ms]
    json.dump(res, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    lines = []
    for r in res:
        vh, va = r['value']['home'], r['value']['away']
        ratio = max(vh, va) / min(vh, va)
        lines.append('%s %s vs %s [%s] 身价%.1fM/%.1fM(%.2f倍)%s' % (
            r['num'], r['home'], r['away'], r['league'], vh / 1e6, va / 1e6, ratio,
            ' 【单关】' if r['is_single'] else ''))
        lines.append('   λ %.2f/%.2f(总%.2f) 基准%.2f/%.2f｜%s' % (
            r['lambda_home'], r['lambda_away'], r['lambda_total'],
            r['lambda_base'][0], r['lambda_base'][1], r['rule65'] or '规则65未触发'))
        lines.append('   融合 主%.1f/平%.1f/客%.1f → %s(%.1f) / %s(%.1f)  分歧%.0fpp  %s %s' % (
            r['fused']['home'] * 100, r['fused']['draw'] * 100, r['fused']['away'] * 100,
            NAME_CN[r['primary']], r['primary_prob'] * 100,
            NAME_CN[r['secondary']], r['secondary_prob'] * 100,
            r['diverge'] * 100, r['conf'], r['rule63'] or ''))
        lines.append('   让(%s) %s / %s   异常:%s' % (
            r['hhad_line'], NAME_CN.get(r['hc_first'], r['hc_first']),
            NAME_CN.get(r['hc_second'], r['hc_second']),
            '、'.join(r['table_missing']) or '无'))
        lines.append('   k_dist=%+d(%.1f%%) k_rec=%+d(%.1f%%) %s' % (
            r['k_dist'], r['k_dist_prob'] * 100, r['k_rec'], r['k_rec_prob'] * 100,
            '一致' if r['k_consistent'] else '分歧'))
        lines.append('   TTG %s %s(%s) 0-1球%.0f%% 2-3球%.0f%% 4-5球%.0f%% 6+%.0f%%' % (
            r['ttg_top2'], r['tier'], r['over_under'],
            r['p01'] * 100, r['p23'] * 100, r['p45'] * 100, r['p6'] * 100))
        lines.append('   比分TOP5 %s' % [( '%d-%d' % (a, b), round(p * 100, 1)) for a, b, p in r['top_scores']])
        lines.append('   半全场 %s' % [(k, round(v * 100, 1)) for k, v in r['htft_top3']])
    io.open(LOG, 'w', encoding='utf-8').write('\n'.join(lines))
    print('\n'.join(lines))
    print('\nsaved', OUT)


if __name__ == '__main__':
    main()
