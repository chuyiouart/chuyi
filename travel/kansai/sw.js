const prefix = "ouart-kansai-travel-";
const cacheName = prefix + "28b6f341c745461a";
const files = ["index.html","journey.css","journey.js","trip-transport.enc.json","assets/lucua-access.webp","assets/lucua-10f.webp","assets/lucua-11f.webp","assets/lucua-12f.webp","assets/lucua-13f.webp","assets/sky-christmas.webp","assets/tools-access.webp","assets/daruma-entry.webp","assets/kawachi-entry.webp","assets/sky-tree.webp","assets/kyoto-night.webp","assets/otagi-rakan.webp","assets/uji-koshoji.webp","assets/nintendo-entrance.webp","assets/teamlab-preview.webp","assets/wyeth-preview.webp","assets/tools-entry.webp","assets/lucua-south-entry.webp","assets/yodobashi-entry.webp","assets/cosme-entry.webp","assets/marimekko-entry.webp","assets/nintendo-route.webp","assets/kyoto-platforms.webp","assets/dining-kix-sukiya.webp","assets/dining-kix-kamukura.webp","assets/dining-kix-551.webp","assets/dining-todai.webp","assets/dining-toyotei.webp","assets/dining-uogashi.webp","assets/dining-ine.webp","assets/dining-yoshimura.webp","assets/dining-iwawo.webp","assets/dining-takamatsu.webp","assets/dining-hashitate.webp","assets/dining-izasa.webp","assets/dining-hiraso.webp","assets/dining-ganko.webp","assets/dining-letemps.webp","assets/dining-moritaya.webp","assets/dining-ito.webp","assets/dining-nakamura.webp","assets/dining-katsusen.webp","assets/dining-mimiu.webp","assets/dining-daruma.webp","assets/dining-romantei.webp","assets/dining-hokkyokusei-lucua.webp","assets/dining-hokkyokusei-main.webp","assets/dining-harijyu.webp","assets/dining-sukiya-upper.webp","assets/dining-benitora.webp","assets/dining-fukutaro.webp","assets/dining-fascino.webp","assets/dining-obon.webp","assets/dining-daiki.webp","assets/dining-kyk.webp","assets/dining-yaekatsu.webp","assets/dining-moriya.webp","assets/dining-tonsho.webp","assets/dining-mensho.webp","assets/dining-kamukura-premium.webp","assets/dining-onigiri-burger.webp","assets/dining-kiji.webp","assets/ayao-kansai-hero-v4.webp","assets/ayao-ui-atlas.webp","assets/ayao-app-icon.webp","assets/nara-deer.webp","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png","icons/maskable-512.png","icons/apple-touch-icon.png","icons/favicon-32.png"];
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(cacheName).then(cache => cache.addAll(files)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith(prefix) && key !== cacheName).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const scope = new URL(self.registration.scope);
  if (event.request.method !== "GET" || url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
  const name = url.pathname.slice(scope.pathname.length);
  if (event.request.mode === "navigate" && (name === "" || name === "index.html")) {
    event.respondWith(fetch(event.request).catch(() => caches.open(cacheName).then(cache => cache.match("index.html"))));
  } else if (files.includes(name)) {
    if (["journey.js","journey.css","trip-transport.enc.json"].includes(name)) {
      event.respondWith(fetch(event.request).then(response=>{if(!response.ok)throw new Error("network response");return response;}).catch(()=>caches.open(cacheName).then(cache=>cache.match(name))));
    } else event.respondWith(caches.open(cacheName).then(cache => cache.match(name)).then(found => found || fetch(event.request)));
  }
});
