// SKYJINN offline cache. Bump VERSION whenever index.html changes.
const VERSION='skyjinn-v33';
const FILES=['./','./index.html','./manifest.json','./icon-192.png','./icon-512.png',
  './audio/music_menu.mp3','./audio/music_desert.mp3','./audio/music_bridge.mp3','./audio/music_volcano.mp3','./audio/sting_victory.mp3','./audio/sting_defeat.mp3'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(VERSION).then(c=>c.addAll(FILES)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==VERSION).map(k=>caches.delete(k)))));self.clients.claim()});
// Network first so updates show up when online; cache when offline.
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;
  e.respondWith(fetch(e.request).then(r=>{if(r.status===200){const c=r.clone();caches.open(VERSION).then(x=>x.put(e.request,c))}return r}).catch(()=>caches.match(e.request,{ignoreSearch:true}).then(r=>r||caches.match('./index.html'))))});
