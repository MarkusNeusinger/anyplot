# SEO architecture

This document describes the SEO infrastructure for anyplot.ai, including bot detection, dynamic meta tags, branded og:images, and sitemap generation.

## Overview

anyplot.ai is a React SPA (Single Page Application). SPAs have a fundamental SEO challenge: social media bots and search engine crawlers cannot execute JavaScript, so they see an empty page without proper meta tags.

Our solution uses **nginx-based bot detection** to serve pre-rendered HTML with correct `og:tags` to bots, while regular users get the full SPA experience.

## Architecture diagram

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

## Bot detection

### Detected bots

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

### nginx configuration

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

## SEO proxy endpoints

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

### HTML template

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

## Branded OG images

Dynamically generated preview images with anyplot.ai branding.

**Router**: `api/routers/og_images.py`
**Image Processing**: `core/images.py`

### Endpoints

| Endpoint | Description | Dimensions |
|----------|-------------|------------|
| `GET /og/{spec_id}.png` | Collage of top 6 implementations | 1200x630 |
| `GET /og/{spec_id}/{library}.png` | Single branded implementation | 1200x630 |

### Single implementation image

Layout:
- anyplot.ai logo (centered, MonoLisa font 42px, weight 700)
- Tagline: "Beautiful Python plotting made easy."
- Plot image in rounded card with shadow
- Label: `{spec_id} · {library}`

### Collage image (spec overview)

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

Four groups in this order — welcomed AI agents (`ClaudeBot`, `Claude-User`,
`Claude-SearchBot`, `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`,
`Perplexity-User`), declined training collectors (`GPTBot`, `CCBot`,
`Bytespider`, `Amazonbot`, `meta-externalagent`), opt-out tokens
(`Google-Extended`, `Applebot-Extended`), and finally the wildcard. The first
group verbatim; read the file for the rest:

```txt
User-agent: ClaudeBot
User-agent: Claude-User
User-agent: Claude-SearchBot
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: PerplexityBot
User-agent: Perplexity-User
Content-Signal: search=yes,ai-input=yes,ai-train=no,use=reference
Disallow: /debug
Disallow: /interactive
Allow: /
```

Three properties of that file are deliberate and should survive any cleanup:

- The `Content-Signal` line is repeated in **every** group, declining ones
  included. A crawler reads only the group that matches it, so a reservation
  declared once under `User-agent: *` never reaches a named agent — least of all
  the training collectors it is aimed at.
- The named groups come **before** the wildcard group. A spec-compliant crawler
  picks the most specific match regardless of order, but simpler parsers take
  the first match and would read `Allow: /` and stop.
- Inside each group, `Disallow:` comes **before** `Allow: /` — same reason: with
  the broad allow first, a first-match parser (Python's `urllib.robotparser`,
  for one) hands out `/debug` and `/interactive`.

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

### nginx proxy

```nginx
location = /sitemap.xml {
    proxy_pass https://api.anyplot.ai/sitemap.xml;
}
```

## Search Console API access

Search Console holds data that no crawl of the site can reproduce: what people actually searched
for, which URLs Google indexed, and when it last crawled them. Without it the `seo-auditor` in
`/audit` falls back to `structural-only` mode. Credentials are per-machine, so set this up once
on every machine you audit from.

### Property and account

The property is a domain property, `sc-domain:anyplot.ai`. Access is tied to the Google account
that owns it — not to a service account, and not to the repository. Keep the machine-specific
values in `.env`, which is gitignored:

```bash
SEARCH_CONSOLE_PROPERTY=sc-domain:anyplot.ai
SEARCH_CONSOLE_ACCOUNT=owner@example.com
```

The same account also owns `sc-domain:pyplots.ai`, the site's former domain. Keep that property:
it carries the crawl and redirect history of the migration to `anyplot.ai`.

### Set up credentials

1. Enable the API on the GCP project. This is already done for `anyplot` and only needs
   repeating for a new project:

   ```bash
   gcloud services enable searchconsole.googleapis.com --project=anyplot
   ```

2. Authenticate with Application Default Credentials. The Search Console API needs the
   `webmasters.readonly` scope, and ADC is the only credential on this machine that can carry
   it:

   ```bash
   gcloud auth application-default login \
     --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/webmasters.readonly
   gcloud auth application-default set-quota-project anyplot
   ```

   Always keep `cloud-platform` in the scope list. The login overwrites ADC, and dropping the
   scope locks this machine's other Google clients (Cloud SQL, GCS) out.

3. Verify that the property comes back, using the snippet below.

The verification snippet is deliberately unindented: pasted with leading whitespace, the
heredoc terminator stops closing the block and Python rejects the indented program.

```bash
uv run --with google-auth --with requests python - <<'PY'
import google.auth
from google.auth.transport.requests import AuthorizedSession

creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
resp = AuthorizedSession(creds).get("https://www.googleapis.com/webmasters/v3/sites")
print(resp.status_code, resp.text[:400])
PY
```

You want HTTP 200 and `sc-domain:anyplot.ai` with `permissionLevel: siteOwner` in the list.

### Two traps that cost a session

**`gcloud auth print-access-token` returns the wrong token.** It mints a token for the gcloud CLI
credential, whose scope set is fixed (`cloud-platform`, `compute`, `sqlservice.login`) and can
never include `webmasters.readonly`. Every Search Console call made with it fails, which is why
audits before 2026-08-18 all reported `structural-only`. Read the token from ADC instead — either
`google.auth.default()` in a script, or `gcloud auth application-default print-access-token`.

**The localhost callback flow may never complete.** On some machines — WSL2 in particular — the
default browser flow dies within seconds with `(missing_code) Missing code parameter in
response`, because a port probe or a browser prefetch reaches `127.0.0.1:8085` before you finish
the consent screen, and gcloud aborts on the first request without a `code` parameter. Retrying
does not help. Use `--no-launch-browser` instead and paste the `4/0A…` code that Google displays;
that code is single-use and PKCE-bound to the waiting process. When you run the login
non-interactively, hold its stdin open (for example with `tail -f` on a file you append the code
to), otherwise gcloud crashes with `EOFError` before you can answer the prompt.

### What the API cannot answer

Search Analytics (queries, pages, dates — without the UI's 1000-row cap), the `sitemaps`
endpoint, and per-URL `urlInspection/index:inspect` (2000 calls per day) are all available. The
**page indexing report buckets** — "Crawled – currently not indexed", "Discovered – currently not
indexed", "Duplicate without user-selected canonical" — have no API at all. Those numbers only
come from a CSV export in the Search Console UI, so ask for one when the question is about
indexing coverage rather than about ranking.

## Testing

### Test bot detection locally

```bash
# Simulate Twitter bot
curl -H "User-Agent: Twitterbot/1.0" https://anyplot.ai/scatter-basic

# Should return HTML with og:tags, not React SPA
```

### Test OG images

```bash
# Single implementation
curl -o test.png https://api.anyplot.ai/og/scatter-basic/matplotlib.png

# Collage
curl -o test.png https://api.anyplot.ai/og/scatter-basic.png
```

### Validate with social media debuggers

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

## Multi-language URL strategy

Spec URLs are organised so the spec slug is the top-level identifier and the
language sits between spec and library. This keeps the spec — the actual SEO
entity — at the URL root and lets us add Julia, R, and MATLAB without touching
existing Python URLs.

### URL structure

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

### Reserved spec slugs

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

### Marketing subdomain

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

### Path utility

Frontend URL generation is centralized in `app/src/routes/paths.ts`:
- `specPath(specId, language?, library?)` — builds the three-tier URL based on
  which arguments are provided.
- `langFromPath(pathname)` — extracts the language segment from a path.
- `RESERVED_TOP_LEVEL` — Set of slugs that cannot be used as spec IDs.

### Adding a new language

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
