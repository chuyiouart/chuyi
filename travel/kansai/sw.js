const prefix = "ouart-kansai-travel-";
const cacheName = prefix + "5868d6c725a24a06";
const files = ["index.html","editorial.css","editorial.js","trip-editorial.enc.json","assets/lucua-access.webp","assets/lucua-10f.webp","assets/lucua-11f.webp","assets/lucua-12f.webp","assets/lucua-13f.webp","assets/sky-christmas.webp","assets/tools-access.webp","assets/daruma-entry.webp","assets/kawachi-entry.webp","assets/sky-tree.webp","assets/autumn-cover.webp","assets/kyoto-night.webp","assets/otagi-rakan.webp","assets/uji-koshoji.webp","assets/nintendo-entrance.webp","assets/teamlab-preview.webp","assets/wyeth-preview.webp","assets/tools-entry.webp","assets/lucua-south-entry.webp","assets/yodobashi-entry.webp","assets/cosme-entry.webp","assets/marimekko-entry.webp"];
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
    event.respondWith(caches.open(cacheName).then(cache => cache.match(name)).then(found => found || fetch(event.request)));
  }
});
