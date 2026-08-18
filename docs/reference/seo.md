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

nginx detects 52 User-Agent patterns, organized by category:

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

**User-directed AI fetchers:**

These arrive because a human asked their assistant to open a page — they are
not index crawlers. Google documents its own as
[generally ignoring robots.txt](https://developers.google.com/search/docs/crawling-indexing/google-user-triggered-fetchers),
so this map is the only control point for them: robots.txt cannot govern what
they fetch, only this decides what they receive. Every entry below was verified
receiving the empty SPA shell before it was added (2026-08-18) — an assistant
asked about a plot page could describe nothing at all.

| Fetcher | User-Agent Pattern |
|---------|-------------------|
| Gemini (NotebookLM) | `gemininotebook`, `notebooklm` |
| Gemini Deep Research | `gemini-deep-research` |
| Google agents (Mariner) | `googleagent`, `google-agent` |
| Meta AI | `meta-externalfetcher` |
| Mistral (Le Chat) | `mistralai-user`, `mistralai-index` |
| DuckDuckGo AI | `duckassistbot` |
| Amazon (retrieval) | `amzn-searchbot`, `amzn-user` |
| Meta AI search | `meta-webindexer` |
| xAI / Grok · You.com · Cohere | `grokbot`, `xai-grok`, `grok-deepsearch`, `youbot`, `cohere-ai` — community-reported tokens, no vendor documentation; best-effort |

Three vendor splits are easy to get backwards, so they are spelled out:

- **Meta**: `meta-externalfetcher` (user-directed) and `meta-webindexer` (AI
  search index) are served; `meta-externalagent` is the training crawler and is
  not mapped.
- **Mistral**: `mistralai-user` and `mistralai-index` are served — Mistral
  documents both as never used for generative-AI training; `mistralai-training`
  is the training crawler and is not mapped.
- **Amazon**: `amzn-searchbot` and `amzn-user` are the sanctioned retrieval
  agents, both documented as not crawling for model training; plain `amazonbot`
  is the training crawler and is not mapped.

Mapping is not permission. This map decides only *what* an agent receives once
it arrives; whether it may crawl at all is robots.txt plus Cloudflare's AI Crawl
Control — which is why mapping community-reported tokens costs nothing, and why
an unmapped agent is not thereby declined. Under the current policy everything
except `Bytespider` may crawl, so the mapping question is only ever about
rendering.

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
| OpenAI crawler | `gptbot` | training crawler; allowed and mapped |
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

## What a crawler sees of the plot

Two different images exist per implementation, and the bot page carries both,
deliberately:

| Image | What it is | Where it appears |
|---|---|---|
| `api.anyplot.ai/og/{spec}/{language}/{library}.png` | 1200×630 branded social card; the plot is a thumbnail inside chrome | `og:image`, `twitter:image` |
| `…/plot-light.png`, `…/plot-dark.png` in GCS | the actual render, full resolution | the page body, as a `<picture>` |

The card is right for a shared link and wrong for an assistant asked to show the
plot — in it the plot is roughly a third of the frame and the cell labels are
barely legible. So the body carries the real render instead. Attribution does not
suffer: every render's own title reads `{spec} · {language} · {library} ·
anyplot.ai`, so the source travels with the image wherever it is embedded.

The pipeline writes `_400`, `_800` and `_1200` derivatives beside each render and
the suffix is the true pixel width — verified across square and wide plots in all
four languages. Those three form the `srcset`. The full-size original is **not**
in it: its width varies per plot (2400, 3200, 4766 among the ones measured), so
no honest `w` descriptor exists for it. It gets its own link instead, and the
`src` points at the 1200px variant so a consumer ignoring `srcset` does not pull
a five-megapixel file.

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

Static file at `app/public/robots.txt`. It carries the full policy — the content
signals and the one declined agent — so it holds regardless of what Cloudflare
does or does not prepend (see [AI crawler policy](#ai-crawler-policy)):

Two groups, in this order: `Bytespider`, declined on bandwidth grounds, then the
wildcard that allows everyone else. The retrieval-yes / training-no split this
section used to describe is gone — the policy is open to every operator, so the
named allow-groups it needed became redundant with `User-agent: *`. The declined
group verbatim; read the file for the rest:

```txt
User-agent: Bytespider
Content-Signal: search=yes,ai-input=yes,ai-train=yes,use=reference
Disallow: /
```

Three properties of that file are deliberate and should survive any cleanup:

- The `Content-Signal` line is repeated in **every** group. A crawler reads only
  the group that matches it, so a signal declared once under `User-agent: *`
  never reaches a named agent.
- The named group comes **before** the wildcard. A spec-compliant crawler picks
  the most specific match regardless of order, but simpler parsers take the
  first match and would read `Allow: /` and stop.
- Inside each group, `Disallow:` comes **before** `Allow: /` — same reason: with
  the broad allow first, a first-match parser (Python's `urllib.robotparser`,
  for one) hands out `/debug` and `/interactive`.

### Backend (api.anyplot.ai)

Dynamic endpoint at `GET /robots.txt`:

```txt
User-agent: *
Allow: /og/
Disallow: /
```

`/og/` is the exception: every prerendered page references its preview image
there, so a blanket `Disallow` pointed crawlers at an image they were forbidden
to fetch. `Allow` comes first for the first-match parsers described above.

**Why block the API?**
- APIs should not be indexed by search engines
- Prevents crawling of debug endpoints, docs, and API responses
- Social media bots (WhatsApp, Twitter, etc.) are unaffected - they fetch og:images directly

### AI crawler policy

**Decision (2026-08-18, supersedes issue #9633):** everything is open. Retrieval,
citation, search indexing and model training are permitted for every operator.

The previous policy drew a retrieval-yes / training-no line and expressed the
training half as a reservation of rights under Article 4 of EU Directive
2019/790. That line was never coherent here: the catalogue is MIT-licensed and
published to be reused, so declining a training crawler protected nothing the
licence had not already given away, while costing reach.

It also had a concrete, unintended consequence. Google offers a single token,
`Google-Extended`, that governs Gemini **grounding and training together** —
there is no finer control, verified against Google's crawler documentation. The
old policy declined it as if it were a training-only token, which kept anyplot
out of Gemini's answers entirely. `Applebot-Extended` genuinely *is*
training-only (retrieval and Siri answers ride on `Applebot`), so declining it
was correct under the old policy and is simply no longer wanted under this one.

| Group | Agents | Policy |
|---|---|---|
| Everything | search engines, AI assistants, their index and training crawlers, social and link previews | allowed |
| Bandwidth exception | `Bytespider` | declined |
| App internals | `/debug`, `/interactive` for all agents | declined |

`Bytespider` is the one exception and it is operational, not principled: it is
documented as ignoring robots.txt and crawls far more aggressively than this
catalogue can justify serving. The robots group states the intent; Cloudflare
does the enforcing. If its behaviour changes, the group can go.

#### Cloudflare is the enforcement layer

The edge can be stricter than this file and answers blocked agents with `HTTP
403` regardless of what is written here — so **a permission granted in
`robots.txt` that the dashboard still blocks is a published lie**. Keep the two
in step.

Measured on the live zone 2026-08-18 (zone `anyplot.ai` → **AI Crawl Control** →
Security):

The dashboard was brought in line with the open policy on 2026-08-18. State
after that change:

| State | Agents |
|---|---|
| Blocked at the edge | `Bytespider`, `TikTok Spider`, `Anchor Browser`, `Novellum AI Crawl`, `Timpibot` |
| Passing | everything else, including `GPTBot`, `CCBot`, `Amazonbot`, `meta-externalagent`, `Google-CloudVertexBot`, `PetalBot`, `FacebookBot`, `Arquivo Web Crawler`, and every retrieval agent |

`Bytespider` and `TikTok Spider` are both ByteDance; the first is documented as
ignoring robots.txt, and the second shares its operator. The remaining three are
blocked for a weaker reason — no vendor documentation of their crawling
behaviour could be found, so their rule-compliance is unverified rather than
disproven. Revisit if that changes.

Cloudflare is **not** prepending a managed robots.txt block: the live file is
byte-identical to this repo's, and enforcement is purely the 403. That was
different at the 2026-07-25 measurement, so re-check rather than assume.

`bot-serving-check` deliberately tests the Cloud Run origin, not the edge, so it
will never catch a dashboard change. Edge drift has to be checked by hand.

Verify afterwards:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -A "Mozilla/5.0 (compatible; GPTBot/1.4; +https://openai.com/gptbot)" https://anyplot.ai/   # expect 200 once unblocked
curl -s -o /dev/null -w '%{http_code}\n' -A "Mozilla/5.0 (compatible; Bytespider)" https://anyplot.ai/                              # expect 403
curl -sA "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)" https://anyplot.ai/scatter-basic | grep -o '<title>[^<]*</title>'   # per-route title, not the SPA shell
```

The last command is the part this repo owns: `app/nginx.conf` maps the AI UAs
onto the seo-proxy path, and `.github/workflows/bot-serving-check.yml` guards it
daily against the Cloud Run origin (origin, not edge — so it reports on the
nginx map no matter what the zone policy is, and will never catch edge drift).

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
