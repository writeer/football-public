# -*- coding: utf-8 -*-
"""生成 2026-11-03 预测 JSON（memory/predictions + reports/data）"""
import json, io, os

model = json.load(io.open('reports/data/20261103_model_output.json', encoding='utf-8'))
raw = json.load(io.open('reports/data/20261103_matches.json', encoding='utf-8'))
raw_by_num = {m['num']: m for m in raw}

META = {
 '周二001': dict(kickoff='15:45', conf='★★', first='away', second='draw',
   tier='常规正常球(2-3球)', ttg_top2=['3球', '2球'],
   value_h='€7.38M', value_a='€14.35M',
   stadium='McDonald Jones Stadium（纽卡斯尔，正常）', weather='16-31℃ 阵雨概率80% 可能雷暴',
   inj_h='3人：肯尼迪（踝）、弗赖尔（十字韧带）、库珀（足）',
   inj_a='1人：蒯纪闻（中场）；外援齐整',
   top5=['1-1', '1-2', '0-2', '0-1', '0-3'], htft=['AA', 'DA', 'DD'],
   hc_first='lose', hc_second='push',
   note='喷气机亚冠3战0分、进4失15；海港争前8主力出战。让(+1)且客胜≥45%，让胜被排除，让负33.5%首选、让平21.6%次选。'),
 '周二002': dict(kickoff='18:00', conf='★★', first='home', second='away',
   tier='大球(4-5球)', ttg_top2=['3球', '4球'],
   value_h='€18.33M', value_a='€13.35M',
   stadium='三协F柏球场（千叶柏市，正常）', weather='13-20℃ 多云 无雨',
   inj_h='5人：手冢康平、马场晴也（十字韧带）、山田雄士（半月板）、大久保智明（跟腱）、熊坂光希（膝）',
   inj_a='1人：徐荣宰（踝）',
   top5=['2-1', '1-1', '3-1', '2-0', '3-0'], htft=['HH', 'DH', 'AA'],
   hc_first='win', hc_second='push',
   note='L258触发：主队5人长期伤停=残阵 → 方向次选必须客胜（不得给平）。让(-1)且主胜55.3%≥55%禁让负，让胜35.3%首选。'),
 '周二003': dict(kickoff='20:15', conf='★', first='away', second='draw',
   tier='常规正常球(2-3球)', ttg_top2=['3球', '2球'],
   value_h='€8.75M', value_a='€11.53M',
   stadium='True BG Stadium（巴吞他尼，正常）', weather='29℃ 晴 降雨<5%',
   inj_h='3人：卡卡·门德斯（膝）、阿斯纳维（跟腱术后）、马特乌斯·林斯（术后）',
   inj_a='5-7人：斯帕伊奇、法比奥（赛季报销）、吴少聪、何宇鹏、韩佳奇；塞尔吉尼奥/拉莫斯成疑',
   top5=['1-1', '1-2', '0-2', '0-1', '0-3'], htft=['AA', 'DA', 'DD'],
   hc_first='lose', hc_second='push',
   note='单关（用户赛前告知）：平局25.6%→27.6%（+8%，首选与平局差23.1pp≥20pp档）。国安残阵+长途飞行，方向次选给平；让(+1)且客胜≥45%，让负28.2%首选。'),
 '周二004': dict(kickoff='01:45', conf='★★', first='home', second='away',
   tier='大球(4-5球)', ttg_top2=['4球', '3球'],
   value_h='€381.5M', value_a='€399.45M',
   stadium='RAMS Park（伊斯坦布尔，正常）', weather='15.4℃ 小雨 风3km/h',
   inj_h='0人：奥斯梅恩、巴达克奇、托雷拉全可用',
   inj_a='3-5人：绍尔、斯蒂勒（核心中场）、瓦格诺曼；迪尔/扎加杜成疑',
   top5=['2-1', '1-1', '2-2', '1-2', '3-1'], htft=['HH', 'DH', 'DA'],
   hc_first='lose', hc_second='push',
   note='L258触发：斯图加特客场4-2勒沃库森、欧冠2胜1平 → 次选客胜。加拉主场对德球队9场不胜。'),
 '周二005': dict(kickoff='04:00', conf='★', first='away', second='home',
   tier='常规正常球(2-3球)', ttg_top2=['3球', '2球'],
   value_h='€703.5M', value_a='€1040M',
   stadium='大都会球场（马德里，正常）', weather='10-11℃ 无雨 风4km/h',
   inj_h='2-3人：卡多佐（大腿）、尤尔曼德（停赛）、科克成疑',
   inj_a='4-6人：路易斯·迪亚斯、格纳布里、穆西亚拉、赛巴里；诺伊尔/奥利塞成疑（大概率出战）',
   top5=['1-1', '1-2', '2-1', '2-2', '0-1'], htft=['AA', 'HH', 'DA'],
   hc_first='win', hc_second='push',
   note='单关（用户赛前告知）：平局26.0%→28.9%（+11%，差14.1pp落在10-20pp档）。客胜38.6%首选、主胜32.5%次选（高于平局28.9%）。拜仁锋线仅剩凯恩，主帅孔帕尼未随队。'),
 '周二006': dict(kickoff='04:00', conf='★★★', first='home', second='draw',
   tier='常规正常球(2-3球)', ttg_top2=['3球', '2球'],
   value_h='€62.4M', value_a='€38.17M',
   stadium='Raiffeisen Arena（林茨，正常）', weather='6.4℃ 无雨 风6km/h',
   inj_h='0人（贝洛肌肉伤成疑）', inj_a='0人（切雷普卡伊背伤成疑）',
   top5=['2-0', '2-1', '1-1', '3-0', '1-0'], htft=['HH', 'DH', 'AA'],
   hc_first='push', hc_second='win',
   note='客队看台关闭（Slovan球迷被禁1场），非空场。Slovan欧冠11连败0分，LASK上轮3-2客胜葡萄牙体育。'),
 '周二007': dict(kickoff='04:00', conf='★', first='away', second='draw',
   tier='小球(1-2球)', ttg_top2=['2球', '1球'],
   value_h='€245.23M', value_a='€738.3M',
   stadium='德奎普（鹿特丹，正常）', weather='7.6-8℃ 无雨 风15-20km/h',
   inj_h='5-8人：博斯、莫德、纽科普、斯马尔、圣贾斯特；纳尔逊/贝伦/S.范佩西',
   inj_a='5-7人：巴斯托尼（停赛）、劳塔罗（肌肉）、琼斯、斯通斯、帕瓦尔、普罗韦德尔',
   top5=['1-1', '0-1', '0-0', '1-2', '1-0'], htft=['AA', 'HH', 'DA'],
   hc_first='win', hc_second='push',
   note='重叠残阵（L029例外）：双方≥5人伤停，让球不套用“主胜≥55%禁让负”，按52a取让胜。'),
 '周二008': dict(kickoff='04:00', conf='★', first='home', second='away',
   tier='常规正常球(2-3球)', ttg_top2=['3球', '2球'],
   value_h='€928.8M', value_a='€498.4M',
   stadium='老特拉福德（曼彻斯特，正常）', weather='10℃ 无雨 风11-13km/h',
   inj_h='4-5人：多古、拉什福德（髋）、舍什科（胫）、肖（大腿）；迪亚洛成疑',
   inj_a='3-4人：斯维拉尔（主力门将）、科内、佩莱格里尼；迪巴拉成疑',
   top5=['1-1', '2-1', '1-2', '2-2', '1-0'], htft=['HH', 'AA', 'DH'],
   hc_first='lose', hc_second='push',
   note='L258触发：曼联近10场1胜3平6负、残阵 → 次选客胜。曼联主场对罗马4战全胜为唯一反向支撑。'),
 '周二009': dict(kickoff='04:00', conf='★★', first='home', second='away',
   tier='超大球(5-6球)', ttg_top2=['4球', '5球'],
   value_h='€1295.8M', value_a='€633.7M',
   stadium='诺坎普（巴塞罗那，正常）', weather='13.1℃ 小雨 风14km/h',
   inj_h='6人：克里斯滕森、埃里克·加西亚、埃斯帕特、孔德（踝）、奥尔莫、巴尔德吉',
   inj_a='2-3人：鲁杰里、万-比萨卡（大腿）、奥纳纳（十字韧带）',
   top5=['3-1', '2-1', '3-0', '4-1', '2-0'], htft=['HH', 'DH', 'AA'],
   hc_first='lose', hc_second='win',
   note='残阵降级→L260失效“残阵例外”启用：让球首选回模型最高腿 让(-2)负43.7%。维拉欧冠9分第2、3连胜。'),
 '周二010': dict(kickoff='04:00', conf='★★', first='away', second='home',
   tier='大球(4-5球)', ttg_top2=['3球', '4球'],
   value_h='€368.05M', value_a='€1360M',
   stadium='陶瓷球场（比利亚雷亚尔，正常）', weather='9℃ 无雨 风2km/h',
   inj_h='4人：阿霍马奇、萨利巴（肌肉）、福伊特、莫雷诺（队长，肌肉）',
   inj_a='4人：登贝莱、克瓦拉茨赫利亚（膝）、马尔基尼奥斯、努诺·门德斯',
   top5=['1-2', '1-1', '1-3', '2-2', '0-2'], htft=['AA', 'DA', 'HH'],
   hc_first='lose', hc_second='push',
   note='PSG四主力未随队但欧冠13场不败、9连胜；黄潜欧冠3战3分。方向客胜56.2%，次选主胜22.1%（略高于平局21.7%）。让(+1)且客胜≥45%，让负36.6%首选。'),
 '周二011': dict(kickoff='04:00', conf='★★', first='home', second='draw',
   tier='常规正常球(2-3球)', ttg_top2=['3球', '2球'],
   value_h='€79.2M', value_a='€253.3M',
   stadium='Aspmyra（博德，正常）', weather='8.7℃ 小雨 风40-42km/h（大风）',
   inj_h='4人：埃维延（膝）、法耶·伦德、里斯奈斯（膝）、米克尔森（腹股沟）',
   inj_a='5人：本塔莱布（病）、姆巴佩（停赛）、蒂亚戈·桑托斯（膝）、上田（脚）、伊加马内（十字韧带）',
   top5=['1-1', '2-1', '2-0', '1-0', '3-1'], htft=['HH', 'DH', 'AA'],
   hc_first='win', hc_second='push',
   note='里尔5人伤停+欧冠3连败0分；博德主场欧冠4连胜，但大风40km/h抑制进攻。L253：主胜56.5%≥55%禁让负→让胜首选。'),
}

TM = {
 '周二001': ('Newcastle Jets', 'Shanghai Port'),
 '周二002': ('Kashiwa Reysol', 'Daejeon Hana Citizen'),
 '周二003': ('Port FC', 'Beijing Guoan'),
 '周二004': ('Galatasaray', 'VfB Stuttgart'),
 '周二005': ('Atletico Madrid', 'Bayern Munich'),
 '周二006': ('LASK', 'Slovan Bratislava'),
 '周二007': ('Feyenoord', 'Inter Milan'),
 '周二008': ('Manchester United', 'AS Roma'),
 '周二009': ('FC Barcelona', 'Aston Villa'),
 '周二010': ('Villarreal', 'Paris Saint-Germain'),
 '周二011': ('Bodo/Glimt', 'Lille'),
}
TM_URL = 'https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query='

out = []
for num, m in model.items():
    meta = META[num]
    r = raw_by_num[num]
    crs_odds = {}
    for o in r.get('crs', []):
        crs_odds[o['key']] = o['odds']
    def crs_odd(score):
        for k in (score, score.replace('-', ':')):
            if k in crs_odds: return crs_odds[k]
        return None
    top5 = []
    for s in meta['top5']:
        p = next((x[1] for x in m['top_scores'] if x[0] == s), None)
        top5.append({'score': s, 'prob': round(p, 4) if p else 0.0, 'odds': crs_odd(s)})
    hafu = [{'pick': k, 'prob': round(m['htft'].get(k, 0), 4), 'odds': next((o['odds'] for o in r.get('hafu', []) if o['key'] == k), None)} for k in meta['htft']]
    hc_map = {'win': '让胜', 'push': '让平', 'lose': '让负'}
    rec = {
      'had_primary': meta['first'],
      'had_primary_prob': round(m['probs_final'][meta['first']], 4),
      'had_secondary': meta['second'],
      'had_secondary_prob': round(m['probs_final'][meta['second']], 4),
      'hc_line': m['handicap']['line'],
      'hc_primary': meta['hc_first'], 'hc_primary_label': hc_map[meta['hc_first']],
      'hc_primary_prob': round(m['handicap'][meta['hc_first']], 4),
      'hc_secondary': meta['hc_second'], 'hc_secondary_label': hc_map[meta['hc_second']],
      'hc_secondary_prob': round(m['handicap'][meta['hc_second']], 4),
      'cr_top5': top5,
      'hafu_top3': hafu,
      'ttg_top2': meta['ttg_top2'],
      'six_tier': meta['tier'],
      'ht_scores_top3': [{'score': s, 'prob': round(p, 4)} for s, p in m['ht_scores'][:3]],
      'k_dist': m['k_dist'], 'k_rec': m['k_rec'],
    }
    up = m['single']['uplift']
    if up:
        tier = '≥20pp' if up['gap_pp'] > 20 else ('10~20pp' if up['gap_pp'] > 10 else '≤10pp')
        single_match = {
          'is_single': True, 'source': '用户赛前告知',
          'gap_pp': up['gap_pp'], 'tier': tier, 'uplift': up['factor'],
          'draw_before': round(up['draw_after'] / up['factor'], 4),
          'draw_after': round(up['draw_after'], 4),
        }
    else:
        single_match = None
    item = {
      'num': num, 'league': r['league'], 'home': r['home'], 'away': r['away'],
      'kickoff': meta['kickoff'], 'match_date': r['match_date'],
      'is_single': m['single']['is_single'], 'single_note': m['single']['uplift'],
      'single_match': single_match,
      'confidence': meta['conf'],
      'lambda': {k: round(v, 2) for k, v in m['lambda'].items()},
      'model': {k: round(v, 4) for k, v in m['probs_final'].items()},
      'market': {k: round(v, 4) for k, v in m['market'].items()} if m['market'] else None,
      'handicap': {**{k: round(v, 4) for k, v in m['handicap'].items()}},
      'odds_had': {o['key']: o['odds'] for o in r.get('had', [])},
      'odds_hhad': {**{o['key']: o['odds'] for o in r.get('hhad', {}).get('outcomes', [])}, 'handicap': r.get('hhad', {}).get('goalLine')},
      'odds_crs': crs_odds, 'odds_ttg': {o['key']: o['odds'] for o in r.get('ttg', [])},
      'odds_hafu': {o['key']: o['odds'] for o in r.get('hafu', [])},
      'value': {'home': meta['value_h'], 'away': meta['value_a']},
      'value_source': {
        'home': TM_URL + TM[num][0].replace(' ', '+'),
        'away': TM_URL + TM[num][1].replace(' ', '+'),
        'provider': 'Transfermarkt（阵容页快照，2026-11-03 采集）',
      },
      'stadium': meta['stadium'], 'weather': meta['weather'],
      'injuries': {'home': meta['inj_h'], 'away': meta['inj_a']},
      'recommendation': rec,
      'note': meta['note'],
    }
    out.append(item)

os.makedirs('memory/predictions/20261103_tuesday', exist_ok=True)
for path in ['memory/predictions/20261103_tuesday/prediction.json', 'reports/data/20261103_predictions.json']:
    io.open(path, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('saved', len(out), 'matches')
for x in out:
    rc = x['recommendation']
    print(x['num'], x['confidence'], rc['had_primary'], rc['had_primary_prob'], '/', rc['had_secondary'], rc['had_secondary_prob'],
          '| 让', rc['hc_line'], rc['hc_primary_label'], rc['hc_primary_prob'], '/', rc['hc_secondary_label'], rc['hc_secondary_prob'],
          '|', rc['six_tier'], rc['ttg_top2'], '|', [c['score'] for c in rc['cr_top5']], '|', [h['pick'] for h in rc['hafu_top3']])
