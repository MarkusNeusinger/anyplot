export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    // The Plausible proxy shares this route. `/api/event` is the analytics
    // endpoint the site's nginx also proxies (app/nginx.conf); it is not an
    // anyplot API path and must reach Plausible untouched.
    //
    // It is also the ONE path under this route that goes to the SITE's origin
    // instead of the API host — and the app has an origin gate of its own now
    // (app/origin-gate.conf.template). The same finding applies a second time:
    // a Worker subrequest to a host in the same zone skips that zone's
    // Transform Rules, so the app gate can only ever see the header if it is
    // stamped right here. Without these three lines, arming the app gate takes
    // every Plausible pageview on anyplot.ai down — quietly, because analytics
    // failing is not something a page tells its visitor about.
    //
    // Deleted before it is set, for the same reason as below: the headers are
    // cloned from the incoming request, so a caller could otherwise supply its
    // own value and have it forwarded whenever the binding is unset — which
    // would make an unarmed probe report a false `off-seen` and corrupt the one
    // measurement the rollout hangs on.
    if (url.pathname === '/api/event') {
      const eventHeaders = new Headers(request.headers);
      eventHeaders.delete('X-Origin-Secret');
      if (env.ORIGIN_SECRET) eventHeaders.set('X-Origin-Secret', env.ORIGIN_SECRET);
      return fetch(new Request(request, { headers: eventHeaders }));
    }
    const targetPath = url.pathname.replace(/^\/api/, '');
    const targetUrl = `https://api.anyplot.ai${targetPath}${url.search}`;
    const headers = new Headers(request.headers);
    headers.delete('host');
    // The API's origin gate (api/origin_gate.py) admits only requests that
    // carry the secret Cloudflare stamps at the edge. A Worker subrequest to
    // the same zone skips the zone's Transform Rules, so the Worker stamps the
    // header itself from its secret binding (unset binding = nothing stamped).
    // Delete first: the headers are cloned from the incoming request, so
    // without this a caller could supply its own X-Origin-Secret and have it
    // forwarded whenever the binding is unset — which would also make an
    // unarmed /health probe report a false `off-seen` and corrupt the one
    // measurement the rollout depends on.
    headers.delete('X-Origin-Secret');
    if (env.ORIGIN_SECRET) headers.set('X-Origin-Secret', env.ORIGIN_SECRET);
    return fetch(targetUrl, {
      method: request.method,
      headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : null,
      redirect: 'manual',
    });
  },
};
