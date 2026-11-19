// Balance check for lane-prototype.html: every faction pairing, AI vs AI, headless.
// Usage: node tools/lane_balance.js [gamesPerPairing=5] [easy|normal|hard]   (needs playwright)
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + e.message + '\n' + e.stack));
  await p.goto('file://' + require('path').resolve(__dirname, '../lane-prototype.html'));
  await p.waitForTimeout(500);
  const N = +(process.argv[2] || 2), lvl = process.argv[3] || 'normal';
  const res = await p.evaluate(({N, lvl}) => {
    const F = Object.keys(SKY.FACTIONS), out = {}, wins = {}, games = {}, all = [];
    F.forEach(f => { wins[f] = 0; games[f] = 0; });
    let seed = 1;
    const t0 = performance.now();
    for (const a of F) for (const bb of F) {
      if (a === bb) continue;
      for (let i = 0; i < N; i++) {
        const r = SKY.simMatch(a, bb, seed++, 900, lvl);
        games[a]++; games[bb]++;
        if (r.winner === 0) wins[a]++; else if (r.winner === 1) wins[bb]++;
        all.push([a, bb, r.winner, r.t, r.peak, r.hp.join('/'), r.kills.join('/')]);
      }
    }
    return { wins, games, all, ms: performance.now() - t0 };
  }, {N, lvl});
  for (const r of res.all) console.log(r.join('\t'));
  for (const f in res.wins) console.log(f, res.wins[f] + '/' + res.games[f], (100 * res.wins[f] / res.games[f]).toFixed(0) + '%');
  const ts = res.all.map(r => r[3]); console.log('avg t', (ts.reduce((a, b) => a + b, 0) / ts.length).toFixed(0), 'draws', res.all.filter(r => r[2] === -1).length, 'ms', res.ms.toFixed(0));
  console.log('errors:', errs.join('\n') || 'none');
  await b.close();
})();
