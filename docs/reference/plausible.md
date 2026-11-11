# Plausible analytics tracking

How anyplot.ai uses Plausible Analytics: how pageviews are sent, the custom
events and their properties, what the dashboard needs, and what is
deliberately not tracked. The dashboard at
[plausible.io/anyplot.ai](https://plausible.io/anyplot.ai) is public, so every
event is one a reader from outside understands.

## Setup

**Location**: `app/index.html`

- Self-hosted Plausible script loaded via `/js/script.js`
- Custom endpoint: `/api/event` (proxied through nginx to avoid adblockers)
- Manual pageview tracking: `autoCapturePageviews: false`
- No form-submission goal: `formSubmissions: false` (since 2026-11-08). The
  agent chat's message box is a form, so the script's automatic
  `Form: Submission` goal counted chat messages that the chat's own events
  already count: 144 of its 146 events in the 28 days before were the
  admin's own chat messages.
  Outbound links and file downloads keep the script's defaults: the script
  records a click on a link to another site as `Outbound Link: Click`, with the
  link's address, and the app sends no link event of its own.
- Production-only: Only tracks on `anyplot.ai` domain
- Privacy-focused: No cookies, GDPR-compliant

## Page views

**Implementation**: Query parameters converted to URL path segments for better analytics segmentation.

### When a pageview is sent

Since 2026-11-11 the layout sends the pageview of every page: `RootLayout`
(`app/src/layouts/RootLayout.tsx`) calls `trackPageview()` in a layout effect
on every navigation, and no page sends its own. The gallery is the one other
sender. A filter change on `/plots` rewrites the address without a navigation,
so `useUrlSync` records that page itself. The same address is never sent twice
in a row, whichever of the two comes second.

The timing is what Plausible's scroll depth depends on. The script closes the
page being left when the next pageview arrives, and reports that page's depth
as the deepest offset reached over the document height it last observed, which
a ResizeObserver keeps current. Until 2026-11-11 each page sent its own
pageview from an effect, 150 ms late, so the call arrived after the next page
had rendered. The depth of the page being left was then divided by the height
of the next page: too low before a longer page, too high before a shorter one.
Measured with the live script on 2026-11-11, a landing page left at 47 % was
sent as 30 %, and the gallery after 12,000 px as 1,176 %. A layout effect runs
before the browser lays the next page out, so the depth is measured against
the page it belongs to.

Four things follow from that place in the commit:

- **The scroll reset comes first.** The reset on a forward navigation is a
  layout effect declared before the pageview's, because the script takes the
  scroll offset at the pageview as the new page's first depth.
- **A page's own layout effects come first too.** The gallery writes the
  filters it restores from the last visit into the address there, so that
  visit is one pageview, of the filtered page. The agent chat switches its
  admin mute on there (see [Agent chat](#agent-chat)).
- **An address that only redirects is no page.** `/{spec_id}/{language}` and
  `/debug/agent` redirect in their route's loader
  (`app/src/routes/redirects.ts`), so the router never renders them and they
  record nothing. The page being left also stays on screen until the
  destination is there.
- **Back and forward send the pageview from the top.** They keep the
  browser's own scroll restoration, which Chrome applies after the layout
  effect, so the offset at that moment is still the one of the page being
  left. The layout scrolls to the top, sends the pageview, and puts the offset
  back before anything is painted; the script learns the page's real offset
  from the scroll event that follows. Without this, a landing page restored at
  35 % was sent as 98 % (measured on 2026-11-11). The gallery is the exception:
  it turns the browser's restoration off and restores its own offset, so a
  navigation to `/plots` always starts from the top, Back included.

Every address that becomes a page records a pageview, including one the app
can't serve: the 404 page is recorded under the path that was asked for, so a
missing page shows under the dashboard's pages with that path. Until
2026-11-11 a 404 recorded no pageview, and a spec page recorded its pageview
only once its data had loaded. Until 2026-11-12 a 404 also sent a
`page_not_found` event (see [Events that ended](#events-that-ended)).

### The `page` property

Since 2026-11-12 every pageview carries the kind of page as `page`
(`pageKind()` in `app/src/hooks/useAnalytics.ts`), so the dashboard and its
funnels can group pages by kind without a path pattern:

| `page` | The address |
|--------|-------------|
| `home` | `/` |
| `plots` | `/plots`, with any filters |
| `spec_overview` | `/{spec_id}`, a spec's hub |
| `spec_detail` | `/{spec_id}/{language}/{library}`, one implementation |
| `agent_chat` | `/agent` |
| `other` | Every other page, and an address that names nothing |

`copy_code` and `download_image` send the same values, so one `page`
breakdown covers the pageviews and the two conversions. A spec that doesn't
exist is recorded as the kind its address has: the layout sends the pageview
at the navigation, before the page knows what it holds.

### Scroll depth

Plausible measures scroll depth itself, per pageview; the app sends no scroll
event for it. The dashboard keeps one scroll goal, "Scroll 90% on /": a visitor
saw the whole landing page.

The gallery at `/plots` loads its results in batches while the visitor
scrolls, so that page has no fixed height and its scroll depth says nothing.
`plots_scrolled` reports the gallery instead (see
[Gallery scroll](#gallery-scroll-plots_scrolled)).

### Multi-language URL strategy

**Cutover date**: 2026-04-20

Spec URLs follow the three-tier structure `/{specId}[/{language}[/{library}]]`,
so the spec slug — the actual SEO entity — sits at the URL root and the
language slots between spec and library:

- Root `/` and reserved static pages (`/plots`, `/specs`, `/libraries`,
  `/palette`, `/about`, `/legal`, `/mcp`, `/stats`) are un-prefixed.
- Cross-language hub: `/{spec_id}` (lists every implementation across
  all languages).
- Language overview: `/{spec_id}/{language}` (e.g. `/scatter-basic/python`).
  It redirects to the hub scoped to that language,
  `/{spec_id}?language={language}`, and is recorded as that page.
- Implementation detail: `/{spec_id}/{language}/{library}` (e.g.
  `/scatter-basic/python/matplotlib`).
- Interactive view is no longer a separate route — the detail page toggles
  between static preview and iframe via `?view=interactive`. The query
  string is **not** included in Plausible URLs (canonical only).
- Marketing subdomain `python.anyplot.ai` rewrites internally; canonical
  in HTML points back to `anyplot.ai/{spec_id}/python[/{library}]` so all
  pageviews show up under the main domain.

Historical data before 2026-04-14 uses un-prefixed paths
(`/{spec_id}`); data between 2026-04-14 and 2026-04-20 uses the legacy
`/python/{spec_id}[/{library}]` prefix. Both ranges remain visible in
Plausible but are no longer produced.

### Filter-based pageviews

Two pages have a query that names a different page: the gallery's filters and
a spec hub's language scope. For those, the query is appended to the page's
own path as `/{category}/{value}` pairs (`buildPlausibleUrl()` in
`app/src/hooks/useAnalytics.ts`):

```
https://anyplot.ai/{pathname}/{category}/{value}/{category}/{value}/...
```

Every other page is recorded by its path alone, whatever its query. An
implementation page stays one page with the carousel's `?language=` scope and
with `?view=interactive`, and its language segment is recorded in lowercase.
The agent chat stays `/agent` with the `?spec=&library=&language=` it opens
with.

The gallery lives at `/plots`, so its filter views are recorded under
`/plots/...`; on a spec hub the spec path comes first.
Until PR #9625 (2026-07-10) the reserved prefix was stripped, so older data
records the same gallery filters without `/plots` (`/lib/matplotlib`).

**Ordered categories**: `lang`, `lib`, `spec`, `plot`, `data`, `dom`, `feat`, `dep`, `tech`, `pat`, `prep`, `style`, `language`

**Examples (gallery)**:
- `/plots?lib=matplotlib` → `https://anyplot.ai/plots/lib/matplotlib`
- `/plots?lib=matplotlib&plot=scatter` → `https://anyplot.ai/plots/lib/matplotlib/plot/scatter`
- `/plots?lib=matplotlib,seaborn` → `https://anyplot.ai/plots/lib/matplotlib,seaborn` (OR logic)
- `/plots?lib=matplotlib&lib=seaborn` → `https://anyplot.ai/plots/lib/matplotlib/lib/seaborn` (AND logic)
- `/plots?spec=manhattan-gwas` → `https://anyplot.ai/plots/spec/manhattan-gwas`

**Examples (spec routes)**:
- `/scatter-basic?language=python` → `https://anyplot.ai/scatter-basic/language/python`

One spec is therefore recorded under three families of paths: gallery views
filtered to it (`/plots/spec/{spec_id}`, plus any other filter segments), the
hub (`/{spec_id}`, and `/{spec_id}/language/{language}` when the carousel is
scoped) and its implementation pages (`/{spec_id}/{language}/{library}`).
Filter Pages by "contains `{spec_id}`" to see them together. "contains" also
matches longer ids that include this one (`line-basic` inside
`sparkline-basic`); for such ids use the Stats API `matches` operator with the
id anchored on a path segment, for example `[/,]line-basic([/,]|$)` — a comma
counts as a boundary because OR-filtered gallery views record
`/plots/spec/a,b`.

**Benefits**:
- Plausible shows popular filter combinations
- No manual event tracking needed for filter changes
- URL structure clearly shows user's browsing context

### Pages

| URL | Description |
|-----|-------------|
| `/` | Home page (no filters) |
| `/plots` | Plots page (filter grid of all implementations) |
| `/specs` | Specs page (alphabetical spec list) |
| `/libraries` | Libraries listing |
| `/palette` | Color palette reference |
| `/about` | About page |
| `/legal` | Legal notice, privacy policy, transparency |
| `/mcp` | MCP server documentation (AI assistant integration) |
| `/stats` | Platform statistics (library scores, coverage, tags, top implementations) |
| `/map` | Network map of specs clustered by visual similarity |
| `/debug` | Pipeline status dashboard (spec coverage, feedback, agent cases, ping); the agent cases section sends no event of its own |
| `/agent` | The "Use with my data" agent chat (experimental, public since 2026-11-02), one page for visitors and admins since 2026-11-06; recorded without its query string, and only for a visitor: an admin's use records nothing (see [Agent chat](#agent-chat)). Since 2026-11-11 a visitor's visit is recorded whatever the page shows, also while the public lane is closed or the query names no catalogue pair; until then only a visit that opened a session was. `agent_open` still counts only those. In a build without `VITE_ENABLE_AGENT_CHAT=true` the address is the 404 page. `/debug/agent` only redirects here since 2026-11-06 and records nothing; until then it was the admin's chat page and recorded `/debug/agent` |
| `/{spec_id}` | Cross-language spec hub (all implementations across all languages); `/{spec_id}/language/{language}` when the carousel is scoped to one language |
| `/{spec_id}/{language}` | Records nothing: it redirects to the hub scoped to that language, which is recorded as `/{spec_id}/language/{language}` |
| `/{spec_id}/{language}/{library}` | Implementation detail (preview ↔ interactive toggle) |
| any other path | The 404 page, under the path that was asked for (since 2026-11-11) |

**Total pageview tracking**: `RootLayout` sends every page's pageview (see
[When a pageview is sent](#when-a-pageview-is-sent)).

## Custom events

The app sends eleven custom events, and no others. The set is closed in the
code: `AnalyticsEvent` in `app/src/hooks/useAnalytics.ts` names them, every
component receives the sender as that type, and the compiler refuses a name
that isn't in it. Before 2026-11-12 the app sent 42 event names, 23 of them
without a goal, so they were counted and shown nowhere.

| Event | Properties | Sent by | Counts |
|-------|------------|---------|--------|
| `copy_code` | `spec`, `library`, `method`, `page` | `ImageCard.tsx`, `SpecPage.tsx`, `SpecTabs/CodeTab.tsx`, `agent-chat/ResultCard.tsx` | A visitor copies an implementation's code: the primary conversion |
| `download_image` | `spec`, `library`, `page` | `SpecPage.tsx` | A visitor downloads a plot's PNG |
| `interactive_open` | `spec`, `library` | `SpecOverview.tsx` | A visitor opens an implementation's interactive view from the spec hub. Until 2026-11-12 the event was named `open_interactive` |
| `search` | `query`, `category` | `FilterBar/FilterSearch.tsx` | A visitor searches the gallery and picks a result |
| `search_no_results` | `query` | `FilterBar/FilterSearch.tsx` | A search finds nothing: what the catalogue lacks |
| `feedback_submitted` | `source`, `spec`, `library` | `FeedbackWidget.tsx`, `useQuickReaction.ts` | A visitor sends feedback or votes on a plot |
| `agent_open` | `spec`, `library`, `source` | `AgentChatPage.tsx` | A visitor opens the agent chat for a plot |
| `agent_plot_rendered` | `spec`, `library`, `status`, `repaired` | `useAgentSession.ts` | The agent chat ends a plot run |
| `plots_scrolled` | `share`, `results`, `filtered` | `usePlotsScrolled.ts` | How far a visitor got through the gallery |
| `ui_feature` | `feature` | Twelve places, see [Feature use](#feature-use-ui_feature) | A visitor uses a feature of the interface, once per feature and visit |
| `nav_click` | `source`, `target`, `spec`, `library` | The landing page, see [Landing page clicks](#landing-page-clicks-nav_click) | A visitor goes on from an element of the landing page |

Every property holds a value from a closed list or a catalogue id, with one
exception: `query` is what a visitor typed (see [Search](#search)). Every
pageview and event also carries the ambient `theme` (`dark` or `light`), the
theme in effect, which `RootLayout` sets through `setAnalyticsAmbientProps`.

### Conversions

`copy_code` says how the code was copied in `method`:

- `card`: the copy button on a gallery card
- `image`: the copy button on a plot image of a spec page
- `tab`: the copy button in the code tab
- `agent`: the copy button on an agent chat result card (the adapted code)

`copy_code` and `download_image` say where in `page`, with the values of
[the `page` property](#the-page-property). To see whether visitors copy from
the gallery or after opening a plot, break `copy_code` down by `page`.

### Search

`search` fires when a visitor picks a search result, with the `category` of
the result (`lib`, `spec`, `plot`, `data`, `dom`, `feat`, `dep`, `tech`, `pat`,
`prep`, `style`). `search_no_results` fires when a query of at least two
characters finds nothing inside the active filters, 200 ms after the last
keystroke. Such a query also fires it when the dropdown offers `.search_all()`,
because the same query finds matches without the filters.

`query` is the one property a visitor writes, and the public dashboard lists
it. `normalizeQuery()` therefore sends it in lowercase, with single spaces,
and cut at 40 characters (`MAX_QUERY_LENGTH`): "Scatter", "scatter " and
"SCATTER" are one entry, catalogue words and spec names fit, and a long text
pasted into the box by mistake doesn't stand there in full.

### Feedback

`feedback_submitted` fires when the server stored a feedback entry. `source`
says which control sent it:

- `widget_quick`: a one-tap 👍 or 👎 from the feedback button's quick stack
- `widget_form`: the feedback form
- `plot_vote`: a 👍 or 👎 on a plot, which also carries the `library` the vote
  is about

`spec` is set on a spec page. The reaction, the text and the contact are in
the database, not in the event.

### Agent chat

The "Use with my data" chat (`app/src/pages/AgentChatPage.tsx`, design in
[Agent network design](../concepts/agent-network.md)) sends two events, with
enum properties only. No event carries message text, pasted data, column
names, code or a dataset size. The events exist only in builds with
`VITE_ENABLE_AGENT_CHAT=true`, and like every event they fire only on
`anyplot.ai`.

| Event | What its properties say |
|-------|-------------------------|
| `agent_open` | The chat page opened for a visitor. `source` is `plot_page` when a plot page's `.use_my_data() →` led there, `spec_hub` when the spec hub's header entry did, `plot_of_the_day` when the landing page's plot of the day did, `landing` (a line that led there on 2026-11-02 only), and `direct` otherwise: a typed URL, a bookmark, a reload |
| `agent_plot_rendered` | A turn's `plot` event arrived. `status` is `ok`, `needs_attention`, `failed`, or `not_ready`; `repaired` is `yes` when the run needed its repair round, else `no`. A plot the server refuses before the run sends no `plot` event, so it fires none |

`copy_code` on a result card carries `method: agent` and `page: agent_chat`
plus the `spec` and `library` of the version.

**An admin's use is not counted.** Since 2026-11-06 one page at `/agent` serves
visitors and admins (`/debug/agent` only redirects there). While the page
serves an admin's browser — on the admin lane, in the admin menu's "view as
visitor", and after an expired admin session — it records no pageview and no
event: `AgentChatPage` mutes the analytics (`app/src/analytics/mute.ts`), which
stops every `useAnalytics` call while the page is mounted, the site's own
events on that page included, and unmutes them when it unmounts, before the
next page records its pageview. The mute is a layout effect, so it is on
before the layout sends the page's pageview, and an admin's browser is known
at the first render: it carries the admin hint, and the check that follows
only picks the lane. Until 2026-11-06 the admin chat recorded the
pageview `/debug/agent` and the same events as a visitor's.

**What a session did step by step is not on the public dashboard.** The chat's
pastes, files, confirmations, data changes, refusals, saves, feedback and cut
streams are content-free lines of the server's usage telemetry in BigQuery
(`data_input`, `chat_turn`, `pipeline_run`, `outcome`, `plot_switch`,
`language_offer`): see [Agent usage telemetry](agent-telemetry.md). Until
2026-11-12 ten more Plausible events repeated part of it from the browser (see
[Events that ended](#events-that-ended)); most of the chat's sessions were the
owner's own, and the numbers sat on a public dashboard nobody could read them
from. A copy, a download, a save and a sent feedback still send the outcome
beacon (`POST /debug/agent/sessions/{sid}/outcome`), which is not a Plausible
event and fires on every host.

### Gallery scroll (`plots_scrolled`)

How far a visitor got through the gallery, once per visit to `/plots` (since
2026-11-11). The event is sent when the visit ends: the visitor leaves the
page, or the tab goes away. A visit without scrolling sends none, and the
offset the page restores from an earlier visit doesn't count, only a point
below it.

- `share` is the deepest point as a share of the result list, in percent
  bands: `0-10`, `10-25`, `25-50`, `50-75`, `75-100`. It is the percentage the
  filter bar shows, which scales the loaded part up to the whole list.
- `results` is the size of that list: `1-24`, `25-99`, `100-999`, `1000+`.
- `filtered` is `true` or `false`.

When the filters change during a visit, all three describe the list the
deepest point was reached in, and the event is recorded under that list's page
(`/plots/lib/matplotlib`).

### Feature use (`ui_feature`)

One event answers one question per feature of the interface: is it used at
all? `feature` names the feature, and the event carries nothing else. It is
sent once per feature and visit, so the goal's unique visitors and its events
both read as "visits that used it", and a visitor who toggles a tab forty
times weighs as much as one who did it once.

| `feature` | The use | Sent by |
|-----------|---------|---------|
| `tab_toggle` | Opens or closes a tab under a plot (code, specification, implementation, quality) | `SpecTabs/index.tsx` |
| `view_mode_change` | Switches an implementation between its preview and its interactive view | `SpecDetailView.tsx` |
| `grid_resize` | Switches the gallery between normal and compact cards | `ToolbarActions.tsx` |
| `filter_remove` | Removes a filter in the gallery, one or all at once | `useFilterState.ts` |
| `random_filter` | Asks the gallery for a random filter (the shuffle icon or the space bar) | `useFilterState.ts` |
| `plot_rotate` | Clicks an image on `/specs` to see the next library's version | `SpecsListPage.tsx` |
| `library_filter` | Filters `/libraries` by language or framework | `LibrariesPage.tsx` |
| `theme_toggle` | Cycles the theme (system, light, dark) | `MastheadRule.tsx` |
| `feedback_open` | Opens the feedback button's quick stack | `FeedbackWidget.tsx` |
| `map_node_click` | Clicks a node on `/map` and goes to its spec | `MapPage.tsx` |
| `map_node_pin` | On touch, taps a node on `/map` to pin its preview | `MapPage.tsx` |
| `map_search_select` | Picks a result of the `/map` search | `sections/map/useMapSearch.ts` |

The list is `UI_FEATURES` in `useAnalytics.ts`, and `feature` is typed with
it. Until 2026-11-12 each feature was an event of its own with its own
properties (which tab, which filter, which theme): twelve goals, or none, for
one question.

**A visit is Plausible's.** Plausible ends a visit after 30 minutes without a
pageview or an event. `trackEvent` keeps the features the current visit used
in memory and starts over after the same 30 minutes without anything sent, so
a tab left open overnight counts a feature again the next day. Nothing is
stored in the browser: a reload starts over too, which can count a feature
twice in one visit and never a visitor twice.

### Landing page clicks (`nav_click`)

`nav_click` says which element of the landing page a visitor went on from:
`source` names the element and `target` where it leads. Some sources also
carry `spec` and `library`.

| `source` | Element | Leads to |
|----------|---------|----------|
| `hero_cta_browse`, `hero_mcp`, `hero_github` | The hero's call to action and its two secondary links (`HeroSection.tsx`) | `/plots`, `/mcp`, GitHub |
| `hero_use_my_data` | `# new: pick any plot, then .use_my_data() →` under the hero, shown while the agent chat's public lane is open | `/plots` |
| `potd_terminal_image`, `potd_terminal_filename`, `potd_terminal_github` | The plot of the day in its terminal frame (`PlotOfTheDayTerminal.tsx`), with `spec` and `library` | The plot's page, GitHub |
| `featured_thumb` | A plot of the featured grid, with `spec` | The spec's hub |
| `library_card` | A library card, with `library` | `/plots` filtered to the library |
| `section_header` | The link of a section header: `specs.all()`, `libraries.all()`, `palette.explore()`, `map.explore()` | `/specs`, `/libraries`, `/palette`, `/map` |
| `map_teaser_preview` | The map teaser's image | `/map` |
| `specs_more_link` | `+ N more in the catalogue →` | `/specs` |
| `suggest_spec_link` | `spec.suggest()` | A GitHub issue form |
| `masthead_branch`, `masthead_release` | `main` and the version in the masthead, which only the landing page shows | GitHub |

Until 2026-11-12 the event also fired for the menu bar, the logo, the
breadcrumb and the gallery's `{spec_id}.compare()` link, on every page: 76 %
of its events were menu clicks, which the pageview that follows already
records. `SectionHeader` is used on other pages too (the tiles on `/stats`)
and sends the event only on the landing page.

### Events that ended

Their history stays visible in Plausible; their goals and properties are
removed from the dashboard (see [Dashboard checklist](#dashboard-checklist)).

| Ended | Event | Where its number is now |
|-------|-------|-------------------------|
| 2026-11-12 | `tab_toggle`, `view_mode_change`, `grid_resize`, `filter_remove`, `random_filter`, `plot_rotate`, `library_filter`, `theme_toggle`, `feedback_opened`, `map_node_click`, `map_node_pin`, `map_search_select` | `ui_feature`, by `feature` (`feedback_opened` as `feedback_open`) |
| 2026-11-12 | `open_interactive` | Renamed `interactive_open` |
| 2026-11-12 | `external_link` | The script's `Outbound Link: Click`, which records the same click with the link's address |
| 2026-11-12 | `internal_link`, `tag_click`, `library_click`, `stats_top_impl_click`, and `nav_click` from the menu, the logo, the breadcrumb and the gallery | The pageview of the page the link leads to |
| 2026-11-12 | `suggest_spec`, `report_issue` | `Outbound Link: Click`: both are links to GitHub |
| 2026-11-12 | `page_not_found` | The pageview of the address that was asked for. An implementation that is gone redirects to the spec's hub, so it records two pageviews: the address asked for, then the hub |
| 2026-11-12 | `agent_data_parsed`, `agent_data_confirmed`, `agent_data_prepared`, `agent_data_undo`, `agent_data_file`, `agent_input_routed`, `agent_guardrail_block`, `agent_session_saved`, `agent_result_feedback`, `agent_turn_resumed` | The server's usage telemetry ([Agent usage telemetry](agent-telemetry.md)) |
| 2026-11-11 | `og_image_view` | The share counters in the database ([Shared links](#shared-links)) |
| 2026-11-08 | `LCP`, `CLS`, `INP`, `FCP`, `TTFB`, and the script's `Form: Submission` | Nowhere: see [Core Web Vitals are not tracked](#core-web-vitals-are-not-tracked) and [Setup](#setup) |
| earlier | `potd_dismiss`, and the `nav_click` sources `potd_image`, `potd_title`, `potd_source_link` | Nowhere: the dismissible plot-of-the-day banner is gone |

### Core Web Vitals are not tracked

The site sent `LCP`, `CLS`, `INP`, `FCP`, and `TTFB` as custom events from
2026-03-10 (#4741) to 2026-11-08 and stopped for three reasons:

- They were 44 % of the billable events (17,044 of 38,818 in the 28 days
  before), and `FCP` and `TTFB` had no goal, so they were billed and shown
  nowhere.
- Every custom event un-bounces its visit. Visits with a vitals event bounced
  at 0 %, visits without one at 88 %, so the dashboard's bounce rate of about
  5 % was an artifact. Expect it to rise to a realistic value from 2026-11-08.
- No code change in nearly eight months was motivated by a vitals number.

Read Core Web Vitals from [PageSpeed Insights](https://pagespeed.web.dev/)
when you need them: it reports lab numbers and, through the Chrome UX Report,
field numbers. The events before 2026-11-08 stay visible in Plausible.

---

## The analytics shield

`app/nginx.conf` answers `/api/event` itself with `202` when the sender's user
agent is a crawler (`$is_bot`) or automation (`$is_headless_client`), so the
event never reaches Plausible. Nothing is blocked: such a client still gets
every page, it is just not counted, and the `202` mirrors Plausible's accepted
response so the client doesn't retry. The shield exists since audit 2026-07-08
(High #7), when synthetic traffic inflated visitor counts by about 40 %.
The API itself sends Plausible nothing since 2026-11-11 (see
[Shared links](#shared-links)).

Both maps name a client by its own token: a crawler's name, a headless
browser, an HTTP library, or an empty user agent. Neither matches a browser's
user agent, whatever its version, because a farm that wears one shares it with
real visitors, and nginx would drop their events without anyone seeing it.
Such a farm's traffic from hosting networks is challenged at the Cloudflare
edge instead, where a person who gets caught sees the challenge and can pass
it. Its traffic through residential addresses is deliberately left alone,
because those addresses are shared with people, so that share can still reach
the dashboard. See "Security rules" in
[`infra/cloudflare/README.md`](../../infra/cloudflare/README.md#a-managed-challenge-for-hosting-network-asns).
`tests/unit/api/test_analytics_event_proxy.py` fails if a browser's user agent
loses its events, and it carries the shapes farms have worn.

### The Windows 10 Chrome farm (2026-11-09)

Since 2026-11-03 a crawler farm has loaded about 17 spec pages per hour around
the clock, from a new exit IP on almost every request: about 64 % from Tencent
Cloud (AS132203), the rest through residential proxies. It runs the page's
JavaScript, so its events arrive as a browser's. In the 7 days before
2026-11-08 it made up 675 of 1,451 dashboard visitors.

On 2026-11-09, #12860 added an entry to `$is_headless_client` that matched the
farm's user agents, Windows 10 Chrome 100 to 139. It was removed the same day:

- The farm moved to Chrome 148 to 150 on Windows and macOS that day, so the
  entry no longer matched it and caught 14 events all day.
- The entry kept dropping the events of real visitors on a pinned old Chrome,
  about 1.8 % of visits (37 of 2,069 in the 28 days before 2026-11-08).

The one mechanism against the farm is now the Cloudflare Managed Challenge for
four hosting-network ASNs: Tencent (132203 and 45090), Leaseweb (394380), and
Huawei Cloud (136907), with verified bots excluded. The farm's residential
share is deliberately left alone. See
[A Managed Challenge for hosting-network ASNs](../../infra/cloudflare/README.md#a-managed-challenge-for-hosting-network-asns).

---

## AI and crawler traffic (retired bot site)

From 2026-08-18 until the machine-read lines replaced it in November 2026, a
second Plausible site, `bots.anyplot.ai`, recorded three server-side events:
`bot_fetch` (a catalogue page an AI assistant or search crawler requested),
`asset_fetch` (one implementation's code or one spec's detail fetched through
the API), and the machine side of `og_image_view`. It saw about 1.7 % of the
real crawler reads, because Plausible drops events from crawler and datacenter
addresses, and 71 % of its last week was a scanner that spoofed crawler user
agents. Its history is exported to
`~/backups/plausible/bots.anyplot.ai-2026-11-09/` on the owner's machine (four
Stats API pulls and a README; 7,184 `bot_fetch` events since 2026-08-18). The
site stays dormant for 30 days after the change deployed and is then deleted;
until then its dashboard shows a flat line, which is expected.

Machine reads are now one content-free line per request by a crawler, an AI
assistant, or an MCP client, written to Cloud Logging and read in BigQuery:
[Machine readers](machine-readers.md). The `kind` taxonomy and the vendor
table, `AI_AGENTS` in `api/analytics.py`, are described there.

### A crawler's fetch of a preview image is a machine read

A search or AI crawler that fetches a page's og:image shared nothing. Since
`robots.txt` began permitting `/og/` those fetches arrive in volume: in the
week before 2026-11-11 the API served about 2,400 preview images, and about
2,250 of them went to crawlers (PerplexityBot, Googlebot-Image, AhrefsBot,
bingbot, and Amazonbot lead). The API writes its machine-read line for each,
with `surface` `og`, and the share counter below counts none of them:
`detect_ai_agent` decides which is which.

## Shared links

A messenger or a social network that shows a link's preview fetches the page's
og:image from the API. It runs no JavaScript, so no page analytics sees it: the
fetch is the one trace a share leaves. Since 2026-11-11 the API counts it
itself, in the database, and nothing about it goes to Plausible.

Until then every preview image sent an `og_image_view` event to Plausible, with
the fetcher's address and user agent. That measured little. Plausible drops
every user agent it knows as a bot, so Slack, X, LinkedIn, and Teams never
showed; of 402 events in the 28 days before the change, 371 had the platform
`unknown` and 31 were WhatsApp. Tests and local requests sent real events, and
so did a fetch that ended in a 404.

### What is counted

`api/shared_links.py` adds one to a counter after the API served a preview
image. A counter is a row of the `link_shares` table (see
[Database](database.md)): the UTC day, the platform, and the page, with the
plot it shows. A row holds no address, no user agent, and no time of day, so
it says how often a page was shared and never by whom. The rows are kept
without a time limit.

A row also says whether Cloudflare verified the fetcher as a bot it knows
(`verified`, from the `X-Verified-Bot-Category` header that
[Machine readers](machine-readers.md#verified-or-not) describes; a request to
the raw `*.run.app` origin is never verified, because only the edge sets that
header). The platform's name is read from the user agent, which a client
writes itself, and the row keeps no user agent: the verdict is the one thing
left that tells a platform's own fetch from a scanner that signs as one. It is
a diagnosis, not a filter. WhatsApp and Signal fetch the preview from the
sender's own phone, which nobody can verify, so the public numbers count a
share whatever the verdict, and `/debug` shows the verified part beside each
total. A platform Cloudflare does verify, such as Slack or LinkedIn, whose
shares are mostly unverified is being imitated.

Who fetched decides what the fetch is:

| Fetched by | Counted as |
|---|---|
| A crawler or an AI assistant (`detect_ai_agent`) | Nothing here: a machine read, see above |
| One of the preview platforms below | A share on that platform |
| Anything else: a scanner, a browser that opens the image, an app the list doesn't know | `other`, which the public numbers leave out |

Four rules keep the number honest and the counter harmless:

- **Only the production service counts** (`settings.is_production`). A test or
  a local request for an image counts nothing.
- **Only a served image counts.** A fetch that ends in a 404 is no preview
  anyone saw.
- **The write never delays or fails the image.** It runs in the background, and
  a failure is logged with the exception's class and goes no further. That
  covers the table not being there yet: the migration reaches production
  through `sync-postgres.yml`, which can run after the deploy of the code that
  writes.
- **The writes never crowd out the API.** They hold at most two of the API's 15
  database connections (`WRITE_CONNECTIONS`); the others wait their turn, a few
  milliseconds each. Beyond 256 writes waiting (`MAX_PENDING_WRITES`) a fetch is
  not counted: that many is a flood, not sharing.

### Platforms

The platform is one name from a closed set, read from the user agent, which is
then dropped. WhatsApp and Messages are asked first; after them the first
matching token wins (`SHARE_TOKENS`):

| Platform | Token in the user agent | Note |
|---|---|---|
| `imessage` | `facebookexternalhit` and `twitterbot` together | Apple's Messages signs as both crawlers at once (`… facebookexternalhit/1.1 Facebot Twitterbot/1.0`), which neither does itself |
| `telegram` | `telegrambot` | Asked before Twitter: Telegram signs as `TelegramBot (like TwitterBot)` |
| `twitter`, `facebook`, `linkedin`, `pinterest`, `reddit`, `tumblr`, `mastodon` | `twitterbot`, `facebookexternalhit`, `linkedinbot`, `pinterestbot`, `redditbot`, `tumblr`, `mastodon` | Social networks |
| `slack` | `slackbot`, `slack-imgproxy` | Slack reads the page as Slackbot-LinkExpanding and fetches the image through its image proxy |
| `discord`, `viber`, `snapchat` | `discordbot`, `viber`, `snapchat` | Messengers |
| `teams` | `skypeuripreview`, `microsoft teams` | Microsoft's preview service still signs as SkypeUriPreview; Skype closed in May 2025 |
| `github` | `github-camo` | GitHub's image proxy, for an image linked in a README, an issue, or a comment |
| `embedly`, `quora`, `outbrain`, `rogerbot`, `showyoubot` | The name itself (`quora link preview` for Quora) | Link preview services |
| `whatsapp` | `WhatsApp/` with a full version, such as `WhatsApp/2.23.18.78 i` | The real app |
| `whatsapp-lite` | `WhatsApp` without a full version | An app that borrows the name to pass rate limits, which Signal does ([Signal-Android #10060](https://github.com/signalapp/Signal-Android/issues/10060)); the tile shows it as "signal & similar" |
| `other` | Nothing above, and no crawler | Not a share |

The tokens `slack-imgproxy`, `skypeuripreview`, and `github-camo` come from a
week of the API's request log (2026-11-04 to 2026-11-11): the image itself is
often fetched by a proxy that doesn't carry the name of the bot that read the
page. A new platform shows up as a rising `other` on `/debug`; the request log
names it, and it gets a row here and a token in `SHARE_TOKENS`.

### Preview images and their cache

| Endpoint | Image | Counted as page |
|----------|-------|-----------------|
| `/og/home.png` | Static image of the home page | `home`, whatever the query |
| `/og/plots.png` | Static image of the plots page | `plots` |
| `/og/{spec_id}.png` | Collage of a spec's best implementations | `spec_overview`, with the spec |
| `/og/{spec_id}/{language}/{library}.png` | One implementation, branded | `spec_detail`, with spec, language, and library |

Every preview image answers `Cache-Control: public, max-age=300`. A fetch the
edge answers from its cache never reaches the API, so it is a share nobody
counts. Until 2026-11-11 the images were cached for an hour (plot pages) and a
day (home and plots), so most repeated previews were invisible. Rendering is
not what the five minutes cost: the images stay in the API's own cache.

### Where the numbers appear

- **`/stats`, the "shared links" tile** (`GET /insights/shared-links`): the
  shares of the last 28 UTC days as one bar per day, the platforms with their
  totals, and the five most shared plot pages. A spec's hub and one
  implementation of it are entries of their own. `other` is not in these
  numbers. The answer is kept for an hour.
- **`/debug`, the "shared links" section** (`GET /debug/shared-links`, admin
  only): the same numbers read fresh, plus `other`, and beside each platform's
  total and beside `other` how many of the fetches Cloudflare verified.

### What the count can't see

- A preview the platform still holds from an earlier share. Most platforms keep
  a link's preview for hours or days and fetch it once for many readers.
- A fetch the edge answered from its cache, within the five minutes.
- Who shared, where, or to how many people: one fetch is one count.

---

## Plausible dashboard configuration

Plausible shows a custom event only as a goal, and a property only once it is
registered, so the dashboard holds exactly what the app sends. The Sites API
can read both lists (`GET /api/v1/sites/goals` and
`/api/v1/sites/custom-props` with the Stats API key); writing them needs an
Enterprise plan, so you change them in the dashboard.

### Goals

**Go to**: Site settings → Goals → Add goal

| Goal | Type | Says |
|------|------|------|
| `copy_code` | Custom event | Code copies, the primary conversion |
| `download_image` | Custom event | Image downloads |
| `interactive_open` | Custom event | Interactive views opened from a spec hub |
| `search` | Custom event | Searches that led to a result |
| `search_no_results` | Custom event | Searches that found nothing: content gaps |
| `feedback_submitted` | Custom event | Feedback entries and plot votes |
| `agent_open` | Custom event | Opens of the agent chat, and where they came from |
| `agent_plot_rendered` | Custom event | Agent chat plot runs, by outcome |
| `plots_scrolled` | Custom event | How far visitors get through the gallery |
| `ui_feature` | Custom event | Which features of the interface are used |
| `nav_click` | Custom event | Which element of the landing page visitors go on from |
| Visit /plots | Pageview, `/plots*` | Visitors who reached the gallery, with any filters |
| Scroll 90% on / | Pageview, scroll depth | Visitors who saw the whole landing page |
| Outbound Link: Click | The script's own | Clicks on links to other sites |

### Custom properties

**Go to**: Site settings → Custom properties → Add property

| Property | Values | Sent with |
|----------|--------|-----------|
| `spec` | A specification id, such as `scatter-basic` | `copy_code`, `download_image`, `interactive_open`, `feedback_submitted`, `agent_open`, `agent_plot_rendered`, `nav_click` |
| `library` | A library id: `matplotlib`, `seaborn`, `plotly`, `bokeh`, `altair`, `plotnine`, `pygal`, `letsplot`, `ggplot2`, `makie`, `chartjs`, `d3`, `echarts`, `highcharts`, `muix` (`LIBRARIES_METADATA` in `core/constants.py`) | The same events as `spec` |
| `method` | `card`, `image`, `tab`, `agent` | `copy_code` |
| `page` | `home`, `plots`, `spec_overview`, `spec_detail`, `agent_chat`, `other` | Every pageview, `copy_code`, `download_image` |
| `source` | For `nav_click` the element (see [Landing page clicks](#landing-page-clicks-nav_click)); for `agent_open` `plot_page`, `spec_hub`, `plot_of_the_day`, `landing`, `direct`; for `feedback_submitted` `widget_quick`, `widget_form`, `plot_vote` | `nav_click`, `agent_open`, `feedback_submitted` |
| `target` | A path of the site, or `github` and other labels of an outbound element | `nav_click` |
| `query` | The search text: lowercase, single spaces, at most 40 characters | `search`, `search_no_results` |
| `category` | `lib`, `spec`, `plot`, `data`, `dom`, `feat`, `dep`, `tech`, `pat`, `prep`, `style` | `search` |
| `status` | `ok`, `needs_attention`, `failed`, `not_ready` | `agent_plot_rendered` |
| `repaired` | `yes`, `no` | `agent_plot_rendered` |
| `share` | `0-10`, `10-25`, `25-50`, `50-75`, `75-100` | `plots_scrolled` |
| `results` | `1-24`, `25-99`, `100-999`, `1000+` | `plots_scrolled` |
| `filtered` | `true`, `false` | `plots_scrolled` |
| `feature` | The twelve of [Feature use](#feature-use-ui_feature) | `ui_feature` |
| `theme` | `dark`, `light`: the theme in effect, resolved from the three-state mode | Every pageview and event |

### Funnels and breakdowns

The questions the dashboard answers, and where:

- **Which plots and libraries are copied?** `copy_code` by `spec` and by
  `library`.
- **Do visitors copy from the gallery or after opening a plot?** `copy_code`
  by `page`.
- **What is searched, and what is missing?** `search` and `search_no_results`
  by `query`.
- **Which features are used at all?** `ui_feature` by `feature`.
- **Where does the landing page send visitors?** `nav_click` by `source`.
- **How many visits get from a kind of page to a copy?** A funnel of pageview
  steps filtered by `page` (`home`, then `spec_detail`) and `copy_code`. The
  gallery is the page goal "Visit /plots".

## Reading stats — backend → Plausible Stats API

The backend sends Plausible nothing. It reads aggregate visitor data from
Plausible to render the unique-visitors chart at the top of the public stats
page.

- **Endpoint**: `GET /insights/visitors` (in `api/routers/insights.py`)
- **Upstream call**: `POST https://plausible.io/api/v2/query` with body
  `{"site_id": "anyplot.ai", "metrics": ["visitors"], "date_range": "28d", "dimensions": ["time:day"]}`
  (28d matches Plausible's own default "Last 28 days" report so totals here
  align with the dashboard at plausible.io/anyplot.ai)
- **Auth**: `Authorization: Bearer ${PLAUSIBLE_API_KEY}` (Stats API key
  created in Plausible → Account Settings → API Keys, then mirrored to
  GCP Secret Manager as `PLAUSIBLE_API_KEY` for Cloud Run)
- **Caching**: 1h stale-while-revalidate via `get_or_set_cache` so
  traffic spikes stay well under Plausible's 600-req/h rate limit.
- **Graceful degradation**: When `PLAUSIBLE_API_KEY` is unset or the
  upstream call fails, the endpoint returns `points: []` (empty list).
  The frontend distinguishes this from "real zeros" — an empty list
  triggers the "visitor data unavailable" placeholder, while a non-empty
  list with low/zero values renders the normal 30-bar chart. The
  dashboard endpoint is unaffected because visitors load on a separate
  fetch.

## Code locations

- **Plausible setup**: `app/index.html` (the inline script at the end of `<head>`)
- **Analytics shield**: the `$is_bot` and `$is_headless_client` maps and both `location = /api/event` blocks in `app/nginx.conf`
- **Analytics hook**: `app/src/hooks/useAnalytics.ts`: the closed event set (`AnalyticsEvent`, `TrackEvent`), `UI_FEATURES` and the once-per-visit rule, `normalizeQuery()`, `pageKind()`, `buildPlausibleUrl()`
- **Admin mute**: `app/src/analytics/mute.ts`
- **Pageview sending**: the layout effect in `app/src/layouts/RootLayout.tsx` (every navigation) and `app/src/hooks/useUrlSync.ts` (a filter change on `/plots`)
- **Redirects that record nothing**: `app/src/routes/redirects.ts`
- **Gallery scroll event**: `app/src/hooks/usePlotsScrolled.ts`, with the percentage from `app/src/utils/galleryScroll.ts`
- **Event sending**: a component calls `useAnalytics().trackEvent`, or receives it as an `onTrackEvent` or `onTrack` prop of the type `TrackEvent`
- **Agent chat events**: `app/src/pages/AgentChatPage.tsx` (`agent_open`, admin mute), `app/src/hooks/useAgentSession.ts` (`agent_plot_rendered`), `app/src/sections/agent-chat/ResultCard.tsx` (`copy_code`)
- **Stats API consumer**: `_fetch_plausible_visitors()` in `api/routers/insights.py`
- **Shared links** (not in Plausible): `record_share()` in `api/shared_links.py`, called by `api/routers/og_images.py`; a crawler's fetch is a machine read instead (`api/machine_reads.py`, [Machine readers](machine-readers.md))

## Add or change an event

1. Decide whether it needs an event at all. A click on a link is recorded by
   the pageview it leads to, or by `Outbound Link: Click`. A use of a feature
   is a value of `ui_feature`: add it to `UI_FEATURES`.
2. For a new event, add its name to `AnalyticsEvent` in
   `app/src/hooks/useAnalytics.ts`. The compiler then accepts it everywhere.
3. Send only values from a closed list or catalogue ids. Reuse a registered
   property before you add one.
4. Describe the event here, and add the goal and any new property to
   [Plausible dashboard configuration](#plausible-dashboard-configuration).
5. After the deploy, register the goal and the property in Plausible, and
   delete what the change retired.

## Testing

**Development**: Tracking disabled (not on anyplot.ai domain)

**Production testing**:
1. Open https://anyplot.ai
2. Open browser console
3. Check for Plausible script load
4. Trigger events and verify in Plausible dashboard (may take 1-2 min)

**Debug mode**:
```javascript
// In browser console
window.plausible = function(...args) { console.log('Plausible:', args); };
```

To read what the live tracker script sends without recording anything, serve
a local build under `https://anyplot.ai` by request interception and answer
`/api/event` yourself.

---

## Dashboard checklist

The goals and properties change in phases, each after the deploy that stops
or starts its events: deleting a goal before its event stops only hides the
event.

- [x] Phase 1, after the vitals events stopped (2026-11-08): the `LCP`, `CLS`,
  and `INP` goals and the properties `rating` and `value` deleted
- [x] Phase 2, after the pageview timing (2026-11-11): the `plots_scrolled`
  goal and the properties `share`, `results`, and `filtered` added; the
  "Scroll 25% on /", "Scroll 50% on /", and "Scroll 75% on /" goals deleted,
  "Scroll 90% on /" kept; the page goal "Visit /plots" (`/plots*`) in place of
  "Visit /specs"
- [x] Phase 3, after the share counter (2026-11-11): the `og_image_view` goal
  and the properties `platform`, `language`, and the eleven `filter_*` entries
  deleted
- [ ] Phase 5, after the event set of 2026-11-12 is deployed:
  - Add the goals `ui_feature`, `interactive_open`, `feedback_submitted`,
    `agent_open`, and `agent_plot_rendered`
  - Add the properties `feature`, `status`, and `repaired`
  - Delete the goals `tab_toggle`, `plot_rotate`, `grid_resize`,
    `filter_remove`, `random_filter`, `theme_toggle`, `internal_link`,
    `external_link`, `tag_click`, `suggest_spec`, `report_issue`, and
    `open_interactive`
  - Delete the properties `action`, `destination`, `framework`, `from`,
    `has_contact`, `input_method`, `mode`, `open`, `param`, `reaction`,
    `size`, `spec_id`, `tab`, and `to`
  - Rebuild or delete the funnels that use a deleted goal

---

**Last Updated**: 2026-11-12
**Status**: Eleven custom events, each a dashboard goal; pageviews carry the kind of page; the agent chat's detail is in the server's telemetry and shared links in the database, not here
