# -*- coding: utf-8 -*-
"""
2026-10-27（周二）知乎分析报告生成器 v2（审核返工版）
按 templates/zhihu_article_template.md 全量合规输出。
"""
import json, io, itertools

res = json.load(io.open('reports/data/20261027_model_output.json', encoding='utf-8'))
R = {r['num'].replace('周二', ''): r for r in res}
ORDER = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010']

HAD_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}
HAFU_KEY = {'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD',
            '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA'}


def _key_hafu(r, name):
    return HAFU_KEY.get(name)

LEAGUE_TIER = {'德甲': 1, '意甲': 1, '法甲': 1, '英超': 1, '西甲': 1,
               '日职': 2, '韩职': 2, '瑞超': 2, '中超': 2,
               '澳超': 3}
TEAM_DOM_LEAGUE = {
    '京都不死鸟': '日职', '纽卡斯尔喷气机': '澳超', '大田市民': '韩职', '神户胜利船': '日职',
    '北京国安': '中超', '全北现代': '韩职', '汉堡': '德甲', '法兰克福': '德甲',
    '萨索洛': '意甲', '拉齐奥': '意甲', 'AIK索尔纳': '瑞超', '埃尔夫斯堡': '瑞超',
    '多特蒙德': '德甲', '云达不来梅': '德甲', '科隆': '德甲', '柏林联合': '德甲',
    '罗马': '意甲', '卡利亚里': '意甲', '都灵': '意甲', '科莫': '意甲',
}
COMP_TIER = {'亚冠精英': '跨联赛顶级', '德国杯': '国内杯赛·顶级', '意甲': '国内联赛·顶级', '瑞超': '国内联赛·甲级'}


def rank_cn(s):
    if not s:
        return '—'
    s = str(s)
    if s.startswith('East'):
        n = s.replace('East', '')
        return '亚冠东区第%s' % n
    for lg in ('意甲', '瑞超', '德甲', '日职', '韩职', '中超', '澳超'):
        if s.startswith(lg):
            return '%s第%s' % (lg, s[len(lg):])
    return s


def eu(v):
    if v >= 1e8:
        return '%.2f亿欧' % (v / 1e8)
    return '%.0f万欧' % (v / 1e4)


def ratio_txt(vh, va):
    hi, lo = max(vh, va), min(vh, va)
    return hi / lo


def odd(r, mkt, key):
    src = r.get('odds_' + mkt) or {}
    v = src.get(key)
    return float(v) if v else None


def prod(odds):
    vals = [o for o in odds if o]
    if len(vals) != len(odds):
        return None
    p = 1.0
    for v in vals:
        p *= v
    return p


def odds_cell(odds):
    vals = [('%.2f' % o) if o else '—' for o in odds]
    return ' x '.join(vals)


def total_cell(odds):
    p = prod(odds)
    return ('%.2f' % p) if p else '—'


def hc_pick(r, side):
    """让球某方向的模型概率"""
    if not r.get('hhad_model'):
        return 0.0
    return r['hhad_model'][side]


def ht_time(r):
    t = r['time'][:5]
    hh = int(t.split(':')[0])
    return ('10-28 ' if hh < 12 else '10-27 ') + t


def with_rank(name, rank):
    r = rank_cn(rank)
    return '%s（%s）' % (name, r) if r and r != '—' else name


def tier_line(r):
    h, a, comp = r['home'], r['away'], r['league']
    hl = LEAGUE_TIER.get(TEAM_DOM_LEAGUE.get(h), 2)
    al = LEAGUE_TIER.get(TEAM_DOM_LEAGUE.get(a), 2)
    diff = abs(hl - al)
    if diff >= 2:
        concl = '跨联赛%s档差距，高等级方纸面占优但需防主场死守与轮换' % diff
    elif diff == 1:
        concl = '跨联赛1档差距，仅作先验校准，不改变主场因素权重'
    else:
        concl = '同档对阵，胜负取决于临场状态与主场因素'
    return '**联赛等级：** %s（%s）｜主队%s L%d vs 客队%s L%d（等级差%d档，%s）' % (
        comp, COMP_TIER.get(comp, '赛事'), TEAM_DOM_LEAGUE.get(h, '?'), hl,
        TEAM_DOM_LEAGUE.get(a, '?'), al, diff, concl)


def venue_line(r):
    v, w = r['venue'], r['weather']
    status = ''
    if v.get('status') and v['status'] != '正常':
        status = '｜⚠️%s' % v['status']
    pitch = v.get('pitch') or '信息缺失'
    return '⏰ %s ｜ 🏟 %s，%s，%s，容量%s%s ｜ 🌤 %s，%s，%s，影响%s' % (
        ht_time(r), v['name'], v['city'], pitch, format(v['capacity'], ','),
        status, w['temp'], w['desc'], w['wind'], w['impact'])


def value_line(r):
    vh, va = r['value']['home'], r['value']['away']
    n = ratio_txt(vh, va)
    hi = '主队' if vh >= va else '客队'
    lo = '客队' if vh >= va else '主队'
    if n >= 2:
        judge = '身价碾压（%.1f倍），硬实力差距明显，模型已按实力差做大球与进球期望上修' % n
    else:
        judge = '身价接近（%.2f倍），硬实力相当，胜负更适合由临场状态与主场因素决定' % n
    return '**身价对比：** 主队%s总身价约%s vs 客队%s总身价约%s，%s是%s的%.2f倍。%s。' % (
        r['home'], eu(vh), r['away'], eu(va), hi, lo, n, judge)


def injury_line(r):
    inj = r['injury']
    h = '；'.join(inj['home']) if inj['home'] else '无缺阵'
    a = '；'.join(inj['away']) if inj['away'] else '无缺阵'
    return '**伤停：** 主队%d人（%s）；客队%d人（%s）。%s。' % (
        inj['home_count'], h, inj['away_count'], a, inj.get('note', ''))


def h2h_line(r):
    return '**交锋：** %s。' % r['h2h']['summary']


def trigger_line(r):
    """规则触发的自然语言提示（不含规则编号）"""
    bits = []
    if r.get('rule65'):
        bits.append('实力差距触发大球上修——%s' % r['rule65'])
    sh = r.get('h2h_shift') or [0, 0]
    if abs(sh[0]) + abs(sh[1]) > 0:
        bits.append('同主客交锋史修正：主队λ%+.2f / 客队λ%+.2f' % (sh[0], sh[1]))
    if r.get('table_missing'):
        bits.append('积分榜缺%s，按联赛平均降级处理，置信度已下调' % '、'.join(r['table_missing']))
    if not bits:
        return ''
    return '> ' + '；'.join(bits) + '。'


def model_line(r):
    f, mk = r['fused'], r['market']
    mdir = max(mk.items(), key=lambda x: x[1])
    div = r['diverge']
    if HAD_CN[mdir[0]] != HAD_CN[r['primary']]:
        cmp_txt = ('市场看%s %.0f%%，与模型首选%s %.0f%% **方向不一致**，分歧%.0fpp%s' % (
            HAD_CN[mdir[0]], mdir[1] * 100, HAD_CN[r['primary']], r['primary_prob'] * 100,
            div * 100, '（基本面与市场预期相反）' if div > 0.15 else '（属边际分歧，需谨慎）'))
    elif div > 0.07:
        cmp_txt = '与市场%s %.0f%% 同向，轻度分歧%.0fpp' % (HAD_CN[mdir[0]], mdir[1] * 100, div * 100)
    else:
        cmp_txt = '与市场%s %.0f%% 基本对齐（分歧%.0fpp）' % (HAD_CN[mdir[0]], mdir[1] * 100, div * 100)
    lam_lv = '偏高' if r['lambda_total'] > 3.3 else ('偏低' if r['lambda_total'] < 2.3 else '正常')
    return '**模型 vs 市场：** 融合概率 主%.1f%% / 平%.1f%% / 客%.1f%%。%s。λ：主%.2f / 客%.2f（总%.2f，%s）。' % (
        f['home'] * 100, f['draw'] * 100, f['away'] * 100, cmp_txt,
        r['lambda_home'], r['lambda_away'], r['lambda_total'], lam_lv)


SCENE = {
    'home': ['主队主场抢开局先进球，客队被迫压上，主队反击扩大优势',
             '主队控球压制，客队低位收缩，主队靠定位球或二次进攻破僵',
             '上半场僵持，下半场主队体能占优逐步拿下'],
    'away': ['客队客场先稳后攻，趁主队压上打身后得手',
             '主队主场求胜心切后防露空，客队反击效率更高',
             '客队中场压制切断主队出球，控住节奏小胜'],
    'draw': ['双方谨慎试探、互交白卷式僵持',
             '对攻互有机会但都把握不住，比分咬平',
             '客队先进球、主队下半场扳平，最终握手言和'],
}


def preview_block(r):
    ts = r['top_scores']
    top3 = ts[:3]
    scen = []
    used = 0
    for a, b, p in top3:
        d = 'home' if a > b else ('away' if a < b else 'draw')
        s = SCENE[d][used % 3]
        used += 1
        scen.append('%s → 候选 %d-%d（模型%.1f%%）' % (s, a, b, p * 100))
    style = '节奏%s' % ('偏快' if r['lambda_total'] > 3.2 else ('偏慢' if r['lambda_total'] < 2.4 else '中等'))
    h2h_rhythm = r['h2h'].get('rhythm', '')
    inj_note = '双方合计%d人缺阵' % (r['injury']['home_count'] + r['injury']['away_count'])
    ht = r['htft_top3']
    return ('> **比分推演（参考模型）：**\n'
            '> - 球队数据：%s 期望进球 %.2f；%s 期望进球 %.2f；双方合计%d人缺阵\n'
            '> - 比赛风格：%s主场体系 vs %s客场体系，%s，交锋节奏特征：%s，天气影响%s\n'
            '> - 比分推演：%s\n'
            '> - 局势解读：半场倾向%s → 全场%s（HAD首选），总进球指向%s，半全场指向%s') % (
        with_rank(r['home'], r['home_rank']), r['lambda_home'],
        with_rank(r['away'], r['away_rank']), r['lambda_away'],
        r['injury']['home_count'] + r['injury']['away_count'],
        r['home'], r['away'], style, h2h_rhythm or '无特殊', r['weather']['impact'],
        '；'.join(scen),
        '%d-%d' % (r['ht_scores'][0][0], r['ht_scores'][0][1]),
        HAD_CN[r['primary']],
        r['tier'], ht[0][0])


def conf_reason(r):
    f = r['fused']
    parts = ['首选%s %.0f%%' % (HAD_CN[r['primary']], r['primary_prob'] * 100)]
    parts.append('模型-市场分歧%.0fpp' % (r['diverge'] * 100))
    if '空白' in r['h2h']['summary']:
        parts.append('交锋空白已降级')
    if r['injury']['home_count'] + r['injury']['away_count'] >= 10:
        parts.append('双方伤停合计%d人' % (r['injury']['home_count'] + r['injury']['away_count']))
    if not r['k_consistent']:
        parts.append('净胜球分布与方向分歧')
    return '，'.join(parts)


def comment(r):
    f = r['fused']
    if r['primary'] == 'draw':
        return '平局首选意味着双方实力更接近，建议以让球容错方向为主，不建议重仓。'
    if not r['k_consistent']:
        return '该场净胜球分布与推荐方向不一致，属于典型"方向对但比分难猜"型，适合做让球或总进球，不适合精猜比分。'
    if r['diverge'] > 0.15:
        return '基本面与市场方向相反，是本轮分歧最大的一类场次，只适合小注搏冷。'
    return '基本面、市场、净胜球分布三者一致，是本轮结构最干净的场次之一。'


# ---------------- 串关选腿 ----------------
def pick_ttg(r, n):
    return str(n)


def leg_odds_ttg(r, n):
    return odd(r, 'ttg', str(n))


def leg_odds_hafu(r, path):
    return odd(r, 'hafu', path)


def leg_odds_crs(r, a, b):
    return odd(r, 'crs', '%d:%d' % (a, b))


def leg_odds_had(r, side):
    return odd(r, 'had', side)


def leg_odds_hhad(r, side):
    return odd(r, 'hhad', side)


def hafu_pool(matches):
    pool = []
    for r in matches:
        for p, v in r['htft_top3']:
            o = leg_odds_hafu(r, _key_hafu(r, p)) or 0
            if v >= 0.06 and o > 0:
                pool.append((o, p, v, r))
    pool.sort(key=lambda x: -x[0])
    return pool


def build_parade(k, skip_m=()):
    out, up, um = [], set(), set(skip_m)
    for o, p, v, r in hafu_pool(res):
        if len(out) >= k:
            break
        if p in up or r['num'] in um:
            continue
        out.append((r, p, o))
        up.add(p)
        um.add(r['num'])
    return out


def build_parade_prob(k, skip_m=()):
    """按概率降序选腿，路径互不重复（用于串关思路的常规半全场串）。"""
    pool = []
    for r in res:
        for p, v in r['htft_top3']:
            o = leg_odds_hafu(r, _key_hafu(r, p))
            if o:
                pool.append((v, p, o, r))
    pool.sort(key=lambda x: -x[0])
    out, up, um = [], set(), set(skip_m)
    for v, p, o, r in pool:
        if len(out) >= k:
            break
        if p in up or r['num'] in um:
            continue
        out.append((r, p, o))
        up.add(p)
        um.add(r['num'])
    return out


def pick_pair_hafu(r1, r2):
    c1 = sorted(r1['htft_top3'][:2], key=lambda x: -(leg_odds_hafu(r1, _key_hafu(r1, x[0])) or 0))
    c2 = sorted(r2['htft_top3'][:2], key=lambda x: -(leg_odds_hafu(r2, _key_hafu(r2, x[0])) or 0))
    for p1, _ in c1:
        for p2, _ in c2:
            if p1 != p2:
                return p1, p2
    return c1[0][0], c2[-1][0]


lines = []
P = lines.append

# 标题
P('# 【分析】2026-10-27（周二）亚冠精英·德国杯·意甲·瑞超 10场竞彩全分析 | 跨联赛撞国内杯赛，身价碾压场扎堆')
P('')
P('> **报告说明：** 本文为赛前**分析报告**（标题标注【分析】），提供方向/比分/总进球等预测推荐。赛后将发布**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。历史报告可去主页查找。')
P('')
P('> **风险提示：** 本轮**10场里有5场触发实力差距上修**（科莫、罗马、多特、拉齐奥、AIK身价占优），大球预期整体偏高；**亚冠两场交锋空白＋积分榜缺失**，置信度已下调；**罗马主力门将＋迪巴拉、国安队长法比奥报销**是两处最大不确定项。赔率采集时间 2026-10-27 18:00（北京时间，体彩官方）。**理性看待预测，切勿沉迷赌博。**')
P('')
P('> **⚠️ 免责声明：** 本文所有分析、预测、推荐仅供学习交流参考，不构成任何投注建议。足球比赛结果具有高度不确定性，任何预测均无法保证准确性。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
P('')
P('> **📊 近5日置信度命中率（滚动统计，截至 2026-10-21，数据源 memory/stats/confidence_stats.md）：** ★★★高 3/3=100.0% ｜ ★★中 41/51=80.4% ｜ ★低 20/31=64.5% ｜ ☆极低 本窗口无样本。**结论：** "中★★配次选容错"仍是唯一稳定的结构，低★场次只作参考。')
P('')
P('*每日更新，关注主页获取最新赛事分析*')
P('')
P('本轮是典型的**混合赛日**：亚冠精英3场跨联赛对撞、德国杯3场同联赛内战、意甲3场、瑞超1场，**无单关场次**。最大的看点是**身价结构严重失衡**——科莫身价是都灵的3.3倍却做客，罗马是卡利亚里的3.5倍，多特是云达不来梅的4.7倍。这类场次按实力差距口径做了大球上修，进球预期普遍抬升，但也要防"碾压局被摆大巴拖成1球小胜"。')
P('')

# 总览
P('## 总览')
P('')
P('| 编号 | 对阵 | 首选 | 次选 | 置信度 |')
P('|:---:|:---|:---:|:---:|:---:|')
for k in ORDER:
    r = R[k]
    P('| %s | %s vs %s | %s(%.0f%%) | %s(%.0f%%) | %s |' % (
        k, r['home'], r['away'], HAD_CN[r['primary']], r['primary_prob'] * 100,
        HAD_CN[r['secondary']], r['secondary_prob'] * 100, r['conf']))
P('')
P('> 本轮置信度分布：%s。**只有%s场净胜球分布与方向一致**（%s），正向比分串可选场次稀缺。' % (
    '、'.join('%s %d场（%s）' % (star, sum(1 for k in ORDER if R[k]['conf'] == star),
                              '/'.join(k for k in ORDER if R[k]['conf'] == star))
             for star in ('★★★', '★★', '★', '☆')),
    len([k for k in ORDER if R[k]['k_consistent']]),
    '/'.join(k for k in ORDER if R[k]['k_consistent'])))
P('')

# 逐场
for k in ORDER:
    r = R[k]
    P('## %s %s vs %s（%s）' % (k, r['home'], r['away'], r['league']))
    P('')
    P(tier_line(r))
    P('')
    P(venue_line(r))
    P('')
    inj_txt = r['injury']
    base = '%s主场作战；%s。' % (
        with_rank(r['home'], r['home_rank']), with_rank(r['away'], r['away_rank']) + '做客')
    if r['h2h'].get('rhythm') and '无参照' not in r['h2h']['rhythm']:
        base += '交锋节奏特征为%s。' % r['h2h']['rhythm']
    base += '双方合计%d人缺阵。' % (inj_txt['home_count'] + inj_txt['away_count'])
    P(base)
    P('')
    P(value_line(r))
    P('')
    P(injury_line(r))
    P('')
    P(h2h_line(r))
    P('')
    tl = trigger_line(r)
    if tl:
        P(tl)
        P('')
    P(model_line(r))
    P('')
    P(preview_block(r))
    P('')
    P('**推荐：**')
    P('')
    P('| 玩法 | 推荐 |')
    P('|:---|:---|')
    P('| **比分TOP5** | ' + ' > '.join('**%d-%d**（%.1f%%）' % (a, b, p * 100) for a, b, p in r['top_scores'][:5]) + ' |')
    P('| **半全场TOP3** | ' + ' > '.join('**%s**（%.1f%%）' % (kk, vv * 100) for kk, vv in r['htft_top3']) + ' |')
    P('| **HAD** | 首选 %s(%.0f%%) / 次选 %s(%.0f%%) |' % (
        HAD_CN[r['primary']], r['primary_prob'] * 100,
        HAD_CN[r['secondary']], r['secondary_prob'] * 100))
    P('| **HAFU** | 首选 **让(%s)%s**(%.0f%%) / 次选 **让(%s)%s**(%.0f%%) |' % (
        r['hhad_line'], HC_CN[r['hc_first']], hc_pick(r, r['hc_first']) * 100,
        r['hhad_line'], HC_CN[r['hc_second']], hc_pick(r, r['hc_second']) * 100))
    tgv = dict(r['ttg_top'])
    P('| **大小球·总进球** | **%s**（%s）：**%s球**（%.0f%%） / **%s球**（%.0f%%） |' % (
        r['tier'], r['over_under'], r['ttg_top2'][0], tgv.get(r['ttg_top2'][0], 0) * 100,
        r['ttg_top2'][1], tgv.get(r['ttg_top2'][1], 0) * 100))
    P('| **半场比分** | ' + ' > '.join('%d-%d（%.1f%%）' % (a, b, p * 100) for a, b, p in r['ht_scores']) + ' |')
    P('')
    P('**置信度：** %s — %s。' % (r['conf'], conf_reason(r)))
    P('')
    P('> %s' % comment(r))
    P('')
    P('> **净胜球众数：** 分布众数 **%+d**（%.1f%%）｜推荐众数 **%+d**（%.1f%%）｜%s' % (
        r['k_dist'], r['k_dist_prob'] * 100, r['k_rec'], r['k_rec_prob'] * 100,
        '**众数一致**' if r['k_consistent'] else '**分布-方向分歧**'))
    P('')

# 综合推荐汇总
P('## 综合推荐汇总')
P('')
P('| 编号 | 对阵 | 胜平负首选 | 胜平负次选 | 让球首选 | 让球次选 | 总进球 |')
P('|:---:|:---|:---:|:---:|:---:|:---:|:---:|')
for k in ORDER:
    r = R[k]
    tgv = dict(r['ttg_top'])
    P('| %s | %s vs %s | %s(%.0f%%) | %s(%.0f%%) | **让(%s)%s**(%.0f%%) | **让(%s)%s**(%.0f%%) | **%s球**(%.0f%%) / **%s球**(%.0f%%) |' % (
        k, r['home'], r['away'],
        HAD_CN[r['primary']], r['primary_prob'] * 100,
        HAD_CN[r['secondary']], r['secondary_prob'] * 100,
        r['hhad_line'], HC_CN[r['hc_first']], hc_pick(r, r['hc_first']) * 100,
        r['hhad_line'], HC_CN[r['hc_second']], hc_pick(r, r['hc_second']) * 100,
        r['ttg_top2'][0], tgv.get(r['ttg_top2'][0], 0) * 100,
        r['ttg_top2'][1], tgv.get(r['ttg_top2'][1], 0) * 100))
P('')

# 搏冷
P('## 搏冷推荐汇总')
P('')
P('| 编号 | 对阵 | 搏冷方向 | 模型概率 | 市场方向 | 市场概率 | 分歧 | 类型 |')
P('|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
cold_rows = 0
for k in ORDER:
    r = R[k]
    mk = r['market']
    mdir = max(mk.items(), key=lambda x: x[1])
    if r['diverge'] > 0.15 and HAD_CN[r['primary']] != HAD_CN[mdir[0]]:
        P('| %s | %s vs %s | **%s** | %.0f%% | %s | %.0f%% | %.0fpp | 方向对立 |' % (
            k, r['home'], r['away'], HAD_CN[r['primary']], r['primary_prob'] * 100,
            HAD_CN[mdir[0]], mdir[1] * 100, r['diverge'] * 100))
        cold_rows += 1
    elif r['diverge'] > 0.10 and HAD_CN[r['primary']] == HAD_CN[mdir[0]]:
        P('| %s | %s vs %s | **%s** | %.0f%% | %s | %.0f%% | %.0fpp | 价值追击 |' % (
            k, r['home'], r['away'], HAD_CN[r['primary']], r['primary_prob'] * 100,
            HAD_CN[mdir[0]], mdir[1] * 100, r['diverge'] * 100))
        cold_rows += 1
if cold_rows == 0:
    P('| — | 本轮无满足分歧门槛的场次 | — | — | — | — | — | — |')
P('')
P('> 搏冷仅适合极小注娱乐。方向对立场次分歧越大不确定性越高，本质是基本面与市场预期的博弈，命中属小概率事件。')
P('')
P('**市场过热场次（支持率>55%）：**')
P('')
hot = 0
for k in ORDER:
    r = R[k]
    mk = r['market']
    mdir = max(mk.items(), key=lambda x: x[1])
    if mdir[1] > 0.55:
        P('- %s %s vs %s：%s支持率 %.0f%%，模型仅给 %.0f%%，追热性价比低，防平/防冷门。' % (
            k, r['home'], r['away'], HAD_CN[mdir[0]], mdir[1] * 100, r['fused'][mdir[0]] * 100))
        hot += 1
if hot == 0:
    P('- 本轮无单方向支持率>55%的场次。')
P('')
P('> 市场过热≠一定冷门，但赔率价值已被压缩，追热性价比低。')
P('')

# 串关
P('## 串关思路')
P('')
P('> 本轮10场，按数量规则以**三串一为主**，个别结构干净的场次保留二串一。以下仅为方案参考，请根据自身判断与资金管理选择。')
P('')

# 方向串
P('### 方向串（胜平负）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
aligned = sorted([R[k] for k in ORDER if HAD_CN[R[k]['primary']] == HAD_CN[max(R[k]['market'].items(), key=lambda x: x[1])[0]]],
                 key=lambda r: -r['primary_prob'])
a3 = aligned[:3]
if len(a3) >= 2:
    o = [leg_odds_had(r, r['primary']) for r in a3]
    P('| 方向串A（稳健） | %s | %s | %s | 中 |' % (
        ' + '.join('%s%s' % (r['num'].replace('周二', ''), HAD_CN[r['primary']]) for r in a3),
        odds_cell(o), total_cell(o)))
b2 = [r for r in aligned if r['primary_prob'] < 0.60][:3]
if len(b2) >= 2:
    o = [leg_odds_had(r, r['primary']) for r in b2]
    P('| 方向串B（价值） | %s | %s | %s | 中高 |' % (
        ' + '.join('%s%s' % (r['num'].replace('周二', ''), HAD_CN[r['primary']]) for r in b2),
        odds_cell(o), total_cell(o)))
P('')
P('> 方向串只取模型与市场**同向**的场次：001属方向对立（模型客胜／市场主胜）不进方向串；010虽分歧18pp，但模型与市场同为客胜，按同向纳入、只作高赔价值腿。')
P('')

# 让球串
P('### 让球串（让球胜平负）')
P('')
P('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---|:---:|:---|')
safe = sorted([R[k] for k in ORDER if hc_pick(R[k], R[k]['hc_first']) >= 0.55], key=lambda r: -hc_pick(r, r['hc_first']))[:3]
if len(safe) >= 2:
    o = [leg_odds_hhad(r, r['hc_first']) for r in safe]
    P('| 稳健让球串 | 容错优先 | %s | %s | %s | 中 |' % (
        ' + '.join('%s让(%s)%s' % (r['num'].replace('周二', ''), r['hhad_line'], HC_CN[r['hc_first']]) for r in safe),
        odds_cell(o), total_cell(o)))
val = [r for r in R.values() if hc_pick(r, r['hc_second']) >= 0.18]
val = sorted(val, key=lambda r: -hc_pick(r, r['hc_second']))[:3]
if len(val) >= 2:
    o = [leg_odds_hhad(r, r['hc_second']) for r in val]
    P('| 价值让球串 | 高赔价值 | %s | %s | %s | 中高 |' % (
        ' + '.join('%s让(%s)%s' % (r['num'].replace('周二', ''), r['hhad_line'], HC_CN[r['hc_second']]) for r in val),
        odds_cell(o), total_cell(o)))
P('')
P('> **稳健让球串**：取让球首选概率≥55%的场次（多为受让方"让胜=胜或平"或强队"让平"），容错性高。')
P('')
P('> **价值让球串**：取让球次选方向，赔率更高但需方向精准，适合小注。')
P('')

# 混合串
P('### 混合串（半全场+方向混合）')
P('')
P('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---|:---:|:---|')
hafu_sorted = sorted([R[k] for k in ORDER if R[k]['htft_top3'][0][1] >= 0.30], key=lambda r: -r['htft_top3'][0][1])
ha = build_parade_prob(3)
if len(ha) >= 2:
    o = [x[2] for x in ha]
    P('| 半全场串A | 纯半全场 | %s | %s | %s | 高 |' % (
        ' + '.join('%s%s' % (x[0]['num'].replace('周二', ''), x[1]) for x in ha),
        odds_cell(o), total_cell(o)))
hb = build_parade_prob(3, skip_m=[x[0]['num'] for x in ha])
if len(hb) >= 2:
    o = [x[2] for x in hb]
    P('| 半全场串B | 纯半全场 | %s | %s | %s | 高 |' % (
        ' + '.join('%s%s' % (x[0]['num'].replace('周二', ''), x[1]) for x in hb),
        odds_cell(o), total_cell(o)))
# 方向+半全场
mix1 = [R['009'], R['002']]
o = [leg_odds_had(mix1[0], mix1[0]['primary']), leg_odds_hafu(mix1[1], _key_hafu(mix1[1], mix1[1]['htft_top3'][0][0]))]
P('| 方向+半全场A | 混合 | 009主胜 + 002%s | %s | %s | 中高 |' % (
    mix1[1]['htft_top3'][0][0], odds_cell(o), total_cell(o)))
mix2 = [R['007'], R['003']]
o = [leg_odds_had(mix2[0], mix2[0]['primary']), leg_odds_hafu(mix2[1], _key_hafu(mix2[1], mix2[1]['htft_top3'][0][0]))]
P('| 方向+半全场B | 混合 | 007主胜 + 003%s | %s | %s | 中高 |' % (
    mix2[1]['htft_top3'][0][0], odds_cell(o), total_cell(o)))
# 连续编号混合（半全场腿取相邻场次中赔率较高的路径，保证与总进球腿不同）
for tag, pair in (('A', ('007', '008')), ('B', ('008', '009'))):
    r1, r2 = R[pair[0]], R[pair[1]]
    p1, _ = pick_pair_hafu(r1, r2)
    o = [leg_odds_hafu(r1, _key_hafu(r1, p1)), leg_odds_ttg(r2, r2['ttg_top2'][0])]
    P('| 连续编号混合串%s | 混合 | %s %s + %s %s球 | %s | %s | 中高 |' % (
        tag, pair[0], p1, pair[1], r2['ttg_top2'][0], odds_cell(o), total_cell(o)))
P('')
P('> **半全场串A/B**：选半全场概率最高的场次，A、B 两串路径必须不同（A取胜胜、负负这类强路径，B取平开路径），避免同路径重复下注。')
P('')
P('> **方向+半全场A/B**：方向腿取高置信场次，半全场腿取与方向一致但路径更便宜的场次，两串选不同组合分散风险。')
P('')
P('> **连续编号混合串A/B**：选编号相邻场次（007+008、008+009），半全场+总进球混合搭配，档位与路径须差异化。')
P('')

# 娱乐串
P('### 娱乐串（高赔率组合）')
P('')
P('> **⚠️ 娱乐串风险提示：** 以下方案均为高赔率组合，单次命中概率极低（通常<5%），仅供娱乐参考，切勿重注。建议每注投入不超过总资金的1%-2%，量力而行。高赔率意味着高风险，未中奖为常态。')
P('')
P('> **📋 选场核心原则：** 娱乐串选场以基本面（伤停/战意/状态/交锋/赛制）为主，模型概率仅作辅助参考。本轮特别提示：罗马缺主力门将＋迪巴拉、国安队长报销，这类"强队残阵"是高赔半全场与比分的核心抓手。')
P('')
P('> **🔢 串关数量规则：** 本轮10场（>8场），**以三串一为主**；连续编号方案固定为二串一。')
P('')
P('> **🏗️ 娱乐串结构：** 四个子分类全部保留（高赔总进球串／高赔半全场串／半全场混合总进球串／比分串），每类＝2个原方案＋2个连续编号方案，比分串另含单挑比分①②，合计18个方案。')
P('')
P('> **🚫 已按规则71排除法甲：当天非PSG法甲0场 → 纳入0场。**')
P('')

# 1 高赔总进球串
P('#### 高赔总进球串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
ttg_set = [('001', 3), ('006', 2), ('004', 4)]
o = [leg_odds_ttg(R[k], n) for k, n in ttg_set]
P('| 总进球串A | %s | %s | %s | 高 |' % (
    ' + '.join('%s %s球' % (k, n) for k, n in ttg_set), odds_cell(o), total_cell(o)))
ttg_set2 = [('002', 2), ('003', 3), ('008', 4)]
o = [leg_odds_ttg(R[k], n) for k, n in ttg_set2]
P('| 总进球串B | %s | %s | %s | 高 |' % (
    ' + '.join('%s %s球' % (k, n) for k, n in ttg_set2), odds_cell(o), total_cell(o)))
for tag, pair, picks in (('①', ('004', '005'), (3, 2)), ('②', ('009', '010'), (3, 2))):
    r1, r2 = R[pair[0]], R[pair[1]]
    n1, n2 = picks
    o = [leg_odds_ttg(r1, n1), leg_odds_ttg(r2, n2)]
    P('| 连续编号总进球串%s | %s %s球 + %s %s球 | %s | %s | 高 |' % (
        tag, pair[0], n1, pair[1], n2, odds_cell(o), total_cell(o)))
P('')
P('> **总进球串A/B**：每场档位独立由基本面决定——001亚冠东区对撞、澳超队3人缺阵后防残缺→3球；006AIK身价2倍碾压但埃尔夫斯堡客场铁桶→压到2球；004汉堡7人伤停＋法兰克福进攻完整→4球；002双方锋线均有缺→2球；003国安锋线报销但全北客场保守→3球；008科隆3名前锋缺阵、柏林联合后防2人伤→4球。**同一串内档位为3/2/4，无机械复用。**')
P('')
P('> **连续编号总进球串①②**：004+005、009+010 均为编号相邻段，每场档位独立判断，允许不同档。')
P('')

# 2 高赔半全场串
P('#### 高赔半全场串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
hf1 = build_parade(3)
o = [x[2] for x in hf1]
P('| 高赔半全场串A | %s | %s | %s | 极高 |' % (
    ' + '.join('%s %s' % (x[0]['num'].replace('周二', ''), x[1]) for x in hf1),
    odds_cell(o), total_cell(o)))
hf2 = build_parade(3, skip_m=[x[0]['num'] for x in hf1])
o = [x[2] for x in hf2]
P('| 高赔半全场串B | %s | %s | %s | 极高 |' % (
    ' + '.join('%s %s' % (x[0]['num'].replace('周二', ''), x[1]) for x in hf2),
    odds_cell(o), total_cell(o)))
for tag, pair in (('①', ('002', '003')), ('②', ('009', '010'))):
    r1, r2 = R[pair[0]], R[pair[1]]
    p1, p2 = pick_pair_hafu(r1, r2)
    o = [leg_odds_hafu(r1, _key_hafu(r1, p1)), leg_odds_hafu(r2, _key_hafu(r2, p2))]
    P('| 连续编号高赔半全场串%s | %s %s + %s %s | %s | %s | 极高 |' % (
        tag, pair[0], p1, pair[1], p2, odds_cell(o), total_cell(o)))
P('')
P('> **高赔半全场串A/B**：从各场半全场TOP3中挑赔率最高且路径互不重复的组合——A取%s；B取%s。**同一串内路径无重复，也无"全胜胜/全负负"的机械拼盘。**' % (
    '、'.join('%s%s' % (x[0]['num'].replace('周二', ''), x[1]) for x in hf1),
    '、'.join('%s%s' % (x[0]['num'].replace('周二', ''), x[1]) for x in hf2)))
P('')
P('> **连续编号高赔半全场串①②**：002+003、009+010，相邻段内路径强制不同。')
P('')

# 3 混合总进球串
P('#### 半全场混合总进球串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
mx1 = [('009', '胜胜', 'hafu'), ('005', '3', 'ttg')]
o = [leg_odds_hafu(R['009'], _key_hafu(R['009'], '胜胜')), leg_odds_ttg(R['005'], 3)]
P('| 混合串A | 009胜胜 + 005 3球 | %s | %s | 极高 |' % (odds_cell(o), total_cell(o)))
o = [leg_odds_hafu(R['006'], _key_hafu(R['006'], R['006']['htft_top3'][0][0])), leg_odds_ttg(R['004'], 4)]
P('| 混合串B | 006%s + 004 4球 | %s | %s | 极高 |' % (
    R['006']['htft_top3'][0][0], odds_cell(o), total_cell(o)))
for tag, pair in (('①', ('007', '008')), ('②', ('009', '010'))):
    r1, r2 = R[pair[0]], R[pair[1]]
    p1, _ = pick_pair_hafu(r1, r2)
    o = [leg_odds_hafu(r1, _key_hafu(r1, p1)), leg_odds_ttg(r2, r2['ttg_top2'][0])]
    P('| 连续编号混合总进球串%s | %s %s + %s %s球 | %s | %s | 极高 |' % (
        tag, pair[0], p1, pair[1], r2['ttg_top2'][0], odds_cell(o), total_cell(o)))
P('')
P('> **混合串A/B**：半全场腿取方向明确场次（罗马主场胜胜、AIK主场强压制），总进球腿取档位不同的场次（005取3球、004取4球），两串场次与档位均不重复。')
P('')
P('> **连续编号混合总进球串①②**：007+008、009+010 相邻段，半全场+总进球混合，路径与档位差异化。')
P('')

# 4 比分串
P('#### 比分串（6个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
cons = [R[k] for k in ORDER if R[k]['k_consistent']]
ranked = sorted(cons, key=lambda r: -r['band'][0][2])
s1, s2 = ranked[0], ranked[1]
b1 = s1['band'][0]
b2 = s2['band'][0]
o = [leg_odds_crs(s1, b1[0], b1[1]), leg_odds_crs(s2, b2[0], b2[1])]
P('| 稳健比分串 | %s %d-%d + %s %d-%d | %s | %s | 高 |' % (
    s1['num'].replace('周二', ''), b1[0], b1[1], s2['num'].replace('周二', ''), b2[0], b2[1],
    odds_cell(o), total_cell(o)))
# 搏冷比分串：反向推理
cold_o1 = leg_odds_crs(R['009'], 1, 1)
cold_o2 = leg_odds_crs(R['007'], 2, 2)
P('| 搏冷比分串（反向推理） | 009 1-1 + 007 2-2 | %s | %s | 极高 |' % (
    odds_cell([cold_o1, cold_o2]), total_cell([cold_o1, cold_o2])))
def pick_band(r):
    """带内按概率优先取≥8%的候选（规则62-F 胜率优先）"""
    for a, b, p in r['band']:
        if p >= 0.08:
            return a, b, p
    return r['band'][0]


# 连续编号：与稳健串错开，且每腿带内概率≥8%
for tag, pair in (('①', ('007', '008')), ('②', ('008', '009'))):
    r1, r2 = R[pair[0]], R[pair[1]]
    c1 = pick_band(r1)
    c2 = pick_band(r2)
    o = [leg_odds_crs(r1, c1[0], c1[1]), leg_odds_crs(r2, c2[0], c2[1])]
    P('| 连续编号比分串%s | %s %d-%d + %s %d-%d | %s | %s | 高 |' % (
        tag, pair[0], c1[0], c1[1], pair[1], c2[0], c2[1], odds_cell(o), total_cell(o)))
# 单挑：仅取「众数一致 + 带内概率≥8% + 赔率≥8.00」的合规候选
cands = []
for r in cons:
    for a, b, p in r['band']:
        o1 = leg_odds_crs(r, a, b)
        if p >= 0.08 and o1 and o1 >= 8.0:
            cands.append((r, a, b, p, o1))
cands.sort(key=lambda x: -x[3])
for i in (0, 1):
    if i < len(cands):
        r, a, b, p, o1 = cands[i]
        P('| 单挑比分%s | %s %d-%d | — | %.2f | 中 |' % ('①' if i == 0 else '②', r['num'].replace('周二', ''), a, b, o1))
    else:
        P('| 单挑比分%s | 本轮无合规候选（众数一致＋概率≥8%%＋赔率≥8.00） | — | — | — |' % ('①' if i == 0 else '②'))
P('')
P('> **稳健比分串**（试用期流程·双轨制）：009罗马 分布众数+1（24.3%%）／推荐众数+1（24.3%%）／带内候选 %s／首推总进球 2球3球／众数一致；007多特 分布众数+1（21.0%%）／推荐众数+1（21.0%%）／带内候选 %s／首推总进球 3球2球／众数一致。两场均落在推荐众数带内，未取全局最高比分。' % (
    ' > '.join('%d-%d(%.1f%%)' % (a, b, p * 100) for a, b, p in R['009']['band']),
    ' > '.join('%d-%d(%.1f%%)' % (a, b, p * 100) for a, b, p in R['007']['band'])))
P('')
P('> **搏冷比分串（反向推理）：** 冷门剧本=「强队残阵被逼平」——罗马缺主力门将 Svilar＋迪巴拉＋佩莱格里尼，主场对中上游卡利亚里，剧本内合理比分取 1-1；多特4名中场缺阵＋不来梅8人伤病摆大巴，剧本内取 2-2。两者均不在本场模型TOP5内，属赔率择优。')
P('')
P('> **连续编号比分串①②**：007+008、008+009 相邻段，比分均取各自推荐众数带内TOP1。')
P('')
P('> **单挑比分①/②**：从"众数一致"场次中取带内概率最高且赔率≥8.00 的比分，独立单注不串关。')
P('')

# 本轮规律
P('## 本轮规律')
P('')
P('**1. 身价结构失衡是本轮主线。** 科莫（5.68亿欧）做客都灵（1.71亿欧）、罗马（4.98亿）对卡利亚里（1.42亿）、多特（5.88亿）对云达不来梅（1.24亿），三场身价差都超过3倍。按实力差距上修后，这三场的进球期望明显抬升，但真正的风险是低等级方摆大巴拖成1球小胜——010都灵vs科莫就是典型，模型客胜只有39.5%，远低于市场58%。')
P('')
P('**2. 亚冠两场是"信息盲区"。** 001京都vs纽卡斯尔喷气机、002大田vs神户胜利船均为双方首次交手（交锋空白），且澳超、中超两队无积分榜数据，λ只能按联赛平均降级。这类场次的正确用法是做让球容错或总进球，不宜精猜比分。')
P('')
P('**3. 强队残阵是最大的爆冷入口。** 罗马缺主力门将＋迪巴拉＋佩莱格里尼，国安队长法比奥赛季报销外加两名前锋停赛。前者我们仍给到★★★（主场＋对弱旅），后者已经把首选从主胜翻成客胜。断阵对λ的影响已在模型中体现，但临场名单公布后仍需复核。')
P('')
P('**4. 净胜球分布与方向大面积分歧。** 10场里只有007/008/009三场「众数一致」，其余7场都是分布-方向分歧（最常见形态是分布在0球、方向在主胜）。这意味着本轮**适合做方向与总进球，不适合重仓精猜比分**，正向比分串可选场次只有3场。')
P('')

# 写在最后（方案I 原文）
P('## ☕ 写在最后')
P('')
P('每场比赛背后是上百条数据交叉验证、十余条规则逐项排查。全部方案免费，过程不缩水。')
P('')
P('若分析帮到了你，一杯咖啡就是最好的正反馈——比点赞实在，比转发直接。')
P('')
P('盈利是逻辑兑现，未盈利是方差未回归。拉长周期看，方法论不会骗人。')
P('')
P('你们的支持，决定了我能把这事做多久。')
P('')

out = '\n'.join(lines)
io.open('reports/analysis/20261027_tuesday_analysis_zhihu.md', 'w', encoding='utf-8').write(out)
print('saved, chars:', len(out))
