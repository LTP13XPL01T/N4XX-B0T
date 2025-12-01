// Service Worker untuk PWA: Caching aset statis dan strategi offline
const CACHE_NAME = 'h2a-v1';
const urlsToCache = [
    '/',
    '/index.html',
    '/about.html',
    '/services.html',
    '/contact.html',
    '/blog.html',
    '/style.css',
    '/script.js',
    '/manifest.json',
    '/img/logo.png',
    '/img/hero.jpg',
    '/img/about.jpg',
    '/img/service1.jpg',
    '/img/service2.jpg',
    '/img/service3.jpg',
    '/img/blog1.jpg',
    '/img/blog2.jpg',
    '/img/logo-192.png',
    '/img/logo-512.png'
];

// Install: Cache aset statis
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

// Fetch: Strategi cache-first untuk aset statis, network-first untuk data dinamis (e.g., blog JSON jika ada)
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Cache aset statis
    if (urlsToCache.some(cachedUrl => url.pathname.includes(cachedUrl))) {
        event.respondWith(
            caches.match(event.request)
                .then(response => response || fetch(event.request))
        );
    } else {
        // Network-first untuk data dinamis, fallback ke cache
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }
                    // Clone dan cache response
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME)
                        .then(cache => cache.put(event.request, responseToCache));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
    }
});

// Activate: Hapus cache lama
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Push Notifications: Handle incoming pushes (butuh server setup)
self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'Update baru dari H2A!',
        icon: '/img/logo.png',
        badge: '/img/logo-192.png'
    };
    event.waitUntil(self.registration.showNotification('H2A Update', options));
});