# -*- coding: utf-8 -*-
"""
2026-10-27（周二）竞彩10场 模型计算 v2（审核返工版）

相对 v1 的修正：
  1. 新增第1/2步真实信息（身价/伤停/场地/天气/交锋）→ reports/data/20261027_info.json
  2. 规则65：身价差≥2倍 / λ差≥0.8 / 排名差≥8 触发大球上修（按身价份额分配，Tier 分级）
  3. 规则12：历史交锋比分驱动，同主客权重最高（lam_shift 由总控裁决）
  4. 规则66：半全场 TOP3 改为按概率降序（不再强行把"平"排第一）
  5. 规则74：大小球档位与 TOP2 球数强制自洽
  6. 规则55：让球次选不得与首选构成 H/A 对立
  7. FMT-8：比分 TOP5 方向覆盖校验（某方向≥15%必须在 TOP5 出现）
  8. 规则79：λ 仍只用基本面，赔率仅去水对照（禁止反解）

输出：reports/data/20261027_model_output.json
"""
import sys, json, io, os
sys.path.insert(0, r'e:\VibeCoding\football')
import numpy as np
from scipy import stats as sp_stats
from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, OddsCalibrator, HTFTModel)
from lottery_agent.fundamental import fundamental_lambdas
from lottery_agent.config import LEAGUE_PROFILES

SRC = 'reports/data/20261027_matches.json'
INFO = 'reports/data/20261027_info.json'
OUT = 'reports/data/20261027_model_output.json'

LEAGUE_PROFILE_KEY = {
    '亚冠精英': '欧冠',
    '德国杯': 'default',
    '意甲': '意甲',
    '瑞超': '瑞超',
}

# 规则65 三级框架：Tier1(Big5) +0.15 / Tier2(甲级) +0.30 / Tier3(次级·跨联赛) +0.40
LEAGUE_TIER65 = {
    '意甲': 1, '德国杯': 1,
    '瑞超': 2,
    '亚冠精英': 3,
}

TEAM_HT = {
    '京都不死鸟': 0.534, '纽卡斯尔喷气机': None,
    '大田市民': 0.512, '神户胜利船': 0.534,
    '北京国安': None, '全北现代': 0.512,
    '汉堡': 0.359, '法兰克福': 0.359,
    '萨索洛': 0.409, '拉齐奥': 0.409,
    'AIK索尔纳': 0.413, '埃尔夫斯堡': 0.413,
    '多特蒙德': 0.359, '云达不来梅': 0.359,
    '科隆': 0.359, '柏林联合': 0.359,
    '罗马': 0.409, '卡利亚里': 0.409,
    '都灵': 0.409, '科莫': 0.409,
}

SINGLE = set()
LEAGUE_SHIFT = {}

HAD_ORDER = ['home', 'draw', 'away']
NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}

TABLE_FILE = {
    '意甲': 'table_italy1.json', '瑞超': 'table_sweden1.json',
    '德甲': 'table_germany1.json', '日职': 'table_japan1.json',
    '韩职': 'table_korea1.json',
}

TEAM_LEAGUE = {
    '京都不死鸟': '日职', '纽卡斯尔喷气机': None,
    '大田市民': '韩职', '神户胜利船': '日职',
    '北京国安': None, '全北现代': '韩职',
    '汉堡': '德甲', '法兰克福': '德甲',
    '萨索洛': '意甲', '拉齐奥': '意甲',
    'AIK索尔纳': '瑞超', '埃尔夫斯堡': '瑞超',
    '多特蒙德': '德甲', '云达不来梅': '德甲',
    '科隆': '德甲', '柏林联合': '德甲',
    '罗马': '意甲', '卡利亚里': '意甲',
    '都灵': '意甲', '科莫': '意甲',
}

TEAM_ALIAS = {
    '京都不死鸟': 'Kyoto', '纽卡斯尔喷气机': None,
    '大田市民': 'Daejeon', '神户胜利船': 'Vissel Kobe',
    '北京国安': None, '全北现代': 'Jeonbuk',
    '汉堡': 'Hamburger SV', '法兰克福': 'Eintracht Frankfurt',
    '萨索洛': 'Sassuolo', '拉齐奥': 'Lazio',
    'AIK索尔纳': 'AIK', '埃尔夫斯堡': 'Elfsborg',
    '多特蒙德': 'Dortmund', '云达不来梅': 'Werder Bremen',
    '科隆': 'FC Koln', '柏林联合': 'Union Berlin',
    '罗马': 'AS Roma', '卡利亚里': 'Cagliari',
    '都灵': 'Torino', '科莫': 'Como',
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


def fundamental_pair(m, league):
    prof_key = LEAGUE_PROFILE_KEY.get(league, 'default')
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

    res = fundamental_lambdas(hrow, arow, prof_key, table_rows=table_rows,
                              home_advantage=prof['home_advantage'])
    res['missing'] = missing
    res['profile_key'] = prof_key
    return res


def de_vig(odds):
    inv = {k: 1.0 / v for k, v in odds.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}


def rule65(lh, la, info, m, league):
    """规则65：实力差距大 → 大球上修。返回 (lh, la, 触发说明)。"""
    vh, va = info['value']['home'], info['value']['away']
    ratio = max(vh, va) / min(vh, va)
    lam_gap = abs(lh - la)
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
    if rank_gap >= 8:
        triggers.append('排名差%d位' % rank_gap)

    if not triggers:
        return lh, la, None

    tier = LEAGUE_TIER65.get(league, 1)
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
    """规则46 简化：概率主导，分歧/交锋空白/伤停做降级。"""
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

    fund = fundamental_pair(m, league)
    lh, la = fund['lambda_home'], fund['lambda_away']

    # 规则65
    lh, la, r65 = rule65(lh, la, info, m, league)
    # 规则12 交锋修正
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

    if league in LEAGUE_SHIFT:
        dh, dd = LEAGUE_SHIFT[league]
        fused['home'] += dh / 100.0
        fused['draw'] += dd / 100.0
        fused['away'] -= (dh + dd) / 100.0
    fused = {k: max(v, 0.01) for k, v in fused.items()}
    s = sum(fused.values())
    fused = {k: v / s for k, v in fused.items()}

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

    # 规则52a 让球：无条件净胜球众数
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
        # 规则55：次选不得与首选 H/A 对立
        combo = {k: 0.5 * hh_model[k] + 0.5 * (hh_market.get(k, 0)) for k in HAD_ORDER}
        if hc_first == 'home':
            pool = ['draw']
        elif hc_first == 'away':
            pool = ['draw']
        else:
            pool = ['home', 'away']
        hc_second = sorted(pool, key=lambda k: -combo[k])[0]
        # 让平概率≥20% 且未入选时提为次选
        if gd.get(-gl, 0.0) >= 0.20 and 'draw' not in (hc_first, hc_second):
            hc_second = 'draw'

    ht_home = TEAM_HT.get(m['home'])
    ht_away = TEAM_HT.get(m['away'])
    ht_home = ht_home if ht_home is not None else 0.40
    ht_away = ht_away if ht_away is not None else 0.40
    ht_draw = max(ht_home, ht_away)
    hr = 0.38 if ht_draw >= 0.40 else (0.42 if ht_draw >= 0.35 else 0.45)
    htft = HTFTModel(dc)
    htft.ht_ratio = hr
    ht_res = htft.predict(lh, la)
    htft_cn = [(HAFU_CN.get(str(r['code']).replace('/', ''), r['htft']), r['probability'])
               for r in ht_res]
    htft_cn = sorted(htft_cn, key=lambda x: -x[1])  # 规则66修正：按概率降序
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
    # 规则53：比分首选 0-0 → TTG 必须含 0 球
    raw_scores = sorted([(i, j, matrix[i, j]) for i in range(n) for j in range(n)],
                        key=lambda x: -x[2])
    if raw_scores[0][0] == 0 and raw_scores[0][1] == 0 and 0 not in top2:
        top2 = [0, top2[0]]
    tier, over = tier_of(top2[0], p01, p6, p_over25)

    # FMT-8 #4：方向概率≥15% 必须在比分TOP5出现
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
    h2h_blank = '空白' in info['h2h']['summary']
    stars = conf_stars(sf[0][1], div, h2h_blank, inj_sum)

    return {
        'num': num, 'league': league, 'home': m['home'], 'away': m['away'],
        'home_rank': m['home_rank'], 'away_rank': m['away_rank'], 'time': m['time'],
        'is_single': num in SINGLE, 'had_source': src,
        'value': info['value'], 'injury': info['injury'],
        'venue': info['venue'], 'weather': info['weather'], 'h2h': info['h2h'],
        'rule65': r65, 'h2h_shift': [dsh, dsa],
        'odds_had': ({o['key']: o['odds'] for o in m['had']} if m['had'] else None),
        'odds_hhad': hh_odds, 'hhad_line': gl, 'odds_ttg': ttg_odds,
        'odds_hafu': hafu_odds, 'odds_crs': crs_odds,
        'market': {k: round(v, 4) for k, v in market.items()},
        'shin': [round(p, 4) for p in shin_probs],
        'lambda_home': round(lh, 3), 'lambda_away': round(la, 3),
        'lambda_total': round(lh + la, 3), 'lambda_base': [round(fund['lambda_home'], 3), round(fund['lambda_away'], 3)],
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
        lines.append('%s %s vs %s [%s] 身价%.2fM/%.2fM(%.2f倍)' % (
            r['num'], r['home'], r['away'], r['league'], vh / 1e6, va / 1e6, ratio))
        lines.append('   λ %.2f/%.2f(总%.2f) 基准%.2f/%.2f｜%s' % (
            r['lambda_home'], r['lambda_away'], r['lambda_total'],
            r['lambda_base'][0], r['lambda_base'][1], r['rule65'] or '规则65未触发'))
        lines.append('   融合 主%.1f/平%.1f/客%.1f → %s(%.1f) / %s(%.1f)  分歧%.0fpp  %s' % (
            r['fused']['home'] * 100, r['fused']['draw'] * 100, r['fused']['away'] * 100,
            NAME_CN[r['primary']], r['primary_prob'] * 100,
            NAME_CN[r['secondary']], r['secondary_prob'] * 100,
            r['diverge'] * 100, r['conf']))
        lines.append('   让(%s) %s / %s' % (r['hhad_line'], NAME_CN.get(r['hc_first'], r['hc_first']),
                                          NAME_CN.get(r['hc_second'], r['hc_second'])))
        lines.append('   k_dist=%+d(%.1f%%) k_rec=%+d(%.1f%%) %s' % (
            r['k_dist'], r['k_dist_prob'] * 100, r['k_rec'], r['k_rec_prob'] * 100,
            '一致' if r['k_consistent'] else '分歧'))
        lines.append('   TTG %s %s(%s) 0-1球%.0f%% 2-3球%.0f%% 4-5球%.0f%% 6+%.0f%%' % (
            r['ttg_top2'], r['tier'], r['over_under'],
            r['p01'] * 100, r['p23'] * 100, r['p45'] * 100, r['p6'] * 100))
        lines.append('   半全场 %s' % [(k, round(v * 100, 1)) for k, v in r['htft_top3']])
    io.open('reports/data/20261027_model_log.txt', 'w', encoding='utf-8').write('\n'.join(lines))
    print('\n'.join(lines))
    print('\nsaved', OUT)


if __name__ == '__main__':
    main()
