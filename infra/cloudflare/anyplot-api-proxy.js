export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    // The Plausible proxy shares this route. `/api/event` is the analytics
    // endpoint the site's nginx also proxies (app/nginx.conf); it is not an
    // anyplot API path and must reach Plausible untouched.
    if (url.pathname === '/api/event') {
      return fetch(request);
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
