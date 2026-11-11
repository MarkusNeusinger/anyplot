# Plausible analytics tracking

This document provides a comprehensive overview of Plausible Analytics implementation for anyplot.ai, including all tracked events, user interactions, and the required Plausible dashboard configuration.

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
  Outbound links and file downloads keep the script's defaults.
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
can't serve: the 404 page is recorded under the path that was asked for, next
to its `page_not_found` event (see [Diagnostics](#diagnostics)). Until
2026-11-11 a 404 recorded no pageview, and a spec page recorded its pageview
only once its data had loaded.

### Scroll depth

Plausible measures scroll depth itself, per pageview; the app sends no scroll
event for it. The dashboard keeps one scroll goal, "Scroll 90% on /": a visitor
saw the whole landing page.

The gallery at `/plots` loads its results in batches while the visitor
scrolls, so that page has no fixed height and its scroll depth says nothing.
`plots_scrolled` reports the gallery instead (see
[Feature usage](#feature-usage)).

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

### Conversions

| Event Name | Properties | Where | Description |
|------------|-----------|-------|-------------|
| `copy_code` | `spec`, `library`, `method`, `page` | ImageCard.tsx, SpecPage.tsx, SpecTabs.tsx, agent-chat/ResultCard.tsx | User copies code to clipboard |
| `download_image` | `spec`, `library`, `page` | SpecPage.tsx | User downloads PNG image |

**Copy methods**:
- `card`: Quick copy button on image card (home grid)
- `image`: Copy button on main image (spec page)
- `tab`: Copy button in Code tab
- `agent`: Copy button on an agent chat result card (the adapted code)

**Page values** (for user journey tracking):
- `home`: HomePage grid view
- `spec_overview`: SpecPage showing all library implementations
- `spec_detail`: SpecPage showing single library implementation
- `agent_chat`: the agent chat at `/agent` (a visitor's; an admin's use records nothing since 2026-11-06)

### Agent chat

The "Use with my data" chat (`app/src/pages/AgentChatPage.tsx`, design in
[Agent network design](../concepts/agent-network.md)) records enum properties
only. No event carries message text, pasted data, column names, code or a
dataset size: the size travels as a bucket. The events exist only in builds
with `VITE_ENABLE_AGENT_CHAT=true`, and like every event they fire only on
`anyplot.ai`. The feedback form's `# include data.csv` box starts unticked, so
`include_data` reads `no` unless the user ticked the box.

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
So every event below is a visitor's, and `agent_session_saved`, whose `.save()`
only an admin has, no longer fires in production.

| Event Name | Properties | Where | Description |
|------------|-----------|-------|-------------|
| `agent_open` | `library`, `source`, `spec` | AgentChatPage.tsx | The chat page opened for a visitor (until 2026-11-06 also for an admin). `source` is `plot_page` when the plot page's entry led there (`.use_my_data() →` beside the library carousel or beside the code tab's copy button; the `.adapt()` button on the image until 2026-11-02, under the same value), `spec_hub` when the spec hub's header entry did (`.use_my_data() →` at the top of `/{spec-id}`, which opens matplotlib where it is among the cards shown, else the first of them), `landing` when the landing page's line did (public lane, on 2026-11-02 only: the line now leads to `/plots`, tracked as `nav_click{source: hero_use_my_data}`; the chat still accepts the value), `plot_of_the_day` when the landing page's plot of the day did (`.use_my_data()` beside `github.open()` in its header, since 2026-11-04, for that plot's spec and library), `direct` otherwise (a typed URL, a bookmark, a reload) |
| `agent_data_parsed` | `status`, `size_bucket` | useAgentSession.ts | The pasted data came back from the parse. `status` ∈ `ok`, `too_long`, `unparseable`, `data_refused`, `error` (any other refusal; until 2026-11-04 also a formula or code the server answered with `422 formula` or `422 code`), `data_request` (since 2026-11-01: the text asked for data instead of holding it, such as "Beispieldaten"; the server answered `422 data_request` and the page sent the text to the chat as the user's message, where the assistant generates example data), `formula` and `code` (since 2026-11-04: the server answered `422 formula` or `422 code`; within 2,000 characters the page sent the text to the chat as the user's message, where the assistant computes the formula or runs the code, and longer code stayed in the data box with a line that asks to shorten it), `transcribed` (the text was not a table, a model read it into one and the page asks the user to confirm it; nothing is stored yet), `discarded` (the user dropped such a table; `.use()` instead parses it again and reports `ok`); `size_bucket` ∈ `lt_1kb`, `1_10kb`, `10_50kb`, `50_200kb`, `over_200kb` (the last one is refused in the browser before anything is sent) |
| `agent_data_confirmed` | `size_bucket` | useAgentSession.ts | The user ended step 1: the stored data and its bindings fit, and the server confirmed them. Since 2026-11-04 it fires inside the plot button's click (`.create_plot()`, `plot the new data`, `.update_plot()` on unconfirmed data, `.plot_all()`, and a switch's carry, which the plot button runs since 2026-11-07), which confirms first and starts the plot only on success, so it counts the clicks on unconfirmed data whose confirmation went through, not a separate step; until then `.confirm()` was a button of its own. Fires again after each new parse, binding change, data change or undo that the user confirms. `size_bucket` as for `agent_data_parsed`; data the assistant generated from a formula without a paste counts as `lt_1kb` |
| `agent_data_prepared` | `changes` | useAgentSession.ts | The assistant changed the data in a turn (its `prepare_data`, for example "read Anteil as numbers" or "sum per month") or computed it from a formula (its `generate_data`, for example "sin(x) from -pi to pi"): the turn's `done` carried a new data version, which the data panel shows with its change lines and, when an earlier version exists, `.undo()`. A generated table in a session without data is the session's first data, with nothing to undo, and fires this event too, and so does the data panel's `.to_long()` (a wide table made long, no model call). `changes` ∈ `1`, `2`, `3+`, the number of change lines (one per operation; a generated table has one, plus one per series with undefined values) |
| `agent_data_undo` | `version` | useAgentSession.ts | The user took back the assistant's last change to the data with `.undo()`, and the server restored the version before it. `version` ∈ `1` (back at the paste), `2`, `3+`: the restored version's place among its data's versions in the order they were made, the paste being 1. Since 2026-11-08 the server numbers versions once per session, across pastes, so the page counts the place from the data's first number (`version - original_version + 1`) and `1` still means back at the paste; an undone version's number is never given again, so after an undo and a new change the places count on (paste, change, undo, change, change, undo is `3+`, where the old count said `2`) |
| `agent_data_file` | `kind`, `encoding`, `outcome` | useChatAttachment.ts, DataPanel.tsx | A file reached the chat: dropped on it, chosen with `.open()` in the line above the message box (in the composer's row from 2026-11-05 to 2026-11-07) or pasted as a file, and became the message box's attachment (since 2026-11-05; the data card's box until then, since 2026-10-15). A text file is read in the browser; a spreadsheet, Parquet, Feather, Arrow or NumPy file goes to the server, which converts it in the renderer's sandbox (since the binary-file step of 2026-10-15). Enter afterwards reports `agent_data_parsed` as for a paste. `kind` ∈ `text`, `spreadsheet`, `parquet`, `arrow`, `numpy`, `hdf5`, `pickle`, `pdf`, `archive`, `binary` (by the file's first bytes in the browser; `binary` for anything else that is not text), `unknown` (refused before it was read), and for a file the server converted the format it found: `xlsx`, `xlsm`, `xlsb`, `xls`, `ods`, `parquet`, `feather`, `arrow`, `npy`, `npz`; `encoding` ∈ `utf-8`, `utf-8-bom`, `utf-16le`, `utf-16be`, `windows-1252`, `none` (a binary file); `outcome` ∈ `attached` (the file became the attachment; since 2026-11-05), `removed` (× on a file's attachment; since 2026-11-05), `filled`, `replaced` and `kept` (the data card's box and its `.replace()` and `.keep()`, until 2026-11-05), `sheet` (another sheet or `.npz` array chosen in the data card's sheet picker and read again), `refused` (a format never read, an empty file, or a file the server refused: encrypted, damaged, over a cap), `failed` (the server could not convert it now: rate limit, no render slot, renderer unavailable, network), `too_large` (over 4 MB as a text file or 5 MB as a binary one, or over 1 MB as text), `busy` (a step was running, or another file was still being read), `unreadable` (the browser could not read it). The file's name and its sheet names are never sent |
| `agent_input_routed` | `as`, `via` | useChatAttachment.ts | How the message box took a paste, a file or a typed table (since 2026-11-05), for tuning the paste routing (`routeInput.ts`): `as` ∈ `data` (the attachment, which Enter sends to the dataset route) or `message` (typed text, which Enter sends as a turn); `via` ∈ `paste` (pasted text, routed by its shape), `file` (a file, always `data`) or `typed` (since 2026-11-05: the box's own text on Enter, a table typed by hand or pasted without a paste event; always `data`, since a typed message fires nothing). Fires once per paste, file or typed table, never with its text; an empty paste fires nothing |
| `agent_plot_rendered` | `library`, `status`, `repaired`, `spec` | useAgentSession.ts | A turn's `plot` event arrived. `status` ∈ `ok`, `needs_attention`, `failed`, `not_ready`; `repaired` is `yes` when the run needed its repair round (two attempts), else `no`. Since 2026-11-08 a plot the server refuses before the run (in a turn that changed the data, or on a paste's summary turn while the data is unconfirmed) sends no `plot` event, so it fires none; a `not_ready` from the run itself still does |
| `agent_guardrail_block` | `reason` | useAgentSession.ts | A guardrail stopped a request. `reason` ∈ `out_of_scope`, `needs_data` (the request needs data the service would have to fetch), `budget` (the user's own daily token budget), `service_paused` (since 2026-11-02: the whole service spent its day budget, from a turn's refusal or the dataset route's `429`), `unsupported_content`, `rate_limited` and `daily_limit` (the user's message limits per minute and per day, and since 2026-10-14 the paste limits, which the data panel reports from the dataset route's `429`), `session_closed` (the session closed after three scope refusals), `other_library` (a request for this plot in another library or language, answered with a pointer to the catalogue), `locked_out` (the user is paused for the day after three attack verdicts; these are the stream's fixed refusals), `data_refused` (the pre-filter or the dataset judge refused the pasted data: text addressed to an AI, or the judge's verdict; personal data is never a reason), `guard_unavailable` (the scope check could not answer and failed closed), `other` (a refusal code the page does not know yet) |
| `agent_session_saved` | `include_data` | useAgentSession.ts | The admin saved the session as a JSON file with `.save()`, in the admin menu since 2026-11-06 (in the chat header's "⋯" menu from 2026-11-02, admin lane only), and the download started. `include_data` is `yes` when the `# include data.csv` box was ticked (unticked by default since 2026-11-06), so the file holds each version's data file, else `no`. A failed save fires nothing. Since 2026-11-06 an admin's use records nothing, so the event no longer reaches Plausible in production; the save's outcome beacon (below) still reaches the usage telemetry |
| `agent_result_feedback` | `reaction`, `include_data`, `subject` | useAgentSession.ts | The user sent quick feedback with the feedback form's own `.send()`, on a result version from its result card or on the chat itself from the form that `.feedback()` at the end of the chat's status line opens (below the composer until 2026-11-07), and the BFF stored it as a feedback case. `reaction` ∈ `thumbs_up`, `thumbs_down`, `bug`, `idea`, the site feedback's set; `include_data` is `yes` when the `# include data.csv` box was ticked (unticked by default; until 2026-11-06 ticked by default for an admin), so the case holds the data file, else `no`; `subject` is `result` for a version and `chat` for the chat (since 2026-10-12, for a session that made no plot). An edit that replaces a sent case fires again. A failed send fires nothing; the text never travels |
| `agent_turn_resumed` | `outcome` | useAgentSession.ts | A turn's stream was cut after its first event (it failed, as with an HTTP/3 error between the browser and the edge, or ended without `done`), and the page read the rest of the turn again (`GET /agent/session/turn`, after 1, 2, 4 and 8 seconds). `outcome` ∈ `resumed` (a read reached the turn's `done`, so the page showed how the turn ended, its plot or its own error, instead of the cut's error), `gone` (the server holds another turn, or the session ended) or `failed` (every read failed, or the read found the turn cancelled because the agents service saw its stream end; the page showed the error). The event measures the connection, not the turn: a turn that ended in its own error after a resumed read still counts as `resumed`. Once per cut; a stop or a closed page fires nothing. The origin's logs cannot see such a cut, so this is how often the edge loses a stream |

`copy_code` on a result card carries `method: agent` and `page: agent_chat`
plus the `spec` and `library` of the version.

These Plausible events count page interactions in the browser. Since 2026-10-16
the chat also has a server-side usage telemetry in BigQuery, with its own
content-free events (`data_input`, `chat_turn`, `pipeline_run`, `outcome`): the
copy, download, save and feedback actions above additionally send an outcome
beacon (`POST /debug/agent/sessions/{sid}/outcome`) that the agents service writes
as an `outcome` line. That beacon is not a Plausible event and fires on every host,
not only `anyplot.ai`. See [Agent usage telemetry](agent-telemetry.md).

### Discovery

| Event Name | Properties | Where | Description |
|------------|-----------|-------|-------------|
| `search` | `query`, `category` | FilterBar/FilterSearch.tsx | User searches and selects value |
| `search_no_results` | `query` | FilterBar/FilterSearch.tsx | Search query of at least 2 characters returns no results inside the active filters (debounced 200ms). `query` is the text as typed, before the search drops generic words. Such a query also fires it when the dropdown offers `.search_all()`, because the same query finds matches without the filters. |

### Feature usage

| Event Name | Properties | Where | Description |
|------------|-----------|-------|-------------|
| `random_filter` | `category`, `value`, `method` | useFilterState.ts | User triggers random filter |
| `filter_remove` | `category`, `value` | useFilterState.ts | User removes a filter. `.search_all()` in the filter search sends one per filter it removes. |
| `grid_resize` | `size` | ToolbarActions.tsx | User toggles between normal/compact view |
| `plots_scrolled` | `share`, `results`, `filtered` | usePlotsScrolled.ts (PlotsPage.tsx) | How far a visitor got through the gallery, once per visit to `/plots` (since 2026-11-11). Sent when the visit ends: the visitor leaves the page, or the tab goes away. A visit without scrolling sends none, and the offset the page restores from an earlier visit doesn't count, only a point below it. `share` is the deepest point as a share of the result list, in percent bands: `0-10`, `10-25`, `25-50`, `50-75`, `75-100`. It is the percentage the filter bar shows, which scales the loaded part up to the whole list. `results` is the size of that list: `1-24`, `25-99`, `100-999`, `1000+`. `filtered` is `true` or `false`. When the filters change during a visit, all three describe the list the deepest point was reached in, and the event is recorded under that list's page (`/plots/lib/matplotlib`). |
| `tab_toggle` | `action`, `tab`, `library` | SpecTabs.tsx | User opens or closes a tab |
| `plot_rotate` | `spec` | SpecsListPage.tsx | User clicks image on specs page to rotate library |
| `open_interactive` | `spec`, `library` | SpecOverview.tsx, SpecDetailView.tsx | User opens interactive HTML view |
| `suggest_spec` | - | SpecsListPage.tsx | User clicks the `spec.suggest()` link on the specs list page. The mirror link on the landing page emits `nav_click` with `source: suggest_spec_link` instead. |
| `report_issue` | `spec`, `library`? | SpecPage.tsx | User clicks the "report issue ↗" link on a spec hub page. The in-plot `.report()` flag was replaced by the 👍/👎 vote buttons, so `library` is now only set when the hub page has a library selected. |
| `tag_click` | `param`, `value`, `source` | SpecTabs.tsx, StatsPage.tsx | User clicks a tag chip to filter (`source` ∈ `spec_detail`, `stats`) |
| `theme_toggle` | `to` | MastheadRule.tsx | User cycles tri-state theme mode (`to` ∈ `system`, `light`, `dark`). The cycle order is `system → light → dark → system`. |
| `view_mode_change` | `mode`, `library` | SpecDetailView.tsx | User toggles preview ↔ interactive view inside a spec detail. `mode` ∈ `preview`, `interactive`. Fires on every toggle in either direction (cf. `open_interactive`, which only fires when the interactive HTML is opened in a new tab). |
| `library_click` | `source`, `library` | LibrariesPage.tsx | User clicks a library card on `/libraries` to navigate to its filtered plots view. `source` is `libraries_page` from this entry point. |
| `library_filter` | `source`, `framework` | LibrariesPage.tsx | User clicks a language/framework filter chip on `/libraries` (`framework` carries the chip id; register the prop in the dashboard for breakdowns) |
| `stats_top_impl_click` | `spec`, `library` | StatsPage.tsx | User clicks a "top implementation" thumbnail on `/stats` to jump into its spec detail. |
| `map_node_click` | `spec` | MapPage.tsx | User clicks a node on `/map` (or, on touch, second tap on an already-pinned node) to navigate to its spec detail. |
| `map_node_pin` | `spec` | MapPage.tsx | Touch device only: first tap on a node opens the preview panel + pin marker without navigating. A second tap on the same node fires `map_node_click` and navigates. |
| `map_search_select` | `spec` | MapPage.tsx | User picks a result from the `/map` search dropdown (`⌘K` / `Ctrl+K` opens it). The camera flies to the node and the preview panel opens. |
| `feedback_opened` | `path` | FeedbackWidget.tsx | User clicks the floating feedback FAB and the quick mini-stack of 👍 / 👎 / 💬 appears (issue #5662). `path` is `window.location.pathname + search` at open time. |
| `feedback_submitted` | `path`, `reaction`?, `has_contact`, `spec_id`?, `library`?, `mode` | FeedbackWidget.tsx, SpecDetailView.tsx (via useQuickReaction.ts) | User submits a feedback entry. `reaction` ∈ `thumbs_up`, `thumbs_down`, `bug`, `idea` (omitted if none selected). `mode` is `"quick"` for a one-tap 👍/👎 from the mini-stack, `"full"` for a submit from the detailed dialog, and `"plot_overlay"` for a 👍 (top-left) / 👎 (bottom-left) tap directly on the plot in a spec detail view — that one also carries `library`, because the vote is about one implementation and the server stores `library_id` + `language` with it. `has_contact` is `"true"`/`"false"` — the contact field is now a free-form name/email/handle, not strictly an email. `spec_id` is set when the current route resolves to a spec page. |

### Diagnostics

| Event | Properties | Source | Description |
|-------|-----------|--------|-------------|
| `page_not_found` | `path`, `source` | NotFoundPage.tsx, SpecPage.tsx | A visitor reached a URL the app cannot serve. `path` is `window.location.pathname`. `source` says which kind of miss it was: `catch_all` (the URL matches no route at all), `spec_missing` (the spec itself does not exist), `impl_missing` (the spec exists but not that library/language pair), `route_error` (the router returned a 404 response). Until 2026-11-11 the list had a fifth value, `language_params`, for a `/{spec}/{language}` URL without both segments; the route can't match such a URL, so the value never fired. |

Read `source` before `path`. A `catch_all` miss is usually a bad inbound link;
`impl_missing` is content that used to exist and no longer does, which is the
pattern a library migration leaves behind and the one worth alerting on.

One asymmetry to know about: `impl_missing` fires without a 404 page ever being
shown. `SpecPage.tsx` redirects those visitors to the spec hub with a language
filter, to preserve their intent — so the event is reported from there rather
than from `NotFoundPage.tsx`. Every other source accompanies a rendered 404.

Since 2026-11-11 the address of a miss also records a pageview, under the path
that was asked for (see [When a pageview is sent](#when-a-pageview-is-sent)).
An `impl_missing` visit therefore records two: the implementation page that is
gone, then the hub it was sent to.

The bot-facing side of the same URLs answers HTTP 404 from `api/routers/seo.py`,
but crawlers never run JavaScript and `app/nginx.conf` short-circuits bot user
agents with `return 202` on `/api/event` (see
[The analytics shield](#the-analytics-shield)), so nothing they do appears
here — this event covers humans only.

### Navigation clicks (`nav_click`)

A single event captures every clickable surface on the chrome, the editorial
landing page and the gallery so we can answer "where do users go, from which
page, and via which UI element". One event, one event-property pair: `source` (which UI
element was clicked) + `target` (where it leads). Some sources additionally
carry `spec`, `library`, or `value` for richer breakdowns.

| `source` value | Where | Target |
|----------------|-------|--------|
| `nav_specs` / `nav_plots` / `nav_map` / `nav_libraries` / `nav_stats` / `nav_palette` / `nav_mcp` | NavBar.tsx | top-level menu bar |
| `nav_logo` | NavBar.tsx | logo → `/` |
| `nav_search` | NavBar.tsx | `plots.search()` button → `/plots?focus=search` |
| `masthead_logo` / `masthead_branch` / `masthead_release` | MastheadRule.tsx | masthead `~/anyplot.ai · main · v1.x.x` |
| `breadcrumb` | MastheadRule.tsx | breadcrumb segments on non-landing routes |
| `hero_cta_browse` / `hero_mcp` / `hero_github` | HeroSection.tsx | hero call-to-action + secondary links |
| `hero_use_my_data` | HeroSection.tsx | `# new: pick any plot, then .use_my_data() →` under the hero CTAs, shown only while the agent chat's public lane is open → `/plots` |
| `potd_terminal_image` / `potd_terminal_filename` / `potd_terminal_github` | PlotOfTheDayTerminal.tsx | hero terminal-framed POTD |
| `featured_thumb` | LandingPage.tsx | featured plot grid |
| `library_card` | LandingPage.tsx | library cards (carries `value=<library_id>`) |
| `section_header` | SectionHeader.tsx | `specs.all()` / `libraries.all()` / `palette.explore()` headers |
| `specs_more_link` | LandingPage.tsx | `+ N more in the catalogue →` |
| `suggest_spec_link` | LandingPage.tsx | `spec.suggest()` GitHub-issue link |
| `gallery_spec_hub` | PlotsPage.tsx | `{spec_id}.compare() →` above the grid when `/plots` is filtered to exactly one spec (carries `spec`) → `/{spec_id}` |

**Random methods**:
- `click`: Shuffle icon clicked
- `space`: Spacebar pressed
- `doubletap`: Mobile double-tap gesture

**Grid sizes**:
- `normal`: Larger cards (1-3 columns)
- `compact`: Smaller cards (2-6 columns)

**Tab toggle actions**:
- `open`: User opened a tab
- `close`: User closed a tab

**Tab names**: `code`, `specification`, `implementation`, `quality`

### External and internal link events

| Event Name | Properties | Where | Description |
|------------|-----------|-------|-------------|
| `external_link` | `destination`, `spec`?, `library`? | Footer.tsx, LegalPage.tsx, AboutPage.tsx, LibrariesPage.tsx, SectionHeader.tsx | User clicks external link |
| `internal_link` | `destination`, `spec`?, `library`? | Footer.tsx, AboutPage.tsx | User clicks internal link |

**External destinations (Footer)**: `github`, `github_issue_chooser`, `linkedin`
**External destinations (LegalPage)**: `linkedin`, `x`, `github_personal`, `kurrentschrift`, `cite_citadel`
**Internal destinations (Footer)**: `about`, `legal`

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
Server-side events are a separate path, see
[Two things Plausible will silently drop](#two-things-plausible-will-silently-drop).

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

### og:image is split by who fetched it

A social or messenger preview means a person shared a link, a product signal
that belongs with the human numbers, so `og_image_view` on `anyplot.ai`
records it. A search or AI crawler fetching the same image is not a share, and
since `robots.txt` began permitting `/og/` those arrive in volume: on the main
site they would drown the sharing signal and inflate visitor counts. So
`track_og_image` returns early when `detect_ai_agent` recognises the user
agent. A crawler's image fetch sends nothing to Plausible, and the API writes
its machine-read line instead, with `surface` `og`. Anything `detect_ai_agent`
doesn't recognise (Twitter, Facebook, Slack, WhatsApp, …) is a share and stays
on `anyplot.ai`.

Plausible discards an event and still answers `202 ok` in two cases, both
found by probe events against the live API:

- **A bot user agent.** The same event sent as `Claude-User` never appeared,
  sent as a browser user agent it did. Whether that also costs some preview
  events (a preview fetcher sends its own crawler-like user agent) has not
  been measured.
- **Our own IP instead of the visitor's.** The
  [Events API docs](https://plausible.io/docs/events-api) state that Plausible
  uses "the first valid IP address from the list" and that if you "forward a
  server, hosting provider, or CDN IP address instead of the actual visitor
  IP, Plausible's bot filtering will drop the event". The event therefore
  carries `visitor_ip`, **not** the rate limiter's `client_ip`, which returns
  the rightmost forwarded entry, our own infrastructure. `visitor_ip` takes
  `cf-connecting-ip` first, which Cloudflare overwrites, then the leftmost
  public forwarded entry, so a forged private address at the front of the list
  is skipped. `api/request_context.py` documents why the two must stay
  separate.

## Server-side og:image tracking

Social media bots (Twitter, WhatsApp, Teams, etc.) don't execute JavaScript, so og:image requests can only be tracked server-side.

### Architecture

All og:images are routed through the API for tracking:

```
Bot requests page → nginx detects bot → SEO proxy serves HTML with og:image URL
                                                            ↓
                                          https://api.anyplot.ai/og/{endpoint}.png
                                                            ↓
                                          track_og_image() → Plausible Events API
                                                            ↓
                                          Return image (fire-and-forget tracking)
```

**Implementation**: `api/analytics.py` (server-side Plausible tracking)

### og:image event

| Event Name | Properties | Description |
|------------|------------|-------------|
| `og_image_view` | `page`, `platform`, `spec`?, `language`?, `library`?, `filter_*`? | Bot requested og:image |

### Properties

| Property | Values | Description |
|----------|--------|-------------|
| `page` | `home`, `plots`, `spec_overview`, `spec_detail` | Page type |
| `platform` | See list below | Detected platform from User-Agent |
| `spec` | Specification ID | Only for spec pages |
| `language` | Language slug (e.g. `python`) | Only for spec detail pages |
| `library` | Library ID | Only for spec detail pages |
| `filter_*` | Filter value | Dynamic props for filtered URLs (e.g., `filter_lib`, `filter_dom`) |

### Platform detection (27 platforms)

**Social Media**: twitter, facebook, linkedin, pinterest, reddit, tumblr, mastodon

**Messaging Apps**: slack, discord, telegram, whatsapp, signal, viber, skype, teams, snapchat

**Search Engines**: google, bing, yandex, duckduckgo, baidu, apple. `detect_ai_agent` recognises all six, so their fetches are machine reads and never reach Plausible; the values stay in `detect_platform` for completeness.

**Link Preview Services**: embedly, quora, outbrain, rogerbot, showyoubot

**Fallback**: unknown

#### WhatsApp variant detection

Some apps (Signal, others) use a WhatsApp User-Agent to bypass rate limits ([Issue #10060](https://github.com/signalapp/Signal-Android/issues/10060)). We distinguish real WhatsApp from spoofed requests by version format:

| Platform | User-Agent Example | Detection |
|----------|-------------------|-----------|
| `whatsapp` | `WhatsApp/2.23.18.78 i` | 3+ part version = verified WhatsApp |
| `whatsapp-lite` | `WhatsApp` or `WhatsApp/2` | Simplified UA = Signal or other spoofers |

### API endpoints

| Endpoint | Description | Tracking |
|----------|-------------|----------|
| `/og/home.png` | Static og:image for home page | `page=home`, `filter_*` from query params |
| `/og/plots.png` | Static og:image for plots page | `page=plots` |
| `/og/{spec_id}.png` | Collage og:image for spec overview | `page=spec_overview`, `spec` |
| `/og/{spec_id}/{language}/{library}.png` | Branded og:image for implementation | `page=spec_detail`, `spec`, `language`, `library` |

### Filter tracking for shared URLs

When users share filtered URLs (e.g., `https://anyplot.ai/?lib=plotly&dom=statistics`), the filters are passed to the og:image endpoint:

```
og:image URL: https://api.anyplot.ai/og/home.png?lib=plotly,matplotlib&dom=statistics
                                                  ↓
Tracked props: { page: "home", platform: "twitter", filter_lib: "plotly,matplotlib", filter_dom: "statistics" }
```

**Note**: Each filter category becomes a separate prop (`filter_lib`, `filter_dom`, etc.) to handle comma-separated values.

---

## Plausible dashboard configuration

### Required custom properties

To see event properties in Plausible dashboard, you **MUST** register them as custom properties.

**Go to**: Plausible Dashboard → Site Settings → Custom Properties → Add Property

#### Properties to register

| Property | Description | Used By Events |
|----------|-------------|----------------|
| `spec` | Plot specification ID | `copy_code`, `download_image`, `plot_rotate`, `external_link`, `internal_link`, `open_interactive`, `report_issue`, `tag_click`, `og_image_view`, `agent_open`, `agent_plot_rendered` |
| `language` | Language slug (`python`, `r`, `julia`, `javascript`) | `og_image_view` |
| `library` | Library name (matplotlib, seaborn, etc.) | `copy_code`, `download_image`, `external_link`, `internal_link`, `open_interactive`, `tab_toggle`, `og_image_view`, `feedback_submitted` (plot-overlay votes only), `agent_open`, `agent_plot_rendered` |
| `method` | Action method (card, image, tab, agent, click, space, doubletap) | `copy_code`, `random_filter` |
| `page` | Page context (home, plots, spec_overview, spec_detail, agent_chat) | `copy_code`, `download_image`, `og_image_view` |
| `status` | Outcome of an agent chat step (`ok`, `needs_attention`, `failed`, `not_ready`; for a parse also `too_long`, `unparseable`, `data_refused`, `error`, `data_request`, `formula`, `code`, `transcribed`, `discarded`) | `agent_data_parsed`, `agent_plot_rendered` |
| `size_bucket` | Size class of pasted data (`lt_1kb`, `1_10kb`, `10_50kb`, `50_200kb`, `200kb_1mb`, `over_1mb`; `over_200kb` until the paste cap rose to 1 MB on 2026-10-14), never the size | `agent_data_parsed`, `agent_data_confirmed` |
| `changes` | How many change lines an assistant's data change or generated table carried (`1`, `2`, `3+`) | `agent_data_prepared` |
| `version` | The data version an undo restored, by its place in its data (`1` is the paste, `2`, `3+`), never the session's number for it | `agent_data_undo` |
| `kind` | What a file brought into the agent chat was, by its first bytes (`text`, `spreadsheet`, `parquet`, `arrow`, `numpy`, `hdf5`, `pickle`, `pdf`, `archive`, `binary`, `unknown`), or the format the server found when it converted the file (`xlsx`, `xlsm`, `xlsb`, `xls`, `ods`, `parquet`, `feather`, `arrow`, `npy`, `npz`) | `agent_data_file` |
| `encoding` | The text encoding the browser read a dropped file with (`utf-8`, `utf-8-bom`, `utf-16le`, `utf-16be`, `windows-1252`, `none`) | `agent_data_file` |
| `outcome` | What happened to a dropped file (`attached`, `removed`, `sheet`, `refused`, `failed`, `too_large`, `busy`, `unreadable`; `filled`, `replaced` and `kept` until 2026-11-05), or to a cut turn the page read again (`resumed`, `gone`, `failed`) | `agent_data_file`, `agent_turn_resumed` |
| `as` | How the agent chat's message box took a paste, a file or a typed table (`data`: an attachment for the dataset route; `message`: typed text) | `agent_input_routed` |
| `via` | Where that input came from (`paste`, `file`, `typed`) | `agent_input_routed` |
| `repaired` | Whether an agent run needed its repair round (`yes` / `no`) | `agent_plot_rendered` |
| `reason` | Why a guardrail stopped an agent chat request (`out_of_scope`, `needs_data`, `budget`, `service_paused`, `unsupported_content`, `rate_limited`, `daily_limit`, `session_closed`, `other_library`, `locked_out`, `data_refused`, `guard_unavailable`, `other`) | `agent_guardrail_block` |
| `include_data` | Whether a saved agent chat session, or a feedback case, carries the data file (`yes` / `no`) | `agent_session_saved`, `agent_result_feedback` |
| `reaction` | The reaction of a feedback entry or of an agent result's quick feedback (`thumbs_up`, `thumbs_down`, `bug`, `idea`) | `feedback_submitted`, `agent_result_feedback` |
| `platform` | Bot/platform name (twitter, whatsapp, teams, etc.) | `og_image_view` |
| `category` | Filter category (lib, spec, plot, data, dom, feat, dep, tech, pat, prep, style) | `search`, `random_filter`, `filter_remove` |
| `value` | Filter value | `random_filter`, `filter_remove`, `tag_click` |
| `query` | Search query text | `search`, `search_no_results` |
| `destination` | Link-target slug — external: `github`, `github_issue_chooser`, `github_personal`, `github_bug`, `github_discussions`, `github_plot_request`, `github_releases`, `linkedin`, `x`, `kurrentschrift`, `cite_citadel`, `library_docs`; internal: `about`, `legal`, `legal_transparency`, `palette`, `stats`, `plots`, `mcp`. `SectionHeader` external links emit the target **hostname** instead (e.g. `plausible.io`). Grep `destination:` in `app/src` for the authoritative list. | `external_link`, `internal_link` |
| `tab` | Tab name (code, specification, implementation, quality) | `tab_toggle` |
| `action` | Toggle action (open, close) | `tab_toggle` |
| `size` | Grid size (normal, compact) | `grid_resize` |
| `param` | URL parameter name for tag | `tag_click` |
| `source` | Source UI element / page context | `tag_click`, `nav_click`, `agent_open` (`plot_page` / `spec_hub` / `landing` / `plot_of_the_day` / `direct`) |
| `framework` | Library id clicked in the libraries-page filter (needs dashboard registration to appear in breakdowns) | `library_filter` |
| `target` | Click destination (route or external label) | `nav_click` |
| `subject` | What an agent chat quick feedback is about (`result`: a result version, `chat`: the chat itself) | `agent_result_feedback` |
| `to` | New mode after toggle (`system` / `light` / `dark`) | `theme_toggle` |
| `mode` | Spec detail view mode (`preview` / `interactive`) | `view_mode_change` |
| `theme` | Ambient *effective* theme attached to **every** pageview & event (`dark` / `light`) — resolved from the tri-state mode so OS-followers still split cleanly | all events (set in RootLayout via `setAnalyticsAmbientProps`) |
| `share` | Deepest point of a gallery visit as a share of the result list, in percent bands (`0-10`, `10-25`, `25-50`, `50-75`, `75-100`) | `plots_scrolled` |
| `results` | Size of the gallery's result list at that point (`1-24`, `25-99`, `100-999`, `1000+`) | `plots_scrolled` |
| `filtered` | Whether that list was filtered (`true` / `false`) | `plots_scrolled` |
| `filter_lib` | Library filter value (for og:image) | `og_image_view` |
| `filter_spec` | Specification filter value (for og:image) | `og_image_view` |
| `filter_plot` | Plot type filter value (for og:image) | `og_image_view` |
| `filter_data` | Data type filter value (for og:image) | `og_image_view` |
| `filter_dom` | Domain filter value (for og:image) | `og_image_view` |
| `filter_feat` | Features filter value (for og:image) | `og_image_view` |
| `filter_dep` | Dependencies filter value (for og:image) | `og_image_view` |
| `filter_tech` | Techniques filter value (for og:image) | `og_image_view` |
| `filter_pat` | Patterns filter value (for og:image) | `og_image_view` |
| `filter_prep` | Dataprep filter value (for og:image) | `og_image_view` |
| `filter_style` | Styling filter value (for og:image) | `og_image_view` |

### Goals configuration

**Go to**: Plausible Dashboard → Site Settings → Goals → Add Goal

#### Recommended goals

| Goal Name | Type | Description |
|-----------|------|-------------|
| `copy_code` | Custom Event | Track code copies (primary conversion) |
| `download_image` | Custom Event | Track image downloads |
| `search` | Custom Event | Track successful searches |
| `search_no_results` | Custom Event | Track failed searches (content gaps) |
| `random_filter` | Custom Event | Track random filter usage |
| `filter_remove` | Custom Event | Track filter removal |
| `grid_resize` | Custom Event | Track view preference |
| `plots_scrolled` | Custom Event | Track how far visitors get through the gallery, by share of the result list |
| Scroll 90% on / | Pageview (scroll depth) | Track visitors who saw the whole landing page. The only scroll goal: the 25 %, 50 %, and 75 % goals go once this timing is live |
| `tab_toggle` | Custom Event | Track tab interactions |
| `external_link` | Custom Event | Track outbound clicks |
| `internal_link` | Custom Event | Track internal navigation links |
| `open_interactive` | Custom Event | Track interactive mode usage |
| `suggest_spec` | Custom Event | Track spec suggestion clicks |
| `report_issue` | Custom Event | Track issue report clicks |
| `tag_click` | Custom Event | Track tag filter clicks |
| `plot_rotate` | Custom Event | Track plot image rotation on specs page |
| `nav_click` | Custom Event | Track which UI element on the chrome, the landing page or the gallery leads users where |
| `theme_toggle` | Custom Event | Track dark/light theme switches |
| `view_mode_change` | Custom Event | Track preview ↔ interactive toggles in spec detail |
| `library_click` | Custom Event | Track library-card clicks on the libraries page |
| `library_filter` | Custom Event | Track language/framework filter-chip clicks on the libraries page |
| `stats_top_impl_click` | Custom Event | Track clicks on top-quality implementation thumbnails on /stats |
| `map_node_click` | Custom Event | Track navigation clicks from `/map` into a spec detail |
| `map_node_pin` | Custom Event | Track touch users opening the preview panel on `/map` (first tap) |
| `map_search_select` | Custom Event | Track use of the `/map` search-and-fly-to feature |
| `og_image_view` | Custom Event | Track og:image requests from social media bots |
| `agent_open` | Custom Event | Track opens of the agent chat (admin and public) and where they came from |
| `agent_data_parsed` | Custom Event | Track parse outcomes of pasted data in the agent chat |
| `agent_data_confirmed` | Custom Event | Track how often users confirm their data before the agent chat plots it |
| `agent_data_prepared` | Custom Event | Track how often the agent chat's assistant changes the data in step 1 or computes it from a formula |
| `agent_data_undo` | Custom Event | Track how often users take back the assistant's change to their data |
| `agent_data_file` | Custom Event | Track which files users bring into the agent chat, and how often the browser refuses one |
| `agent_input_routed` | Custom Event | Track how the agent chat's message box routes a paste, a file or a typed table: as data or as a message |
| `agent_plot_rendered` | Custom Event | Track agent chat plot outcomes and repair rounds |
| `agent_guardrail_block` | Custom Event | Track agent chat refusals and failed-closed guard checks |
| `agent_session_saved` | Custom Event | Track how often admins save an agent chat session as a file, and with the data or without |
| `agent_result_feedback` | Custom Event | Track quick feedback on agent chat results by reaction, and how often the case holds the data |
| `agent_turn_resumed` | Custom Event | Track how often the agent chat's stream is cut mid-turn, and how often the page reads the result anyway |

### Funnels (optional)

**Example funnel**: Home → Spec → Copy

1. Pageview `/` (home)
2. Pageview `/{spec_id}/{language}/{library}` (spec detail)
3. `copy_code` event

### Dashboard widgets

Recommended custom widgets:

1. **Top Specs Copied**: `copy_code` breakdown by `spec`
2. **Popular Libraries**: `copy_code` breakdown by `library`
3. **Copy Journey**: `copy_code` breakdown by `page`
4. **Search Terms**: `search` breakdown by `query`
5. **Missing Content**: `search_no_results` breakdown by `query`
6. **View Preference**: `grid_resize` breakdown by `size`

---

## User journey tracking

### Understanding the `page` property

The `page` property tracks **where** users perform actions to understand their journey:

```
User lands on anyplot.ai
    │
    ├─→ Home (grid view)
    │   └─→ copy_code { page: 'home' }
    │
    ├─→ Cross-Language Hub (/{spec_id})
    │   └─→ copy_code { page: 'spec_hub' }
    │
    ├─→ Language Overview (/{spec_id}/{language})
    │   └─→ copy_code { page: 'spec_overview' }
    │   └─→ download_image { page: 'spec_overview' }
    │
    └─→ Implementation Detail (/{spec_id}/{language}/{library})
        └─→ copy_code { page: 'spec_detail' }
        └─→ download_image { page: 'spec_detail' }
        └─→ open_interactive { spec, language, library }
```

### Journey examples in Plausible

**Q: Do users copy from search results or spec pages?**
- Filter `copy_code` by `page` property
- `home` = direct from search/browse
- `spec_overview` = after viewing all implementations
- `spec_detail` = after deep-diving into one library

**Q: Which library implementations are most downloaded?**
- Filter `download_image` by `library` property
- Filter by `page` to see if users download from overview or detail

---

## Complete event reference

### Events summary table

| Event | Properties | Code Location |
|-------|------------|---------------|
| `copy_code` | `spec`, `library`, `method`, `page` | ImageCard.tsx, SpecPage.tsx, SpecTabs.tsx, agent-chat/ResultCard.tsx |
| `download_image` | `spec`, `library`, `page` | SpecPage.tsx |
| `agent_open` | `library`, `source`, `spec` | AgentChatPage.tsx |
| `agent_data_parsed` | `status`, `size_bucket` | useAgentSession.ts |
| `agent_data_confirmed` | `size_bucket` | useAgentSession.ts |
| `agent_data_prepared` | `changes` | useAgentSession.ts |
| `agent_data_undo` | `version` | useAgentSession.ts |
| `agent_data_file` | `kind`, `encoding`, `outcome` | useChatAttachment.ts, DataPanel.tsx |
| `agent_input_routed` | `as`, `via` | useChatAttachment.ts |
| `agent_plot_rendered` | `library`, `status`, `repaired`, `spec` | useAgentSession.ts |
| `agent_guardrail_block` | `reason` | useAgentSession.ts |
| `agent_session_saved` | `include_data` | useAgentSession.ts |
| `agent_result_feedback` | `reaction`, `include_data`, `subject` | useAgentSession.ts |
| `agent_turn_resumed` | `outcome` | useAgentSession.ts |
| `search` | `query`, `category` | FilterBar/FilterSearch.tsx |
| `search_no_results` | `query` | FilterBar/FilterSearch.tsx |
| `random_filter` | `category`, `value`, `method` | useFilterState.ts |
| `filter_remove` | `category`, `value` | useFilterState.ts |
| `grid_resize` | `size` | ToolbarActions.tsx |
| `plots_scrolled` | `share`, `results`, `filtered` | usePlotsScrolled.ts |
| `tab_toggle` | `action`, `tab`, `library` | SpecTabs.tsx |
| `tag_click` | `param`, `value`, `source` | SpecTabs.tsx, StatsPage.tsx |
| `plot_rotate` | `spec` | SpecsListPage.tsx |
| `open_interactive` | `spec`, `library` | SpecOverview.tsx, SpecDetailView.tsx |
| `suggest_spec` | - | SpecsListPage.tsx (LandingPage mirror attributed via `nav_click` with `source: suggest_spec_link`) |
| `report_issue` | `spec`, `library`? | SpecPage.tsx |
| `external_link` | `destination`, `spec`?, `library`? | Footer.tsx, LegalPage.tsx, AboutPage.tsx, LibrariesPage.tsx, SectionHeader.tsx |
| `internal_link` | `destination`, `spec`?, `library`? | Footer.tsx, AboutPage.tsx |
| `nav_click` | `source`, `target`, `spec`?, `library`?, `value`? | NavBar, MastheadRule, HeroSection, SectionHeader, PlotOfTheDayTerminal, LandingPage, PlotsPage |
| `theme_toggle` | `to` | MastheadRule.tsx |
| `view_mode_change` | `mode`, `library` | SpecDetailView.tsx |
| `library_click` | `source`, `library` | LibrariesPage.tsx |
| `library_filter` | `source`, `framework` | LibrariesPage.tsx |
| `stats_top_impl_click` | `spec`, `library` | StatsPage.tsx |
| `map_node_click` | `spec` | MapPage.tsx |
| `map_node_pin` | `spec` | MapPage.tsx |
| `map_search_select` | `spec` | MapPage.tsx |
| `feedback_opened` | `path` | FeedbackWidget.tsx |
| `feedback_submitted` | `path`, `reaction`?, `has_contact`, `spec_id`?, `library`?, `mode` | FeedbackWidget.tsx, SpecDetailView.tsx |
| `page_not_found` | `path`, `source` | NotFoundPage.tsx, SpecPage.tsx |
| `og_image_view` | `page`, `platform`, `spec`?, `language`?, `library`?, `filter_*`? | api/analytics.py (server-side) |

**Total: 39 client-side + 1 server-side = 40 events** (the twelve `agent_*`
events exist only in builds with `VITE_ENABLE_AGENT_CHAT=true`)

> Removed events: `potd_dismiss` (and the `nav_click` sources `potd_image` /
> `potd_title` / `potd_source_link`) died with the dismissible
> `PlotOfTheDay.tsx` banner — the POTD now lives in `PlotOfTheDayTerminal.tsx`
> and only emits the `potd_terminal_*` `nav_click` sources. Historical
> `potd_dismiss` data remains visible in Plausible; the goal can be deleted
> from the dashboard.
>
> `LCP`, `CLS`, `INP`, `FCP`, and `TTFB`, with their `value` and `rating`
> properties, stopped on 2026-11-08 together with `reportWebVitals.ts` and the
> `web-vitals` dependency (see
> [Core Web Vitals are not tracked](#core-web-vitals-are-not-tracked)). So did
> the script's automatic `Form: Submission` goal. Their history stays visible
> in Plausible; the `LCP`, `CLS`, and `INP` goals can be deleted from the
> dashboard.

> Every pageview and event additionally carries a `theme` ambient prop (`dark` /
> `light`). Set in `RootLayout` via `setAnalyticsAmbientProps` whenever the user
> toggles the theme — register `theme` as a custom property to see the
> dark-vs-light split per URL.

---

## Property values reference

### `spec` values
Any valid specification ID (e.g., `scatter-basic`, `heatmap-correlation`, `bar-grouped`)

### `library` values
```
matplotlib | seaborn | plotly | bokeh | altair | plotnine | pygal | letsplot
ggplot2 | makie | chartjs | d3 | echarts | highcharts | muix
```
(Canonical source: `LIBRARIES_METADATA` in `core/constants.py`.)

### `method` values
```
card      # ImageCard copy button (home grid)
image     # SpecPage image copy button
tab       # SpecTabs code tab copy button
agent     # Agent chat result card copy button
click     # Random icon clicked
space     # Spacebar pressed
doubletap # Mobile double-tap
```

### `page` values
```
home          # HomePage grid view (client) or og:image home endpoint (server)
plots         # PlotsPage (server og:image only)
spec_overview # SpecPage showing all libraries
spec_detail   # SpecPage showing single library
agent_chat    # Agent chat result card (copy_code only)
```

### `platform` values (server-side og:image tracking only)
```
# Social Media
twitter | facebook | linkedin | pinterest | reddit | tumblr | mastodon

# Messaging Apps
# NB: Signal spoofs the WhatsApp UA (see line 260 above), so the analytics
# pipeline never emits `signal` as a platform value — Signal traffic surfaces
# as `whatsapp-lite`.
slack | discord | telegram | whatsapp | whatsapp-lite | viber | skype | teams | snapchat

# Search Engines
google | bing | yandex | duckduckgo | baidu | apple

# Link Preview Services
embedly | quora | outbrain | rogerbot | showyoubot

# Fallback
unknown
```

### `category` values
```
# Spec-level (WHAT is visualized)
lib   # library filter
spec  # specification filter
plot  # plot_type filter
data  # data_type filter
dom   # domain filter
feat  # features filter

# Impl-level (HOW it is implemented)
dep   # dependencies filter
tech  # techniques filter
pat   # patterns filter
prep  # dataprep filter
style # styling filter
```

### `tab` values
```
code           # Python code tab
specification  # Spec details tab
implementation # AI implementation review tab
quality        # Quality score breakdown tab
```

### `destination` values
```
github          # GitHub repository link (Footer)
stats           # Plausible stats dashboard link (Footer)
linkedin        # LinkedIn profile link (Footer, LegalPage)
x               # X/Twitter profile link (LegalPage)
github_personal # Personal GitHub link (LegalPage)
mcp             # MCP documentation page (internal link, Footer)
legal           # Legal page (internal link, Footer)
```

### `size` values
```
normal   # Larger cards (1-3 columns)
compact  # Smaller cards (2-6 columns)
```

---

## Reading stats — backend → Plausible Stats API

In addition to *sending* events, the backend reads aggregate visitor data
from Plausible to render the unique-visitors chart at the top of the
public stats page.

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
- **Analytics hook**: `app/src/hooks/useAnalytics.ts`
- **Admin mute**: `app/src/analytics/mute.ts`
- **Pageview sending**: the layout effect in `app/src/layouts/RootLayout.tsx` (every navigation) and `app/src/hooks/useUrlSync.ts` (a filter change on `/plots`)
- **Pageview building**: `buildPlausibleUrl()` in useAnalytics.ts
- **Redirects that record nothing**: `app/src/routes/redirects.ts`
- **Gallery scroll event**: `app/src/hooks/usePlotsScrolled.ts`, with the percentage from `app/src/utils/galleryScroll.ts`
- **Event tracking**: Passed via `onTrackEvent` prop throughout component tree
- **Agent chat events**: `app/src/hooks/useAgentSession.ts` (parse, plot, guardrail), `app/src/pages/AgentChatPage.tsx` (open, admin mute), `app/src/sections/agent-chat/ResultCard.tsx` (`copy_code`)
- **Stats API consumer**: `_fetch_plausible_visitors()` in `api/routers/insights.py`
- **og:image events**: `track_og_image()` in `api/analytics.py`; a crawler's fetch is a machine read instead (`api/machine_reads.py`, [Machine readers](machine-readers.md))

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

---

## Implementation checklist

- [x] Plausible script loaded
- [x] Manual pageview tracking, sent by the layout at the navigation (2026-11-11)
- [x] Filter-based URL generation
- [x] Gallery scroll event (`plots_scrolled` with `share`, `results`, `filtered`)
- [x] Code copy events with journey tracking (`copy_code` + `page`)
- [x] Download tracking (`download_image` + `page`)
- [x] Search events (`search`, `search_no_results`)
- [x] Random filter events (`random_filter`)
- [x] Filter removal tracking (`filter_remove`)
- [x] Grid size toggle tracking (`grid_resize`)
- [x] Tab interaction events (`tab_toggle`)
- [x] Tag click events (`tag_click`)
- [x] External link events (`external_link`)
- [x] Internal link events (`internal_link`)
- [x] Feature link events (`open_interactive`, `suggest_spec`, `report_issue`)
- [x] Plot rotation (`plot_rotate`)
- [x] Server-side og:image tracking (`og_image_view`) with platform detection
- [x] Landing-page navigation tracking (`nav_click`)
- [x] Theme tracking (`theme_toggle` event + `theme` ambient pageview prop)
- [x] Agent chat events (`agent_open`, `agent_data_parsed`, `agent_data_confirmed`, `agent_data_prepared`, `agent_data_undo`, `agent_data_file`, `agent_plot_rendered`, `agent_guardrail_block`, `agent_session_saved`), enum properties only
- [ ] Agent chat paste routing (`agent_input_routed` with `as` and `via`): register the goal and the two properties in Plausible after the deploy
- [x] Agent chat quick feedback (`agent_result_feedback`), with the feedback control
- [ ] Agent chat cut streams (`agent_turn_resumed` with `outcome`): register the goal in Plausible after the deploy

### Plausible dashboard checklist

- [ ] Register all custom properties (see table above, including `action`, `param`, `source`, `platform`, `filter_*`, and for the agent chat `status`, `size_bucket`, `changes`, `version`, `repaired`, `reason`, `include_data`, `reaction`)
- [ ] Create goals for key events
- [ ] Delete the `LCP`, `CLS`, and `INP` goals, whose events stopped on 2026-11-08
- [ ] After the pageview timing of 2026-11-11 is deployed: add the `plots_scrolled` goal and the properties `share`, `results`, and `filtered`; delete the "Scroll 25% on /", "Scroll 50% on /", and "Scroll 75% on /" goals and keep "Scroll 90% on /"
- [ ] Set up funnels (optional)
- [ ] Create custom dashboard widgets (optional)

---

**Last Updated**: 2026-11-11
**Status**: Production-ready with full journey tracking, server-side og:image analytics, landing-page nav tracking, theme analytics, and the analytics shield against automation
