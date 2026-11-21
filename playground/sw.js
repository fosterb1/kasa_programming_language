/* Kasa offline-first shell. Build-time hash changes when site contents change. */
'use strict';
const CACHE_NAME = 'kasa-playground-__KASA_BUILD_HASH__';
// Set true only in build_site.py's verified standalone web archive.
const KASA_PACKAGED_MODULES = false;
const KASA_PACKAGED_G1_MODULES = false;
const CORE = [
  './', './index.html', './style.css', './app.js', './worker.js',
  './kasa-runtime.js', './diagnostics.js', './manifest.webmanifest',
  './icons/kasa-192.png', './icons/kasa-512.png',
];
if (KASA_PACKAGED_MODULES) CORE.push('./kasa-pinned-modules.js');
if (KASA_PACKAGED_G1_MODULES) CORE.push('./kasa-g1-pinned-modules.js');
const OPTIONAL_NATIVE = ['./native/kasa-native.js', './native/kasa-native.wasm'];
const WHITELIST = new Set([...CORE, ...OPTIONAL_NATIVE].map(path =>
  new URL(path, self.registration.scope).pathname));

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith('kasa-playground-') && key !== CACHE_NAME)
      .map(key => caches.delete(key))
  )).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request=event.request;
  if (request.method !== 'GET') return;
  const url=new URL(request.url);
  if (url.origin !== self.location.origin || !WHITELIST.has(url.pathname)) return;
  // Network first ensures a new deployment is picked up; cache serves offline.
  event.respondWith(caches.open(CACHE_NAME).then(async cache => {
    try {
      const response=await fetch(request);
      if (response.ok) await cache.put(request, response.clone());
      return response;
    } catch (error) {
      const cached=await cache.match(request, { ignoreSearch: true });
      if (cached) return cached;
      throw error;
    }
  }));
});
