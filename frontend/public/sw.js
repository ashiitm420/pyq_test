const CACHE_NAME = 'mauryahub-static-v1';
const STATIC_ASSET_RE = /^\/(?:assets\/[^/]+-[A-Za-z0-9_-]{8,}\.(?:js|css|woff2?|ttf)|favicon\.svg|icon-(?:192|512)\.png|study\.css|study-theme\.js)$/;

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || !STATIC_ASSET_RE.test(url.pathname)) return;
  event.respondWith(
    caches.open(CACHE_NAME).then(async cache => {
      const cached = await cache.match(req);
      if (cached) return cached;
      const response = await fetch(req);
      if (response && response.status === 200 && response.type === 'basic') {
        cache.put(req, response.clone());
      }
      return response;
    })
  );
});
