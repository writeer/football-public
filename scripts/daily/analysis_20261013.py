# -*- coding: utf-8 -*-
"""
2026-10-13 周二 竞彩12场 模型计算（AGENTS.md 第5步）
- 读取 reports/data/20261013_matches.json
- 以市场去水概率为锚点反解 lambda（网格搜索最小二乘拟合 DC 矩阵）
- 输出各模型概率、比分矩阵、净胜球双众数(k_dist/k_rec)、TTG、半全场、让球、比分TOP5
- 008 无胜平负盘：由 CRS 的 noVigProb 聚合求主/平/客
"""
import sys, json, itertools
sys.path.insert(0, r'e:\VibeCoding\football')
import numpy as np
from scipy import stats as sp_stats
from scipy.optimize import minimize
from lottery_agent.models import (
    DixonColesModel, NegativeBinomialModel, ZIPModel,
    SkellamModel, MonteCarloSimulator, OddsCalibrator, HTFTModel
)
from lottery_agent.config import LEAGUE_PROFILES

SRC = r'e:\VibeCoding\football\reports\data\20261013_matches.json'
OUT = r'e:\VibeCoding\football\reports\data\20261013_model_output.json'

LEAGUE_MAP = {
    '亚洲冠军精英联赛': '亚冠',
    '欧洲冠军联赛': '欧冠',
    '英格兰冠军联赛': '英冠',
    '日本联赛杯': 'default',
    '南美解放者杯': 'default',
}
EXTRA_PROFILES = {
    '亚冠': {'avg_goals': 2.55, 'vmr': 1.15, 'home_advantage': 1.30, 'defensive': False, 'over_dispersed': False},
}
# 规则66 半场lambda比例
HT_RATIO = {'英冠': 0.38, '欧冠': 0.42, '亚冠': 0.42, 'default': 0.45}

IS_SINGLE = {'周二003', '周二007', '周二011'}

HAD_KEY_ORDER = ['home', 'draw', 'away']


def load():
    d = json.load(open(SRC, encoding='utf-8-sig'))['data']
    out = []
    for m in d['matches']:
        if not m['matchNumStr'].startswith('周二'):
            continue
        mk = m['markets']
        had = mk.get('had', {}).get('outcomes', [])
        if had:
            odds = {o['key'] if 'key' in o else o['labelZh']: o['odds'] for o in had}
            # key may be like 'h','d','a'
            o = {}
            for x in had:
                k = str(x.get('key', '')).lower()
                lab = x.get('labelZh', '')
                if k in ('h', 'home') or lab in ('胜', '主胜'):
                    o['home'] = x['odds']
                elif k in ('d', 'draw') or lab in ('平', '平局'):
                    o['draw'] = x['odds']
                elif k in ('a', 'away') or lab in ('负', '客胜'):
                    o['away'] = x['odds']
            odds = o
        else:
            odds = None
        hh = mk.get('hhad', {})
        gl = hh.get('goalLine', hh.get('goal_line'))
        mm = {
            'match_num': m['matchNumStr'],
            'league_raw': m['league']['allName'],
            'home': m['home']['allName'],
            'away': m['away']['allName'],
            'home_rank': m['home'].get('rank', ''),
            'away_rank': m['away'].get('rank', ''),
            'match_time': m['businessDate'] + ' ' + m['matchTime'],
            'match_id': m['matchId'],
            'odds': odds,
            'hhad_line': gl,
            'markets': mk,
            'is_single': m['matchNumStr'] in IS_SINGLE,
            'stadium_status': '正常',
        }
        out.append(mm)
    return out


def derive_had_from_crs(mk):
    crs = mk.get('crs', {}).get('outcomes', [])
    h = d = a = 0.0
    for o in crs:
        k = o.get('key', '')
        p = o.get('noVigProb', 0)
        try:
            i, j = [int(t) for t in k.split(':')]
        except Exception:
            continue
        if i > j:
            h += p
        elif i == j:
            d += p
        else:
            a += p
    tot = h + d + a
    if tot <= 0:
        return None
    return {'home': h/tot, 'draw': d/tot, 'away': a/tot}


def de_vig(odds):
    inv = {k: 1.0/v for k, v in odds.items()}
    s = sum(inv.values())
    return {k: v/s for k, v in inv.items()}


def fit_lambdas(market, league_avg):
    """L-BFGS-B 最小化 DC 概率与市场概率的误差"""
    dc = DixonColesModel()

    def obj(x):
        lh, la = x
        p = dc.outcome_probs(lh, la)
        return ((p['home']-market['home'])**2 + (p['draw']-market['draw'])**2 + (p['away']-market['away'])**2)

    x0 = [max(0.4, league_avg*0.6), max(0.3, league_avg*0.4)]
    r = minimize(obj, x0, method='L-BFGS-B', bounds=[(0.05, 5.0), (0.05, 5.0)],
                 options={'eps': 0.01, 'maxiter': 200})
    lh, la = float(r.x[0]), float(r.x[1])
    return round(lh, 3), round(la, 3)


def analyze(mm):
    raw_league = mm['league_raw']
    league = LEAGUE_MAP.get(raw_league, 'default')
    prof = EXTRA_PROFILES.get(league) or LEAGUE_PROFILES.get(league, LEAGUE_PROFILES['default'])
    mk = mm['markets']

    if mm['odds'] is None:
        market = derive_had_from_crs(mk)
        src = 'CRS聚合'
    else:
        market = de_vig(mm['odds'])
        src = 'HAD去水'

    shin = OddsCalibrator(mm['odds']['home'], mm['odds']['draw'], mm['odds']['away']) if mm['odds'] else None
    if shin:
        sr = shin.shin()
        shin_probs = [sr['home'], sr['draw'], sr['away']]
    else:
        shin_probs = [market['home'], market['draw'], market['away']]

    lh, la = fit_lambdas(market, prof['avg_goals'])

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

    matrix = dc.compute_matrix(lh, la)
    n = matrix.shape[0]

    # 总进球分布
    tg = {}
    for t in range(n*2):
        tg[t] = 0.0
    for i in range(n):
        for j in range(n):
            if i+j in tg:
                tg[i+j] += matrix[i, j]

    # 净胜球分布（逐 k 独立，禁止合并桶）
    gd = {}
    for i in range(n):
        for j in range(n):
            k = i-j
            gd[k] = gd.get(k, 0.0) + matrix[i, j]

    k_dist = max(gd.items(), key=lambda x: x[1])

    # 融合概率（权重按规则28：基本面15%暂由总控在报告层处理，这里给模型+市场）
    W = {'dc': 0.30, 'nb': 0.20, 'zip': 0.12, 'sk': 0.13, 'mc': 0.10, 'shin': 0.08, 'mkt': 0.07}
    def blend(k):
        return (W['dc']*dc_p[k] + W['nb']*nb_p[k] + W['zip']*zip_p[k] + W['sk']*skp[k]
                + W['mc']*mc_p[k] + W['shin']*shin_probs[HAD_KEY_ORDER.index(k)] + W['mkt']*market[k])
    fused = {k: blend(k) for k in HAD_KEY_ORDER}
    s = sum(fused.values()); fused = {k: v/s for k, v in fused.items()}
    sorted_f = sorted(fused.items(), key=lambda x: -x[1])
    primary, secondary = sorted_f[0][0], sorted_f[1][0]

    # k_rec：方向内众数
    if primary == 'home':
        cand = {k: v for k, v in gd.items() if k >= 1}
    elif primary == 'away':
        cand = {k: v for k, v in gd.items() if k <= -1}
    else:
        cand = {k: v for k, v in gd.items() if k == 0}
    k_rec = max(cand.items(), key=lambda x: x[1]) if cand else k_dist
    consistent = ((primary == 'home' and k_dist[0] >= 1) or (primary == 'away' and k_dist[0] <= -1)
                  or (primary == 'draw' and k_dist[0] == 0))

    # 带内展开 TOP5（固定 k_rec）
    kr = k_rec[0]
    band = []
    for i in range(n):
        j = i - kr
        if 0 <= j < n:
            band.append((i, j, matrix[i, j]))
    band.sort(key=lambda x: -x[2])

    # 让球（Skellam）
    gl = mm['hhad_line']
    hh_p = None
    if gl is not None:
        th = -gl
        hh_p = {'home': sp_stats.skellam.sf(th, lh, la),
                'draw': sp_stats.skellam.pmf(th, lh, la),
                'away': sp_stats.skellam.cdf(th-1, lh, la)}

    # 半全场
    htft = HTFTModel(dc)
    htft.ht_ratio = HT_RATIO.get(league, HT_RATIO['default'])
    ht_res = htft.predict(lh, la)
    M = {'H/H': '胜胜', 'H/D': '胜平', 'H/A': '胜负', 'D/H': '平胜', 'D/D': '平平',
         'D/A': '平负', 'A/H': '负胜', 'A/D': '负平', 'A/A': '负负'}
    htft_cn = [(M.get(r['code'], r['htft']), r['probability']) for r in ht_res]

    # 半场比分 TOP3（规则33第6维度）
    hr = HT_RATIO.get(league, HT_RATIO['default'])
    mat_ht = dc.compute_matrix(lh*hr, la*hr)
    ht_scores = sorted([(i, j, mat_ht[i, j]) for i in range(4) for j in range(4)],
                       key=lambda x: -x[2])[:4]

    # TTG TOP
    ttg_sorted = sorted(tg.items(), key=lambda x: -x[1])[:5]

    # 单关平局上修（规则63）
    single_note = ''
    if mm['is_single']:
        first = sorted_f[0][1]; draw_p = fused['draw']
        gap = (first - draw_p)*100
        adj = 0.14 if gap <= 10 else (0.11 if gap <= 20 else 0.09)
        old = fused['draw']; new = min(old + adj, 0.65)
        add = new - old
        nd = fused['home']+fused['away']
        if nd > 0:
            fused['home'] -= add*fused['home']/nd
            fused['away'] -= add*fused['away']/nd
        fused['draw'] = new
        s = sum(fused.values()); fused = {k: v/s for k, v in fused.items()}
        sorted_f = sorted(fused.items(), key=lambda x: -x[1])
        primary, secondary = sorted_f[0][0], sorted_f[1][0]
        single_note = f"单关平局上修+{add*100:.1f}%（差距{gap:.1f}pp）"

    return {
        'match_num': mm['match_num'], 'league': league, 'league_raw': raw_league,
        'home': mm['home'], 'away': mm['away'], 'home_rank': mm['home_rank'], 'away_rank': mm['away_rank'],
        'match_time': mm['match_time'], 'is_single': mm['is_single'], 'stadium_status': mm['stadium_status'],
        'had_source': src, 'odds': mm['odds'],
        'market': {k: round(v, 4) for k, v in market.items()},
        'shin': [round(p, 4) for p in shin_probs],
        'lambda_home': lh, 'lambda_away': la, 'lambda_total': round(lh+la, 3),
        'dc': {k: round(v, 4) for k, v in dc_p.items()},
        'fused': {k: round(v, 4) for k, v in fused.items()},
        'primary': primary, 'secondary': secondary,
        'primary_prob': round(sorted_f[0][1], 4), 'secondary_prob': round(sorted_f[1][1], 4),
        'hhad_line': gl, 'hhad': {k: round(v, 4) for k, v in hh_p.items()} if hh_p else None,
        'k_dist': k_dist[0], 'k_dist_prob': round(k_dist[1], 4),
        'k_rec': k_rec[0], 'k_rec_prob': round(k_rec[1], 4), 'k_consistent': consistent,
        'band': [(a, b, round(p, 4)) for a, b, p in band[:6]],
        'tg': {str(k): round(v, 4) for k, v in sorted(tg.items())},
        'ttg_top': [(k, round(v, 4)) for k, v in ttg_sorted],
        'htft': [(k, round(v, 4)) for k, v in htft_cn],
        'ht_scores': [(a, b, round(p, 4)) for a, b, p in ht_scores],
        'single_note': single_note,
    }


def main():
    ms = load()
    res = [analyze(m) for m in ms]
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    for r in res:
        print(f"{r['match_num']} {r['home']} vs {r['away']} [{r['league']}] 单关={r['is_single']}")
        print(f"   λ {r['lambda_home']}/{r['lambda_away']} (总{r['lambda_total']}) 市场{r['had_source']}"
              f" 主{r['market']['home']*100:.1f}/平{r['market']['draw']*100:.1f}/客{r['market']['away']*100:.1f}")
        print(f"   融合 主{r['fused']['home']*100:.1f}/平{r['fused']['draw']*100:.1f}/客{r['fused']['away']*100:.1f}"
              f" → 首选{r['primary']}({r['primary_prob']*100:.1f}) 次选{r['secondary']}({r['secondary_prob']*100:.1f})")
        print(f"   让球({r['hhad_line']}) {r['hhad']}")
        print(f"   k_dist={r['k_dist']}({r['k_dist_prob']*100:.1f}) k_rec={r['k_rec']}({r['k_rec_prob']*100:.1f}) "
              f"{'一致' if r['k_consistent'] else '分歧'} 带内={[(f'{a}-{b}',f'{p*100:.1f}%') for a,b,p in r['band'][:4]]}")
        print(f"   TTG={[(k,f'{v*100:.1f}%') for k,v in r['ttg_top'][:3]]}")
        print(f"   半全场={[(k,f'{v*100:.1f}%') for k,v in r['htft'][:3]]}")
        print(f"   半场比分={[(f'{a}-{b}',f'{p*100:.1f}%') for a,b,p in r['ht_scores'][:3]]}")
        print()
    print('saved', OUT)


if __name__ == '__main__':
    main()
