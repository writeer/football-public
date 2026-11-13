const fs = require('fs');
const path = require('path');
const leagueDir = 'e:\\VibeCoding\\football\\memory\\leagues\\';
const leagues = ['j_league_jp.json','k_league_kr.json','efl_championship_en.json','eredivisie_nl.json','premier_league_en.json','serie_a_it.json','ligue_1_fr.json','bundesliga_de.json','la_liga_es.json','primeira_liga_pt.json','eliteserien_no.json','serie_a_br.json'];

leagues.forEach(file => {
  const fp = path.join(leagueDir, file);
  const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
  const li = data.league_info || {};
  const st = data.statistics || {};
  const ms = data.match_style || {};
  console.log(`\n=== ${file} ===`);
  console.log('name:', li.name || li.league_name || li.full_name || 'N/A');
  console.log('ht_draw_rate:', li.ht_draw_rate || st.ht_draw_rate || 'N/A');
  console.log('home_adv:', st.home_advantage || st.home_win_rate || 'N/A');
  console.log('draw_rate:', st.draw_rate || 'N/A');
  console.log('avg_goals:', st.avg_goals || st.average_goals || 'N/A');
  console.log('top5:', JSON.stringify(st.top5_scores || st.top_scores || st.most_common_scores || 'N/A'));
  console.log('style:', ms.style || ms.playing_style || ms.tactical_style || 'N/A');
  // print statistics keys
  console.log('stat_keys:', Object.keys(st).join(', '));
  console.log('info_keys:', Object.keys(li).join(', '));
});
