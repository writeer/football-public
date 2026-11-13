const fs = require('fs');
const path = require('path');

const leagueDir = 'e:\\VibeCoding\\football\\memory\\leagues\\';
const leagues = [
  'j_league_jp.json', 'k_league_kr.json', 'efl_championship_en.json',
  'eredivisie_nl.json', 'premier_league_en.json', 'serie_a_it.json',
  'ligue_1_fr.json', 'bundesliga_de.json', 'la_liga_es.json',
  'primeira_liga_pt.json', 'eliteserien_no.json', 'serie_a_br.json'
];

leagues.forEach(file => {
  const fp = path.join(leagueDir, file);
  if (!fs.existsSync(fp)) { console.log(`\n=== ${file} NOT FOUND ===`); return; }
  const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
  console.log(`\n=== ${file} ===`);
  console.log('League:', data.league_name || data.name || 'N/A');
  console.log('ht_draw_rate:', data.ht_draw_rate || 'N/A');
  console.log('home_advantage:', data.home_advantage || data.stats?.home_advantage || 'N/A');
  console.log('draw_rate:', data.draw_rate || data.stats?.draw_rate || 'N/A');
  console.log('avg_goals:', data.avg_goals || data.stats?.avg_goals || 'N/A');
  console.log('top5_scores:', JSON.stringify(data.top5_scores || data.stats?.top5_scores || 'N/A'));
  console.log('style:', data.playing_style || data.style || 'N/A');
  // Print all keys for reference
  console.log('keys:', Object.keys(data).join(', '));
});
