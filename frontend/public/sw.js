const CACHE_NAME = 'graftai-offline-v1';

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
  '/',
  '/login',
  '/dashboard',
  '/icon.png',
  '/favicon.ico',
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('📦 [SW] Pre-caching application shell...');
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🧹 [SW] Cleaning up old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Only handle GET requests for navigation and assets
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Skip API calls (handled by Dexie/Offline hooks)
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/auth')) return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      // If not in cache, try network and then cache the result (Stale-While-Revalidate style)
      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }

        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return networkResponse;
      }).catch(() => {
        // Offline Fallback for Page Navigations
        if (event.request.mode === 'navigate') {
          return caches.match('/dashboard') || caches.match('/login');
        }
      });
    })
  );
});
