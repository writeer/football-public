# -*- coding: utf-8 -*-
"""2026-11-08 周日竞彩24场模型计算（L241–L245 修正版）

规则79：λ 只由积分榜基本面推导；赔率仅 de-vig 后作对照，不进入任何融合权重。
数据边界：当日只有赛程/赔率/积分榜，无身价、伤停、场地、近5场半场记录：
  - L242/L243 的身价门槛缺数据 → 以 λ 差≥1.0 替代并显式披露；
  - L244 半场领先被翻记录缺失 → 不触发，保留提示；
  - 未做规则65 身价加成，也未用让球盘反推 λ（避免市场进入 λ）。

输出：reports/data/20261108_model_output.json + 20261108_model_log.txt
"""
import io
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy import stats as sp_stats

sys.path.insert(0, r'e:\VibeCoding\football')

from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, HTFTModel)
from lottery_agent.fundamental import fundamental_lambdas
from lottery_agent.config import LEAGUE_PROFILES, HT_RATIO_DEFAULT
from lottery_agent.strategy import (fuse_outcomes, select_direction, goal_band,
                                    score_pool, htft_pool, handicap_pick,
                                    parlay_leg_eligible)

DATA = 'reports/data'
SRC = os.path.join(DATA, '20261108_matches.json')
OUT = os.path.join(DATA, '20261108_model_output.json')
LOG = os.path.join(DATA, '20261108_model_log.txt')

MAXG = 15
RHO = -0.13
SEED = 20261108

TABLE_FILE = {
    '西甲': 'table_spain1.json', '芬超': 'table_finland1.json', '荷甲': 'table_holland1.json',
    '挪超': 'table_norway.json', '英超': 'table_premier.json', '意甲': 'table_italy1.json',
    '德甲': 'table_germany1.json', '瑞超': 'table_sweden1.json', '法甲': 'table_france1.json',
    '葡超': 'table_portugal1.json',
}

TEAM_ALIAS = {
    '埃尔切': 'Elche', '皇家贝蒂斯': 'Betis', '皇家社会': 'Real Sociedad',
    '巴列卡诺': 'Rayo Vallecano', '比利亚雷亚尔': 'Villarreal', '赫塔费': 'Getafe',
    '维戈塞尔塔': 'Celta Vigo', '莱万特': 'Levante', '马德里竞技': 'Atl. Madrid',
    '巴塞罗那': 'Barcelona',
    '库奥皮奥': 'KuPS', '国际图尔库': 'Inter Turku',
    '特温特': 'Twente', '阿贾克斯': 'Ajax', '阿尔克马尔': 'AZ Alkmaar', '格罗宁根': 'Groningen',
    '特罗姆瑟': 'Tromso', '博德闪耀': 'Bodo/Glimt',
    '桑德兰': 'Sunderland', '切尔西': 'Chelsea', '伊普斯维奇': 'Ipswich',
    '伯恩茅斯': 'Bournemouth', '水晶宫': 'Crystal Palace', '利物浦': 'Liverpool',
    '曼彻斯特联': 'Manchester Utd', '阿斯顿维拉': 'Aston Villa',
    '蒙扎': 'Monza', '亚特兰大': 'Atalanta', '热那亚': 'Genoa', 'AC米兰': 'AC Milan',
    '国际米兰': 'Inter', '科莫': 'Como', '佛罗伦萨': 'Fiorentina', '尤文图斯': 'Juventus',
    '科隆': 'FC Koln', '勒沃库森': 'Bayer Leverkusen', '弗赖堡': 'Freiburg',
    '柏林联合': 'Union Berlin', '霍芬海姆': 'Hoffenheim', '沙尔克04': 'Schalke',
    'AIK索尔纳': 'AIK', '赫根': 'Hacken',
    '勒芒': 'Le Mans', '摩纳哥': 'Monaco', '朗斯': 'Lens', '马赛': 'Marseille',
    '吉马良斯': 'Vitoria Guimaraes', '波尔图': 'FC Porto',
}

# 半场平局率（沿用既有脚本口径；缺失联赛用默认 0.40）
HT_RATE = {
    '西甲': 0.441, '荷甲': 0.387, '挪超': 0.325, '英超': 0.384,
    '意甲': 0.409, '德甲': 0.359, '瑞超': 0.38, '法甲': 0.40, '葡超': 0.40,
}

NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}

_TABLE_CACHE = {}
MC = MonteCarloSimulator(n_sim=20000, seed=SEED)


def load_table(league):
    if league in _TABLE_CACHE:
        return _TABLE_CACHE[league]
    fn = TABLE_FILE.get(league)
    rows = None
    if fn and os.path.exists(os.path.join(DATA, fn)):
        with io.open(os.path.join(DATA, fn), encoding='utf-8-sig') as f:
            rows = json.load(f).get('table')
    _TABLE_CACHE[league] = rows
    return rows


def match_row(name, league):
    rows = load_table(league) or []
    key = TEAM_ALIAS.get(name, name).lower()
    for r in rows:
        if r.get('team', '').lower() == key:
            return r
    for r in rows:
        if key in r.get('team', '').lower():
            return r
    return None


def de_vig(outs):
    odds = {o['key']: o['odds'] for o in outs}
    inv = {k: 1.0 / v for k, v in odds.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}


def kickoff_dt(m):
    t = datetime.strptime(m['time'], '%H:%M:%S')
    dt = datetime.strptime(m['match_date'], '%Y-%m-%d').replace(
        hour=t.hour, minute=t.minute, second=t.second)
    if t.hour < 12:            # 竞彩跨零点场次
        dt += timedelta(days=1)
    return dt


def analyze(m, now):
    num, league = m['num'], m['league']
    hrow = match_row(m['home'], league)
    arow = match_row(m['away'], league)
    missing = []
    if hrow is None:
        missing.append(m['home'])
        hrow = {'team': m['home'], 'played': 0, 'avg_goals_scored': 1.2,
                'avg_goals_conceded': 1.2}
    if arow is None:
        missing.append(m['away'])
        arow = {'team': m['away'], 'played': 0, 'avg_goals_scored': 1.2,
                'avg_goals_conceded': 1.2}

    fund = fundamental_lambdas(hrow, arow, league, table_rows=load_table(league))
    lh, la = fund['lambda_home'], fund['lambda_away']

    prof = LEAGUE_PROFILES.get(league, LEAGUE_PROFILES['default'])
    gamma = 0.15 if prof.get('over_dispersed') else 0.10

    dc = DixonColesModel(rho=RHO)
    dc.max_goals = MAXG
    nb = NegativeBinomialModel(gamma_disp=gamma)
    nb.max_goals = MAXG
    zp = ZIPModel()
    zp.max_goals = MAXG
    sk = SkellamModel()

    dc_p = dc.outcome_probs(lh, la)
    nb_p = nb.outcome_probs(lh, la)
    zp_p = zp.outcome_probs(lh, la)
    sk_p = sk.outcome_probs(lh, la)
    mc_r = MC.simulate(lh, la, gamma_disp=gamma)
    mc_p = {'home': mc_r['home_win'], 'draw': mc_r['draw'], 'away': mc_r['away_win']}
    fused = fuse_outcomes(dc_p, nb_p, zp_p, sk_p, mc_p)

    market = de_vig(m['had']) if m.get('had') else None
    is_single = bool(m.get('betting_single'))
    sel = select_direction(fused, market, is_single=is_single)

    mat = dc.compute_matrix(lh, la)
    top_scores = sorted(((i, j, float(mat[i, j])) for i in range(MAXG) for j in range(MAXG)),
                        key=lambda x: -x[2])
    tg, gd = {}, {}
    for i in range(MAXG):
        for j in range(MAXG):
            tg[i + j] = tg.get(i + j, 0.0) + mat[i, j]
            gd[i - j] = gd.get(i - j, 0.0) + mat[i, j]

    primary = sel['primary']
    if primary == 'home':
        k_rec = max(((k, v) for k, v in gd.items() if k >= 1), key=lambda x: x[1])
    elif primary == 'away':
        k_rec = max(((k, v) for k, v in gd.items() if k <= -1), key=lambda x: x[1])
    else:
        k_rec = (0, gd.get(0, 0))
    k_dist = max(gd.items(), key=lambda x: x[1])

    p01 = sum(v for k, v in tg.items() if k <= 1)
    p23 = sum(v for k, v in tg.items() if k in (2, 3))
    p45 = sum(v for k, v in tg.items() if k in (4, 5))
    p6 = sum(v for k, v in tg.items() if k >= 6)
    p_over25 = sum(v for k, v in tg.items() if k >= 3)
    top_total = max(tg.items(), key=lambda x: x[1])[0]
    dist = {'p01': p01, 'p23': p23, 'p45': p45, 'p6': p6,
            'p_over25': p_over25, 'top_total': top_total}
    band = goal_band(lh, la, dist, league=league)

    pool = score_pool(top_scores, primary, abs(lh - la))

    line = (m.get('hhad') or {}).get('goalLine')
    hc = None
    if line is not None:
        th = -line
        hc_model = {'home': float(sk_skellam_sf(th, lh, la)),
                    'draw': float(sk_skellam_pmf(th, lh, la)),
                    'away': float(sk_skellam_cdf(th - 1, lh, la))}
        hc = handicap_pick(hc_model, line, primary, k_rec[0])
    else:
        hc_model = None

    hr = HT_RATE.get(league, HT_RATIO_DEFAULT)
    htft_model = HTFTModel(dc, ht_ratio=hr)
    htft_all = htft_model.predict(lh, la, n=9)
    htft_sorted = [(r['code'].replace('/', ''), r['probability']) for r in htft_all]
    hp = htft_pool(htft_sorted)

    market_side = max(market, key=lambda k: market[k]) if market else None
    leg = {
        'num': num, 'side': primary, 'prob': fused[primary],
        'market_side': market_side,
        'same_direction': primary == market_side if market_side else False,
        'dual': sel['dual'],
        'eligible': bool(market and parlay_leg_eligible(fused[primary], primary, market_side)),
    }
    if leg['eligible']:
        leg['note'] = 'L245① 首选%.1f%%≥55%%且模型-市场同向' % (fused[primary] * 100)
    else:
        reason = '首选%.1f%%<55%%' % (fused[primary] * 100) if fused[primary] < 0.55 else '模型-市场不同向'
        leg['note'] = 'L245① 不入方向串（%s）' % reason

    status = '已开赛' if kickoff_dt(m) <= now else '待开赛'
    notes = list(sel['notes']) + list(band['notes']) + list(pool['notes'])
    notes += hp['notes'] + (hc['notes'] if hc else [])
    notes.append('数据缺口：无身价/伤停/场地/近5场明细，未做规则65及场地修正')

    return {
        'num': num, 'league': league, 'home': m['home'], 'away': m['away'],
        'home_rank': m.get('home_rank'), 'away_rank': m.get('away_rank'),
        'time': m['time'], 'status': status, 'is_single': is_single,
        'table_missing': missing,
        'lambda_home': round(lh, 3), 'lambda_away': round(la, 3),
        'lambda_total': round(lh + la, 3),
        'lambda_base': [round(fund['lambda_home'], 3), round(fund['lambda_away'], 3)],
        'lambda_source': 'fundamental(rule79): 积分榜场均进失球+守恒式λ',
        'league_avg': round(fund['league_avg'], 3),
        'atk_def': {'atk_home': round(fund['atk_home'], 3), 'def_home': round(fund['def_home'], 3),
                    'atk_away': round(fund['atk_away'], 3), 'def_away': round(fund['def_away'], 3)},
        'dc': {k: round(v, 4) for k, v in dc_p.items()},
        'nb': {k: round(v, 4) for k, v in nb_p.items()},
        'zip': {k: round(v, 4) for k, v in zp_p.items()},
        'skellam': {k: round(v, 4) for k, v in sk_p.items()},
        'mc': {k: round(v, 4) for k, v in mc_p.items()},
        'fused': {k: round(v, 4) for k, v in fused.items()},
        'market': {k: round(v, 4) for k, v in market.items()} if market else None,
        'divergence': ({k: round(fused[k] - market[k], 4) for k in fused} if market else None),
        'selection': {k: v for k, v in sel.items()},
        'k_dist': {'k': k_dist[0], 'p': round(k_dist[1], 4)},
        'k_rec': {'k': k_rec[0], 'p': round(k_rec[1], 4)},
        'top_scores': [(h, a, round(p, 4)) for h, a, p in pool['scores']],
        'score_pool': {'forced': pool['forced'], 'tail_only': pool['tail_only'],
                       'notes': pool['notes']},
        'ttg': {str(k): round(v, 4) for k, v in sorted(tg.items()) if v > 0.0005},
        'ttg_top': [(k, round(v, 4)) for k, v in sorted(tg.items(), key=lambda x: -x[1])[:6]],
        'goal_band': band,
        'p01': round(p01, 4), 'p23': round(p23, 4), 'p45': round(p45, 4),
        'p6': round(p6, 4), 'p_over25': round(p_over25, 4),
        'ht_draw_rate': hr,
        'htft': [(k, round(v, 4)) for k, v in htft_sorted[:9]],
        'htft_top3': [(k, round(v, 4)) for k, v in hp['picks']],
        'htft_forced': hp['forced'],
        'hhad_line': line,
        'hhad_model': ({k: round(v, 4) for k, v in hc_model.items()} if hc_model else None),
        'hhad_market': ({o['key']: round(o['noVig'] or 0, 4) for o in m['hhad']['outcomes']}
                        if m.get('hhad') else None),
        'hhad_pick': hc,
        'parlay_leg': leg,
        'notes': notes,
    }


def sk_skellam_sf(x, mu1, mu2):
    return sp_stats.skellam.sf(x, mu1, mu2)


def sk_skellam_pmf(x, mu1, mu2):
    return sp_stats.skellam.pmf(x, mu1, mu2)


def sk_skellam_cdf(x, mu1, mu2):
    return sp_stats.skellam.cdf(x, mu1, mu2)


def json_safe(o):
    if isinstance(o, dict):
        return {str(k): json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [json_safe(v) for v in o]
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    return o


def main():
    now = datetime.now()
    with io.open(SRC, encoding='utf-8-sig') as f:
        matches = json.load(f)
    res = [analyze(m, now) for m in matches]

    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(json_safe({'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
                             'source': SRC, 'match_count': len(res),
                             'rule79': 'λ仅基本面；市场仅对照',
                             'matches': res}), f, ensure_ascii=False, indent=1)

    lines = ['2026-11-08 模型运行 %s（%d场，规则79）' % (now.strftime('%Y-%m-%d %H:%M'), len(res)),
             '数据缺口：无身价/伤停/场地/近5场半场记录；L242/L243以身价缺失披露，L244未触发', '']
    for r in res:
        lines.append('%s %s vs %s [%s] %s λ%.2f/%.2f(总%.2f) %s' % (
            r['num'], r['home'], r['away'], r['league'], r['status'],
            r['lambda_home'], r['lambda_away'], r['lambda_total'],
            '【单关】' if r['is_single'] else ''))
        mk = r['market']
        lines.append('  融合 主%.1f/平%.1f/客%.1f | 市场 %s | 首选%s(%.1f%%) 次选%s(%.1f%%)%s' % (
            r['fused']['home'] * 100, r['fused']['draw'] * 100, r['fused']['away'] * 100,
            ('主%.1f/平%.1f/客%.1f' % (mk['home'] * 100, mk['draw'] * 100, mk['away'] * 100)) if mk else '无',
            NAME_CN[r['selection']['primary']], r['fused'][r['selection']['primary']] * 100,
            NAME_CN[r['selection']['secondary']], r['fused'][r['selection']['secondary']] * 100,
            '（双选）' if r['selection']['dual'] else ''))
        lines.append('  比分TOP5 %s | 进球%s %s | TTG前2 %s' % (
            ['%d-%d' % (h, a) for h, a, _ in r['top_scores']],
            r['goal_band']['tier'], r['goal_band']['over_under'], r['ttg_top'][:2]))
        lines.append('  半全场TOP3 %s%s | 让球(%s) %s' % (
            ['%s%s' % (k, HAFU_CN.get(k, '')) for k, _ in r['htft_top3']],
            '（含强制%s）' % r['htft_forced'] if r['htft_forced'] else '',
            r['hhad_line'], HC_CN.get(r['hhad_pick']['pick'], '-') if r['hhad_pick'] else '-'))
        for n in r['notes']:
            lines.append('  · ' + n)
        lines.append('')

    with io.open(LOG, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    avail = [r for r in res if r['status'] == '待开赛']
    print('场次 %d，待开赛 %d，已开赛 %d' % (len(res), len(avail), len(res) - len(avail)))
    for r in res:
        print('%s %-6s %-10s vs %-10s λ%.2f/%.2f | 主%.1f 平%.1f 客%.1f | 首%s 次%s | %s %s | %s' % (
            r['num'], r['league'], r['home'], r['away'], r['lambda_home'], r['lambda_away'],
            r['fused']['home'] * 100, r['fused']['draw'] * 100, r['fused']['away'] * 100,
            NAME_CN[r['selection']['primary']], NAME_CN[r['selection']['secondary']],
            r['goal_band']['tier'], r['goal_band']['over_under'], r['status']))
    print('saved', OUT, '|', LOG)


if __name__ == '__main__':
    main()
