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

nginx detects 37 User-Agent patterns, organized by category:

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
| Google URL inspection | `google-inspectiontool` |
| Google misc crawler | `googleother` |
| Bing | `bingbot` |
| Yandex | `yandexbot` |
| DuckDuckGo | `duckduckbot` |
| Baidu | `baiduspider` |
| Apple | `applebot` |

**AI Assistants & AI Search:**
| Bot | User-Agent Pattern | Role |
|-----|-------------------|------|
| Anthropic crawler | `claudebot` | index/crawl |
| Claude user fetch | `claude-user` | a human asked Claude to open the page |
| Claude search | `claude-searchbot` | citation index |
| OpenAI crawler | `gptbot` | training (declined in robots.txt, mapped anyway — see below) |
| ChatGPT search | `oai-searchbot` | citation index |
| ChatGPT user fetch | `chatgpt-user` | a human asked ChatGPT to open the page |
| Perplexity | `perplexitybot`, `perplexity-user` | citation index / user fetch |

None of these execute JavaScript, so without the map entries an AI answer
citing anyplot would describe the empty SPA shell. The map decides **what** a
crawler is served, never **whether** it may fetch — that is the robots.txt +
Cloudflare question in [AI crawler policy](#ai-crawler-policy).

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

All SEO proxy endpoints share one template (`BOT_HTML_TEMPLATE` + `_render_bot_html()`):
the `<head>` carries the meta/OG/Twitter tags plus an optional JSON-LD script, and the
`<body>` carries what search engines actually index. Every page ends with a site-wide
`<nav>` (home, plots, specs, libraries, map, palette, mcp, stats, about) so crawlers
landing deep can walk the site without executing the SPA.

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
    {jsonld}
</head>
<body>
{body}
</body>
</html>
```

Per-page body content:

| Page | Body | JSON-LD |
|------|------|---------|
| Static pages (`/`, `/plots`, …) | `<h1>` + description + nav | — |
| Spec hub `/{spec_id}` | description, preview `<img>`, one link per implementation page | `BreadcrumbList` + `ItemList` |
| Implementation `/{spec_id}/{language}/{library}` | description, preview `<img>`, full source in `<pre><code>` (noqa-stripped, HTML-escaped), hub link, sibling-implementation links | `BreadcrumbList` + `SoftwareSourceCode` |

Display names (Matplotlib, Makie.jl, Apache ECharts, …) are derived from
`core/constants.py` (`LANGUAGES_METADATA` / `LIBRARIES_METADATA`) — never
hand-maintained in the router.

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

Static file at `app/public/robots.txt`. It carries the full policy — content
signals, the welcomed AI agents, the declined training collectors — so it holds
regardless of what Cloudflare does or does not prepend (see
[AI crawler policy](#ai-crawler-policy)):

```txt
… welcomed AI agents (Claude*, OAI-SearchBot, ChatGPT-User, Perplexity*)
      + Content-Signal, Allow: /, Disallow: /debug, /interactive
… declined training collectors (GPTBot, CCBot, Bytespider, Amazonbot, meta-externalagent)
… opt-out tokens (Google-Extended, Applebot-Extended)

User-agent: *
Content-Signal: search=yes,ai-input=yes,ai-train=no,use=reference
Allow: /
Disallow: /debug
Disallow: /interactive

Sitemap: https://anyplot.ai/sitemap.xml
```

Two properties of that file are deliberate:

- The `Content-Signal` line is **repeated** in the welcomed-AI group. A crawler
  obeys the single group that matches it, so an agent named in its own group
  never sees the signal declared under `User-agent: *` — and that group is
  precisely where the training reservation has to land.
- The named groups come **before** the wildcard group. A spec-compliant crawler
  picks the most specific match regardless of order, but simpler parsers take
  the first match and would read `Allow: /` and stop.

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

### AI crawler policy

**Decision (issue #9633):** AI agents that *retrieve and cite* are welcome;
agents that only *collect for training* are declined. anyplot's entire strategy
is to be consumable by AI agents — `/llms.txt`, the MCP server, MIT-licensed
code on every page — so blocking the retrieval side works against the product.
The training reservation stays expressed, and it is the legally load-bearing
part: `Content-Signal: ai-train=no` is an express reservation of rights under
Article 4 of EU Directive 2019/790.

| Group | Agents | Policy |
|---|---|---|
| Retrieval / citation / user-directed | `ClaudeBot`, `Claude-User`, `Claude-SearchBot`, `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`, `Perplexity-User` | allowed |
| Training collectors | `GPTBot`, `CCBot`, `Bytespider`, `Amazonbot`, `meta-externalagent` | declined |
| Opt-out tokens (vendor crawls under another UA) | `Google-Extended`, `Applebot-Extended` | declined |

`GPTBot` is the deliberate borderline call: it is OpenAI's *training* crawler,
so it sits with the declined group, while ChatGPT's retrieval path
(`OAI-SearchBot`, `ChatGPT-User`) stays open. Reversing that is a one-group
edit in `app/public/robots.txt`. Vendor UA roles shift — re-check the current
role of each agent against Cloudflare's AI Crawl Control categories before
changing the policy.

#### Cloudflare is the enforcement layer

Measured 2026-07-25 on the live zone: Cloudflare prepends a **managed
robots.txt** block (`Disallow: /` for ClaudeBot, GPTBot, CCBot, Google-Extended,
Amazonbot, Applebot-Extended, Bytespider, meta-externalagent,
CloudflareBrowserRenderingCrawler) *and* answers those user agents with a hard
`HTTP 403 Your request was blocked.` at the edge — including `Claude-User` and
`ChatGPT-User`, and including `/llms.txt` itself. The file written for AI agents
was unreachable to every agent it was written for. Googlebot passes (200).

`api.anyplot.ai` is **not** covered by the block (ClaudeBot gets 200 there), so
the MCP server stayed reachable.

Aligning the edge with this policy is a dashboard action (zone `anyplot.ai` →
**AI Crawl Control** / Bots): allow the retrieval group, keep the training
group blocked, and either turn off the managed robots.txt (this repo's file
already carries the content signals) or leave it on and accept that the live
file is stricter than the repo's.

Verify afterwards:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -A "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)" https://anyplot.ai/llms.txt   # expect 200
curl -s -o /dev/null -w '%{http_code}\n' -A "Mozilla/5.0 (compatible; CCBot/2.0; +https://commoncrawl.org/faq/)"   https://anyplot.ai/          # expect 403
curl -sA "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)" https://anyplot.ai/scatter-basic | grep -o '<title>[^<]*</title>'   # per-route title, not the SPA shell
```

The last command is the part this repo owns: `app/nginx.conf` maps the AI UAs
onto the seo-proxy path, and `.github/workflows/bot-serving-check.yml` guards it
daily against the Cloud Run origin (origin, not edge — so it reports on the
nginx map no matter what the zone policy is).

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
| `app/public/robots.txt` | Frontend robots.txt (content signals, AI crawler policy, blocks /debug) |
| `app/public/llms.txt` | Agent-facing site summary; served directly, never via the seo-proxy |
| `api/routers/seo.py` | SEO proxy endpoints, robots.txt, sitemap generation |
| `api/routers/og_images.py` | Branded og:image endpoints |
| `core/images.py` | Image processing, branding functions |
| `.github/workflows/bot-serving-check.yml` | Daily synthetic check of the bot → seo-proxy path |

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
