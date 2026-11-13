# -*- coding: utf-8 -*-
"""2026-11-13（周五）销售日：λ 建模 + 全玩法概率（DC 泊松）"""
import json, math, itertools

RAW = json.load(open('reports/data/20261113_calc_raw.json', encoding='utf-8'))
BASE = json.load(open('reports/data/20261113_collect_base.json', encoding='utf-8'))

ELO = {'Moldova':1288,'Kazakhstan':1387,'Bulgaria':1450,'Iceland':1597,'Luxembourg':1383,'Estonia':1406,
       'Netherlands':1974,'Greece':1804,'Scotland':1718,'North Macedonia':1533,'Serbia':1683,'Germany':1895,
       'Slovakia':1678,'Faroe Islands':1397,'Slovenia':1718,'Switzerland':1975,
       'Singapore':1149,'Paraguay':1836,'Argentina':2175,'Uruguay':1851,'Colombia':1990,'Chile':1723}
ST = BASE['standings']

TEAMS_EN = {
 '周五001': ('Singapore','Paraguay'), '周五002': ('Moldova','Kazakhstan'), '周五003': ('Bulgaria','Iceland'),
 '周五004': ('Scotland','North Macedonia'), '周五005': ('Serbia','Germany'), '周五006': ('Luxembourg','Estonia'),
 '周五007': ('Slovakia','Faroe Islands'), '周五008': ('Slovenia','Switzerland'), '周五009': ('Netherlands','Greece'),
 '周五010': ('Argentina','Uruguay'), '周五011': ('Colombia','Chile')}
FRIENDLY = {'周五001','周五010','周五011'}

# 伤停/回归修正（依据 Sports Mole 赛前预览，攻击/防守乘数）
INJ = {
 '周五002': ((1.00,1.00),(0.98,1.04)),   # 哈萨克 Malyy 停赛（后卫）
 '周五003': ((1.03,0.98),(1.00,1.00)),   # 保加利亚 Mitov/Petkov 回归
 '周五004': ((1.04,1.00),(1.00,1.00)),   # 苏格兰 McTominay 回归
 '周五005': ((0.93,1.00),(1.00,1.00)),   # 塞尔维亚 Lukic/Maksimovic 停赛
 '周五006': ((0.97,1.03),(0.98,1.00)),   # 卢森堡 Carlson 停赛/Jans 回归；爱沙尼亚 Kuusk/Saarma 缺
 '周五007': ((0.90,1.02),(1.00,1.00)),   # 斯洛伐克 Lobotka/Suslov 伤缺；法罗 Agnarsson 停赛
 '周五008': ((0.80,1.06),(1.00,1.00)),   # 斯洛文尼亚 Sesko 伤缺 + Zec/Janza 停赛
 '周五009': ((0.94,1.04),(1.00,1.00)),   # 荷兰 Van Dijk/Gravenberch/Taylor/Brobbey 缺
 '周五010': ((1.00,1.00),(1.00,1.00)),
 '周五011': ((0.90,1.00),(0.96,1.04)),   # 哥伦比亚 Rios/L.Diaz/Campaz 缺；智利 Kuscevic 等缺
 '周五001': ((0.96,1.00),(0.97,1.00)),   # 新加坡 Ikhsan Fandi 等伤缺；巴拉圭 Sanabria 伤缺
}

def pois(l, k):
    return math.exp(-l) * l**k / math.factorial(k)

def dc_matrix(lh, la, rho=-0.05, n=11):
    M = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            v = pois(lh,i)*pois(la,j)
            if i==0 and j==0: v *= 1-lh*la*rho
            elif i==0 and j==1: v *= 1+lh*rho
            elif i==1 and j==0: v *= 1+la*rho
            elif i==1 and j==1: v *= 1-rho
            M[i][j] = max(v, 0.0)
    s = sum(sum(r) for r in M)
    return [[v/s for v in r] for r in M]

def shin(odds):
    q = [1.0/o for o in odds]; S = sum(q)
    lo, hi = 0.0, 0.5
    for _ in range(80):
        z = (lo+hi)/2
        p = [(math.sqrt(z*z + 4*(1-z)*qq*qq/S) - z)/(2*(1-z)) for qq in q]
        if sum(p) > 1: lo = z
        else: hi = z
    p = [(math.sqrt(z*z + 4*(1-z)*qq*qq/S) - z)/(2*(1-z)) for qq in q]
    s = sum(p)
    return [x/s for x in p]

out = []
for m in RAW['value']['matchInfoList'][0]['subMatchList']:
    num = m['matchNumStr']
    h_en, a_en = TEAMS_EN[num]
    league = 'fifa.friendly' if num in FRIENDLY else 'uefa.nations'
    T = 2.70 if num in FRIENDLY else 2.48
    D = ELO[h_en] - ELO[a_en] + 65
    S_sup = max(-1.7, min(1.7, 0.0045*D))
    lp_h = max(0.25, (T+S_sup)/2); lp_a = max(0.25, (T-S_sup)/2)
    lam = {'prior': [round(lp_h,3), round(lp_a,3)], 'group': None}
    if num not in FRIENDLY:
        sh, sa = ST[h_en], ST[a_en]
        grp = sh['group']
        members = [k for k,v in ST.items() if v['group']==grp]
        total_gf = sum(ST[k]['gf'] for k in members); total_gp = sum(ST[k]['gp'] for k in members)
        g = total_gf/total_gp
        att_h = (sh['gf']/sh['gp'])/g; def_h = (sh['ga']/sh['gp'])/g
        att_a = (sa['gf']/sa['gp'])/g; def_a = (sa['ga']/sa['gp'])/g
        w = 4/(sh['gp']+4)
        att_h = 1+(att_h-1)*w; def_h = 1+(def_h-1)*w
        att_a = 1+(att_a-1)*w; def_a = 1+(def_a-1)*w
        lg_h = g*att_h*def_a*1.08; lg_a = g*att_a*def_h/1.08
        lam['group'] = [round(lg_h,3), round(lg_a,3)]
        lh = 0.5*lp_h + 0.5*lg_h; la = 0.5*lp_a + 0.5*lg_a
        lam['group_avg'] = round(g,3)
    else:
        lh, la = lp_h, lp_a
    (iah, idh), (iaa, ida) = INJ.get(num, ((1,1),(1,1)))
    lh = lh*iah; la = la*iaa
    lh = max(0.2, lh); la = max(0.2, la)
    lam['final'] = [round(lh,3), round(la,3)]
    M = dc_matrix(lh, la)
    n = 11
    # HAD
    ph = sum(M[i][j] for i in range(n) for j in range(n) if i>j)
    pd = sum(M[i][i] for i in range(n))
    pa = sum(M[i][j] for i in range(n) for j in range(n) if i<j)
    # HHAD
    line = int(m['hhad']['goalLine'].replace('+','')) if m['hhad'].get('goalLine') else 0
    hh = sum(M[i][j] for i in range(n) for j in range(n) if i+line>j)
    hd = sum(M[i][j] for i in range(n) for j in range(n) if i+line==j)
    ha = sum(M[i][j] for i in range(n) for j in range(n) if i+line<j)
    # TTG
    ttg = {}
    for t in range(7):
        ttg[str(t)] = sum(M[i][j] for i in range(n) for j in range(n) if i+j==t)
    ttg['7'] = sum(M[i][j] for i in range(n) for j in range(n) if i+j>=7)
    # HAFU：上/下半场独立泊松（HT 0.45λ，2H 0.55λ）合成
    def ht_probs(l):
        return [math.exp(-l)*l**k/math.factorial(k) for k in range(9)]
    hlh, hla = lh*0.45, la*0.45
    slh, sla = lh*0.55, la*0.55
    h1 = ht_probs(hlh); h2 = ht_probs(hla)
    s1 = ht_probs(slh); s2 = ht_probs(sla)
    ht_matrix = [[h1[i]*h2[j] for j in range(8)] for i in range(8)]
    s = sum(sum(r) for r in ht_matrix); ht_matrix = [[v/s for v in r] for r in ht_matrix]
    hafu = {'hh':0,'hd':0,'ha':0,'dh':0,'dd':0,'da':0,'ah':0,'ad':0,'aa':0}
    for i in range(8):
        for j in range(8):
            pht = ht_matrix[i][j]
            rht = 'h' if i>j else ('d' if i==j else 'a')
            for u in range(8):
                for v in range(8):
                    p2 = s1[u]*s2[v]
                    if pht*p2 < 1e-9: continue
                    fi, fj = i+u, j+v
                    rft = 'h' if fi>fj else ('d' if fi==fj else 'a')
                    hafu[rht+rft] += pht*p2
    st = sum(hafu.values()); hafu = {k:v/st for k,v in hafu.items()}
    # 半场比分 TOP3
    ht_scores = sorted([(f'{i}-{j}', ht_matrix[i][j]) for i in range(5) for j in range(5)], key=lambda x:-x[1])[:3]
    # 比分 TOP
    scores = sorted([(f'{i}-{j}', M[i][j]) for i in range(7) for j in range(7)], key=lambda x:-x[1])[:8]
    # 净胜球
    kd = {}
    for i in range(n):
        for j in range(n):
            kd[i-j] = kd.get(i-j,0)+M[i][j]
    k_dist = max(kd.items(), key=lambda x:x[1])
    first = 'h' if ph>=pd and ph>=pa else ('d' if pd>=pa else 'a')
    if first=='h': sub = {k:v for k,v in kd.items() if k>=1}
    elif first=='d': sub = {0:kd[0]}
    else: sub = {k:v for k,v in kd.items() if k<=-1}
    k_rec = max(sub.items(), key=lambda x:x[1])
    # 市场
    mk = {}
    if m['had']:
        mh, md, ma = float(m['had']['h']), float(m['had']['d']), float(m['had']['a'])
        psh = shin([mh,md,ma])
        mk['HAD'] = {'odds':[mh,md,ma], 'shin':[round(x,4) for x in psh]}
    hh_odds = [float(m['hhad']['h']), float(m['hhad']['d']), float(m['hhad']['a'])]
    mk['HHAD'] = {'line': line, 'odds': hh_odds, 'shin':[round(x,4) for x in shin(hh_odds)]}
    crs_o = {}
    for k,v in m['crs'].items():
        if not k.startswith('s') or k.endswith('f'): continue
        mm = k if k.startswith('s1s') else None
        if mm:
            crs_o[{'s1sa':'其他-主胜','s1sd':'其他-平局','s1sh':'其他-客胜'}[k]] = float(v)
        else:
            hh_, aa_ = int(k[1:3]), int(k[4:6])
            crs_o[f'{hh_}-{aa_}' + ('+' if hh_==5 or aa_==5 else '')] = float(v)
    mk['CRS_odds'] = crs_o
    mk['TTG_odds'] = {k[1:]: float(v) for k,v in m['ttg'].items() if k.startswith('s') and not k.endswith('f')}
    mk['HAFU_odds'] = {k: float(v) for k,v in m['hafu'].items() if k in hafu and not k.endswith('f')}
    ou2 = sum(v for k,v in ttg.items() if int(k) <= 2)
    top2 = sorted(ttg.items(), key=lambda x:-x[1])[:2]
    tg = sorted([int(k) for k in ttg], key=lambda t:-ttg[str(t)])[0]
    if tg <= 1: bucket = '闷战超小球（0-1）'
    elif tg == 2: bucket = '小球（1-2）' if ou2 > 0.5 else '常规正常球（2-3）'
    elif tg == 3: bucket = '常规正常球（2-3）'
    elif tg <= 5: bucket = '大球（4-5）'
    else: bucket = '超大球（5-6）or 穿盘（6-7+）'
    gap = [round(ph - mk['HAD']['shin'][0], 4), round(pd - mk['HAD']['shin'][1], 4), round(pa - mk['HAD']['shin'][2], 4)] if 'HAD' in mk else None
    out.append({
        'num': num, 'home': m['homeTeamAbbName'], 'away': m['awayTeamAbbName'], 'league': league,
        'time': m['matchTime'], 'date': m['matchDate'], 'single': m['bettingSingle'],
        'lam': lam, 'probs': {'HAD':[round(ph,4),round(pd,4),round(pa,4)], 'HHAD':[round(hh,4),round(hd,4),round(ha,4)],
        'TTG':{k:round(v,4) for k,v in ttg.items()}, 'HAFU':{k:round(v,4) for k,v in hafu.items()},
        'scores':[(s,round(p,4)) for s,p in scores], 'ht_scores':[(s,round(p,4)) for s,p in ht_scores],
        'k_dist':[k_dist[0],round(k_dist[1],4)], 'k_rec':[k_rec[0],round(k_rec[1],4)], 'first':first,
        'ou25':[round(ou2,4), round(1-ou2,4)], 'top2_ttg':[[k,round(v,4)] for k,v in top2], 'bucket':bucket, 'gap':gap},
        'market': mk,
    })

json.dump(out, open('reports/data/20261113_model_output.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
for r in out:
    p = r['probs']
    print(r['num'], r['home'], 'vs', r['away'], '| λ', r['lam']['final'], '| HAD', p['HAD'], '| HHAD', p['HHAD'], '| k_dist', p['k_dist'], 'k_rec', p['k_rec'])
    print('   TTG', p['TTG'])
    print('   scores', p['scores'][:6], '| HT', p['ht_scores'], '| HAFU', sorted(p['HAFU'].items(), key=lambda x:-x[1])[:4])
    if 'HAD' in r['market']: print('   mkt HAD shin', r['market']['HAD']['shin'], 'odds', r['market']['HAD']['odds'], '| HHAD shin', r['market']['HHAD']['shin'], 'odds', r['market']['HHAD']['odds'], 'line', r['market']['HHAD']['line'])
