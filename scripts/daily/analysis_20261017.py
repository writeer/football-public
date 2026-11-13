# -*- coding: utf-8 -*-
"""
2026-10-17 周六 竞彩30场 模型计算（AGENTS.md 第4-5步）
- 市场去水概率反解 lambda（DC 最小二乘）
- 伤停/战意/赛程 lambda 修正（总控人工裁定表）
- 规则63单关平局上修（003/007/017/024）
- 规则65大球上修 / 规则68英超 / 规则22意甲·西甲·韩职 / 规则22-L1法甲
- 输出：融合概率、TTG、CRS、HAFU、HTFT、半场比分、k_dist/k_rec、带内候选
"""
import sys, json
sys.path.insert(0, r'e:\VibeCoding\football')
import numpy as np
from scipy import stats as sp_stats
from scipy.optimize import minimize
from lottery_agent.models import (DixonColesModel, NegativeBinomialModel, ZIPModel,
                                  SkellamModel, MonteCarloSimulator, OddsCalibrator, HTFTModel)

SRC = 'reports/data/20261017_saturday_matches.json'
OUT = 'reports/data/20261017_model_output.json'

# 联赛 -> (ht_draw_rate, 半场lambda比例)
LEAGUE_HT = {
    '澳超': (None, 0.45), '日职': (0.534, 0.38), '日乙': (None, 0.45), '韩职': (0.512, 0.38),
    '英超': (0.384, 0.42), '英冠': (0.425, 0.38), '西甲': (0.441, 0.38), '挪超': (0.325, 0.45),
    '意甲': (0.409, 0.38), '芬超': (0.418, 0.38), '德甲': (0.359, 0.42), '法甲': (0.393, 0.42),
    '荷甲': (0.387, 0.42), '美职': (0.366, 0.42),
}

# 总控人工修正表：lh/la = 伤停体能战意对攻击lambda的乘数；dt = 规则65大球上修（总进球增加值）
ADJ = {
    '周六001': dict(lh=0.98, la=1.03, dt=0.0, note='麦克阿瑟4人伤缺+新帅首战；珀斯3名后卫缺阵'),
    '周六002': dict(lh=1.05, la=0.95, dt=0.30, note='长崎5人伤缺且客场4战不胜；鹿岛主场强'),
    '周六003': dict(lh=1.06, la=0.92, dt=0.30, note='蔚山争冠组战意+主场；富川7轮不胜客场3连败'),
    '周六004': dict(lh=0.95, la=0.95, dt=0.0, note='中央海岸5连败；纽喷11人伤缺+亚冠连败3天2赛'),
    '周六005': dict(lh=1.05, la=0.95, dt=0.30, note='柏5连胜领跑；名古屋客场1胜4负'),
    '周六006': dict(lh=1.03, la=0.92, dt=0.30, note='磐田4主力伤缺+3天前0-4；宫崎无伤病'),
    '周六007': dict(lh=0.98, la=0.95, dt=0.0, note='埃弗顿3人伤疑；切尔西詹姆斯等3人缺阵'),
    '周六008': dict(lh=1.08, la=0.90, dt=0.40, note='林肯3连败失11球+2人停赛；米尔沃尔主场'),
    '周六009': dict(lh=0.93, la=1.03, dt=0.15, note='西班牙人2主力缺阵；马竞5连胜仅卡多索缺阵'),
    '周六010': dict(lh=1.00, la=0.95, dt=0.30, note='博德欧冠3天后作客+4人伤缺；汉坎人造草主场'),
    '周六011': dict(lh=0.90, la=0.97, dt=0.10, note='威尼斯0分8连败7人伤；那不勒斯客场3场不胜'),
    '周六012': dict(lh=1.05, la=0.97, dt=0.30, note='HJK两轮10球；Gnistan客场刚负VPS'),
    '周六013': dict(lh=1.03, la=0.90, dt=0.15, note='奥格斯堡6人缺阵含穆涅/克洛德-莫里斯'),
    '周六014': dict(lh=0.90, la=0.95, dt=0.15, note='不来梅8人伤缺；帕德博恩4人缺阵'),
    '周六015': dict(lh=1.00, la=0.93, dt=0.15, note='美因茨门将/锋线/后腰缺阵；沙尔克主场两连0-0'),
    '周六016': dict(lh=0.90, la=0.92, dt=0.15, note='汉堡4人缺阵；斯图加特6人缺阵+欧冠3天2赛'),
    '周六017': dict(lh=0.90, la=0.93, dt=0.15, note='柏林联合3主力缺阵；多特3人缺阵+欧冠输球'),
    '周六018': dict(lh=1.05, la=0.88, dt=0.0, note='利物浦格拉文贝赫停赛+多人伤疑+欧冠后轮换'),
    '周六019': dict(lh=1.05, la=1.00, dt=0.0, note='曼城全员6连胜；伊普斯升班马状态尚可'),
    '周六020': dict(lh=0.95, la=1.00, dt=0.0, note='富勒姆垫底0胜；赫尔城状态好但8人伤疑'),
    '周六021': dict(lh=0.97, la=0.97, dt=0.15, note='黄潜欧冠3天后；埃尔切1人缺阵'),
    '周六022': dict(lh=0.88, la=1.03, dt=0.15, note='斯特拉斯堡5人伤缺；PSG仅马尤卢缺阵且欧冠胜曼城'),
    '周六023': dict(lh=0.93, la=0.90, dt=0.10, note='博洛尼亚2人缺阵；国米劳塔罗+2人缺阵+欧冠负'),
    '周六024': dict(lh=0.93, la=0.92, dt=0.0, note='纽卡3人伤疑；维拉两左后卫+奥纳纳缺阵'),
    '周六025': dict(lh=0.97, la=0.90, dt=0.15, note='拜仁穆西亚拉/诺伊尔缺阵；莱比锡4人缺阵且客场全败'),
    '周六026': dict(lh=0.97, la=0.97, dt=0.15, note='贝蒂斯2人缺阵；巴萨克里斯滕森缺阵+双线轮换'),
    '周六027': dict(lh=1.00, la=0.90, dt=0.30, note='费耶诺德8人伤缺+欧冠轮换；特尔斯达主场未胜'),
    '周六028': dict(lh=0.85, la=0.95, dt=0.10, note='罗马迪巴拉/科内/克里斯坦特/斯维拉尔缺阵+马伦停赛'),
    '周六029': dict(lh=0.90, la=0.93, dt=0.0, note='巴伦西亚7人伤缺+新帅；毕尔巴鄂桑塞特/拉波尔特缺阵'),
    '周六030': dict(lh=0.97, la=0.95, dt=0.0, note='新英格兰4人伤缺+三赛；芝加哥5人缺阵含停赛'),
}
SINGLE = {'周六003', '周六007', '周六017', '周六024'}
# 联赛概率修正：主胜/平局平移（百分点）
LEAGUE_SHIFT = {'英超': (-4, +5), '意甲': (0, +3), '西甲': (0, +4), '韩职': (0, +3)}

HAD_ORDER = ['home', 'draw', 'away']
NAME_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HAFU_CN = {'HH': '胜胜', 'HD': '胜平', 'HA': '胜负', 'DH': '平胜', 'DD': '平平',
           'DA': '平负', 'AH': '负胜', 'AD': '负平', 'AA': '负负'}


def de_vig(odds):
    inv = {k: 1.0 / v for k, v in odds.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}


def had_from_crs(crs):
    h = d = a = 0.0
    for o in crs:
        k = str(o.get('key', ''))
        if ':' not in k: continue
        try:
            i, j = [int(t) for t in k.split(':')]
        except Exception:
            continue
        p = o.get('noVig') or 0
        if i > j: h += p
        elif i == j: d += p
        else: a += p
    t = h + d + a
    return {'home': h / t, 'draw': d / t, 'away': a / t}


def fit_lambdas(market, start_total):
    dc = DixonColesModel()
    def obj(x):
        lh, la = x
        p = dc.outcome_probs(lh, la)
        return ((p['home'] - market['home']) ** 2 + (p['draw'] - market['draw']) ** 2
                + (p['away'] - market['away']) ** 2)
    x0 = [max(0.4, start_total * 0.57), max(0.3, start_total * 0.43)]
    r = minimize(obj, x0, method='L-BFGS-B', bounds=[(0.05, 5.0), (0.05, 5.0)],
                 options={'eps': 0.01, 'maxiter': 300})
    return float(r.x[0]), float(r.x[1])


def analyze(m):
    num = m['num']; league = m['league']
    mk = m
    if m['had']:
        odds = {o['key']: o['odds'] for o in m['had']}
        market = de_vig(odds)
        shin = OddsCalibrator(odds['home'], odds['draw'], odds['away']).shin()
        shin_probs = [shin['home'], shin['draw'], shin['away']]
        src = 'HAD去水'
    else:
        market = had_from_crs(m['crs'])
        shin_probs = [market['home'], market['draw'], market['away']]
        src = 'CRS聚合'

    avg = {'澳超': 2.72, '日职': 2.52, '日乙': 2.49, '韩职': 2.48, '英超': 2.86, '英冠': 2.45,
           '西甲': 2.48, '挪超': 2.82, '意甲': 2.63, '芬超': 2.55, '德甲': 3.21, '法甲': 2.68,
           '荷甲': 3.18, '美职': 2.68}.get(league, 2.6)
    lh, la = fit_lambdas(market, avg)

    adj = ADJ.get(num, dict(lh=1.0, la=1.0, dt=0.0, note=''))
    lh *= adj['lh']; la *= adj['la']
    if adj['dt']:
        tot = lh + la
        lh += adj['dt'] * lh / tot; la += adj['dt'] * la / tot

    dc = DixonColesModel(); nb = NegativeBinomialModel(); zp = ZIPModel(); sk = SkellamModel()
    mc = MonteCarloSimulator(n_sim=20000)
    dc_p = dc.outcome_probs(lh, la); nb_p = nb.outcome_probs(lh, la)
    zip_p = zp.outcome_probs(lh, la); skp = sk.outcome_probs(lh, la)
    mcr = mc.simulate(lh, la)
    mc_p = {'home': mcr['home_win'], 'draw': mcr['draw'], 'away': mcr['away_win']}
    W = {'dc': 0.30, 'nb': 0.20, 'zip': 0.12, 'sk': 0.13, 'mc': 0.10, 'shin': 0.08, 'mkt': 0.07}
    fused = {}
    for k in HAD_ORDER:
        fused[k] = (W['dc'] * dc_p[k] + W['nb'] * nb_p[k] + W['zip'] * zip_p[k] + W['sk'] * skp[k]
                    + W['mc'] * mc_p[k] + W['shin'] * shin_probs[HAD_ORDER.index(k)] + W['mkt'] * market[k])

    # 联赛特化平移
    if league in LEAGUE_SHIFT:
        dh, dd = LEAGUE_SHIFT[league]
        fused['home'] += dh / 100.0; fused['draw'] += dd / 100.0
        fused['away'] -= (dh + dd) / 100.0
    for k in HAD_ORDER:
        fused[k] = max(fused[k], 0.01)
    s = sum(fused.values()); fused = {k: v / s for k, v in fused.items()}

    # 规则63 单关平局上修
    single_note = ''
    if num in SINGLE:
        sf = sorted(fused.items(), key=lambda x: -x[1])
        gap = (sf[0][1] - fused['draw']) * 100
        add = 0.14 if gap <= 10 else (0.11 if gap <= 20 else 0.08)
        old = fused['draw']; new = min(old + add, 0.65); add = new - old
        nd = fused['home'] + fused['away']
        fused['draw'] = new
        if nd > 0:
            fused['home'] -= add * fused['home'] / nd
            fused['away'] -= add * fused['away'] / nd
        s = sum(fused.values()); fused = {k: v / s for k, v in fused.items()}
        single_note = f"单关平局上修+{add*100:.1f}pp（首选-平差距{gap:.1f}pp）"

    sf = sorted(fused.items(), key=lambda x: -x[1])
    primary, secondary = sf[0][0], sf[1][0]

    n = 16 if (lh + la) > 3.4 else 13
    dc.max_goals = n
    matrix = dc.compute_matrix(lh, la)

    tg = {}
    for i in range(n):
        for j in range(n):
            tg[i + j] = tg.get(i + j, 0.0) + matrix[i, j]
    gd = {}
    for i in range(n):
        for j in range(n):
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

    # 让球（Skellam + 市场）
    gl = m['hhad']['goalLine']
    hh_model = None
    if gl is not None:
        th = -gl
        hh_model = {'home': float(sp_stats.skellam.sf(th, lh, la)),
                    'draw': float(sp_stats.skellam.pmf(th, lh, la)),
                    'away': float(sp_stats.skellam.cdf(th - 1, lh, la))}
    hh_market = {}
    hh_odds = {}
    for o in m['hhad']['outcomes']:
        hh_odds[o['key']] = o['odds']; hh_market[o['key']] = o['noVig']

    hr = LEAGUE_HT.get(league, (None, 0.45))[1]
    htft = HTFTModel(dc); htft.ht_ratio = hr
    ht_res = htft.predict(lh, la)
    htft_cn = [(HAFU_CN.get(r['code'].replace('/', ''), r['htft']), r['probability']) for r in ht_res]
    mat_ht = dc.compute_matrix(lh * hr, la * hr)
    ht_scores = sorted([(i, j, mat_ht[i, j]) for i in range(4) for j in range(4)], key=lambda x: -x[2])[:4]

    ttg_top = sorted(tg.items(), key=lambda x: -x[1])[:6]
    ttg_odds = {o['key']: o['odds'] for o in m['ttg']}
    hafu_odds = {o['key']: o['odds'] for o in m['hafu']}
    crs_odds = {o['key']: o['odds'] for o in m['crs']}

    # 比分矩阵TOP（全分布，供校核）
    top_scores = sorted([(i, j, matrix[i, j]) for i in range(n) for j in range(n)], key=lambda x: -x[2])[:8]

    return {
        'num': num, 'league': league, 'home': m['home'], 'away': m['away'],
        'home_rank': m['home_rank'], 'away_rank': m['away_rank'], 'time': m['time'],
        'is_single': num in SINGLE, 'had_source': src,
        'odds_had': ({o['key']: o['odds'] for o in m['had']} if m['had'] else None),
        'odds_hhad': hh_odds, 'hhad_line': gl, 'odds_ttg': ttg_odds, 'odds_hafu': hafu_odds,
        'odds_crs': crs_odds,
        'market': {k: round(v, 4) for k, v in market.items()},
        'shin': [round(p, 4) for p in shin_probs],
        'lambda_home': round(lh, 3), 'lambda_away': round(la, 3), 'lambda_total': round(lh + la, 3),
        'adj_note': adj['note'], 'dc': {k: round(v, 4) for k, v in dc_p.items()},
        'fused': {k: round(v, 4) for k, v in fused.items()},
        'primary': primary, 'secondary': secondary,
        'primary_prob': round(sf[0][1], 4), 'secondary_prob': round(sf[1][1], 4),
        'single_note': single_note,
        'hhad_model': {k: round(v, 4) for k, v in hh_model.items()} if hh_model else None,
        'hhad_market': {k: round(v, 4) for k, v in hh_market.items()},
        'k_dist': k_dist[0], 'k_dist_prob': round(k_dist[1], 4),
        'k_rec': k_rec[0], 'k_rec_prob': round(k_rec[1], 4), 'k_consistent': bool(consistent),
        'band': [(a, b, round(p, 4)) for a, b, p in band[:6]],
        'top_scores': [(a, b, round(p, 4)) for a, b, p in top_scores],
        'tg': {str(k): round(v, 4) for k, v in sorted(tg.items()) if v > 0.0005},
        'ttg_top': [(k, round(v, 4)) for k, v in ttg_top],
        'htft': [(k, round(v, 4)) for k, v in htft_cn[:9]],
        'ht_scores': [(a, b, round(p, 4)) for a, b, p in ht_scores],
    }


def main():
    ms = json.load(open(SRC, encoding='utf-8'))
    res = [analyze(m) for m in ms]
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for r in res:
        print(f"{r['num']} {r['home']} vs {r['away']} [{r['league']}] 单关={r['is_single']} "
              f"λ{r['lambda_home']}/{r['lambda_away']}(总{r['lambda_total']})")
        print(f"   融合 主{r['fused']['home']*100:.1f}/平{r['fused']['draw']*100:.1f}/客{r['fused']['away']*100:.1f}"
              f" → 首选{r['primary']}({r['primary_prob']*100:.1f}) 次选{r['secondary']}({r['secondary_prob']*100:.1f})")
        print(f"   让({r['hhad_line']}) 模型{r['hhad_model']} 市场{r['hhad_market']}")
        print(f"   k_dist={r['k_dist']}({r['k_dist_prob']*100:.1f}) k_rec={r['k_rec']}({r['k_rec_prob']*100:.1f}) "
              f"{'一致' if r['k_consistent'] else '分歧'} 带内={[(a,b,round(p*100,1)) for a,b,p in r['band'][:4]]}")
        print(f"   TTG={[(k,round(v*100,1)) for k,v in r['ttg_top'][:3]]} 半全场={[(k,round(v*100,1)) for k,v in r['htft'][:3]]}")
    print('saved', OUT)


if __name__ == '__main__':
    main()
