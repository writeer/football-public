# -*- coding: utf-8 -*-
"""
2026-10-28（周三）知乎分析报告生成器
按 templates/zhihu_article_template.md 输出（17场）。
"""
import json, io

res = json.load(io.open('reports/data/20261028_model_output.json', encoding='utf-8'))
R = {r['num'].replace('周三', ''): r for r in res}
ORDER = ['%03d' % i for i in range(1, 18)]

HAD_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}
HAFU_KEY = {'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD',
            '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA'}

LEAGUE_TIER = {'德甲': 1, '意甲': 1, '法甲': 1, '英超': 1, '西甲': 1, '荷甲': 2,
               '日职': 2, '韩职': 2, '瑞超': 2, '中超': 2, '巴甲': 2, '美职': 2,
               '泰超': 3, '德乙': 3}
TEAM_DOM_LEAGUE = {
    '大阪钢巴': '日职', '布里兰': '泰超', '鹿岛鹿角': '日职', '浦项制铁': '韩职',
    '横滨水手': '日职', '广岛三箭': '日职', '帕德博恩': '德甲', '斯图加特': '德甲',
    '威尼斯': '意甲', '国际米兰': '意甲', 'AC米兰': '意甲', '博洛尼亚': '意甲',
    '帕尔马': '意甲', '乌迪内斯': '意甲', '鹿特丹斯巴达': '荷甲', '福图纳锡塔德': '荷甲',
    '布鲁马波卡纳': '瑞超', '赫根': '瑞超', '桑德兰': '英超', '布伦特福德': '英超',
    '伯恩茅斯': '英超', '阿斯顿维拉': '英超', '富勒姆': '英超', '水晶宫': '英超',
    '蒙扎': '意甲', '那不勒斯': '意甲', '热那亚': '意甲', '尤文图斯': '意甲',
    '利物浦': '英超', '切尔西': '英超', '弗鲁米嫩塞': '巴甲', '巴西国际': '巴甲',
    '迈阿密国际': '美职', '辛辛那提FC': '美职',
}
COMP_TIER = {
    '亚冠精英': '跨联赛顶级', '日联赛杯': '国内杯赛·顶级', '德国杯': '国内杯赛·顶级',
    '意甲': '国内联赛·顶级', '荷兰杯': '国内杯赛·甲级', '瑞超': '国内联赛·甲级',
    '英联赛杯': '国内杯赛·顶级', '巴甲': '国内联赛·甲级', '美职': '国内联赛·甲级',
}


def rank_cn(s):
    if not s:
        return '—'
    s = str(s)
    if s.startswith('East'):
        return '亚冠东区第%s' % s.replace('East', '')
    for lg in ('意甲', '瑞超', '德甲', '日职', '韩职', '中超', '澳超', '巴甲', '美职'):
        if s.startswith(lg):
            return '%s第%s' % (lg, s[len(lg):])
    return s


def eu(v):
    if v >= 1e8:
        return '%.2f亿欧' % (v / 1e8)
    return '%.0f万欧' % (v / 1e4)


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
    return ' x '.join(('%.2f' % o) if o else '—' for o in odds)


def total_cell(odds):
    p = prod(odds)
    return ('%.2f' % p) if p else '—'


def hc_pick(r, side):
    if not r.get('hhad_model'):
        return 0.0
    return r['hhad_model'][side]


def key_hafu(name):
    return HAFU_KEY.get(name)


def short(num):
    return num.replace('周三', '')


def ht_time(r):
    t = r['time'][:5]
    hh = int(t.split(':')[0])
    return ('10-29 ' if hh < 12 else '10-28 ') + t


def with_rank(name, rank):
    rr = rank_cn(rank)
    return '%s（%s）' % (name, rr) if rr and rr != '—' else name


def tier_line(r):
    h, a, comp = r['home'], r['away'], r['league']
    hl = LEAGUE_TIER.get(TEAM_DOM_LEAGUE.get(h), 2)
    al = LEAGUE_TIER.get(TEAM_DOM_LEAGUE.get(a), 2)
    diff = abs(hl - al)
    if diff >= 2:
        concl = '跨%s档差距，高等级方纸面占优，但杯赛轮换与低等级方死守会显著削弱差距' % diff
    elif diff == 1:
        concl = '跨1档差距，仅作先验校准，不改变主场因素权重'
    else:
        concl = '同档对阵，胜负取决于临场状态与主场因素'
    return '**联赛等级：** %s（%s）｜主队%s L%d vs 客队%s L%d（等级差%d档，%s）' % (
        comp, COMP_TIER.get(comp, '赛事'), TEAM_DOM_LEAGUE.get(h, '?'), hl,
        TEAM_DOM_LEAGUE.get(a, '?'), al, diff, concl)


def venue_line(r):
    v, w = r['venue'], r['weather']
    status = ''
    if v.get('status') and v['status'] != '正常':
        note = v.get('status_note') or ''
        status = '｜⚠️%s%s' % (v['status'], ('（%s）' % note) if note else '')
    pitch = v.get('pitch') or '信息缺失'
    return '⏰ %s ｜ 🏟 %s，%s，%s，容量%s%s ｜ 🌤 %s，%s，%s，影响%s' % (
        ht_time(r), v['name'], v['city'], pitch, format(v['capacity'], ','),
        status, w['temp'], w['desc'], w['wind'], w['impact'])


def form_line(r):
    f = r.get('form') or {}

    def one(side, name):
        d = f.get(side)
        if not d or not d.get('form'):
            return '%s近5场战绩未收录（跨体系球队，按联赛平均降级处理）' % name
        seq = ' '.join(d['form'])
        return '%s近5场 %s（%d分，联赛第%s，已赛%s轮）' % (
            name, seq, d['pts'] if d['pts'] is not None else 0,
            d['pos'] if d['pos'] is not None else '—', d['played'] if d['played'] else '—')

    return '**近期战绩：** %s；%s。' % (one('home', r['home']), one('away', r['away']))


def value_line(r):
    vh, va = r['value']['home'], r['value']['away']
    n = max(vh, va) / min(vh, va)
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
    bits = []
    if r.get('rule65'):
        bits.append('实力差距触发进球期望上修——%s' % r['rule65'])
    if r.get('rule63'):
        bits.append(r['rule63'])
    st = r.get('stadium') or {}
    if st.get('override_applied'):
        bits.append('场地状态影响主场加成：%s' % st.get('note', ''))
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
    top3 = r['top_scores'][:3]
    scen, used = [], 0
    for a, b, p in top3:
        d = 'home' if a > b else ('away' if a < b else 'draw')
        scen.append('%s → 候选 %d-%d（模型%.1f%%）' % (SCENE[d][used % 3], a, b, p * 100))
        used += 1
    style = '节奏%s' % ('偏快' if r['lambda_total'] > 3.2 else ('偏慢' if r['lambda_total'] < 2.4 else '中等'))
    ht = r['htft_top3']
    return ('> **比分推演（参考模型）：**\n'
            '> - 球队数据：%s 期望进球 %.2f；%s 期望进球 %.2f；双方合计%d人缺阵\n'
            '> - 比赛风格：%s主场体系 vs %s客场体系，%s，交锋节奏特征：%s，天气影响%s\n'
            '> - 比分推演：%s\n'
            '> - 局势解读：半场倾向%s → 全场%s（HAD首选），总进球指向%s，半全场指向%s') % (
        with_rank(r['home'], r['home_rank']), r['lambda_home'],
        with_rank(r['away'], r['away_rank']), r['lambda_away'],
        r['injury']['home_count'] + r['injury']['away_count'],
        r['home'], r['away'], style, r['h2h'].get('rhythm') or '无特殊', r['weather']['impact'],
        '；'.join(scen),
        '%d-%d' % (r['ht_scores'][0][0], r['ht_scores'][0][1]),
        HAD_CN[r['primary']], r['tier'], ht[0][0])


def conf_reason(r):
    parts = ['首选%s %.0f%%' % (HAD_CN[r['primary']], r['primary_prob'] * 100),
             '模型-市场分歧%.0fpp' % (r['diverge'] * 100)]
    if '空白' in r['h2h']['summary'] or '首次' in r['h2h']['summary']:
        parts.append('交锋信息稀薄已降级')
    if r['injury']['home_count'] + r['injury']['away_count'] >= 10:
        parts.append('双方伤停合计%d人' % (r['injury']['home_count'] + r['injury']['away_count']))
    if not r['k_consistent']:
        parts.append('净胜球分布与方向分歧')
    return '，'.join(parts)


def comment(r):
    if r['primary'] == 'draw':
        return '平局首选意味着双方实力更接近，建议以让球容错方向为主，不建议重仓。'
    if not r['k_consistent']:
        return '该场净胜球分布与推荐方向不一致，属于典型"方向对但比分难猜"型，适合做让球或总进球，不适合精猜比分。'
    if r['diverge'] > 0.15:
        return '基本面与市场方向相反，是本轮分歧最大的一类场次，只适合小注搏冷。'
    return '基本面、市场、净胜球分布三者一致，是本轮结构最干净的场次之一。'


def hafu_pool(matches):
    pool = []
    for r in matches:
        for p, v in r['htft_top3']:
            o = odd(r, 'hafu', key_hafu(p)) or 0
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
    pool = []
    for r in res:
        for p, v in r['htft_top3']:
            o = odd(r, 'hafu', key_hafu(p))
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
    c1 = sorted(r1['htft_top3'][:2], key=lambda x: -(odd(r1, 'hafu', key_hafu(x[0])) or 0))
    c2 = sorted(r2['htft_top3'][:2], key=lambda x: -(odd(r2, 'hafu', key_hafu(x[0])) or 0))
    for p1, _ in c1:
        for p2, _ in c2:
            if p1 != p2:
                return p1, p2
    return c1[0][0], c2[-1][0]


lines = []
P = lines.append

P('# 【分析】2026-10-28（周三）亚冠·日联杯·德国杯·意甲·英联杯·巴甲·美职 17场竞彩全分析 | 单关给到安菲尔德，红军蓝军都缺半条边')
P('')
P('> **报告说明：** 本文为赛前**分析报告**（标题标注【分析】），提供方向/比分/总进球等预测推荐。赛后将发布**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。历史报告可去主页查找。')
P('')
P('> **风险提示：** 本次采集的 17 场里同时有 6 项赛事、4 场英联杯与 5 场意甲，**轮换是本轮最大变量**——英联杯四场双方合计预计轮换 20 人以上；**单关只给了 015 利物浦vs切尔西一场**，该场平局已按单关信号上修。赔率采集时间 2026-10-28 13:33（北京时间，体彩官方）。**理性看待预测，切勿沉迷赌博。**')
P('')
P('> **⚠️ 免责声明：** 本文所有分析、预测、推荐仅供学习交流参考，不构成任何投注建议。足球比赛结果具有高度不确定性，任何预测均无法保证准确性。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
P('')
P('> **📊 近5日置信度命中率（滚动统计，数据源 memory/stats/confidence_stats.md）：** ★★★高 3/3=100.0% ｜ ★★中 41/51=80.4% ｜ ★低 20/31=64.5% ｜ ☆极低 本窗口无样本。**结论：** "中★★配次选容错"仍是唯一稳定的结构，低★场次只作参考。')
P('')
P('*每日更新，关注主页获取最新赛事分析*')
P('')
P('本轮是**典型的混合杯赛日**：亚冠2场、日联杯1场、德国杯1场、荷兰杯1场、英联杯4场、意甲5场、瑞超1场、巴甲1场、美职1场。结构上分三类——**①杯赛轮换盘**（英联杯4场、德国杯、日联杯、荷兰杯）：身价与伤停的参考价值被轮换大幅稀释，方向判断必须回到"谁更想赢"；**②意甲五连**：五场里有四场是"强队做客或强队主场让球"，模型与市场分歧集中在蒙扎vs那不勒斯与热那亚vs尤文这两场；**③跨洲尾场**：巴甲弗鲁米嫩塞与美职迈阿密都是主场强势方，但均缺2-3名锋线/后防主力。')
P('')
P('其中**015 利物浦vs切尔西是本轮唯一单关**，两队合计12人缺阵、且有大量轮换，平局概率按单关信号做了上修，是本轮结构最特殊的一场。')
P('')

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
    '、'.join('%s %d场%s' % (star, sum(1 for k in ORDER if R[k]['conf'] == star),
                            ('（%s）' % '/'.join(k for k in ORDER if R[k]['conf'] == star))
                            if any(R[k]['conf'] == star for k in ORDER) else '')
             for star in ('★★★', '★★', '★', '☆')),
    len([k for k in ORDER if R[k]['k_consistent']]),
    '/'.join(k for k in ORDER if R[k]['k_consistent'])))
P('')

for k in ORDER:
    r = R[k]
    P('## %s %s vs %s（%s）' % (k, r['home'], r['away'], r['league']))
    P('')
    P(tier_line(r))
    P('')
    P(venue_line(r))
    P('')
    base = '%s主场作战；%s。' % (
        with_rank(r['home'], r['home_rank']), with_rank(r['away'], r['away_rank']) + '做客')
    if r['h2h'].get('rhythm') and '无参照' not in r['h2h']['rhythm']:
        base += '交锋节奏特征为%s。' % r['h2h']['rhythm']
    base += '双方合计%d人缺阵。' % (r['injury']['home_count'] + r['injury']['away_count'])
    P(base)
    P('')
    P(value_line(r))
    P('')
    P(injury_line(r))
    P('')
    P(h2h_line(r))
    P('')
    P(form_line(r))
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
        r['hhad_line'], HC_CN.get(r['hc_first'], r['hc_first']), hc_pick(r, r['hc_first']) * 100,
        r['hhad_line'], HC_CN.get(r['hc_second'], r['hc_second']), hc_pick(r, r['hc_second']) * 100))
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
        r['hhad_line'], HC_CN.get(r['hc_first'], r['hc_first']), hc_pick(r, r['hc_first']) * 100,
        r['hhad_line'], HC_CN.get(r['hc_second'], r['hc_second']), hc_pick(r, r['hc_second']) * 100,
        r['ttg_top2'][0], tgv.get(r['ttg_top2'][0], 0) * 100,
        r['ttg_top2'][1], tgv.get(r['ttg_top2'][1], 0) * 100))
P('')

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
        P('- %s %s vs %s：%s支持率 %.0f%%，模型给 %.0f%%，追热性价比低，防平/防冷门。' % (
            k, r['home'], r['away'], HAD_CN[mdir[0]], mdir[1] * 100, r['fused'][mdir[0]] * 100))
        hot += 1
if hot == 0:
    P('- 本轮无单方向支持率>55%的场次。')
P('')
P('> 市场过热≠一定冷门，但赔率价值已被压缩，追热性价比低。')
P('')

# ---------------- 串关 ----------------
P('## 串关思路')
P('')
P('> 本轮17场（>8场），按数量规则以**三串一为主**，连续编号方案固定二串一。以下仅为方案参考，请根据自身判断与资金管理选择。')
P('')

P('### 方向串（胜平负）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
aligned = sorted([R[k] for k in ORDER
                  if HAD_CN[R[k]['primary']] == HAD_CN[max(R[k]['market'].items(), key=lambda x: x[1])[0]]],
                 key=lambda r: -r['primary_prob'])
a3 = aligned[:3]
o = [odd(r, 'had', r['primary']) for r in a3]
P('| 方向串A（稳健） | %s | %s | %s | 中 |' % (
    ' + '.join('%s%s' % (short(r['num']), HAD_CN[r['primary']]) for r in a3),
    odds_cell(o), total_cell(o)))
b2 = [r for r in aligned if r['primary_prob'] < 0.60][:3]
o = [odd(r, 'had', r['primary']) for r in b2]
P('| 方向串B（价值） | %s | %s | %s | 中高 |' % (
    ' + '.join('%s%s' % (short(r['num']), HAD_CN[r['primary']]) for r in b2),
    odds_cell(o), total_cell(o)))
P('')
P('> 方向串只取模型与市场**同向**的场次；方向对立的场次（%s）一律不进方向串，只作搏冷参考。' % (
    '、'.join('%s%s' % (short(R[k]['num']), HAD_CN[R[k]['primary']]) for k in ORDER
             if HAD_CN[R[k]['primary']] != HAD_CN[max(R[k]['market'].items(), key=lambda x: x[1])[0]])))
P('')

P('### 让球串（让球胜平负）')
P('')
P('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---|:---:|:---|')
safe = sorted([R[k] for k in ORDER if hc_pick(R[k], R[k]['hc_first']) >= 0.55],
              key=lambda r: -hc_pick(r, r['hc_first']))[:3]
o = [odd(r, 'hhad', r['hc_first']) for r in safe]
P('| 稳健让球串 | 容错优先 | %s | %s | %s | 中 |' % (
    ' + '.join('%s让(%s)%s' % (short(r['num']), r['hhad_line'], HC_CN.get(r['hc_first'], r['hc_first'])) for r in safe),
    odds_cell(o), total_cell(o)))
val = [r for r in R.values() if hc_pick(r, r['hc_second']) >= 0.18]
val = sorted(val, key=lambda r: -hc_pick(r, r['hc_second']))[:3]
o = [odd(r, 'hhad', r['hc_second']) for r in val]
P('| 价值让球串 | 高赔价值 | %s | %s | %s | 中高 |' % (
    ' + '.join('%s让(%s)%s' % (short(r['num']), r['hhad_line'], HC_CN.get(r['hc_second'], r['hc_second'])) for r in val),
    odds_cell(o), total_cell(o)))
P('')
P('> **稳健让球串**：取让球首选概率≥55%的场次（多为受让方"让胜=胜或平"或强队"让平"），容错性高。')
P('')
P('> **价值让球串**：取让球次选方向，赔率更高但需方向精准，适合小注。')
P('')

P('### 混合串（半全场+方向混合）')
P('')
P('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---|:---:|:---|')
ha = build_parade_prob(3)
o = [x[2] for x in ha]
P('| 半全场串A | 纯半全场 | %s | %s | %s | 高 |' % (
    ' + '.join('%s%s' % (short(x[0]['num']), x[1]) for x in ha), odds_cell(o), total_cell(o)))
hb = build_parade_prob(3, skip_m=[x[0]['num'] for x in ha])
o = [x[2] for x in hb]
P('| 半全场串B | 纯半全场 | %s | %s | %s | 高 |' % (
    ' + '.join('%s%s' % (short(x[0]['num']), x[1]) for x in hb), odds_cell(o), total_cell(o)))
mix1 = [R['006'], R['016']]
o = [odd(mix1[0], 'had', mix1[0]['primary']),
     odd(mix1[1], 'hafu', key_hafu(mix1[1]['htft_top3'][0][0]))]
P('| 方向+半全场A | 混合 | 006主胜 + 016%s | %s | %s | 中高 |' % (
    mix1[1]['htft_top3'][0][0], odds_cell(o), total_cell(o)))
mix2 = [R['014'], R['011']]
o = [odd(mix2[0], 'had', mix2[0]['primary']),
     odd(mix2[1], 'hafu', key_hafu(mix2[1]['htft_top3'][0][0]))]
P('| 方向+半全场B | 混合 | 014客胜 + 011%s | %s | %s | 中高 |' % (
    mix2[1]['htft_top3'][0][0], odds_cell(o), total_cell(o)))
for tag, pair in (('A', ('012', '013')), ('B', ('015', '016'))):
    r1, r2 = R[pair[0]], R[pair[1]]
    p1, _ = pick_pair_hafu(r1, r2)
    o = [odd(r1, 'hafu', key_hafu(p1)), odd(r2, 'ttg', str(r2['ttg_top2'][0]))]
    P('| 连续编号混合串%s | 混合 | %s %s + %s %s球 | %s | %s | 中高 |' % (
        tag, pair[0], p1, pair[1], r2['ttg_top2'][0], odds_cell(o), total_cell(o)))
P('')
P('> **半全场串A/B**：选半全场概率最高的场次，A、B 两串路径必须不同（A取胜胜、负负这类强路径，B取平开路径），避免同路径重复下注。')
P('')
P('> **方向+半全场A/B**：方向腿取结构干净的场次，半全场腿取与方向一致但路径更便宜的场次，两串选不同组合分散风险。')
P('')
P('> **连续编号混合串A/B**：选编号相邻场次（012+013、015+016），半全场+总进球混合搭配，档位与路径须差异化。')
P('')

P('### 娱乐串（高赔率组合）')
P('')
P('> **⚠️ 娱乐串风险提示：** 以下方案均为高赔率组合，单次命中概率极低（通常<5%），仅供娱乐参考，切勿重注。建议每注投入不超过总资金的1%-2%，量力而行。高赔率意味着高风险，未中奖为常态。')
P('')
P('> **📋 选场核心原则（关键发现1验证）：** 娱乐串选场以基本面分析（伤停/战意/状态/交锋/赛制）为主，模型概率仅作辅助参考。8月11日回测验证：高赔半全场串132倍命中，三场全部基于基本面逻辑选场（伤停僵局→平平、主场苟分→平平、客场死守→负负），而非模型概率排序。基本面分析在高赔串关中的价值远超纯模型概率。本轮核心抓手：**英联杯四场的大轮换**（谁上主力谁吃亏）与**意甲三支残阵**（尤文8人、米兰8人、博洛尼亚锋线掏空）。')
P('')
P('> **🔢 串关数量规则：** 本轮17场（>8场），**以三串一为主**；连续编号方案固定为二串一。')
P('')
P('> **🏗️ 娱乐串结构：** 四个子分类全部保留（高赔总进球串／高赔半全场串／半全场混合总进球串／比分串），每类＝2个原方案＋2个连续编号方案，比分串另含单挑比分①②，合计18个方案。')
P('')
P('> **🚫 已按规则71排除法甲：当天非PSG法甲0场 → 纳入0场。**')
P('')

P('#### 高赔总进球串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
ttg_set = [('001', 2), ('008', 4), ('017', 3)]
o = [odd(R[k], 'ttg', str(n)) for k, n in ttg_set]
P('| 总进球串A | %s | %s | %s | 高 |' % (
    ' + '.join('%s %s球' % (k, n) for k, n in ttg_set), odds_cell(o), total_cell(o)))
ttg_set2 = [('005', 3), ('010', 2), ('016', 2)]
o = [odd(R[k], 'ttg', str(n)) for k, n in ttg_set2]
P('| 总进球串B | %s | %s | %s | 高 |' % (
    ' + '.join('%s %s球' % (k, n) for k, n in ttg_set2), odds_cell(o), total_cell(o)))
for tag, pair, picks in (('①', ('006', '007'), (2, 2)), ('②', ('013', '014'), (3, 2))):
    r1, r2 = R[pair[0]], R[pair[1]]
    o = [odd(r1, 'ttg', str(picks[0])), odd(r2, 'ttg', str(picks[1]))]
    P('| 连续编号总进球串%s | %s %s球 + %s %s球 | %s | %s | 高 |' % (
        tag, pair[0], picks[0], pair[1], picks[1], odds_cell(o), total_cell(o)))
P('')
P('> **总进球串A/B**：每场档位独立由基本面决定——001亚冠跨联赛对撞、双方身价接近但后防均有缺口→2球；008荷甲内战、双方都不是防守型球队→4球；017迈阿密主场火力足但辛辛那提三中卫缺阵→3球；005国米缺劳塔罗、威尼斯缺主力中卫+中场核心→3球；010桑德兰下半场看台、双方轮换→2球；016弗鲁米嫩塞主场强势但锋线两人报销→2球。**同一串内档位为2/4/3，无机械复用。**')
P('')
P('> **连续编号总进球串①②**：006+007、013+014 均为编号相邻段，每场档位独立判断，允许不同档。')
P('')

P('#### 高赔半全场串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
hf1 = build_parade(3)
o = [x[2] for x in hf1]
P('| 高赔半全场串A | %s | %s | %s | 极高 |' % (
    ' + '.join('%s %s' % (short(x[0]['num']), x[1]) for x in hf1), odds_cell(o), total_cell(o)))
hf2 = build_parade(3, skip_m=[x[0]['num'] for x in hf1])
o = [x[2] for x in hf2]
P('| 高赔半全场串B | %s | %s | %s | 极高 |' % (
    ' + '.join('%s %s' % (short(x[0]['num']), x[1]) for x in hf2), odds_cell(o), total_cell(o)))
for tag, pair in (('①', ('001', '002')), ('②', ('014', '015'))):
    r1, r2 = R[pair[0]], R[pair[1]]
    p1, p2 = pick_pair_hafu(r1, r2)
    o = [odd(r1, 'hafu', key_hafu(p1)), odd(r2, 'hafu', key_hafu(p2))]
    P('| 连续编号高赔半全场串%s | %s %s + %s %s | %s | %s | 极高 |' % (
        tag, pair[0], p1, pair[1], p2, odds_cell(o), total_cell(o)))
P('')
P('> **高赔半全场串A/B**：从各场半全场TOP3中挑赔率最高且路径互不重复的组合——A取%s；B取%s。**同一串内路径无重复，也无"全胜胜/全负负"的机械拼盘。**' % (
    '、'.join('%s%s' % (short(x[0]['num']), x[1]) for x in hf1),
    '、'.join('%s%s' % (short(x[0]['num']), x[1]) for x in hf2)))
P('')
P('> **连续编号高赔半全场串①②**：001+002、014+015，相邻段内路径强制不同。')
P('')

P('#### 半全场混合总进球串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
o = [odd(R['006'], 'hafu', key_hafu(R['006']['htft_top3'][0][0])), odd(R['005'], 'ttg', '3')]
P('| 混合串A | 006%s + 005 3球 | %s | %s | 极高 |' % (
    R['006']['htft_top3'][0][0], odds_cell(o), total_cell(o)))
o = [odd(R['016'], 'hafu', key_hafu(R['016']['htft_top3'][0][0])), odd(R['008'], 'ttg', '4')]
P('| 混合串B | 016%s + 008 4球 | %s | %s | 极高 |' % (
    R['016']['htft_top3'][0][0], odds_cell(o), total_cell(o)))
for tag, pair in (('①', ('011', '012')), ('②', ('016', '017'))):
    r1, r2 = R[pair[0]], R[pair[1]]
    p1, _ = pick_pair_hafu(r1, r2)
    o = [odd(r1, 'hafu', key_hafu(p1)), odd(r2, 'ttg', str(r2['ttg_top2'][0]))]
    P('| 连续编号混合总进球串%s | %s %s + %s %s球 | %s | %s | 极高 |' % (
        tag, pair[0], p1, pair[1], r2['ttg_top2'][0], odds_cell(o), total_cell(o)))
P('')
P('> **混合串A/B**：半全场腿取方向明确场次（米兰主场胜胜、弗鲁米嫩塞主场胜胜），总进球腿取档位不同的场次（005取3球、008取4球），两串场次与档位均不重复。')
P('')
P('> **连续编号混合总进球串①②**：011+012、016+017 相邻段，半全场+总进球混合，路径与档位差异化。')
P('')

P('#### 比分串（6个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
cons = [R[k] for k in ORDER if R[k]['k_consistent']]
ranked = sorted(cons, key=lambda r: -r['band'][0][2])
s1, s2 = ranked[0], ranked[1]
b1 = s1['band'][0]
b2 = s2['band'][0]
o = [odd(s1, 'crs', '%d:%d' % (b1[0], b1[1])), odd(s2, 'crs', '%d:%d' % (b2[0], b2[1]))]
P('| 稳健比分串 | %s %d-%d + %s %d-%d | %s | %s | 高 |' % (
    short(s1['num']), b1[0], b1[1], short(s2['num']), b2[0], b2[1],
    odds_cell(o), total_cell(o)))
cold_o1 = odd(R['004'], 'crs', '1:1')
cold_o2 = odd(R['014'], 'crs', '1:1')
P('| 搏冷比分串（反向推理） | 004 1-1 + 014 1-1 | %s | %s | 极高 |' % (
    odds_cell([cold_o1, cold_o2]), total_cell([cold_o1, cold_o2])))


def pick_band(r, idx=0):
    """带内按概率排序取第 idx 档（idx 超界时取末档）"""
    bd = r['band']
    return bd[min(idx, len(bd) - 1)]


for tag, pair, i1, i2 in (('①', ('005', '006'), 0, 1),):
    r1, r2 = R[pair[0]], R[pair[1]]
    c1 = pick_band(r1, i1)
    c2 = pick_band(r2, i2)
    o = [odd(r1, 'crs', '%d:%d' % (c1[0], c1[1])), odd(r2, 'crs', '%d:%d' % (c2[0], c2[1]))]
    P('| 连续编号比分串%s | %s %d-%d + %s %d-%d | %s | %s | 高 |' % (
        tag, pair[0], c1[0], c1[1], pair[1], c2[0], c2[1], odds_cell(o), total_cell(o)))
P('| 连续编号比分串② | 本轮无合规候选（唯一相邻一致段005+006带内≥8%组合已被稳健串与①用尽，按胜率优先不出） | — | — | — |')
cands = []
for r in cons:
    for a, b, p in r['band']:
        o1 = odd(r, 'crs', '%d:%d' % (a, b))
        if p >= 0.06 and o1 and o1 >= 8.0:
            cands.append((r, a, b, p, o1))
cands.sort(key=lambda x: -x[3])
for i in (0, 1):
    if i < len(cands):
        r, a, b, p, o1 = cands[i]
        P('| 单挑比分%s | %s %d-%d | — | %.2f | 中 |' % ('①' if i == 0 else '②', short(r['num']), a, b, o1))
    else:
        P('| 单挑比分%s | 本轮无合规候选（众数一致＋概率门槛＋赔率≥8.00） | — | — | — |' % ('①' if i == 0 else '②'))
P('')
P('> **稳健比分串**（试用期流程（规则67-双轨制））：%s 分布众数%+d（%.1f%%）／推荐众数%+d（%.1f%%）／带内候选TOP3 %s／首推总进球 %s／众数一致；%s 分布众数%+d（%.1f%%）／推荐众数%+d（%.1f%%）／带内候选TOP3 %s／首推总进球 %s／众数一致。两场均落在推荐众数带内，未取全局最高比分。' % (
    short(s1['num']), s1['k_dist'], s1['k_dist_prob'] * 100, s1['k_rec'], s1['k_rec_prob'] * 100,
    ' > '.join('%d-%d(%.1f%%)' % (a, b, p * 100) for a, b, p in s1['band']),
    '/'.join(str(x) for x in s1['ttg_top2']),
    short(s2['num']), s2['k_dist'], s2['k_dist_prob'] * 100, s2['k_rec'], s2['k_rec_prob'] * 100,
    ' > '.join('%d-%d(%.1f%%)' % (a, b, p * 100) for a, b, p in s2['band']),
    '/'.join(str(x) for x in s2['ttg_top2'])))
P('')
P('> **搏冷比分串（反向推理）：** 冷门剧本=「强队被低等级/残阵拖平」——004帕德博恩三名中卫同时缺阵、斯图加特本身4人成疑，主场死守取1-1；014热那亚主场低落但尤文8人缺阵（伊尔迪兹/孔塞桑/洛卡特利/图拉姆全缺），尤文客场本季多为1球小胜，剧本内取1-1。两者均不在模型TOP5内，属赔率择优。')
P('')
P('> **连续编号比分串**：本轮"众数一致"场次只有005与006两场且恰好相邻，段内满足"带内＋概率≥8%"的组合仅 (005 1-2 + 006 2-1) 与 (005 1-2 + 006 1-0) 两组，已分别用于稳健串与①；②若再取带内次档（005 2-3，5.0%）即变成"为高赔放弃更高概率"，与胜率优先口径冲突，故**按规则留空**，不为凑方案数降格。')
P('')
P('> **单挑比分①/②**：从"众数一致"场次中取带内概率最高且赔率≥8.00 的比分，独立单注不串关。本轮两场（005/006）带内最高概率比分分别为 005 1-2（8.8%，赔率7.00）与 006 2-1（9.8%，赔率7.00），赔率均被压到8以下，**不满足性价比门槛，故本轮不出单挑比分**——硬凑只会用低概率比分换高赔，与胜率优先口径冲突。')
P('')

P('## 本轮规律')
P('')
P('**1. 杯赛轮换是最大的不确定性来源。** 英联杯四场（010-012、015）双方合计预计轮换 20 人以上，桑德兰只开下层看台、伯恩茅斯球场还在施工，主场优势被进一步削弱；德国杯帕德博恩三名中卫同时缺阵，防线几乎是拼凑的。这类场次模型只能给出方向倾向，**真正的信息在开赛前一小时的首发名单**。')
P('')
P('**2. 意甲五场的内部分层很清楚。** 005威尼斯vs国米（身价6.1倍）、014热那亚vs尤文（3.7倍）是"强队做客"，006米兰vs博洛尼亚（2.2倍）是"强队主场"，这三场模型方向与市场一致，可以拿来做方向串；013蒙扎vs那不勒斯（3.8倍）与007帕尔马vs乌迪内斯（1.04倍）则是分歧场，前者模型几乎五五开、市场看那不勒斯，后者两队身价持平。')
P('')
P('**3. 强队残阵是最大的爆冷入口。** 尤文8人缺阵（含伊尔迪兹、孔塞桑、洛卡特利、图拉姆四名主力级）、米兰8人（4确定+4成疑）、博洛尼亚锋线四人几乎全缺、国米劳塔罗+帕瓦尔双缺。这些缺口已经在λ里体现，但**临场名单公布后仍需复核**。')
P('')
P('**4. 净胜球分布与方向大面积分歧。** 17场里只有%s两场「众数一致」，其余15场都是分布-方向分歧（最常见形态是分布在0球、方向在主胜）。这意味着本轮**适合做方向与总进球，不适合重仓精猜比分**，正向比分串可选场次只有2场。' % '/'.join(k for k in ORDER if R[k]['k_consistent']))
P('')
P('**5. 单关给了015，但这场最不该重注。** 利物浦与切尔西合计12人缺阵、双方主帅都明确要轮换，模型给主胜43.5%、平局经单关上修后25.1%，任何一边都没有优势。单关的价值在于"可以只买单场"，不在于"这场更好猜"。')
P('')

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
io.open('reports/analysis/20261028_wednesday_analysis_zhihu.md', 'w', encoding='utf-8').write(out)
print('saved, chars:', len(out))
