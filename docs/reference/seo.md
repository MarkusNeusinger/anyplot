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
| `GET /seo-proxy/catalog` | Catalog page | Default |
| `GET /seo-proxy/legal` | Legal page | Default |
| `GET /seo-proxy/{spec_id}` | Spec overview | Collage (2x3 grid) |
| `GET /seo-proxy/{spec_id}/{library}` | Implementation | Single branded |

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
  <url><loc>https://anyplot.ai/catalog</loc></url>
  <url><loc>https://anyplot.ai/legal</loc></url>
  <!-- For each spec with implementations: -->
  <url><loc>https://anyplot.ai/{spec_id}</loc></url>
  <url><loc>https://anyplot.ai/{spec_id}/{library}</loc></url>
  <!-- ... -->
</urlset>
```

### Included URLs

1. Home page (`/`)
2. Catalog page (`/catalog`)
3. Legal page (`/legal`)
4. Spec overview pages (`/{spec_id}`) - only if spec has implementations
5. Implementation pages (`/{spec_id}/{library}`) - all implementations

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

## Security

- All user input (spec_id, library) is HTML-escaped before rendering
- XSS prevention via `html.escape()` for all dynamic content
- og:image URLs use `html.escape(url, quote=True)` to prevent attribute injection
