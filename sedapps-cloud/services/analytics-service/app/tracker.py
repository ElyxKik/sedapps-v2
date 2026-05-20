from __future__ import annotations

TRACKER_JS = r"""
(function(){
  var script = document.currentScript;
  var trackerId = script && script.getAttribute('data-tracker-id');
  var endpoint = script && script.getAttribute('data-endpoint');
  if (!trackerId || !endpoint) return;
  if (navigator.doNotTrack === '1' || window.doNotTrack === '1') return;
  var sidKey = 'sedapps_sid_' + trackerId;
  var sid = sessionStorage.getItem(sidKey);
  if (!sid) {
    sid = Math.random().toString(36).slice(2) + Date.now().toString(36);
    sessionStorage.setItem(sidKey, sid);
  }
  function send(event, metadata) {
    var payload = {
      tracker_id: trackerId,
      session_id: sid,
      event: event,
      path: location.pathname + location.search,
      referrer: document.referrer || null,
      metadata: metadata || {}
    };
    var body = JSON.stringify(payload);
    if (navigator.sendBeacon) {
      navigator.sendBeacon(endpoint + '/v1/events', new Blob([body], {type: 'application/json'}));
      return;
    }
    fetch(endpoint + '/v1/events', {method:'POST', headers:{'Content-Type':'application/json'}, body:body, keepalive:true}).catch(function(){});
  }
  send('pageview', {title: document.title});
  document.addEventListener('click', function(e){
    var el = e.target && e.target.closest ? e.target.closest('[data-event],a[href^="tel:"],a[href^="mailto:"],a[href^="https://wa.me"]') : null;
    if (!el) return;
    send(el.getAttribute('data-event') || 'click', {href: el.href || null, text: (el.innerText || '').slice(0, 120)});
  }, true);
  document.addEventListener('submit', function(e){
    var form = e.target;
    if (form && form.matches && form.matches('form[data-track]')) {
      send('form_submit', {form: form.getAttribute('data-track')});
    }
  }, true);
})();
""".strip()
