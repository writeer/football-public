# -*- coding: utf-8 -*-
"""2026-11-01 周日 25 场：结算 6 维 + 26 个串关方案"""
import json, io

D = r'e:\VibeCoding\football\reports\data'
pred = {m['num']: m for m in json.load(io.open(D + r'\20261101_predictions.json', encoding='utf-8-sig'))}
res = {r['num']: r for r in json.load(io.open(D + r'\20261101_results_official.json', encoding='utf-8-sig'))}

HAFU = {('H', 'H'): '胜胜', ('H', 'D'): '胜平', ('H', 'A'): '胜负',
        ('D', 'H'): '平胜', ('D', 'D'): '平平', ('D', 'A'): '平负',
        ('A', 'H'): '负胜', ('A', 'D'): '负平', ('A', 'A'): '负负'}
DIR = {'home': '主胜', 'draw': '平', 'away': '客胜'}
HC = {'home': '让胜', 'draw': '让平', 'away': '让负'}


def rl(s):
    a, b = [int(x) for x in str(s).replace(':', '-').split('-')]
    return a, b


def code(h, a):
    return 'H' if h > a else ('D' if h == a else 'A')


def tier_hit(tier, total):
    m = {'闷战超小球(0-1球)': total <= 1, '小球(1-2球)': total in (1, 2),
         '常规正常球(2-3球)': total in (2, 3), '大球(4-5球)': total in (4, 5),
         '超大球(5-6球)': total in (5, 6), '穿盘可能(6-7+球)': total >= 6}
    return m.get(tier, False)


rows = []
for num in sorted(pred):
    p, s = pred[num], res.get(num)
    rec = p['recommendation']
    if not s or not s.get('ft'):
        rows.append({'num': num, 'league': p['league'], 'home': p['home'], 'away': p['away'],
                     'status': 'pending', 'conf': p['conf']})
        continue
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    total = h + a
    actual = 'home' if h > a else ('draw' if h == a else 'away')
    had = 'first' if rec['had_primary'] == actual else ('second' if rec['had_secondary'] == actual else 'miss')

    gl = rec.get('hc_line')
    adj = (h - a) + gl
    hh_res = 'home' if adj > 0 else ('draw' if adj == 0 else 'away')
    hc = 'first' if rec['hc_primary'] == hh_res else ('second' if rec['hc_secondary'] == hh_res else 'miss')

    ttg = 'hit' if total in rec['ttg_top2'] else 'miss'
    hafu_actual = HAFU[(code(hh, ha), code(h, a))]
    hafu_pick = [x[0] for x in rec['htft_top3']]
    hafu = 'hit' if hafu_actual in hafu_pick else 'miss'

    crs_pick = [x['score'] for x in rec['cr_top5']]
    crs_actual = '%d-%d' % (h, a)
    crs = 'hit' if crs_actual in crs_pick else 'miss'
    crs_rank = (crs_pick.index(crs_actual) + 1) if crs == 'hit' else None

    ht_pick = [x['score'] for x in rec['ht_score']]
    ht_actual = '%d-%d' % (hh, ha)
    ht_hit = 'hit' if ht_actual in ht_pick else 'miss'

    tier = 'hit' if tier_hit(rec['tier'], total) else 'miss'

    rows.append({
        'num': num, 'league': p['league'], 'home': p['home'], 'away': p['away'],
        'ft': s['ft'], 'ht': s['ht'], 'total': total,
        'pred_dir': rec['had_primary'], 'pred_dir2': rec['had_secondary'],
        'p_dir': (round(p['model']['home'] * 100, 1), round(p['model']['draw'] * 100, 1),
                  round(p['model']['away'] * 100, 1)),
        'actual_dir': actual, 'had': had,
        'hhad_line': gl, 'pred_hc': rec['hc_primary'], 'pred_hc2': rec['hc_secondary'],
        'actual_hc': hh_res, 'hc': hc,
        'ttg_top2': rec['ttg_top2'], 'ttg': ttg,
        'hafu_top3': hafu_pick, 'hafu_actual': hafu_actual, 'hafu': hafu,
        'crs_top5': crs_pick, 'crs_actual': crs_actual, 'crs': crs, 'crs_rank': crs_rank,
        'tier': rec['tier'], 'tier_hit': tier,
        'ht_top3': ht_pick, 'ht_actual': ht_actual, 'ht_hit': ht_hit,
        'lambda': (p['model']['lambda_home'], p['model']['lambda_away']),
        'conf': p['conf'], 'is_single': p.get('is_single', False),
        'k_dist': p['k_dist'], 'k_rec': p['k_rec'], 'k_consistent': p['k_consistent'],
        'kickoff': p['kickoff'],
    })

settled = [x for x in rows if x.get('status') != 'pending']
N = len(settled)


def stat(key, first_only=False):
    if first_only:
        n = sum(1 for x in settled if x.get(key) == 'first')
    else:
        n = sum(1 for x in settled if (x.get(key) in ('first', 'second', 'hit')))
    return n, N, n / N * 100


# ---- 串关（与 20261101 分析报告一一对应，26 个方案） ----
P = [
    ('方向串A（稳健）', '方向串', 2.31, [('007', 'had', 'home'), ('013', 'had', 'home'), ('003', 'had', 'home')]),
    ('方向串B（价值）', '方向串', 4.71, [('020', 'had', 'home'), ('012', 'had', 'home'), ('017', 'had', 'home')]),
    ('稳健让球串', '让球串', 2.19, [('018', 'hhad', 'home'), ('005', 'hhad', 'home')]),
    ('价值让球串', '让球串', 15.06, [('017', 'hhad', 'draw'), ('024', 'hhad', 'draw')]),
    ('方向+半全场A', '混合串', 2.43, [('003', 'had', 'home'), ('007', 'hafu', '胜胜')]),
    ('方向+半全场B', '混合串', 5.34, [('020', 'had', 'home'), ('012', 'hafu', '胜胜')]),
    ('连续编号混合串A', '混合串', 4.40, [('003', 'had', 'home'), ('004', 'hafu', '胜胜')]),
    ('连续编号混合串B', '混合串', 5.64, [('012', 'hafu', '胜胜'), ('013', 'hafu', '胜胜')]),
    ('总进球串A', '总进球串', 15.75, [('015', 'ttg', 4), ('025', 'ttg', 3)]),
    ('总进球串B', '总进球串', 16.38, [('011', 'ttg', 3), ('025', 'ttg', 4)]),
    ('连续编号总进球A', '总进球串', 11.05, [('003', 'ttg', 3), ('004', 'ttg', 2)]),
    ('连续编号总进球B', '总进球串', 12.77, [('013', 'ttg', 2), ('014', 'ttg', 3)]),
    ('半全场串A', '高赔半全场串', 4.44, [('015', 'hafu', '胜胜'), ('013', 'hafu', '胜胜')]),
    ('半全场串B', '高赔半全场串', 4.19, [('009', 'hafu', '负负'), ('010', 'hafu', '负负')]),
    ('连续编号半全场A', '高赔半全场串', 6.20, [('007', 'hafu', '胜胜'), ('008', 'hafu', '平平')]),
    ('连续编号半全场B', '高赔半全场串', 10.92, [('019', 'hafu', '胜胜'), ('020', 'hafu', '胜胜')]),
    ('半全场+总进球A', '半全场混合', 6.35, [('017', 'hafu', '胜胜'), ('018', 'ttg', 2)]),
    ('半全场+总进球B', '半全场混合', 18.75, [('021', 'hafu', '平平'), ('025', 'ttg', 3)]),
    ('连续编号混合A', '半全场混合', 10.22, [('023', 'hafu', '胜胜'), ('024', 'ttg', 2)]),
    ('连续编号混合B', '半全场混合', 16.31, [('024', 'hafu', '平平'), ('025', 'ttg', 3)]),
    ('比分串A（稳健）', '比分串', 47.45, [('007', 'crs', '2-0'), ('013', 'crs', '2-0')]),
    ('比分串B（搏冷）', '比分串', 52.50, [('020', 'crs', '2-1'), ('003', 'crs', '2-0')]),
    ('连续编号比分A', '比分串', 50.25, [('003', 'crs', '2-0'), ('004', 'crs', '1-0')]),
    ('连续编号比分B', '比分串', 48.75, [('012', 'crs', '2-1'), ('013', 'crs', '2-0')]),
    ('单挑比分①', '比分串', 48.91, [('007', 'crs', '2-0'), ('004', 'crs', '1-0')]),
    ('单挑比分②', '比分串', 38.25, [('008', 'crs', '1-1'), ('012', 'crs', '2-1')]),
]


def leg_ok(num, market, pick):
    s = res.get('周日' + num)
    if not s or not s.get('ft'):
        return None
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return ('home' if h > a else ('draw' if h == a else 'away')) == pick
    if market == 'hhad':
        adj = (h - a) + pred['周日' + num]['recommendation']['hc_line']
        return ('home' if adj > 0 else ('draw' if adj == 0 else 'away')) == pick
    if market == 'crs':
        return ('%d-%d' % (h, a)) == str(pick)
    if market == 'ttg':
        return (h + a) == int(pick)
    if market == 'hafu':
        return HAFU[(code(hh, ha), code(h, a))] == pick
    return None


def leg_text(num, market, pick):
    s = res.get('周日' + num)
    h, a = rl(s['ft'])
    hh, ha = rl(s['ht'])
    if market == 'had':
        return '%s %s(%s)' % (num, DIR[pick], s['ft'])
    if market == 'hhad':
        return '%s 让(%+d)%s(%s)' % (num, pred['周日' + num]['recommendation']['hc_line'], HC[pick], s['ft'])
    if market == 'ttg':
        return '%s %d球(实%d球)' % (num, pick, h + a)
    if market == 'hafu':
        return '%s %s(实%s)' % (num, pick, HAFU[(code(hh, ha), code(h, a))])
    if market == 'crs':
        return '%s %s(实%s)' % (num, pick, s['ft'])
    return num


hit = 0
stake = ret = 0.0
out_parlays = []
for name, cat, odds, legs in P:
    oks = [leg_ok(*lg) for lg in legs]
    pend = any(o is None for o in oks)
    allok = all(o is True for o in oks) and not pend
    stake += 1
    if allok:
        hit += 1
        ret += odds
    out_parlays.append({'name': name, 'cat': cat, 'odds': odds, 'hit': allok, 'pending': pend,
                        'legs': [{'match': lg[0], 'market': lg[1], 'pick': lg[2], 'ok': o}
                                 for lg, o in zip(legs, oks)],
                        'results': [leg_text(*lg) for lg in legs]})

json.dump({'rows': rows, 'parlays': out_parlays},
          io.open(D + r'\20261101_backtest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(rows, io.open(D + r'\20261101_backtest_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('=== 6维 ===')
print('方向 首选 %d/%d=%.1f%% 含次选 %d/%d=%.1f%%' % (*stat('had', True), *stat('had')))
print('让球 首选 %d/%d=%.1f%% 含次选 %d/%d=%.1f%%' % (*stat('hc', True), *stat('hc')))
print('总进球TOP2 %d/%d=%.1f%%' % stat('ttg'))
print('半全场TOP3 %d/%d=%.1f%%' % stat('hafu'))
print('比分TOP5 %d/%d=%.1f%%' % stat('crs'))
print('半场比分TOP3 %d/%d=%.1f%%' % stat('ht_hit'))
print('大小球六档 %d/%d=%.1f%%' % stat('tier_hit'))
print('进球分布', [x['total'] for x in settled], '场均%.2f' % (sum(x['total'] for x in settled) / N))
print('平局', sum(1 for x in settled if x['actual_dir'] == 'draw'), '大2.5', sum(1 for x in settled if x['total'] >= 3))
print('=== 串关 %d/%d 回收%.2f 投入%d ===' % (hit, len(out_parlays), ret, len(out_parlays)))
for q in out_parlays:
    print(('OK ' if q['hit'] else 'NG '), q['name'], q['odds'], '|', ' / '.join(
        '%s%s%s' % (lg['match'], lg['market'], 'V' if lg['ok'] else 'X') for lg in q['legs']))
print('=== 逐场 ===')
for x in settled:
    print(x['num'], x['ft'], 'HT', x['ht'], '| 方向', DIR[x['pred_dir']], DIR[x['pred_dir2']], '→', DIR[x['actual_dir']], x['had'],
          '| 让', x['hhad_line'], HC[x['pred_hc']], HC[x['pred_hc2']], '→', HC[x['actual_hc']], x['hc'],
          '| TTG', x['ttg_top2'], '实', x['total'], x['ttg'],
          '| HAFU', x['hafu_top3'], '实', x['hafu_actual'], x['hafu'],
          '| CRS', x['crs_top5'], '实', x['crs_actual'], x['crs'], x['crs_rank'],
          '| HT', x['ht_top3'], '实', x['ht_actual'], x['ht_hit'],
          '| 档', x['tier'], x['tier_hit'], '| conf', x['conf'])


# ---------------- 报告生成 ----------------
def rating(pct):
    if pct >= 100:
        return '完美'
    if pct >= 75:
        return '优秀'
    if pct >= 60:
        return '良好'
    if pct >= 45:
        return '一般'
    return '较差'


def num_only(s):
    return s.replace('周日', '')


tier_groups = {'★★★': [], '★★': [], '★': [], '☆': []}
for x in settled:
    tier_groups.setdefault(x['conf'], []).append(x)
tier_txt = []
for key in ['★★★', '★★', '★', '☆']:
    xs = tier_groups.get(key, [])
    if not xs:
        continue
    f = sum(1 for x in xs if x['had'] == 'first')
    c = sum(1 for x in xs if x['had'] in ('first', 'second'))
    tier_txt.append('%s（%d场）首选 %d/%d、含次选 %d/%d' % (key, len(xs), f, len(xs), c, len(xs)))

dir_miss = [num_only(x['num']) for x in settled if x['had'] == 'miss']
hc_miss = [num_only(x['num']) for x in settled if x['hc'] == 'miss']

NOTE = {
 '001': '首选主胜/次选平双错，客队两次反击带走比赛；但让(-1)让负首选、比分1-2第5位、半场0-1、总进球3球、档位常规全部命中——方向错在把主场优势当成硬实力。',
 '002': '首选主胜、总进球3球、比分2-1第2位、半场0-1、档位常规命中，让(-1)让平由次选兜住（净胜1）；唯半全场实际"负胜"（半场落后逆转）不在TOP3。',
 '003': '次选平、半全场平平、半场0-0命中；但0-0把总进球3/4球、常规档、比分TOP5（无0-0）与让(-1)让胜/让平一起打穿——本轮最大冷门，J1闷战被低估。',
 '004': '方向主胜/平双错（补时被绝杀），总进球2/3球与实际1球、比分TOP5无0-1、半全场无平负均未中；仅让(-1)让负次选、半场0-0命中。',
 '005': '首选主胜、让(+1)让胜、半全场胜胜命中；但4-0打穿总进球3/2球与常规档，比分TOP5（无4-0）、半场（0-0/1-0/0-1）全落空——澳超主场爆发被低估。',
 '006': '首选主胜、半全场胜胜、半场1-0命中，让(-1)让平次选兜住；总进球3/2球、档位常规与实际1球、比分TOP5无1-0，三项落空。',
 '007': '本轮唯一★★★，首选主胜、半全场胜胜、比分1-0第3位、半场1-0命中，让(-1)让平次选兜住；总进球3/2球与常规档被1球打穿——方向对、进球高估。',
 '008': '单关。方向平/客胜双错（主队半场落后3-1逆转），总进球2/3球、常规档、比分TOP5、半全场全错；仅让(+1)让胜首选、半场0-1命中——冷门判断站反了。',
 '009': '首选客胜、总进球3球、比分1-2第2位、半场1-0、档位常规命中，让(+1)让平次选命中（净负1）；唯半全场实际"胜负"（半场领先被翻）不在TOP3。',
 '010': '首选客胜、半全场负负命中；但0-9把总进球3/2球、常规档、比分TOP5（上限2-2）、半场（0-0/0-1/1-1）全部打穿——极端比分成倍低估，属尾部样本。',
 '011': '次选主胜兜住、让(+1)让胜首选、半场1-1命中；总进球3/4球与5球、比分TOP5（上限2-2）、半全场（实平胜）全错——挪超对攻被低估一球。',
 '012': '首选主胜、半全场平胜、比分2-0第4位、半场0-0、档位常规命中；总进球3/4球与实际2球偏高一球；让(-1)让平/让负双错（净胜2=让胜）。',
 '013': '首选主胜、总进球3球、半全场平胜、比分2-1第4位、档位常规命中，让(-1)让平次选命中（净胜1）；唯半场1-1不在TOP3。',
 '014': '首选平、让(+1)让胜、总进球2球、比分1-1第1位、半场1-0、档位常规命中；唯半全场实际"胜平"不在TOP3——六维中五，本轮最完整的一场。',
 '015': '方向主胜/平双错、让(-1)让平/让胜双错（实际让负）、半全场（实平负）、半场（实2-2）、比分TOP5全错；只有总进球4/5球（实5）与"穿盘"档命中——进球对、其余全崩。',
 '016': '☆最低星。方向平/客胜次选兜住、总进球2/1球（实1）、半全场负负、比分0-1第4位、半场0-1、让(+1)让平次选全中；仅常规档与1球不符——低星场反而最完整。',
 '017': '首选主胜、半全场平胜、比分3-1第4位、半场1-1命中；4球打穿总进球3/2球与常规档；让(-1)让负/让平双错（净胜2=让胜）——价值让球串这条腿断。',
 '018': '让(+1)让平次选、总进球3球、比分1-2第5位、档位常规命中；方向主胜/平双错、半全场（实负负）与半场（实1-2）未中。',
 '019': '方向主胜/平双错，总进球2/3球与实际1球、常规档、比分TOP5无0-1、半全场无平负全错；仅让(-1)让负首选与半场0-0命中。',
 '020': '首选主胜、让(-1)让平首选、总进球3球、比分2-1第2位、档位常规命中；半场0-1与半全场实际"负胜"未中——方向串B的关键腿兑现。',
 '021': '首选主胜、总进球2球、半全场平胜、半场0-0、档位常规命中；让(-1)让负/让平双错（净胜2=让胜）、比分TOP5无2-0。',
 '022': '首选主胜、半全场胜胜、比分2-0第4位、档位常规命中；总进球3/4球与实际2球、半场2-0不在TOP3；让(-1)让负/让平双错（净胜2=让胜）。',
 '023': '首选主胜、半全场胜胜、比分2-1第2位、总进球3球、档位常规命中，让(-1)让平次选命中（净胜1）；唯半场2-1不在TOP3——德比路径判断到位。',
 '024': '首选主胜、总进球2球、半全场胜胜、半场1-0、档位常规命中；让(-1)让负/让平双错（净胜2=让胜），比分TOP5无2-0——价值让球串另一条腿也断。',
 '025': '方向主胜/客胜次选兜住、总进球3球、比分1-2第4位、半场0-0、档位常规命中，让(+1)让平次选命中；唯半全场实际"平负"不在TOP3（给胜胜/负负/平胜）。',
}

L = []
A = L.append
A('# 【回测】2026-11-02（周一）11-01周日25场回测 | 方向含次选19/25、比分TOP5 14/25，串关仅2/26')
A('')
A('> **报告说明：** 本文为赛后**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。赛前**分析报告**（标题标注【分析】）提供方向/比分/总进球等预测推荐。历史报告可去主页查找。')
A('')
A('> **风险提示：** 回测结果仅供参考，历史命中不代表未来表现。赔率数据以采集时为准。**理性看待预测，切勿沉迷赌博。**')
A('')
A('> **⚠️ 免责声明：** 本文所有回测数据、命中率统计、教训分析仅供学习交流参考，不构成任何投注建议。回测结果具有时效性，历史命中不代表未来表现。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
A('')
A('*每日更新，关注主页获取最新赛事分析*')
A('')
A('11-01 共 25 场（001-025，008-016 九场单关），全部已结算。**方向首选 15/25=60.0%、含次选 19/25=76.0%**；**让球首选只有 7/25=28.0%**，含次选 17/25=68.0%；**比分TOP5 14/25=56.0%** 是近期最好的一轮。串关 **2/26=7.7%、回收 14.93/投入 26、ROI -42.6%**，娱乐组仅 1/18。')
A('')
A('## 总览')
A('')
A('| 编号 | 对阵 | 赛事 | 预测方向(首选/次选) | 实际方向 | 命中 | 让球 | 让球命中 | 总进球 | 进球命中 | 半全场 | 半全场命中 | 比分TOP5命中 |')
A('|:---:|:---|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
mk = {'first': '✅首', 'second': '✅次', 'miss': '❌'}
for x in settled:
    hafu_cell = x['hafu_top3'][0] + '(实际' + x['hafu_actual'] + ')/' + '/'.join(x['hafu_top3'][1:])
    cells = [
        num_only(x['num']),
        '%s vs %s' % (x['home'], x['away']),
        x['league'],
        '%s/%s' % (DIR[x['pred_dir']], DIR[x['pred_dir2']]),
        DIR[x['actual_dir']],
        mk[x['had']],
        '让(%+d)%s/%s' % (x['hhad_line'], HC[x['pred_hc']], HC[x['pred_hc2']]),
        mk[x['hc']],
        '%d球(实%s)' % (x['ttg_top2'][0], x['ft']),
        '✅' if x['ttg'] == 'hit' else '❌',
        hafu_cell,
        '✅' if x['hafu'] == 'hit' else '❌',
        ('✅第%d位' % x['crs_rank']) if x['crs'] == 'hit' else '❌',
    ]
    A('| ' + ' | '.join(cells) + ' |')
A('')
A('> 命中汇总：方向首选 15/25=60.0%｜含次选 19/25=76.0%｜让球首选 7/25=28.0%｜含次选 17/25=68.0%｜总进球TOP2 13/25=52.0%｜半全场TOP3 13/25=52.0%｜比分TOP5 14/25=56.0%｜半场比分TOP3 17/25=68.0%｜大小球档位 13/25=52.0%。')
A('')
A('## 逐场回测')

for x in settled:
    p = pred[x['num']]
    A('### %s %s vs %s（%s）' % (num_only(x['num']), x['home'], x['away'], x['league']))
    A('')
    t = x['kickoff'][:5]
    d = '11-01 ' if int(num_only(x['num'])) <= 15 else '11-02 '
    A('⏰ %s%s ｜ 🏟 %s ｜ **%s**' % (d, t, p['venue']['name'], x['ft']))
    A('')
    A('**赛果：** 半场%s → 全场%s ｜ 总进球%d ｜ %s' % (x['ht'], x['ft'], x['total'], DIR[x['actual_dir']]))
    A('')
    A('| 维度 | 预测 | 实际 | 命中 |')
    A('|:---|:---|:---|:---:|')
    mk2 = {'first': '✅首中', 'second': '✅次中', 'miss': '❌'}
    A('| **方向** | %s / %s | %s | %s |' % (DIR[x['pred_dir']], DIR[x['pred_dir2']], DIR[x['actual_dir']], mk2[x['had']]))
    A('| **让球** | 让(%+d)%s / 让(%+d)%s | 让(%+d)%s | %s |' % (
        x['hhad_line'], HC[x['pred_hc']], x['hhad_line'], HC[x['pred_hc2']],
        x['hhad_line'], HC[x['actual_hc']], mk2[x['hc']]))
    A('| **总进球TOP2** | **%d球** / **%d球** | %d球 | %s |' % (
        x['ttg_top2'][0], x['ttg_top2'][1], x['total'], '✅' if x['ttg'] == 'hit' else '❌'))
    A('| **半全场TOP3** | %s（实际:%s） | %s | %s |' % (
        ' > '.join(x['hafu_top3']), x['hafu_actual'], x['hafu_actual'], '✅' if x['hafu'] == 'hit' else '❌'))
    A('| **比分TOP5** | %s | **%s** | %s |' % (
        ' > '.join(x['crs_top5']), x['crs_actual'],
        ('✅（第%d位）' % x['crs_rank']) if x['crs'] == 'hit' else '❌'))
    A('| **半场比分TOP3** | %s | %s | %s |' % (
        ' > '.join(x['ht_top3']), x['ht_actual'], '✅' if x['ht_hit'] == 'hit' else '❌'))
    A('| **大小球档位** | %s | %d球 | %s |' % (x['tier'], x['total'], '✅' if x['tier_hit'] == 'hit' else '❌'))
    A('')
    A('> %s' % NOTE.get(num_only(x['num']), ''))
    A('')

A('## 命中率统计')
A('')
A('| 维度 | 命中/总场 | 命中率 | 评级 |')
A('|:---|:---:|:---:|:---:|')
for label, key, first_only in [('方向(首选+次选)', 'had', False), ('方向(仅首选)', 'had', True),
                               ('让球(首选+次选)', 'hc', False), ('让球(仅首选)', 'hc', True),
                               ('总进球TOP2', 'ttg', False), ('半全场TOP3', 'hafu', False),
                               ('比分TOP5', 'crs', False), ('半场比分TOP3', 'ht_hit', False),
                               ('大小球档位', 'tier_hit', False)]:
    n2, d2, pr = stat(key, first_only)
    A('| **%s** | %d/%d | %.1f%% | %s |' % (label, n2, d2, pr, rating(pr)))
A('')
A('> 方向命中明细：首选 %d 场 + 次选 %d 场 = %d 场命中，未中 %d 场（%s）。' % (
    sum(1 for x in settled if x['had'] == 'first'), sum(1 for x in settled if x['had'] == 'second'),
    sum(1 for x in settled if x['had'] in ('first', 'second')), len(dir_miss), '、'.join(dir_miss)))
A('')
A('> 让球命中明细：首选 %d 场 + 次选 %d 场 = %d 场命中，未中 %d 场（%s）；其中**让球仅首选命中 %d 场（%.1f%%）**。' % (
    sum(1 for x in settled if x['hc'] == 'first'), sum(1 for x in settled if x['hc'] == 'second'),
    sum(1 for x in settled if x['hc'] in ('first', 'second')), len(hc_miss), '、'.join(hc_miss),
    sum(1 for x in settled if x['hc'] == 'first'), stat('hc', True)[2]))
A('')
A('**实际进球分布：** %s ｜ 场均 %.2f 球 ｜ 大2.5 %d/%d ｜ 平局 %d/%d' % (
    '、'.join('%d球×%d场' % (t2, sum(1 for x in settled if x['total'] == t2))
             for t2 in sorted(set(x['total'] for x in settled))),
    sum(x['total'] for x in settled) / N,
    sum(1 for x in settled if x['total'] >= 3), N,
    sum(1 for x in settled if x['actual_dir'] == 'draw'), N))
A('')
A('**按置信度分层：** %s —— 星级与方向命中本轮基本同向，唯一例外是 ☆ 的 016 靠次选兜住。' % ' ｜ '.join(tier_txt))
A('')
A('## 串关回测')
A('')
A('| 方案 | 类型 | 场次 | 各场结果 | 串关命中 | 估算赔率 |')
A('|:---|:---|:---|:---|:---:|:---:|')


def pick_cn(market, pick):
    if market == 'had':
        return DIR[pick]
    if market == 'hhad':
        return HC[pick]
    if market == 'ttg':
        return '%d球' % int(pick)
    return str(pick)


for q in out_parlays:
    marks = []
    for lg, rs in zip(q['legs'], q['results']):
        mark = '✅' if lg['ok'] is True else ('⏳' if lg['ok'] is None else '❌')
        marks.append('%s %s' % (rs, mark))
    tag = '✅中' if q['hit'] else ('⏳待' if q['pending'] else '❌')
    A('| %s | %s | %s | %s | %s | ~%.2f |' % (
        q['name'], q['cat'], ' + '.join(lg['match'] for lg in q['legs']), ' ｜ '.join(marks), tag, q['odds']))
A('')
robust = [q for q in out_parlays if q['cat'] in ('方向串', '让球串', '混合串')]
fun = [q for q in out_parlays if q['cat'] not in ('方向串', '让球串', '混合串')]
A('> 串关 **%d/%d=%.1f%%**（回收 %.2f / 投入 %d，ROI **%+.1f%%**）：稳健组（方向串/让球串/混合串）%d/%d=%.1f%%，娱乐组（总进球串/高赔半全场串/半全场混合/比分串）%d/%d=%.1f%%。' % (
    hit, len(out_parlays), hit / len(out_parlays) * 100, ret, len(out_parlays),
    (ret - len(out_parlays)) / len(out_parlays) * 100,
    sum(1 for q in robust if q['hit']), len(robust), sum(1 for q in robust if q['hit']) / len(robust) * 100,
    sum(1 for q in fun if q['hit']), len(fun), sum(1 for q in fun if q['hit']) / len(fun) * 100))
A('')
A('> 唯二命中是**方向串B**（020主胜+012主胜+017主胜，4.71）与**连续编号混合A**（023胜胜+024 2球，10.22）；两者共同点是"模型与市场同向的主胜腿 + 低赔半全场/总进球腿"。6 个比分串/单挑再次全灭，方向串A 被 003 的 0-0 一腿打穿，稳健让球串被 018 的 1-2 打穿。')
A('')
A('## 关键发现')
A('')
A('**1. 方向 60.0%/76.0%，但 6 场未中里有 5 场押主胜。** 001/004/015/018/019 的首选全是主胜、结果全输，且这 5 场的次选清一色是平，**没有一场把客胜放进双选**；008 则是平/客胜双选站到了主队 3-1 逆转的反面。主胜偏好本轮付出了 5 场的代价。')
A('')
A('**2. 让球首选 28.0% 再创新低，但含次选 68.0% 说明"次选兜底"有效。** 让(-1)且首选"让负"的 5 场（012/017/021/022/024）全部打成让胜（净胜≥2），同为让(-1)的 003 也因 0-0 打成让负——**"-1盘押让负"的惯性是可直接修的结构性偏差**，不是随机误差。')
A('')
A('**3. 总进球 52.0%：中位惯性同时错过两端。** 0-1 球的 6 场里 5 场预测≥2 球（003/004/006/007/019）；≥4 球的 6 场里 5 场预测≤4 球（005/008/010/011/017），其中 010 的 0-9 是极端尾部。预测几乎全部挤在 2-4 球，两端各留一场覆盖的规则仍未落地。')
A('')
A('**4. 比分 TOP5 56.0% 是近期最佳，但首位精度仍差。** 14 场命中里 13 场落在第 2-5 位，只有 014 的 1-1 是 TOP1；落空的 11 场集中在闷平、一球小胜与两球完胜（003的0-0、004/019的0-1、006的1-0、021/024的2-0）。**覆盖面在改善，但"零封/闷平/两球完胜"这三格依旧靠后。**')
A('')
A('**5. 半全场 52.0%：缺的不是概率，是路径。** 12 场未中里，002/008/020的负胜、009的胜负、011的平胜、004/019/025的平负、014的胜平，都是"半场与全场不同向"的路径；TOP3 仍按概率贴着首选方向排，缺少"逆转/被翻"覆盖位——与 10-31 的 L250 是同一个未修复的问题。')
A('')
A('**6. 串关 2/26，娱乐组 1/18。** 稳健组 1/8 靠方向串B；娱乐组只有连续编号混合A（023胜胜+024 2球）命中。比分串 6 个全灭、总进球串 4 个全灭，与 10-31 的结论一致：**高赔组合在 25 场样本里没有可投性。**')
A('')
A('## 待改进')
A('')
A('- **让(-1)首选禁令**：模型主胜≥55% 且让(-1)时，首选禁止"让负"，只能在"让胜/让平"中选；本轮该规则可救回 5 场（012/017/021/022/024）。')
A('- **主胜首选的双选结构**：主胜为首选但对手客场状态不差时，次选优先给客胜而非平局；本轮 001/004/015/018/019 的次选全是平，若改客胜可直接多中 3-5 场。')
A('- **进球两端强制覆盖**：λ总和<2.3 的场次 TOP2 必含 1 球；λ总和>3.5 的场次 TOP2 必含 4 球；全天再各留一场 0-1 球与 ≥5 球的尾部覆盖。')
A('- **半全场补逆转路径**：半场首选领先时，TOP3 必须含"胜负"或"平负"；半场落后但全场首选主胜时，必须含"负胜"。')
A('- **串关继续收缩**：比分串/单挑暂停；总进球串只在两腿都是 TOP1 时保留；稳健组只保留"模型-市场同向"的方向腿，避免 003 这类冷门一腿拖死整串。')
A('')
A('## ☕ 写在最后')
A('')
A('全部方案免费分享。如觉有用，赏杯咖啡。')
A('')
A('赢了庆祝，没赢别急，早晚的事。')
A('')
A('感谢阅读。')
A('')

out = '\n'.join(L)
import os
os.makedirs(r'e:\VibeCoding\football\reports\backtest', exist_ok=True)
io.open(r'e:\VibeCoding\football\reports\backtest\backtest_20261101_sunday_zhihu.md', 'w', encoding='utf-8').write(out)
print('saved report chars', len(out))
