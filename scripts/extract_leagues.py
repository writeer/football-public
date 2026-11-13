import json, os

base = r'e:\VibeCoding\football\memory\leagues'
files = {
    '意甲': 'serie_a_it.json',
    '沙职': 'pro_league_sa.json',
    '瑞超': 'allsvenskan_se.json',
    '西甲': 'la_liga_es.json',
    '英超': 'premier_league_en.json',
    '法乙': 'ligue_2_fr.json',
    '葡超': 'primeira_liga_pt.json',
    '巴甲': 'serie_a_br.json',
}

for name, fn in files.items():
    path = os.path.join(base, fn)
    if not os.path.exists(path):
        print(f'[{name}] FILE NOT FOUND: {fn}')
        continue
    with open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    print(f'===== [{name}] {fn} =====')
    st = d.get('statistics', {})
    print('  avg_goals:', st.get('avg_goals_per_match'))
    print('  draw_rate:', st.get('draw_rate'))
    print('  home_win_rate:', st.get('home_win_rate'))
    print('  away_win_rate:', st.get('away_win_rate'))
    print('  over25_rate:', st.get('over_25_rate') or st.get('over25_rate'))
    print('  top5_scores:', st.get('top5_scores') or st.get('most_common_scores'))
    style = d.get('match_style', {})
    print('  style:', str(style.get('tactical_style',''))[:120])
    mkt = d.get('public_opinion_and_market', {})
    print('  cold_upset_freq:', mkt.get('cold_upset_frequency'))
    print('  notes:', str(mkt.get('lottery_notes',''))[:150])
    print()
