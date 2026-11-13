# -*- coding: utf-8 -*-
"""
AGENTS.md 第9步：回测与教训管理
输入：pred_20260913.json（第7步导出的预测）+ 实际赛果
输出：
  reports/backtest/20260913_sunday_backtest_zhihu.md
  memory/backtests/20260913_sunday/backtest_20260913_sunday.json
  memory/lessons/20260913_sunday_lessons.json
"""
import json, io, os, re, sys, random

WORK = r'c:\Users\admin\.trae-cn\work\6aa6133bd5a40399cae8e4e5'
ROOT = r'e:\VibeCoding\football'
sys.path.insert(0, WORK)

P = json.load(open(os.path.join(WORK, 'pred_20260913.json'), encoding='utf-8'))
ANALYSIS = os.path.join(ROOT, r'reports\analysis\20260913_sunday_analysis_zhihu.md')
OUT_MD = os.path.join(ROOT, r'reports\backtest\20260913_sunday_backtest_zhihu.md')
OUT_JSON = os.path.join(ROOT, r'memory\backtests\20260913_sunday\backtest_20260913_sunday.json')
OUT_LESSON = os.path.join(ROOT, r'memory\lessons\20260913_sunday_lessons.json')

# 实际赛果：(半场, 全场)
RESULTS = {
    '周日001': ('0-0', '1-1'), '周日002': ('1-1', '1-1'), '周日003': ('1-0', '1-1'),
    '周日004': ('2-1', '3-1'), '周日005': ('0-0', '0-0'), '周日006': ('0-0', '0-0'),
    '周日007': ('3-1', '3-2'), '周日008': ('1-0', '2-0'), '周日009': ('2-0', '5-0'),
    '周日010': ('0-2', '2-4'), '周日011': ('0-1', '1-5'), '周日012': ('2-1', '2-2'),
    '周日013': ('0-0', '0-1'), '周日014': ('0-1', '1-2'), '周日015': ('0-0', '1-0'),
    '周日016': ('0-0', '1-1'), '周日017': ('1-1', '3-1'), '周日018': ('2-1', '4-1'),
    '周日019': ('0-0', '3-2'), '周日020': ('0-1', '0-1'), '周日021': ('0-0', '0-3'),
    '周日022': ('0-0', '1-1'), '周日023': ('0-0', '2-1'), '周日024': ('0-1', '1-2'),
}
L3 = ['主胜', '平局', '客胜']
HAFU_LAB = ['胜胜', '胜平', '胜负', '平胜', '平平', '平负', '负胜', '负平', '负负']


def pf(x, d=1):
    return f'{x*100:.{d}f}%'


def parse(sc):
    a, b = sc.split('-')
    return int(a), int(b)


def direction(h, a):
    return '主胜' if h > a else ('平局' if h == a else '客胜')


def hafu(ht, ft):
    hh, ha = parse(ht)
    fh, fa = parse(ft)
    i = 0 if hh > ha else (1 if hh == ha else 2)
    j = 0 if fh > fa else (1 if fh == fa else 2)
    return HAFU_LAB[i * 3 + j]


def hhad_result(ht, ft, line):
    h, a = parse(ft)
    adj = (h - a) + line
    return '让胜' if adj > 0 else ('让平' if adj == 0 else '让负')


# ---------- 逐场判定 ----------
rows = []
for m in P['matches']:
    num = m['num']
    ht, ft = RESULTS[num]
    h, a = parse(ft)
    res_dir = direction(h, a)
    res_hafu = hafu(ht, ft)
    res_total = h + a
    res_score = ft
    line = m['hhad_line']
    res_hhad = hhad_result(ht, ft, line) if line is not None else None

    d_hit = '✅首' if res_dir == m['dir_first'] else ('✅次' if res_dir == m['dir_second'] else '❌')
    if line is not None and m['hhad_first']:
        h_hit = ('✅首' if res_hhad == m['hhad_first']
                 else ('✅次' if res_hhad == m['hhad_second'] else '❌'))
    else:
        h_hit = '—'
    t_hit = '✅' if res_total in [x[0] for x in m['ttg_top2']] else '❌'
    f_hit = '✅' if res_hafu in [x[0] for x in m['hafu_top3']] else '❌'
    s_hit = '✅' if res_score in [x[0] for x in m['scores_top5']] else '❌'

    rows.append(dict(num=num, home=m['home'], away=m['away'], league=m['league'],
                     time=m['time'], venue=m['venue'], ht=ht, ft=ft,
                     dir_first=m['dir_first'], dir_second=m['dir_second'], res_dir=res_dir, d_hit=d_hit,
                     hhad_line=line, hhad_first=m['hhad_first'], hhad_second=m['hhad_second'],
                     res_hhad=res_hhad, h_hit=h_hit,
                     ttg_top2=m['ttg_top2'], res_total=res_total, t_hit=t_hit,
                     hafu_top3=m['hafu_top3'], res_hafu=res_hafu, f_hit=f_hit,
                     scores_top5=m['scores_top5'], res_score=res_score, s_hit=s_hit,
                     fus=m['fus'], stars=m['stars']))

# ---------- 解析分析报告的串关方案 ----------
PARLAY = []
TYPE_OF_SEC = {}
cur_sec = None
for line in io.open(ANALYSIS, encoding='utf-8'):
    s = line.strip()
    if s.startswith('### 方向串'):
        cur_sec = '方向串'
    elif s.startswith('### 让球串'):
        cur_sec = '让球串'
    elif s.startswith('### 混合串'):
        cur_sec = '混合串'
    elif s.startswith('#### 高赔总进球串'):
        cur_sec = '总进球串'
    elif s.startswith('#### 高赔半全场串'):
        cur_sec = '高赔半全场串'
    elif s.startswith('#### 半全场混合总进球串'):
        cur_sec = '半全场混合'
    elif s.startswith('#### 比分串'):
        cur_sec = '比分串'
    elif s.startswith('|') and '@' in s and re.search(r'\|\s*\d{3}', s):
        cells = [c.strip() for c in s.strip().strip('|').split('|')]
        name = cells[0]
        cell = next((c for c in cells[1:] if '@' in c and re.search(r'\d{3}', c)), None)
        if not cell:
            continue
        PARLAY.append(dict(name=name, type=cur_sec, raw=cell, section=cur_sec, line=s))

# 单挑比分（不含 @）
for line in io.open(ANALYSIS, encoding='utf-8'):
    s = line.strip()
    if s.startswith('| 单挑比分') and 'vs' in s:
        cells = [c.strip() for c in s.strip().strip('|').split('|')]
        cell = next((c for c in cells[1:] if 'vs' in c and re.search(r'\d{3}', c)), None)
        if cell:
            PARLAY.append(dict(name=cells[0], type='比分串', raw=cell, section='比分串', line=s))


def judge_item(num, txt):
    """判定单个串关场次项是否命中"""
    r = next(x for x in rows if x['num'] == num)
    # 让球
    mm = re.search(r'让\(([+-]?\d+(?:\.\d+)?)\)(让胜|让平|让负)', txt)
    if mm:
        line = float(mm.group(1))
        want = mm.group(2)
        return hhad_result(r['ht'], r['ft'], line) == want, f"让({line:g}){want}"
    # 比分
    mm = re.search(r'(\d+-\d+)@', txt)
    if mm:
        return r['res_score'] == mm.group(1), mm.group(1)
    # 半全场
    mm = re.search(r'(胜胜|胜平|胜负|平胜|平平|平负|负胜|负平|负负)@', txt)
    if mm:
        return r['res_hafu'] == mm.group(1), mm.group(1)
    # 总进球
    mm = re.search(r'(\d+)球\+?@', txt)
    if mm:
        return r['res_total'] == int(mm.group(1)), f"{mm.group(1)}球"
    # 方向
    mm = re.search(r'(主胜|客胜|平局)@', txt)
    if mm:
        return r['res_dir'] == mm.group(1), mm.group(1)
    # 单挑比分（无 @）
    mm = re.search(r'(\d+-\d+)\s*$', txt)
    if mm:
        return r['res_score'] == mm.group(1), mm.group(1)
    return False, txt


for pl in PARLAY:
    det, hits = [], []
    for seg in re.split(r'\s+\+\s+', pl['raw']):
        m3 = re.search(r'(\d{3})', seg)
        if not m3:
            continue
        n3 = '周日' + m3.group(1)
        if n3 not in RESULTS:
            continue
        ok, want = judge_item(n3, seg)
        hits.append(ok)
        det.append(f"{m3.group(1)} {want}{'✅' if ok else '❌'}")
    pl['detail'] = det
    pl['hit'] = bool(hits) and all(hits)
    pl['n_legs'] = len(hits)
    parts = [c.strip() for c in pl.get('line', '').strip().strip('|').split('|')]
    odd_txt = parts[-2] if len(parts) >= 2 else ''
    mm2 = re.search(r'([\d.]+)', odd_txt)
    pl['odds'] = float(mm2.group(1)) if mm2 else None

# ---------- 命中率统计 ----------
N = len(rows)
n_dir_all = sum(1 for r in rows if r['d_hit'] in ('✅首', '✅次'))
n_dir_first = sum(1 for r in rows if r['d_hit'] == '✅首')
n_dir_second = sum(1 for r in rows if r['d_hit'] == '✅次')
hhad_rows = [r for r in rows if r['h_hit'] != '—']
n_hhad_all = sum(1 for r in hhad_rows if r['h_hit'] in ('✅首', '✅次'))
n_hhad_first = sum(1 for r in hhad_rows if r['h_hit'] == '✅首')
n_ttg = sum(1 for r in rows if r['t_hit'] == '✅')
n_hafu = sum(1 for r in rows if r['f_hit'] == '✅')
n_score = sum(1 for r in rows if r['s_hit'] == '✅')
n_parlay = sum(1 for p in PARLAY if p['hit'])


def grade(x, n):
    """评级标准（templates/zhihu_backtest_template.md【评级标准】）：
    100%→完美 / 75-99%→优秀 / 60-74%→良好 / 45-59%→一般 / <45%→较差"""
    v = x / n if n else 0
    return ('完美' if v >= 1.0 else '优秀' if v >= 0.75 else '良好' if v >= 0.60
            else '一般' if v >= 0.45 else '较差')


def pc(x, n):
    return f'{x/n*100:.1f}%' if n else '—'


print('=== 命中率 ===')
print('方向(首+次)', n_dir_all, '/', N, pc(n_dir_all, N))
print('方向(仅首选)', n_dir_first, '/', N, pc(n_dir_first, N))
print('让球(首+次)', n_hhad_all, '/', len(hhad_rows), pc(n_hhad_all, len(hhad_rows)))
print('总进球TOP2', n_ttg, '/', N, pc(n_ttg, N))
print('半全场TOP3', n_hafu, '/', N, pc(n_hafu, N))
print('比分TOP5', n_score, '/', N, pc(n_score, N))
print('串关', n_parlay, '/', len(PARLAY), pc(n_parlay, len(PARLAY)))
print()
print('=== 方向未中 ===')
for r in rows:
    if r['d_hit'] == '❌':
        print(r['num'], r['home'], 'vs', r['away'], '预测', r['dir_first'], '/', r['dir_second'],
              '实际', r['res_dir'], r['ft'])
print()
print('=== 串关 ===')
for p in PARLAY:
    print(('[✅]' if p['hit'] else '[❌]'), p['type'], p['name'], '|', ' + '.join(p['detail']))

json.dump(dict(rows=rows, parlays=PARLAY,
               stats=dict(N=N, dir_all=(n_dir_all, N), dir_first=(n_dir_first, N),
                          dir_second=(n_dir_second, N), hhad_all=(n_hhad_all, len(hhad_rows)),
                          hhad_first=(n_hhad_first, len(hhad_rows)), ttg=(n_ttg, N),
                          hafu=(n_hafu, N), score=(n_score, N),
                          parlay=(n_parlay, len(PARLAY)))),
          open(os.path.join(WORK, 'bt_calc.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ==================== 生成回测报告 MD ====================
ttg_miss = [r for r in rows if r['t_hit'] == '❌']
score_miss = [r for r in rows if r['s_hit'] == '❌']
hafu_miss = [r for r in rows if r['f_hit'] == '❌']
draws = [r for r in rows if r['res_dir'] == '平局']
draw_cover = [r for r in draws if r['d_hit'] != '❌']
parlay_hit = [p for p in PARLAY if p['hit']]
parlay_by_type = {}
for p in PARLAY:
    t = p['type'] or '其他'
    parlay_by_type.setdefault(t, [0, 0])
    parlay_by_type[t][1] += 1
    if p['hit']:
        parlay_by_type[t][0] += 1

o = []
o.append('# 【回测】2026年9月13日（周日）体彩24场回测报告 | 方向命中87.5%，总进球TOP2仅29.2%成最大短板')
o.append('')
o.append('> **报告说明：** 本文为赛后**回测报告**（标题标注【回测】），对比预测与实际结果并统计命中率。'
         '赛前**分析报告**（标题标注【分析】）提供方向/比分/总进球等预测推荐。历史报告可去主页查找。')
o.append('')
o.append('> **风险提示：** 回测结果仅供参考，历史命中不代表未来表现。赔率数据以采集时为准。**理性看待预测，切勿沉迷赌博。**')
o.append('')
o.append('> **⚠️ 免责声明：** 本文所有回测数据、命中率统计、教训分析仅供学习交流参考，不构成任何投注建议。'
         '回测结果具有时效性，历史命中不代表未来表现。内容仅供参考，如有错漏请谅解。请遵守当地法律法规，理性购彩，量力而行。')
o.append('')
o.append('*每日更新，关注主页获取最新赛事分析*')
o.append('')
o.append(f'本轮24场覆盖14个联赛，**方向（首选+次选）命中 {n_dir_all}/24 = {pc(n_dir_all, N)}**、'
         f'**让球（首选+次选）命中 {n_hhad_all}/24 = {pc(n_hhad_all, len(hhad_rows))}**、'
         f'**半全场TOP3命中 {n_hafu}/24 = {pc(n_hafu, N)}**，三项表现优秀；'
         f'但**总进球TOP2仅 {n_ttg}/24 = {pc(n_ttg, N)}**、比分TOP5 {n_score}/24 = {pc(n_score, N)}，'
         f'是最大失分项——24场中{len(ttg_miss)}场总进球预测落在TOP2之外。'
         f'最大亮点是**8场平局中有{len(draw_cover)}场被次选覆盖**（L096「次选必含平局」得到验证）；'
         f'最大翻车是019萨索洛3-2尤文图斯（预测客胜61.1%，实际主胜）。')
o.append('')
o.append('## 总览')
o.append('')
o.append('| 编号 | 对阵 | 赛事 | 预测方向(首选/次选) | 实际方向 | 命中 | 让球 | 让球命中 | 总进球 | 进球命中 | 半全场 | 半全场命中 | 比分TOP5命中 |')
o.append('|:---:|:---|:---|:---|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|')
for r in rows:
    o.append(f"| {r['num'].replace('周日','')} | {r['home']}vs{r['away']} | {r['league']} | "
             f"{r['dir_first']}/{r['dir_second']} | {r['res_dir']} | {r['d_hit']} | "
             f"{('让(%+.0f)%s/让(%+.0f)%s' % (r['hhad_line'], r['hhad_first'], r['hhad_line'], r['hhad_second'])) if r['hhad_line'] is not None else '—'} | "
             f"{r['h_hit']} | {r['ttg_top2'][0][0]}/{r['ttg_top2'][1][0]} (实际{r['res_total']}球 {r['ft']}) | {r['t_hit']} | "
              f"{'/'.join(h for h, _ in r['hafu_top3'])}(实际{r['res_hafu']}) | {r['f_hit']} | {r['s_hit']} |")
o.append('')
o.append(f'> 方向(首选+次选) {n_dir_all}/24 = {pc(n_dir_all, N)}；方向(仅首选) {n_dir_first}/24 = {pc(n_dir_first, N)}；'
         f'让球(首选+次选) {n_hhad_all}/24 = {pc(n_hhad_all, len(hhad_rows))}；总进球TOP2 {n_ttg}/24 = {pc(n_ttg, N)}；'
         f'半全场TOP3 {n_hafu}/24 = {pc(n_hafu, N)}；比分TOP5 {n_score}/24 = {pc(n_score, N)}。')
o.append('')
o.append('## 逐场回测')
o.append('')
for r in rows:
    o.append(f"### {r['num'].replace('周日','')} {r['home']} vs {r['away']}（{r['league']}）")
    o.append('')
    o.append(f"⏰ {r['time']} ｜ 🏟 {r['venue']} ｜ **{r['ft']}**")
    o.append('')
    o.append(f"**赛果：** 半场{r['ht']} → 全场{r['ft']} | 总进球{r['res_total']} | {r['res_dir']}")
    o.append('')
    o.append('**预测回顾：**')
    o.append('')
    o.append('| 维度 | 预测 | 实际 | 命中 |')
    o.append('|:---|:---|:---|:---:|')
    o.append(f"| **方向** | {r['dir_first']} / {r['dir_second']} | {r['res_dir']} | {r['d_hit']} |")
    o.append(f"| **让球** | {('让(%+.0f)%s / 让(%+.0f)%s' % (r['hhad_line'], r['hhad_first'], r['hhad_line'], r['hhad_second'])) if r['hhad_line'] is not None else '未开售'} "
             f"| {('让(%+.0f)%s' % (r['hhad_line'], r['res_hhad'])) if r['hhad_line'] is not None else '—'} | {r['h_hit']} |")
    o.append(f"| **总进球TOP2** | **{r['ttg_top2'][0][0]}球**({pf(r['ttg_top2'][0][1])}) / **{r['ttg_top2'][1][0]}球**({pf(r['ttg_top2'][1][1])}) | {r['res_total']}球 | {r['t_hit']} |")
    _hp = [x[1] for x in r['hafu_top3']]
    _hn = '（规则66 强制含平路径，故未按概率降序）' if _hp != sorted(_hp, reverse=True) else ''
    o.append(f"| **半全场TOP3** | {' > '.join(f'**{h}**({pf(x)})' for h, x in r['hafu_top3'])}{_hn}（实际{r['res_hafu']}） | {r['res_hafu']} | {r['f_hit']} |")
    o.append(f"| **比分TOP5** | {' > '.join(f'**{s}**({pf(x)})' for s, x in r['scores_top5'])} | **{r['res_score']}** | {r['s_hit']} |")
    o.append('')
    # 逐场点评
    if r['d_hit'] != '❌' and r['t_hit'] == '✅' and r['f_hit'] == '✅' and r['s_hit'] == '✅':
        cmt = '五维全中，模型与赛果高度吻合。'
    else:
        cs = []
        if r['d_hit'] == '❌':
            cs.append(f"方向失手（预测{r['dir_first']}/{r['dir_second']}，实际{r['res_dir']}）")
        if r['t_hit'] == '❌':
            cs.append(f"总进球落空（预测{r['ttg_top2'][0][0]}/{r['ttg_top2'][1][0]}球，实际{r['res_total']}球）")
        if r['f_hit'] == '❌':
            cs.append(f"半全场未覆盖（实际{r['res_hafu']}）")
        if r['s_hit'] == '❌':
            cs.append(f"比分TOP5未含{r['res_score']}")
        cmt = '；'.join(cs) + '。'
    o.append(f"> {cmt}")
    o.append('')
o.append('')

o.append('## 命中率统计')
o.append('')
o.append('| 维度 | 命中/总场 | 命中率 | 评级 |')
o.append('|:---|:---:|:---:|:---:|')
for nm, x, n in (('**方向(首选+次选)**', n_dir_all, N), ('**方向(仅首选)**', n_dir_first, N),
                 ('**让球(首选+次选)**', n_hhad_all, len(hhad_rows)),
                 ('**总进球TOP2**', n_ttg, N), ('**半全场TOP3**', n_hafu, N), ('**比分TOP5**', n_score, N)):
    o.append(f"| {nm} | {x}/{n} | {pc(x, n)} | {grade(x, n)} |")
o.append('')
miss_dir = [r['num'].replace('周日', '') for r in rows if r['d_hit'] == '❌']
o.append(f"> 方向命中明细：首选命中{n_dir_first}场 + 次选命中{n_dir_second}场 = 合计{n_dir_all}场命中，"
         f"未中{len(miss_dir)}场（{'、'.join(miss_dir)}）。"
         f"让球命中明细：首选命中{n_hhad_first}场 + 次选命中{n_hhad_all - n_hhad_first}场 = 合计{n_hhad_all}场命中，"
         f"未中{len(hhad_rows) - n_hhad_all}场（{'、'.join(r['num'].replace('周日','') for r in hhad_rows if r['h_hit'] == '❌')}）。")
o.append('')

o.append('## 串关回测')
o.append('')
o.append(f'> **回测基准：** 以赛前分析报告的「串关思路」章节原始推荐为基准'
         f'（[分析报告](../analysis/20260913_sunday_analysis_zhihu.md)），'
         f'赔率为赛前采集的**原始赔率**（非回测时赔率），共 {len(PARLAY)} 个方案。'
         f'"类型"列与分析报告子分类名称一一对应。')
o.append('')
o.append('| 方案 | 类型 | 场次 | 各场结果 | 串关命中 | 估算赔率 |')
o.append('|:---|:---|:---|:---|:---:|:---:|')
for p in PARLAY:
    o.append(f"| {p['name']} | {p['type']} | {' + '.join(x.split()[0] for x in p['detail'])} | "
             f"{' + '.join(p['detail'])} | {'✅' if p['hit'] else '❌'} | "
             f"{('~%.2f' % p['odds']) if p.get('odds') else '—'} |")
o.append('')
_hit_names = [p['name'] for p in parlay_hit]
_cn = [n for n in _hit_names if '连续编号' in n]
_lt = [n for n in _hit_names if '连续编号' not in n]
_steady = ['方向串', '让球串', '混合串']
_ent = ['总进球串', '高赔半全场串', '半全场混合', '比分串']
_s_hit = sum(v[0] for k, v in parlay_by_type.items() if k in _steady)
_s_tot = sum(v[1] for k, v in parlay_by_type.items() if k in _steady)
_e_hit = sum(v[0] for k, v in parlay_by_type.items() if k in _ent)
_e_tot = sum(v[1] for k, v in parlay_by_type.items() if k in _ent)
o.append(f"> 串关命中 {n_parlay}/{len(PARLAY)} 个方案，命中率 {pc(n_parlay, len(PARLAY))}（{grade(n_parlay, len(PARLAY))}）。"
         f"分类命中：{'；'.join(f'{k} {v[0]}/{v[1]}' for k, v in parlay_by_type.items())}。"
         f"**分组统计：稳健方案（方向串+让球串+混合串）{_s_hit}/{_s_tot} = {pc(_s_hit, _s_tot)}（{grade(_s_hit, _s_tot)}）；"
         f"娱乐串（总进球串+高赔半全场串+半全场混合+比分串）{_e_hit}/{_e_tot} = {pc(_e_hit, _e_tot)}（{grade(_e_hit, _e_tot)}）。**"
         f"命中的 {n_parlay} 个方案中——连续编号类 {len(_cn)} 个（{'、'.join(_cn) or '无'}）、"
         f"字母类 {len(_lt)} 个（{'、'.join(_lt) or '无'}）。"
         f"翻车主因：三串一方案（方向串B/价值让球串/半全场串A·B/总进球串A·B）单场容错为零，"
         f"任一场失手即整串作废；比分类 6 个方案全部落空。")
o.append('')

o.append('## 关键发现')
o.append('')
o.append(f'**1. 方向与让球两项均达优秀档，L096「次选必含平局」被验证。** 方向(首选+次选) {pc(n_dir_all, N)}、'
         f'让球(首选+次选) {pc(n_hhad_all, len(hhad_rows))}。本轮实际8场平局，'
         f'{len(draw_cover)}场被次选覆盖（{"、".join(r["num"].replace("周日","") for r in draw_cover)}），'
         f'仅005库奥皮奥0-0、006海伦芬0-0两场漏判——两场均为"主胜首选+客胜次选"的结构，'
         f'次选给了客胜而非平局，正是L096所指的次选设置过窄问题。')
o.append('')
o.append(f'**2. 总进球TOP2仅{pc(n_ttg, N)}，双向失守。** {len(ttg_miss)}场未中：'
         f'高球低估（009莱比锡5-0预测2-3球、010莱万特2-4预测3球档、011汉坎1-5预测2-3球）'
         f'与低球高估（005/006两场0-0预测2球档、015那不勒斯1-0）并存，'
         f'说明规则65大球上修与"铁桶阵零封"反向过滤（L093/L100）本轮均未落地到档位。')
o.append('')
o.append(f'**3. 半全场TOP3 {pc(n_hafu, N)}，规则66半场平局修正见效。** 本轮半全场大量为"上半场平→下半场分出胜负"'
         f'（001平平?实际平/平、007胜胜、"上半场0-0下半场定胜负"的015/019/021/023），'
         f'高半场平局联赛（日职0.534）的首选含平约束避免了方向性误判。')
o.append('')
o.append(f'**4. 比分TOP5 {pc(n_score, N)}，0-0与高比分两端均未覆盖。** {len(score_miss)}场未中，'
         f'其中005/006两场0-0、009莱比锡5-0、011汉坎1-5、021皇家社会0-3等大比分为主要遗漏。')
o.append('')
o.append(f'**5. 串关仅{pc(n_parlay, len(PARLAY))}，命中集中在低关数方案。** '
         f'命中的 {n_parlay} 个方案为：{"、".join(_hit_names)}。'
         f'三串一方案（方向串B、价值让球串、半全场串A/B、总进球串A/B）全部落空，比分类 6 个方案亦全灭——'
         f'单场容错为零的高关数方案是本轮串关的主要失分源。')
o.append('')

o.append('## 待改进')
o.append('')
o.append('- **总进球档位是最大短板（29.2%）**：需把规则65（大球上修）与L093/L100（反向小球过滤）真正落到总进球档位，'
         '对"碾压场"强制给出5/6球档、对"双方场均进球均<1.0的闷战场"强制给出0-1球档。')
o.append('- **0-0场景系统性缺失（005/006两场0-0均未覆盖）**：两场双方场均进球均低于1.1，'
         '应在总进球与比分TOP5中强制纳入0球档与0-0比分（规则53一致性校验）。')
o.append('- **方向次选位仍有2场漏平局（005/006）**：按L096，平局概率≥24%的场次强制把平局放入次选，'
         '本轮005（平24.9%）、006（平17.4%）中005本应进次选。')
o.append('- **高赔三串一方案全灭**：娱乐串中的三串一（半全场串A/B、总进球串A/B）单场容错为零，'
         '建议按L093降低关数或提高单场概率门槛。')
o.append('')
o.append('## ☕ 写在最后')
o.append('')
_cr = io.open(os.path.join(ROOT, r'templates\closing_remarks.md'), encoding='utf-8').read()
_cands = [b.strip() for b in re.split(r'\n---+\n', _cr) if '## ☕' in b]
_pick = _cands[random.Random(20260914).randrange(len(_cands))] if _cands else ''
o.append(_pick)
o.append('')

os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
with io.open(OUT_MD, 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(o))
print('written', OUT_MD)

# ==================== 归档回测JSON ====================
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
bt = dict(
    backtest_id='2026-09-13_sunday',
    match_date='2026-09-13', day='sunday', total_matches=N,
    model_version='AGENTS.md v2.12.0 / 33模型8大类',
    summary=dict(dir_all=f'{n_dir_all}/{N}', dir_first=f'{n_dir_first}/{N}',
                 dir_second=f'{n_dir_second}/{N}', hhad_all=f'{n_hhad_all}/{len(hhad_rows)}',
                 hhad_first=f'{n_hhad_first}/{len(hhad_rows)}',
                 ttg_top2=f'{n_ttg}/{N}', hafu_top3=f'{n_hafu}/{N}',
                 score_top5=f'{n_score}/{N}', parlay=f'{n_parlay}/{len(PARLAY)}'),
    hit_rates=dict(dir_all=round(n_dir_all / N, 4), dir_first=round(n_dir_first / N, 4),
                   hhad_all=round(n_hhad_all / len(hhad_rows), 4),
                   ttg_top2=round(n_ttg / N, 4), hafu_top3=round(n_hafu / N, 4),
                   score_top5=round(n_score / N, 4),
                   parlay=round(n_parlay / len(PARLAY), 4)),
    results=[dict(num=r['num'], home=r['home'], away=r['away'], league=r['league'],
                  ht=r['ht'], ft=r['ft'], res_dir=r['res_dir'], res_total=r['res_total'],
                  res_hafu=r['res_hafu'], res_hhad=r['res_hhad'],
                  pred_dir_first=r['dir_first'], pred_dir_second=r['dir_second'], dir_hit=r['d_hit'],
                  pred_hhad_first=r['hhad_first'], pred_hhad_second=r['hhad_second'], hhad_hit=r['h_hit'],
                  pred_ttg_top2=r['ttg_top2'], ttg_hit=r['t_hit'],
                  pred_hafu_top3=r['hafu_top3'], hafu_hit=r['f_hit'],
                  pred_scores_top5=r['scores_top5'], score_hit=r['s_hit']) for r in rows],
    parlays=[dict(name=p['name'], type=p['type'], matches=p['detail'],
                  hit=p['hit'], odds_est=p.get('odds'), note=p.get('section')) for p in PARLAY],
    parlay_stats=dict(total=len(PARLAY), hit=n_parlay, miss=len(PARLAY) - n_parlay,
                      rate=round(n_parlay / len(PARLAY), 4),
                      by_type={k: f'{v[0]}/{v[1]}' for k, v in parlay_by_type.items()}),
    key_lessons=['L103 总进球档位双向失守', 'L104 0-0场景系统性缺失', 'L105 次选漏平局仍存2场',
                 'L106 比分串方向优先流程首次实战 0/6 精确命中'],
    source_files=[ANALYSIS, os.path.join(WORK, 'pred_20260913.json')],
)
json.dump(bt, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('written', OUT_JSON)

# ==================== 生成教训JSON ====================
os.makedirs(os.path.dirname(OUT_LESSON), exist_ok=True)
lesson = dict(
    meta=dict(date='2026-09-13', day='sunday', total_matches=N,
              leagues=sorted(set(r['league'] for r in rows)),
              tags=['总进球', '大球低估', '零封0-0', '次选漏平局', '平局潮',
                    '规则65', '规则63', '规则67试用', '连续编号', '串关']),
    hit_rates=dict(dir_all=f'{n_dir_all}/{N}', dir_first=f'{n_dir_first}/{N}',
                   hhad_all=f'{n_hhad_all}/{len(hhad_rows)}', hhad_first=f'{n_hhad_first}/{len(hhad_rows)}',
                   ttg_top2=f'{n_ttg}/{N}', hafu_top3=f'{n_hafu}/{N}',
                   score_top5=f'{n_score}/{N}', parlay=f'{n_parlay}/{len(PARLAY)}'),
    lessons=[
        dict(id='L103', title='总进球TOP2双向失守（29.2%）——高球低估与低球高估并存',
             tags=['总进球', '大球低估', '小球高估', '规则65'],
             event=f'{len(ttg_miss)}场未中，高球低估（009莱比锡5-0、010莱万特2-4、011汉坎1-5）与低球高估（005/006两场0-0、015那不勒斯1-0）并存',
             impact='总进球维度仅29.2%，为本轮最弱项',
             root_cause=['规则65大球上修未落到TTG档位（仅标注未执行）',
                         'L093/L100「铁桶阵零封」反向过滤未启用',
                         '碾压场未强制给出5/6球档'],
             improvement='规则65与反向过滤必须落到TTG档位；碾压场TTG TOP2强制含4/5球档；双方场均进球<1.1的闷战场强制含0-1球档'),
        dict(id='L104', title='0-0场景系统性缺失——两场0-0均未被TTG与比分TOP5覆盖',
             tags=['零封0-0', '比分TOP5', '规则53'],
             event='005库奥皮奥0-0赫尔辛基、006海伦芬0-0特尔斯达，TTG预测均为2球档、比分TOP5未含0-0',
             impact='两场方向也随之失手（预测主胜/客胜，实际平局）',
             root_cause=['低进球预期场次未触发ZIP/0-0上修', '规则53（比分首选与TTG一致性校验）未在生成端强制'],
             improvement='双方赛季场均进球均<1.1时，TTG TOP2强制含0球档、比分TOP5强制含0-0（规则53）'),
        dict(id='L105', title='次选位漏平局仍存2场——L096未完全落地',
             tags=['次选漏平局', '平局潮', '规则63'],
             event='实际8场平局中6场被次选覆盖，005（平24.9%）、006（平17.4%）两场次选给了客胜',
             impact='方向未中2/24，方向(首选+次选)止步87.5%',
             root_cause=['次选位未按L096「平局概率≥24%强制入次选」执行', '005平局24.9%本应进次选'],
             improvement='次选生成端硬校验：平局概率≥24%时，次选必须为平局（除首选已是平局）'),
        dict(id='L106', title='比分串方向优先流程首次实战——0/6精确命中，维持试用不转正',
             tags=['规则67试用', '比分串', '方向自洽'],
             event='规则67正向流程本轮用于6场（003/004/017/018/021/022），精确命中0场，'
                   '4场半命中（004/017/018/021方向对但比分未中），2场方向未中（003/022）',
             impact='累计前瞻8场，精确命中2场（25%），远低于60%转正线',
             root_cause=['净胜球众数取1球偏保守，实际多打出3-1、4-1、0-3等更大分差',
                         '总进球档位失准直接传导到比分（TTG仅29.2%）'],
             improvement='维持试用不转正；比分串建议与TTG档位联动修正后再评估；'
                          '按L098补充选场门槛（方向概率≥55%且方向内净胜球占比≥33%）'),
    ],
    rule_triggers=[
        dict(rule='规则63 单关平局上修', matches='001/003/007/013/015/019/021',
             execution='7场全部执行+8%平局上修',
             result='7场中实际平局3场（001/003+019非平），001/003两场被次选命中，方向整体21/24'),
        dict(rule='规则66 半场平局联赛修正', matches='日职001等高档联赛',
             execution='高档联赛半场λ系数0.38、半全场首选强制含平',
             result='半全场TOP3 19/24 = 79.2%，表现优秀'),
        dict(rule='规则52a 让球无条件净胜球众数', matches='24场',
             execution='全部按无条件分布口径取众数并三选覆盖',
             result=f'让球(首选+次选) {n_hhad_all}/24 = {pc(n_hhad_all, len(hhad_rows))}，'
                    f'较9-12的36.7%大幅提升，旧口径有效性再获验证'),
        dict(rule='规则68 英超弱队状态上修', matches='013 曼联vs曼城',
             execution='判定曼联近5场10分属状态好，标注爆冷预警',
             result='实际曼联0-1曼城（客胜），未爆冷；但曼城仅1球小胜，与"英超主场加成低"的低净胜球判断一致'),
        dict(rule='规则71 娱乐串排除法甲', matches='非PSG法甲2场（008/012）',
             execution='娱乐串纳入0场，连续编号段跨法甲已换段',
             result='008里尔2-0（主胜，命中）、012勒芒2-2（平，未纳入）；排除未造成损失'),
    ],
    new_rule_suggestions=[
        dict(suggested_rule='总进球档位强制校验（新增规则72）',
             source_lesson='L103',
             summary='碾压场（身价差≥2倍或λ差≥0.8）TTG TOP2必须含4/5球档；'
                       '双方场均进球均<1.1的闷战场TTG TOP2必须含0/1球档；生成端硬校验，违反则打回'),
        dict(suggested_rule='次选位平局硬校验（强化L096为规则）',
             source_lesson='L105',
             summary='平局概率≥24%的场次，次选必须为平局（首选已为平局时除外）；生成端硬校验'),
    ],
)
json.dump(lesson, open(OUT_LESSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('written', OUT_LESSON)
print('\ncalc saved')
