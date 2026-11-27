// node simrun.js <reps> <out.json> : every ordered faction pair x 3 maps x {normal,hard}, reps each, 4 pages in parallel
const {chromium}=require('playwright');const fs=require('fs');
const D2=(process.env.DIFFS||'normal,hard').split(',');const F=['djinn','verdant','mutant','knight','goblin','undead','auto','dragon'],M=['dunes','bridge','volcano'],D=['normal','hard'];
const reps=+process.argv[2]||1,outF=process.argv[3]||'simres.json';
const jobs=[];for(let r=0;r<reps;r++)for(const a of F)for(const b of F)if(a!==b)for(const m of M)for(const d of D2)jobs.push([a,b,m,d]);
(async()=>{const t0=Date.now();const res=[];let next=0;
 const worker=async()=>{const br=await chromium.launch();const p=await br.newPage();await p.goto('file://'+require('path').resolve(__dirname,'../index.html'));await p.waitForTimeout(1200);
   while(true){const i=next;next+=6;if(i>=jobs.length)break;const batch=jobs.slice(i,i+6);
     const r=await p.evaluate(B=>B.map(([a,b,m,d])=>{const x=window.__sky.sim(a,d,true,b,m);return {a,b,m,d,win:x.win,why:x.why,t:x.t,an:x.a.map(v=>Math.round(v)),w:x.w}}),batch);res.push(...r);
     fs.writeFileSync(outF,JSON.stringify(res));if(res.length%60<6)process.stderr.write(res.length+'/'+jobs.length+' '+((Date.now()-t0)/1000|0)+'s\n')}
   await br.close()};
 await Promise.all([worker(),worker(),worker(),worker()]);fs.writeFileSync(outF,JSON.stringify(res));console.log('done',res.length,((Date.now()-t0)/1000|0)+'s')})();
