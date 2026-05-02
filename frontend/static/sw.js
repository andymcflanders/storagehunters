/**
 * StorageHub Service Worker
 * Provides offline support and caching for PWA functionality.
 */

// __BUILD_VERSION__ is replaced at image build time so each deploy gets a
// unique cache name. The activate handler below purges any cache whose name
// doesn't match — that's how stale assets from a previous deploy get cleared.
const CACHE_NAME = 'storagehub-__BUILD_VERSION__';
const OFFLINE_URL = '/offline';

// Assets to cache on install
const PRECACHE_ASSETS = [
	'/',
	'/offline',
	'/manifest.json'
];

// Install event - precache essential assets
self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => {
			return cache.addAll(PRECACHE_ASSETS);
		})
	);
	self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((cacheNames) => {
			return Promise.all(
				cacheNames
					.filter((cacheName) => cacheName !== CACHE_NAME)
					.map((cacheName) => caches.delete(cacheName))
			);
		})
	);
	self.clients.claim();
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
	const { request } = event;
	const url = new URL(request.url);

	// Skip non-GET requests
	if (request.method !== 'GET') {
		return;
	}

	// Skip API requests - always go to network
	if (url.pathname.startsWith('/api/')) {
		return;
	}

	// Skip WebSocket connections
	if (url.protocol === 'ws:' || url.protocol === 'wss:') {
		return;
	}

	// For navigation requests, try network first
	if (request.mode === 'navigate') {
		event.respondWith(
			fetch(request)
				.then((response) => {
					// Clone and cache successful responses
					if (response.ok) {
						const responseClone = response.clone();
						caches.open(CACHE_NAME).then((cache) => {
							cache.put(request, responseClone);
						});
					}
					return response;
				})
				.catch(() => {
					// Return cached version or offline page
					return caches.match(request).then((cachedResponse) => {
						return cachedResponse || caches.match(OFFLINE_URL);
					});
				})
		);
		return;
	}

	// For assets, use stale-while-revalidate strategy
	event.respondWith(
		caches.match(request).then((cachedResponse) => {
			const fetchPromise = fetch(request)
				.then((networkResponse) => {
					if (networkResponse.ok) {
						const responseClone = networkResponse.clone();
						caches.open(CACHE_NAME).then((cache) => {
							cache.put(request, responseClone);
						});
					}
					return networkResponse;
				})
				.catch(() => cachedResponse);

			return cachedResponse || fetchPromise;
		})
	);
});

// Handle push notifications (for future use)
self.addEventListener('push', (event) => {
	if (event.data) {
		const data = event.data.json();
		const options = {
			body: data.body,
			icon: '/icons/icon-192.png',
			badge: '/icons/icon-72.png',
			vibrate: [100, 50, 100],
			data: {
				url: data.url || '/'
			}
		};
		event.waitUntil(self.registration.showNotification(data.title, options));
	}
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
	event.notification.close();
	const url = event.notification.data?.url || '/';
	event.waitUntil(
		clients.matchAll({ type: 'window' }).then((clientList) => {
			// Focus existing window if open
			for (const client of clientList) {
				if (client.url === url && 'focus' in client) {
					return client.focus();
				}
			}
			// Open new window
			if (clients.openWindow) {
				return clients.openWindow(url);
			}
		})
	);
});

// Handle background sync (for offline actions)
self.addEventListener('sync', (event) => {
	if (event.tag === 'sync-pending-actions') {
		event.waitUntil(syncPendingActions());
	}
});

async function syncPendingActions() {
	// Future: sync offline changes when back online
	console.log('Background sync triggered');
}
