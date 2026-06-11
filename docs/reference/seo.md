# SEO Architecture

This document describes the SEO infrastructure for anyplot.ai, including bot detection, dynamic meta tags, branded og:images, and sitemap generation.

## Overview

anyplot.ai is a React SPA (Single Page Application). SPAs have a fundamental SEO challenge: social media bots and search engine crawlers cannot execute JavaScript, so they see an empty page without proper meta tags.

Our solution uses **nginx-based bot detection** to serve pre-rendered HTML with correct `og:tags` to bots, while regular users get the full SPA experience.

## Architecture Diagram

```
                                    ┌─────────────────────┐
                                    │   Social Media Bot  │
                                    │  (Twitter, FB, etc) │
                                    └──────────┬──────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                           nginx (Frontend)                            │
│                                                                       │
│  1. Check User-Agent against bot list                                │
│  2. If bot → proxy to api.anyplot.ai/seo-proxy/*                     │
│  3. If human → serve React SPA (index.html)                          │
└──────────────────────────────────────────────────────────────────────┘
                    │                               │
                    │ Bot                           │ Human
                    ▼                               ▼
    ┌───────────────────────────┐    ┌───────────────────────────┐
    │   Backend API (FastAPI)   │    │      React SPA            │
    │                           │    │                           │
    │  /seo-proxy/*             │    │  Client-side routing      │
    │  Returns HTML with:       │    │  Dynamic content          │
    │  - og:title               │    │  Full interactivity       │
    │  - og:description         │    │                           │
    │  - og:image (branded)     │    │                           │
    └───────────────────────────┘    └───────────────────────────┘
                    │
                    │ og:image URL
                    ▼
    ┌───────────────────────────┐
    │   /og/{spec_id}.png       │  ← Collage (2x3 grid, top 6 by quality)
    │   /og/{spec_id}/{lib}.png │  ← Single branded implementation
    │                           │
    │   Dynamically generated   │
    │   1-hour cache            │
    └───────────────────────────┘
```

## Bot Detection

### Detected Bots

nginx detects 27 bots via User-Agent matching, organized by category:

**Social Media:**
| Bot | User-Agent Pattern |
|-----|-------------------|
| Twitter/X | `twitterbot` |
| Facebook | `facebookexternalhit` |
| LinkedIn | `linkedinbot` |
| Pinterest | `pinterestbot` |
| Reddit | `redditbot` |
| Tumblr | `tumblr` |
| Mastodon | `mastodon` |

**Messaging Apps:**
| Bot | User-Agent Pattern |
|-----|-------------------|
| Slack | `slackbot` |
| Discord | `discordbot` |
| Telegram | `telegrambot` |
| WhatsApp | `whatsapp` |
| Signal | `signal` |
| Viber | `viber` |
| Skype/Teams | `skypeuripreview` |
| Microsoft Teams | `microsoft teams` |
| Snapchat | `snapchat` |

**Search Engines:**
| Bot | User-Agent Pattern |
|-----|-------------------|
| Google | `googlebot` |
| Bing | `bingbot` |
| Yandex | `yandexbot` |
| DuckDuckGo | `duckduckbot` |
| Baidu | `baiduspider` |
| Apple | `applebot` |

**Link Preview Services:**
| Bot | User-Agent Pattern |
|-----|-------------------|
| Embedly | `embedly` |
| Quora | `quora link preview` |
| Outbrain | `outbrain` |
| Rogerbot | `rogerbot` |
| Showyoubot | `showyoubot` |

### nginx Configuration

Located in `app/nginx.conf`:

```nginx
# Bot detection map
map $http_user_agent $is_bot {
    default 0;
    ~*twitterbot 1;
    ~*facebookexternalhit 1;
    # ... more bots
}

# SPA routing with bot detection
location / {
    error_page 418 = @seo_proxy;
    if ($is_bot) {
        return 418;  # Trigger proxy to backend
    }
    try_files $uri $uri/ /index.html;
}

# Named location for bot proxy
location @seo_proxy {
    proxy_pass https://api.anyplot.ai/seo-proxy$request_uri;
}
```

## SEO Proxy Endpoints

Backend endpoints that serve HTML with correct meta tags for bots.

**Router**: `api/routers/seo.py`

### Endpoints

| Endpoint | Purpose | og:image |
|----------|---------|----------|
| `GET /seo-proxy/` | Home page | Default (`og-image.png`) |
| `GET /seo-proxy/plots` | Plots page | Default |
| `GET /seo-proxy/specs` | Specs page | Default |
| `GET /seo-proxy/legal` | Legal page | Default |
| `GET /seo-proxy/{spec_id}` | Spec overview (cross-language hub) | Collage (2x3 grid) |
| `GET /seo-proxy/{spec_id}/{language}` | **301** → `/seo-proxy/{spec_id}` (consolidated) | — |
| `GET /seo-proxy/{spec_id}/{language}/{library}` | Implementation | Single branded |

### HTML Template

All SEO proxy endpoints return minimal HTML with meta tags:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>{title}</title>
    <meta name="description" content="{description}" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:image" content="{image}" />
    <meta property="og:url" content="{url}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="anyplot.ai" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{title}" />
    <meta name="twitter:description" content="{description}" />
    <meta name="twitter:image" content="{image}" />
    <link rel="canonical" href="{url}" />
</head>
<body><h1>{title}</h1><p>{description}</p></body>
</html>
```

## Branded OG Images

Dynamically generated preview images with anyplot.ai branding.

**Router**: `api/routers/og_images.py`
**Image Processing**: `core/images.py`

### Endpoints

| Endpoint | Description | Dimensions |
|----------|-------------|------------|
| `GET /og/{spec_id}.png` | Collage of top 6 implementations | 1200x630 |
| `GET /og/{spec_id}/{library}.png` | Single branded implementation | 1200x630 |

### Single Implementation Image

Layout:
- anyplot.ai logo (centered, MonoLisa font 42px, weight 700)
- Tagline: "Beautiful Python plotting made easy."
- Plot image in rounded card with shadow
- Label: `{spec_id} · {library}`

### Collage Image (Spec Overview)

Layout:
- anyplot.ai logo (centered, MonoLisa font 38px)
- Tagline
- 2x3 grid of top 6 implementations (sorted by `quality_score` descending)
- Each plot in 16:9 rounded card with label below

### Caching

- **TTL**: 1 hour (3600 seconds)
- **Cache Key**: `og:{spec_id}:{library}` or `og:{spec_id}:collage`
- **Storage**: In-memory API cache

### Font

Uses **MonoLisa** variable font (commercial, not in repo):
- Downloaded from GCS: `gs://anyplot-static/fonts/MonoLisaVariableNormal.ttf`
- Cached locally in `/tmp/anyplot-fonts/`
- Fallback: DejaVuSansMono-Bold

## Robots.txt

### Frontend (anyplot.ai)

Static file at `app/public/robots.txt`:

```txt
User-agent: *
Allow: /
Disallow: /debug

Sitemap: https://anyplot.ai/sitemap.xml
```

### Backend (api.anyplot.ai)

Dynamic endpoint at `GET /robots.txt`:

```txt
User-agent: *
Disallow: /
```

**Why block the API?**
- APIs should not be indexed by search engines
- Prevents crawling of debug endpoints, docs, and API responses
- Social media bots (WhatsApp, Twitter, etc.) are unaffected - they fetch og:images directly

## Sitemap

Dynamic XML sitemap for search engine indexing.

### Endpoint

`GET /sitemap.xml` (proxied from frontend nginx to backend)

### Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://anyplot.ai/</loc></url>
  <url><loc>https://anyplot.ai/plots</loc></url>
  <url><loc>https://anyplot.ai/specs</loc></url>
  <url><loc>https://anyplot.ai/legal</loc></url>
  <!-- For each spec with implementations: -->
  <url><loc>https://anyplot.ai/{spec_id}</loc></url>
  <url><loc>https://anyplot.ai/{spec_id}/{language}/{library}</loc></url>
  <!-- ... -->
</urlset>
```

The `/{spec_id}/{language}` tier is intentionally **not** listed: language
filtering is served as `/{spec_id}?language={language}` (the hub with a filter
query param, same canonical as the unfiltered hub), so listing it would create
duplicate-content entries for Google.

### Included URLs

1. Home page (`/`)
2. Plots page (`/plots`)
3. Legal page (`/legal`)
4. Spec overview pages (`/{spec_id}`) — only if spec has implementations
5. Implementation pages (`/{spec_id}/{language}/{library}`) — all implementations

### nginx Proxy

```nginx
location = /sitemap.xml {
    proxy_pass https://api.anyplot.ai/sitemap.xml;
}
```

## Testing

### Test Bot Detection Locally

```bash
# Simulate Twitter bot
curl -H "User-Agent: Twitterbot/1.0" https://anyplot.ai/scatter-basic

# Should return HTML with og:tags, not React SPA
```

### Test OG Images

```bash
# Single implementation
curl -o test.png https://api.anyplot.ai/og/scatter-basic/matplotlib.png

# Collage
curl -o test.png https://api.anyplot.ai/og/scatter-basic.png
```

### Validate with Social Media Debuggers

- **LinkedIn**: https://www.linkedin.com/post-inspector/

## Files

| File | Purpose |
|------|---------|
| `app/nginx.conf` | Bot detection, SPA routing, sitemap proxy |
| `app/public/robots.txt` | Frontend robots.txt (blocks /debug) |
| `api/routers/seo.py` | SEO proxy endpoints, robots.txt, sitemap generation |
| `api/routers/og_images.py` | Branded og:image endpoints |
| `core/images.py` | Image processing, branding functions |

## Multi-Language URL Strategy

Spec URLs are organised so the spec slug is the top-level identifier and the
language sits between spec and library. This keeps the spec — the actual SEO
entity — at the URL root and lets us add Julia, R, and MATLAB without touching
existing Python URLs.

### URL Structure

| URL | Purpose | canonical |
|-----|---------|-----------|
| `/` | Landing | self |
| `/{spec_id}` | Cross-language hub — lists every implementation across all languages | self |
| `/{spec_id}?language={language}` | Hub filtered to one language (client-side filter) | `/{spec_id}` (without query) |
| `/{spec_id}/{language}/{library}` | Implementation detail — preview ↔ interactive toggle | self |
| `/{spec_id}/{language}/{library}?view=interactive` | Same page, interactive iframe pre-selected | base URL without query |
| `/plots`, `/specs`, `/libraries`, `/palette`, `/about`, `/legal`, `/mcp`, `/stats` | Static pages | self |

There is intentionally no canonical `/{spec_id}/{language}` URL. Language
filtering is served via a `?language=` query param on the hub, and the hub's
canonical tag omits the query — so the hub and its language-filtered variants
all consolidate on the same canonical URL. Legacy links to
`/{spec_id}/{language}` redirect to `/{spec_id}?language={language}` (SPA
client-side redirect via `app/src/routes/index.tsx`; bots get a 301 from
`/seo-proxy/{spec_id}/{language}` to `/seo-proxy/{spec_id}`).

The interactive view follows the same pattern: `?view=interactive` is a
deep-link parameter only; the canonical tag always points at the base URL
without the query string.

### Reserved Spec Slugs

Spec IDs are top-level path segments, so they must not collide with reserved
routes. The blocklist is enforced at runtime in `app/src/routes/paths.ts`
(`RESERVED_TOP_LEVEL`) and at spec creation time in `.github/workflows/spec-create.yml`:

```
plots, specs, libraries, palette, about, legal, mcp, stats, debug,
sitemap.xml, robots.txt
```

### Legacy URLs

There is no legacy redirect layer. Old `/python/{spec_id}[/{library}]` and
`/python/interactive/{spec_id}/{library}` URLs return the SPA's NotFoundPage
(catch-all `*` route) and emit a 404 on bot requests via `/seo-proxy`. The
sitemap stops listing those URLs, and Google removes them on next crawl.

### Marketing Subdomain

`python.anyplot.ai` is served by a dedicated nginx server block
(`app/nginx.conf`) that proxies bot requests to the main-domain hub / detail
proxies:

| Subdomain URL | Internal rewrite | Canonical (in HTML) |
|---|---|---|
| `python.anyplot.ai/{spec_id}` | `/seo-proxy/{spec_id}` | `https://anyplot.ai/{spec_id}` |
| `python.anyplot.ai/{spec_id}/{library}` | `/seo-proxy/{spec_id}/python/{library}` | `https://anyplot.ai/{spec_id}/python/{library}` |

The user keeps the marketing-friendly hostname; Google sees a canonical on the
main-domain hub so authority and ranking signals stay consolidated on a single
URL. Human visitors: the SPA may detect
`window.location.hostname === 'python.anyplot.ai'` and append
`?language=python` on spec routes so the grid renders filtered without
changing the canonical.

### Path Utility

Frontend URL generation is centralized in `app/src/routes/paths.ts`:
- `specPath(specId, language?, library?)` — builds the three-tier URL based on
  which arguments are provided.
- `langFromPath(pathname)` — extracts the language segment from a path.
- `RESERVED_TOP_LEVEL` — Set of slugs that cannot be used as spec IDs.

### Adding a New Language

When adding Julia, R, or MATLAB:

1. Set `Library.language = "julia"` (etc.) on each library row.
2. Implementations automatically appear under
   `/{spec_id}/julia/{library_id}`; sitemap and OG image routes pick them up.
3. The cross-language hub `/{spec_id}` lists the new language's
   implementations alongside Python's — no per-spec migration needed.
4. Users can filter the hub to a single language via `/{spec_id}?language=julia`
   (no new canonical URL is created; the filter is UX-only).
5. Optionally add a `julia.anyplot.ai` server block mirroring the Python one.

## Security

- All user input (spec_id, library) is HTML-escaped before rendering
- XSS prevention via `html.escape()` for all dynamic content
- og:image URLs use `html.escape(url, quote=True)` to prevent attribute injection
