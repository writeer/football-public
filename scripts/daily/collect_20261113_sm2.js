const fs = require('fs');
const H = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' };
function strip(html) {
  return html.replace(/<script[\s\S]*?<\/script>/gi, ' ').replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, '\n').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"').replace(/[ \t]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();
}
(async () => {
  const page = await (await fetch('https://www.sportsmole.co.uk/football/argentina/', { headers: H })).text();
  const links = [...new Set((page.match(/href="[^"]*preview[^"]*"/g) || []).map(s => s.slice(6, -1)))];
  console.log('ARG preview links:', links.slice(0, 12).join('\n'));
  const uy = links.filter(l => /uruguay/i.test(l));
  console.log('URUGUAY hits:', uy);
  const existing = JSON.parse(fs.readFileSync('reports/data/20261113_sm_previews.json', 'utf8'));
  const targets = {
    'singapore-vs-paraguay': 'https://www.sportsmole.co.uk/football/singapore/preview/singapore-vs-paraguay-prediction-team-news-lineups_608909.html',
    'colombia-vs-chile': 'https://www.sportsmole.co.uk/football/colombia/preview/colombia-vs-chile-prediction-team-news-lineups_608950.html',
  };
  if (uy.length) targets['argentina-vs-uruguay'] = 'https://www.sportsmole.co.uk' + uy[0];
  for (const [k, u] of Object.entries(targets)) {
    const r = await fetch(u, { headers: H });
    const t = strip(await r.text());
    fs.writeFileSync(`reports/data/raw_sm_${k}.txt`, t, 'utf8');
    const i = t.indexOf('Team News');
    existing[k] = { found: true, url: u, status: r.status, teamNews: t.slice(i > 0 ? i : 0, (i > 0 ? i : 0) + 2600) };
    console.log('====', k, r.status, '====');
    console.log(existing[k].teamNews.slice(0, 2200));
    console.log();
  }
  fs.writeFileSync('reports/data/20261113_sm_previews.json', JSON.stringify(existing, null, 1), 'utf8');
})();
