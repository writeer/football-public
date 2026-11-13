// Sports Mole 赛前预览抓取（伤停/预计首发）+ wttr.in 天气
const fs = require('fs');
const H = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' };
async function txt(url) { const r = await fetch(url, { headers: H }); return { status: r.status, body: await r.text() }; }
function strip(html) {
  return html.replace(/<script[\s\S]*?<\/script>/gi, ' ').replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, '\n').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"').replace(/[ \t]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();
}
(async () => {
  const idx = ['https://www.sportsmole.co.uk/football/uefa-nations-league/team-news/',
    'https://www.sportsmole.co.uk/football/international-friendlies/team-news/',
    'https://www.sportsmole.co.uk/football/international-friendlies/team-news/page-2.html'];
  const links = new Set();
  let idxEvidence = [];
  for (const u of idx) {
    const r = await txt(u);
    idxEvidence.push({ url: u, status: r.status, len: r.body.length, previews: (r.body.match(/href="[^"]*preview[^"]*"/g) || []).length });
    for (const m of r.body.match(/href="([^"]*preview[^"]*)"/g) || []) {
      const href = m.replace(/^href="/, '').replace(/"$/, '');
      if (href.includes('prediction-team-news-lineups')) links.add('https://www.sportsmole.co.uk' + href);
    }
  }
  const all = [...links];
  fs.writeFileSync('reports/data/20261113_sm_index_evidence.json', JSON.stringify({ idxEvidence, total: all.length, links: all }, null, 1), 'utf8');
  console.log('preview links total', all.length);
  const want = {
    'moldova-vs-kazakhstan': 'Moldova vs Kazakhstan',
    'bulgaria-vs-iceland': 'Bulgaria vs Iceland',
    'luxembourg-vs-estonia': 'Luxembourg vs Estonia',
    'netherlands-vs-greece': 'Netherlands vs Greece',
    'scotland-vs-n-macedonia': 'Scotland vs North Macedonia',
    'serbia-vs-germany': 'Serbia vs Germany',
    'slovakia-vs-faroe-islands': 'Slovakia vs Faroe Islands',
    'slovenia-vs-switzerland': 'Slovenia vs Switzerland',
    'singapore-vs-paraguay': 'Singapore vs Paraguay',
    'argentina-vs-uruguay': 'Argentina vs Uruguay',
    'colombia-vs-chile': 'Colombia vs Chile',
  };
  const out = {};
  for (const key of Object.keys(want)) {
    const hit = all.find(u => u.includes(key));
    if (!hit) { out[key] = { found: false, evidence: 'index pages scanned: ' + all.length + ' preview links, no slug match' }; console.log('MISS', key); continue; }
    const r = await txt(hit);
    const plain = strip(r.body);
    fs.writeFileSync(`reports/data/raw_sm_${key}.txt`, plain, 'utf8');
    const grab = (from, to, max) => {
      const i = plain.indexOf(from); if (i < 0) return '';
      const j = to ? plain.indexOf(to, i + from.length) : -1;
      return plain.slice(i, j > 0 ? j : i + (max || 2500)).slice(0, max || 2500);
    };
    const teamNews = grab('Team News', 'Predicted Lineups', 3000) || grab('TEAM NEWS', 'PREDICTED', 3000);
    const lineups = grab('Predicted Lineups', 'We say', 1200) || grab('PREDICTED LINEUPS', 'We say', 1200) || grab('PREDICTED LINEUPS', 'Prediction', 1200);
    const pred = grab('We say', 'Data Analysis', 900) || grab('Prediction', 'Data Analysis', 900);
    out[key] = { found: true, url: hit, status: r.status, teamNews, lineups, pred };
    console.log('OK', key, r.status, 'teamNews', teamNews.length, 'lineups', lineups.length);
  }
  fs.writeFileSync('reports/data/20261113_sm_previews.json', JSON.stringify(out, null, 1), 'utf8');

  // 天气
  const cities = ['Chisinau', 'Plovdiv', 'Luxembourg', 'Amsterdam', 'Glasgow', 'Belgrade', 'Kosice', 'Maribor', 'Singapore', 'Buenos+Aires', 'Cali'];
  const wx = {};
  for (const c of cities) {
    try {
      const r = await fetch(`https://wttr.in/${c}?format=j1`, { headers: H });
      const d = JSON.parse(await r.text());
      const near = (d.weather || []).filter(w => ['2026-11-13', '2026-11-14'].includes(w.date));
      wx[c] = {
        status: r.status,
        current: { temp_C: d.current_condition[0].temp_C, feels: d.current_condition[0].FeelsLikeC, desc: d.current_condition[0].weatherDesc[0].value, wind: d.current_condition[0].windspeedKmph, humidity: d.current_condition[0].humidity, observed: d.current_condition[0].localObsDateTime },
        days: near.map(w => ({ date: w.date, maxC: w.maxtempC, minC: w.mintempC, totalSnow: w.totalSnow_cm, sunHour: w.sunHour, hourly: (w.hourly || []).filter(h => ['0', '300', '600', '900', '1200', '1500', '1800', '2100'].includes(h.time)).map(h => ({ time: h.time, tempC: h.tempC, desc: h.weatherDesc[0].value, rainChance: h.chanceofrain, wind: h.windspeedKmph })) })),
      };
      console.log('WX', c, r.status, near.map(x => x.date + ' ' + x.maxtempC + '/' + x.mintempC).join(' | '));
    } catch (e) { wx[c] = { error: e.message }; console.log('WX ERR', c, e.message); }
  }
  fs.writeFileSync('reports/data/20261113_weather.json', JSON.stringify(wx, null, 1), 'utf8');
})().catch(e => { console.error(e); process.exit(1); });
