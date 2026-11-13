# -*- coding: utf-8 -*-
"""
竞彩Agent — HTML报告生成器
生成可视化的竞彩分析报告
"""

import json
import os
from datetime import datetime

from .config import COLORS, REPORT_CONFIG


class ReportGenerator:
    """HTML报告生成器"""

    def __init__(self, report_data):
        self.data = report_data
        self.ticket_id = report_data.get('ticket_id', 'unknown')
        self.date = report_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))

    def generate_html(self, output_path=None):
        """生成完整HTML报告"""
        html = self._build_html()

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[ReportGenerator] HTML报告已保存至 {output_path}")

        return html

    def _build_html(self):
        """构建HTML内容"""
        summary = self.data.get('summary', {})
        matches = self.data.get('matches', [])
        parlay = self.data.get('parlay_suggestions', {})

        sections = []
        sections.append(self._header())
        sections.append(self._summary_section(summary))
        sections.append(self._matches_table(matches))

        for i, m in enumerate(matches):
            sections.append(self._match_detail(m, i+1))

        sections.append(self._parlay_section(parlay))
        sections.append(self._divergence_section(summary.get('divergence_alerts', [])))
        sections.append(self._gaoshan_section())
        sections.append(self._footer())

        return '\n'.join(sections)

    def _header(self):
        """HTML头部"""
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>竞彩分析报告 #{self.ticket_id}</title>
<style>
:root {{
  --primary: {COLORS['primary']};
  --success: {COLORS['success']};
  --warning: {COLORS['warning']};
  --danger: {COLORS['danger']};
  --info: {COLORS['info']};
  --text: {COLORS['text']};
  --text2: {COLORS['text_secondary']};
  --bg: {COLORS['bg']};
  --border: {COLORS['border']};
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
h1 {{ font-size: 28px; margin-bottom: 8px; color: var(--primary); }}
h2 {{ font-size: 20px; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 2px solid var(--primary); color: var(--text); }}
h3 {{ font-size: 16px; margin: 16px 0 8px; color: var(--text2); }}
.header {{ background: linear-gradient(135deg, var(--primary), #0d47a1); color: white; padding: 24px; border-radius: 12px; margin-bottom: 20px; }}
.header .subtitle {{ opacity: 0.85; font-size: 14px; margin-top: 4px; }}

/* 卡片 */
.card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.card-title {{ font-size: 16px; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}

/* 统计网格 */
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 12px 0; }}
.stat-box {{ background: var(--bg); border-radius: 8px; padding: 14px; text-align: center; }}
.stat-value {{ font-size: 24px; font-weight: 700; color: var(--primary); }}
.stat-label {{ font-size: 12px; color: var(--text2); margin-top: 4px; }}

/* 表格 */
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }}
th {{ background: var(--bg); text-align: left; padding: 10px 8px; font-weight: 600; border-bottom: 2px solid var(--border); }}
td {{ padding: 10px 8px; border-bottom: 1px solid var(--border); }}
tr:hover {{ background: rgba(26,115,232,0.03); }}

/* 标签 */
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
.badge-high {{ background: #e8f5e9; color: var(--success); }}
.badge-medium {{ background: #fff3e0; color: #e65100; }}
.badge-low {{ background: #fce4ec; color: var(--danger); }}
.badge-divergence {{ background: #f3e5f5; color: #6a1b9a; }}

/* 概率条 */
.prob-bar {{ height: 6px; background: var(--bg); border-radius: 3px; overflow: hidden; margin-top: 4px; }}
.prob-fill {{ height: 100%; border-radius: 3px; transition: width 0.3s; }}
.prob-fill-home {{ background: var(--success); }}
.prob-fill-draw {{ background: var(--warning); }}
.prob-fill-away {{ background: var(--danger); }}

/* 串关卡片 */
.parlay-card {{ border-left: 4px solid var(--primary); padding-left: 16px; margin: 12px 0; }}
.parlay-card.conservative {{ border-color: var(--success); }}
.parlay-card.balanced {{ border-color: var(--warning); }}
.parlay-card.aggressive {{ border-color: var(--danger); }}

/* 分歧警告 */
.divergence-alert {{ background: #fff3e0; border-left: 4px solid var(--warning); padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; }}

/* 比分推荐 */
.score-rec {{ display: inline-block; background: var(--primary); color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; margin-right: 6px; }}
.score-alt {{ display: inline-block; background: var(--bg); color: var(--text2); padding: 4px 10px; border-radius: 6px; font-size: 12px; margin-right: 4px; }}

/* 折叠详情 */
.details-toggle {{ cursor: pointer; color: var(--primary); font-size: 13px; }}
.match-details {{ display: none; margin-top: 12px; padding-top: 12px; border-top: 1px dashed var(--border); }}
.match-details.active {{ display: block; }}

/* 响应式 */
@media (max-width: 768px) {{
  .container {{ padding: 10px; }}
  .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
  table {{ font-size: 12px; }}
  td, th {{ padding: 6px 4px; }}
}}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>⚽ 竞彩分析报告 #{self.ticket_id}</h1>
<div class="subtitle">生成时间: {self.date} | 基于Dixon-Coles / 负二项 / Skellam / 蒙特卡洛多模型融合</div>
</div>'''

    def _summary_section(self, summary):
        """摘要区域"""
        total = summary.get('total_matches', 0)
        high = len(summary.get('high_confidence', []))
        medium = len(summary.get('medium_confidence', []))
        low = len(summary.get('low_confidence', []))
        dd = summary.get('direction_distribution', {})

        return f'''
<div class="card">
  <div class="card-title">📊 分析摘要</div>
  <div class="stats-grid">
    <div class="stat-box"><div class="stat-value">{total}</div><div class="stat-label">分析场次</div></div>
    <div class="stat-box"><div class="stat-value" style="color:{COLORS['success']}">{high}</div><div class="stat-label">高置信度</div></div>
    <div class="stat-box"><div class="stat-value" style="color:#e65100">{medium}</div><div class="stat-label">中置信度</div></div>
    <div class="stat-box"><div class="stat-value" style="color:{COLORS['danger']}">{low}</div><div class="stat-label">低置信度</div></div>
    <div class="stat-box"><div class="stat-value">{dd.get('主胜',0)}</div><div class="stat-label">推荐主胜</div></div>
    <div class="stat-box"><div class="stat-value">{dd.get('平局',0)}</div><div class="stat-label">推荐平局</div></div>
    <div class="stat-box"><div class="stat-value">{dd.get('客胜',0)}</div><div class="stat-label">推荐客胜</div></div>
  </div>
</div>'''

    def _value_cell(self, info):
        """生成身价对比单元格/段落 HTML
        身价单位: 万欧元。返回 (主队身价文本, 客队身价文本, 倍数) 或 None
        """
        home_v = info.get('home_value')
        away_v = info.get('away_value')
        if home_v is None or away_v is None:
            return '<span style="color:var(--text2)">信息缺失</span>'
        try:
            home_v = float(home_v)
            away_v = float(away_v)
        except (TypeError, ValueError):
            return '<span style="color:var(--text2)">信息缺失</span>'
        return self._value_html(home_v, away_v)

    @staticmethod
    def _fmt_value(v):
        """格式化身价: <10000万 → XXXX万欧元, >=10000万 → X.XX亿欧元"""
        if v >= 10000:
            return f"约{v/10000:.2f}亿欧元"
        return f"约{int(round(v))}万欧元"

    def _value_html(self, home_v, away_v):
        """生成身价对比HTML (含倍率与碾压标记)"""
        home_str = self._fmt_value(home_v)
        away_str = self._fmt_value(away_v)
        ratio = max(home_v, away_v) / min(home_v, away_v) if min(home_v, away_v) > 0 else 0
        dominant = '主队' if home_v >= away_v else '客队'
        weaker = '客队' if home_v >= away_v else '主队'
        crush = ' <span style="color:var(--danger)">碾压</span>' if ratio >= 2 else ''
        return f'{home_str}<span style="color:var(--text2)"> vs </span>{away_str}（{dominant}是{weaker}的{ratio:.1f}倍{crush}）'

    def _matches_table(self, matches):
        """比赛总览表格"""
        rows = []
        for i, m in enumerate(matches):
            info = m['analysis']['match_info']
            rec = m['recommendation']
            conf = m['analysis']['confidence']
            final = m['analysis']['final_probabilities']
            div = m['analysis']['divergence']

            # 身价对比列
            value_cell = self._value_cell(info)

            has_divergence = any(abs(v) > REPORT_CONFIG['show_divergence_threshold'] for v in div.values())
            divergence_badge = '<span class="badge badge-divergence">分歧</span>' if has_divergence else ''

            conf_class = f"badge-{conf['level']}"
            conf_label = {'high': '高', 'medium': '中', 'low': '低', 'very_low': '极低'}.get(conf['level'], '未知')

            # 概率条
            max_p = max(final.values())
            home_w = final['home'] / max_p * 100 if max_p > 0 else 0
            draw_w = final['draw'] / max_p * 100 if max_p > 0 else 0
            away_w = final['away'] / max_p * 100 if max_p > 0 else 0

            rows.append(f'''
<tr>
  <td><strong>{info['match_id']}</strong></td>
  <td>{info['league']}</td>
  <td>{info['home_team']} <span style="color:var(--text2)">vs</span> {info['away_team']}</td>
  <td>{value_cell}</td>
  <td><span class="badge {conf_class}">{conf_label} {conf['stars']}</span> {divergence_badge}</td>
  <td><strong>{rec['direction']}</strong> <span style="color:var(--text2);font-size:11px">{rec['direction_prob']:.1%}</span></td>
  <td><span class="score-rec">{rec['scores']['primary']}</span></td>
  <td>
    <div style="display:flex;gap:4px;align-items:center;font-size:11px">
      <span style="width:24px">主</span><div class="prob-bar" style="flex:1"><div class="prob-fill prob-fill-home" style="width:{home_w:.0f}%"></div></div>
      <span style="width:24px">平</span><div class="prob-bar" style="flex:1"><div class="prob-fill prob-fill-draw" style="width:{draw_w:.0f}%"></div></div>
      <span style="width:24px">客</span><div class="prob-bar" style="flex:1"><div class="prob-fill prob-fill-away" style="width:{away_w:.0f}%"></div></div>
    </div>
  </td>
</tr>''')

        return f'''
<div class="card">
  <div class="card-title">📋 比赛总览</div>
  <table>
    <thead><tr><th>编号</th><th>联赛</th><th>对阵</th><th>身价对比</th><th>置信度</th><th>推荐</th><th>首选比分</th><th>概率分布</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div>'''

    def _match_detail(self, match_data, idx):
        """单场比赛详情"""
        a = match_data['analysis']
        rec = match_data['recommendation']
        info = a['match_info']
        final = a['final_probabilities']
        models = a['model_outcomes']
        scores = a['final_scores']
        htft = a['htft']
        div = a['divergence']
        ev = a['ev']
        diag = a['league_diagnosis']
        odds = a['odds_calibration']

        # 模型对比表
        model_rows = []
        for name, label in [('dc', 'DC模型'), ('nb', '负二项'), ('skellam', 'Skellam'), ('elo', 'Elo评级'), ('monte_carlo', '蒙特卡洛'), ('shin', 'Shin去水')]:
            if models.get(name):
                m = models[name]
                if isinstance(m, dict) and 'home' in m:
                    model_rows.append(f'<tr><td>{label}</td><td>{m["home"]:.1%}</td><td>{m["draw"]:.1%}</td><td>{m["away"]:.1%}</td></tr>')

        # 比分Top5
        score_lines = []
        for (home_g, away_g), p in scores[:5]:
            score_lines.append(f'<span class="score-alt">{home_g}-{away_g} ({p:.1%})</span>')

        # 半全场
        htft_lines = []
        for h in htft[:3]:
            htft_lines.append(f'<span class="score-alt">{h["htft"]} ({h["probability"]:.1%})</span>')

        # 分歧
        div_lines = []
        for outcome, val in div.items():
            label = {'home': '主胜', 'draw': '平局', 'away': '客胜'}[outcome]
            sign = '+' if val > 0 else ''
            color = 'var(--success)' if val > 0 else ('var(--danger)' if val < 0 else 'var(--text2)')
            div_lines.append(f'<span style="color:{color}">{label}: {sign}{val:.1%}</span>')

        # EV
        ev_lines = []
        for outcome, val in ev.items():
            label = {'home': '主胜', 'draw': '平局', 'away': '客胜'}[outcome]
            color = 'var(--success)' if val > 0 else 'var(--danger)'
            ev_lines.append(f'<span style="color:{color}">{label}: {val:+.2f}</span>')

        # 高山验证
        gaoshan = a.get('confidence', {}).get('gaoshan', {})
        gaoshan_text = gaoshan.get('reason', '无数据')

        return f'''
<div class="card" id="match-{idx}">
  <div class="card-title">
    <span>#{info['match_id']}</span>
    <strong>{info['home_team']} vs {info['away_team']}</strong>
    <span style="color:var(--text2);font-size:12px">{info['league']}</span>
    <span class="badge badge-{a['confidence']['level']}">{a['confidence']['stars']}</span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-top:12px">
    <div>
      <h3>🎯 综合推荐</h3>
      <p>方向: <strong>{rec['direction']}</strong> ({rec['direction_prob']:.1%})</p>
      <p>比分: <span class="score-rec">{rec['scores']['primary']}</span> <span class="score-alt">{rec['scores']['alt1']}</span> <span class="score-alt">{rec['scores']['alt2']}</span></p>
      <p>总进球: {rec['total_goals']}</p>
      <p>半全场: {rec['htft']}</p>
      <p>💰 身价对比: {self._value_cell(info)}</p>
    </div>
    <div>
      <h3>📈 模型对比</h3>
      <table style="font-size:12px;margin:0">
        <thead><tr><th>模型</th><th>主胜</th><th>平局</th><th>客胜</th></tr></thead>
        <tbody>{''.join(model_rows)}</tbody>
      </table>
    </div>
    <div>
      <h3>📐 联赛诊断</h3>
      <p>VMR: {diag['vmr']:.2f} — {diag['vmr_conclusion']}</p>
      <p>主力模型: {diag['primary_model']}</p>
      <p>零膨胀: {diag['zip_conclusion']}</p>
      <p>场均进球: {diag['avg_goals']:.2f}</p>
    </div>
    <div>
      <h3>💰 赔率与EV</h3>
      <p>原始: {info['odds']['home']:.2f} / {info['odds']['draw']:.2f} / {info['odds']['away']:.2f}</p>
      <p>抽水: {odds['margin']:.2f}%</p>
      <p>Shin z: {odds['shin'].get('z', 0):.3f}</p>
      <p>EV: {' | '.join(ev_lines)}</p>
    </div>
  </div>
  <div style="margin-top:12px;font-size:12px;color:var(--text2)">
    <p>🔄 模型分歧: {' | '.join(div_lines)}</p>
    <p>🏔️ 高山验证: {gaoshan_text}</p>
  </div>
</div>'''

    def _parlay_section(self, parlay):
        """串关建议区域"""
        sections = []

        for ptype, label, css_class in [
            ('conservative', '稳健型', 'conservative'),
            ('balanced', '平衡型', 'balanced'),
            ('aggressive', '激进型', 'aggressive'),
        ]:
            suggestions = parlay.get(ptype, [])
            if not suggestions:
                continue

            for sug in suggestions:
                matches_html = '<br>'.join(
                    f"• {m['match_id']} {m['match']} → <strong>{m['direction']}</strong> ({m['probability']:.1%}, 赔{m['odds']:.2f})"
                    for m in sug['matches']
                )
                note = sug.get('note', '')
                note_html = f'<p style="color:var(--text2);font-size:12px;margin-top:4px">{note}</p>' if note else ''

                sections.append(f'''
<div class="parlay-card {css_class}">
  <strong>{label} {sug['type']}</strong>
  <span class="badge badge-{css_class}" style="margin-left:8px">{sug['risk_level']}风险</span>
  <div style="margin:8px 0;font-size:13px">{matches_html}</div>
  <p>组合概率: <strong>{sug['combined_prob']:.1%}</strong> | 组合赔率: <strong>{sug['combined_odds']:.2f}</strong></p>
  {note_html}
</div>''')

        if not sections:
            sections.append('<p style="color:var(--text2)">暂无符合条件的串关建议</p>')

        return f'''
<div class="card">
  <div class="card-title">🔗 串关建议</div>
  {''.join(sections)}
</div>'''

    def _divergence_section(self, alerts):
        """分歧预警区域"""
        if not alerts:
            return ''

        alert_cards = []
        for alert in alerts:
            alert_cards.append(f'''
<div class="divergence-alert">
  <strong>{alert['match_id']}</strong> {alert['match']} — {alert['direction']}<br>
  模型概率: {alert['model_prob']:.1%} vs 市场概率(Shin): {alert['market_prob']:.1%}<br>
  分歧幅度: <strong style="color:var(--danger)">{alert['divergence']:+.1%}</strong>
</div>''')

        return f'''
<div class="card">
  <div class="card-title">⚠️ 模型与市场严重分歧预警</div>
  {''.join(alert_cards)}
  <p style="font-size:12px;color:var(--text2);margin-top:8px">当模型与市场概率差&gt;15%时，该方向不确定性极高，仅适合极小注娱乐。</p>
</div>'''

    def _gaoshan_section(self):
        """高山流水统计区域"""
        gs = self.data.get('gaoshan_summary', {})
        top_leagues = gs.get('top_leagues', [])
        league_rows = ''.join(
            f'<tr><td>{name}</td><td>{data["total"]}</td><td>{data["accuracy"]:.1%}</td></tr>'
            for name, data in top_leagues[:5]
        )

        return f'''
<div class="card">
  <div class="card-title">🏔️ 高山流水参考源统计</div>
  <p style="font-size:13px;color:var(--text2);margin-bottom:12px">
    总样本: {gs.get('total_matches', 0)}场 | 
    有方向预测: {gs.get('total_with_sport', 0)}场 | 
    整体方向命中率: {gs.get('overall_direction_accuracy', 0):.1%}
  </p>
  <table style="font-size:12px">
    <thead><tr><th>联赛</th><th>样本量</th><th>方向命中率</th></tr></thead>
    <tbody>{league_rows}</tbody>
  </table>
</div>'''

    def _footer(self):
        """页脚"""
        return '''
<div style="text-align:center;padding:24px;color:var(--text2);font-size:12px;border-top:1px solid var(--border);margin-top:24px">
  <p>⚠️ 风险提示：足球比赛存在极大不确定性，任何模型预测均非100%准确</p>
  <p>模型基于历史数据，突发因素（红牌、点球、天气等）无法完全预测</p>
  <p>理性看待预测，切勿沉迷赌博</p>
</div>
</div>
</body>
</html>'''
