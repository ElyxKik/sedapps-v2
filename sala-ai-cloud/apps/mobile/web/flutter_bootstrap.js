{{flutter_js}}
{{flutter_build_config}}

(async () => {
  // Firebase Hosting already serves immutable assets efficiently. Disable the
  // generated Flutter service worker because stale workers can reject route
  // navigations (for example /#/login) after a deployment.
  if ('serviceWorker' in navigator) {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(registrations.map((registration) => registration.unregister()));
  }

  if ('caches' in window) {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map((cacheName) => caches.delete(cacheName)));
  }

  await _flutter.loader.load({serviceWorkerSettings: null});
})();
