// 逐场采集：伤停、大名单、近况、交锋 + 场馆天气
const fs = require('fs');
const HDR = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' };
async function get(url) { const r = await fetch(url, { headers: HDR, redirect: 'follow' }); const t = await r.text(); let d = null; try { d = JSON.parse(t); } catch (e) {} return { status: r.status, text: t, data: d }; }

(async () => {
const base = JSON.parse(fs.readFileSync('reports/data/20261113_collect_base.json', 'utf8'));
const detail = {};
for (const ev of base.events) {
  const url = `https://site.api.espn.com/apis/site/v2/sports/soccer/${ev.league}/summary?event=${ev.id}`;
  const r = await get(url);
  fs.writeFileSync(`reports/data/raw_espn_summary_${ev.id}.json`, r.text, 'utf8');
  const d = r.data || {};
  const inj = [];
  for (const t of d.injuries || []) {
    for (const i of t.injuries || []) {
      inj.push({
        team: (t.team && (t.team.displayName || t.team.name)) || '',
        athlete: (i.athlete && i.athlete.displayName) || '', position: (i.athlete && i.athlete.position && i.athlete.position.abbreviation) || '',
        status: i.status || '', date: i.date || '', detail: i.detail || i.longComment || '',
      });
    }
  }
  const rosters = [];
  for (const t of d.rosters || []) {
    rosters.push({
      team: (t.team && t.team.displayName) || '',
      count: (t.roster || []).length,
      players: (t.roster || []).slice(0, 0),
    });
  }
  const form = [];
  for (const t of d.form || []) {
    form.push({ team: (t.team && t.team.displayName) || '', games: (t.events || []).slice(0, 8).map(x => ({ date: x.gameDate, opp: (x.opponent && x.opponent.displayName) || '', score: x.score || '', result: x.gameResult || '', comp: (x.leagueName || x.competitionName) || '' })) });
  }
  const h2h = [];
  for (const g of ((d.headToHead && d.headToHead.games) || []).slice(0, 8)) {
    const e = g || {};
    h2h.push({ date: e.gameDate, name: e.name, score: e.score, comp: (e.leagueName || e.competitionName) || '' });
  }
  detail[ev.id] = { name: ev.name, league: ev.league, venue: ev.venue, city: ev.city, country: ev.country, kickoff: ev.kickoff, injuries: inj, rosters, form, h2h, summaryKeys: Object.keys(d) };
  console.log(ev.id, ev.homeName, 'vs', ev.awayName, '| inj:', inj.length, '| rosterTeams:', rosters.map(x => x.team + ':' + x.count).join(','), '| formTeams:', form.length, '| h2h:', h2h.length);
  console.log('   injuries:', inj.slice(0, 6).map(i => `${i.team}/${i.athlete}/${i.position}/${i.status}/${i.date}`).join(' ; ') || 'none');
  console.log('   form:', JSON.stringify(form).slice(0, 500));
}
fs.writeFileSync('reports/data/20261113_espn_detail.json', JSON.stringify(detail, null, 1), 'utf8');

// 天气：Open-Meteo（城市 -> 经纬度 -> 当日/次日逐小时）
const cities = [...new Set(base.events.map(e => e.city))];
const wx = {};
for (const city of cities) {
  const g = await get(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=en&format=json`);
  const loc = g.data && g.data.results && g.data.results[0];
  if (!loc) { wx[city] = { error: `geocoding no result (HTTP ${g.status})` }; console.log('WX FAIL', city, g.status); continue; }
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${loc.latitude}&longitude=${loc.longitude}&hourly=temperature_2m,precipitation_probability,wind_speed_10m,weather_code&timezone=auto&start_date=2026-11-13&end_date=2026-11-14`;
  const w = await get(url);
  if (!w.data) { wx[city] = { error: `forecast HTTP ${w.status}` }; console.log('WX FAIL2', city, w.status); continue; }
  wx[city] = { lat: loc.latitude, lon: loc.longitude, elev: loc.elevation, tz: w.data.timezone, hourly: w.data.hourly };
  console.log('WX OK', city, loc.latitude, loc.longitude, w.data.timezone);
}
fs.writeFileSync('reports/data/20261113_weather.json', JSON.stringify(wx, null, 1), 'utf8');

// 身价源探测（Transfermarkt 反爬验证，记录真实失败证据）
const tmTests = ['https://www.transfermarkt.com/singapore/startseite/verein/13967', 'https://www.transfermarkt.com/paraguay/startseite/verein/3581'];
for (const u of tmTests) {
  const r = await get(u);
  console.log('TM', r.status, u, 'len', r.text.length, /Access Denied|captcha|Cloudflare/i.test(r.text) ? 'BLOCKED' : 'ok?');
  fs.writeFileSync('reports/data/20261113_tm_probe.txt', `URL ${u}\nHTTP ${r.status}\nLEN ${r.text.length}\nHEAD ${r.text.slice(0, 300)}`, 'utf8');
}
})().catch(e => { console.error(e); process.exit(1); });
