/**
 * Service Worker for The Independent Archipelago
 * Manages intelligent caching with automatic updates
 */

const CACHE_VERSION = "archipelago-v1";
const CACHE_NAME = `${CACHE_VERSION}-${new Date().toISOString().split("T")[0]}`;
const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/css/style.css",
  "/js/app.js",
  "/favicon.png",
];

const DATA_URLS = ["/data/games.json", "/data/users.json"];

// Files to never cache
const NO_CACHE = ["data/games.json", "data/users.json"];

/**
 * Install event - cache static assets
 */
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        // Fail silently if some assets aren't available
        console.warn("Some static assets could not be cached");
      });
    }),
  );
  // Skip waiting to activate immediately
  self.skipWaiting();
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete old caches (not the current version)
          if (!cacheName.startsWith(CACHE_VERSION)) {
            return caches.delete(cacheName);
          }
        }),
      );
    }),
  );
  // Claim all clients
  self.clients.claim();
});

/**
 * Fetch event - implement stale-while-revalidate strategy
 */
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and external APIs
  if (request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  // For data files: network-first with cache fallback
  if (DATA_URLS.some((dataUrl) => url.pathname.includes(dataUrl))) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful responses
          if (response && response.status === 200) {
            const responseToCache = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          // Return cached version if network fails
          return caches.match(request);
        }),
    );
    return;
  }

  // For other assets: cache-first with network fallback
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // Return cached but check for updates in background
        fetch(request)
          .then((response) => {
            if (response && response.status === 200) {
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(request, response.clone());
              });
              // Notify clients of update (for data files)
              self.clients.matchAll().then((clients) => {
                clients.forEach((client) => {
                  client.postMessage({
                    type: "CACHE_UPDATED",
                    url: request.url,
                  });
                });
              });
            }
          })
          .catch(() => {
            // Silently fail background update
          });
        return cachedResponse;
      }

      // No cache, fetch from network
      return fetch(request).catch(() => {
        // Return a custom offline page if needed
        return new Response("Offline - cached content unavailable", {
          status: 503,
          statusText: "Service Unavailable",
          headers: new Headers({
            "Content-Type": "text/plain",
          }),
        });
      });
    }),
  );
});

/**
 * Message handler for manual cache clearing
 */
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "CLEAR_CACHE") {
    caches.keys().then((cacheNames) => {
      cacheNames.forEach((cacheName) => {
        caches.delete(cacheName);
      });
    });
  }
});
