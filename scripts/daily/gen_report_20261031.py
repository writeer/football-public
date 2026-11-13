# -*- coding: utf-8 -*-
"""2026-10-31（周六）知乎分析报告生成器（28场，005/006/025为单关）"""
import json, io

res = json.load(io.open('reports/data/20261031_model_output.json', encoding='utf-8'))
infos = json.load(io.open('reports/data/20261031_info.json', encoding='utf-8'))
R = {r['num'].replace('周六', ''): r for r in res}
ORDER = ['%03d' % i for i in range(1, 29)]

HAD_CN = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC_CN = {'home': '让胜', 'draw': '让平', 'away': '让负'}
HAFU_KEY = {'胜胜': 'HH', '胜平': 'HD', '胜负': 'HA', '平胜': 'DH', '平平': 'DD',
            '平负': 'DA', '负胜': 'AH', '负平': 'AD', '负负': 'AA'}

TEAM_DOM_LEAGUE = {
    '冈山绿雉': '日职', '东京FC': '日职', '仙台七夕': '日乙', '大宫松鼠RB': '日乙',
    '柏太阳神': '日职', '浦和红钻': '日职', '光州FC': '韩职', '金泉尚武': '韩职',
    '麦克阿瑟FC': '澳超', '西悉尼漫步者': '澳超',
    '切尔西': '英超', '曼彻斯特联': '英超', '林肯城': '英冠', '伯明翰': '英冠',
    '莱万特': '西甲', '马德里竞技': '西甲', '博洛尼亚': '意甲', '蒙扎': '意甲',
    '勒沃库森': '德甲', '斯图加特': '德甲', '沙尔克04': '德甲', '莱比锡红牛': '德甲',
    '奥格斯堡': '德甲', '弗赖堡': '德甲', '门兴格拉德巴赫': '德甲', '帕德博恩': '德甲',
    '云达不来梅': '德甲', '霍芬海姆': '德甲', '考文垂': '英超', '桑德兰': '英超',
    '伯恩茅斯': '英超', '利兹联': '英超', '赫尔城': '英超', '伊普斯维奇': '英超',
    '布伦特福德': '英超', '诺丁汉森林': '英超', '腓特烈斯塔': '挪超', '罗森博格': '挪超',
    '巴列卡诺': '西甲', '维戈塞尔塔': '西甲', '乌迪内斯': '意甲', '罗马': '意甲',
    '托特纳姆热刺': '英超', '水晶宫': '英超', '拜仁慕尼黑': '德甲', '多特蒙德': '德甲',
    '皇家贝蒂斯': '西甲', '马拉加': '西甲', 'AC米兰': '意甲', '国际米兰': '意甲',
    '阿斯顿维拉': '英超', '富勒姆': '英超', '巴塞罗那': '西甲', '阿拉维斯': '西甲',
    '阿贾克斯': '荷甲', '阿尔克马尔': '荷甲',
}
LEAGUE_TIER = {'英超': 1, '西甲': 1, '意甲': 1, '德甲': 1, '法甲': 1,
               '荷甲': 2, '挪超': 2, '日职': 2, '韩职': 2,
               '英冠': 3, '日乙': 3, '澳超': 3}
COMP_TIER = {'英超': '国内联赛·顶级', '西甲': '国内联赛·顶级', '意甲': '国内联赛·顶级',
             '德甲': '国内联赛·顶级', '荷甲': '国内联赛·甲级', '挪超': '国内联赛·甲级',
             '日职': '国内联赛·甲级', '韩职': '国内联赛·甲级',
             '英冠': '国内联赛·次级', '日乙': '国内联赛·次级', '澳超': '国内联赛·顶级（澳超）'}

# 总控补充说明（只写事实性背景，不覆盖模型数字）
SPECIAL = {
    '006': '单关焦点：切尔西失若昂·佩德罗与主力门将、周中还踢了联赛杯；曼联整周备战但伤停同样到5人。模型给主胜43.8%、平局经单关上修到33.9%，这是一场"谁先犯错"的比赛，直接压主胜的风险高于让球容错。',
    '023': '德国国家德比：两队同积17分，拜仁净胜球+19、主场3战18球；多特近5场零封、靠低位防守与反击。模型主胜56.6%，但市场把拜仁压到1.19（约81%），分歧17pp——拜仁赢球不难，难的是让(-2)能否打穿。',
    '025': '米兰德比+单关：国米联赛8胜1平不败、米兰近4次德比3胜1平，但米兰双中卫托莫里/加比亚同时缺阵，国米失劳塔罗。模型主胜37.9%、平局经单关上修到37.2%，几乎是三选一里的"硬币局"，不建议只压一边。',
    '027': '本场未开胜平负（仅让球-3），市场概率由比分盘推导。巴萨6人伤缺、其中4名后卫，下周还有欧战；阿拉维斯五后卫低位。模型主胜76.9%，但让(-3)让胜只有43.8%，让球端不宜追。',
    '024': '贝蒂斯主场（比利亚马林改造，临时使用La Catuja）对垫底马拉加，客队5人伤缺含两名十字韧带。模型主胜71.8%、净胜球众数+2，是本轮结构最干净的场次之一。',
    '005': '单关悉尼德比：双方同积4分，麦克阿瑟5人伤缺、替补深度受损，西悉尼仅缺1名轮换前锋；天气预报阵雨、北风5级。模型平局经单关上修到34.6%成为首选，1-1是唯一与方向一致的比分。',
    '003': '柏太阳神周中亚冠长途飞行、浦和周三联赛杯踢满120分钟，双方体能都在临界点；柏主场传控对浦和21.5次/场传中。模型主胜60.5%，是本轮日系场次里方向最清晰的一场。',
    '010': '勒沃库森主场全胜但刚0-3负霍芬海姆；斯图加特联赛5负、还失去斯蒂勒与两名右后卫。模型主胜60.2%，市场1.64（约57%），方向一致、分歧7pp。',
    '021': '罗马3天2赛且周中欧冠，迪巴拉、佩莱格里尼、科内同时缺阵；乌迪内斯三场不进球但五后卫收缩。模型客胜57.6%，让(+1)让胜（乌迪内斯不败）37.1%是更稳的容错位。',
    '022': '热刺7人伤缺、攻击线几乎断档，周中联赛杯虽胜曼城但轮换消耗；水晶宫三中卫+反击专克热刺高位防线。模型主胜39.9%、市场主胜1.50（约62%），分歧19pp，是本轮最典型的"市场追热、模型不跟"场次。',
    '013': '门兴8人伤缺、联赛失球最多（22球），主场开局3连败；帕德博恩两轮不败。模型客胜39.0%略高于主胜38.1%，与市场（主胜1.74、约57%）方向相反13pp，属于"基本面与市场预期相反"的场次。',
    '011': '沙尔克8人伤缺、主场3场0球；莱比锡客场3战全负（2-11）。模型客胜51.9%，但让(+1)让胜（沙尔克不败）46.6%接近五五开，说明这场"强弱差"被双方各自的极端状态抵消了一部分。',
    '028': '阿贾克斯近5次对AZ不胜（0胜2平3负）、AZ最近做客2-0；两队下周都有欧战。模型主胜53.3%，市场1.54（约59%），分歧4pp，方向可信但让(-1)让负45.0%说明"赢两球"并不稳。',
}


def rank_cn(s):
    if not s:
        return '—'
    s = str(s)
    for lg in ('日职', '日乙', '韩职', '澳超', '英超', '英冠', '西甲', '意甲', '德甲', '挪超', '荷甲'):
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
    return r['hhad_model'][side] if r.get('hhad_model') else 0.0


def short(num):
    return num.replace('周六', '')


def ht_time(r):
    t = r['time'][:5]
    hh = int(t.split(':')[0])
    return ('11-01 ' if hh < 12 else '10-31 ') + t


def with_rank(name, rank):
    rr = rank_cn(rank)
    return '%s（%s）' % (name, rr) if rr and rr != '—' else name


def tier_line(r):
    h, a, comp = r['home'], r['away'], r['league']
    hl = LEAGUE_TIER.get(TEAM_DOM_LEAGUE.get(h), 2)
    al = LEAGUE_TIER.get(TEAM_DOM_LEAGUE.get(a), 2)
    return '**联赛等级：** %s（%s）｜同联赛内战，不触发跨联赛等级差先验（主队%s L%d vs 客队%s L%d）' % (
        comp, COMP_TIER.get(comp, '赛事'), TEAM_DOM_LEAGUE.get(h, '?'), hl,
        TEAM_DOM_LEAGUE.get(a, '?'), al)


def venue_line(r):
    v, w = r['venue'], r['weather']
    st = v.get('status') or '正常'
    if st == '正常':
        status = ' ｜场地状态：正常（无空场/中立场公告）'
    else:
        status = ' ｜⚠️场地状态：%s（%s）' % (st, v.get('status_note') or '')
    pitch = v.get('pitch') or '信息缺失'
    return '⏰ %s ｜ 🏟 %s，%s，%s，容量%s%s ｜ 🌤 %s，%s，%s，影响%s' % (
        ht_time(r), v['name'], v['city'], pitch, format(int(v['capacity']), ','),
        status, w['temp'], w['desc'], w['wind'], w['impact'])


def value_line(r):
    vh, va = r['value']['home'], r['value']['away']
    n = max(vh, va) / min(vh, va)
    hi = '主队' if vh >= va else '客队'
    lo = '客队' if vh >= va else '主队'
    if n >= 2:
        judge = '身价碾压（%.1f倍），硬实力差距明显，模型已按实力差上修进球期望' % n
    elif n >= 1.5:
        judge = '身价有差距（%.2f倍），强队仍需解决"破密集/防反击"的临场问题' % n
    else:
        judge = '身价接近（%.2f倍），硬实力相当，胜负更适合由临场状态、伤停与主场因素决定' % n
    return '**身价对比：** 主队%s总身价约%s vs 客队%s总身价约%s，%s是%s的%.2f倍。%s。' % (
        r['home'], eu(vh), r['away'], eu(va), hi, lo, n, judge)


def injury_line(r):
    inj = r['injury']
    h = '；'.join(inj['home']) if inj['home'] else '无确认缺阵'
    a = '；'.join(inj['away']) if inj['away'] else '无确认缺阵'
    return '**伤停：** 主队%d人（%s）；客队%d人（%s）。%s' % (
        inj['home_count'], h, inj['away_count'], a, inj.get('note', ''))


def h2h_line(r):
    return '**交锋：** %s。' % r['h2h']['summary'].rstrip('。')


def news_line(r):
    c = infos.get('周六' + short(r['num']), {}).get('context') or {}
    bits = [c.get(k) for k in ('stake', 'fitness', 'psych') if c.get(k)]
    text = '；'.join(bits) if bits else '信息缺失'
    return '**球队动态：** %s。%s' % (text, r['injury'].get('note', ''))


def context_block(r):
    c = infos.get('周六' + short(r['num']), {}).get('context') or {}
    lu = infos.get('周六' + short(r['num']), {}).get('lineup') or {}
    if not c:
        return ''
    return ('> **战意心理与体能分析：**\n'
            '> - 战意：%s\n'
            '> - 体能与休息：%s\n'
            '> - 心理因素：%s\n'
            '> - 赛程牵制：%s\n'
            '> - 预计首发：主队 %s；客队 %s') % (
        c.get('stake', '—'), c.get('fitness', '—'), c.get('psych', '—'),
        c.get('schedule', '—'), lu.get('home', '—'), lu.get('away', '—'))


def trigger_line(r):
    bits = []
    if r.get('rule65'):
        if '例外不上修' in r['rule65']:
            bits.append('实力差距触发条件已满足（%s），但英超按例外**不上修**，λ未加码' %
                        r['rule65'].replace('触发（', '').replace('）但英超按例外不上修', ''))
        else:
            bits.append('实力差距触发大球上修——%s' % r['rule65'])
    if r.get('rule_shift'):
        bits.append(r['rule_shift'])
    if r.get('rule63'):
        bits.append(r['rule63'])
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
        if div <= 0.05:
            cmp_txt = ('市场看%s %.0f%%，与模型首选%s %.0f%% 几乎持平（分歧%.0fpp），属**方向不明的五五开场次**' % (
                HAD_CN[mdir[0]], mdir[1] * 100, HAD_CN[r['primary']], r['primary_prob'] * 100, div * 100))
        else:
            cmp_txt = ('市场看%s %.0f%%，与模型首选%s %.0f%% **方向不一致**，分歧%.0fpp%s' % (
                HAD_CN[mdir[0]], mdir[1] * 100, HAD_CN[r['primary']], r['primary_prob'] * 100,
                div * 100, '（基本面与市场预期相反）' if div > 0.15 else '（属边际分歧，需谨慎）'))
    elif div > 0.07:
        cmp_txt = '与市场%s %.0f%% 同向，轻度分歧%.0fpp' % (HAD_CN[mdir[0]], mdir[1] * 100, div * 100)
    else:
        cmp_txt = '与市场%s %.0f%% 基本对齐（分歧%.0fpp）' % (HAD_CN[mdir[0]], mdir[1] * 100, div * 100)
    if r.get('had_source', '').startswith('CRS'):
        cmp_txt = '本场未开胜平负，市场概率由比分盘推导——' + cmp_txt
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


def formation(text):
    if not text:
        return '阵型未公布'
    t = text.split('：')[0]
    for sep in ('（', '('):
        t = t.split(sep)[0]
    return t.strip() or '阵型未公布'


def preview_block(r):
    k = short(r['num'])
    top3 = r['top_scores'][:3]
    scen, used = [], 0
    for a, b, p in top3:
        d = 'home' if a > b else ('away' if a < b else 'draw')
        scen.append('%s → 候选 %d-%d（模型%.1f%%）' % (SCENE[d][used % 3], a, b, p * 100))
        used += 1
    lu = infos.get('周六' + k, {}).get('lineup') or {}
    style = '主队%s、客队%s' % (formation(lu.get('home')), formation(lu.get('away')))
    tempo = '节奏%s' % ('偏快' if r['lambda_total'] > 3.2 else ('偏慢' if r['lambda_total'] < 2.4 else '中等'))
    return ('> **比分推演（参考模型）：**\n'
            '> - 球队数据：%s 期望进球 %.2f；%s 期望进球 %.2f；双方合计%d人缺阵\n'
            '> - 比赛风格：%s；%s，交锋节奏特征：%s，天气影响%s\n'
            '> - 比分推演：%s\n'
            '> - 局势解读：半场倾向%s → 全场%s（HAD首选），总进球指向%s，半全场指向%s') % (
        with_rank(r['home'], r['home_rank']), r['lambda_home'],
        with_rank(r['away'], r['away_rank']), r['lambda_away'],
        r['injury']['home_count'] + r['injury']['away_count'],
        style, tempo, r['h2h'].get('rhythm') or '无特殊', r['weather']['impact'],
        '；'.join(scen),
        '%d-%d' % (r['ht_scores'][0][0], r['ht_scores'][0][1]),
        HAD_CN[r['primary']], r['tier'], r['htft_top3'][0][0])


def conf_reason(r):
    parts = ['首选%s %.0f%%' % (HAD_CN[r['primary']], r['primary_prob'] * 100),
             '模型-市场分歧%.0fpp' % (r['diverge'] * 100)]
    if r['injury']['home_count'] + r['injury']['away_count'] >= 10:
        parts.append('双方伤停合计%d人' % (r['injury']['home_count'] + r['injury']['away_count']))
    if not r['k_consistent']:
        parts.append('净胜球分布与方向分歧')
    if r.get('table_missing'):
        parts.append('积分榜缺%s' % '、'.join(r['table_missing']))
    return '，'.join(parts)


def comment(r):
    k = short(r['num'])
    if k in SPECIAL:
        return SPECIAL[k]
    mk = r['market']
    mdir = max(mk.items(), key=lambda x: x[1])
    if HAD_CN[mdir[0]] != HAD_CN[r['primary']] and r['diverge'] > 0.10:
        return ('模型首选%s（%.1f%%）与市场%s（%.0f%%）方向相反、分歧%.0fpp。基本面站在模型一侧时，这种场次适合小注或做让球容错；若基本面并不支持逆向，宁可放弃。'
                % (HAD_CN[r['primary']], r['primary_prob'] * 100, HAD_CN[mdir[0]],
                   mdir[1] * 100, r['diverge'] * 100))
    if r['diverge'] > 0.10:
        return ('模型与市场同向，但分歧%.0fpp——市场把%s的赔率价值压得较低。方向上不必逆市，但追热性价比一般，建议用让球或总进球替代直接买胜。'
                % (r['diverge'] * 100, HAD_CN[r['primary']]))
    if not r['k_consistent']:
        return ('模型与市场基本对齐，但净胜球分布众数落在%d球、与首选方向不一致——典型"方向可判、比分难猜"，更适合让球与总进球，不适合精猜比分。'
                % r['k_dist'])
    return '模型、市场与净胜球分布三者方向一致，是本轮结构较干净的场次；仍建议以首选+次选双选的方式控制风险。'


lines = []
P = lines.append

DIV10 = [k for k in ORDER if R[k]['diverge'] > 0.10]
OPP = [k for k in DIV10
       if HAD_CN[max(R[k]['market'].items(), key=lambda x: x[1])[0]] != HAD_CN[R[k]['primary']]]

P('# 【分析】2026-10-31（周六）28场竞彩全分析 | 三场单关：悉尼德比、切尔西vs曼联、米兰德比；拜仁多特榜首战')
P('')
P('> **报告说明：** 本文为赛前**分析报告**（标题标注【分析】），提供方向/比分/总进球等预测推荐。赛后将发布**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。历史报告可去主页查找。')
P('')
P('> **风险提示：** 今天共 **28 场**，是本周期最大的一天：**三场单关**（005 悉尼德比、006 切尔西vs曼联、025 米兰德比），**两场榜首/国家德比**（023 拜仁vs多特、025 米兰德比），**一场未开胜平负**（027 巴萨，仅让球-3）。伤停面同样夸张——热刺7人、沙尔克8人、门兴8人、不来梅8人、巴萨6人、AC米兰6人，**"残阵"是本轮最大的共同变量**。模型与市场分歧≥10pp的场次达到 %d 场（%s），其中方向相反的有 %d 场（%s），分歧过大一律不构成博胆。赔率采集时间 2026-10-31 上午（北京时间，体彩官方）。**理性看待预测，切勿沉迷赌博。**' % (
    len(DIV10), '/'.join(DIV10), len(OPP), '/'.join(OPP)))
P('')
P('> **⚠️ 免责声明：** 本文所有分析、预测、推荐仅供学习交流参考，不构成任何投注建议。足球比赛结果具有高度不确定性，任何预测均无法保证准确性。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
P('')
P('> **📊 近5日置信度命中率（滚动统计，数据源 memory/stats/confidence_stats.md）：** ★★★高 3/3=100.0% ｜ ★★中 28/37=75.7% ｜ ★低 17/24=70.8% ｜ ☆极低 1/1=100.0%。**结论：** "中★★配次选容错"仍是最稳结构，低★配次选同样能到70%；极低☆样本太小，不构成参考。')
P('')
P('*每日更新，关注主页获取最新赛事分析*')
P('')
P('28场全部是国内联赛，没有跨联赛等级差问题，但结构上分五类——**①三场单关**（005/006/025）：主任开单关=悬念信号，三场模型平局全部被上修，其中005和025的平局直接进入首选/次选；**②榜首战与德比**（006、023、025）：战意满格、对抗强度高，但拜仁让(-2)、米兰双中卫缺阵让"赢球"和"打穿"变成两件事；**③残阵对撞**（011、013、014、017、022、027）：单队5-8人缺阵，缺口集中在后防与锋线，是最容易出冷门的一类；**④强弱分明**（024、027、008、021）：模型主/客胜≥57%，但市场赔率已压得很低，价值在让球与总进球而非直接买胜；**⑤五五开混战**（001、004、005、016、020、025）：首选概率≤38%，方向本身不可重注。')
P('')
P('三场单关里，**005 悉尼德比**的模型平局34.6%已是首选；**006 切尔西vs曼联**主胜43.8%、平33.9%，是"主队略优但不敢压"的结构；**025 米兰德比**主胜37.9%、平37.2%，几乎是硬币局。**单关的价值在于"可以只买一场"，不在于这场更好猜。**')
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
_dists = []
for star in ('★★★', '★★', '★', '☆'):
    ks = [k for k in ORDER if R[k]['conf'] == star]
    if ks:
        _dists.append('%s %d场（%s）' % (star, len(ks), '/'.join(ks)))
cons_list = [k for k in ORDER if R[k]['k_consistent']]
P('> 本轮置信度分布：%s。**净胜球分布与方向一致的 %d 场**（%s），正向比分串可选面比上一轮宽，但仍集中在强队主场。' % (
    '、'.join(_dists), len(cons_list), '/'.join(cons_list) or '—'))
P('')

for k in ORDER:
    r = R[k]
    P('## %s %s vs %s（%s）' % (k, r['home'], r['away'], r['league']))
    P('')
    P(tier_line(r))
    P('')
    P(venue_line(r))
    P('')
    _inj_sum = r['injury']['home_count'] + r['injury']['away_count']
    P('%s主场作战；%s。%s。' % (
        with_rank(r['home'], r['home_rank']),
        with_rank(r['away'], r['away_rank']) + '做客',
        ('双方合计%d人缺阵（含停赛与成疑）' % _inj_sum) if _inj_sum
        else '双方暂无公开伤停，均接近最强阵容'))
    P('')
    P(news_line(r))
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
    P(context_block(r))
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
    if r.get('hhad_model'):
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
    hcf = ('**让(%s)%s**(%.0f%%)' % (r['hhad_line'], HC_CN.get(r['hc_first'], r['hc_first']),
                                     hc_pick(r, r['hc_first']) * 100)) if r.get('hhad_model') else '未开'
    hcs = ('**让(%s)%s**(%.0f%%)' % (r['hhad_line'], HC_CN.get(r['hc_second'], r['hc_second']),
                                     hc_pick(r, r['hc_second']) * 100)) if r.get('hhad_model') else '—'
    P('| %s | %s vs %s | %s(%.0f%%) | %s(%.0f%%) | %s | %s | **%s球**(%.0f%%) / **%s球**(%.0f%%) |' % (
        k, r['home'], r['away'],
        HAD_CN[r['primary']], r['primary_prob'] * 100,
        HAD_CN[r['secondary']], r['secondary_prob'] * 100,
        hcf, hcs,
        r['ttg_top2'][0], tgv.get(r['ttg_top2'][0], 0) * 100,
        r['ttg_top2'][1], tgv.get(r['ttg_top2'][1], 0) * 100))
P('')
P('> **让球口径说明：** 让球首选采用**无条件净胜球众数**，与HAD首推方向**口径独立**——本轮多数场次分布众数落在0球，因此让(-1)的场次首选普遍是"让负/让平"，让(+1/+2)的场次首选是"让胜"。这不是方向矛盾，而是让球盘本身在覆盖"方向出错"的可能。')
P('')

P('## 单关专项（005 / 006 / 025）')
P('')
P('| 编号 | 对阵 | 模型首选 | 平局(上修后) | 市场 | 建议 |')
P('|:---:|:---|:---:|:---:|:---:|:---|')
for k in ('005', '006', '025'):
    r = R[k]
    mk = r['market']
    mdir = max(mk.items(), key=lambda x: x[1])
    P('| %s | %s vs %s | %s %.0f%% | **%.1f%%** | %s %.0f%% | %s |' % (
        k, r['home'], r['away'], HAD_CN[r['primary']], r['primary_prob'] * 100,
        r['fused']['draw'] * 100, HAD_CN[mdir[0]], mdir[1] * 100,
        {'005': '平局首选，1-1 与方向一致；可单买平或平+客双选',
         '006': '主胜不过半，建议主胜+平双选，或让(-1)让负',
         '025': '平局逼近首选，德比不建议单压一边，平+主双选'}[k]))
P('')
P('> 单关上修口径：平局按"与首选差距"分档 +8~15pp（差距≤10pp 取 +13pp、10~20pp 取 +11pp、≥20pp 取 +8pp），主胜/客胜按原比例压缩，累计上限 +18pp。三场当中 025 的平局上修幅度最大（+11pp），直接把平局推到与主胜几乎并列，这正是单关信号的用法——**提示平局风险，而不是让你去买平。**')
P('')

P('## 搏冷推荐汇总')
P('')
P('| 编号 | 对阵 | 搏冷方向 | 模型概率 | 市场方向 | 市场概率 | 分歧 | 类型 |')
P('|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
cold = 0
for k in ORDER:
    r = R[k]
    mk = r['market']
    mdir = max(mk.items(), key=lambda x: x[1])
    if r['diverge'] > 0.15 and HAD_CN[r['primary']] != HAD_CN[mdir[0]]:
        P('| %s | %s vs %s | **%s** | %.0f%% | %s | %.0f%% | %.0fpp | 方向对立 |' % (
            k, r['home'], r['away'], HAD_CN[r['primary']], r['primary_prob'] * 100,
            HAD_CN[mdir[0]], mdir[1] * 100, r['diverge'] * 100))
        cold += 1
    elif r['diverge'] > 0.10 and HAD_CN[r['primary']] == HAD_CN[mdir[0]] and r['primary_prob'] >= 0.40:
        P('| %s | %s vs %s | **%s** | %.0f%% | %s | %.0f%% | %.0fpp | 价值追击 |' % (
            k, r['home'], r['away'], HAD_CN[r['primary']], r['primary_prob'] * 100,
            HAD_CN[mdir[0]], mdir[1] * 100, r['diverge'] * 100))
        cold += 1
if cold == 0:
    P('| — | 本轮无满足分歧门槛的场次 | — | — | — | — | — | — |')
P('')
P('> 搏冷仅适合极小注娱乐。本轮方向对立的典型场次：**013 门兴（模型客胜39.0% vs 市场主胜57%）、015 考文垂（模型主胜41.7% vs 市场客胜约45%）、016 伯恩茅斯（模型客胜37.1% vs 市场主胜约47%）、022 热刺（模型主胜39.9% vs 市场主胜约62%）、025 米兰（模型主胜37.9% vs 市场客胜约51%）**。分歧越大不确定性越高，只适合极小注。')
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
P('> 本轮28场（>8场），按场次数量以**三串一为主**，连续编号方案固定二串一。以下仅为方案参考，请根据自身判断与资金管理选择。')
P('')

P('### 方向串（胜平负）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
a3 = [(R['024'], 'home'), (R['010'], 'home'), (R['018'], 'home')]
o = [odd(r, 'had', s) for r, s in a3]
P('| 方向串A（稳健） | %s | %s | %s | 中 |' % (
    ' + '.join('%s%s' % (short(r['num']), HAD_CN[s]) for r, s in a3), odds_cell(o), total_cell(o)))
b3 = [(R['003'], 'home'), (R['008'], 'away'), (R['006'], 'home')]
o = [odd(r, 'had', s) for r, s in b3]
P('| 方向串B（价值） | %s | %s | %s | 中高 |' % (
    ' + '.join('%s%s' % (short(r['num']), HAD_CN[s]) for r, s in b3), odds_cell(o), total_cell(o)))
P('')
P('> 方向串只取模型与市场**同向**的场次：024主胜（71.8%/约84%）、010主胜（60.2%/约57%）、018主胜（52.1%/约53%）；B串取"同向但市场低估"的003主胜（60.5%/约50%）、008客胜（48.8%/约71%）、006主胜（43.8%/约55%）。**013/015/016/022/025 方向与市场相反，一律不进方向串。**')
P('')

P('### 让球串（让球胜平负）')
P('')
P('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---|:---:|:---|')
safe = [(R['017'], 'home'), (R['015'], 'home')]
o = [odd(r, 'hhad', s) for r, s in safe]
P('| 稳健让球串 | 容错优先 | %s | %s | %s | 中 |' % (
    ' + '.join('%s让(%s)%s' % (short(r['num']), r['hhad_line'], HC_CN[s]) for r, s in safe),
    odds_cell(o), total_cell(o)))
val = [(R['024'], 'draw'), (R['026'], 'draw')]
o = [odd(r, 'hhad', s) for r, s in val]
P('| 价值让球串 | 高赔价值 | %s | %s | %s | 中高 |' % (
    ' + '.join('%s让(%s)%s' % (short(r['num']), r['hhad_line'], HC_CN[s]) for r, s in val),
    odds_cell(o), total_cell(o)))
P('')
P('> **稳健让球串**：017让(+1)让胜（赫尔城不败）72.6%、015让(+1)让胜（考文垂不败）71.5%，两场都是受让方不败的容错盘。')
P('')
P('> **价值让球串**：024让(-1)让平（贝蒂斯正好赢一球）22.8%、026让(-1)让平（维拉正好赢一球）23.7%，赔率高但需精准。')
P('')

P('### 混合串（方向/半全场混合）')
P('')
P('| 方案 | 类型 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---|:---:|:---|')
o = [odd(R['024'], 'had', 'home'), odd(R['021'], 'hafu', 'AA')]
P('| 方向+半全场A | 混合 | 024主胜 + 021负负 | %s | %s | 中高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['018'], 'had', 'home'), odd(R['026'], 'hafu', 'HH')]
P('| 方向+半全场B | 混合 | 018主胜 + 026胜胜 | %s | %s | 中高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['017'], 'had', 'home'), odd(R['018'], 'hafu', 'HH')]
P('| 连续编号混合串A | 混合 | 017主胜 + 018胜胜 | %s | %s | 中高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['019'], 'hafu', 'AA'), odd(R['020'], 'ttg', '2')]
P('| 连续编号混合串B | 混合 | 019负负 + 020 2球 | %s | %s | 中高 |' % (odds_cell(o), total_cell(o)))
P('')
P('> **方向+半全场A/B**：A取"贝蒂斯碾压+罗马客场半场即领先"（024主胜+021负负）；B取"布伦特福德主场+维拉半场定调"（018主胜+026胜胜），两串赛事与路径不重复。')
P('')
P('> **连续编号混合串A/B**：A取017+018（赫尔城主场 + 布伦特福德胜胜），B取019+020（罗森博格负负 + 巴列卡诺2球），均为编号相邻段。')
P('')

P('### 娱乐串（高赔率组合）')
P('')
P('> **⚠️ 娱乐串风险提示：** 以下方案均为高赔率组合，单次命中概率极低（通常<5%），仅供娱乐参考，切勿重注。建议每注投入不超过总资金的1%-2%，量力而行。高赔率意味着高风险，未中奖为常态。')
P('')
P('> **📋 选场核心原则：** 娱乐串以基本面（伤停/战意/状态/交锋/赛制）为主，模型概率仅作辅助参考。本轮核心抓手：**三场单关的平局上修**（005/006/025）、**六支残阵的攻防缺口**（热刺7、沙尔克8、门兴8、不来梅8、巴萨6、AC米兰6），以及**两场强队主场碾压**（024贝蒂斯、027巴萨）。')
P('')
P('> **🔢 串关数量说明：** 本轮28场（>8场），**以三串一为主**；每个子分类保留2个原方案＋2个连续编号方案。')
P('')
P('> **🏗️ 娱乐串结构：** 四个子分类全部保留（高赔总进球串／高赔半全场串／半全场混合总进球串／比分串），比分串含单挑比分①②，合计18个方案。')
P('')
P('> **🚫 法甲排除：今日无法甲场次，不触发。**')
P('')

P('#### 高赔总进球串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
ttg_set = [('003', 4), ('006', 4), ('014', 4)]
o = [odd(R[k], 'ttg', str(n)) for k, n in ttg_set]
P('| 总进球串A | %s | %s | %s | 高 |' % (
    ' + '.join('%s %s球' % (k, n) for k, n in ttg_set), odds_cell(o), total_cell(o)))
ttg_set2 = [('010', 3), ('018', 2), ('026', 2)]
o = [odd(R[k], 'ttg', str(n)) for k, n in ttg_set2]
P('| 总进球串B | %s | %s | %s | 高 |' % (
    ' + '.join('%s %s球' % (k, n) for k, n in ttg_set2), odds_cell(o), total_cell(o)))
o = [odd(R['017'], 'ttg', '2'), odd(R['018'], 'ttg', '2')]
P('| 连续编号总进球串① | 017 2球 + 018 2球 | %s | %s | 高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['023'], 'ttg', '3'), odd(R['024'], 'ttg', '2')]
P('| 连续编号总进球串② | 023 3球 + 024 2球 | %s | %s | 高 |' % (odds_cell(o), total_cell(o)))
P('')
P('> **总进球串A**：003日职对攻（λ总4.27，双方周中双赛体能临界）→4球；006英超强强对话但双方锋线都有缺口（λ总3.64）→4球；014德甲对攻属性最强（λ总4.05、霍村3-0胜过药厂）→4球。三场档位独立判断，不机械取同一档。')
P('')
P('> **总进球串B**：010药厂主场火力但斯图加特缺斯蒂勒（λ总3.98）→3球；018森林客场进攻乏力（λ总2.63）→2球；026维拉主场对富勒姆历史比分偏小（λ总2.55）→2球。')
P('')
P('> **连续编号总进球串①/②**：017+018（英超两场2球，均为低比分结构）、023+024（拜仁多特3球 + 贝蒂斯2球），两组均为编号相邻段且档位差异化。')
P('')

P('#### 高赔半全场串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
hf = [('003', '胜胜'), ('021', '负负'), ('024', '胜胜')]
o = [odd(R[k], 'hafu', HAFU_KEY[p]) for k, p in hf]
P('| 高赔半全场串A | %s | %s | %s | 极高 |' % (
    ' + '.join('%s%s' % (k, p) for k, p in hf), odds_cell(o), total_cell(o)))
hf2 = [('010', '胜胜'), ('019', '负负'), ('027', '胜胜')]
o = [odd(R[k], 'hafu', HAFU_KEY[p]) for k, p in hf2]
P('| 高赔半全场串B | %s | %s | %s | 极高 |' % (
    ' + '.join('%s%s' % (k, p) for k, p in hf2), odds_cell(o), total_cell(o)))
o = [odd(R['001'], 'hafu', 'DA'), odd(R['002'], 'hafu', 'HH')]
P('| 连续编号高赔半全场串① | 001平负 + 002胜胜 | %s | %s | 极高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['025'], 'hafu', 'DH'), odd(R['026'], 'hafu', 'HH')]
P('| 连续编号高赔半全场串② | 025平胜 + 026胜胜 | %s | %s | 极高 |' % (odds_cell(o), total_cell(o)))
P('')
P('> **高赔半全场串A/B**：A取"柏主场压制+罗马客场半场领先+贝蒂斯碾压"（003胜胜/021负负/024胜胜）；B取"药厂半场定调+罗森博格客场领先+巴萨碾压"（010胜胜/019负负/027胜胜），同一串内路径无重复。')
P('')
P('> **连续编号高赔半全场串①/②**：001+002（冈山半场落后→全场负、仙台开局即压制→胜胜），025+026（米兰德比半场闷平→下半场分胜负、维拉胜胜），路径强制不同。')
P('')

P('#### 半全场混合总进球串（4个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
o = [odd(R['018'], 'hafu', 'HH'), odd(R['003'], 'ttg', '4')]
P('| 混合串A | 018胜胜 + 003 4球 | %s | %s | 极高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['021'], 'hafu', 'AA'), odd(R['024'], 'ttg', '2')]
P('| 混合串B | 021负负 + 024 2球 | %s | %s | 极高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['015'], 'ttg', '2'), odd(R['016'], 'hafu', 'AA')]
P('| 连续编号混合总进球串① | 015 2球 + 016负负 | %s | %s | 极高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['019'], 'hafu', 'AA'), odd(R['020'], 'ttg', '2')]
P('| 连续编号混合总进球串② | 019负负 + 020 2球 | %s | %s | 极高 |' % (odds_cell(o), total_cell(o)))
P('')
P('> **混合串A/B**：A取"布伦特福德主场半场定调+柏太阳神对攻4球"；B取"罗马客场半场领先+贝蒂斯主场2球"，两串赛事、路径与档位均不重复。')
P('')
P('> **连续编号混合总进球串①/②**：015+016（考文垂保级战2球 + 利兹客场半场领先）、019+020（罗森博格负负 + 巴列卡诺2球），均为编号相邻段。')
P('')

P('#### 比分串（6个方案）')
P('')
P('| 方案 | 场次 | 逐场赔率 | 串关赔率 | 风险 |')
P('|:---|:---|:---|:---:|:---|')
o = [odd(R['024'], 'crs', '2:0'), odd(R['005'], 'crs', '1:1')]
P('| 稳健比分串 | 024 2-0 + 005 1-1 | %s | %s | 高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['006'], 'crs', '1:2'), odd(R['022'], 'crs', '1:2')]
P('| 搏冷比分串（反向推理） | 006 1-2 + 022 1-2 | %s | %s | 极高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['003'], 'crs', '2:1'), odd(R['004'], 'crs', '1:2')]
P('| 连续编号比分串① | 003 2-1 + 004 1-2 | %s | %s | 高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['017'], 'crs', '2:1'), odd(R['018'], 'crs', '1:0')]
P('| 连续编号比分串② | 017 2-1 + 018 1-0 | %s | %s | 高 |' % (odds_cell(o), total_cell(o)))
o = [odd(R['024'], 'crs', '2:0')]
P('| 单挑比分① | 024 2-0（12.8%%，赔率%s） | %s | %s | 中 |' % (
    ('%.2f' % o[0]) if o[0] else '—', odds_cell(o), total_cell(o)))
o = [odd(R['027'], 'crs', '3:0')]
P('| 单挑比分② | 027 3-0（8.8%%，赔率%s） | %s | %s | 中 |' % (
    ('%.2f' % o[0]) if o[0] else '—', odds_cell(o), total_cell(o)))
P('')
P('> **稳健比分串**：按"方向一致＋众数带内＋概率≥8%＋赔率≥6.00"四条件筛，024 2-0（12.8%/7.00）与005 1-1（11.5%/6.75）均达标，且005是平局首选、1-1与方向一致。')
P('')
P('> **搏冷比分串**：反向推理——006切尔西vs曼联、022热刺vs水晶宫都是"市场追主队、模型不跟"的场次，取客队1-2作为冷门剧本，两场赔率均在10倍以上。')
P('')
P('> **连续编号比分串①/②**：003+004（柏主胜2-1 + 光州客胜1-2）、017+018（赫尔城主胜2-1 + 布伦特福德1-0），均为编号相邻段且方向各自一致。')
P('')
P('> **单挑比分①②**：024 2-0（净胜球众数+2、概率12.8%）、027 3-0（巴萨主场、概率8.8%），只取单场精准比分，不串关。')
P('')

P('## 数据与口径说明')
P('')
P('- **赔率**：体彩官方 2026-10-31 上午抓取，HAD/HHAD/CRS/TTG/HAFU 五类全玩法；027未开胜平负，市场概率由比分盘去水推导。')
P('- **积分榜**：日职/日乙/意甲/荷甲于 10-31 上午按 Transfermarkt 26/27 最新一轮刷新；德甲补齐门兴（此前缺行）；英超/英冠/西甲/韩职/澳超/挪超沿用最近一期当季榜。')
P('- **λ来源**：只由积分榜场均进失球→攻防强度→守恒式λ，赔率不参与求解；赔率仅用于去水对照与分歧计算。')
P('- **伤停/场地**：伤停来自俱乐部官网、FotMob、premierleague.com伤停页、bundesliga.com、Sky/Gazzetta 与中文源交叉；官方首发未公布，标"疑"者以赛前名单为准。28场均未检索到空场/中立场公告；024贝蒂斯临时使用同城La Cartuja、027诺坎普改造后开放62,652席，均非中立场。')
P('- **单关**：按用户赛前告知——周六005、周六006、周六025 开胜平负单关，其余场次视为未开单关。')
P('')
P('> **最后提醒：** 28场里真正"方向+比分都干净"的只有 003/010/024/027 四场；其余大多数属于"方向可判、比分难猜"。**单关不是稳胆，残阵不是必冷，分歧不是价值**——控制注码，比猜对一场更重要。理性购彩，量力而行。')
P('')

out = 'reports/analysis/20261031_saturday_analysis_zhihu.md'
io.open(out, 'w', encoding='utf-8').write('\n'.join(lines))
print('saved', out, len(lines), 'lines')
