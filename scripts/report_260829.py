# -*- coding: utf-8 -*-
"""
生成周六2026-08-29 竞彩分析HTML报告
读取 260829_analysis_results.json，输出知乎风格HTML报告
"""
import json, html, os

BASE = r'e:\VibeCoding\football'

with open(os.path.join(BASE, r'reports\data\260829_analysis_results.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

matches = data['matches']
parlays = data['parlays']
single_matches = set(data['single_matches'])

# 联赛分组顺序
league_order = ['日职', '日乙', '韩职', '英超', '瑞超', '德甲', '西甲', '法甲', '挪超', '意甲', '荷甲', '葡超', '美职']
league_names = {
    '日职': '日职联 J1', '日乙': '日职乙 J2', '韩职': '韩K联', '英超': '英超',
    '瑞超': '瑞典超', '德甲': '德甲', '西甲': '西甲', '法甲': '法甲',
    '挪超': '挪超', '意甲': '意甲', '荷甲': '荷甲', '葡超': '葡超', '美职': '美职联'
}

def esc(s):
    return html.escape(str(s))

def league_key(m):
    return m['league']

# 按联赛分组
groups = {}
for num, m in matches.items():
    lg = m['league']
    groups.setdefault(lg, []).append((num, m))

# 排序分组
sorted_groups = []
for lg in league_order:
    if lg in groups:
        # 组内按时间排序
        items = sorted(groups[lg], key=lambda x: x[1]['time'])
        sorted_groups.append((lg, items))
# 兜底：未在order中的
for lg, items in groups.items():
    if lg not in league_order:
        sorted_groups.append((lg, sorted(items, key=lambda x: x[1]['time'])))

# 概率条颜色
def bar_color(pct):
    if pct >= 55:
        return '#e74c3c'
    elif pct >= 45:
        return '#e67e22'
    elif pct >= 35:
        return '#f1c40f'
    else:
        return '#95a5a6'

def prob_bar(pct):
    return f'<div class="bar"><div class="bar-fill" style="width:{min(pct,100):.1f}%;background:{bar_color(pct)}"></div><span>{pct:.1f}%</span></div>'

def star_disp(stars):
    s = esc(stars)
    return f'<span class="stars">{s}</span>'

# 方向标签颜色
def dir_badge(direction):
    c = {'主胜': '#c0392b', '客胜': '#2980b9', '平局': '#7f8c8d'}.get(direction, '#7f8c8d')
    return f'<span class="dir-badge" style="background:{c}">{esc(direction)}</span>'

# 生成单场卡片
def match_card(num, m):
    single_tag = '<span class="single-tag">单关</span>' if m['single'] else ''
    stars = m.get('stars', '')
    ttg2 = m.get('ttg_top2', [])
    scores5 = m.get('scores_top5', [])
    hafu3 = m.get('hafu_top3', [])
    h2h = m.get('h2h', '')
    inj_h = m.get('injuries_h', '')
    inj_a = m.get('injuries_a', '')
    ctx = m.get('context', '')
    lam_h = m.get('lambda_h', 0)
    lam_a = m.get('lambda_a', 0)
    val = m.get('value_diff', 0)

    val_note = ''
    if val and val != 1.0:
        if val >= 2.0:
            val_note = f'<span class="val-note">身价差 {val:.1f}×（身价碾压）</span>'
        else:
            val_note = f'<span class="val-note">身价差 {val:.2f}×</span>'

    h2h_html = f'<div class="kv"><span class="k">交锋</span><span class="v">{esc(h2h)}</span></div>' if h2h else ''
    inj_html = ''
    if inj_h or inj_a:
        inj_html = '<div class="kv"><span class="k">伤停</span><span class="v">'
        if inj_h:
            inj_html += f'<b>{esc(m["home"])}</b>：{esc(inj_h)}'
        if inj_a:
            inj_html += f'　<b>{esc(m["away"])}</b>：{esc(inj_a)}'
        inj_html += '</span></div>'
    ctx_html = f'<div class="kv"><span class="k">要点</span><span class="v">{esc(ctx)}</span></div>' if ctx else ''

    return f'''
    <div class="match-card">
      <div class="match-head">
        <div class="match-title">
          <span class="match-num">周六{esc(num)}</span>
          <span class="match-teams">{esc(m['home'])} <span class="vs">vs</span> {esc(m['away'])}</span>
          {single_tag} {val_note}
        </div>
        <div class="match-dir">{dir_badge(m['direction'])} <span class="dir-2nd">次选 {esc(m['direction_2nd'])}</span> {star_disp(stars)}</div>
      </div>
      <div class="match-probs">
        <div class="prob-item"><label>主胜</label>{prob_bar(m['home_win'])}</div>
        <div class="prob-item"><label>平局</label>{prob_bar(m['draw'])}</div>
        <div class="prob-item"><label>客胜</label>{prob_bar(m['away_win'])}</div>
      </div>
      <div class="match-detail">
        <div class="kv"><span class="k">总进球</span><span class="v">TOP2：{esc(' / '.join(f'{t}球' for t in ttg2))}</span></div>
        <div class="kv"><span class="k">比分</span><span class="v">TOP5：{esc('、'.join(scores5))}</span></div>
        <div class="kv"><span class="k">半全场</span><span class="v">TOP3：{esc('、'.join(hafu3))}</span></div>
        <div class="kv"><span class="k">模型λ</span><span class="v">主{lam_h:.2f} / 客{lam_a:.2f}</span></div>
        {h2h_html}{inj_html}{ctx_html}
      </div>
    </div>'''

# 组装HTML
cards_html = []
for lg, items in sorted_groups:
    cards = '\n'.join(match_card(num, m) for num, m in items)
    cards_html.append(f'''
    <section class="league-block">
      <h2 class="league-title">{esc(league_names.get(lg, lg))} <span class="count">({len(items)}场)</span></h2>
      <div class="cards">{cards}</div>
    </section>''')

cards_all = '\n'.join(cards_html)

# 总览表
overview_rows = []
for num in sorted(matches.keys()):
    m = matches[num]
    single = '单关' if m['single'] else ''
    overview_rows.append(f'''<tr class="{'single-row' if m['single'] else ''}">
      <td>{esc(num)}</td>
      <td>{esc(m['league'])}</td>
      <td>{esc(m['home'])} vs {esc(m['away'])}</td>
      <td>{dir_badge(m['direction'])}</td>
      <td>{esc(m['direction_2nd'])}</td>
      <td>{esc(m['stars'])}</td>
      <td>{m['home_win']:.1f}% / {m['draw']:.1f}% / {m['away_win']:.1f}%</td>
      <td>{esc(' / '.join(f'{t}球' for t in m['ttg_top2']))}</td>
      <td>{esc('、'.join(m['scores_top5'][:3]))}</td>
      <td>{single}</td>
    </tr>''')
overview_html = '\n'.join(overview_rows)

# 串关方案
parlay_meta = {
    'A_方向串': ('方向串 A（稳健）', '选取高置信度方向场次，追求稳健'),
    'B_让球串': ('让球串 B（价值）', '让球盘深场次，追求让球价值'),
    'C_混合串': ('混合串 C', '方向与让球结合'),
    'D_娱乐串': ('娱乐串 D（比分）', '高赔比分串，基本面优先'),
}
parlay_html = ''
for key, (title, desc) in parlay_meta.items():
    nums = parlays.get(key, [])
    rows = ''
    for num in nums:
        if num in matches:
            m = matches[num]
            if '让球' in title:
                rec = f'让{m["goalLine"]}球 {m["direction"]}'
            elif '比分' in title or '娱乐' in title:
                rec = f'比分 {m["scores_top5"][0]}'
            else:
                rec = m['direction']
            rows += f'<tr><td>{esc(num)}</td><td>{esc(m["home"])} vs {esc(m["away"])}</td><td>{esc(rec)}</td><td>{esc(m["stars"])}</td><td>{m["home_win"]:.1f}% / {m["draw"]:.1f}% / {m["away_win"]:.1f}%</td></tr>'
    parlay_html += f'''
    <div class="parlay-block">
      <h3>{esc(title)}</h3>
      <p class="parlay-desc">{esc(desc)}</p>
      <table class="parlay-table"><thead><tr><th>场次</th><th>对阵</th><th>推荐</th><th>置信度</th><th>概率(主/平/客)</th></tr></thead><tbody>{rows}</tbody></table>
    </div>'''

single_list = '、'.join(f'周六{n}' for n in sorted(single_matches))

html_doc = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026-08-29 周六竞彩足球分析报告</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Microsoft YaHei", sans-serif; background: #f5f6f8; color: #2c3e50; line-height: 1.6; }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 24px 16px 60px; }}
  header {{ background: linear-gradient(135deg, #1a5c3a 0%, #2e8b57 100%); color: #fff; padding: 32px 28px; border-radius: 14px; margin-bottom: 24px; }}
  header h1 {{ font-size: 26px; margin-bottom: 8px; }}
  header .sub {{ opacity: 0.92; font-size: 14px; }}
  .stat-row {{ display: flex; gap: 14px; margin-top: 16px; flex-wrap: wrap; }}
  .stat {{ background: rgba(255,255,255,0.15); padding: 10px 16px; border-radius: 8px; font-size: 14px; }}
  .stat b {{ font-size: 20px; }}
  h2.league-title {{ font-size: 19px; margin: 26px 0 12px; padding-left: 12px; border-left: 4px solid #2e8b57; color: #1a5c3a; }}
  .count {{ font-size: 13px; color: #888; font-weight: normal; }}
  .cards {{ display: grid; grid-template-columns: 1fr; gap: 14px; }}
  .match-card {{ background: #fff; border-radius: 12px; padding: 16px 18px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .match-head {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }}
  .match-num {{ font-weight: 700; color: #1a5c3a; margin-right: 6px; }}
  .match-teams {{ font-size: 16px; font-weight: 600; }}
  .vs {{ color: #bbb; font-weight: normal; font-size: 13px; margin: 0 4px; }}
  .single-tag {{ background: #e74c3c; color: #fff; font-size: 11px; padding: 2px 7px; border-radius: 4px; margin-left: 6px; }}
  .val-note {{ font-size: 11px; color: #e67e22; background: #fdf2e9; padding: 2px 7px; border-radius: 4px; margin-left: 6px; }}
  .dir-badge {{ color: #fff; font-size: 13px; font-weight: 700; padding: 3px 12px; border-radius: 14px; }}
  .dir-2nd {{ font-size: 13px; color: #666; margin-left: 6px; }}
  .stars {{ color: #f39c12; font-weight: 700; margin-left: 4px; }}
  .match-probs {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 10px; }}
  .prob-item label {{ font-size: 12px; color: #777; display: block; margin-bottom: 3px; }}
  .bar {{ position: relative; background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 10px; }}
  .bar span {{ position: absolute; right: 8px; top: 0; font-size: 11px; line-height: 20px; color: #333; }}
  .match-detail {{ font-size: 13px; }}
  .kv {{ display: flex; margin-bottom: 4px; }}
  .kv .k {{ flex: 0 0 62px; color: #999; font-size: 12px; }}
  .kv .v {{ flex: 1; color: #444; }}
  .kv .v b {{ color: #2c3e50; }}
  .overview-table, .parlay-table {{ width: 100%; border-collapse: collapse; background: #fff; font-size: 13px; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .overview-table th, .overview-table td, .parlay-table th, .parlay-table td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #eee; }}
  .overview-table th {{ background: #1a5c3a; color: #fff; }}
  .single-row td {{ background: #fef5f5; }}
  .parlay-block {{ background: #fff; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .parlay-block h3 {{ font-size: 16px; color: #1a5c3a; margin-bottom: 4px; }}
  .parlay-desc {{ font-size: 12px; color: #999; margin-bottom: 10px; }}
  .parlay-table th {{ background: #2e8b57; color: #fff; }}
  .risk {{ background: #fff8e1; border-left: 4px solid #f39c12; padding: 16px 18px; border-radius: 8px; margin-top: 24px; font-size: 13px; color: #7f6000; }}
  .risk h3 {{ color: #b7791f; font-size: 15px; margin-bottom: 8px; }}
  .risk ul {{ padding-left: 20px; }}
  .risk li {{ margin-bottom: 4px; }}
  .section-nav {{ background: #fff; border-radius: 10px; padding: 14px 18px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); font-size: 13px; color: #666; }}
  .section-nav a {{ color: #2e8b57; text-decoration: none; margin-right: 10px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>周六竞彩足球分析报告</h1>
    <div class="sub">日期：2026-08-29（周六）｜ 基于多模型融合（Dixon-Coles + 泊松 + 单关平局上修 + 大球上修）</div>
    <div class="stat-row">
      <div class="stat">总场次 <b>{data['total_matches']}</b></div>
      <div class="stat">单关场次 <b>{len(single_matches)}</b></div>
      <div class="stat">覆盖联赛 <b>{len(groups)}</b></div>
    </div>
  </header>

  <div class="section-nav">单关场次：{esc(single_list)}　|　<a href="#overview">总览</a> <a href="#parlays">串关方案</a> <a href="#risk">风险提示</a></div>

  <h2 class="league-title" id="overview">全场次总览</h2>
  <table class="overview-table">
    <thead><tr><th>场次</th><th>联赛</th><th>对阵</th><th>方向</th><th>次选</th><th>置信</th><th>概率(主/平/客)</th><th>总进球TOP2</th><th>比分TOP3</th><th>单关</th></tr></thead>
    <tbody>{overview_html}</tbody>
  </table>

  {cards_all}

  <h2 class="league-title" id="parlays">串关推荐方案</h2>
  {parlay_html}

  <div class="risk" id="risk">
    <h3>风险提示</h3>
    <ul>
      <li>本报告基于历史数据与数学模型，任何预测均非 100% 准确，比分存在极大不确定性。</li>
      <li>突发因素（红牌、点球、天气、临场伤停）无法完全预测，请以实时数据为准。</li>
      <li>单关场次平局概率已按规则 63 上修，方向仅供概率参考，不代表必然结果。</li>
      <li>大球预测已按规则 65 上修，Tier2/Tier3 联赛倾向大球，但小球联赛（日乙等）需注意小球基准冲突。</li>
      <li>理性看待预测，切勿沉迷赌博。本报告不构成任何投注建议。</li>
    </ul>
  </div>
</div>
</body>
</html>'''

out_path = os.path.join(BASE, r'reports\analysis\260829_saturday_analysis.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html_doc)

print(f"HTML报告已生成: {out_path}")
print(f"共 {data['total_matches']} 场，单关 {len(single_matches)} 场")
