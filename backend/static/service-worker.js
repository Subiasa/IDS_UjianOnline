const CACHE_NAME = 'hids-agent-v2';
const ASSETS = [
    './',
    './index.html',
    './api.js',
    './sensors.js',
    './ui.js',
    './manifest.json'
];

self.addEventListener('install', (event) => {
    // Skip waiting to activate immediately
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log("Caching assets...");
            return cache.addAll(ASSETS);
        })
    );
});

self.addEventListener('activate', (event) => {
    // Clean up old caches
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    // Cache-first strategy for static assets
    if (event.request.method !== 'GET' || event.request.url.includes('/api/v1/')) {
        // Do not cache API requests
        return fetch(event.request);
    }
    
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            // Fallback to network
            return fetch(event.request).then((networkResponse) => {
                // Optionally cache the new response here
                return networkResponse;
            });
        })
    );
});
