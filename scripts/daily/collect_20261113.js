// 2026-11-13 销售日：采集 ESPN 场次/场馆/伤停/大名单 + 欧国联积分榜 + Elo + 天气
const fs = require('fs');
const HDR = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' };

async function get(url) {
  const r = await fetch(url, { headers: HDR, redirect: 'follow' });
  const t = await r.text();
  let d = null; try { d = JSON.parse(t); } catch (e) {}
  return { status: r.status, text: t, data: d };
}
function statMap(entry) {
  const o = {};
  for (const s of entry.stats || []) o[s.name] = s.value;
  return o;
}
const NAME_MAP = {
  'Moldova': '摩尔多瓦', 'Kazakhstan': '哈萨克斯坦', 'Bulgaria': '保加利亚', 'Iceland': '冰岛',
  'Scotland': '苏格兰', 'North Macedonia': '北马其顿', 'Serbia': '塞尔维亚', 'Germany': '德国',
  'Luxembourg': '卢森堡', 'Estonia': '爱沙尼亚', 'Slovakia': '斯洛伐克', 'Faroe Islands': '法罗群岛',
  'Slovenia': '斯洛文尼亚', 'Switzerland': '瑞士', 'Netherlands': '荷兰', 'Greece': '希腊',
  'Singapore': '新加坡', 'Paraguay': '巴拉圭', 'Argentina': '阿根廷', 'Uruguay': '乌拉圭',
  'Colombia': '哥伦比亚', 'Chile': '智利',
};
const ELO_CODE = {
  'Moldova': 'MD', 'Kazakhstan': 'KZ', 'Bulgaria': 'BG', 'Iceland': 'IS', 'Scotland': 'SC',
  'North Macedonia': 'MK', 'Serbia': 'RS', 'Germany': 'DE', 'Luxembourg': 'LU', 'Estonia': 'EE',
  'Slovakia': 'SK', 'Faroe Islands': 'FO', 'Slovenia': 'SI', 'Switzerland': 'CH', 'Netherlands': 'NL',
  'Greece': 'GR', 'Singapore': 'SG', 'Paraguay': 'PY', 'Argentina': 'AR', 'Uruguay': 'UY',
  'Colombia': 'CO', 'Chile': 'CL',
};

(async () => {
  const out = { fetchedAt: new Date().toISOString(), standings: {}, events: [], elo: {}, weather: {} };

  // 1) 欧国联积分榜
  const st = await get('https://site.api.espn.com/apis/v2/sports/soccer/uefa.nations/standings');
  fs.writeFileSync('reports/data/20261113_espn_nations_standings_raw.json', st.text, 'utf8');
  if (st.data) {
    for (const g of st.data.children || []) {
      const gname = g.name;
      for (const e of (g.standings && g.standings.entries) || []) {
        const s = statMap(e);
        out.standings[e.team.displayName] = {
          group: gname, rank: (e.note && e.note.rank) || null,
          gp: s.gamesPlayed, w: s.wins, d: s.ties, l: s.losses,
          gf: s.pointsFor, ga: s.pointsAgainst, gd: s.pointDifferential,
          pts: s.points, rankNote: (e.note && e.note.description) || '',
        };
      }
    }
  }

  // 2) Elo
  const elo = await get('https://www.eloratings.net/World.tsv');
  fs.writeFileSync('reports/data/20261113_elo_world.tsv', elo.text, 'utf8');
  const want = Object.values(ELO_CODE);
  for (const line of elo.text.split('\n')) {
    const c = line.split('\t');
    if (c.length < 4) continue;
    const code = c[2];
    if (want.includes(code)) out.elo[code] = { rank: Number(c[0]), rating: Number(c[3]) };
  }

  // 3) 场次（欧国联 11-13 + 国际赛 11-13/14）
  const boards = [
    ['uefa.nations', '20261113'], ['fifa.friendly', '20261113'], ['fifa.friendly', '20261114'],
  ];
  const events = [];
  for (const [league, date] of boards) {
    const r = await get(`https://site.api.espn.com/apis/site/v2/sports/soccer/${league}/scoreboard?dates=${date}`);
    fs.writeFileSync(`reports/data/20261113_espn_${league.replace('.', '_')}_${date}_raw.json`, r.text, 'utf8');
    for (const e of (r.data && r.data.events) || []) {
      const comp = e.competitions && e.competitions[0];
      if (!comp) continue;
      const cs = comp.competitors || [];
      const home = cs.find(c => c.homeAway === 'home');
      const away = cs.find(c => c.homeAway === 'away');
      if (!home || !away) continue;
      const venue = comp.venue || {};
      events.push({
        league, date, id: e.id, name: e.name, kickoff: e.date, status: (e.status && e.status.type && e.status.type.description) || '',
        homeName: home.team.displayName, awayName: away.team.displayName,
        homeId: home.team.id, awayId: away.team.id,
        venue: venue.fullName || '', city: (venue.address && venue.address.city) || '', country: (venue.address && venue.address.country) || '',
        attendance: venue.capacity || null,
        broadcasts: (comp.broadcasts || []).flatMap(b => b.names || []).join('/'),
      });
    }
  }
  const wanted = ['Moldova', 'Bulgaria', 'Scotland', 'Serbia', 'Luxembourg', 'Slovakia', 'Slovenia', 'Netherlands', 'Singapore', 'Argentina', 'Colombia'];
  const picked = events.filter(e => wanted.includes(e.homeName));
  out.events = picked;
  fs.writeFileSync('reports/data/20261113_espn_events.json', JSON.stringify(out.events, null, 1), 'utf8');
  console.log('standings teams:', Object.keys(out.standings).length, 'elo:', Object.keys(out.elo).length, 'events picked:', picked.length);
  for (const e of picked) console.log(e.league, e.id, e.homeName, 'vs', e.awayName, '|', e.venue, ',', e.city, ',', e.country, '|', e.kickoff);
  fs.writeFileSync('reports/data/20261113_collect_base.json', JSON.stringify(out, null, 1), 'utf8');
})();
