// SKYJINN offline cache. Bump VERSION whenever index.html changes.
// Cache first: a return visit loads from this cache and downloads nothing. The browser re-checks this small file on
// each visit; a new VERSION downloads the game once in the background, then takes over (the page reloads on the menu).
const VERSION='skyjinn-v39';
const FILES=['./','./index.html','./manifest.json','./icon-192.png','./icon-512.png',
  './audio/music_menu.mp3','./audio/music_desert.mp3','./audio/music_bridge.mp3','./audio/music_volcano.mp3','./audio/sting_victory.mp3','./audio/sting_defeat.mp3'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(VERSION).then(c=>c.addAll(FILES.map(f=>new Request(f,{cache:'reload'})))));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
async function answer(q){const c=await caches.open(VERSION);
  const hit=await c.match(q,{ignoreSearch:true})||(q.mode==='navigate'?await c.match('./index.html'):null);if(hit)return hit;
  const r=await fetch(q);if(r.status===200)c.put(q,r.clone());return r}
self.addEventListener('fetch',e=>{const q=e.request;if(q.method!=='GET'||new URL(q.url).origin!==location.origin)return;e.respondWith(answer(q))});
