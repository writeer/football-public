# -*- coding: utf-8 -*-
"""生成 2026-11-02 周一 回测报告（知乎 Markdown，模板 zhihu_backtest_template）"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
PRED = os.path.join(BASE, 'reports', 'data', '20261102_predictions.json')
MODEL = os.path.join(BASE, 'reports', 'data', '20261102_model_output.json')
BT = os.path.join(BASE, 'memory', 'backtests', '20261102_monday', 'backtest.json')
OUT = os.path.join(BASE, 'reports', 'backtest', 'backtest_20261102_monday_zhihu.md')

DIR = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC = {'win': '胜', 'push': '平', 'lose': '负'}
TIME = {'周一001': '00:00', '周一002': '01:30', '周一003': '02:00', '周一004': '03:45', '周一005': '03:45',
        '周一006': '04:00', '周一007': '04:00', '周一008': '04:15', '周一009': '07:00'}

NOTES = {
    '周一001': '方向首选主胜命中，但过程与赛前“低进球”假设完全相反：国际图尔库4-3火花、7球对攻，半场1-1。让(-1)平靠次选兜住，半全场平胜在TOP2命中；总进球押2/3球、六档押2-3球，与7球差了整整三档——赛前“国际主场场均1.07球+本季三战不胜火花”的低进球逻辑被彻底击穿。',
    '周一002': '方向靠次选客胜兜住（首选主胜落空）；但让(+1)胜70.5%这条“全场最高概率腿”被打穿：佛罗伦萨客场4战3负的样本被高估，实际客队打进4球。总进球6球、半全场平负、半场1-1全部在池外，仅“大球”方向命中。',
    '周一003': '本轮最完整的一场：方向首选、让球次选让平、总进球3球、半全场胜胜、半场1-0、六档全部命中；唯一漏的是比分2-1（TOP5为1-1/1-0/0-0/2-0/0-1，未含2-1）。低战意+13人缺阵下，“盖斯主场防守+一次定位球”的判断兑现。',
    '周一004': '本轮最大翻车：首选主胜61.0%、次选平，实际0-3。9人伤停+3天后欧协联的降级信号只落到λ×0.78和降星，没有落到方向首选；让球端更可惜——模型最高腿本是让(-1)负38.0%，被L253“主胜≥55%禁让负”强制改成让胜36.4%，结果让负才是正确答案。',
    '周一005': '三路平开（34.6/33.3/32.1）的六分战，实际南锡4-1大胜；模型把“南锡法乙最佳防守”读成低进球，忽略了红星主场4战1胜的崩盘风险。方向三项全错，但让(-1)负64.6%稳稳兜住——这是“低★场只做让球容错”的正面样本。',
    '周一006': '单关主胜40.1%落空（0-1）。埃弗顿“近两次做客SJP全胜”的交锋信号只写进了风险提示，没有进次选（次选给了平）；而让(-1)负59.0%、半场0-0、比分0-1三项全中，说明模型对“低进球+埃弗顿不败”的判断是对的，错在把方向首选放在主胜。',
    '周一007': '本轮仅次于003的完整场：方向首选、让球次选让平、比分2-1（TOP3）、总进球3球、半场0-1、六档全中；唯一漏掉半全场“负胜”——TOP3是胜胜/平胜/平平，L250要求的“半场≠全场覆盖位”没有执行。',
    '周一008': '让(-2)负50.9%、与市场分歧15.8pp的判断完全正确：本菲卡轮换只赢1球，深盘打不穿。比分1-0（TOP5末位）、半场0-0、半全场平胜（TOP2）都命中；但总进球/六档押3球+“大球”，实际只有1球——身价8.58倍的直觉压过了10天3赛的轮换信号。',
    '周一009': '官方 getUniformMatchResultV1 在 09:33 仍返回空比分（`lastUpdateTime=2026-11-03 09:33:47`），按规则单列待结算，不以任何非官方比分顶替。方向/让球/比分/半全场/总进球/六档及3个含009的串关全部挂账。',
}


def pct(x):
    return f'{x * 100:.1f}%'


def line_str(line):
    return f'{int(line):+d}'


def grade(h, t):
    if not t:
        return '—'
    r = h / t
    if r >= 1:
        return '完美'
    if r >= 0.75:
        return '优秀'
    if r >= 0.6:
        return '良好'
    if r >= 0.45:
        return '一般'
    return '较差'


def split_ratio(s):
    h, t = s.split('/')
    return int(h), int(t)


def hit_label(row, key):
    if row['status'] != 'settled':
        return '⏳'
    v = row['hits'].get(key)
    if v is None:
        return '—'
    return '✅' if v else '❌'


def main():
    preds = {p['num']: p for p in json.load(open(PRED, encoding='utf-8'))}
    model = json.load(open(MODEL, encoding='utf-8'))
    bt = json.load(open(BT, encoding='utf-8'))
    rows = {r['num']: r for r in bt['rows']}
    agg = bt['aggregate']
    parlays = bt['parlays']

    d_h, d_t = split_ratio(agg['direction_cover'])
    p_h, p_t = split_ratio(agg['direction_primary'])
    hc_h, hc_t = split_ratio(agg['handicap_cover'])
    hcp_h, hcp_t = split_ratio(agg['handicap_primary'])

    L = []
    L.append('# 【回测】2026-11-02（周一）回测报告 | 方向4/7、让球6/8、串关0/26；004残阵翻车、008深盘判断兑现')
    L.append('')
    L.append('> **报告说明：** 本文为赛后**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。赛前**分析报告**（标题标注【分析】）提供方向/比分/总进球等预测推荐。历史报告可去主页查找。')
    L.append('')
    L.append('> **风险提示：** 9场中8场已按体彩官方接口结算，**009布拉干蒂诺vs桑托斯官方未开奖（`sectionsNo999`为空），按规则单列“待结算”，不以任何非官方比分顶替**，其相关维度与3个含009的串关不计入命中率。赔率数据以采集时为准。**理性看待预测，切勿沉迷赌博。**')
    L.append('')
    L.append('> **⚠️ 免责声明：** 本文所有回测数据、命中率统计、教训分析仅供学习交流参考，不构成任何投注建议。回测结果具有时效性，历史命中不代表未来表现。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
    L.append('')
    L.append('*每日更新，关注主页获取最新赛事分析*')
    L.append('')
    L.append('9场中8场结算（009巴甲官方未开奖，单列待结算）。**方向含次选4/7=57.1%、仅首选3/7=42.9%；让球含次选6/8=75.0%是唯一“优秀”维度；26注已结算串关全灭、ROI -100%。** 最大亮点是008让(-2)负与007的五维命中，最大翻车是004亚特兰大9人残阵仍押主胜61%，被打成0-3。')
    L.append('')

    # 总览
    L.append('## 总览')
    L.append('')
    L.append('| 编号 | 对阵 | 赛事 | 预测方向(首选/次选) | 实际方向 | 命中 | 让球 | 让球命中 | 总进球 | 进球命中 | 半全场 | 半全场命中 | 比分TOP5命中 |')
    L.append('|:---:|:---|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
    for num in sorted(preds):
        p, r = preds[num], rows[num]
        rec = p['recommendation']
        a = r['actual']
        if num == '周一008':
            d = '未开HAD'
        else:
            d = f'{DIR[rec["had_primary"]]}/{DIR[rec["had_secondary"]]}'
        hc = f'让({line_str(rec["hc_line"])}){HC[rec["hc_primary"]]}'
        if r['status'] != 'settled':
            L.append(f'| {num[-3:]} | {p["home"]}vs{p["away"]} | {p["league"]} | {d} | 待结算 | ⏳ | {hc} | ⏳ | {rec["ttg_top2"][0]}球(实际—) | ⏳ | {rec["hafu_top3"][0]["pick"]}(实际—)/{rec["hafu_top3"][1]["pick"]}/{rec["hafu_top3"][2]["pick"]} | ⏳ | ⏳ |')
            continue
        actual_dir = DIR[a['direction']]
        dir_lab = '—' if num == '周一008' else ('✅首' if r['hits']['direction_primary'] else ('✅次' if r['hits']['direction_secondary'] else '❌'))
        hc_lab = '✅首' if r['hits']['handicap_primary'] else ('✅次' if r['hits']['handicap_secondary'] else '❌')
        ttg_lab = '✅' if r['hits']['ttg_top2'] else '❌'
        hafu_lab = '✅' if r['hits']['hafu_top3'] else '❌'
        cr_lab = '✅' if r['hits']['score_top5'] else '❌'
        hafu_str = f'{rec["hafu_top3"][0]["pick"]}/{rec["hafu_top3"][1]["pick"]}/{rec["hafu_top3"][2]["pick"]}(实际{a["htft"]})'
        L.append(f'| {num[-3:]} | {p["home"]}vs{p["away"]} | {p["league"]} | {d} | {actual_dir} | {dir_lab} | {hc} | {hc_lab} | {rec["ttg_top2"][0]}球(实际{a["score"]}) | {ttg_lab} | {hafu_str} | {hafu_lab} | {cr_lab} |')
    L.append('')
    L.append(f'> 方向含次选{d_h}/{d_t}、仅首选{p_h}/{p_t}；让球含次选{hc_h}/{hc_t}、仅首选{hcp_h}/{hcp_t}；总进球3/8、半全场3/8、比分3/8、半场比分5/8、六档3/8。9场中009单列待结算，不计入分母。')
    L.append('')

    # 逐场
    L.append('## 逐场回测')
    L.append('')
    for num in sorted(preds):
        p, r = preds[num], rows[num]
        rec = p['recommendation']
        mo = model[num]
        a = r['actual']
        L.append(f'### {num[-3:]} {p["home"]} vs {p["away"]}（{p["league"]}）')
        L.append('')
        if r['status'] == 'settled':
            L.append(f'⏰ {TIME[num]}（北京时间11-03）｜ 🏟 — ｜ **{a["score"]}**')
            L.append('')
            L.append(f'**赛果：** 半场{a["ht_score"]} → 全场{a["score"]} ｜ 总进球{a["total"]} ｜ {DIR[a["direction"]]} ｜ 让({line_str(a["goalLine"])}){HC[a["handicap"]]}')
        else:
            L.append(f'⏰ {TIME[num]}（北京时间11-03）｜ 🏟 — ｜ 官方未开奖')
            L.append('')
            L.append('**赛果：** 半场— → 全场— ｜ 总进球— ｜ 方向—（`sectionsNo999`为空，待结算）')
        L.append('')
        L.append('**预测回顾：**')
        L.append('')
        L.append('| 维度 | 预测 | 实际 | 命中 |')
        L.append('|:---|:---|:---|:---:|')
        if r['status'] != 'settled':
            if num == '周一008':
                L.append('| **方向** | 未开HAD | 待结算 | ⏳ |')
            else:
                L.append(f'| **方向** | {DIR[rec["had_primary"]]}({pct(rec["had_primary_prob"])}) / {DIR[rec["had_secondary"]]}({pct(rec["had_secondary_prob"])}) | 待结算 | ⏳ |')
            sec = r['prediction']['hc_secondary']
            L.append(f'| **让球** | 让({line_str(rec["hc_line"])}){HC[rec["hc_primary"]]}({pct(mo["handicap"][rec["hc_primary"]])}) / 让({line_str(rec["hc_line"])}){HC[sec]}({pct(mo["handicap"][sec])}) | 待结算 | ⏳ |')
            t1, t2 = rec['ttg_top2']
            L.append(f'| **总进球TOP2** | **{t1}球**({pct(mo["ttg"][str(t1)])}) / **{t2}球**({pct(mo["ttg"][str(t2)])}) | 待结算 | ⏳ |')
            h = rec['hafu_top3']
            L.append(f'| **半全场TOP3** | **{h[0]["pick"]}**({pct(h[0]["prob"])}) > **{h[1]["pick"]}**({pct(h[1]["prob"])}) > **{h[2]["pick"]}**({pct(h[2]["prob"])}) | 待结算 | ⏳ |')
            cr = rec['cr_top5']
            L.append('| **比分TOP5** | ' + ' > '.join(f'**{x["score"]}**({pct(x["prob"])})' for x in cr) + ' | 待结算 | ⏳ |')
            ht = rec['ht_score']
            L.append('| **半场比分TOP3** | ' + ' > '.join(f'**{x["score"]}**({pct(x["prob"])})' for x in ht) + ' | 待结算 | ⏳ |')
            L.append(f'| **大小球六档** | **{rec["tier"]}**（{rec["over_under"]}） | 待结算 | ⏳ |')
        else:
            if num == '周一008':
                L.append(f'| **方向** | 未开HAD（模型 {pct(p["model"]["home"])}/{pct(p["model"]["draw"])}/{pct(p["model"]["away"])}） | {DIR[a["direction"]]} | — |')
            else:
                L.append(f'| **方向** | {DIR[rec["had_primary"]]}({pct(rec["had_primary_prob"])}) / {DIR[rec["had_secondary"]]}({pct(rec["had_secondary_prob"])}) | {DIR[a["direction"]]} | {"✅首" if r["hits"]["direction_primary"] else ("✅次" if r["hits"]["direction_secondary"] else "❌")} |')
            sec = r['prediction']['hc_secondary']
            L.append(f'| **让球** | 让({line_str(rec["hc_line"])}){HC[rec["hc_primary"]]}({pct(mo["handicap"][rec["hc_primary"]])}) / 让({line_str(rec["hc_line"])}){HC[sec]}({pct(mo["handicap"][sec])}) | 让({line_str(a["goalLine"])}){HC[a["handicap"]]} | {"✅首" if r["hits"]["handicap_primary"] else ("✅次" if r["hits"]["handicap_secondary"] else "❌")} |')
            t1, t2 = rec['ttg_top2']
            L.append(f'| **总进球TOP2** | **{t1}球**({pct(mo["ttg"][str(t1)])}) / **{t2}球**({pct(mo["ttg"][str(t2)])}) | **{a["total"]}球** | {"✅" if r["hits"]["ttg_top2"] else "❌"} |')
            h = rec['hafu_top3']
            L.append(f'| **半全场TOP3** | **{h[0]["pick"]}**({pct(h[0]["prob"])}) > **{h[1]["pick"]}**({pct(h[1]["prob"])}) > **{h[2]["pick"]}**({pct(h[2]["prob"])}) | **{a["htft"]}** | {"✅" if r["hits"]["hafu_top3"] else "❌"} |')
            cr = rec['cr_top5']
            L.append('| **比分TOP5** | ' + ' > '.join(f'**{x["score"]}**({pct(x["prob"])})' for x in cr) + f' | **{a["score"]}** | {"✅" if r["hits"]["score_top5"] else "❌"} |')
            ht = rec['ht_score']
            L.append('| **半场比分TOP3** | ' + ' > '.join(f'**{x["score"]}**({pct(x["prob"])})' for x in ht) + f' | **{a["ht_score"]}** | {"✅" if r["hits"]["ht_score_top3"] else "❌"} |')
            L.append(f'| **大小球六档** | **{rec["tier"]}**（{rec["over_under"]}） | {a["total"]}球 | {"✅" if r["hits"]["tier"] else "❌"} |')
            if p.get('is_single'):
                L.append(f'| **单关** | {DIR[rec["had_primary"]]}({pct(rec["had_primary_prob"])}) | {DIR[a["direction"]]} | {"✅" if r["hits"]["direction_primary"] else "❌"} |')
        L.append('')
        L.append(f'> {NOTES[num]}')
        L.append('')

    # 命中率
    L.append('## 命中率统计')
    L.append('')
    L.append('| 维度 | 命中/总场 | 命中率 | 评级 |')
    L.append('|:---|:---:|:---:|:---:|')
    dims = [
        ('方向(首选+次选)', agg['direction_cover']),
        ('方向(仅首选)', agg['direction_primary']),
        ('让球(首选+次选)', agg['handicap_cover']),
        ('让球(仅首选)', agg['handicap_primary']),
        ('总进球TOP2', agg['ttg_top2']),
        ('半全场TOP3', agg['hafu_top3']),
        ('比分TOP5', agg['score_top5']),
        ('半场比分TOP3', agg['ht_score_top3']),
        ('大小球六档', agg['tier']),
        ('大小球方向(大/小)', agg['over_under']),
    ]
    for label, ratio in dims:
        h, t = split_ratio(ratio)
        L.append(f'| **{label}** | {h}/{t} | {pct(h / t) if t else "—"} | {grade(h, t)} |')
    L.append('')
    L.append(f'> 方向命中明细：首选命中{p_h}场 + 次选命中{d_h - p_h}场 = 合计{d_h}场命中，未中{d_t - d_h}场（{", ".join(n[-3:] for n in agg["settled_nums"] if n != "周一008" and not rows[n]["hits"]["direction_cover"])}）；008未开HAD不计入方向分母。')
    L.append('')
    L.append(f'> 让球命中明细：首选命中{hcp_h}场 + 次选命中{hc_h - hcp_h}场 = 合计{hc_h}场命中，未中{hc_t - hc_h}场（{", ".join(n[-3:] for n in agg["settled_nums"] if not rows[n]["hits"]["handicap_cover"])}）；**让球仅首选命中{hcp_h}/{hcp_t}={pct(hcp_h / hcp_t)}**。')
    L.append('')
    L.append('> 单关006：方向主胜40.1% ❌，但让(-1)负、半场0-0、比分0-1三项命中，属于“方向错、结构对”的单关。')
    L.append('')

    # 置信度
    L.append('## 置信度表现')
    L.append('')
    L.append('| 置信度 | 已结算场次 | 方向(首选+次选) | 方向(仅首选) | 让球(首选+次选) | 让球(仅首选) |')
    L.append('|:---:|:---:|:---:|:---:|:---:|:---:|')
    for conf, label in [('★★', '中★★'), ('★', '低★')]:
        nums = [n for n in agg['settled_nums'] if rows[n]['confidence'] == conf]
        dn = [n for n in nums if rows[n]['hits']['direction_cover'] is not None]
        dp = sum(1 for n in dn if rows[n]['hits']['direction_primary'])
        dc = sum(1 for n in dn if rows[n]['hits']['direction_cover'])
        hp = sum(1 for n in nums if rows[n]['hits']['handicap_primary'])
        hcv = sum(1 for n in nums if rows[n]['hits']['handicap_cover'])
        L.append(f'| **{label}** | {len(nums)} | {dc}/{len(dn)}（{pct(dc / len(dn))}） | {dp}/{len(dn)}（{pct(dp / len(dn))}） | {hcv}/{len(nums)}（{pct(hcv / len(nums))}） | {hp}/{len(nums)}（{pct(hp / len(nums))}） |')
    L.append('')
    L.append('> ★★仅006/007两场：方向1/2、让球2/2；007五维命中，006方向错但让球/比分/半场全对。★7场中008无HAD、009待结算，有效方向样本5场（3/5），让球样本6场（4/6）。**低★的让球覆盖66.7%明显高于方向60.0%，继续支持“低★只出双选+让球容错”的用法。**')
    L.append('')

    # 串关
    L.append('## 串关回测')
    L.append('')
    L.append('> 以赛前分析报告的原始推荐为基准，28个方案全部列出；搏冷比分串按报告“2注”拆成两行展示。共29行，已结算26、待结算3（含009）。')
    L.append('')
    L.append('| 方案 | 类型 | 场次 | 各场结果 | 串关命中 | 估算赔率 |')
    L.append('|:---|:---|:---|:---|:---:|:---:|')
    for pl in parlays:
        legs = []
        for leg in pl['legs']:
            num = leg['num']
            if leg['market'] == 'had':
                pick = f'{num[-3:]}{DIR[leg["pick"]]}'
                actual = rows[num]['actual']
                mark = '⏳' if leg['hit'] is None else ('✅' if leg['hit'] else '❌')
                detail = '待结算' if leg['hit'] is None else DIR[actual['direction']]
            elif leg['market'] == 'hhad':
                pick = f'{num[-3:]}让({line_str(preds[num]["recommendation"]["hc_line"])}){HC[leg["pick"]]}'
                actual = rows[num]['actual']
                mark = '⏳' if leg['hit'] is None else ('✅' if leg['hit'] else '❌')
                detail = '待结算' if leg['hit'] is None else (f'让({line_str(actual["goalLine"])}){HC[actual["handicap"]]}' if leg['hit'] else f'让({line_str(actual["goalLine"])}){HC[actual["handicap"]]}')
            elif leg['market'] == 'ttg':
                pick = f'{num[-3:]} {leg["pick"]}球'
                actual = rows[num]['actual']
                mark = '⏳' if leg['hit'] is None else ('✅' if leg['hit'] else '❌')
                detail = '待结算' if leg['hit'] is None else f'{actual["total"]}球'
            elif leg['market'] == 'hafu':
                pick = f'{num[-3:]}{leg["pick"]}'
                actual = rows[num]['actual']
                mark = '⏳' if leg['hit'] is None else ('✅' if leg['hit'] else '❌')
                detail = '待结算' if leg['hit'] is None else (actual['htft'] if leg['hit'] else actual['htft'])
            else:
                pick = f'{num[-3:]} {leg["pick"]}'
                actual = rows[num]['actual']
                mark = '⏳' if leg['hit'] is None else ('✅' if leg['hit'] else '❌')
                detail = '待结算' if leg['hit'] is None else actual['score']
            legs.append(f'{pick}({mark}{detail})')
        sym = {'win': '✅', 'lose': '❌', 'pending': '⏳'}[pl['status']]
        L.append(f'| {pl["name"]} | {pl["type"]} | {" + ".join(legs)} | {sym} | ~{pl["odds"]:.2f} |')
    L.append('')
    type_order = ['方向串', '让球串', '混合串', '高赔总进球串', '高赔半全场串', '半全场混合总进球串', '比分串']
    parts = []
    for t in type_order:
        ps = [x for x in parlays if x['type'] == t]
        s = [x for x in ps if x['status'] != 'pending']
        w = sum(1 for x in s if x['status'] == 'win')
        extra = f"，待结算{len(ps) - len(s)}" if len(ps) != len(s) else ''
        parts.append(f'{t}{w}/{len(s)}{extra}')
    L.append('> 按子类：' + '、'.join(parts) + '。')
    L.append('')
    L.append('> **串关汇总：0/26命中（3个待结算），命中率0.0%，ROI -100.0%。** 稳健组（方向串+让球串+混合串）0/9，娱乐组（高赔总进球串+高赔半全场串+半全场混合总进球串+比分串）0/17。方向串A死在004主胜、方向串B死在006主胜；稳健让球串只差007的“让平”、价值让球串只差002的“让(+1)负”；比分串7行里6行直接落空。**翻车主因：4条主胜腿（004/006）与同场半全场+总进球绑腿，单场方向错误被串关放大。**')
    L.append('')

    # 关键发现
    L.append('## 关键发现')
    L.append('')
    L.append('**1. 方向结构性问题：8场中7场首选主胜，其中4场实际客胜。** 002靠次选客胜兜住，而004/005/006次选都给“平”、三场全灭。真正的分水岭不是首选概率，而是次选有没有给到客胜——凡是“主队残阵、客队客场有韧性、或同主客交锋客队占优”的场次，次选给平等于放弃第二次机会。')
    L.append('')
    L.append('**2. 让球是唯一优秀维度（6/8=75.0%），但仅首选只有3/8=37.5%，靠次选让平三次兜底。** 001/003/007三场都是“-1盘、净胜1球 → 让平”，而赛前次选全部写了让平；004则相反，L253把模型最高腿让负38.0%改成让胜36.4%，直接造成一次反向。')
    L.append('')
    L.append('**3. 串关全灭不是运气问题，是“腿的独立性”问题。** 方向串A/B都是三腿全主胜，004/006一崩整串即死；稳健让球串/价值让球串各只差一腿；娱乐组里半全场与总进球高度绑定同一场比赛（008的“胜胜+3球”“007胜胜+008 3球”同源），一错俱错。')
    L.append('')
    L.append('**4. 总进球与六档出现“单点故障”：9场全部押“常规正常球(2-3球)”。** 实际分布是1球×2、3球×3、5球×1、6球×1、7球×1——三场被低估（001/002/005），两场被高估（006/008），六档只有3/8。全天同档意味着只要轮次风格偏移，这一维度就整体报废。')
    L.append('')

    # 待改进
    L.append('## 待改进')
    L.append('')
    L.append('- **规则32“残阵降级”必须传导到方向首选。** 004亚特兰大9人伤停+3天后欧协联，只降λ与星级、没改首选方向，实际0-3。改进：单队≥7人伤停且3天内有欧战 → HAD首选不得为“主胜”，改平局或直接降为“只出让球”。')
    L.append('- **L253需要“残阵例外”。** 004因“主胜≥55%禁让负”放弃让负38.0%，实际让负。改进：当同一场已触发残阵降级时，L253的禁让负条款失效，让球首选回到模型最高腿。')
    L.append('- **主胜首选场的次选结构要改写。** 004/005/006三场次选都给平、全部落空。改进：客队近5个客场≥2胜、或同主客交锋客队占优、或主队残阵 → 次选优先客胜；只有“客队客场全败且无交锋优势”时才给平。')
    L.append('- **六档禁止全天同档，半全场TOP3强制变盘位。** 本轮六档3/8、半全场3/8，且6/8场次“半场≠全场”。改进：全天至少两端各留一场（≤1球、≥5球）；半全场TOP3固定保留1条变盘路径（平负/负胜/负负）。')
    L.append('- **比分TOP5与串关门槛。** 4个比分未中全是尾部大比分（4-3/2-4/0-3/1-4）；串关0/26。改进：残阵/深盘/客队反击信号场次，TOP5必须含一个净胜≥3的尾部比分；方向仅首选<45%的轮次，方向串≤1个、比分串暂停。')
    L.append('')

    # 写在最后 方案E
    L.append('## ☕ 写在最后')
    L.append('')
    L.append('本文全部方案免费分享，如觉内容有价值，欢迎请作者一杯咖啡。')
    L.append('')
    L.append('投资是长线工程，盈利了是逻辑验证，暂未盈利也无需焦虑——坚持正确的方法论，结果自然会来。')
    L.append('')
    L.append('你们的关注与支持，是我持续优化的动力。')
    L.append('')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    print('written', OUT, len(L), 'lines')


if __name__ == '__main__':
    main()
