# -*- coding: utf-8 -*-
"""2026-11-01（周日）25场知乎分析报告生成 → reports/analysis/20261101_sunday_analysis_zhihu.md"""
import json, io

SRC = 'reports/data/20261101_model_output.json'
OUT = 'reports/analysis/20261101_sunday_analysis_zhihu.md'

ms = json.load(io.open(SRC, encoding='utf-8'))
BY = {r['num']: r for r in ms}
CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
LEVEL = {
    '英超': 'L1', '西甲': 'L1', '意甲': 'L1', '德甲': 'L1', '法甲': 'L1',
    '荷甲': 'L2', '葡超': 'L2', '日职': 'L2', '韩职': 'L2', '巴西杯': 'L2', '美职': 'L2',
    '瑞超': 'L3', '挪超': 'L3', '澳超': 'L3',
}
HAFU_CODE = {'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD',
             '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA'}


def pct(x, nd=1):
    return ('%.' + str(nd) + 'f%%') % (x * 100)


def money(x):
    return '%.0f万欧' % (x / 1e4)


def odds_of(r, pool, key):
    src = {'had': r.get('odds_had'), 'hhad': r.get('odds_hhad'),
           'ttg': r.get('odds_ttg'), 'hafu': r.get('odds_hafu'),
           'crs': r.get('odds_crs')}.get(pool) or {}
    return src.get(str(key))


def grade_text(r):
    lv = LEVEL.get(r['league'], 'L2')
    if r['league'] == '巴西杯':
        return '巴西杯（淘汰赛·跨赛事性质）｜两队均来自巴甲（L2 vs L2），按同联赛基准处理，但杯赛淘汰赛谨慎度更高'
    return '%s（国内联赛·%s）｜同联赛内战，不触发跨联赛等级差先验（主队%s %s vs 客队%s %s）' % (
        r['league'], {'L1': '顶级', 'L2': '次顶级', 'L3': '三级', 'L4': '四级'}.get(lv, '次级'),
        r['league'], lv, r['league'], lv)


def path_text(direction):
    return {'home': '主队控球压制、边路冲击建立优势并守住',
            'draw': '双方中场互相抵消、节奏偏慢、互交白卷',
            'away': '客队反击效率更高或主队后防露空被打穿'}[direction]


def ht_lead(r):
    a, b, _ = r['ht_scores'][0]
    if a > b:
        return '主队%s领先' % ('%d-%d' % (a, b))
    if a < b:
        return '客队%s领先' % ('%d-%d' % (b, a))
    return '%d-%d' % (a, b)


def score_story(score, direction):
    a, b = [int(x) for x in score.split('-')]
    d = 'home' if a > b else ('away' if a < b else 'draw')
    if d == 'draw':
        return '双方谨慎试探、互交白卷式僵持 → 候选 %s' % score
    if d == 'home':
        return '主队控球压制，客队低位收缩，主队靠定位球或二次进攻破僵 → 候选 %s' % score
    return '客队中场压制切断主队出球，靠快反或定位球偷袭得手 → 候选 %s' % score


def hc_cn(k):
    return {'home': '让胜', 'draw': '让平', 'away': '让负'}[k]


def market_top(r):
    k = max(r['market'].items(), key=lambda x: x[1])
    return k[0], k[1]


def rank_txt(r, side):
    rk = (r.get('home_rank') if side == 'home' else r.get('away_rank')) or ''
    return ('（%s）' % rk) if rk else ''


def clean(s):
    return (s or '').strip().rstrip('。；，')


def lam_word(t):
    return '偏低' if t < 2.3 else ('正常' if t <= 3.3 else '偏高')


# 阵型 → 风格解读（用户要求：介绍阵容时顺带说明这套阵型代表什么打法）
STYLE = {
    '4-2-3-1': '双后腰托底+三前腰游弋，攻守均衡的现代主流阵，丢球后回防层次清楚',
    '4-3-3': '边锋拉开宽度的高位压迫，进攻火力足，但两个边后卫身后容易被打身后',
    '4-4-2': '两条平行四人的传统英式阵，中场线平、出球直接，靠边路传中与二点球',
    '4-4-1-1': '4-4-2的回收版，一人回撤做前腰，守强于攻，适合客场求稳',
    '4-1-4-1': '单后腰+四中场，防守时退成4-5-1，典型稳守反击结构',
    '4-5-1': '五中场单前锋，摆守势、等反击，进攻端只能靠单点',
    '5-3-2': '五后卫+三中场，低位防守反击，接近摆大巴，赢球靠效率和定位球',
    '5-4-1': '五后卫+四中场单前锋，极致摆大巴、禁区前沿堆人，目标就是0-0或偷一球',
    '5-4-1-0': '五后卫+四中场，几乎放弃进攻的纯防守阵',
    '3-4-2-1': '三中卫+双前腰的控球压迫，中路堆人、翼卫提供宽度，丢球就地反抢',
    '3-4-3': '三中卫配三前锋的对攻阵，攻击性强，但后场空间大、怕快反',
    '3-5-2': '三中卫+翼卫上下往返，中场人多的控球阵，边路攻防全靠翼卫',
    '3-5-1-1': '三中卫五中场单前锋，低位防反，先立于不败',
    '3-4-1-2': '三中卫+单前腰双前锋，偏保守的意式结构，中路密度高',
    '4-3-1-2': '菱形中场，前腰串联双前锋，中路渗透为主、边路靠边卫补',
    '4-2-2-2': '双后腰+双前腰+双前锋的巴西式阵，中路密集、边路交给边卫',
    '3-1-4-2': '三中卫+单后腰+四中场的J联赛常见控球阵，重中场人数',
    '4-2-4': '四前锋式搏命阵，只在落后时使用，攻守极度失衡',
}


def form_of(lineup):
    return (lineup or '').replace('（非官方）', '').replace('（媒体预测）', '').strip()


def style_of(lineup):
    s = form_of(lineup)
    key = s.split('（')[0].strip()
    if key in STYLE:
        return STYLE[key]
    parts = key.split('-')
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        d, m, f = [int(x) for x in parts]
        if d >= 5:
            return '五后卫体系，防守优先，靠反击与定位球找机会'
        if d == 3:
            return '三中卫体系，翼卫前压、进攻投入偏大'
        if d == 4:
            return '常规四后卫体系，攻守相对均衡'
    return '阵型信息不完整，按常规四后卫体系处理'


def section(r):
    L = []
    num = r['num'][-3:]
    L.append('## %s %s vs %s（%s）' % (num, r['home'], r['away'], r['league']))
    L.append('')
    L.append('**联赛等级：** %s' % grade_text(r))
    L.append('')
    tag = ' 【单关】' if r['is_single'] else ''
    L.append('⏰ %s ｜ 🏟 %s，%s，%s，容量%s ｜场地状态：%s（%s） ｜ 🌤 %s，%s，%s，影响%s%s' % (
        r['time'], r['venue']['name'], r['venue'].get('city', ''), r['venue'].get('pitch', '天然草'),
        '{:,}'.format(r['venue'].get('capacity', 0)), r['venue'].get('status', '正常'),
        r['venue'].get('status_note', ''), r['weather'].get('temp', ''), r['weather'].get('desc', ''),
        r['weather'].get('wind', ''), r['weather'].get('impact', ''), tag))
    L.append('')
    inj_h, inj_a = r['injury']['home_count'], r['injury']['away_count']
    L.append('%s%s主场作战；%s%s做客。双方合计%d人缺阵（含停赛与成疑）。' % (
        r['home'], rank_txt(r, 'home'), r['away'], rank_txt(r, 'away'), inj_h + inj_a))
    L.append('')
    ctx = r['context']
    L.append('**球队动态：** %s；%s；%s。%s' % (
        clean(ctx.get('stake')), clean(ctx.get('fitness')), clean(ctx.get('psych')),
        clean(r['injury'].get('note'))))
    L.append('')
    vh, va = r['value']['home'], r['value']['away']
    ratio = max(vh, va) / min(vh, va)
    hi = '主队' if vh > va else '客队'
    if ratio >= 2.0:
        cmp_txt = '身价差距明显（%.2f倍），%s硬实力占优，但赔率端是否已充分定价需要对照。' % (ratio, hi)
    elif ratio >= 1.4:
        cmp_txt = '身价有差距（%.2f倍），%s略占上风，仍需结合伤停与主客场因素。' % (ratio, hi)
    else:
        cmp_txt = '身价接近（%.2f倍），硬实力相当，胜负更适合由临场状态、伤停与主场因素决定。' % ratio
    L.append('**身价对比：** 主队%s总身价约%s vs 客队%s总身价约%s，%s%s' % (
        r['home'], money(vh), r['away'], money(va), ('客队是主队的%.2f倍，' % (va / vh) if va > vh
                                                     else '主队是客队的%.2f倍，' % (vh / va)), cmp_txt))
    L.append('')
    L.append('**伤停：** 主队%d人（%s）；客队%d人（%s）。%s' % (
        inj_h, '；'.join(r['injury']['home']) or '无确认缺阵',
        inj_a, '；'.join(r['injury']['away']) or '无确认缺阵', r['injury'].get('note', '')))
    L.append('')
    L.append('**交锋：** %s' % r['h2h'].get('summary', ''))
    L.append('')
    if r['rule65']:
        L.append('> 实力差距触发大球上修——%s；同主客交锋史修正：主队λ%+0.2f / 客队λ%+0.2f。' % (
            r['rule65'], r['h2h_shift'][0], r['h2h_shift'][1]))
        L.append('')
    L.append('> **战意心理与体能分析：**')
    L.append('> - 战意：%s' % ctx.get('stake', ''))
    L.append('> - 体能与休息：%s' % ctx.get('fitness', ''))
    L.append('> - 心理因素：%s' % ctx.get('psych', ''))
    L.append('> - 赛程牵制：%s' % ctx.get('schedule', ''))
    L.append('> - 预计首发：主队 %s —— %s；客队 %s —— %s' % (
        r['lineup'].get('home', ''), style_of(r['lineup'].get('home')),
        r['lineup'].get('away', ''), style_of(r['lineup'].get('away'))))
    L.append('')
    mk = r['market']
    mt, mp = market_top(r)
    same = (mt == r['primary'])
    div = r['diverge']
    rel = '基本对齐' if div <= 0.08 else ('存在分歧' if div <= 0.15 else '分歧较大')
    align = '与市场%s同向' % CN[mt] if same else '与市场%s方向相反' % CN[mt]
    extra = ''
    if r.get('rule_shift'):
        extra += '；联赛修正：%s' % r['rule_shift']
    if r.get('rule63'):
        extra += '；%s' % r['rule63']
    L.append('**模型 vs 市场：** 融合概率 主%s / 平%s / 客%s。市场 主%s / 平%s / 客%s（%s，%s，%s）。λ：主%.2f / 客%.2f（总%.2f，%s）%s' % (
        pct(r['fused']['home']), pct(r['fused']['draw']), pct(r['fused']['away']),
        pct(mk['home']), pct(mk['draw']), pct(mk['away']), align, rel, '分歧%.0fpp' % (div * 100),
        r['lambda_home'], r['lambda_away'], r['lambda_total'],
        lam_word(r['lambda_total']), extra))
    L.append('')
    L.append('> **比分推演（参考模型）：**')
    L.append('> - 球队数据：%s%s 期望进球 %.2f；%s%s 期望进球 %.2f；双方合计%d人缺阵' % (
        r['home'], rank_txt(r, 'home'), r['lambda_home'],
        r['away'], rank_txt(r, 'away'), r['lambda_away'], inj_h + inj_a))
    L.append('> - 比赛风格：主队%s（%s）、客队%s（%s）；节奏%s，交锋节奏特征：%s，天气影响%s' % (
        form_of(r['lineup'].get('home')), style_of(r['lineup'].get('home')),
        form_of(r['lineup'].get('away')), style_of(r['lineup'].get('away')),
        '中等' if r['lambda_total'] < 3.2 else '偏快', clean(r['h2h'].get('rhythm')), clean(r['weather'].get('impact'))))
    ts = r['top_scores']
    s1 = '%d-%d' % (ts[0][0], ts[0][1])
    s2 = '%d-%d' % (ts[1][0], ts[1][1])
    s3 = '%d-%d' % (ts[2][0], ts[2][1])
    L.append('> - 比分推演：%s（模型%s）；%s（模型%s）；%s（模型%s）' % (
        score_story(s1, r['primary']), pct(ts[0][2]), score_story(s2, r['primary']), pct(ts[1][2]),
        score_story(s3, r['secondary']), pct(ts[2][2])))
    L.append('> - 局势解读：半场倾向%s → 全场%s（HAD首选），总进球指向%s，半全场指向%s' % (
        ht_lead(r), CN[r['primary']], r['tier'], r['htft_top3'][0][0]))
    L.append('')
    L.append('**推荐：**')
    L.append('')
    L.append('| 玩法 | 推荐 |')
    L.append('|:---|:---|')
    L.append('| **比分TOP5** | %s |' % ' > '.join('**%d-%d**（%s）' % (a, b, pct(p)) for a, b, p in ts))
    L.append('| **半全场TOP3** | %s |' % ' > '.join('**%s**（%s）' % (k, pct(v)) for k, v in r['htft_top3']))
    L.append('| **HAD** | 首选 %s(%s) / 次选 %s(%s) |' % (
        CN[r['primary']], pct(r['primary_prob'], 0), CN[r['secondary']], pct(r['secondary_prob'], 0)))
    hcm = r.get('hhad_model') or {}
    L.append('| **HAFU** | 首选 **让(%s)%s**(%s) / 次选 **让(%s)%s**(%s) |' % (
        r['hhad_line'], hc_cn(r['hc_first']), pct(hcm.get(r['hc_first'], 0), 0),
        r['hhad_line'], hc_cn(r['hc_second']), pct(hcm.get(r['hc_second'], 0), 0)))
    t1, t2 = r['ttg_top2']
    L.append('| **大小球·总进球** | **%s**（%s）：**%d球**(%s) / **%d球**(%s) |' % (
        r['tier'], r['over_under'], t1, pct(r['tg'].get(str(t1), 0), 0),
        t2, pct(r['tg'].get(str(t2), 0), 0)))
    L.append('| **半场比分** | %s |' % ' > '.join(
        '%d-%d（%s）' % (a, b, pct(p)) for a, b, p in r['ht_scores']))
    L.append('')
    L.append('**置信度：** %s — 首选%s %s，模型-市场分歧%.0fpp，净胜球%s。' % (
        r['conf'], CN[r['primary']], pct(r['primary_prob'], 0), div * 100,
        '分布与方向一致' if r['k_consistent'] else '分布与方向分歧'))
    L.append('')
    if div > 0.20:
        L.append('> 分歧超过20pp，模型与市场对这场球的定价完全不同，方向上不宜重注，最多小注跟模型、或直接放弃。')
    elif div >= 0.11:
        L.append('> 分歧偏大（%.0fpp），模型与市场各有理由，建议方向+次选容错，或改用让球/总进球降低方向风险。' % (div * 100))
    elif not r['k_consistent']:
        L.append('> 模型与市场基本对齐，但净胜球分布众数落在%+d、与首选方向不一致——典型"方向可判、比分难猜"，更适合让球与总进球，不适合精猜比分。' % r['k_dist'])
    else:
        L.append('> 方向、净胜球分布与市场三者同向，是本轮结构较完整的一场。')
    L.append('')
    L.append('> **净胜球众数：** 分布众数 **%+d**（%s）｜推荐众数 **%+d**（%s）｜**%s**' % (
        r['k_dist'], pct(r['k_dist_prob']), r['k_rec'], pct(r['k_rec_prob']),
        '分布-方向一致' if r['k_consistent'] else '分布-方向分歧'))
    L.append('')
    return L


def build():
    L = []
    single_nums = [r['num'][-3:] for r in ms if r['is_single']]
    div10 = [r['num'][-3:] for r in ms if r['diverge'] >= 0.10]
    opposite = [r['num'][-3:] for r in ms if max(r['market'].items(), key=lambda x: x[1])[0] != r['primary']]
    three = [r['num'][-3:] for r in ms if r['conf'] == '★★★']
    two = [r['num'][-3:] for r in ms if r['conf'] == '★★']
    one = [r['num'][-3:] for r in ms if r['conf'] == '★']
    zero = [r['num'][-3:] for r in ms if r['conf'] == '☆']
    consistent = [r['num'][-3:] for r in ms if r['k_consistent']]

    L.append('# 【分析】2026-11-01（周日）25场竞彩全分析 | 九场单关008-016；利物浦vs阿森纳、町田争冠、拉齐奥领头羊')
    L.append('')
    L.append('> **报告说明：** 本文为赛前**分析报告**（标题标注【分析】），提供方向/比分/总进球等预测推荐。赛后将发布**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。历史报告可去主页查找。')
    L.append('')
    L.append('> **风险提示：** 今天共 **25 场**，结构上最突出的特征是**九场单关连开**（008-016，从西甲赫塔费vs塞维利亚到英超利物浦vs阿森纳），主任一次性把悬念场集中放出，说明这九场的方向都不牢靠。其余看点：**016 利物浦vs阿森纳**英超争冠卡位战、**003 町田泽维亚**榜首主场对保级区钢巴、**013 拉齐奥**意甲领头羊主场、**023 巴斯克德比**、**007 科莫**对垫底威尼斯。模型与市场分歧≥10pp共 %d 场（%s），方向相反 %d 场（%s）。赔率采集时间 2026-11-01 上午 11:22（北京时间，体彩官方）。**理性看待预测，切勿沉迷赌博。**' % (
        len(div10), '/'.join(div10), len(opposite), '/'.join(opposite)))
    L.append('')
    L.append('> **⚠️ 免责声明：** 本文所有分析、预测、推荐仅供学习交流参考，不构成任何投注建议。足球比赛结果具有高度不确定性，任何预测均无法保证准确性。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
    L.append('')
    L.append('> **📊 近5日置信度命中率（滚动统计，数据源 memory/stats/confidence_stats.md）：** ★★★高 3/3=100.0% ｜ ★★中 28/37=75.7% ｜ ★低 17/24=70.8% ｜ ☆极低 1/1=100.0%。**结论：** "中★★配次选容错"仍是最稳结构，低★配次选同样能到70%。')
    L.append('')
    L.append('*每日更新，关注主页获取最新赛事分析*')
    L.append('')
    L.append('今天 25 场的结构分五类——**①九场单关**（008-016）：主任把平局风险最高的一批场次集中放出，模型平局概率经单关信号上修后，008、014、016 三场平局直接成为首选；**②强弱分明**（003、007、013、020、017）：模型一方胜率 ≥58%，但市场已把赔率压低，价值在让球与总进球；**③争冠/卡位战**（016 利物浦vs阿森纳、013 拉齐奥、004 首尔、002 蔚山）；**④残阵对撞**（014 柏林联合、012 都灵、018 莱切、019 巴伦西亚）：缺口集中在后防与锋线；**⑤五五开混战**（005、011、021、024、025）：首选概率 ≤44%，方向本身不可重注。')
    L.append('')
    L.append('九场单关里，**016 利物浦vs阿森纳**是本轮最大焦点：模型 λ 1.15/1.11（总2.26），平局基准就有34.8%，单关上修+13pp后到47.8%，是"低进球+势均力敌+单关信号"三重叠加的结果；**008 赫塔费vs塞维利亚**平局45.3%（赫塔费主场场均只进0.5球、塞维利亚客场1.6球），属于典型的闷战结构；**010 SBV精英vs特温特**与**009 马尔默vs哈马比**则是客队明显占优、但单关信号把平局抬到30%以上的类型。**单关的价值在于"可以只买一场"，不在于这场更好猜。**')
    L.append('')
    L.append('## 总览')
    L.append('')
    L.append('| 编号 | 对阵 | 首选 | 次选 | 置信度 |')
    L.append('|:---:|:---|:---:|:---:|:---:|')
    for r in ms:
        L.append('| %s | %s vs %s | %s(%s) | %s(%s) | %s |' % (
            r['num'][-3:], r['home'], r['away'], CN[r['primary']], pct(r['primary_prob'], 0),
            CN[r['secondary']], pct(r['secondary_prob'], 0), r['conf']))
    L.append('')
    L.append('> 本轮置信度分布：★★★ %d场（%s）、★★ %d场（%s）、★ %d场（%s）、☆ %d场（%s）。**净胜球分布与方向一致的 %d 场**（%s），比上一轮多，正向比分串可选面仍然集中在强队主场。' % (
        len(three), '/'.join(three), len(two), '/'.join(two), len(one), '/'.join(one),
        len(zero), '/'.join(zero), len(consistent), '/'.join(consistent)))
    L.append('')
    for r in ms:
        L.extend(section(r))

    # 综合推荐汇总
    L.append('## 综合推荐汇总')
    L.append('')
    L.append('| 编号 | 对阵 | 胜平负首选 | 胜平负次选 | 让球首选 | 让球次选 | 总进球 |')
    L.append('|:---:|:---|:---:|:---:|:---:|:---:|:---:|')
    for r in ms:
        hcm = r.get('hhad_model') or {}
        t1, t2 = r['ttg_top2']
        L.append('| %s | %s vs %s | %s(%s) | %s(%s) | **让(%s)%s**(%s) | **让(%s)%s**(%s) | **%d球**(%s) / **%d球**(%s) |' % (
            r['num'][-3:], r['home'], r['away'],
            CN[r['primary']], pct(r['primary_prob'], 0), CN[r['secondary']], pct(r['secondary_prob'], 0),
            r['hhad_line'], hc_cn(r['hc_first']), pct(hcm.get(r['hc_first'], 0), 0),
            r['hhad_line'], hc_cn(r['hc_second']), pct(hcm.get(r['hc_second'], 0), 0),
            t1, pct(r['tg'].get(str(t1), 0), 0), t2, pct(r['tg'].get(str(t2), 0), 0)))
    L.append('')
    L.append('> **让球口径说明：** 让球首选采用**无条件净胜球众数**，与HAD首推方向**口径独立**——本轮多数场次分布众数落在0球，因此让(-1)的场次首选普遍是"让负/让平"，让(+1)的场次首选是"让胜"。这不是方向矛盾，而是让球盘本身在覆盖"方向出错"的可能。')
    L.append('')

    # 单关专项
    L.append('## 单关专项（008 / 009 / 010 / 011 / 012 / 013 / 014 / 015 / 016）')
    L.append('')
    L.append('| 编号 | 对阵 | 模型首选 | 平局(上修后) | 市场 | 建议 |')
    L.append('|:---:|:---|:---:|:---:|:---:|:---|')
    advice = {
        '008': '平局首选且市场给客胜，闷战结构，单买平或平+客双选',
        '009': '客胜41.6%仍是首选，但市场压到59.3%已无价值，平+客双选更稳',
        '010': '客胜43.4%，市场62.7%过热，建议客胜+平双选，或让(+1)让胜',
        '011': '客胜与主胜几乎并列，平局被抬到28.8%，这场最不建议单压一边',
        '012': '主胜55.2%是全轮单关里方向最清楚的，可让(-1)让平做价值',
        '013': '主胜67.9%，但让(-1)让胜仅56.5%，"赢球"与"打穿"要分开',
        '014': '平局36.5%成首选，德甲保级对话，平+客双选',
        '015': '主胜58.1%，λ总4.75偏大，让(-1)让平只有18.6%，谨慎追穿盘',
        '016': '平局47.8%为全轮最高，模型与市场方向相反，只建议平+客双选或放弃',
    }
    for r in ms:
        if not r['is_single']:
            continue
        mt, mp = market_top(r)
        L.append('| %s | %s vs %s | %s %s | **%s** | %s %s | %s |' % (
            r['num'][-3:], r['home'], r['away'], CN[r['primary']], pct(r['primary_prob'], 0),
            pct(r['fused']['draw'], 0), CN[mt], pct(mp, 0), advice.get(r['num'][-3:], '')))
    L.append('')
    L.append('> 单关上修口径：平局按"与首选差距"分档 +8~13pp（差距≤10pp 取 +13pp、10~20pp 取 +11pp、≥20pp 取 +8pp），主胜/客胜按原比例压缩，累计上限 +18pp。九场当中 **016 的平局上修幅度最大（+13pp）**，把平局推到 47.8%，成为全轮最高的单一结果概率；**008（+13pp→45.3%）、014（+11pp→36.5%）** 也直接变成首选。这正是单关信号的用法——**提示平局风险，而不是让你去买平。**')
    L.append('')
    L.append('> **⚠️ 口径提醒：** 单关上修是模型端的结构性修正，不是市场信号。上修后的平局概率**不能直接当作"价值"**——上修前 016 的平局是 34.8%、008 是 32.3%、014 是 25.5%，与市场去水后的 27.4% / 31.3% / 26.2% 对比，只有 016 明显高出市场。**判断是否有价值，要看上修前的基准，而不是上修后的数字。**')
    L.append('')

    # 搏冷
    L.append('## 搏冷推荐汇总')
    L.append('')
    L.append('| 编号 | 对阵 | 搏冷方向 | 模型概率 | 市场方向 | 市场概率 | 分歧 | 类型 |')
    L.append('|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
    for r in ms:
        mt, mp = market_top(r)
        if mt == r['primary']:
            continue
        if r['diverge'] < 0.09:
            continue
        L.append('| %s | %s vs %s | **%s** | %s | %s | %s | %.0fpp | 方向对立 |' % (
            r['num'][-3:], r['home'], r['away'], CN[r['primary']], pct(r['primary_prob'], 0),
            CN[mt], pct(mp, 0), r['diverge'] * 100))
    L.append('')
    L.append('> 搏冷仅适合极小注娱乐。本轮方向对立的典型场次：**008 赫塔费（模型平45.3% vs 市场客胜39.0%）、014 柏林联合（模型平36.5% vs 市场客胜38.0%）、016 利物浦（模型平47.8% vs 市场客胜41.2%）、018 莱切（模型主胜43.4% vs 市场客胜39.9%）、025 新英格兰（模型主胜43.8% vs 市场客胜45.0%）**。分歧越大不确定性越高，只适合极小注。')
    L.append('')
    L.append('**市场过热场次（支持率>55%）：**')
    L.append('')
    for r in ms:
        mt, mp = market_top(r)
        if mp <= 0.55:
            continue
        if mp <= r['fused'][mt] + 0.005:
            continue
        L.append('- %s %s vs %s：%s支持率 %s，模型给 %s，追热性价比低，防平/防冷门。' % (
            r['num'][-3:], r['home'], r['away'], CN[mt], pct(mp, 0), pct(r['fused'][mt], 0)))
    L.append('')
    L.append('> 市场过热≠一定冷门，但赔率价值已被压缩，追热性价比低。')
    L.append('')

    # 串关
    L.append('## 串关思路')
    L.append('')
    L.append('> 本轮25场（>8场），按场次数量以**三串一为主**，连续编号方案固定二串一。以下仅为方案参考，请根据自身判断与资金管理选择。')
    L.append('')

    def leg(num, pool, key, cn_text):
        r = BY['周日' + num]
        o = odds_of(r, pool, key)
        return {'num': num, 'pool': pool, 'key': key, 'odds': o, 'text': cn_text}

    def name(num):
        r = BY['周日' + num]
        return '%s%s' % (num, '主胜' if False else ''), r

    def parlay_line(label, legs, kind, risk, note):
        prod = 1.0
        for g in legs:
            prod *= (g['odds'] or 1.0)
        body = ' + '.join('%s %s' % (g['num'], g['text']) for g in legs)
        odds_txt = ' x '.join('%.2f' % (g['odds'] or 0) for g in legs)
        return '| %s | %s | %s | %s | **%.2f** | %s |' % (label, kind, body, odds_txt, prod, risk)

    L.append('### 方向串（胜平负）')
    L.append('')
    L.append('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    L.append('|:---|:---|:---|:---:|:---:|:---|')
    a_legs = [leg('007', 'had', 'home', '主胜'), leg('013', 'had', 'home', '主胜'), leg('003', 'had', 'home', '主胜')]
    b_legs = [leg('020', 'had', 'home', '主胜'), leg('012', 'had', 'home', '主胜'), leg('017', 'had', 'home', '主胜')]
    L.append(parlay_line('方向串A（稳健）', a_legs, '同向·高概率', '中', ''))
    L.append(parlay_line('方向串B（价值）', b_legs, '同向·市场低估', '中高', ''))
    L.append('')
    L.append('> 方向串只取模型与市场**同向**的场次：A串 007主胜（77.4%/76.4%）、013主胜（67.9%/68.6%）、003主胜（78.0%/55.9%）；B串 020主胜（68.4%/50.2%）、012主胜（55.2%/46.0%）、017主胜（58.9%/62.3%）。**005/008/014/016/018/025 方向与市场相反，一律不进方向串。**')
    L.append('')
    L.append('### 让球串（让球胜平负）')
    L.append('')
    L.append('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    L.append('|:---|:---|:---|:---:|:---:|:---|')
    L.append(parlay_line('稳健让球串', [leg('018', 'hhad', 'home', '让(1)让胜'), leg('005', 'hhad', 'home', '让(1)让胜')],
                          '容错优先', '中', ''))
    L.append(parlay_line('价值让球串', [leg('017', 'hhad', 'draw', '让(-1)让平'), leg('024', 'hhad', 'draw', '让(-1)让平')],
                          '高赔价值', '中高', ''))
    L.append('')
    L.append('> **稳健让球串**：018让(+1)让胜（莱切不败）70.3%、005让(+1)让胜（珀斯不败）66.9%，两场都是受让方不败的容错盘。')
    L.append('')
    L.append('> **价值让球串**：017让(-1)让平（法兰克福正好赢一球）22.3%、024让(-1)让平（格雷米奥正好赢一球）21.0%，赔率高但需精准。')
    L.append('')
    L.append('### 混合串（方向/半全场混合）')
    L.append('')
    L.append('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    L.append('|:---|:---|:---|:---:|:---:|:---|')
    L.append(parlay_line('方向+半全场A', [leg('003', 'had', 'home', '主胜'), leg('007', 'hafu', 'HH', '胜胜')],
                          '混合', '中高', ''))
    L.append(parlay_line('方向+半全场B', [leg('020', 'had', 'home', '主胜'), leg('012', 'hafu', 'HH', '胜胜')],
                          '混合', '中高', ''))
    L.append(parlay_line('连续编号混合串A', [leg('003', 'had', 'home', '主胜'), leg('004', 'hafu', 'HH', '胜胜')],
                          '混合·003+004', '中高', ''))
    L.append(parlay_line('连续编号混合串B', [leg('012', 'hafu', 'HH', '胜胜'), leg('013', 'hafu', 'HH', '胜胜')],
                          '混合·012+013', '中高', ''))
    L.append('')
    L.append('> **方向+半全场A/B**：A取"町田碾压+科莫半场即领先"（003主胜+007胜胜）；B取"维塞乌主场+弗洛西诺内半场定调"（020主胜+012胜胜），两串赛事与路径不重复。')
    L.append('')
    L.append('> **连续编号混合串A/B**：A取003+004（町田主胜 + 首尔胜胜），B取012+013（弗洛西诺内胜胜 + 拉齐奥胜胜），均为编号相邻段。')
    L.append('')
    L.append('### 娱乐串（高赔率组合）')
    L.append('')
    L.append('> **⚠️ 娱乐串风险提示：** 以下方案均为高赔率组合，单次命中概率极低（通常<5%），仅供娱乐参考，切勿重注。建议每注投入不超过总资金的1%-2%，量力而行。高赔率意味着高风险，未中奖为常态。')
    L.append('')
    L.append('> **📋 选场核心原则：** 娱乐串以基本面（伤停/战意/状态/交锋/赛制）为主，模型概率仅作辅助参考。本轮核心抓手：**九场单关的平局风险**（008/009/010/011/012/013/014/015/016）、**残阵缺口**（柏林联合中卫+中场双缺、都灵中卫线长期缺人、巴伦西亚缺中卫+头号中锋），以及**强队主场碾压**（007科莫、013拉齐奥、003町田）。')
    L.append('')
    L.append('> **🔢 串关数量说明：** 本轮25场（>8场），**以三串一为主**；每个子分类保留2个原方案＋2个连续编号方案。')
    L.append('')
    L.append('> **🏗️ 娱乐串结构：** 四个子分类全部保留（高赔总进球串／高赔半全场串／半全场混合总进球串／比分串），比分串含单挑比分①②，合计18个方案。')
    L.append('')
    L.append('> **🚫 法甲排除：** 今日非PSG法甲场次 N=1（022 马赛vs图卢兹），N<3 → 娱乐串纳入0场，022 不得出现在以下任何方案。')
    L.append('')
    L.append('#### 高赔总进球串（4个方案）')
    L.append('')
    L.append('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    L.append('|:---|:---|:---|:---:|:---:|:---|')
    L.append(parlay_line('总进球串A', [leg('015', 'ttg', '4', '4球'), leg('025', 'ttg', '3', '3球')], '原方案', '高', ''))
    L.append(parlay_line('总进球串B', [leg('011', 'ttg', '3', '3球'), leg('025', 'ttg', '4', '4球')], '原方案', '高', ''))
    L.append(parlay_line('连续编号总进球A', [leg('003', 'ttg', '3', '3球'), leg('004', 'ttg', '2', '2球')], '003+004', '高', ''))
    L.append(parlay_line('连续编号总进球B', [leg('013', 'ttg', '2', '2球'), leg('014', 'ttg', '3', '3球')], '013+014', '高', ''))
    L.append('')
    L.append('> A取两场λ总值最高的荷甲/美职对攻（015总4.75、025总3.96）；B取挪超布兰vs莫尔德（总3.99）与美职（3.96）的高进球组合；连续编号段A=003+004（日职+韩职）、B=013+014（意甲+德甲）。')
    L.append('')
    L.append('#### 高赔半全场串（4个方案）')
    L.append('')
    L.append('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    L.append('|:---|:---|:---|:---:|:---:|:---|')
    L.append(parlay_line('半全场串A', [leg('015', 'hafu', 'HH', '胜胜'), leg('013', 'hafu', 'HH', '胜胜')], '原方案', '高', ''))
    L.append(parlay_line('半全场串B', [leg('009', 'hafu', 'AA', '负负'), leg('010', 'hafu', 'AA', '负负')], '原方案', '高', ''))
    L.append(parlay_line('连续编号半全场A', [leg('007', 'hafu', 'HH', '胜胜'), leg('008', 'hafu', 'DD', '平平')], '007+008', '高', ''))
    L.append(parlay_line('连续编号半全场B', [leg('019', 'hafu', 'HH', '胜胜'), leg('020', 'hafu', 'HH', '胜胜')], '019+020', '高', ''))
    L.append('')
    L.append('> 半全场串A取荷甲格罗宁根与意甲拉齐奥"半场即领先"（胜胜）；B取瑞超/荷甲两场客队半场压制（009负负2.15 + 010负负1.95）。')
    L.append('')
    L.append('#### 半全场混合总进球串（4个方案）')
    L.append('')
    L.append('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    L.append('|:---|:---|:---|:---:|:---:|:---|')
    L.append(parlay_line('半全场+总进球A', [leg('017', 'hafu', 'HH', '胜胜'), leg('018', 'ttg', '2', '2球')], '原方案', '高', ''))
    L.append(parlay_line('半全场+总进球B', [leg('021', 'hafu', 'DD', '平平'), leg('025', 'ttg', '3', '3球')], '原方案', '高', ''))
    L.append(parlay_line('连续编号混合A', [leg('023', 'hafu', 'HH', '胜胜'), leg('024', 'ttg', '2', '2球')], '023+024', '高', ''))
    L.append(parlay_line('连续编号混合B', [leg('024', 'hafu', 'DD', '平平'), leg('025', 'ttg', '3', '3球')], '024+025', '高', ''))
    L.append('')
    L.append('> A取法兰克福半场即领先+莱切热那亚低进球（胜胜 + 2球）；B取尤文那不勒斯半场僵持+美职对攻（平平 + 3球）；连续编号段A=023+024、B=024+025，覆盖西甲德比与巴西杯/美职。')
    L.append('')
    L.append('#### 比分串（6个方案，含单挑①②）')
    L.append('')
    L.append('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
    L.append('|:---|:---|:---|:---:|:---:|:---|')
    L.append(parlay_line('比分串A（稳健）', [leg('007', 'crs', '2:0', '2-0'), leg('013', 'crs', '2:0', '2-0')], '方向+众数带内', '极高', ''))
    L.append(parlay_line('比分串B（搏冷）', [leg('020', 'crs', '2:1', '2-1'), leg('003', 'crs', '2:0', '2-0')], '方向+众数带内', '极高', ''))
    L.append(parlay_line('连续编号比分A', [leg('003', 'crs', '2:0', '2-0'), leg('004', 'crs', '1:0', '1-0')], '003+004', '极高', ''))
    L.append(parlay_line('连续编号比分B', [leg('012', 'crs', '2:1', '2-1'), leg('013', 'crs', '2:0', '2-0')], '012+013', '极高', ''))
    L.append(parlay_line('单挑比分①', [leg('007', 'crs', '2:0', '2-0'), leg('004', 'crs', '1:0', '1-0')], '单挑', '极高', ''))
    L.append(parlay_line('单挑比分②', [leg('008', 'crs', '1:1', '1-1'), leg('012', 'crs', '2:1', '2-1')], '单挑', '极高', ''))
    L.append('')
    L.append('> **比分串三约束（方向一致＋k_rec带＋赔率逻辑）核对：** 007（主胜/k=+2/2-0 13.8%）、013（主胜/k=+2/2-0 14.2%）、020（主胜/k=+1/2-1 9.4%）、003（主胜/k=+2/2-0 9.8%）、004（主胜/k=+1/1-0 10.9%）、012（主胜/k=+1/2-1 9.1%）、008（平/k=0/1-1 14.5%）——七场全部落在各自 `k_rec` 净胜球带内、方向与HAD首推一致。**两处主动放弃：** 003 的 3-0 虽是模型最高分，但净胜+3 超出 k_rec=+2 带；015 带内最高 2-1 仅 6.9%（<8% 胜率门槛），两场均不进入正向比分串。')
    L.append('')
    L.append('> **单挑①②**：①取科莫2-0（垫底威尼斯客场场均失2.11，带内TOP1 13.8%）+ 首尔1-0（K联赛领头羊主场对仁川，带内TOP1 10.9%）；②取赫塔费1-1（全轮最低总进球之一、单关平局，带内TOP1 14.5%）+ 弗洛西诺内2-1（主场场均2.44球，带内TOP1 9.1%）。')
    L.append('')

    # 数据与口径
    L.append('## 数据与口径说明')
    L.append('')
    L.append('- **概率链路：** 积分榜场均进失球 → 攻击/防守强度（按场次收缩，10场左右样本强度约0.6权重）→ 守恒式 λ → DC/负二项/ZIP/Skellam/蒙特卡洛五模型加权（0.34/0.22/0.13/0.14/0.17）→ 联赛修正 → 单关修正 → 归一。**赔率不参与任何一步概率生成**，仅去水后用于对照分歧。')
    L.append('- **积分榜来源：** football-charts 当季实时榜（日职12轮、韩职33轮、澳超2-3轮、荷甲10轮、意甲9轮、西甲10-11轮、瑞超26轮、挪超24-25轮、德甲7-8轮、英超8轮、葡超9-10轮、法甲8-9轮、巴甲30轮、美职32轮），抓取时间 2026-11-01 11:20 前后。024 巴西杯为淘汰赛，两队联赛数据取自巴甲榜单。')
    L.append('- **联赛修正：** 英超主场加成下调（主胜-4pp、平局+5pp）；西甲平局+4pp、意甲平局+3pp、韩职平局+3pp；法甲非PSG平局+5pp（仅022，娱乐串已按法甲过滤口径排除）。')
    L.append('- **单关修正：** 008-016 共九场由用户赛前告知开单关，按平局与首选差距分档上修（+13/+11/+8pp，上限+18pp）。未告知场次一律视为未开单关。')
    L.append('- **大球上修：** 触发条件为身价差≥2倍 / λ差≥0.8 / 让球≥1球 / 排名差≥8位；德甲·西甲·意甲 Tier1（+0.15~0.20球）、日职·韩职·荷甲·挪超·葡超·法甲·瑞超 Tier2（+0.30~0.35球）、澳超·巴西杯·美职 Tier3（+0.40~0.45球），英超按例外不上修。')
    L.append('- **半场修正：** 半场平局率按联赛取值（日职0.534、韩职0.512、西甲0.441、意甲0.409、法甲/葡超/美职0.40、荷甲0.387、英超0.384、德甲0.359、挪超0.325等），并据此调整半全场分布。')
    L.append('- **大小球六档：** 以2.5球为界，按P(0-1球)/P(2-3球)/P(4-5球)/P(6+球)与总进球众数落档；"大小球"与"总进球"合并为同一行输出。')
    L.append('- **场地：** 25场均无空场/部分关闭/中立场公告，主场加成全额；024 巴西杯为主客场制淘汰赛，非中立场。')
    L.append('- **信息口径：** 伤停/场地/天气/身价/交锋为赛前检索（Transfermarkt、FotMob、各联赛与俱乐部官网、直播吧等），部分场次官方名单未公布，伤停人数为公开报道统计，存在赛前变动可能。')
    L.append('- **置信度口径：** 由首选概率、模型-市场分歧、交锋样本完整度、伤停规模四项打分（≥3★、1-2★★、0★、<0☆）。')
    L.append('')
    L.append('> **最后提醒：** 25场里真正"方向+比分都干净"的只有 007/013/020/003 四场；其余大多数属于"方向可判、比分难猜"。**单关不是稳胆，残阵不是必冷，分歧不是价值**——九场单关同时开，恰恰说明今天没有哪一场是白送的。控制注码，比猜对一场更重要。理性购彩，量力而行。')
    L.append('')
    L.append('---')
    L.append('')
    L.append('*本报告由竞彩分析管道自动生成：信息收集 → 信息核查 → 联赛分析 → 基本面 → 五模型融合 → 串关优化 → 报告输出 → 报告审核。*')

    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('saved', OUT, len(L), 'lines')


if __name__ == '__main__':
    build()
