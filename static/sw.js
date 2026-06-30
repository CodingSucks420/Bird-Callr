const CACHE_NAME = 'bird-callr-cache-v1';
const urlsToCache = [
  './',
  './manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        // Failing to cache one file won't fail the whole install if we catch it, 
        // but for simplicity we just try to add the core files.
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  // We only cache our own local static assets
  if (event.request.url.includes('xeno-canto.org') || event.request.url.includes('wikipedia.org')) {
    return; 
  }
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
