# -*- coding: utf-8 -*-
"""生成 memory/predictions/20261105_thursday/prediction.json（项目口径）"""
import json, os

P = json.load(open('reports/data/20261105_predictions.json', encoding='utf-8'))
M = json.load(open('reports/data/20261105_model_output.json', encoding='utf-8'))

CONF = {'周四001': '★★★', '周四002': '★', '周四003': '★', '周四004': '★★', '周四005': '★★',
        '周四006': '★★★', '周四007': '★', '周四008': '★★★', '周四009': '★', '周四010': '★★',
        '周四011': '★', '周四012': '★★', '周四013': '★★★'}

VALUE = {
    '周四001': ('€17.00M', '€14.15M', 'https://www.transfermarkt.com/machida-zelvia/startseite/verein/23568', 'https://www.transfermarkt.com/shanghai-shenhua/startseite/verein/3183'),
    '周四002': ('€603M', '€281M', 'https://www.transfermarkt.com/crystal-palace/startseite/verein/873', 'https://www.transfermarkt.com/tsg-1899-hoffenheim/startseite/verein/533'),
    '周四003': ('€91.25M', '€624M', 'https://www.transfermarkt.com/ac-sparta-praha/startseite/verein/197', 'https://www.transfermarkt.com/afc-bournemouth/startseite/verein/989'),
    '周四004': ('€44.68M', '€21.45M', 'https://www.transfermarkt.com/nec-nijmegen/startseite/verein/467', 'https://www.transfermarkt.com/omonia-nikosia/startseite/verein/4177'),
    '周四005': ('€278M', '€259M', 'https://www.transfermarkt.com/real-sociedad-san-sebastian/startseite/verein/681', 'https://www.transfermarkt.com/olympique-lyon/startseite/verein/1041'),
    '周四006': ('€503M', '€38.25M', 'https://www.transfermarkt.com/ac-mailand/startseite/verein/5', 'https://www.transfermarkt.com/ferencvaros-budapest/startseite/verein/279'),
    '周四007': ('€184.30M', '€211M', 'https://www.transfermarkt.com/trabzonspor/startseite/verein/449', 'https://www.transfermarkt.com/sc-freiburg/startseite/verein/60'),
    '周四008': ('€459M', '€77.95M', 'https://www.transfermarkt.com/afc-sunderland/startseite/verein/289', 'https://www.transfermarkt.com/dinamo-zagreb/startseite/verein/419'),
    '周四009': ('€173M', '€119.35M', 'https://www.transfermarkt.com/real-club-celta-de-vigo/startseite/verein/940', 'https://www.transfermarkt.com/royale-union-saint-gilloise/startseite/verein/3948'),
    '周四010': ('€374M', '€54.50M', 'https://www.transfermarkt.com/sl-benfica/startseite/verein/294', 'https://www.transfermarkt.com/lech-posen/startseite/verein/1504'),
    '周四011': ('€129.30M', '€614M', 'https://www.transfermarkt.com/az-alkmaar/startseite/verein/1090', 'https://www.transfermarkt.com/juventus-turin/startseite/verein/506'),
    '周四012': ('€481M', '€182M', 'https://www.transfermarkt.com/bayer-04-leverkusen/startseite/verein/15', 'https://www.transfermarkt.com/olympique-marseille/startseite/verein/244'),
    '周四013': ('€218.58M', '€23.00M', 'https://www.transfermarkt.com/sociedade-esportiva-palmeiras/startseite/verein/1023', 'https://www.transfermarkt.com/clube-do-remo-pa-/startseite/verein/10997'),
}

STADIUM = {
    '周四001': '町田GION体育场（町田，正常）',
    '周四002': 'Selhurst Park（伦敦，正常）',
    '周四003': 'epet ARENA（布拉格，正常）',
    '周四004': 'Goffertstadion（奈梅亨，正常）',
    '周四005': 'Reale Arena（圣塞巴斯蒂安，正常）',
    '周四006': 'San Siro（米兰，正常）',
    '周四007': 'Papara Park（特拉布宗，正常）',
    '周四008': 'Stadium of Light（桑德兰，正常）',
    '周四009': 'Abanca-Balaídos（维戈，正常）',
    '周四010': 'Estádio da Luz（里斯本，正常）',
    '周四011': 'AFAS Stadion（阿尔克马尔，正常）',
    '周四012': 'BayArena（勒沃库森，正常）',
    '周四013': 'Allianz Parque（圣保罗，正常）',
}

INJ = {
    '周四001': '町田无重要伤停；申花4主力缺阵：陈晋一（左脚第五跖骨应力性骨折，11-05手术，休10-12周赛季报销）、朱辰杰（联赛结束后复出）、盖伊、李可。来源：新浪体育/7M/搜狐（中文媒体，**未验证一手**）。',
    '周四002': '水晶宫：萨尔（腹股沟）、富安健洋（小腿）、沙迪·里亚德（膝）缺阵，另有1名主力停赛（中文译名不一致待核），斯特兰德·拉森/廷贝尔存疑；霍芬海姆：赫洛热克（小腿）、赫拉纳奇、孔特缺阵。来源：水晶宫官网/Fotmob（一手）+球迷屋（中文，未验证）。',
    '周四003': '斯巴达：雷恩斯（左翼卫，2球3助攻）、卡拉贝奇（前腰队长，3球3助攻）缺阵；伯恩茅斯：斯科特（腿筋）、阿劳霍（腿筋）、米洛舍维奇（膝）伤缺，另有福斯特、阿伦斯、胡安卢、杰比森、克鲁皮5人未进入欧联名单。来源：Transfermarkt/球迷屋/腾讯（部分未验证）。',
    '周四004': '奈梅亨：塔迪奇（前腰核心，3助攻）、桑德勒、努伊丁克（踝）、莫尔（腹股沟）缺阵；奥莫尼亚：巴尔科维奇（左后卫）缺阵。来源：NEC官网/腾讯/球迷屋（未完全验证一手）。',
    '周四005': '皇社：奥德里奥索拉、贝蒂亚、扎哈良缺阵；里昂：奥彭达、莫顿（腹股沟）、苏尔茨、坎戈、韦德拉奥戈伤缺，尼亚卡特停赛，努瓦马11-04新增伤情。来源：Fotmob/球迷屋（未完全验证一手）。',
    '周四006': '米兰：托莫里（肌肉）、丘库埃泽（髋）伤缺，迈尼昂停赛；费伦茨瓦罗斯：库列诺维奇伤缺。来源：Transfermarkt/球迷屋。',
    '周四007': '特拉布宗：11人伤病+3人无报名资格（含门将塞维坎、后卫巴塔戈夫、边锋希姆希尔/弗兰库利诺），为全轮最严重残阵；弗赖堡：3人伤缺（奥格布斯等）。来源：球迷屋/Transfermarkt/弗赖堡官网。',
    '周四008': '桑德兰：迪亚拉（肌肉，约6周）、蒙德尔、巴拉德、穆基莱缺阵；迪纳摩：罗德里格斯、拉德尔吉奇、托皮奇、麦肯纳缺阵。来源：桑德兰官网/Fotmob（一手）。',
    '周四009': '塞尔塔：博尔哈·伊格莱西亚斯（左小腿肌腱断裂）、乌戈·冈萨雷斯、阿卜杜拉维、努内斯（腹股沟）、昆卡伤缺；圣吉罗斯：1人停赛未进大名单。来源：塞尔塔官网/球迷屋。',
    '周四010': '本菲卡：朗格莱（右大腿挫伤）、巴雷罗（右大腿肌肉）缺阵，巴雷内切亚恢复合练；莱赫：戈利扎德（十字韧带）、穆蒂尼奥（脚部骨折）、道格拉斯（踝）、蒙卡、伊沙克、萨亚德马内什缺阵。来源：本菲卡官网/搜狐/球迷屋（部分未验证）。',
    '周四011': 'AZ：霍恩坎普伤缺；尤文：麦肯尼（腹股沟）、伊尔迪兹、洛卡特利、孔塞桑、尼科·冈萨雷斯、切利克、图拉姆、格拉巴拉缺阵，斯帕莱蒂明确轮换（卢库米/洛卡特利休息，3天后联赛）。来源：懂球帝/球迷屋/微博（**未验证一手**）。',
    '周四012': '勒沃库森：迪亚比（大腿）、泰里耶、本塞吉尔、科法内、泰拉、巴代、杜埃、艾希霍恩8人伤缺，仅希克一名正印中锋；马赛：埃默森、科内利乌斯伤缺。来源：Fotmob/虎扑/球迷屋。',
    '周四013': '帕尔梅拉斯：拉蒙·索萨、保利尼奥、热夫特伤缺；里莫：波韦达、贾德森、马特乌斯·费利佩、若昂·卢卡斯伤缺，另有泽·韦利松、埃德森·费尔南多、贾贾停赛/缺席。来源：Fotmob/新浪（部分未验证）。',
}

RECENT = {
    '周四001': '町田J1第3（13轮8-4-1，30:10，近5 WWWDD），亚冠乙3战全胜9分、4:0；申花中超第6（29轮14-5-10，63:50，近5 LWWWL），亚冠小组赛前3轮积分未取到官方页（未验证）。',
    '周四002': '水晶宫英超第18（9轮2-1-6，9:21，近5 DWLLL），主场场均1.0球；霍芬海姆德甲第12（8轮3-0-5，14:16，近5 LLWWL），场均1.75/2.00。',
    '周四003': '斯巴达捷甲13轮7-2-4，25:13，23分（第2-3集团）；伯恩茅斯英超第8（9轮3-3-3，14:13，近5 LLWWW），欧联客场曾胜AC米兰。',
    '周四004': '奈梅亨荷甲第13（11轮2-5-4，17:19，近5 DDDDL）；奥莫尼亚塞浦路斯冠军，欧联3轮6分（胜塞尔塔、采列，负本菲卡），客场3胜1平3负。',
    '周四005': '皇社西甲第5（11轮6-1-4，20:20，近5 WWWWL）；里昂法甲第3（9轮5-2-2，15:7，近5 WLWLW），欧战客场5人缺阵。',
    '周四006': '米兰意甲第5（10轮6-3-1，21:12，近5 DWWLW）；费伦茨匈甲第3（11轮5-5-1，20:10，近5 DDDWW）。',
    '周四007': '特拉布宗土超第3（10轮7-1-2，24:8，近5 WWWWW），但伤停11人；弗赖堡德甲第3（8轮5-1-2，18:10，近5 DWLLW），欧协联前2轮不败。',
    '周四008': '桑德兰英超第20（9轮1-2-6，7:17，近5 LLLDL），欧联主场表现优于联赛；迪纳摩克甲第2（10轮22分、净胜+12），近5不败。',
    '周四009': '塞尔塔西甲第11（11轮2-6-3，10:10，近5 WDWDL），欧联曾0-3负奥莫尼亚；圣吉罗斯比甲第2（10轮8-2-0，29:7，近5 WWDWW），欧联4-0比尔舒华夏普尔、1-1皇社。',
    '周四010': '本菲卡葡超第2（10轮8-1-1，27:8，近5 WLWWW）；莱赫波甲第1（12轮10-1-1，32:11，近5 WWWWW），欧联客场表现偏弱。',
    '周四011': 'AZ荷甲第5（11轮6-2-3，20:13，近5 WLDLL）；尤文意甲第7（10轮5-2-3，13:10，近5 DLWLW），8人伤+明确轮换。',
    '周四012': '勒沃库森德甲第6（8轮4-1-3，18:16，近5 WWWLL），欧联前3轮零失球但联赛两场丢7球；马赛法甲第6（9轮5-0-4，20:13，近5 LWWWW），欧联3连胜。',
    '周四013': '帕尔梅拉斯巴甲第2（30轮18-9-3，52:22，63分，近5 DWDWW），争冠；里莫第19（30轮5-10-15，33:48，25分，近5 LLLDD），保级。',
}

H2H = {
    '周四001': '两队亚冠层面首次交锋（小组赛第4轮），无历史样本。',
    '周四002': '两队无正式交锋记录。',
    '周四003': '两队无正式交锋记录。',
    '周四004': '两队无正式交锋记录。',
    '周四005': '两队欧战无正式交锋记录（未取到可靠H2H源）。',
    '周四006': '两队无正式交锋记录。',
    '周四007': '两队无正式交锋记录。',
    '周四008': '两队无正式交锋记录。',
    '周四009': '两队无正式交锋记录。',
    '周四010': '两队欧战无正式交锋记录。',
    '周四011': '两队无正式交锋记录。',
    '周四012': '两队欧战有交锋史，但近年样本不足（未取到可靠H2H，未验证）。',
    '周四013': '2026-05-11 里莫主场1-1帕尔梅拉斯（FIFA Match Centre），本场为反向主客。',
}

RISK = {
    '周四001': '客队4主力伤缺但为客场；模型63.6% vs 市场71.3%（-7.8pp），亚冠样本薄。',
    '周四002': '单关首选43.6%<45%，平局上修后30.1%逼近；水晶宫联赛状态极差。',
    '周四003': '伯恩茅斯8人不可用（5人未报名），模型50.6% vs 市场65.0%（-14.4pp），接近分歧阈值。',
    '周四004': '奈梅亨核心塔迪奇缺阵，主胜48.4%<50%。',
    '周四005': '里昂5伤1停但为客场；皇社主场场均失1.82球。',
    '周四006': '迈尼昂停赛+托莫里伤；费伦茨欧战经验足。',
    '周四007': '特拉布宗11人伤病残阵，三方概率30.5/32.4/37.1，方向高度不确定（规则32改判客胜首选）。',
    '周四008': '桑德兰英超第20、联赛状态极差；欧联杯赛专注度待验证。',
    '周四009': '模型客胜37.1%与市场主胜45.7%方向相反，平33.1%最高，属高不确定场。',
    '周四010': 'HAD未开售；让球-2让胜仅25.7%，莱赫6人伤但为波甲榜首。',
    '周四011': '尤文8人伤+明确轮换，客胜42.4%<45%。',
    '周四012': '勒沃库森8人伤（锋线仅希克），模型56.8% vs 市场71.9%，分歧-15.1pp（>15pp红线），不作博胆。',
    '周四013': '里莫6+人缺阵但保级拼命；帕尔梅拉斯三线作战体能。',
}

TIER_NOTE = {
    '周四001': '2球23.9%＋3球22.4%＝46.3%为最高band；两端0-1球20.7%、6-7+球7.4%均未达35%，按L266/L270不预留。',
    '周四002': '2球24.8%＋3球22.2%＝47.0%为最高band；两端0-1球22.2%、6-7+球6.5%未达35%，不预留。',
    '周四003': '2球26.9%＋3球21.2%＝48.0%为最高band；0-1球28.8%<35%，不预留低端。',
    '周四004': '2球25.1%＋3球22.2%＝47.3%为最高band；0-1球23.0%<35%，不预留。',
    '周四005': '2球26.6%＋3球21.4%＝48.0%为最高band；0-1球27.8%<35%，不预留。',
    '周四006': '2球24.4%＋3球22.3%＝46.7%为最高band；0-1球22.0%<35%，不预留。',
    '周四007': '2球26.7%＋3球21.4%＝48.1%为最高band；0-1球27.7%<35%，不预留。',
    '周四008': '2球24.7%＋3球22.2%＝47.0%为最高band；0-1球22.7%<35%，不预留。',
    '周四009': '1球22.9%＋2球28.0%＝50.9%为最高band；闷战0-1球35.6%≥35%可作次选（L266），但不作首选。',
    '周四010': '2球23.7%＋3球22.4%＝46.1%为最高band；0-1球20.5%<35%，不预留。',
    '周四011': '2球25.5%＋3球22.0%＝47.5%为最高band；0-1球23.9%<35%，不预留。',
    '周四012': '2球25.4%＋3球22.0%＝47.4%为最高band；0-1球24.0%<35%，不预留。',
    '周四013': '2球23.7%＋3球22.4%＝46.1%为最高band；0-1球20.9%<35%，不预留。',
}

HC_CN = {'win': '胜', 'push': '平', 'lose': '负'}

out = []
for o in P:
    num = o['num']
    m = M[num]
    vh, va, uh, ua = VALUE[num]
    hc = o['handicap']
    crs = {k.replace('-', ':'): v for k, v in o['odds']['crs'].items()}
    hhad = o['odds']['hhad']
    out.append({
        'num': num, 'league': o['league'], 'home': o['home'], 'away': o['away'],
        'kickoff': m['time'], 'match_date': '2026-11-05（销售日）/ 001 11-05、其余 11-06 北京时间',
        'is_single': o['is_single'],
        'single_note': ('接口 bettingSingle=false 与用户投注端“002为单关”冲突；按 L273 以用户端为准并执行规则63上修' if o['is_single']
                        else '官方接口 bettingSingle=false，用户未赛前告知单关'),
        'single_match': o['single_match'],
        'confidence': CONF[num],
        'lambda': o['lambda'],
        'model': {k: v / 100 for k, v in o['probs'].items()},
        'market': ({k: (v / 100 if k != 'overround' else v) for k, v in o['market'].items()} if o['market'] else None),
        'handicap': {'line': hc['line'], 'win': hc['win'] / 100, 'push': hc['push'] / 100, 'lose': hc['lose'] / 100},
        'odds_had': o['odds']['had'],
        'odds_hhad': ({'handicap': hhad['handicap'], 'home': hhad['home'], 'draw': hhad['draw'], 'away': hhad['away']} if hhad else None),
        'odds_crs': crs, 'odds_ttg': o['odds']['ttg'], 'odds_hafu': o['odds']['hafu'],
        'value': {'home': vh, 'away': va, 'ratio': round(float(vh.replace('€', '').replace('M', '')) / float(va.replace('€', '').replace('M', '')), 2)},
        'value_source': {'home': uh, 'away': ua, 'provider': 'Transfermarkt（2026-11-05 采集）'},
        'stadium': STADIUM[num],
        'weather': '赛时预报未取到一手源（未验证），无极端天气预警',
        'injuries': {'home': INJ[num], 'source_level': '部分一手（官网/Fotmob）+中文二手（未验证）'},
        'recent': RECENT[num], 'h2h': H2H[num],
        'had': {'first': o['first'], 'second': o['second'], 'firstProb': o['firstProb'] / 100, 'secondProb': o['secondProb'] / 100},
        'hhad': {'first': HC_CN[hc['first']], 'second': HC_CN[hc['second']],
                 'firstProb': hc['firstProb'] / 100, 'secondProb': hc['secondProb'] / 100,
                 'structure_leg': HC_CN[hc['structure']], 'structureProb': hc['structureProb'] / 100,
                 'note': 'L268 结构腿不作首选/不作串关腿，单独记账留次选'},
        'ttg': {'tier': o['band'], 'tierNote': TIER_NOTE[num],
                'first': int(o['ttgTop2'][0][0]), 'second': int(o['ttgTop2'][1][0]),
                'firstProb': o['ttgTop2'][0][1] / 100, 'secondProb': o['ttgTop2'][1][1] / 100,
                'over25': o['over25'] / 100, 'under25': o['under25'] / 100,
                'bands': {k: v / 100 for k, v in o['bandSorted']}},
        'hafu': {'top3': [x[0] for x in o['hafuTop3']], 'top3Probs': [x[1] / 100 for x in o['hafuTop3']], 'quota': 'L267'},
        'scoreTop5': [{'score': s, 'prob': v / 100} for s, v in o['scoreTop5']],
        'htScoreTop3': [{'score': s, 'prob': v / 100} for s, v in o['htScoreTop3']],
        'k_dist': o['k_dist'], 'k_rec': o['k_rec'],
        'k_consistency': ('一致' if (o['k_rec']['k'] > 0 and o['first'] == 'home') or (o['k_rec']['k'] < 0 and o['first'] == 'away') or (o['k_rec']['k'] == 0 and o['first'] == 'draw') else '分布-方向分歧'),
        'marketDivergence_pp': o['divergence'],
        'override_reason': o.get('override_reason'),
        'risk': RISK[num],
        'actual': None, 'backtest': None,
    })

os.makedirs('memory/predictions/20261105_thursday', exist_ok=True)
json.dump(out, open('memory/predictions/20261105_thursday/prediction.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(out, open('reports/data/20261105_predictions_final.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved 2 files, matches=', len(out))
