// Service Worker for Hasteo Bus Attendance System
const CACHE_NAME = 'hasteo-v2.1';
const OFFLINE_URL = '/offline';
const API_CACHE_NAME = 'hasteo-api-v1';

// Static assets to cache
const STATIC_CACHE_URLS = [
    '/',
    '/static/css/common.css',
    '/static/css/auth.css',
    '/static/css/admin.css',
    '/static/css/security.css',
    '/static/js/common.js',
    '/static/js/auth.js',
    '/static/js/admin.js',
    '/static/js/security.js',
    '/static/js/pwa.js',
    '/static/images/logo.png',
    '/static/images/app_logo.png',
    '/manifest.json',
    '/offline'
];

// Install event
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 Caching app shell');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                        console.log('🗑️ Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
        .then(() => self.clients.claim())
    );
});

// Fetch event - Network first for dynamic content, cache first for static
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    const url = new URL(event.request.url);

    // API requests - Network first, cache fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            networkFirstWithCache(event.request, API_CACHE_NAME)
        );
        return;
    }

    // HTML pages - Network first, offline fallback
    if (event.request.headers.get('accept').includes('text/html')) {
        event.respondWith(
            networkFirstWithOfflineFallback(event.request)
        );
        return;
    }

    // Static assets - Cache first, network fallback
    event.respondWith(
        cacheFirstWithNetworkFallback(event.request)
    );
});

// Network first with cache fallback
async function networkFirstWithCache(request, cacheName) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const responseClone = networkResponse.clone();
            caches.open(cacheName).then(cache => {
                cache.put(request, responseClone);
            });
        }
        
        return networkResponse;
    } catch (error) {
        // If network fails, try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline response for specific API endpoints
        if (request.url.includes('/api/attendance') || request.url.includes('/api/bus/timestamps')) {
            return new Response(JSON.stringify([]), {
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        throw error;
    }
}

// Network first with offline fallback
async function networkFirstWithOfflineFallback(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => {
                cache.put(request, responseClone);
            });
        }
        
        return networkResponse;
    } catch (error) {
        // If network fails, try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page
        return caches.match(OFFLINE_URL);
    }
}

// Cache first with network fallback
async function cacheFirstWithNetworkFallback(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        // Update cache in background
        fetch(request).then(networkResponse => {
            if (networkResponse.ok) {
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(request, networkResponse);
                });
            }
        }).catch(() => {});
        
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => {
                cache.put(request, responseClone);
            });
        }
        
        return networkResponse;
    } catch (error) {
        // Return empty responses for CSS/JS to prevent errors
        if (request.url.includes('.css')) {
            return new Response('', { 
                headers: { 'Content-Type': 'text/css' } 
            });
        }
        if (request.url.includes('.js')) {
            return new Response('', { 
                headers: { 'Content-Type': 'application/javascript' } 
            });
        }
        return new Response('', { status: 404 });
    }
}

// Background sync for offline data
self.addEventListener('sync', event => {
    if (event.tag === 'sync-attendance') {
        event.waitUntil(syncOfflineAttendance());
    }
    
    if (event.tag === 'sync-bus-logs') {
        event.waitUntil(syncOfflineBusLogs());
    }
});

// Sync offline attendance records
async function syncOfflineAttendance() {
    console.log('🔄 Syncing offline attendance...');
    
    // Get offline attendance from IndexedDB
    const db = await openDatabase();
    const offlineAttendance = await getAllFromStore(db, 'attendance');
    
    for (const record of offlineAttendance) {
        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(record.data)
            });
            
            if (response.ok) {
                await deleteFromStore(db, 'attendance', record.id);
                console.log(`✅ Synced attendance: ${record.data.register_no}`);
                
                // Send notification
                self.registration.showNotification('Attendance Synced', {
                    body: `${record.data.register_no} scan synced successfully`,
                    icon: '/static/images/app_logo.png',
                    tag: 'sync-success'
                });
            }
        } catch (error) {
            console.log(`❌ Failed to sync: ${record.data.register_no}`, error);
        }
    }
    
    await db.close();
}

// Sync offline bus logs
async function syncOfflineBusLogs() {
    console.log('🔄 Syncing offline bus logs...');
    
    const db = await openDatabase();
    const offlineBusLogs = await getAllFromStore(db, 'busLogs');
    
    for (const log of offlineBusLogs) {
        try {
            const response = await fetch('/api/bus/timestamp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(log.data)
            });
            
            if (response.ok) {
                await deleteFromStore(db, 'busLogs', log.id);
                console.log(`✅ Synced bus log: ${log.data.bus_no}`);
            }
        } catch (error) {
            console.log(`❌ Failed to sync bus log: ${log.data.bus_no}`, error);
        }
    }
    
    await db.close();
}

// IndexedDB helper functions
function openDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('hasteo-offline', 1);
        
        request.onupgradeneeded = function(event) {
            const db = event.target.result;
            
            if (!db.objectStoreNames.contains('attendance')) {
                db.createObjectStore('attendance', { keyPath: 'id', autoIncrement: true });
            }
            
            if (!db.objectStoreNames.contains('busLogs')) {
                db.createObjectStore('busLogs', { keyPath: 'id', autoIncrement: true });
            }
        };
        
        request.onsuccess = function(event) {
            resolve(event.target.result);
        };
        
        request.onerror = function(event) {
            reject(event.target.error);
        };
    });
}

function getAllFromStore(db, storeName) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.getAll();
        
        request.onsuccess = function() {
            resolve(request.result || []);
        };
        
        request.onerror = function() {
            reject(request.error);
        };
    });
}

function deleteFromStore(db, storeName, id) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.delete(id);
        
        request.onsuccess = function() {
            resolve(true);
        };
        
        request.onerror = function() {
            reject(request.error);
        };
    });
}

// Push notifications
self.addEventListener('push', event => {
    if (!event.data) return;
    
    let data;
    try {
        data = event.data.json();
    } catch (e) {
        data = {
            title: 'Hasteo Notification',
            body: event.data.text()
        };
    }
    
    const options = {
        body: data.body,
        icon: '/static/images/app_logo.png',
        badge: '/static/images/app_logo.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/',
            tag: data.tag || 'general'
        },
        actions: data.actions || []
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    const url = event.notification.data.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(clientList => {
            // Check if there's already a window/tab open with the target URL
            for (const client of clientList) {
                if (client.url === url && 'focus' in client) {
                    return client.focus();
                }
            }
            
            // If not, open a new window/tab
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});

// Periodic sync for background updates
self.addEventListener('periodicsync', event => {
    if (event.tag === 'update-cache') {
        event.waitUntil(updateCache());
    }
});

// Update cache periodically
async function updateCache() {
    console.log('🔄 Updating cache...');
    
    const cache = await caches.open(CACHE_NAME);
    const requests = STATIC_CACHE_URLS.map(url => new Request(url));
    
    for (const request of requests) {
        try {
            const networkResponse = await fetch(request);
            if (networkResponse.ok) {
                await cache.put(request, networkResponse);
            }
        } catch (error) {
            console.log(`Failed to update cache for ${request.url}:`, error);
        }
    }
}