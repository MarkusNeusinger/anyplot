# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning is product communication
rather than library SemVer: major for milestone releases, minor for feature batches, patch for
fix-only (see `agentic/commands/release.md`). A PR adds its entries as a fragment, never here;
only a release folds them in. How entries and releases get here is in
[`changelog.d/README.md`](changelog.d/README.md).

## [Unreleased]

## [4.1.0] — 2026-11-11 — Fine-tuning

### Added

- **The pipeline records when a new version stops working in the agent
  chat.** impl-generate and impl-repair scan a Python implementation and its
  predecessor on `main` with the chat's validator
  (`automation/scripts/readiness_scan.py`) and record the refusals only the
  new file has. Record-only: one log line, a job-summary line, and
  `adapt/readiness.json` in staging; nothing reads it yet. On the six
  regenerations of 2026-11-11 it finds two regressions, one of which turned
  a file the chat accepted into one it refuses. (#13054)
- **"Shared links" on the stats page.** A tile with the links to the site
  shared over the last 28 days: one bar per day, the platforms with their
  totals, and the five most shared plot pages. The owner's debug page shows the
  same numbers plus the preview fetches that are no share. The numbers come
  from `GET /insights/shared-links` and `GET /debug/shared-links`. (#13055)
- **Share counters in the database.** A messenger or a social network fetches a
  page's preview image when a person shares its link, and the API now counts
  that fetch itself: one row of the new `link_shares` table per day, platform,
  and page, with no address, no user agent, and no time of day. The rows are
  kept without a time limit, and the legal page says so. Only the production
  service counts, and only an image it served. (#13055)
- **Each counter says whether Cloudflare verified the fetcher.** The platform's
  name is read from a user agent the client wrote, and the row keeps no user
  agent, so the verdict is what tells a platform's own fetch from a scanner
  that signs as one. The debug page shows the verified part beside each total;
  the public numbers count a share whatever the verdict, because WhatsApp and
  Signal fetch the preview from the sender's phone, which nobody can verify.
  (#13055)
- **The review records whether an implementation keeps the generator's
  static contract.** impl-review runs `automation/scripts/contract_check.py`
  on the file at the PR head and, on a regeneration, on its predecessor. Six
  rules: the mandated title tail, the theme read, the themed save target, no
  legacy brand colour, no named library colormap, and no hex outside the
  style guide's palette. Record-only: it writes a job-summary line and a
  notice, and nothing reads the result yet. On `main`, 919 of 4,863 files
  break the title rule, 499 hold a hex outside the palette, and 151 use a
  library colormap, so the rules that become defect lines are chosen from the
  nightly records. The palette rule only records: a colour outside the
  Imprint palette is allowed when there is a very good reason. (#13045)
- **`/debug` shows a feedback case's turn record.** The case detail gains a
  `# turns` block: one row per turn with the page's action or a message, how
  the turn ended, and as chips the guards that fired and the tool calls,
  identical neighbours folded (`get_dataset_profile ×2`). A failed render, a
  broken tool or a lost reply marks its row red; a refusal, a refused call
  such as `plot_as_confirmed`, a cap or a reply check that changed the reply
  marks it amber. Selecting a row opens the turn's whole record: every call
  with its verdict, outcome and code, every guard verdict in order, the
  `prep_ops`, and what the bounds left out. The transcript labels each user
  line with its turn number, so a row leads to its message. A case sent
  before the record says so instead. `GET /debug/agent/cases/{id}` carries
  the record as `turns`, every code closed again to the record's
  vocabularies, which a test pins to the agents service's. (#13044)
- **`plots_scrolled`: how far a visitor gets through the gallery.** One
  Plausible event per visit to `/plots`, sent when the visit ends, and none for
  a visit without scrolling. `share` is the deepest point as a share of the
  result list (`0-10`, `10-25`, `25-50`, `50-75`, `75-100`, the percentage the
  filter bar shows), `results` is the size of that list (`1-24`, `25-99`,
  `100-999`, `1000+`), and `filtered` says whether it was filtered. The gallery
  loads in batches, so the page has no fixed height and Plausible's own scroll
  depth says nothing about it. (#13046)
- **The review warns when the staged renders don't come from the code under
  review.** impl-generate and impl-repair stage `render.sha256` beside the
  PNGs: the sha256 of the implementation they rendered, with its `Quality:`
  header line reset to `pending`. impl-review compares it with the file at the
  PR head and, on a mismatch or a missing hash, posts a comment and a
  job-summary line. Warn-only for a first night: the review, its score, and the
  verdict stay as they were. Both workflows also record, warn-only, whether a
  render is older than the implementation file. The catalogue audit of
  2026-11-08 traced 50 findings to renders that didn't come from the merged
  code. (#13034)
- **Machine readers on the stats page.** A new tile right after the visitors
  strip shows, per UTC day of the last 28, the requests of crawlers and AI
  assistants that Cloudflare verified, split into reads for a person, AI index
  and training reads, and search engines, with the MCP requests of every client
  beside them and a footnote naming the unverified requests of named vendors
  that are not counted. It reads `GET /insights/machine-readers`, counts only,
  from the machine-read lines in BigQuery; a failed query answers
  `unavailable` and is never cached, so the tile recovers on the next load.
  The About page and the README point at it. (#13015)
- **A machine readers section on `/debug`.** `GET /debug/machine-readers`
  (admin, 7 or 30 days) answers every live line whatever its verdict, status
  or surface: the totals, one row per vendor and purpose with Cloudflare's
  category, the counts per surface, the 404s and its five most requested
  routes, and one row per day by audience. The section draws them as tiles, one
  matrix that opens a row to its routes, and a per-day table. (#13015)
- **One working line at the foot of the agent chat, with the plot's clock.** Every turn in flight
  says what it does now beside the site's loader, on both lanes: `drawing your plot · 0:42`, from
  the second try on with the try (`second try`, or `try 2 of 2` from the server's round cap),
  `waiting · you are 3rd` while the own turn waits in the run queue, the words of a turn without
  plot work, and `writing the reply` below the card. It replaces the thread's in-progress line,
  the progress timeline below the thread and the queue counter, so one position shows on screen.
  The status line counts the same clock beside `usually 1–3 min`, hidden from the plot button's
  description, and a shipped card keeps it as `ready in 1:12`. A phone reads `drawing · 0:42`.
  (#12950)
- **The service's mood on the chat window's tab.** `~/anyplot.ai/agent · ● quiet`, `● busy` or
  `● resting until 01:00` on the visitor's own clock, the same for every visitor and for an
  admin, from the one reader of `/status`, which reads again after each run, when the tab becomes
  visible again and every 60 s while it is visible. A `service_paused` refusal rests it at once.
  It replaces the pause note above the composer. On a phone the resting mood reads
  `● back at 01:00`. (#12950)
- **The progress grid and the admin meters in the admin menu.** The running turn's grid moved
  from below the thread into the admin menu, and on the admin lane the menu shows
  `now 2 runs · today 62 %`, read again as it opens, also during a run. The day budget's share is
  one function for the debug page and the chat, so the two never disagree. (#12950)
- **Machine-read lines: one content-free record per crawler, AI assistant or
  MCP read.** The API (`api/machine_reads.py`) and the site's nginx
  (`log_format machine_read` in `app/nginx.conf`) write one JSON line per
  machine request, whoever answered it: the vendor and its purpose from
  `AI_AGENTS`, Cloudflare's verified bot category or none, a closed route
  name, the catalogue ids of a served answer, and the status, never an IP
  address, a user agent, a query string or a raw path. MCP requests write one
  line per JSON-RPC request with the tool's name. nginx copies the edge's
  verdict onto its prerender hop, because the Transform Rule removes it there;
  the apex Worker deletes it, so the apex path can't be forged into a verified
  read. Two BigQuery views (`api/telemetry/views/`) and the one-time Cloud
  Logging and BigQuery setup are in `docs/reference/machine-readers.md`; the
  legal page names the record, its fields and its 180-day retention. (#12962)
- **A feedback case shows what the chat assistant called and what its guards said, turn by turn.** The session bundle,
  and with it every stored case, carries `turns`: per turn its number, how it ended, every tool call in order (refused
  ones too) with the guard's verdict, what the call did and the code of its answer, and the verdicts of the scope
  judge, the output guard, the reply checks, the budget and the run queue. The persona round of 2026-11-06 had to
  infer several root causes because a case held none of this. Closed codes only, no argument, result, id or time; the
  record keeps the latest 50 turns per session and is never matched against log lines. (#12948)
- **The zone's security rules are written down.** The Cloudflare Pro rules
  applied on 2026-11-09 live only in the dashboard, so `infra/cloudflare/README.md`
  now records each one with its purpose and, where the rule has them, its ID,
  phase, expression, and action: the
  Cloudflare Managed Ruleset and the OWASP Core Ruleset at paranoia level 1, both
  answering with a Managed Challenge and the first sparing the free-text routes;
  the transform rule that hands `cf.verified_bot_category` to the API; the smoke
  bypass and the other custom, rate-limit, and cache rules; the Super Bot Fight
  Mode settings, with the switch to Managed Challenge left as an open decision;
  and the principle that no rule hard-blocks traffic that could be a human. The
  AI Crawl Control block rule was deleted the same night, so no crawler is
  blocked at the edge; `docs/reference/seo.md` follows. (#12864)
- **The site smoke gets past Super Bot Fight Mode.** With `SMOKE_TOKEN` set,
  `scripts/site-smoke.mjs` sends `X-Smoke-Token` to the site hosts' own pages and
  nowhere else, never under `/api`, where the Worker and nginx pass headers on to
  the API and Plausible. So the Cloudflare skip rule lets the headless run through even
  if automated traffic is challenged. A page Cloudflare challenges anyway reads
  `SKIP` and the run exits 2, because a challenge page says nothing about the
  site; before, it would have read as an outage. A change to the script now also
  runs CI's app-image smoke. (#12864)
- **Questions in the agent chat are a turn kind of their own.** A typed
  message that changed nothing gets a small `?` beside its bubble, and its
  reply starts with `? answer · nothing changed`; the chapter line counts its
  questions (`# data · 2 questions`), a button that moves the focus to each in
  turn with a short green highlight. "Nothing changed" has to hold by the
  server's word (`done.turn`, new on the page) and by what the turn's stream
  showed, so a plot, a data version, a switch or a chosen language always wins
  over the server's `answer`, a wish kept for the first plot never reads as a
  question, and the memory read after the turn still vetoes. The note typed
  with an attachment is never one: its reply summarizes the data that just
  came. (#12826)
- **A plot card names the remembered decisions it kept.** The open card's
  first line reads `kept: y = 7 line · x label · new: log scale on y` (under
  the image on a phone), from the ids the server sends with each version
  (`plot.memory`). The label keeps the request the version answered, so a
  folded version still says what it was for. The texts stay with the version,
  so a later `.forget()` never rewrites an older card, and a version whose
  memory the server did not name shows no line, never `kept 0`. (#12826)
- **A project skill audits the live catalogue and repairs what the owner
  picks.** `audit-catalogue` turns the MUI X 9 night's ad-hoc loop into rounds.
  `select_candidates.py` selects pairs read-only, from thumbs-down votes (one
  per visitor session, split at the last update), low or capped stored scores
  and kept defects, stale library versions or GCS renders (checked with a
  cache-buster), agent-validator refusals, or a library sweep. An audit
  workflow looks at both renders, the spec and the merged review, and a
  skeptic tries to refute every high or medium finding. `build_page.py` turns
  what survives into a private Artifact page with ids the owner picks from.
  Only then do fixes happen in fresh worktrees, checked by `check_fix.py`
  (scope, header, validator, a local render for Python and JavaScript in a
  scrubbed environment). `dispatch.sh` adopts them from their full SHA, one
  bulk-generate run at a time, so it never cancels a pending run such as
  daily-regen's, and only under an OK bound to a token over the queue and its
  planned SHAs; a gallery shows the owner each fix next to production first.
  R and Julia go through a forced regeneration, stale renders through a
  re-render from `main`, and spec causes through a spec issue the owner files.
  `verify_merged.py` then checks every merged pair on the live site: the code
  on `main` against the fix, the metadata, the database row, both PNGs and the
  `_800.webp` the site shows, and the API. A pair whose fix a pipeline repair
  changed goes to a skeptic's re-audit instead of passing, and passes only
  once that re-audit judges the merged pair clean. (#12825)
- **A binding warning with counts when a plot's key repeats.** For the 90 specs whose plot draws one value per
  key, such as a bar per category, a cell per pair or a point per x of each series, the binding check warns
  when the bound key columns hold fewer keys than the rows that need a mark, for example `x: column 'Length'
  holds 9 values in 27 rows`. The bindings route, `set_bindings` and the session block carry it, and the
  assistant offers the counted `aggregate` instead of letting the plot code average the rows without a count,
  as a persona-test line chart did with 27 measurements. Scatter, box, histogram, strip and other plots where
  repeats are the point never warn, and no default binding changes (#12824).
- **A server line in "what changed" for rows the plot cannot draw.** When a bound column of a mark has empty
  cells, the shipped plot's changes say how many rows draw no mark, per role, for example `2 rows without y
  ('Exam Score')`, for all 15 libraries. It counts only the required roles that place a mark, never a label, an
  optional role or a spec's shorter list beside the rows, such as event dates, and it leaves the status as it
  is (#12824).
- **The chat stream says what a turn changed, which decisions a plot kept, and the round cap.** A turn that ends
  well closes with `done.turn` (`answer`, `data`, `plot`, `switch`, `language`, `kept` or `memory`), which the
  agents service derives from a new per-turn record of the assistant's tool calls (closed tool names, the guards'
  verdicts and a closed outcome per call, never an argument) instead of from the reply. A stored version's `plot`
  event carries `memory: {kept, added}`, the plot memory entry ids it stands on, and every pipeline step's `status`
  carries `max_attempts`. The page can then tell a question from a turn that only kept a wish for the first plot,
  label a version `kept 3`, and say "try 2 of 3" from the server's numbers; an older page ignores all three.
  (#12607)
- **The chat rebuilds from your original table.** `prepare_data` and
  `query_data` take `from_version`: the current version (the default), the
  original table as pasted or opened, or a version number the session block
  lists with the change that made it. "The first 20 after all" after a top
  10 is one call from the original, stored as the next version on top, and
  its first change line says where it started ("from your original table:
  kept the first 20 of 487 rows"); a question reads the pace per run after
  a weekly sum the same way. The history is never rewritten, the user
  confirms the new data, and `.undo()` stays one step back. The original
  stays in the store past the five-version undo history, and a version of
  data a new paste replaced is refused with a closed code (`other_paste`).
  It came from the persona tests of 2026-11-06, where the chat sent users to
  `.undo()` or a new paste three times. (#12600)
- **Derived columns in the data step.** `prepare_data` takes four new
  operations: `compute` adds a number column from an expression over number
  columns (a product, a power, a log, a unit conversion), checked by the
  whitelist `generate_data` already runs, computed exactly for whole
  numbers and in exact decimals for plain arithmetic (`19.99 * 3` is
  59.97); `diff` adds the change from the row one or n places before;
  `rolling` adds a mean or a sum over the last n rows; and `blank` empties
  missing-value codes such as `-0.99` in place while the rows stay. The
  first rows of each group, a missing input, a division by zero and a value
  outside a function's domain leave a cell empty, and the change line counts
  each. It came from the persona tests of 2026-11-06, where five of ten
  personas got no plot because a column could not be derived. (#12597)
- **The last value per month, over several columns.** `aggregate` takes
  `columns`, two to ten value columns with one reduction, and the reductions
  `first` and `last`, by time within each period of a date key, so the last meter
  reading of each month is one operation. (#12597)
- **The top N rows.** `keep_rows` keeps the first n rows in their current
  order, so "the top 10 by revenue" is a sort and a `keep_rows`; the change
  line counts the rows kept and dropped. (#12597)
- **Several values into one category.** A condition takes `values`, an "any
  of" list for `eq` and `contains`, so `classify` puts `Miete` and `Strom`
  into one label, and its change line names how many rows fell to the
  fallback and their three largest groups. (#12597)
- **The chat names what it cannot do.** A change no operation can make, such
  as filling in values, is the `unsupported` operation: it changes nothing,
  answers a fixed sentence in the session language that never sends the user
  to a spreadsheet, and counts the gap by its family in the `chat_turn`
  telemetry (`capability_gap`). (#12597)
- **`agent_turn_resumed`.** A Plausible event with `outcome` (`resumed`, `gone`, `failed`) counts every chat turn
  whose stream was cut after its first event, and whether the page read its result anyway. The origin's logs cannot
  see a cut between the browser and the edge, so this event is how often it happens. (#12572)
- **A decimal comma reads ambiguous dots again from the pasted cells.** A pasted number column of whole numbers
  and `1.234` shapes that nothing else in the file settles now reads as decimals with a warning ("dots read as
  decimal points; say so in the chat if they separate thousands"), and the paste keeps the column's cells as
  written. When the user says the dots separate thousands, the assistant's `set_type` with a decimal comma reads
  the column again from those cells, so `7.000` becomes 7000 rather than 7, while the rows are still the paste's.
  (#12565)
- **`agent_input_routed`.** A Plausible event with `as` (`data`, `message`) and `via` (`paste`, `file`) counts how
  the message box takes each paste and file, for tuning the routing. `agent_data_file` gains the outcomes
  `attached` and `removed`; `filled`, `replaced` and `kept` end with the data card's box. (#12565)
- **The README says who builds anyplot and how.** A "How I build anyplot" section on its first screen
  says who leads the models and how. "Engineering highlights" names seven decisions, each with its
  reason and a link to the code that carries it out. An "Architecture" section draws the services and
  the pipeline as two Mermaid diagrams. Before this, the README described the system in passive voice
  and never said what the human behind it does. (#12559)
- **A showcase image in the README, drawn from live data, and a test that keeps the README honest.**
  `scripts/readme_showcase.py` lays out one spec per library from the `_800` light previews. Its
  counts come from `/stats` and the library registry, and its type is MonoLisa with the script
  italic; the script stops rather than fall back to another font. It replaces the ridgeline preview
  card and links to `/plots`. `tests/unit/test_readme_claims.py` reads each value the highlights, the
  architecture and the About page state from its source and fails when the text no longer matches:
  the rubric's criteria and points, the review bar and its step, the pipeline's bounds, the session
  idle time, the default model, the library count and the MCP tools. It also checks every relative
  link and in-page anchor. The pull-request count is now a floor ("more than 850"), a multiple of 50
  at most one step below a count the test records with its date. The release procedure redraws the
  image, updates that count and raises the floor, and `/write-docs` lists the duty. (#12559)
- **A docs page on how anyplot is built with AI agents.** `docs/concepts/ai-workflow.md` covers who does
  what, the path of a change from idea to production, how a repeated mistake becomes a rule or a test,
  a worked example (#12557), and the limits of the approach. The README links it for the full story.
  (#12559)
- **The About page explains the review, the agent chat, and the MCP server.** One short section each,
  linked to `/stats`, `/plots`, and `/mcp`, mirrored in the bot HTML of `/about` so crawlers read the
  same text. (#12559)
- **`.use_my_data()` on the landing page's plot of the day.** It sits beside `github.open()` in the
  card's header and opens the chat for that plot's spec and library. It shows only when the eligibility
  check names a lane, with one request per view, and the chat records `agent_open{source:
  plot_of_the_day}`. (#12559)
- **Dates as numbers in the data step.** `prepare_data` takes a `date_number`
  operation that adds a number column beside a date column: the calendar
  year, the whole days since the column's earliest date, the Unix time in
  seconds (UTC, with the change line saying how a date without a time and a
  time without an offset were read), or a decimal year. A missing date stays
  empty, the change line counts the dates and the empty cells, the new column
  fills an open role that takes numbers, and `.undo()` takes it back. It came
  from the owner's test of a customers table on `scatter-basic`, where
  "convert subscription date to integer" had no operation and `y` stayed
  open. (#12558)
- **An open number role offers a free date column.** When a required role
  that takes numbers only stays open and a date column is free, the session
  block lists `date_number` as an offer, never made unasked: the unit is the
  user's choice, so the assistant names it in one statement, and a request
  without a unit takes the days since the first date. (#12558)
- **The assistant answers a request for another plot type.** Asked for a violin plot or for the plots that would
  suit the data, it says in one or two sentences that switching the plot type in the chat is planned but not
  possible yet, may name a kind of plot that fits the data, and points to the catalogue at anyplot.ai/plots, where
  each plot's page leads to its own chat and the data is pasted again. It never says the catalogue has a
  particular type, since it does not know the catalogue. The scope judge reads such requests as in scope, with four
  new cases in the scope eval and four in the prep eval, in English and German. (#12557)
- **Text operations in the data step.** `prepare_data` takes four more
  operations with literal texts only, never a pattern: `split` a column at a
  separator into 2 to 10 new columns (`10–25` gives 10 and 25; a leading
  minus stays a sign), `extract` only the number, the digits or the letters of
  each cell, `strip` a prefix or a suffix, and `replace` a text. Each writes
  new columns beside its source, typed as `set_type` reads them (the dataset's
  decimal mark, its thousands rules, at most a tenth of failing cells, which
  the change line counts), and the steps chain in one call, so a column of
  ranges no longer sends the user to a spreadsheet. (#12556)
- **A column of ranges fills a lower and upper bound pair left open.** When
  `min_value` and `max_value` (or `ci_lower` and `ci_upper`, `low` and `high`)
  have no columns and a text column holds two numbers around one dash in every
  cell, the first never above the second, the session block lists its `split`
  as a certain conversion, and the service binds the two new columns to the
  pair. ISO dates, negative numbers, decimal commas, thousands separators, ids
  and spans of years keep their reading. (#12556)
- **`.example_data()` in the agent chat.** While a session has no data, a line above the composer offers
  `# no data at hand?  .example_data()`, which asks the assistant for a made-up table to try the plot and counts the
  seconds while it works. It is a turn action (`example_data`), not the words "example data": the first typed message
  sets the session language, so typed English would have kept a German visitor in English, while the action leaves
  the language to the visitor's own first message. The assistant's prompt names the new control, the picture of the
  catalogue plot in the header and the columns ⓘ, so it can point visitors to them. (#12553)
- **A project skill triages the agent chat's feedback cases in rounds.**
  `triage-agent-cases` lists the open cases read-only, copies their files to a
  private directory outside every checkout, and classifies each one as fixed
  (with the PR), in progress (with a failure-class tag and a general fix) or
  won't solve, in a private report. After the owner's OK for the round,
  `apply_triage.py` writes the statuses and tags in one transaction, after a
  snapshot of the rows, and refuses a row someone changed since the round read
  it. The cases hold users' data, so nothing of them reaches the repository.
  (#12551)
- **A feedback case explains itself.** Each pipeline round now carries the ids
  of the gates its renders failed (`R1`, `G8`) and the closed class of a crash
  (`key`, `timeout`), and every session bundle names how many versions the
  session held and how its latest plot run ended. A chat case, which holds no
  version, now tells a plot the page missed from a run that failed, and the
  `/debug` case view shows a line per round and the session's line. All of it
  is closed codes and counts, never a message or a cell of the data. (#12552)
- **The chat header shows the plot it adapts.** A thumbnail of the catalogue
  plot sits beside the spec's title on `/agent`, in the library in use and the
  site theme, and opens large in a dialog; the columns the plot expects stand
  behind an ⓘ after the title, closed by default. The visitor keeps in view
  what the data should become without leaving the chat (#12549).
- **`.use_my_data() →` on the spec hub and in the code tab.** The hub page
  `/{spec-id}`, where links from the landing page, `/specs`, `/map` and the
  README arrive, offers the chat in its header, with one eligibility request
  per view (matplotlib where it is among the cards shown, else the first of
  them), and the plot page's code tab offers it beside `.copy()`. The chat
  records these opens as `agent_open{source: spec_hub}` and `plot_page`
  (#12549).

### Changed

- **Preview images are cached for five minutes**, not for an hour (plot pages)
  or a day (home and plots). A fetch the edge answers from its cache never
  reaches the API, so most repeated previews went uncounted. (#13055)
- **Platforms are named for what fetched.** Telegram signs as
  `TelegramBot (like TwitterBot)` and was counted as Twitter, and Apple's
  Messages signs as Facebook and Twitter at once. Slack fetches the
  image through `Slack-ImgProxy` and GitHub through `github-camo`, and neither
  had a name. Microsoft's preview service still signs as SkypeUriPreview and is
  counted as Teams, since Skype closed in May 2025. (#13055)
- **Machine readers: the apex Worker deletes the verdict headers.** The owner
  redeployed `anyplot-api-proxy` on 2026-11-11, step 9 of the machine-readers
  runbook and its last one, so a caller of `anyplot.ai/api/*` can no longer
  label itself a verified bot in the telemetry. The runbook's state table says
  so, and "Verify on day one" gains the check that proved it: a forged
  `X-Prerender-Bot-Category` on `/api/llms-full.txt` and a forged
  `X-Verified-Bot-Category` on `/api/specs` both arrive with an empty
  `verified_category`. (#13053)
- **The chat refuses a message of spaces alone.** `POST …/messages` answers
  `422` for a `text` without a visible character. The page never sent one; a
  hand-made request could, and its turn left no transcript line, so a case's
  turn record and transcript named different turns from there on. (#13044)
- **The layout sends every page's pageview, at the navigation.** `RootLayout`
  records the page in a layout effect; the pages no longer send their own,
  150 ms late, from an effect. Only the gallery still records a page itself,
  when a filter changes its address without a navigation. Three visible
  consequences: the 404 page now records a pageview, under the path that was
  asked for; a visitor's visit to `/agent` counts whatever the page shows,
  also while the public lane is closed (`agent_open` still counts sessions
  only); and a spec page counts when it is opened, not once its data loaded.
  (#13046)
- **An address that only redirects is no page.** `/{spec}/{language}` and
  `/debug/agent` redirect in their route's loader now
  (`app/src/routes/redirects.ts`), so the router never renders them: no
  pageview, no history entry, and the page being left stays on screen until
  the destination is there. (#13046)
- **The agent chat's plot button says what one click does.** Under its name stands a small line:
  `ask · edit data · change plot` under `.update_plot() →`, whose click sends the message box's
  text as Enter does and so also answers a question or changes the data, and
  `confirm data · plot it` under `.create_plot() →` and `plot the new data`. The box's placeholder
  after the first plot reads "ask a question or a change". It stays one button; the name alone
  suggested that a question needs another way. (#13043)
- **The agents' tree-sitter grammars are baked into the image, and the service
  never downloads one.** tree-sitter-language-pack moves from 0.13.0 to 1.24.0,
  whose wheel ships no grammars and whose `get_language` downloads a 23 MB bundle
  on first use. `agents/Dockerfile` now fetches the bundle at build time and keeps
  the four grammars the code profiles read (6.2 MB) in a root-owned directory. The
  service loads them through the pack's `LanguageRegistry`, which never downloads,
  and stops at its start when one is missing. A checkout and CI fetch them once
  with `uv run python -m tools.tree_sitter_grammars`. (#12943)
- **Each `role: column` pair on the data card changes its own column.** The
  bindings line under the preview (`direction: day (UTC) · frequency: new
  chats`) only listed the bindings, and `.change()` at its end was easy to
  miss. Now each pair is a button with a dotted underline: a click opens the
  dropdowns with that role's dropdown focused and its list open, or a family's
  `+ y` focused. Escape inside the dropdowns closes them and returns the focus
  to the pair. While the dropdowns would not answer, during a step or with the
  fan-out's panel open, the pairs stay plain text. `.change()` still opens
  every dropdown. On a phone each pair is a 32 px target, and the rows of a
  line that wraps never overlap. (#13005)
- **Shorter message box placeholders on a phone.** A phone cuts a placeholder without an
  ellipsis, so below 600 px the box reads "ask or say what to plot" before the first plot and
  "ask for a change" after it; the wider screen keeps its longer words. (#12950)
- **`AI_AGENTS` names 18 more crawler tokens and a new `seo` purpose.**
  Amazonbot, meta-externalagent, Google-CloudVertexBot, ExaSearchBot,
  Keenable, Bytespider, CCBot, Qwant, PetalBot, the Sogou spider and six SEO
  tools join the table, and xAI-SearchBot is an index read instead of a
  user-directed one. A crawler's og:image fetch now sends nothing to
  Plausible; social and messenger previews still count on anyplot.ai. (#12962)
- **`visitor_ip` reports a public address only, `cf-connecting-ip` first.**
  The one remaining consumer, the og:image event, gets Cloudflare's
  unforgeable address before the forwarded list, and a forged private or
  reserved address at the front of that list is skipped. (#12962)
- **"plot the new data" keeps what you tuned when it can.** The button has an
  action of its own now (`plot_new_data`). When the data comes from the paste
  the library's latest plot drew and the same columns stand in the same roles,
  the run changes that plot for the new data, with one request the server
  writes, so a title, colours or limits the remembered decisions never held
  stay. A new paste, a binding change or a reshape still starts from the
  catalogue plot with the remembered decisions, and now keeps the theme you
  asked for. The plot's `new_data` says which, the card's label names it
  (`new data on v3`), and `.start_over()` stands beside the button whenever
  the library has a plot. The usage telemetry counts the base per run.
  (#12834)
- **The plot code draws every row it gets, in all four languages.** The shared adapter rule no longer lets
  the plot code group, pivot or filter the user's rows: it splits them into series and groups, computes the
  statistic its plot type draws (quartiles, bins, a density, a fit) and the computed roles, but never filters
  by a value, cuts to the first or largest rows, samples, drops duplicates or averages the rows of one key.
  A change request, an earlier request or a plot-memory decision that asks for such a change is left out with
  one note, and the assistant offers it as a data step with counts and an undo, and sends such wishes to the
  data step from then on. The random draws stay for jitter only. In the persona round of 2026-11-06 a line
  chart averaged 27 measurements to 9 points in its code without a count (#12953).
- **A plot of rows that repeat a key combines them first, as a data step.** When a bar, slice, cell or line point
  would draw several rows of one key, the server makes the aggregate the assistant offers before the plot runs:
  a new data version, numbered, on the data card and undoable, with the mean per key, or the sum where the marks
  add up (slices, stacked segments, counts). The plot's "what changed" announces it with both counts, for example
  "averaged 'Reading' over 27 rows into 9, one per 'Length'", and the plot draws every row of that version.
  Price charts and other plots whose measures need several functions keep the warning instead. With the prompt
  rule alone, the plot code still averaged such rows itself in both measured runs (#12953).
- **The assistant names rows the plot draws no mark for.** The server's "The plot draws no mark where a value
  is missing" line is named in every reply to that plot, as what the plot draws and never as rows removed
  from the data, and stays on the list of notices that a short reply keeps (#12953).
- **Eval cases can take data steps before the plot.** A matrix case's `before_operations` are stored as the
  session's next data versions through the server's own code, with no model call. The 45 `n5000` cases of
  `bar-grouped`, `heatmap-basic` and `pie-basic` use it for the aggregate the assistant offers on their
  repeated keys, since their plot code no longer aggregates the raw records itself (#12953).
- **A plot wish pasted with new data reaches the plot of that data.** The
  assistant's `keep_plot_request` refused a note once the library had a plot,
  so a title typed with a second paste never reached its plot. A plot of data
  that a later paste replaced is no plot of the current data now: the note is
  kept for the first plot of the new data, also when the assistant sends it as
  a change of the old plot, and the session block tells the assistant so. Each
  shipped version records the data version it drew. (#12832)
- **New data drops what a library switch carried.** A paste, a change of the
  data, `.to_long()` and an undo drop the switch's carry (the theme, the texts
  and the requests of a plot of the data before), as they already drop a kept
  first-plot note, and the page ends its offer with them. A switch or the admin
  fan-out's copy after the data changed takes only the theme you asked for on
  the plot of the earlier data, never its texts or requests, besides the
  remembered decisions, so the public and the admin lane treat a new paste
  alike. (#12832)
- **The remembered decisions show where new data meets them.** When a paste
  lacks a column the data before it was bound to, the paste answer says
  `columns_changed`, and the new `# data` line holds the decisions until the
  next plot: `3 earlier decisions ▾ · .forget_all()`. One click forgets them
  all; ignored, they stay, since only the user clears the memory. (#12832)
- **The agent chat stays English until you pick another language.** A message
  or a paste in another language no longer switches the replies and the plot:
  the chat offers that language once, in one line,
  `# German detected in your message · .switch()` (or `in your data`), and
  ignoring the line keeps everything English. `.switch()` sets the replies and
  the plot labels (`PUT /language` with `via: offer`); with a plot on screen
  the next version comes in the new language, and after the switch the chat may
  offer English back once. A pick in the header's language menu, or a request
  in the chat such as "auf Deutsch bitte", ends the offers. The fixed refusals
  use the session language now, never the message's, and the reply-language
  check asks again when the assistant answers an English session in the
  language it offered. The page is English, so a visitor who never asked for
  German should not get German replies; the offer replaces the
  `# reply language: de` notice, which repeated for every paste and first
  message. The agents service's content-free usage telemetry counts the offers
  and the picks as the `language_offer` event (`via`: `shown`, `offer` or
  `header`, and the language as a closed code); the page sends no Plausible
  event for them, since most chat sessions are the owner's and the Plausible
  dashboard is public. (#12865)
- **The chat assistant's turn bounds are code, not prompt sentences.** Each turn may call `prepare_data` and
  `generate_data` twice, `query_data` three times, `run_data_code` twice and the plot pipeline once. The call after a
  cap is refused with a fixed message that tells the assistant to answer with what it has, so the "never more than
  twice" sentences left its instructions. (#12853)
- **No plot run in a turn that changed the data, or on a paste's summary turn.** The server refuses the plot call
  before the run (on a summary turn while the data is unconfirmed), keeps the first plot's wish, and records the stop
  as before. The chat shows no failed plot card for such a turn, and the daily run count no longer counts it, nor a
  plot call made after a library switch was asked for. (#12853)
- **The plot buttons' turns tell the assistant what to call.** On "create the plot" turns, the session facts say to
  call the plot pipeline with no arguments, so the instructions no longer open that rule with it. (#12853)
- **robots.txt welcomes every crawler, Bytespider included.** The group that
  declined Bytespider on bandwidth grounds is gone from `app/public/robots.txt`,
  matching the deletion of its Cloudflare block on 2026-11-09: the owner decided
  that every crawler is welcome, and blocking returns only on evidence from the
  request logs. The deploy smoke in `app/cloudbuild.yaml` and the daily
  `bot-serving-check` now recognise the static file by its `Sitemap:` line, which
  the API's own robots.txt lacks while it shares `User-agent: *` and the
  Content-Signal line, so a misrouted request still fails them.
  `docs/reference/seo.md` and the `app/nginx.conf` comment follow. (#12868)
- **The plot button sends, reads and plots in one click.** With a file opened with `.open()`, a
  pasted table or a typed table in the message box, `.create_plot() →` (after a plot
  `plot the new data`) is active: it sends the data as Enter would, with the typed text as its note, and
  once the reading comes back clean the page confirms the data and starts the plot by itself.
  A reading that is not clean (a required role without a column, a warning on the data card or
  from the server's binding check, a question back from the assistant, a refusal, an error or a
  stop) halts at the data card, and the status line says what to look at. Typing or another
  click while the reading runs ends the chain, which never plots twice. Enter still only sends.
  Until now the button stayed greyed out with an attachment in the box, and only Enter read it.
  (#12833)
- **Plot votes count per version of the image.** A 👍/👎 belongs to the image it was cast on: once a plot is
  regenerated (its `updated` changes), only the votes from that moment on count for the current version, and the
  earlier ones stay in the table as votes on an earlier version; nothing is deleted. A visitor who rated the old
  image may rate the new one once: the page keeps its vote per spec, language, library and version, so the old
  thumb no longer stays inked on the new image, and the API's one-vote-per-session guard looks only at the current
  version. A vote stored before this change inks nothing and blocks nothing. One rule in `core/plot_votes.py`
  serves the API, the debug list and the audit skill's selector, which now counts a session once on each side of
  the update. (#12830)
- **`/debug` ranks the plots by their votes.** The "votes per plot" list has one row per implementation with the
  current version's 👍, 👎 and their total, the earlier versions' counts beside them and the newest vote, sorted
  by thumbs down, thumbs up or total from the column headers. It counts one vote per visitor and version and shows
  counts only. `GET /debug/feedback/votes` serves it and replaces `GET /debug/feedback/top`, whose two lists grouped
  the rows of one reaction by page path. (#12830)
- **The remembered decisions moved from above the composer to the latest
  `# plot` line.** `3 decisions ▾` there unfolds their list under the line,
  each with `.forget()`, then `.forget_all()` and the ⓘ, as the v4 design
  draws it; the `# remembered` heading with `.hide()` and `.show()` is gone.
  The list moves with its open state and the focus when a newer plot chapter
  opens, and a removal is still announced outside the thread's log. (#12826)
- **The prep eval scores a case by the table its turn leaves.** The session's data version after the turn must
  equal the table the case's expected operations make from the same version through the same server code
  (`apply_and_parse`, the `generate_data` parse): the same columns in order, dtypes, row count and cells, numbers
  within a 1e-9 relative tolerance, rows in their order unless the case sets `row_order: "any"`. Another sequence
  that makes the same table now matches: guard 2a of #12599 had read `de-hard-kette-gesamtzeile` as a miss when
  the root left out a `drop_columns` that the `aggregate` made anyway. The exact operation match stays as the
  diagnostic `ops_exact`, and it still decides a case that expects no data call, a `run_data_code` case, a
  `refuse` case and a case with `strict_operations: true`. A miss names what differs (`table_miss`, columns at
  most, never a cell), `check_cases` refuses an expectation that leaves its table as it is, and a unit test runs
  every table-scored fixture with a root that makes exactly its operations. (#12617)
- **One number per data version, the same on the card and for the assistant.**
  The agents service numbers every data version once per session, across
  pastes, picks, changes, `.to_long()`, copies and computed tables, and never
  gives a number twice: a paste, a change, an undo and a change are v1, v2, v1
  and v3, and a second paste is v4. The data card shows that number, and after
  an undo it carries the number of the version it went back to
  (`data v1 · back to v1`). Until now the page counted versions itself while
  the server's number started over with every paste, so since `from_version` a
  user who asked for "v2" could get a different table from the one the card
  called v2. Every dataset answer and `done.dataset` now carries `can_undo`,
  which the page reads for `.undo()` instead of guessing from the number, and
  `original_version`, from which the `agent_data_undo` bucket still counts the
  paste as 1. (#12616)
- **The adaptability checker reads the roles the plot computes.** `COMPUTED_ROLES` and `mark_computed` moved
  from the agent to `core/spec_roles.py`, and `spec_context` applies them, so the checker, its workflow mirror
  and the smoke run no longer ask for column constants of the 27 roles of 13 specs that the agent already
  treats as computed, such as the Bollinger bands and the moving averages. `CHECKER_VERSION` is 2, so a
  record says which reading produced it (#12612).
- **The EMA chart accepts both pairs its spec names.** `EMA 50` and `EMA 200`, the golden cross of the spec's
  first application, bind without a window warning beside the example's 12 and 26, and the adapter's brief
  names the window it computes an open EMA with: 26 by default, 200 beside a bound `EMA 50` (#12612).
- **A changed `specification.md` runs the unit tests.** The role audit reads every spec's Data bullets, and a
  spec PR used to skip pytest, which left a failure to the next Python PR (#12612).
- **The gallery search ignores generic words and accents.** On `/plots`, the search drops words
  that only say "a chart" or join two terms (chart, plot, graph, diagram, and, with, of, and their
  German, French, Spanish, Italian, Portuguese, Dutch and Polish forms, such as Diagramm,
  graphique, de or wykres) before it matches. A query of nothing but such words still searches as
  typed. `bar chart` now ranks `type:bar` first where it ranked the spec "Bar Chart with Error
  Bars" first, and `line chart` finds the line specs where it found three bar and indicator specs.
  Fuse folds accents and ß on both sides, so `scätter` finds `scatter`. No dictionary translates
  the query: the catalogue's words stay English, so a German `balken` still finds nothing. (#12608)
- **The gallery counter names its units.** It reads `37% · 8 specs · 120 plots` instead of
  `37% · 120`, at both widths. A tag on 8 specs in 15 libraries showed 120 without saying that the
  number counts plots. (#12608)
- **The agent chat reads in chapters, and the data card stays open.** A `# data`
  or `# plot` line opens each stretch of the talk where it turns from the data to
  the plot and back, and a change of the data after a plot opens a new `# data`
  chapter with the card in it. The thread reads in time order (the owner's
  decisions of 2026-11-07): a change asked for in the chat puts the card right
  after the request, before the reply, and the card's own `.undo()`,
  `.to_long()` or a picker moves it to the thread's end, before and after a plot
  alike, each older version folded with its own summary under it. Every data
  version gets its
  number on the card's border (`data v3 · made long · 48 rows × 4 cols`), and
  every older version folds to that label, which opens it read-only. The page
  names a version only by that number: the card's change lines, its full view
  and the status line (`data v3 fits · 48 rows · 4 columns`) no longer show the
  server's version, which starts over with every paste. A library switch is a
  line of its own that names the decisions it keeps. The pinned header above the
  thread and its `.show()` and `.hide()` are gone: the card stays open in both
  steps. The keyboard focus follows a card that moves, and the page keeps the
  focus clear of the site's sticky masthead. (#12604)
- **On a phone the plot button stands under the message box.** Below the
  page's phone width (the theme's `sm`, 600 px) the composer row stacks the
  box on a line of its own and the plot button under it at the full width, so
  the box's placeholder reads at 390 px instead of "ask about yo…". From `sm`
  up nothing changes. The order stays box first for the eye, the DOM and Tab;
  the plot button keeps one text size at every width, and the assistant's
  instructions say "the plot button by the message box", true at both widths.
  (#12603)
- **The agent chat's cards carry their label on the border.** The data card
  and every plot card are framed like the chat window, with what they hold on
  the top border: `data · 48 rows × 4 cols`, and `plot v2 · matplotlib · title
  in German`, the version, its library and the request it answered (cut to 40
  characters; `first plot` or `.start_over()` when there was none). A plot
  card's label is its toggle, and every version but the latest folds to that
  one line (`▸ plot v1 · matplotlib · first plot`); `.expand()` and
  `.collapse()` went with the header row. The data card heads each preview
  column with its name and type (`month · date`, `units · number`), and says
  its bindings in one line (`x (across): month · y (up): revenue · color:
  region`) with `.change()`, which opens the dropdowns; they open by
  themselves while a required role has no column or the server refused the
  bindings. On a phone the card shows no preview table: `.view_all()` and
  `.change()` stand on its last line, and a plot card's image actions stand by
  their names (`.download()`, `.copy_png()`, `.open()`) on the line right under
  the image. The data card's dropdowns and the start item's columns ⓘ name a
  role's kinds in the chips' words (`numbers or dates`, not `numeric /
  datetime`), the status line asks to check the data, not the preview, at
  every width, and the assistant's list of the page's controls says where each
  download sits. (#12601)
- **The agent chat's session keeps an item per data version, per switch and
  per turn outcome, with nothing on the page changed yet.** Every data version
  gets an item with a snapshot of what it held (rows, columns, preview,
  profile, file, sheet, change lines), numbered per session as `data v3`,
  since the server's version starts over with every paste. A version a turn
  made leaves a stub where the card stood and moves the card, under its id, to
  the thread's end; a version from the card's own controls (`.undo()`,
  `.to_long()`, the pickers) puts the stub above the card, which stays in
  place, unless a plot stands below the card, in which case the card moves
  below it too. A library switch adds an item with the decisions it carries,
  and a typed turn carries what it changed (data, plot, switch, language,
  memory, or nothing, which marks a question), read from the stream until the
  server names it. `threadModel.ts` reads chapters, folds and counts from the
  items for the chapter lines to come, and the thread still renders one card
  per paste: a long session replayed through both reducers renders byte for
  byte as before. (#12598)
- **The prep eval covers the new operations.** Eleven cases on invented data,
  one per persona need and one for the top N, and the Fahrenheit case now
  expects a `compute`. A
  `compute` matches by the values it computes, whatever short names and form
  the expression has. The first run matched 91 of 96 cases for $0.27. (#12597)
- **The agent chat opens with what the plot needs.** The thread's first item
  reads "You came from **Basic Scatter Plot**. It needs", then the spec's
  roles as chips in the words of someone with a table, not a dtype
  (`x · numbers`, `numbers or dates`, `y · numbers, one or more` for a family,
  `series · categories, optional`), beside the catalogue plot's thumbnail in
  the library in use, and ends with "drop a file or paste a table below". The
  thumbnail, the columns ⓘ (now after the chips) and the how-to ⓘ moved there
  from the header row, which keeps the title, the library and the language.
  The item repeats no control, since `.example_data()` and `.open()` stand in
  the line above the message box; it is a message in the thread, so it stays
  first and scrolls up with the talk once data arrives. On a phone it is
  compact: a smaller thumbnail beside the first line, the chips below it.
  (#12596)
- **The agent chat's composer is the message box and the plot button.** The
  box with a brand-green border and a `❯` and the plot button share one row,
  on a phone too; one quiet line right above them holds `.example_data()` and
  `.open()` as links, `# no data at hand? .example_data() · .open() a file`,
  highlighted in green until the first data arrives, then muted, `# other
  data? .open() · .example_data()`. Nothing comes, goes or moves: a state
  changes how the line reads, fills the plot button once there is data, and
  makes a control inert with `aria-disabled`, so a focused one keeps the focus
  and a second key press does nothing. Targets are 44 px. Before data the box
  reads "paste a table or drop a file". (#12594)
- **The plot button keeps its place and changes its name.** It stands quiet
  and inert before data, reads `.create_plot() →` with data, `.update_plot() →`
  once the library has a plot (it sends the box's text and waits while the box
  is empty), `plot the new data` after a change to confirmed data or a new
  paste, and `.plot_all()` with the admin fan-out on. After a library switch it
  keeps its name, and the status line names the decisions its plot keeps, in
  place of the "plot in seaborn with your 3 decisions" button. (#12594)
- **Enter sends, and `.send()` is gone.** On a touch screen, whose keyboard
  labels Enter "return", a small `↵` inside the message box sends too.
  (#12594)
- **`.stop()`, `.start_over()` and `.feedback()` stand at the end of the
  status line.** `.stop()` is a button of its own that Tab reaches, and hands
  its focus to the message box when the run ends; `.start_over()` waits there
  once the library has a plot, and `.feedback()` before the first plot opens
  the chat's feedback form above the line. While a plot runs the line reads
  `drawing your plot · usually 1–3 min`, and the admin fan-out's locked line
  moved into it from above the box. (#12594)
- **A reply never sends the user to the plot button.** `root.md` told the
  assistant in four places to say "press `.create_plot()`" while its reply
  rules forbade it; the instructions now leave the button to the status line,
  and ShippedReply drops a sentence that names `.create_plot()`,
  `.update_plot()` or `.plot_all()` in any turn, logged as `plot_button`,
  unless the user's own message asked about the button. Its sentence split no
  longer ends a sentence after an abbreviation such as "e.g." or "z. B.".
  (#12594)
- **One chat page for visitors and admins.** The agent chat lives at `/agent`
  for everyone: the page detects an admin (the admin hint from `/debug` plus a
  successful admin call) and then calls the admin API, else the public API with
  its bot check. The admin's chat looks and behaves exactly like a visitor's,
  so the owner sees every problem a visitor meets; the server still enforces
  each tier's limits. `/debug/agent` only redirects to `/agent`, keeping the
  pair in the link, so an old bookmark still opens the admin's chat, and the
  admin signs in on `/debug`. (#12589)
- **Every admin extra sits behind one admin menu.** `admin ▾` at the header
  row's end, where the `⋯` menu stood, holds the fan-out toggle
  `all 15 libraries` (in place of the library menu's `all` and the URL's
  `&all=1`), `.save()`, a "view as visitor" switch that runs the public lane
  exactly for the tab, and the admin's diagnostics. An expired admin session
  falls back to the visitor's chat, and the menu says so with a link to
  `/debug`. (#12589)
- **An admin sees what a visitor sees.** The experimental notice, the feedback
  form's consent line and its unticked `# include data.csv` box show for an
  admin too, `.save()` starts unticked as well, and a switched-off service
  reads the same; a parity test fails on any other difference in the page.
  (#12589)
- **An admin's use of the chat no longer counts as a visitor's.** While the
  page serves an admin, on either lane, it sends no pageview and no event, the
  Web Vitals included; the pageview `/debug/agent` is gone. (#12589)
- **A reload after no answer is a plain reload.** `/agent` is not behind
  Cloudflare Access, so the page no longer reloads by itself for it, and the
  link reads `reload` instead of `reload to sign in again`. (#12589)
- **The agent chat is one terminal-style window.** The chat at `/agent` and
  `/debug/agent` stands in one frame with the tab label `~/anyplot.ai/agent` on
  its top border, after the hero panel's construction, with dashed rules under
  the header row and above the composer. The opening, an ineligible pair and an
  error show in the same frame, and the admin fan-out's panel stays below it.
  This is the first slice of the approved v4 design. (#12587)
- **The header row speaks in plain words.** The spec's title is the link back,
  without the arrow; the library chip reads `seaborn ▾` and the language chip
  names the reply language in its own words, `Deutsch ▾`. The library's
  language and how the reply language was set stay in the accessible names,
  which start with the words on screen, so a voice command finds the chips.
  The how-to ⓘ moved from the `# chat` label, which is gone, into the row.
  (#12587)
- **One status line at the frame's foot names the step.** `>>> step 1 of 2 · …`
  replaces the step header above the chat and the step lines above the message
  box, and stays the plot button's description: what the button waits for, the
  plot that runs and its `.stop()`, what to check, or the confirmed data's
  shape. After a lost confirmation it reads `back to step 1 of 2 · …`. (#12587)
- **The experimental notice is one muted line above the chat.** On the public
  lane it reads `// experimental AI · answers can be wrong ⓘ`, right-aligned on
  a wide screen, without the green rule, and stays in place while the session
  opens. (#12587)
- **A lost confirmation is announced once, and a refusal reads in plain words.** After a change to the data or the
  bindings the user had confirmed, or when the server no longer held the confirmation, the thread showed a notice
  ("# data changed · check it, then plot the new data", "# bindings changed · check them, then .create_plot()",
  "# check the data again, then .create_plot()") right above the composer's step line, which said the same; the
  step line is now the one line (the data card's own header stays). A refusal is labelled in plain words
  ("can't fetch data", "outside this chat", "chat paused", ...) instead of "refusal · needs_data", with the code
  behind the label's ⓘ; the admin fan-out panel keeps "refused · needs_data" with the same plain label under it.
  (#12586)
- **The assistant's replies are shorter and never walk through the page.** In the agent chat, a reply
  is one or two short sentences with the counts that matter, four at most with a notice it must
  carry. It no longer tells the user to check the data panel or press `.create_plot()`, which the line
  above the message box already says, nor what the notes do not hold. It no longer counts the plot's
  labels the server checked, and a note the server made from a column with one value in every row
  reads `Currency: USD (the same in every row)` in the data card, which the reply states as a fact of
  the data rather than as the user's note. (#12576)
- **The result card's notes read in plain words.** One line per issue, such as `some labels overlap`,
  replaces the review's lines with their rubric ids, pixel counts and code; the lines in full stay
  behind the notes' ⓘ. (#12576)
- **A repair round reads as the normal course.** In the progress grid, a review that found things to
  fix keeps a dot and says `3 things to fix` in a neutral ink, where it showed a red `✗ review: 3
  findings`; a repair round says `fixing text size, layout`, and the shipped round's `~ 1 note left`
  points at the card's notes. A failed render or code check keeps its red ✗. (#12576)
- **The thread names the buttons the user pressed.** A plot turn shows as `.create_plot()`,
  `.start_over()` or `plot in plotly with your 3 decisions`, not as the action `.carry_plot()` the
  page sends, and the summary after a paste, which no button sends, shows no line. Inline code in a
  reply shows as code, without its backticks. (#12576)
- **The thread says the reply is on its way.** A plot's card arrives seconds before the reply to it;
  in that gap a line below the card reads `writing the reply` beside the loader, and the reply takes
  its place, starting where the line started. (#12576)
- **The line above the message box says how to stop a running plot.** While a plot runs it reads
  `# plotting… .stop() to cancel` in place of the step's line, which still invited the click that
  started the run. (#12576)
- **A series family's columns are chips in one row.** The `y` of line-multi,
  area-stacked and every other spec with a variadic family had one dropdown per
  series plus an empty one for the next, so eight series made nine rows. Now
  each bound column is a chip with a `×` that removes it, followed by `+ y ▾`, a
  menu of the columns left. Columns the role cannot take stay in the menu,
  greyed out with the reason. The row keeps its name and kinds, wraps at a
  phone's width under the role's name, and keeps the keyboard in the row after a
  change. The server still gets `y1` to `yn`. (#12580)
- **Every release runs the agent evals first.** `/release` gains a step before the release PR
  opens: the prep and scope evals always, and the matrix smoke when the window changed the plot
  pipeline. The results go into the PR body as "Agent evals", and the next release compares against
  them. No CI job runs these suites, because they call the real models. A regression on main
  surfaced on 2026-11-05 only because a sibling PR happened to run its eval; a release is now the
  fixed point where every prompt and model change of the window is measured together. (#12579)
- **A binding dropdown greys out the columns its role cannot take.** In the
  data panel of "Use with my data", a column whose type the role refuses
  stays listed with the reason, `Industry (text) · not numeric`, and cannot
  be picked, where picking it brought a red refusal and the dropdown snapped
  back. The page mirrors the server's type table, and a test keeps the two
  equal. (#12574)
- **An attachment that replaces the data says so before it is sent.** While
  the session holds data, the line above the message box reads
  `# the attached table replaces your data (22 rows, no .undo()) when you
  send it`, since a paste starts the data's versions anew. (#12574)
- **The agent chat shows a request id only where a report needs it.** An
  error line keeps its ` · ref <id>` for a fault of the server or the
  connection (a 5xx, no answer, a stream's error). A refusal (a 4xx), such
  as a binding the server refused, a paste the parser cannot read, or a
  limit, names its cause in the text and shows no id, which only puzzled
  visitors. (#12573)
- **The data card stands in the thread after its paste.** A sent attachment is the user's line in the
  agent chat's thread, as its chip named it (`▤ table · 4 lines · 46 B`), and the data card follows it,
  with the summary below. A later paste gets its line and a card of its own, and the card it replaced
  stays as a line with its shape (`# earlier data · 2 rows · 2 columns · replaced below`). A table read
  from text waits in a card at its paste: `.use()` makes it the data card, `.discard()` a
  `# table discarded` line. A change to the data, an undo, `.to_long()` and the table and sheet pickers
  update the card where it is. Once the data is confirmed, the header pinned above the thread leads to
  the card: `.show()` opens it at its place and scrolls there, `.hide()` goes back. (#12570)
- **The loader of a running turn keeps its place.** The thread's in-progress line (`working on your
  message`) is laid out as the progress timeline is, the loader first and the words beside it (on a phone
  below it), so when a typed change reaches its first pipeline step and the timeline takes over, the loader
  stays where it is. It jumped 232 px to the left and 3 px down before. (#12570)
- **The summary comes into view after a tall card.** The first reply after a data card scrolls into
  view as it arrives while the focus is in the message box, so on a phone it no longer lands below the
  fold. (#12570)
- **The server makes a paste's certain conversions for open roles.** On the
  summary turn of a paste (the summary action, or the note sent with it), the
  server applies the operations of every `certain` line of "Conversions for
  open roles" itself before the assistant's first call: a column of years
  read as dates, prices read as numbers, a column of ranges split into its two
  bounds, or the row numbers on an open axis. They land in one data version of
  their own, so one `.undo()` takes back exactly these conversions, and the
  original columns stay. The assistant names each in the summary with its count
  and the new column's name, and never repeats or drops one, also when the
  note asks to keep the column as it is: the original stays beside the new
  column, and the assistant says that `.undo()` takes it back. The conversions
  run behind the scope guard, so a refused note changes nothing. `uncertain`
  lines stay the assistant's one question, a `date_number` offer still waits
  for the user's request, and a later turn never makes a line by itself. The
  assistant used to make these lines with its own `prepare_data` call, and the
  prep eval's `en-note-rename-year-column` failed 3 of 3 runs: the date column
  was skipped, or made and dropped again. Now it passes 3 of 3, with the
  summary's row count and the conversion in every reply. (#12568)
- **The summary turn stays the summary after the assistant changes the
  data.** The session block's "pasted just now" line now holds for every model
  call of that turn. Before, the reply after the assistant's own `prepare_data`
  lost the line and answered the note without the summary. (#12568)
- **One chat field for everything.** The agent chat's message box takes the data now: a table pasted into it, or a
  file opened with `.open()` beside it, dropped anywhere on the chat or pasted as a file, waits above the text as an
  attachment with its name, its lines and its size, and Enter sends it. One line, code, prose, a formula or a
  request for data stays typed text, by rules the page and the server share as 41 test cases. The data card loses
  its text box, its counter, `.parse()`, `.open()`, `.replace()`, `.keep()` and its drop zone, and shows once there
  is data; a workbook's sheet picker reads the stored file again. A table over 1 MB or 20,050 lines turns the
  attachment red, and so does one the server refused, with the reason under it. While an attachment waits, the plot
  buttons wait too. (#12565)
- **The note typed with a paste is its first turn.** Text typed beside an attachment goes with it: once the data is
  stored, the assistant summarizes it in two sentences and acts on the note in the same reply ("nur 2024", "the
  decimal mark is a comma", a title for the first plot, a question about the data) instead of a summary first and
  the note after. A note the scope judge refused is followed by the summary, which skips the judge; when nothing
  was stored (a table read from text, a refusal), the note goes back into the box, and `.discard()` of a table read
  from text gives back what it came from: short pasted text into the box, a file or a longer text as the
  attachment. The scope judge reads the note alone; the paste's notes and file name reach the assistant beside it.
  (#12565)
- **The message box no longer cuts a long text.** Over 2,000 characters the counter turns red and nothing sends
  until it fits. Enter sends (also with Ctrl or ⌘), Shift+Enter is a new line, and an input method's composition
  keeps Enter for itself. A draft or an attachment not sent yet makes a reload ask first. (#12565)
- **The assistant sends the user to the message box.** Its prompt names the attachment and `.open()` in the
  composer, never the data card's box or `.parse()`; a small table typed as a message gets the answer that data
  comes as a paste of at least two rows or a file. (#12565)
- **Model routing moves from `CLAUDE.md` to `agentic/docs/agent-operations.md`.**
  The subagent model tiers, the Gemini lane, the Gemini check before a code PR
  opens, and the second-opinion rule now live in the new document; `CLAUDE.md`
  keeps one rule that points to it and makes it binding, the two `agy`
  prohibitions, and the delegate-brief duties. No rule changes meaning, and
  `tests/unit/test_agent_instructions.py` pins the moved rules in their new place
  (#12566).
- **Comments say why, not who.** A new rule in `CLAUDE.md` and
  `.github/copilot-instructions.md`: provenance (who asked, which review found
  it, the date) goes into the commit or the PR, and code migrates on touch.
  Comments under `api/` and `app/src/` drop their reviewer names, owner-decision
  notes, and dates that only recorded when something was decided or found; dates
  that bound old data or date a measurement stay (#12566).
- **The map's ForceGraph2D instance is typed.** `ForceGraphHandle` names the
  methods the map calls instead of `any`, which removes the last two
  `eslint-disable` comments in `app/src` (#12566).
- **Two series of a family trade columns instead of one dropping out.** In
  the data panel, picking for one member of a numbered series family
  (`y1`, `y2`, ...) the column another member holds now swaps the two:
  with `y1` on Sales and `y2` on Cost, setting `y2` to Sales puts `y1` on
  Cost, and both series stay in the plot. Until now the other member was
  cleared and the family closed up, so Cost left the plot. A member without
  a column, the next member's `— add a column —`, has nothing to trade, so
  the column still moves there. (#12567)
- **One column can play several roles in the data step.** Some plots need the
  same variable twice: the y and the size of a bubble, the value and the colour
  of a bar, a value and its label, a treemap's size and colour. A column you
  bind by hand in the data panel, or that the assistant binds on your request,
  now keeps every role it serves: picking it for a second role no longer
  clears the first, and the binding check accepts it with no warning. The
  adapter prompt tells the plot code to select such a column once and use it
  for both roles, since a table with the same column twice breaks pandas. The
  default bindings and the automatic conversions still give each column one
  role, and inside a numbered series family (`y1`, `y2`, ...) a column stays
  once, because the same series twice is never meant. (#12564)
- **The prep eval counts a closing invitation as a reply miss.** A reply whose
  last sentence or clause asks the user to choose ("Choose …", "Pick one …",
  "tell me which …", "Wähle …") misses on the same terms as a closing
  question, and an open role the session block offered a date column for no
  longer excuses either. On the earlier wording 2 of 5 summary replies of the
  owner's case closed so; on the final one, 0 of 6. (#12558)
- **One click from checked data to the plot.** `.confirm()` is gone: from the moment data is stored,
  `.create_plot()` stands at the composer's right end as the filled button, confirms the data and its bindings as
  the card shows them and starts the plot in the same click, with the typed text as the plot's request when the
  box holds any. A refused confirmation starts nothing and shows under the composer. The line above the message
  box says what the click still waits for: a table read from text to decide on, or a column for a required role.
  After a change to confirmed data `.create_plot()` is filled again, also when the library already has a plot.
  `.send()` shows only while the box holds text, and Enter never confirms. The admin's `.plot_all()` and the plot
  after a library switch confirm the same way. At phone width the buttons wrap below the box and stay at its right
  end. The assistant's prompt and the session block send the user to `.create_plot()` instead of `.confirm()`.
  (#12557)
- **A pasted formula or code goes to the chat by itself.** The data box no longer offers `.send()` when the server
  answers `422 formula` or `422 code`: the page sends the text to the chat as your message at once, as it already
  did for a request for data, and empties the box. Code over the chat's 2,000 characters stays in the box with a
  line that asks to shorten it. `agent_data_parsed` reports such pastes as `formula` or `code` instead of `error`.
  (#12557)
- **The site's loader marks the chat's waits.** The three-dot `LoaderSpinner` of the plots gallery, in a new inline
  size, replaces the pulsing ellipsis while a session opens, in the thread's in-progress line, beside a plot run's
  progress and over the data box while a file is read or the data is parsed, one moving indicator per wait: the
  lines that only say what waits lost their ellipsis, and a question or a summary waiting in the queue shows the
  in-progress line and the queue counter without the progress grid. `.example_data()` steps aside while its turn
  runs, keeping its room, so "making example data" shows once, in the thread. The loader, in the gallery too, drops
  the ochre: a resting pair in the theme's warm gray of muted text and a runner that turns green while it crosses
  them. Its dots stand still under reduced motion, the runner green, and each size has keyframes of its own, so two
  sizes on one page no longer share one animation. (#12557)
- **A network's share of the agent dataset store is 32 MiB.** `AGENT_IP_DATASET_BYTES`
  falls from 64 to 32 MiB of the store's 256 MiB, so eight networks, not four, are
  needed to fill it for everyone else (#12555).
- **The chat header's columns ⓘ lists the spec's roles.** Opening a session now answers the spec's data roles
  (`POST /sessions` gains `roles`), and the ⓘ after the title names them as the data card's dropdowns do, with
  their kinds and whether a role is optional, takes one column per series or is computed by the plot; the spec's
  `data` bullets remain the fallback. (#12553)
- **The data box names code instead of example data.** Its placeholder now reads "or code that makes data (python,
  javascript, …)" and "or a formula", since `.example_data()` took over example data, and the card's ⓘ says that
  you can paste code or a formula that makes data too, up to 2,000 characters. (#12553)
- **The public chat's notice says less in its line and more behind its ⓘ.** The line is now
  `experimental AI · answers can be wrong`; the ⓘ adds that the chat and the data live only in server memory and are
  deleted after an hour idle, that nothing is saved unless you send feedback, and that Claude runs via Google Cloud
  Vertex AI in the EU and is not trained on what you send, as the legal page says. (#12553)
- **The triage rules of a case live in `core`.** `core.agent_cases.triage_updates`
  holds what `PATCH /debug/agent/cases/{id}` checks (tags, the promotion's
  plot, data and expected outcome), and the route and the skill's script both
  call it, so the two never drift apart. The route answers as before. (#12551)
- **`CHANGELOG.md` opens with its format line, not the process.** The thirty lines on fragments,
  the release cut, the GitHub release and the exempt classes moved into `changelog.d/README.md`,
  rule for rule, under task headings; the changelog keeps the format, the versioning line and a
  link there (#12547).
- **The agent chat's data panel is split into six files.** `DataPanel.tsx` keeps the panel's state and layout;
  the file intake moves to the `useFileIntake.ts` hook, the card's content to `DataCard.tsx` and its building
  blocks to `dataCardParts.tsx`, the sticky summary header to `PinnedData.tsx`, and the count formatter they share
  to `countOf.ts`. Behavior and rendered output
  are unchanged: a jsdom snapshot diff of 43 panel states against the base showed 0 differing lines. (#12550)
- **The chat's reply-language line and remembered list are one short line
  each.** `# reply language: en` and `# remembered · 2 decisions` keep only
  what they state; where the language came from, that a plot keeps its own,
  and what the remembered decisions do stand behind an ⓘ, as the experimental
  notice does it (#12549).
- **The site's `.use_my_data()` entries open the public chat for admins too.**
  While the public lane is open, an admin lands on `/agent` like every visitor,
  so the chat is tested as visitors see and use it; `/debug/agent` stays the
  admin's page for `all` and `.save()`, and the entries' target only while the
  public lane is closed (#12549).
- **Dependencies:** 17 Dependabot PRs. `tree-sitter-language-pack` 0.13.0 →
  1.24.0, a major version with the code change in the same PR (#12943, see its
  own entry), then 1.24.1 (#13032). `anthropic` 1.15.0 → 2.3.0, a major version
  (#12535), and on to 2.6.0 in the python-minor group (#12940), which also
  takes `pandas` 3.1.1, `pyarrow` 26.0.1, `fastmcp` 4.1.6, `pydantic` 2.14.3,
  `ruff` 0.17.4, `cachetools` and `python-calamine`. The earlier python-minor
  group (#12532) takes `fastapi` 0.141.1 → 0.162.0, `pytest` 9.2.0, `mypy`
  2.4.1, `selenium` 4.52.0, `pg8000`, `pydantic-settings` and `pandas-stubs`.
  `types-pyyaml` twice (#12534, #12942) and `pytest-asyncio` 1.4.1.post1
  (#12941). In `app/` `jsdom` 30.1.3 → 31.0.0, a major version (#12937),
  `react-router-dom` 7.18.5 (#12529), and the npm-minor group (#12554:
  `eslint` 10.14.0 and `globals`; #12936: `vitest` 5.1.0 with its coverage
  plugin). For the JavaScript renderers `@mui/x-charts` 9.16.0 → 9.17.0
  (#12531), `d3` 7.9.0 → 7.9.2 (#12935) and `playwright` 1.64.1 → 1.65.0
  (#12934); and the actions group (#12533, #12938: `claude-code-action`
  1.0.269, CodeQL 4.39.3).

### Removed

- **`og_image_view` no longer goes to Plausible.** The event carried the
  fetcher's address and user agent to Plausible and measured little: Plausible
  drops every user agent it knows as a bot, so of 402 events in 28 days, 371
  had the platform `unknown` and 31 were WhatsApp, and tests, local requests,
  and fetches that ended in a 404 all sent real events. The code that picked
  the visitor's address for it (`visitor_ip`) is gone with it. (#13055)
- **The nginx user-agent entry for the Windows 10 Chrome crawler farm.** The `$is_headless_client` entry
  from #12860 matched Windows 10 Chrome 100 to 139 and answered those clients' Plausible events with an
  empty `202`. The farm moved to Chrome 148 to 150 on Windows and macOS the same day, so the entry caught
  14 events all day, while it kept dropping the events of about 1.8 % of real visits, people on a pinned
  old Chrome. The Cloudflare Managed Challenge for four hosting-network ASNs (Tencent, Leaseweb, Huawei
  Cloud) is the one mechanism against the farm now, and a person it catches sees the challenge and can
  pass it; `infra/cloudflare/README.md` records it as applied. `app/nginx.conf` holds no entry that
  matches a browser's user agent, and a unit test fails if one comes back. (#13033)
- **The Plausible bot site `bots.anyplot.ai`.** `bot_fetch`, `asset_fetch` and
  the machine side of `og_image_view` are no longer sent: the site saw about
  1.7 % of real crawler reads and was mostly a scanner's spoofed user agents.
  The machine-read lines replace it. (#12962)
- **Core Web Vitals no longer go to Plausible.** The site stops sending `LCP`, `CLS`, `INP`, `FCP` and
  `TTFB` as custom events, and the `web-vitals` dependency goes with them. They were 44 % of the billable
  events (17,044 of 38,818 in 28 days), `FCP` and `TTFB` had no dashboard goal, and every one of them
  un-bounced its visit: visits with a vitals event bounced at 0 %, visits without at 88 %, so the
  dashboard's bounce rate of about 5 % was an artifact and rises to a realistic value from here. Core Web
  Vitals come from PageSpeed Insights when needed, and the privacy text on `/legal` no longer lists them.
  (#12860)
- **The automatic `Form: Submission` goal is off.** `formSubmissions: false` in the Plausible init: the
  agent chat's message box is a form, so the goal counted chat messages that the chat's own events
  already count, 144 of its 146 events the admin's own. (#12860)
- **The public `GET /agent/session/bundle`.** No page has called it since the public
  chat dropped `.save()`; the admin lane's `GET /debug/agent/sessions/{sid}/bundle`
  stays (#12555).

### Fixed

- **A render hash of other code goes before new renders arrive.**
  impl-generate and impl-repair remove an earlier `render.sha256` before they
  upload the renders and write the new one last, with three attempts. They
  used to remove it only after a failed write, and when that removal failed
  too, the old hash stayed beside the new renders. (#13045)
- **One failed read of the render hash no longer reads as `unreadable`.**
  impl-review downloads `render.sha256` with three attempts, as it downloads
  the renders. (#13045)
- **Plausible's scroll depth is measured against the page it belongs to.**
  Plausible's script closes the page being left when the next pageview
  arrives, and divides the deepest scroll offset by the document height it
  last observed. The late pageview arrived after the next page had rendered,
  so the depth of the page being left was divided by the next page's height:
  too low before a longer page, too high before a shorter one. Measured with
  the live script on the same clicks, a landing page left at 47 % was sent as
  30 %, an implementation page left at 63 % as 92 %, and the gallery after
  12,000 px as 1,176 %; all three are now sent as they are. The pageview goes
  out before the browser lays the next page out, and after the scroll reset,
  so the new page starts at the top. On Back and forward, where the browser
  restores the offset itself and Chrome does so only afterwards, the pageview
  is sent from the top and the offset put back before anything is painted.
  (#13046)
- **Back to the gallery starts from the top before the gallery restores its
  own offset.** The gallery turns the browser's scroll restoration off, so on
  Back the offset of the page being left stood until the gallery's restore, or
  for good when it had none to restore. (#13046)
- **A repair can no longer send unchanged code back to review.** impl-repair
  fails unless its push changed the implementation file and the workspace holds
  the pushed file, and it fails without both theme renders, where it used to
  exit 0 and leave the previous renders under the repaired code. The crash
  comment names the gate that failed. (#13034)
- **A generation whose code was never pushed fails.** impl-generate used to
  check out `origin/main` when the branch was missing, which put a
  regeneration's renders under the live implementation. It now also fails when
  the implementation file on the pushed branch isn't the file in the
  workspace, which is the case when an earlier run left its branch behind.
  (#13034)
- **The manual re-render script promotes only the renders.**
  `scripts/migrate_render_and_upload.py` copied everything in staging to
  production; it now copies the `plot-*` objects, as impl-merge does, so a
  staged `render.sha256` or `adapt/` record never reaches production.
  (#13034)
- **`regen_gate.py sanitize-source` keeps line endings.** It used to rewrite
  CRLF as LF, so a CRLF file was committed in a form other than the one
  rendered. (#13034)
- **A change request in words no longer replaces the data.** Since #13019, a
  short request with two "label number" parts, such as `x bis 2030, y bis 60`
  or `Titel 2026, Schrift 14`, routed as a list of pairs. It replaced the
  user's table with two `label`/`value` rows, and there is no `.undo()` back.
  Text with a word of a plot wish (`bis`, `max`, `Titel`, `Linie`, `Schrift`,
  `ticks` and more) is now never a pair list, on the page and in the server's
  reader, which share one word list (`wishWords.json`, pinned by a test). An
  axis letter alone is no label either. While the session holds data, a list
  needs three pairs; on a fresh page two still count (`Apples 7, Pears 12`).
  A table typed into the box over data now gets the same "replaces your data
  (N rows, no .undo())" line as an attachment before it goes. (#13035)
- **A web table copied one cell per line, and an inline list such as
  `a:7,b:12,c:5`, are data now.** Both are shapes from the owner's live session.
  The page sent them to the chat as a message, the plot button stayed grey,
  and the assistant answered that it cannot read data from a message. The page
  now routes them as data (`routeInput.ts`, rules 12 and 13), and the server's
  parser reads them by code (`layouts.py`, source formats `cell_lines` and
  `pair_list`). The parser takes the header from a line split at ` · `, leaves
  out a label block below the rows, keeps a range such as `62–100` as one text
  cell, and adds a warning that says how it read the text. Short text of up to
  2,000 characters that is mostly values goes to the server's transcriber,
  which offers its table for `.use()`. Longer text counts only in a format the
  parser knows: the transcriber now reads at most 2,000 characters (4,000
  before), so long free text never reaches a model as data. A ratio, a time, a
  URL, code and prose stay messages. (#13019)
- **The plot button takes pasted data whenever Enter would.** One pure rule
  (`plotClick` in `plotChain.ts`) now decides both whether the button is
  active and what its click does, so the two can no longer disagree. With the
  admin's `all` pressed, a pasted table left `.plot_all()` inert and only Enter
  read it. Now the one click reads the table and opens the fan-out once it
  reads clean. A table typed over stored data is read first too, never plotted
  as the old data's fan-out or sent as a plot request. A table in the message
  box goes by the dataset's own limits, so a long one goes as data with Enter
  and with the button. (#13019)
- **No more claims that BigQuery's result cache answers repeated telemetry
  queries.** The linked `_AllLogs` view changes with every line, so the
  process caches are the only caches; `api/agent_usage.py` and
  `docs/reference/agent-telemetry.md` say so now. The trigger step of both
  telemetry setups uses the export, edit and import route, because
  `gcloud builds triggers update github` refuses the second-generation
  `deploy-api` trigger. (#13015)
- **Workflow label checks cannot lose a match to SIGPIPE.** The 15 checks of the form `echo "$LABELS" | grep -q`
  in impl-review, impl-merge, sync-labels, report-validate and spec-create now hand grep the labels as a
  here-string. Bash's `echo` writes a multi-line value one line per write, so `grep -q` could match, exit and
  leave `echo` to die on a closed pipe; under `pipefail`, the shell the workflow tests use, the check then read
  as false, and the verdict step failed now and then with "neither ai-approved nor ai-rejected". Live runs use
  `bash -e` and were unaffected. A test now refuses the pattern in every workflow file (#13012).
- **The regen gate's record and summary and the verdict step's scratch files live in `$RUNNER_TEMP`.** Under
  fixed `/tmp` paths, which every workflow test on a machine shares, a gate summary left by one test was posted
  by the next; each test now gets a `$RUNNER_TEMP` of its own. Files the reviewer reads stay in `/tmp` (#13012).
- **The feedback case's turn record knows the newer guard verdicts.** The record's closed verdict sets predated the served-library lift and the language offer, so those guard lines read `other` and two unit tests failed on `main`. (#12991)
- **The renderer's replay tests wait for the join instead of guessing its time.** The page test gave the first build
  a fixed 50 ms to start and never waited for the replay to join it. A page is not kept for replays, so on a loaded
  machine a late replay built the page a second time and the test failed. Both replay tests, the page's and the
  render's, now wait until the build runs and the service logs the replay's join of the build in flight. (#12977)
- **The chat recognises a library however you write its name.** "erstell das
  bitte mal in d3" and "d3.js" got the pointer to the catalogue as another
  library, and only "D3.js" switched the plot. A code check now lets every
  request through that names only libraries the chat serves, in any case, with
  or without `.js` or `.jl`, with any separator, and in the well-known short
  forms (`ggplot`, `mpl`, `mui x`, `CairoMakie`, `apache echarts`); the library
  switch reads the name the same way. One table in `core/library_names.py`
  holds the names. A request for a tool outside the catalogue (Vega-Lite,
  Excel, Plots.jl) still gets the pointer, and an attack or a data request that
  names a library keeps its refusal. In the scope eval the judge itself refused
  4 of 12 such requests, all of which now go through. (#12855)
- **The site's preview images keep a plot's background instead of turning it black.** The smaller PNG and WebP variants dropped the alpha channel, so a render that paints only its panel showed black bars beside the plot; transparent pixels now take the theme's card surface. (#12863)
- **A data change whose result the server refused still counts as the turn's answer.** The empty-reply check read
  only results that passed the size and key checks, so an empty reply after such a change ended as "no reply" although
  the data had changed. (#12853)
- **A crawler farm no longer counts as visitors.** Since 2026-11-03 a farm has loaded about 17 spec pages
  an hour from a new exit IP on almost every request, with plain Windows 10 Chrome 103 to 138 user
  agents, so the nginx analytics shield caught 6 of 16,195 of its event posts in 44 hours, and its
  residential share made up 675 of 1,451 dashboard visitors in 7 days. One more `$is_headless_client`
  entry matches exactly that shape (Windows 10, Chrome 100 to 139, an anchored `Safari/537.3x` tail),
  which keeps Edge, Opera, Windows 7/8.1 and Chrome 140+ out and costs about 2 % of real visits, those on
  a pinned old Chrome. A unit test holds the map against the farm's user agents and current browsers, and
  `docs/reference/plausible.md` carries the review rule for the version ceiling. (#12860)
- **The catalogue corpus tests hold rules, not the counts of one day.** The corpus tests of the ggplot2, Makie,
  plotly and bokeh profiles, the Python theme-token check and the tree-sitter file gates pinned the catalogue as
  it stood between 2026-10-10 and 2026-10-31: file counts (325, 1,617), split counts (4 clean, 306 coupled, 15
  blocked), rewrite counts (34 dpi rewrites, 122 renamed keywords), lists of flagged files and of non-token theme
  conditionals. Two regenerations on 2026-11-09 broke four of them: flowmap-origin-destination's ggplot2 file
  (#12862) dropped the `maps` package, and map-marker-clustered's bokeh file (#12859) saves `curdoc()` and
  screenshots the figure's element. About 140 more regenerations were due the same night. Main never ran these
  tests, because a merge that changes only implementation files skips pytest, so every Python PR inherited the
  failure (#12877). The tests now check each file:
  - a file is blocked exactly when its spec is a map spec, the SECURITY profile flags it or its structure fails,
    and the sweeps' counts, eligible shares and Markdown rows follow from those files;
  - the SECURITY profiles flag no file or rule beyond the known ones, and every import of an unavailable
    package, every `<<-`, every URL string and every call of a denied name is a finding;
  - each detected convention (theme tokens, markers, column constants, the palette, the protected save) and
    each `data-block` and `deprecated-api` hint matches a plain reading of the file's text;
  - the normalisers make only their known rewrites, each where the text calls for it, and leave no catalogue
    header or title behind;
  - every plotly and bokeh file ends on the pinned figure save or carries the normaliser's note on why not, and a
    bokeh file left alone exports through a browser screenshot of its own;
  - every theme conditional built only from literals, `THEME` and the file's tokens is a token;
  - the parse gates read every merged implementation, the specs whose metadata names one.
- **The audit skill's candidate selector reads every stored review.** Some reviews keep a plain number beside the checklist's categories, and the selector stopped on the first one instead of skipping it. (#12827)
- **The prep eval runs again.** Scoring a case by the version its turn starts from had failed on every run since the server began numbering data versions; the eval now looks the version up the way the agent does. (#12823)
- **A merge whose renders never reach production now fails instead of
  passing.** `impl-merge.yml` promoted #12800 (waterfall-basic, MUI X)
  with nothing copied: the copy failed with its error hidden, the step
  deleted staging anyway and reported "Promoted images to production",
  so the site showed the previous code's images under the new review.
  The promotion now lists staging first, fails when either theme render
  is missing and the PR changed its implementation, retries a failed
  listing or copy and then fails with staging kept, and names the number
  of files it copied. A new step comments the fixing command on the
  merged PR: a re-render of the merged file in adopt mode, a forced
  regeneration for R and Julia, or a re-dispatch of `impl-merge.yml`
  when only the transfer failed. The step no longer sets object ACLs,
  which the bucket's uniform bucket-level access rejects on every call.
  (#12819)
- **Prices no longer bind as a MACD line or an RSI, and raw measurements no longer as control-chart
  summaries.** A new name-only role class binds `macd`, `rsi` and the sample means, ranges, limits and
  center line of `spc-xbar-r` only to a column whose name holds them (`MACD_12_26_9`, `RSI 14`, `X-bar`,
  `UCL`), in the default bindings, in the bindings filled after a data change and in the columns a
  conversion makes. Before, a price table drew its opening prices as the MACD line or as an RSI on a 0 to
  100 axis, and `Sample, X1, ..., X5` drew the first measurement as the sample mean and the next ones as
  the range and the limits, each with complete bindings and no warning. Now the role stays missing and the
  page asks for its column (#12612).
- **Search after Back finds spec titles again.** Back to `/plots` restores the gallery from the
  layout's saved state without a fetch, and that state did not hold the spec titles. The search then
  matched spec IDs only: `bar chart`, `pie chart` and `line chart` found nothing, and the spec
  tooltips in the dropdown were empty. (#12608)
- **An empty search inside the filters says why.** When a search finds nothing because the active
  filters hide every match, the dropdown offers `.search_all()` under `results.empty()`, with the
  number of matches in all plots. It removes the filters and keeps the query; a bare Enter never
  picks it. (#12608)
- **The JavaScript catalogue tests hold rules, not the counts of one day.** Five corpus tests pinned the
  catalogue as it stood on 2026-10-30 and 2026-10-31: the readiness split (93 clean MUI X files), the
  detected conventions (1,602 `t` tokens, 1,344 `// Data` markers), the normaliser's rewrites (893 directives
  written out), the 8 files the SECURITY profile flags and which eval specs' MUI X files are clean. Every MUI X
  9 regeneration broke them. Main never
  ran them, because a merge that changes only implementation files skips pytest, so every Python PR inherited
  the failure (#12647). The tests now check each file:
  - the blocked files are exactly the map specs and the known SECURITY cases that still hold their reason;
  - the SECURITY profile flags no file or rule beyond the known ones, and every URL string and every overlong
    quoted string of the code is a finding;
  - a clean file has the adaptable-code layout, and the `data-block` hint appears exactly when that layout is
    incomplete;
  - `deprecated-api` appears only in MUI X 7 files, and in every file that imports `ChartContainer`;
  - each detected convention matches a plain reading of the file's text and the harness's own orientation
    pattern;
  - the normaliser makes only its known rewrites.

  The eval matrix's MUI X 7 preflight tests build their own MUI X 7 file instead of reading `scatter-basic`'s,
  which the MUI X 9 pass rewrote.
- **A pair the regen gate kept on a regression or a technical failure comes
  back after the attempt window.** The pair-mode picker aged a kept pair from
  its keep, so after the 30 days it queued behind about 4,700 pairs, years at
  the nightly rate. That parked live implementations the regeneration had
  clearly beaten except for one regression (funnel-basic/bokeh kept at 83
  against 69). A `regen:kept` PR whose gate record has the code `regression`,
  or a technical one such as `canvas_failed` or `script_crashed`, now holds its
  pair for the window and then lets it return at its age from before the keep,
  usually its metadata `updated`. The second such keep in a row ages the pair
  like a plain keep, so a pair that keeps failing doesn't come back every 30
  days. Every other keep code still ages the pair. The picker reads the records
  from the workflow's own verdict comments in one extra listing; when that
  listing fails, every keep ages its pair as before. (#12605)
- **The agent chat reads headers in comment lines and under an export's metadata.** A
  data file that opens with `#`, `%` or `//` comment lines keeps them as notes, and when
  its table has no header line, the last one or two comment lines name the columns,
  placed by the columns' character ranges, so a monthly series whose header wraps over
  two `#` lines reads `decimal date` and `monthly average` instead of `#`, `date`,
  `alized`. A statistics export's header of years under key-value metadata is the header
  again, a key-value line no longer joins a header, a `:` cell is missing in a number
  column, and a column of flags (`p`, `e`, `ep`) beside a year stays as `<year> flag` with a
  warning that counts the flags. A title above a header of years no longer turns the
  table into one column of text. (#12602)
- **A statistics export's legend below the table stays out of the rows.** A
  spreadsheet export pads every line to the table's width, so the legend under the
  table (`:,not available`, `p,provisional`) read as rows without values and turned a
  year column into text. Such rows now extend the table only up to a blank line; the
  legend after it is kept as notes below the table, so the assistant can say what `:`
  and the flags mean. (#12602)
- **A pasted Markdown table keeps its column names.** The row of dashes under a Markdown
  table's header (`|---|:---:|`), as chat assistants write it, became part of the names
  (`Month -------`, `:------`) or a row of a column of names. It is now left out as
  layout when it stands directly under the header; a row of dashes further down the
  table stays a row. (#12602)
- **No row numbers nobody asked for after a data change.** Once the
  assistant has changed the data in a turn, the session block no longer
  lists the conversion candidates for an open role for the rest of that
  turn. Recomputed on the new version, the row-number fallback reappeared
  as a certain line, and a chain of a drop, an aggregate and a sort gained a
  `row_number` column in about half the prep-eval runs. The conversions the
  server made stay listed, and the next turn lists the candidates again.
  (#12599)
- **A data change no longer fills a role that was open before it.** The
  rule from the plot-button fix that has the assistant bind a required role
  itself now applies only to a role the turn's own data change left open. A
  role that was open before the turn follows the conversion lines again, so
  "drop the Total row" no longer adds a row-number column for an empty axis.
  The prep eval caught it: from that fix on, 7 of 8 runs of the drop cases
  added a `row_number`, against 0 of 9 before it. (#12595)
- **The admin fan-out starts one plot per library.** A render between a
  library's finished plot and the panel's freeing of its place could start a
  second plot there, which held the card at `adapting…`; a run now starts once
  per grant of a place. This was the flaky `FanOut` test in CI. (#12594)
- **A click on the plot button plots.** In two persona tests the user pressed
  the plot button right after a data change and got "not confirmed yet": the
  assistant had bound the new derived column inside the plot turn, which voided
  the click's confirmation. A turn of `.create_plot()` (also "plot the new data"
  and `.start_over()`), the switch offer's carry and `.plot_all()` now plots the
  data and bindings the click confirmed: the agents service refuses every tool
  that would change something in it, and the assistant plots all the same. A
  column you ask to have plotted is bound in the data turn that makes it, so the
  data panel shows it before the click, and the assistant no longer asks you to
  bind a column it can bind itself. (#12593)
- **A note sent with a re-paste is read as the table's note.** The assistant
  answered it with the rule for a table typed into the message ("I can't read
  data from the message itself"), although the table had arrived as the
  message's attachment. The session facts now say that the table came in as an
  attachment and is stored. (#12593)
- **A long reply is shortened, never refused.** A reply of the assistant over
  1,200 characters became the fixed "only this plot and your data" refusal
  unless the turn drew a plot, so an on-topic summary of a pasted bank export
  and an on-topic answer about the user's data came back refused in the persona
  tests. The output guard now asks the assistant once for a shorter reply, the
  way the reply-language check asks again, and sends that one or the reply cut
  at 1,200 characters. (#12590)
- **A turn without a reply says so.** When the assistant's final answer held no
  text, the turn sent nothing but its end, and a paste with a note got no reply
  at all while the paste counted as summarized. The service now asks once more;
  a second empty answer, or a reply the output sanitiser empties, ends the turn
  with the new `error` code `no_reply`, which the chat shows as the turn, and
  the paste stays unsummarized for the next message. (#12590)
- **A note typed with a paste is read beside its table.** The scope judge saw
  such a note alone and refused a question about the pasted table as general
  advice. It now gets the plot's title and the table's column names (never a
  cell) with the note, and an off-topic or data-fetch verdict on a paste's note
  goes on to the assistant, which reads the note beside the table; off-topic
  ones at most five times per user and day (`AGENT_PASTE_NOTE_RESCUES`). An
  attack is refused as before, and a request for another library still gets
  its pointer to the catalogue. (#12590)
- **Indicator lines the plot can compute no longer take a price column.** The
  SMAs of `indicator-sma`, the EMAs of `indicator-ema` and the Ichimoku lines
  were required roles, so a stock table bound `Open`, `High` and `Low` as the
  three moving averages and the chat had nothing left to compute. They are now
  computed roles like the Bollinger bands: bound when a column clearly holds
  one (`SMA 50`, `Long MA`, `EMA 12`, `Tenkan-sen`, `MACD Signal`), otherwise
  computed by the plot code from the close or the high and low. The same
  holds for every catalogue role with a fixed formula over the spec's other
  roles: the MACD signal line and histogram, the ideal burndown line, a
  climograph's annual mean and total, the total error of a bias-variance
  curve, chain-ladder development factors, Weibull plotting positions, a SHAP
  waterfall's prediction and a decision tree's rollback. A test audits the
  role wording of every spec, so a new role worded as a formula fails until it
  is listed or named as data with the reason. An EMA or weighted average is
  no longer read as a simple moving average. (#12588)
- **A kept plot wish survives its own turn and the user's back-and-forth.**
  In "Use with my data", a wish kept before the data is confirmed ("top 10")
  is now judged against the bindings when the plot runs, not at every
  binding write, so unbinding and binding the same column on the way no
  longer drops it. The turn that keeps a wish holds it for the bindings and
  data it ends with, whatever order the assistant kept, bound and changed
  them in. A wish written for a column the user has since rebound is still
  dropped, as before. (#12585)
- **The assistant describes the plot by the columns it drew.** The plot
  result tells the assistant which columns each role took and whether a kept
  wish was used or dropped. It stops calling a plot of `Stock` unfit for an
  earlier "distribution of the prices" after the user rebound the values by
  hand, and stops naming the old binding. (#12585)
- **The plot is checked only for texts the user wrote.** A title or number
  format the plot must show has to stand, as a whole, in the user's own
  words: the message of that turn or the notes pasted with the data (case,
  spacing, quote marks and the kind of dash aside). On the page's
  `.create_plot()` and "plot in …" buttons the assistant can no longer
  re-send a request from an earlier turn; the kept wish and the plot memory
  carry the user's words. (#12585)
- **The plot memory holds each decision once.** A decision that differs only
  in case, spacing or a closing punctuation mark is the same one, and the
  assistant leaves a listed decision out in any wording, passing a change
  with the entry it replaces. (#12585)
- **A request to read a column as numbers converts that column.** When the
  session block lists a conversion for an open role on the column the user
  names ("read Anteil as numbers"), the assistant now reads the column itself
  as numbers or dates, instead of copying the line's new column beside it. The
  new column is only for a conversion nobody asked for, such as the ones the
  server makes on a paste. A reading that guesses (the day and month order, the
  century, the decimal mark) still gets its one question first, and a date
  column's offer stays a `date_number`. A column read in place fills the open
  role that waits for it, exactly as the named conversion did, and never takes
  a role that is already bound. In the prep eval, `de-percent-not-count` and
  `en-percent-unit-mixed` went from 1 of 10 runs on `main` to 10 of 10, and
  the full set scored 83 of 85. (#12582)
- **A note sent with a file is never refused as a request for data.** The scope judge sees the note alone, so
  "unemployment rate per country" with a Eurostat file read as a request to fetch figures and got the data
  refusal in red. A `needs_data` verdict on the note sent with a paste now goes on as in scope, and the root's
  instructions say that such a note never gets the data refusal. A refused note's summary now runs too: the page
  read the note's ended turn as still running and never sent it. (#12578)
- **A table typed into the message box is read as data.** Only a paste was routed, so a CSV table typed by hand
  went out as a message the assistant cannot read data from. Enter now routes the box's own text like a paste:
  a table goes to the dataset route at once, and × on a refused one puts it back into the box. (#12578)
- **One quiet line after a data change, and the button says what it does.** A data change followed by a plot the
  server refused showed the same instruction four times, once in red with the raw code `data_unconfirmed`. The
  refused plot adds no row now, the data change names itself in one notice ("data changed · check it, then plot
  the new data"), the plot button reads "plot the new data", and the root no longer calls the plot in the turn of
  its own data change or repeats the instruction in its reply. (#12578)
- **The data refusals name the message box and `.open()`.** The `needs_data` and `unsupported_content` refusals
  pointed to the data panel's field, which the one message box replaced; all 11 languages now name the message
  box and `.open()`. (#12578)
- **A summary or a question no longer shows its queue position after the wait.**
  A turn without pipeline steps kept its `queue 1/2` badge until the reply,
  because nothing told the page the wait was over. The agents service now sends
  `status{step:"started"}` once, when a run that waited takes its slot. The API
  passes it on both lanes, and a turn read again after a cut replays it. The
  page clears the badge on it. A plot run that leaves the queue before its first
  step shows `starting…` in its progress grid again. (#12577)
- **A web table with grouped columns arrives whole.** A table copied from a
  web page whose header spans two rows (`Density` over `/km2` and `/mi2`)
  is read from the clipboard's HTML with its spans expanded, so the parser
  joins the two header lines into `Density /km2` instead of refusing the
  copy. Only the cells' text is kept, and the copied page is never run.
  (#12574)
- **An id no longer labels the bars, and a founding year is no longer the
  measure.** The default bindings of "Use with my data" rank a text column
  of record ids (every value distinct, named like `Organization Id`, `UUID`
  or `EAN`) after every other text column for a category or label, and read
  a year named for an event of each row (`Founded`, `Year built`, `Baujahr`)
  as no measure and no time key. A table of organizations now binds
  `Name` and `Number of employees` to a bar chart, where it bound
  `Organization Id` and `Founded`. A lone id column still labels, and
  codes such as `iso3` keep their rank. (#12571)
- **A header in two lines is joined or named, never misread.** A grouped
  header copied from a spreadsheet or an expanded web table (`Density` over
  `/km2` and `/mi2`) becomes one name per column, `Density /km2`, with a
  warning. A browser's text copy that lost the spans is refused with that
  cause instead of a hint about quotes that did not apply, and a header
  shorter than rows that all agree says so. (#12571)
- **A replacing paste keeps the plot's axes.** New data that replaces the
  old carries each binding to the new column of the same name or meaning
  (`Land area km2` to `Area km2`), so `x` stays the area instead of
  flipping to the first number column. The other roles get the defaults.
  (#12571)
- **A result card's image actions stay off the plot on a phone.** Below 600 px
  the copy, download and open icons move from the image's top right corner,
  where the plot's title stands, into the card's header row. (#12575)
- **The site's feedback button no longer covers the agent chat.** The chat has
  a feedback row on every result and one for a session without a plot. On a
  phone the site's button covered `.send()`, `.open()` and the replies' right
  edge, so the agent chat no longer shows it. (#12575)
- **One plot button after a library switch with nothing to carry.** An offer
  without decisions showed `.create_plot()` and "plot in seaborn", which did the
  same. Now `.create_plot()` stands alone and still takes the switch's carry
  along. With decisions, the quiet button beside the offer reads
  `.start_over()`. (#12575)
- **Popovers no longer shift the page.** A popover's scroll lock never stopped
  the page from scrolling, because the page clips its horizontal overflow at
  the root. It only padded the body, so the masthead and the right-aligned
  controls jumped 15 px as the library or language menu opened. (#12575)
- **A file chosen with `.open()` hands the focus to the message box.** Enter
  then sends the file instead of opening the chooser again. (#12575)
- **A refused `.copy()` says so.** When the browser refuses the clipboard, the
  button reads `.copy() failed · select the code` for 2 s, a screen reader hears
  it, and the code opens so it can be selected by hand. Before, nothing
  changed on the page. (#12575)
- **The result card takes the progress grid's place.** A run's card used to
  land above the grid while the reply was still being written, pushing the grid
  and the composer down until the turn ended. Now the card replaces the grid,
  and anything the run sends into the thread before its card waits for it. The
  agent BFF mock gains `MOCK_REPLY_MS`, the time the reply takes after the plot.
  (#12575)
- **A cut chat stream no longer hides a plot the server made.** On 2026-11-05 an HTTP/3 error ended a chartjs turn's
  stream 104 s into a 126 s run. Both origin hops ran the turn to its end and stored version 1, but the page showed
  "the server did not answer", and the retry made a version 2. Now every turn event carries the SSE id
  `<run_id>.<n>`, and the session keeps its latest turn's events. A new `GET /agent/session/turn` (and
  `/debug/agent/sessions/{sid}/turn`) with `Last-Event-ID` streams the rest of the turn, live until it ends. When a
  stream fails or ends without `done`, the page keeps the loader with a quiet "connection lost · reconnecting…" line
  and reads the turn again after 1, 2, 4 and 8 s. It shows the error only when every read failed, and the next click
  of the same request reads that turn first instead of making the same plot twice. The agents stream now writes a
  `: ping` after every 15 s without an event, as the BFF route already did, and a test pins the BFF's ping. A client
  that the agents service sees go still cancels the run. (#12572)
- **The progress grid stands still from `.create_plot()` to the result.** After
  the data card folded, the run's `starting…` or `queued · 1 of 2` line above
  the grid went away at the first step, and the grid jumped up one line beside
  the loader (27 px at desktop and phone width). With each step, the cells
  after the active one also slid right by about 11 px, because a step still to
  come had no marker. Now where the run stands shows in the first try's outcome
  cell. Every marker has a slot of the same width, and the label and first step
  columns are sized for `second try` and `repairing` from the start. While the
  run lasts the page also has no scroll anchoring, which had scrolled the page
  by a repair round's new row (25 px at desktop width, 65 px at phone width).
  The agent BFF mock gains `MOCK_START_MS`, which holds a run before its first
  step, and `MOCK_REPAIR=1`, which gives a first plot a repair round. (#12569)
- **One queue position, which moves nothing.** A plot run names its place in
  the queue only in the progress grid's first row. The badge above the composer
  used to come and go there too, moving the grid and the composer 33.5 px down
  and back. A turn without the grid keeps the badge, now beside its in-progress
  line and out of the flow. (#12569)
- **The bindings say why they wait in their heading.** While the assistant
  works or the data is parsed, the heading reads `# bindings — wait while the
  assistant works` (or `… the data is parsed`) and then swaps back. The
  separate line under it read as the heading twice and moved the dropdowns
  as it came and went (25.5 px at desktop width, 45 px on a phone). (#12569)
- **Two flaky tests no longer turn main red.** The adaptability checker's
  design-example test read live catalogue files, so the nightly regeneration
  of line-basic's seaborn file broke it; the two examples now come from
  fixtures under `tests/unit/core/fixtures/adaptability/design/`. The
  validator's per-file CPU budget now measures only the validator's own thread
  with the garbage collector paused: the process-wide CPU time also counted
  the test worker's other threads and heap collections, which pushed 3 ms files
  past the 1 s budget (`network-weighted/matplotlib`,
  `heatmap-periodic-table/plotnine`). (#12563)
- **The default bindings no longer invert a range.** A lower and upper bound
  pair is never bound by default to two columns whose lower one starts above
  the largest value of the upper one, where every row's minimum would lie
  above its maximum; the pair stays open, so the conversion check runs. Bound
  so by hand, the pair is the user's choice: it stays valid, survives every
  change of the data and carries one neutral warning line. (#12556)
- **The docs describe the agent chat and the catalogue as they are.** The agent network design,
  `agents/README.md`, the docs index, the app architecture and the project guide now say the chat
  is public and experimental at `/agent` since 2026-11-02 for all 15 libraries, with the admin
  tools at `/debug/agent`. The style guide names four languages, the current page color and
  border alpha with recomputed contrast ratios, the curated catalogue next to the chat, and the
  seven mobile nav items; the API and repository references show the current response and metadata
  shapes, and per-library metadata lives under `metadata/{language}/` (#12547).
- **The deploy-agents trigger filter and the Vite pin are documented as they run.** The header of
  `agents/cloudbuild.yaml` gives the trigger's ignore list that lets prompt-only changes deploy and
  the export and import route for changing it, and the Dependabot ignore for `vite` names the
  8.3.5 pin, the outage of #12225 and its fix in #12235 (#12547).
- **Pictograms, waffles, dot matrices and parliaments no longer read as made-up
  data.** The render gate that counts more point marks than rows (G8) now skips
  the plot types that draw one mark per unit of a count, so a pictogram of 11
  rows that draws 77 icons is no longer sent to a repair to "draw marks only
  from df". Every other plot keeps the check, and the ceiling on plotted points
  still holds for all. (#12552)
- **The reply after a shipped plot no longer asks to confirm the data.** A code
  check drops every sentence that names `.confirm()` from the assistant's reply
  in a turn whose plot shipped, because a shipped plot was drawn from confirmed
  data. The rest of the reply stays word for word, and the check costs no model
  call. (#12552)
- **The assistant knows that the data panel opens files.** Its list of the page's controls left out `.open()`,
  dropping or pasting a file, and the sheet and table dropdowns, and said the page had no upload, so a user who
  asked to load an Excel file was told it could not be done. The data panel's bullet in
  `agents/anyplot/prompts/root.md` now names them with the formats and size caps (CSV, TSV, JSON or plain text up
  to 1 MB; Excel, ODS, Parquet, Feather, Arrow or NumPy up to 5 MB), plus `.replace()`, `.keep()` and `.view_all()`
  with its full view's buttons, and the disclaimer under the list covers only the settings the page does not have.
  `tests/unit/agents/test_prompt_controls.py` now checks the other direction too: every button the data card
  renders is named in that bullet. (#12548)
- **`/specs` thumbnails follow the site theme, and every library has its short
  name.** The spec list showed the light render in dark mode; it now picks the
  render the gallery cards pick. The compact gallery cards and the mobile
  library carousel read the shared 15-library abbreviation map, so MUI X,
  ggplot2 and Makie show `mui.tsx`, `gg.r` and `mk.jl` instead of their full ids
  (#12546).
- **Links and copy that pointed at the wrong place or said the wrong thing.**
  `libraries.all()` on the landing page opens `/libraries`, not `/plots`; the
  palette link on `/about` navigates inside the app instead of reloading the
  page; `request_plot()` opens the plot request form instead of a blank issue
  with a label and a title prefix. The `/plots` description drops its stale
  "2,600+" count and `/specs` no longer calls the specifications Python-only;
  `/mcp` lists every tag filter `search_specs_by_tags` takes; `llms.txt` names
  the "Use with my data" chat (#12546).
- **Page metadata matches the bot HTML.** Spec pages name Julia and JavaScript
  in the `SoftwareSourceCode` language, carry the bot's breadcrumb (home, spec,
  library), and share the spec card as `og:image` on the hub. The shell's
  `og:image` is the card the bot serves for `/`, and its `theme-color` is the
  page background. `/map` is titled `map | anyplot.ai` with a canonical URL, and
  the chat tab names the plot instead of its spec id (#12546).
- **Toggle state reaches assistive technology on `/palette` and `/map`.** The
  sort buttons carry `aria-pressed`, and the legend and weights toggles carry
  `aria-expanded` (#12546).

### Security

- **Cloudflare Turnstile on the calls that open or store something for a visitor.**
  Opening a public chat session, a public chat feedback case and a site feedback
  entry (the widget and the plot pages' 👍/👎) now need a Turnstile token in
  `X-Turnstile-Token`, which `api/turnstile.py` redeems at Cloudflare's siteverify
  and fails closed on: `403 bot_check_failed` for a missing, refused or reused
  token, `503 bot_check_unavailable` when siteverify cannot answer. The page renders
  the widget in Managed mode, invisible unless Cloudflare asks for a click, loads
  Cloudflare's script only for those calls and takes a fresh token for each, and a
  failed check reads as one line with a retry. Production keeps the public chat's
  door shut without `TURNSTILE_SECRET_KEY` and refuses Cloudflare's test secrets,
  and the deploy smoke proves the secret against siteverify with Cloudflare's dummy
  token. The site's CSP allows `challenges.cloudflare.com` for scripts and frames
  only, and `/legal` names what the check reads and stores (closes #7249) (#12555).

*Catalog: no new specs and no new implementations; 398 regenerations (#12544 to
#13052). 380 were forced through adopt mode on 2026-11-08 and 2026-11-09. 209 of
those PRs finish the MUI X 9 migration: they take the remaining 196 MUI X
implementations (11 of them more than once) from @mui/x-charts 7.29.1 to 9.17.0, so all 323
now run on version 9. The other 171 PRs come from the first catalogue audit round
and cover 167 pairs in 14 libraries: 68 fixes picked from its findings, 99 legacy
regenerations, and four pairs fixed a second time after the re-audit (`pygal` 31,
`letsplot` 23, `bokeh` 22, `matplotlib` 20, `plotly` 17, `plotnine` 16, `seaborn`
16, `altair` 14, and 12 across `echarts`, `highcharts`, `ggplot2`, `chartjs`,
`makie` and `d3`). 18 are daily-regen improvements (`seaborn` 4; `pygal`, `bokeh`
and `altair` 3 each; `plotly` and `plotnine` 2 each; `letsplot` 1), and two kept
regenerations stored their re-score (#12562, #13041).*

## [4.0.0] — 2026-11-03 — Your data

### Added

- **The public "use with my data" page at `/agent`, experimental.** The chat
  page runs on the public lane while the API says it is open
  (`GET /agent/lane`), so one switch on the server opens and closes the page
  and its entry points. It talks to `/agent/*` without a cookie, with a random
  id per browser tab and the session id as headers, and says above the first
  input that an AI does the work, which one and where, that results can be
  wrong and are not checked by hand, what not to paste, that nothing is stored
  without feedback, and that daily limits apply. The plot page's `.adapt()`
  button shows for everyone while the lane is open, and the landing page
  points to the chat with one line. Admins keep `/debug/agent` with
  everything (#12528).
- **A public lane for the agent chat under `/agent`, shipped dark.** The new
  router calls the admin lane's route functions with an anonymous identity
  and the `public` tier, and answers `404` until the owner sets
  `_AGENT_PUBLIC_ENABLED=true` on the deploy-api trigger, on top of
  `AGENT_ENABLED`, which stays the master switch. The page's random tab id
  (`X-Anyplot-Anon`) and the client's network go to the agents service, which
  salts both with a per-process salt, so no durable key links usage to an
  address; the session id travels in `X-Anyplot-Session`, never in a URL.
  The fan-out copy, the day budget and the case triage stay admin-only, and
  `GET /agent/lane` tells the site whether the door is open without an
  upstream call. The deploy smoke checks the door answers as the trigger set
  it (#12527).
- **Per-IP limits for anonymous callers.** The users of one network (an IPv4
  address or an IPv6 /64) share 4 sandbox runs at once, 100 pipeline runs and
  20,000,000 weighted tokens a day, and twice the per-user minute and day of
  pastes, conversions, chat turns and beacons: twice the per-user caps,
  because a tab id costs nothing to mint. A network also holds at most 8 live
  sessions and 64 MiB of the 256 MiB dataset store, so one machine cannot
  fill what every user shares. The public lane holds at most 10
  waiting runs in the agents queue, one API instance relays at most 20 public
  chat turns at once so the catalogue keeps half its request slots, and a
  network stores at most 20 feedback cases an hour (#12527).
- **Switch the plot's library from the chat.** "Make it in seaborn" now moves the plot: the assistant's
  new `switch_plot` asks for the switch, the turn's `done` carries it, and the page switches and makes the
  plot there at once with your decisions, as the library menu's carry run does. A switch the server
  refuses shows in the thread. (#12523)
- **`.plot_all()` plots your tuned plot in every library.** The fan-out's dataset copy now brings the plot
  memory and a carry of the page's latest plot along, so each library's plot starts from its catalogue
  plot with your decisions instead of from scratch. (#12523)
- **The agent chat offers the plot in the new library with your decisions.** After a library switch
  whose answer offers it, the composer's create action reads "plot in seaborn with your 3 decisions"
  and sends `carry_plot`; picking a library runs nothing until that click, so browsing costs nothing.
  `.create_plot()`, or `.start_over()` once the library has a plot, stays beside it as the plot from
  the catalogue code, which keeps your decisions too, and the offer ends once a plot ships in that
  library. (#12522)
- **The remembered decisions stand above the composer.** The plot memory's entries, the decisions every
  next plot takes over, are listed with `.forget()` each and `.forget_all()` for a blank start, the only
  ways the memory is cleared; the list is read again after every turn, after a switch and after a
  removal, hides while the memory is empty and waits while anything runs. (#12522)
- **The plot memory: your decisions about the plot, kept across a library switch.** The agents service
  keeps the decisions of each shipped change (a reference line, a formula as an annotation, outliers as
  red stars, an axis label, the x limits) as entries of a closed kind with library-neutral text, and every
  later plot hands them to the adapter and the reviewer, in any library. The root passes them with the
  run, since it cannot call a tool after a shipped plot, and the memory keeps them only once that plot
  ships. Only you clear it: `GET` and `DELETE /debug/agent/sessions/{sid}/memory[/{id}]` list the
  entries and remove one or all, and once the memory has held a decision, a removed one never comes
  back from the requests behind an earlier plot. (#12520)
- **A library switch carries the tuned plot over.** The switch now writes a carry (the theme you asked
  for, the texts the plot must show) and answers what would carry and whether to offer the plot in the
  new library; the `carry_plot` action makes that plot from the new library's catalogue code with your
  decisions, and checks the label in code. Versions are filed under their (spec, library) pair, so the
  later plot-type switch reuses the same path. `agents/evals/carry.py` checks the owner's five examples
  live from matplotlib to plotly and ggplot2. (#12520)
- **Every row of your data in the agent chat, to search, sort and filter.**
  `.view_all()` next to the data card's preview opens the current data version
  in a read-only MUI X Data Grid (the MIT edition, loaded only when you open
  it): a search over every column, sorting (numeric columns by number, empty
  cells last), a column filter with `>` and `<` on numbers, column resizing
  and hiding, the dtype under each column name, both themes and phone width.
  Values appear exactly as the canonical `data.csv` holds them, which the new
  read-only route `GET /debug/agent/sessions/{sid}/dataset/data.csv` serves and
  a strict RFC 4180 reader parses in the browser, so nothing is rounded or
  reformatted and an empty cell stays empty. The free grid shows 25, 50 or 100
  rows a page; the search, the sort and the filter cover every row. Opening it
  reports the content-free outcome `opened_data_view`. (#12513)
- **An open required role makes the server check which columns a conversion
  would fill it with.** When the bindings leave a required role open, the
  service dry-runs `set_type` on every free text column in code
  (`agents/anyplot/data/conversions.py`), and on a whole-number column with a
  year header, and lists each candidate in the session block with its counts,
  `certain` or `uncertain` with the reason, and the operations. The root makes a
  certain conversion in the summary turn as a new column beside the original
  (`set_type` gained `name`), which the service binds to the role, and proposes
  an uncertain one as its one question; the user confirms as usual and `.undo()`
  takes it back. Ids, codes and spans of years stay out of it. The source column
  leaves the optional roles, so `Month` on `series` never splits the plot into
  one series per row. (#12512)
- **A plot without an x column draws by row number.** The new `row_number`
  operation adds a column `index` of 1 to n. When a required axis has no column
  and no conversion, the root makes it without a question, the axis takes it, and
  a number column that sat on the axis moves to the open measure: a pasted
  `1,3,5,4,6,2` ships as a line plot. A bar chart without labels gets the row
  numbers as a question, never by itself. (#12512)
- **The prep eval fails a skipped conversion, and `chat_turn` reports the
  outcome.** A summary turn that skips a `certain` conversion is a miss and fails
  the run. `chat_turn.conversion` is one closed value: `none`, `date`, `number`,
  `index` or `asked`. (#12512)
- **Per-day agent numbers on `/debug`.** The usage card gains a table of the last
  14 UTC days, newest first: new chats, plots shipped, cost in dollars (the `cost`
  view's logic, the admin fan-out's beside it), limit hits by code and the 95th
  percentile of the run queue's wait, `—` on a day before the field. A new
  `GET /debug/agent-usage/daily` reads it from the telemetry under the card's own
  discipline: filtered on `timestamp` before it deduplicates, kept for ten minutes,
  aggregates only. (#12518)
- **A live line for today on `/debug`.** `GET /debug/agent/budget` shows the service's
  spend against its day budget and how many users are at their own limits, counts
  only, from the agents service's memory. The line says since when it counts, because
  a redeploy or a scale-to-zero starts the counts again. (#12518)
- **An admin lane in the agents service's run queue.** The admin's runs,
  `.plot_all()` above all, may hold five places per admin (public users two),
  with no per-user day caps or message minute (owner decisions of
  2026-11-01). The BFF asserts the tier with `X-Anyplot-Tier: admin` from the
  identity its admin gate verified; a missing or other value is the public
  tier, so the two services deploy in either order. `GET /status` reports the
  caller's own cap, and the fan-out panel follows it (#12507).
- **Anonymous limit telemetry on `pipeline_run`.** `lane`, `queue_wait_ms`,
  `queue_position`, `user_runs_today` and `user_tokens_today` show whether
  anyone waits long or comes close to a limit, as closed sets and bounded
  numbers with no user id and no hash; the views SQL reads them, and applying
  it in BigQuery waits for the owner after the merge (#12507).
- **Example data on request in "Use with my data".** "Beispieldaten",
  "generiere Zufallszahlen mit Kategorien" or "monthly sales for 4 regions" in
  the data field no longer ends in "no table found": the dataset route answers
  `422 data_request` (fixed phrases in eight languages before any model, the
  free-text reader's new `asks_for_data` for the rest) and the page sends the
  text to the chat as the user's message. The assistant reads the plot's data
  roles and writes seeded Python that `run_data_code` runs in the sandbox, so
  no model writes a row; the data panel's change line says
  `generated example data`, and the same works when asked in the chat.
  (#12509)
- **Eval cases for follow-ups that ask for two changes at once.** Four
  hand-written matrix cases send a follow-up such as "Make the title German
  and use a log scale on the y axis" after an English first plot: a language
  with a log scale, a theme with a grid, a language with a colour, and a log
  scale alone as the control. A new `checks` field in `case.json` measures
  each part in code on the version the follow-up shipped: its plot language
  and theme, patterns its code must add or keep, drawn texts that must
  change, and an empty `requested_not_found`. A run passes only when every
  check holds, and the report lists each failed one under `check_failures`.
  (#12510)

### Changed

- **The agent chat shows less text, with the details behind buttons.** The
  public experimental notice is one line, `# experimental AI · results can be
  wrong · stored only if you send feedback`, and its ⓘ button opens the rest
  (which AI and where, what not to paste, the daily limits, the legal page). A
  result card shows its image, toolbar and theme switch, while the rounds and
  the change list sit behind one status line and the code behind
  `.show_code()`, with `.copy()` and the downloads in view; each card keeps its
  choice for the session, and a new version starts folded. The quick feedback
  shows only the reactions until one is picked. On the admin lane `.save()`
  and its data box moved from the header row into a "⋯" menu, not into the
  feedback area, because a save downloads the session and stores nothing; the
  public lane has neither, since a visitor cannot resume a saved session and
  the feedback form covers what went wrong. The data card's
  header is `# your data ⓘ`, its how-to behind the button, and the long hint
  and the how-to paragraph under the card gave way to short placeholders.
  The chat column grows with the window up to 1360 px, so the data card,
  the plot images and the code use a wide screen, while the chat text keeps
  a readable line of about 80 characters. (#12540)
- **The legal page is shorter and states only the current state.** Its visible text drops from 1,805 to 1,072
  words (the privacy policy from 1,546 to 775): what is processed, where it runs, how long each store keeps it, the
  three legal bases and the data assistant's terms now sit in short fact tables with row headers, each fact said
  once. The notes on log entries written before the move to europe-west4 and on older unsalted feedback hashes are
  gone; both conditions ended on 2026-11-02. The feedback IP hash no longer reads as a flat ten minutes: it is
  cleared by the next feedback after its window, and its salt dies with the server instance. The crawler version
  (`/seo-proxy/legal`, 450 words, 370 before) drops the same history and now carries every fact the page states:
  the stored feedback fields, Cloudflare's use of the IP address, all three legal bases, your rights, the telemetry
  retention, the no-training line and the running costs (#12538).
- **The transparency section lists the whole stack and what running the site costs.** Eight grouped rows (site,
  api, catalogue pipeline, data assistant, Google Cloud, edge and analytics, reviews, editor and typography) replace
  the old list, which named neither the data assistant nor most of the Google Cloud services. The cost table shows
  October 2026 as paid after commitments and credits, about $60 a month with the assistant's model, in place of a
  $34 estimate of hosting alone (#12538).
- **The plot page's way into "use with my data" is a text action beside the
  library carousel.** `.use_my_data() →` sits to the right of the carousel as
  the mirror of `← .compare()` on its left and replaces the data-table icon on
  the image, which said little and crowded the overlay buttons. It keeps the
  icon's gating (open lane or an admin, eligible pair), its chat link and
  `agent_open`'s `source=plot_page`; "experimental" is left to the chat's
  notice. The carousel now sits centred over the image, so the action fades
  in after the eligibility check without moving anything; on a phone or
  tablet the two actions share the line above the carousel (#12539).
- **The landing page's line points to the catalogue.** While the public lane
  is open it reads `# new: pick any plot, then .use_my_data() →` and leads to
  `/plots` instead of opening the chat on one fixed plot, tracked as
  `nav_click{source: hero_use_my_data}` (#12539).
- **The README and the docs say the agent chat is open**: since 2 November 2026 every visitor can use "Use with my data", labelled experimental. The README's status line no longer says it is rolling out, and the vision, repository, database, style-guide, Plausible and telemetry docs no longer call it admin-only. (#12537)
- **Feedback and `.save()` leave the data file out unless you tick the box.**
  On the public page both `# include data.csv` boxes start unticked, and the
  feedback form says what sending stores; admins keep their default (#12528).
- **The legal page covers the public assistant.** Its section (now
  `#assistant`) says the assistant is experimental, open to everyone and
  pausable, how ids and IP addresses are salted and never written down, adds
  use and warranty, the generated code's licence with the Highcharts note, and
  the transfers under Google Cloud's and Cloudflare's terms; the feedback IP
  hash wording follows the salted hash, and the bot-facing legal page mirrors
  the facts (#12528).
- **anyplot-api runs as its own least-privilege service account**: the API deploys as `anyplot-api@` instead of the Compute Engine default service account, which holds `roles/editor`. The new account gets only Cloud SQL, its six secrets, the agent-cases and static buckets, read access to the telemetry datasets, and the invoker role on `anyplot-agents`, which now admits it as the BFF caller. A unit test keeps the API's deploy account and the agents service's allowed caller equal. (#12525)
- **The README leads with what anyplot is, its numbers, and how it works.** It opens with the project, its author and a
  live preview card, then the catalogue's numbers from the public API (325 specs, 4,863 implementations, 15 libraries,
  four languages on 2026-11-02), the pipeline with its real quality bar (90 on the first review, 10 points lower per
  repair down to 50, in place of the old "score ≥ 50 required"), the experimental "Use with my data" agent, the MCP
  server, the tech stack and a project structure that now includes `agents/`. The "natural language search" it claimed
  never existed: it now describes the typo-tolerant tag and title search the site has. `docs/concepts/vision.md` counts
  15 libraries across four languages instead of eleven across three, and lists the MCP server as live. (#12524)
- **The agent chat picks its library in a menu.** A chip like the language chip,
  `lib: matplotlib · python`, opens the libraries grouped by language and, for the admin,
  `all libraries`, in place of a pill per library (up to 16 with `all`). The pills' rules stay, and a
  refused switch shows its reason under the chip instead of in the thread. (#12522)
- **A library switch keeps a request kept for the first plot.** The data and bindings it was written for
  stay, so it now waits for the first plot in the new library instead of being dropped. (#12520)
- **`.start_over()` keeps your remembered decisions.** It starts again from the catalogue code, the way
  out of code that went wrong, always on the catalogue base, and applies the plot memory to the new
  plot. (#12520)
- **The row numbers lead the data and the data view.** The `row_number`
  operation inserts its column (`index` by default) as the first column instead
  of the last, and moves a reused row-number column there; the change line says
  so, and no value or row moves. The data view shows a column that numbers the
  rows (the operation's `index`, or a pasted `X`, `Unnamed: 0` or `column_<n>`)
  leftmost in place of its own `#` counter, with the data's own values, also
  after a sort reordered them; without such a column the counter stays. A sorted
  column's header keeps room for its dtype beside the sort arrow and the menu.
  (#12521)
- **A spent service budget has its own refusal.** When the service's day budget is
  spent, not the user's own, the chat now answers `service_paused` in every language,
  a paste or a file conversion `429 service_paused`, instead of the text for a user's
  own limit. It names the reset at 00:00 UTC, the page adds that time in the user's
  own time zone, and `GET /v1/status` answers `paused` and `resets_at`, so the chat
  shows the note before the user types. (#12518)
- **Google ADK 2.13 and pandas 3.1.** ADK now delivers a response schema to Claude
  as a `structured_output` tool, forced with thinking off and only offered with it
  on, which on the adapter and reviewer would sit next to the constrained
  `output_config.format`, so `VertexClaude` drops the tool and keeps the format.
  Since pandas 3.1 reads every float exactly, the loader of an exported `plot.py`
  no longer sets `float_precision`, which pandas deprecated and will remove, and
  pandas is at least 3.1.0. (#12426)
- **The run queue runs five plots at once and starts one every 10 seconds.**
  `AGENT_RUN_CONCURRENCY` 5 for the whole instance and `AGENT_RUNS_PER_MINUTE`
  6 with the starts spaced 10 s apart (1 and 1 before), so the queue holds 60
  and a 15-library fan-out no longer takes about 20 minutes. A public user's
  day is 50 runs and 10,000,000 weighted tokens (about $1), and the global
  day budget is 100,000,000 (about $10), admins included. Claude calls retry
  four times instead of two; a 429 or 529 that outlasts them ends the run as
  `busy`. The render gates run in a worker thread (#12507).
- **The fan-out panel waits out `run_limit` instead of failing.** With
  `.plot_all()` open in several windows the admin's cap counts them all: a
  library the cap refused goes back to waiting, and the panel tries again
  when one of its runs ends or after 15 s, giving up only after 30 minutes.
  The fan-out's data copies no longer count against an admin's copy limits
  (30 a minute, 150 a day), so three windows can copy their 45 datasets at
  once (#12507).
- **The agents service keeps one instance warm.** `anyplot-agents` deploys with one minimum instance, so the first chat message after a quiet period no longer waits for a cold start, and sessions and day counters no longer vanish when Cloud Run scales the service to zero; a session still ends after an hour without activity (`AGENT_SESSION_IDLE_S`), and a deploy still resets both. Its idle cost of about 0.44 CHF a day falls inside the account's unused Compute Flexible commitment until 2027-01-15 (#12511).
- **Dependencies:** 13 Dependabot PRs. The python-minor group (#12426) takes
  `google-adk` 2.11.0 → 2.13.0 and `pandas` 3.0.6 → 3.1.0, with the code fixes
  in the same PR (see its own entry), plus `fastmcp` 4.1.4, `alembic` 1.20.1,
  `plotnine` 0.15.8, `ruff` 0.17.2, `pydantic-settings`, `cachetools` and
  `pytest-asyncio`. `filelock` 3.32.7 → 4.2.1, a major version (#12301),
  `tornado` 6.5.9 → 6.6 (#12425), `authlib` 1.6.12 → 1.9.1 (#12412),
  `dnspython` 2.8.0 → 2.9.0 (#12411), and patch releases of `virtualenv`,
  `pyasn1`, `joserfc` and `fastmcp` (#12302, #12485, #12486, #12300). In
  `app/` the npm-minor group (#12517: the typescript-eslint packages,
  `eslint-plugin-perfectionist`, `vite-plugin-compression2`); for the
  JavaScript renderers `chart.js` 4.4.7 → 4.6.1 (#12252) and `esbuild` 0.28.1
  → 0.28.2 (#12262); and the actions group (#12406: `setup-python` 7.1.0,
  `setup-uv` 10.3.3, CodeQL 4.39.1, `claude-code-action` 1.0.264,
  `setup-julia`).

### Fixed

- **A link to a section of the legal page lands on its heading.** The route loads lazily, so a fresh load of
  `/legal#assistant`, which the chat's notice opens in a new tab, stayed at the top of the page; it now scrolls to
  the section once the page renders, below the sticky masthead. The code and docs that still promised a migration
  for the old unsalted feedback IP hashes now say they were cleared once by hand on 2026-11-02 after a snapshot
  (#12538).
- **Library counts and layouts that still described the catalogue before JavaScript.** The language filter's tooltip
  named only Python and R and now names all four languages; the `GET /stats` example in `docs/reference/api.md`
  showed three fields and 9 libraries and now shows the live payload with `languages` and `lines_of_code`, each field
  explained; and `docs/reference/repository.md` drew `metadata/` and `implementations/` as flat Python lists with
  Highcharts among them and no `javascript/` directory, and now shows the four language directories in every tree:
  8 Python files, ggplot2, Makie, and the five JavaScript ones. (#12526)
- **A formula in a plotly plot is typeset.** The renderer's browser loads no MathJax, so a LaTeX string was
  drawn with its dollar signs; the plotly adapter now writes formulas with plotly's HTML tags
  (`ax<sup>2</sup>`), as the switch eval's first live run showed. (#12520)
- **CI runs the plotting-library tests.** "Run Tests" installs libcairo and
  the eight `lib-*` extras of the renderer image, without its image-export
  stacks, and sets `ANYPLOT_REQUIRE_LIBRARIES=1`, so a library that does not
  import fails its tests instead of skipping them. Before, the validator's
  walk saw matplotlib alone, and 32 harness, validator and normaliser cases
  never ran in CI (#12519).
- **The text probe of pygal, altair and lets-plot holds the drawn texts.** The
  harness wrote it through `os.fdopen`, whose `open` event names no path, so
  the plot guard refused the write and left an empty file. The reply had no
  texts for those three libraries since #12503. The probe now goes out
  through `os.write`, a FIFO at its name no longer blocks the write, a failed
  write is logged as `probe_failed` per launch, and an empty or unreadable
  probe reaches the `pipeline_render` line as `InvalidProbe` (#12519).
- **Month names with a year are dates.** The parser and `set_type` read
  `Nov 2026`, `Okt. 2026`, `2026 Nov` or `März 2026`, in the eleven languages of
  `months.py`, as the first day of each month, with a warning that counts the
  cells; a two-digit year (`Nov 26`) stays text. In the live test of 2026-11-01
  a price table of `Nov 2026` to `Dec 2025` left a time series' date role open,
  and the root asked the user for a date column. A plot writes such a column as
  months, also as a bar chart's labels and past 60 of them. (#12512)
- **A copied web table keeps its last row and loses its button.** A short line
  between the rows that holds text in the value columns (`Show 36 earlier
  months`) is left out with a count, and a last row that lost its empty cells
  stays a row. Before, the button stayed a row of empty cells, the month column
  stayed text and the last month was lost as a footer. (#12512)
- **The minus sign is a minus.** A minus written `−` (U+2212) before a number
  reads as a sign, in the parser and in `set_type number`, with the cells
  counted. An en dash stays text, as a range such as `10–20` does, and
  `set_type` no longer takes a dash for a unit, which dropped the sign of `–5`.
  Before, a change column of `+75` and `−100` stayed text. (#12512)
- **A newest-first time series is sorted, not asked about.** A date column's
  profile says which way its dates run (`order`), and the root sorts a
  newest-first date column of the plot ascending in the summary turn instead of
  asking whether to reverse the rows. (#12512)
- **`set_type` to dates no longer fills in what a cell lacks.** pandas read a
  cell without a year as the year 1 (`May`, `Nov 26`) and a time alone as
  today; such cells now fail and are counted, and a month name no longer leaves
  the day and month order open. (#12512)
- **Float totals add up the cells as they are written.** A group `sum`, a group
  `mean` and a `share` now add a float column in decimals. pandas 3.1 dropped its
  compensated group sum for sorted keys, so 1,840 cells of the eval fixtures and
  test sets changed, and a monthly total of `4024.2` came back as
  `4024.2000000000003`; adding in decimals gives the sum a reader gets by hand, on
  every pandas version. (#12426)
- **A message that asks for a language and another change gets both.** In
  the user test of 2026-11-01, "make the title German and use a log scale"
  reached the plot with the German title only: `root.md` had the root follow
  `set_language` with a fixed rewrite request that ended "change nothing
  else". The rewrite is now the server's job. The adapter already rewrites
  the plot's text when the base version is in another language, so the
  root's change request carries only the user's other changes, and a run with
  none gets the server's own rewrite request. The root also sends a theme only
  as `theme`: written into the change request, "a dark background" made the
  adapter replace the theme tokens with fixed dark colours. (#12510)
- **A cancelled local render waits for both theme containers.** It used to return, and remove the run directory, while the second container was still being killed, which also made a backend test flaky (#12511).

### Security

- **The site feedback's IP hash is salted and short-lived.** `POST /feedback`
  stored an unsalted SHA-256 of the client address without a time limit,
  which trying every IPv4 address undoes. It now stores an HMAC under a
  random per-process salt and clears it once its 10-minute window has
  passed; rows from before keep their old hash until a reviewed migration
  clears them. A log line of an unreachable agents service no longer names
  the session id (#12527).
- **The plot validator refuses banned objects under any name.** pygal binds
  `types.FunctionType` as `pygal.config.callable`, which the validator admitted
  because it bans `FunctionType` and `LambdaType` by name only. The walk of the
  admitted modules now decides by what an object is: a builtin or `types`
  member the validator bans, a module it bans together with that module's
  functions and classes, a loader, a frame, or a wrapper of any of these,
  wherever a public path reaches it. The walk found five more routes, now
  refused: `pathlib.Path`, re-exported by matplotlib and statsmodels;
  multiprocessing's `Pool`; altair's `importlib_version`; and the `tokenize`
  module. The reviews also ban `timeit` on every receiver and the `eval_str=`
  keyword, with which `inspect.signature` evaluates a function's annotations
  (#12519).
- **No route to a module-scoped ban through an expression or `**`.** A path
  that leads to a `MODULE_ESCAPES` entry is only a receiver, a callee or a
  plain alias, so `[matplotlib.cbook][0].Path` and an annotated alias are
  refused. A banned keyword is refused when `**` passes it from a dict held in
  a name or filled by subscript or `.update`, and so is a keyword name built
  at run time, unless its literal head rules out every banned keyword
  (plotly's `f"xaxis{n}"` passes) (#12519).

*Catalog: no new specs and no new implementations; three nightly regenerations, all of
funnel-basic, each kept as an improvement: plotly (#12514, quality 82), altair (#12541, 86)
and plotnine (#12542, 85). For bokeh the regen gate kept the live implementation (#12515),
and the review's re-score of it, 86 → 69, was stored (#12516).*

## [3.6.0] — 2026-11-01 — All fifteen

### Added

- **The prep eval measures the root's replies.** Every reply's words, questions and closing question are counted;
  a closing question the turn was not blocked for, or a reply over 100 words, is a reply miss, gated at 10 %
  (`--max-reply-misses`). A case can send the page's summary action, and four step-1 summary cases join the set.
  (#12506)
- **`--theme dark` for the eval matrix.** Every turn of the run sends the
  site theme, as the chat page does, so dark first renders can be measured
  before the public release. Every committed baseline is light. (#12505)
- **plotly and bokeh in "Use with my data", for the admin's live tests.** The
  Python runtime serves both through the renderer's two-step figure mode: the
  plot writes its figure as JSON under the plot guard, and the JavaScript
  harness draws it in Chromium at the catalogue's canvas. The admin deploy names
  them, so all 15 catalogue libraries are served, and each one's 80 % eval
  matrix gates the public release. Across the catalogue 273 of 325 plotly and
  252 of 325 bokeh files are eligible; in the renderer image 254 of the 273 and
  245 of the 252 render on target in both themes as they stand, the rest only
  because their code divides by the length of the emptied catalogue title.
  (#12490)
- **The validator rules for plotly and bokeh.** Both refuse private names,
  anything but `None` where the library expects a URL, and every model that
  loads from the network or a file: plotly's geo and map traces and its
  `plotly_relayout` family, bokeh's JavaScript, markup, CSS and tile models and
  its import by name. bokeh's tooltip templates pass as the catalogue writes
  them, text tags with a quoted `style` or `class`, never `{safe}`, because
  BokehJS parses a template and each tooltip value as HTML; plotly text holds
  no link. (#12490)
- **The renderer checks a plotly or bokeh figure for markup before it draws
  it.** A figure that holds what a browser would run, load or link (a bokeh
  JavaScript, HTML or CSS model or any model no catalogue plot uses, a tooltip
  outside the template rule, a link in plotly text, an image URL) fails as
  `figure UnsafeMarkup`, whatever code built it, so the downloaded code never
  writes it into the user's HTML. The renderer image's CI asserts the refusal
  through the image's own harness. (#12490)
- **The figure save and the exported code.** The normaliser turns the
  catalogue's save block into one protected statement that writes the figure as
  JSON (plotly's size moved into the figure; bokeh's Selenium screenshot block
  removed). The downloaded `plot.py` swaps it back for the library's normal
  save, so it runs unchanged on the user's machine with `data.csv`: plotly's
  `write_image` and `write_html`, bokeh's `export_png`, `output_file` and
  `save`. This is the one place where the export is not the run form byte for
  byte (owner decision). (#12490)
- **plotly and bokeh adapter sections.** Measured in the renderer image: the
  protected save, the theme tokens on the figure, timestamps converted to UTC
  (plotly draws an offset timestamp's clock time as given), plotly's
  `separators` for the plot language's decimal and thousands marks, bokeh's
  ticks on fixed values with labels written in Python (BokehJS writes English
  marks whatever its `language`), `render_mode="svg"` and no WebGL. An image
  test renders each idiom from a table with missing cells in both themes.
  (#12490)
- **plotly and bokeh eval fixtures.** The ten matrix specs for each (120 cases,
  900 generated in all) and the smoke cases `scatter-basic-plotly-renamed` and
  `scatter-basic-bokeh-renamed`; all twenty files are eligible. (#12490)
- **A plotly figure render gates the renderer's deploy.** The candidate smoke
  renders a plotly figure with an axis range through both steps of the figure
  mode under gVisor and refuses the promotion when it fails twice. (#12490)
- **The pipeline's Claude steps can run on API credits, by workload identity
  federation or an API key: the repository variable `CLAUDE_AUTH`.** Unset or
  `subscription`, all 13 Claude steps in the 8 workflows that run Claude use
  the `CLAUDE_CODE_OAUTH_TOKEN` secret as before. `oidc` exchanges the job's
  GitHub OIDC token for a short-lived token of the `ci-regen` workspace (the
  four `CLAUDE_WIF_*` variables; the Console rule accepts only runs on
  `main`), and `api` uses the `ANTHROPIC_API_KEY` secret. A new first step,
  "Resolve Claude credentials", stops the job on any other value or a missing
  credential instead of falling back to the subscription and the owner's
  interactive quota, and every Claude step reads its outputs, so each passes
  exactly one credential and a new mode changes one step. Under `oidc`, the
  runs federation refuses (pull-request review events, other refs,
  `review-retest.yml`) use the subscription and say so in the job summary.
  `docs/workflows/overview.md` has the Console setup, the switch commands,
  and how to close the federation path when `oidc` is off. (#12487)
- **Every Claude session's cost in the job summary, and a clean stop when
  Claude refuses a session.** A step after each Claude step writes
  `total_cost_usd` (Claude Code's estimate at API list price), the model and
  the credential mode to the job summary and the log, and never fails the
  job. It also reads, from the error fields of a failed session, the API's
  spend-limit, spend-cap and credit messages, the subscription's usage-limit
  messages, and, with `api` or `oidc`, refused credentials: the retry is
  skipped, `impl-generate.yml` parks the pair, `impl-review.yml` and
  `impl-repair.yml` pause the PR with the new labels `ai-review-paused` and
  `ai-repair-paused` without spending their automatic retry or recording a
  score, the watchdog skips paused PRs, and nothing counts as an attempt or
  marks `impl:<lib>:failed`, a first implementation included. Before, a
  subscription usage limit used up a pair's three attempts. The weekly regen
  review's `collect_week.py --costs` reads the line, now counts the
  `daily-regen.yml` pre-flight too, and names the part that ran on API
  credits. (#12487)
- **Daily regeneration by implementation instead of by spec: the repository
  variable `REGEN_PAIRS_PER_DAY`.** Set to N, the scheduled `daily-regen.yml`
  run picks the N oldest (spec, library) pairs across the catalogue
  (`automation/scripts/regen_pick_pairs.py`), skips the spec polish, and
  dispatches each pair straight to `impl-generate.yml` with
  `bulk-generate.yml`'s arguments and pace, since that workflow's single
  concurrency group would cancel queued runs. A pair merged or really
  attempted (a closed PR, a kept regeneration, a failed generation) within
  the attempt window, 30 days unless `attempt_window_days` or
  `REGEN_ATTEMPT_WINDOW_DAYS` says otherwise, is not picked again, while an
  infrastructure failure or a generation Claude stopped leaves it in the
  queue. Paused reviews and repairs are resumed first and count against N,
  and the pick stops when it can't list the implementation PRs. Unset, the
  schedule regenerates whole specs as before; a manual run opts in with the
  new `pairs` input, and the watchdog's cron rescue forwards the variable. (#12487)
- **The renderer draws plotly and bokeh figures in two steps, not served yet.**
  The render harness forks the plot before it arms anything: the plot runs
  under the plot guard and the exec filter with the Python limits and may write
  only its figure as JSON, and the harness, never armed, then hands the figure
  to the JavaScript row's browser harness, which draws it as data with the
  installed package's own plotly.js or BokehJS in the sandboxed page, with a
  stricter policy that runs no script the figure carries. The figure keeps the
  size its code gave it, and the scale makes the image exactly 3200x1800 or
  2400x2400, so the catalogue's layouts look as published. Failures in either
  step end with the same final error line as a JavaScript render. The renderer
  image now carries plotly and bokeh without their kaleido and Selenium export
  stacks. The agent chat does not offer plotly or bokeh yet. (#12484)
- **MUI X in "Use with my data", for the admin's live tests.** The JavaScript
  runtime serves MUI X (`muix`) next to Chart.js, D3, ECharts and Highcharts:
  `plot.tsx`, a React module the renderer's harness bundles through its closed
  import plugin and mounts as a component, with the user's table as typed JSON.
  The admin deploy names it, so 13 of the 15 catalogue libraries are served, and
  its 80 % eval matrix gates the public release. A catalogue file written for
  MUI X 7 is served `coupled` with its `deprecated-api` note, never blocked for
  its version (owner decision): the adapter rewrites `ChartContainer` to MUI X
  9.16's `ChartsContainer`. The interactive `plot.html` and the in-chat preview
  work for MUI X's React bundle as for the other four. (#12483)
- **MUI X idioms in the JavaScript adapter prompt.** `adapter_javascript.md`
  teaches what was measured with MUI X 9.16 in the renderer image: the module's
  imports and its one default export, MUI X 9's names for MUI X 7's, axis bands
  sized for the user's labels (MUI X cuts tick labels that do not fit), overlays
  drawn through the chart's own scales instead of pixel positions from `margin`,
  a `"utc"` time axis with a formatter (a `"time"` axis follows the browser's
  zone in the exported page), `fmt` on every value axis (MUI X writes
  `1,250,000`), and a series formatter that guards `null`, which MUI X hands it
  when a reader hovers a gap; unguarded, the hover removes the whole chart. A
  test runs the idioms through both validator profiles, and an image test
  renders them from a table with missing cells in both themes. (#12483)
- **MUI X eval fixtures.** The ten matrix specs for MUI X (60 cases, 780
  generated in all) and the smoke case `pie-basic-muix-renamed`; five of the
  ten files are `clean` (written for MUI X 9.16), five `coupled`, one of them
  with the `deprecated-api` note. Across the catalogue 311 of 323 MUI X files
  are eligible. (#12483)
- **A Chart.js, D3, ECharts or Highcharts plot plays in the result card.**
  `.interactive()` on the image shows the plot's `plot.html` in the card, in
  the theme on screen, with its tooltips and hover; `.preview()` brings the
  image back, and a theme switch shows that theme's page. Nothing loads before
  the click: the chat then fetches the very page the download serves, through
  the same authenticated route, and holds the session while the server builds
  it. The page reaches the card through a relay on the API, so no token or
  cookie ever meets the plot code, and the site's content security policy is
  unchanged. The frame takes the plot's orientation from the page itself, and
  collapsing the card drops the preview's pages. Opening the preview is its
  own usage outcome, `opened_preview`, a look that counts as no keep. (#12482)
- **The relay page of the chat's interactive preview, `GET /preview/relay`.**
  A static, unauthenticated page of 1 KB on the API, outside `/debug/*`,
  served with `Content-Security-Policy: sandbox allow-scripts`, the browser
  harness's policy and `frame-ancestors` for the site's origins and local dev
  servers, so it runs in an opaque origin without network that no other site
  can frame. Its only message is a constant ready signal without content to
  its parent; the chat posts the page only on that signal from the relay's own
  frame, so a page that stands in at the relay's URL, such as an error page of
  the edge, never receives it, and the card says `relay_unavailable` when no
  signal comes. The relay takes one page, the first that its parent posts from
  an allowed origin, writes it into an `<iframe sandbox="allow-scripts">`
  through the `srcdoc` property and ignores everything else. The BFF mock
  serves the same relay. (#12482)
- **A probe of the relay in the renderer image's CI.** The page probe's new
  relay mode serves the relay with its real headers on an origin of its own,
  frames it scaled from an allowed origin that waits for the signal, and posts
  the CI page's wrapper: the chart draws and answers a hover in a frame of
  origin `null`, the plot code cannot navigate the wrapper or the relay, post
  a page into it or fake the signal, a second page and pages from sibling
  frames and from another origin are ignored, another origin cannot frame the
  relay, and a listening 404 page at the relay's URL receives nothing. The
  image test runs it for all four libraries. (#12482)
- **A Chart.js, D3, ECharts or Highcharts plot downloads as an interactive
  `plot.html`.** The result card's `.download('plot.html')` saves the
  self-contained page in the theme on screen: the chart library, the theme,
  the user's table and the plot code, which opens in any browser without a
  server. The agents service builds it on demand, never stored, through the
  renderer's new `POST /page`, where the browser harness writes the page a
  render would screenshot and starts no browser (`ANYPLOT_PAGE_ONLY=1`). The
  download is a wrapper with no script of its own: the harness's content
  security policy plus `frame-src 'none'`, and the page in an
  `<iframe sandbox="allow-scripts" srcdoc=...>`, so the plot code runs in an
  opaque origin that cannot navigate the window, open popups, fetch, or read
  cookies and storage. Both download routes answer it as an attachment with
  `Content-Security-Policy: sandbox`. A renderer deployed before the route
  answers `503 page_unavailable`. While the page builds, the chat holds its
  composer, theme switches and data edits back, as for a theme render. The
  download is its own usage outcome, `downloaded_page`, which the telemetry
  views count as a download and a keep once they are re-created. A
  JavaScript version now lists five artifacts at most (two PNGs, the code,
  the page and the data), and the assistant names the button and the page's
  place in running `plot.js`. (#12480)
- **A probe of the page's boundary in the renderer image's CI.** It builds a
  Chart.js page with the image, wraps it with the agents' wrapper and opens it
  from `file://` in the image's Chromium: the chart drew and answers a hover,
  the frame's origin is `null`, and the plot code's attempts to set
  `top.location`, call `window.open` and `fetch`, read storage and cookies,
  and navigate its own frame to an http URL all fail. (#12480)
- **Chart.js, D3, ECharts and Highcharts in "Use with my data", for the
  admin's live tests.** `JavaScriptRuntime`
  (`agents/anyplot/render/runtimes/javascript.py`) serves the four libraries on
  the JavaScript code profile: `plot.js` renders through the renderer's
  JavaScript row, the catalogue's browser harness in its sandbox mode, and the
  page reads the user's table as typed JSON that Python writes from the
  canonical CSV (`RenderJob.data_json`), so the theme toggle renders the other
  theme from the same table. The admin deploy names the four libraries next to
  the eight served before, and each library's 80 % eval matrix gates the public
  release. Highcharts is served under its non-commercial licence (owner
  decision). When the typing changes a value, the first entries of the
  version's "what changed" list count the integers past 2^53, the timestamps
  cut to the millisecond and the timestamps converted to UTC, per column, and
  the plot's status stays its own. The PNG and `plot.js` download now; the
  interactive `plot.html` the code file's header names comes in the next step.
  (#12479)
- **A JavaScript adapter prompt.** `adapter_javascript.md` fills the shared
  adapter prompt's slots for JavaScript: the placeholder
  `const data = loadUserData();` and how the table is typed, column constants
  read as `d[COL]`, the protected token lines and orientation directive, `null`
  dropped before any conversion or statistic, a number formatter for every
  library's value axis that writes the plot language's marks, time axes kept in
  UTC so an exported page shows the same dates in every time zone, and Chart.js
  dates on a category or linear axis, since the page has no date adapter. A
  test runs its idioms through both validator profiles for each library, and an
  image test renders them from a table with missing cells. (#12479)
- **JavaScript eval fixtures.** The ten matrix specs for Chart.js, D3, ECharts
  and Highcharts (240 cases, 720 generated in all) with one smoke case each;
  the eligibility sweep covers the four libraries (none `clean`; 306 of 321
  Chart.js, 311 of 325 D3, 311 of 325 ECharts and 310 of 323 Highcharts files
  eligible). (#12479)
- **Agent telemetry: why a run needed its attempts, and with which configuration.** Each `pipeline_run` line
  now lists the stage that ended every attempt (`stages`, so adapter answers cut off at the output limit can
  be counted), the score bucket of every round, the readiness of the catalogue file, the kinds of cells the
  runtime's loader changed (`inexact`, `submillisecond`, `offset`, asked from the runtime), the edit-failure
  kinds and validator rule ids of its checks, the reviewer mode, ship-best and self-review settings, and the
  hashes of the adapter and reviewer prompts. Every token entry gains `thoughts`, the thinking part of
  `output`, which stays inclusive so the cost view and the older rows keep their meaning. All values come from
  closed sets pinned to their sources by tests; an unknown id is `other`, never a dropped line. The views get a
  typed column per field, an `attempts` view and `edit` and `validator` failure kinds. (#12477)
- **Agent telemetry: the review score joins what users do with the plot.** `pipeline_run` names the version
  it shipped (`version`, the number the page sends back with every outcome) and the shipped render's own score
  bucket (`shipped_score`). The new `score_outcomes` view lists every shipped version with its score, rounds and
  attempt stages beside the copies, downloads and reaction on exactly that version, the plots the session shipped
  before it, and the seconds from the first plot to the take-away, so the keep rate can be read per score bucket
  and library, once each session has ended. One limit, `MAX_AGENT_VERSION` (999), now bounds every version
  number the routes and the telemetry take. (#12477)
- **Feedback cases: the catalogue reviewer's prompt has its own hash.** The bundle's `prompt_hashes` gain
  `reviewer_catalogue`: `reviewer` hashed the checklist instruction only, so a change of the catalogue rubric the
  live reviewer runs changed no hash. Every case's combined `prompt_hash` shifts once with this release without any
  prompt changing; the cases before it are all admin test cases. The same deploy shifts three telemetry numbers a
  report sees: `language_source` reads the turn's own detection, `failures` gains the kinds `edit` and `validator`,
  and the fan-out's sessions leave `live` (`docs/reference/agent-telemetry.md`, "Shifts a report notices on
  2026-10-30"). (#12477)
- **Agent telemetry: the plot language, as a code.** `chat_turn` and `pipeline_run` record the session
  language as one of twelve codes or `other`, never the free-text value; the legal page names it. (#12477)
- **Agent telemetry: the admin's fan-out sessions are filed apart.** The sessions "plot in all libraries"
  opens carry `source = "fanout"` on every line, so the live numbers and the `/debug` card no longer count the
  owner's test sessions, none of which ever kept a plot. (#12477)
- **The JavaScript code profile for "Use with my data", not served yet.**
  `agents/anyplot/code/profiles/javascript/` reads Chart.js, D3, ECharts and
  Highcharts code with the pinned tree-sitter grammar for JavaScript and MUI X
  code with the one for TSX (the agents image now keeps both): the protected
  token lines that read the harness's `window.ANYPLOT_*` globals and the
  orientation directive, a normaliser that strips the header, writes one
  directive on the first line and blanks the catalogue title, a SECURITY and
  ADAPTATION validator that resolves scopes and admits a closed world of
  global names (the network, storage, frames, workers, `eval`, `Function`,
  `import()`, `require`, `.constructor`, string timers, elements that load,
  aliasing and computed access on `window`, `this` where it may be the window,
  keys built to spell `constructor`, protocol-relative URLs and writes that
  navigate or load a URL the code did not draw are refused, with the named
  bypasses as tests), MUI X imports checked against a copy of the renderer
  image's import allowlist that a test and CI compare with the image's, the
  readiness scan (93 clean, 1,456 coupled, 68 blocked; MUI X files written
  for 7.29 are coupled with a note naming the imports MUI X 9 lacks), the
  one-line loader `const data = window.ANYPLOT_DATA;`, and an error grammar
  that reads the harness's final error line without its message. The edit
  applier gains a JavaScript dialect (`//` and `/* */` comments, a `#` in a
  string stays text) and the export a `//` header that names the exported
  `plot.html`, with the other languages' output unchanged; the runtime, the
  prompts and the fixtures follow in JS-4. (#12473)
- **Render and unit tests for the palette, debug, and map sections.** Vitest
  suites under `app/src/sections/palette/`, `app/src/sections/debug/`, and
  `app/src/sections/map/` cover the components split out of `PalettePage`,
  `DebugPage`, and `MapPage`: the hue–chroma wheel, comparison palettes,
  snippet tabs, the WCAG swatch stroke per theme, the spec matrix headers and
  filters, feedback triage, and the map legend, hover panel, search pill,
  force weights, and canvas shell. The state that lives in the pages is tested
  on the real pages: `PalettePage.test.tsx` covers the swatch copy reset and
  the CVD sort order, and `DebugPage.test.tsx` the spec sort orders, the
  incomplete and low-score filters, and the feedback status PATCH with its
  revert. Every behaviour the review named was checked by breaking it on
  purpose and watching a test fail. (#12470)
- **A sandbox mode for the JavaScript render harness, not served yet.**
  `automation/js-render/render.mjs` gains switches that only the renderer's
  JavaScript row sets, so the catalogue pipeline renders exactly as before:
  `ANYPLOT_SANDBOX=1` aborts every request of the page, closes every WebSocket,
  blocks popups and WebRTC, adds a content security policy, renders in UTC and
  caps the page's memory; MUI X imports are closed to the image's allowlist, so
  a snippet can no longer bundle a file of the image; the console keeps the first
  five errors; and a failure ends stderr with one line naming the error's kind,
  class and line in the snippet. `ANYPLOT_NO_HTML=1` skips the interactive page,
  and `ANYPLOT_DATA_JSON` injects the table as `window.ANYPLOT_DATA`, typed by the
  service from the canonical CSV (`agents/anyplot/data/typed_json.py`) and carried
  by a new optional `data_json` field of the render request. Every catalogue
  JavaScript file that rendered before renders the same way in sandbox mode. The
  agent chat does not offer JavaScript yet. (#12466)
- **Node and Chromium in the renderer's toolchain image, not served yet.** The
  toolchain image (`agents/renderer/toolchain.Dockerfile`) gains a Node stage of
  its own: the official Node 22 build, the pipeline's major, checked against
  nodejs.org's SHA-256; the repository's `package-lock.json` installed with
  `npm ci --ignore-scripts`; and Playwright's Chromium headless shell alone, with
  the libraries it links and libgbm unpacked without Mesa and LLVM. The
  renderer's JavaScript row runs Node by its path (`/opt/node/bin/node`, never on
  the sandbox's PATH) on the catalogue's own harness, with Liberation fonts for
  that row alone, so the catalogue's Helvetica and Arial font stack resolves as
  on the pipeline's runner while Python's renders keep their fonts. The build
  derives MUI X's import allowlist from the installed packages' exports maps, for
  the harness's sandbox mode and the code profile that come next. 1,565 of the
  1,617 Chart.js, D3, ECharts, Highcharts and MUI X catalogue files render in the
  image unchanged (wall p95 2.4 s at 2 CPUs); the 52 that fail are MUI X files
  written for 7.29. The image build, CI and the deploy's candidate smoke each
  render through the row; the agent chat does not offer JavaScript yet. The
  images grow by 565 MB. (#12465)
- **Makie in "Use with my data", for the admin's live tests.** `JuliaRuntime`
  (`agents/anyplot/render/runtimes/julia.py`) serves Makie on the Julia code
  profile: `plot.jl` renders through the renderer's Julia row in exec mode
  under the preloaded exec filter, with the precompiled depot and the
  precompile workload, and the export downloads as `plot.jl` with `julia
  --project=. plot.jl` in its header. The admin deploy names Makie next to the
  six Python libraries and ggplot2, and its 80 % eval matrix gates the public
  release. ADAPTATION refuses a working form that keeps a dataset package
  (RDatasets, PalmerPenguins). When the loader cuts a timestamp's digits below
  the millisecond, which Julia's `DateTime` cannot hold, the first entry of
  the version's "what changed" list names the columns and counts the cells,
  and the plot's status stays its own. A scripted identity adaptation of the
  smoke fixture renders 3200x1800 in both themes through the local Docker
  backend in about 5.7 s with `exec_deny: on`. (#12464)
- **A Julia adapter prompt.** `adapter_julia.md` fills the shared adapter
  prompt's slots for Julia: the placeholder `df = load_user_data()` and how the
  loader types each column, column constants read as `df[!, COL]`, the
  protected statements, the packages the adapter may load, a number formatter
  that writes the plot language's decimal and thousands marks, and what Makie
  0.24 refuses that the catalogue never meets (a date column with a missing
  cell, spans and bands on a time axis, text as `barplot!`'s x). A test runs
  its idioms through both Julia validator profiles, and an image test renders
  them. Python's prompt is unchanged, and its SHA-256 pin holds. (#12464)
- **Makie eval fixtures.** The ten matrix specs for Makie (60 cases, 480
  generated in all) with the smoke case `scatter-basic-makie-renamed`; the
  eligibility sweep covers Makie (325 files: 0 clean, 308 coupled, 17
  blocked). (#12464)
- **The Julia (Makie) code profile for "Use with my data", not served yet.**
  `agents/anyplot/code/profiles/julia/` reads Makie code with the pinned
  tree-sitter grammar for Julia (the agents image now keeps the R and Julia
  grammars): the protected regions, a normaliser that strips the header,
  blanks the catalogue title, saves into the working directory, renames
  the deprecated `resolution` keyword to `size` and sets only the save's
  `px_per_unit` for CairoMakie's rounding, the SECURITY and ADAPTATION
  validator that refuses by shape (process starts, file I/O, `ENV`,
  evaluation, reflection, native code, computed callees, string
  interpolation walked as code, a `using` allowlist) with the named
  bypasses as tests, the readiness scan (0 clean, 308 coupled, 17
  blocked), a `CSV.read` loader typed from the data's kinds that reads
  every integer exactly and turns timestamps into UTC through TimeZones.jl
  (the kinds count the cells below the millisecond that Julia truncates),
  and an error grammar that never quotes Julia's message. The edit applier
  gains a Julia dialect and the export the run line `julia --project=.
  plot.jl`, with Python's and R's output unchanged; the runtime, the
  prompts and the fixtures follow in the next step. (#12459)
- **The renderer's Julia row loads a precompile workload before every plot.** The
  toolchain image develops a small package, `AnyplotWarmup`, into its own copy of
  the Julia project and precompiles a `PrecompileTools` workload of the calls the
  catalogue's Makie files make most and of the agent's data loader (a typed
  `CSV.read`, datetimes through TimeZones, plots from DataFrame columns); the row
  loads it with `-L /opt/anyplot/toolchain/warmup.jl`, so `plot.jl` stays the
  program and its error frames and exit codes do not change. CSV, DataFrames and
  TimeZones invalidate much of Makie's precompiled code, so an adapted Makie render
  took 16 to 18 s locally at 2 CPUs; with the workload it takes 5 s, and catalogue
  files gain 6 to 63 %. The repository's `Project.toml` and `Manifest.toml` do not
  change; the images grow by about 100 MB. (#12460)
- **Julia in the renderer's toolchain image, not served yet.** The toolchain
  image (`agents/renderer/toolchain.Dockerfile`) gains a Julia stage of its
  own: the official Julia 1.13.2 build, checked against julialang's SHA-256,
  and the catalogue's `Project.toml` and `Manifest.toml` precompiled into a
  depot, so the renderer runs the pipeline's Makie 0.24.16. The renderer's
  Julia row starts the launcher by its path under the preloaded exec filter
  with `--compiled-modules=strict`: a package image that does not load fails
  a render in about a second instead of compiling for minutes under its
  timeout, which the image build, CI and the deploy's candidate smoke each
  check with a Makie render. The agent chat does not offer Makie yet.
  TimeZones.jl becomes a direct dependency of the Julia project, for the
  loader that turns datetimes with offsets into UTC. (#12455)
- **ggplot2 in "Use with my data", for the admin's live tests.** `RRuntime`
  (`agents/anyplot/render/runtimes/r.py`) serves ggplot2 on the R code profile:
  `plot.R` renders through the renderer's R row in exec mode under the
  preloaded exec filter, the export downloads as `plot.R` with `Rscript
  plot.R` in its header, and the registry picks a runtime by the library's
  language. The admin deploy names ggplot2 next to the six Python libraries,
  and its 80 % eval matrix gates the public release. ADAPTATION refuses a
  working form that keeps a dataset package (gapminder, palmerpenguins), and
  when R reads integers beyond 2^53 as the nearest double, the first entry of
  the version's "what changed" list names the columns and counts the cells,
  so no value changes unannounced and the plot's status stays its own.
  A scripted identity adaptation of a fixture renders 3200x1800 in both themes
  through the local Docker backend with `exec_deny: on`. (#12448)
- **An adapter prompt per language.** `adapter.md` keeps the rules every
  language shares and names a slot wherever the code differs;
  `adapter_python.md` and `adapter_r.md` fill them. The R prompt teaches the
  placeholder `df <- load_user_data()`, column constants read through
  `.data[[...]]`, the protected statements, the packages the adapter may
  attach and what the validator refuses. The Python prompt is byte for byte
  the one before, which a test pins by its SHA-256. (#12448)
- **ggplot2 eval fixtures.** The ten matrix specs for ggplot2 (60 cases, 420
  generated in all) with the smoke case `scatter-basic-ggplot2-renamed`; the
  eligibility sweep and the development fixture seed find each library's
  files under its language (325 ggplot2 files: 4 clean, 306 coupled, 15
  blocked). (#12448)
- **The R (ggplot2) code profile for "Use with my data", not served yet.**
  `agents/anyplot/code/profiles/r/` reads ggplot2 code with tree-sitter
  (`tree-sitter` 0.26.0 and `tree-sitter-language-pack` 0.13.0, whose
  bundled grammars need no download; the agents image keeps only the R
  grammar, 0.6 MB of 184 MB): the protected regions, a normaliser that
  strips the header, blanks the catalogue title and sets only the save's
  dpi for ragg's truncation (all 325 catalogue files land on 3200x1800 or
  2400x2400), the SECURITY and ADAPTATION validator with the named
  bypasses as tests, the readiness scan (4 clean, 306 coupled, 15 blocked;
  a missing marker never blocks), a readr loader typed from the data's
  kinds, which also count the integer cells past 2^53 a double would
  change, and an error grammar that never quotes R's message. A denied
  name is refused where it can run (a callee, a function argument, a
  value outside a data mask), so a user's column called `source` or
  `file` passes. The edit applier and the export header now take the
  language as a parameter, with Python's output unchanged; the runtime
  and the registry entry follow in the next step. (#12443)
- **Google Jules takes short implementation tasks.** The new `jules-task`
  skill hands credential-free tasks that fit a roughly 30-minute cloud run to
  Jules through Google's official MCP server (`.mcp.json`, key read from
  `.env`). It covers single tasks against `main`, parallel sub-tasks of a
  `feature/*` branch, and best-of-N comparisons when the approach is open, and
  bundles a session watcher that flags empty PRs. The Ultra plan allows 300
  tasks a day, each counted once, so this work no longer costs Claude tokens.
  (#12429)
- **The renderer runs R plots in exec mode under the exec filter.** The R row of
  the command table starts R's own binary with `--file=plot.R` and the environment
  R's start script would set (UTF-8 locale included), and the harness preloads the
  exec filter into it: every program the plot starts is killed. A preflight starts
  R alone first and lets the plot run only when the filter took there, and a run
  whose filter did not report `on` is refused with exit code 3 as well
  (`RENDERER_EXEC_DENY=optional` stays the switch). Each row now says whether it needs the filter; only the
  JavaScript row, whose Node and Chromium start their own processes, has it off. The
  agents service does not send R jobs yet. (#12428)
- **The renderer builds on a toolchain image with R 4.6.1 and an exec filter for
  exec-mode runtimes.** `anyplot-toolchain` (`agents/renderer/toolchain.Dockerfile`)
  is `python:3.14-slim`, pinned by digest, with Posit's R 4.6.1 for Debian 13, the
  pipeline's ggplot2 package set plus readr as Package Manager binaries, and a
  preload library whose constructor kills every later program start before user
  code runs. The deploy builds and pushes it to Artifact Registry only when the hash
  of its inputs is new, and the CI job pulls it or builds it. The Python renders of
  all six libraries stay byte-identical; R is not served yet (step 2 of the
  all-libraries plan, revised after a second opinion). (#12423)
- **`.plot_all()` in the admin agent chat: one table, a plot in every library at
  once.** In step 2 the page replays the confirmed upload and bindings in a
  session per enabled library, without the summary turn, and runs their plots
  through the normal run queue, at most `AGENT_USER_MAX_RUNS` at a time, which
  `GET /status` now reports as `user_max_runs`. The results show as a grid of
  cards with each library's status, image and `.stop()`. (#12417)
- **"Use with my data" can adapt and render pygal and lets-plot.** The agent
  network's Python runtime (`agents/anyplot/render/runtimes/`) now serves the
  catalogue's pygal and lets-plot files next to matplotlib, seaborn, plotnine and
  altair. pygal saves through `render_to_png` and `cairosvg.svg2png` for the PNG and
  `render_to_file` for the HTML, whose target and file type the validator pins
  because libcairo writes the PNG past the plot guard; lets-plot saves through
  `ggsave` with `path="."`. The validator gains both import surfaces, keeps
  cairosvg's CSS stack unreachable, rules pygal's `css=`, `js=` and `defs=` config,
  and admits lets-plot's tooltip and label builders' `.format` with literal
  arguments. The normaliser rewrites pygal's HTML writes to `render_to_file`,
  expands lets-plot's star import from a static copy of `lets_plot.__all__`, removes
  its `lets-plot-images` epilogue, and sets both libraries' canvas, because R2's
  pixel cap refuses the catalogue's 4800x2700 PNGs outright; its four new guard
  rules and a new target form also lift plotnine from 264 to 267 and altair from 269
  to 273 eligible files. The plot guard imports cairosvg before it is armed and lets
  cssselect2 compile pygal's CSS selectors; the renderer image installs both
  libraries and libcairo, and lets-plot's row runs with its own 2048 MiB address
  space and Arrow's system allocator, which its native rasteriser needs. 209 of 325
  pygal and 284 of 325 lets-plot files are eligible. The eval fixtures cover both
  libraries: 120 more generated cases (360 in all) and one smoke case each (16 in the
  smoke set). `AGENT_LIBRARIES` keeps its default `matplotlib,seaborn` until each
  library's eval matrix reaches 80 %. (#12405)
- **The agent network's runtime seam for every catalogue language.** The renderer
  holds one fixed render command per language in `agents/renderer/commands.py`,
  keyed by the job's `(language, library)` and never taken from the request; the
  probe harness gains an exec mode (`harness.py --exec -- <command>`) that runs a
  non-Python command under the same limits, start and end lines, launcher retry and
  kill path; `GET /status` reports the toolchains the image carries and a job in a
  language without one answers `503 runtime_unavailable`. On the agents side a
  registry (`agents/anyplot/render/runtimes/runtime_for`) hands the pipeline, the
  theme toggle, the local backend and the eval harness one `RuntimeAdapter` per
  library, which now also carries the language's code conventions, error grammar,
  export and the render time a repair reserves; the exported code's artifact name
  follows the language (`plot.py`, `plot.R`, `plot.jl`, `plot.js`, `plot.tsx`)
  through the wire, the BFF, the feedback case and the result card. matplotlib and
  seaborn behave as before; the table's other rows wait for their toolchains.
  (#12404)
- **Phase-2 plan for "Use with my data" in all 15 libraries.**
  `agentic/specs/261024-agent-all-libraries.md` takes the agent network from
  matplotlib and seaborn to the other 13 catalogue libraries: a runtime registry
  in place of the hard-wired Python runtime, one fixed render command per language
  in the renderer, a harness exec mode for Node, Rscript and julia, the toolchains
  in the renderer image, a deterministic code profile per language, and seven PRs in
  order (the seam, plotnine and altair, pygal and lets-plot, R, JavaScript, plotly
  and bokeh, Julia). It records the spike measurements (the JS harness, the Python
  extras under the probe harness, plotly and bokeh, R and Julia in local Docker), the
  Fable second opinion and the owner questions with their defaults. (#12404)
- **"Use with my data" can adapt and render plotnine and altair.** The agent
  network's Python runtime now serves the catalogue's plotnine and altair files
  next to matplotlib and seaborn: a save rule per library
  (`agents/anyplot/code/regions.py`, `SAVE_RULES`) replaces the savefig rule in the
  regions, the normaliser, the readiness scan, the edits and the validator, so
  plotnine's `save` and `ggsave` and altair's `save` are the protected final save;
  the validator gains both import surfaces, parses plotnine's `aes` and facet strings
  as code, refuses `formula=` (patsy runs Python while it parses one), and admits
  altair's PIL padding block on the PNG only; the plot guard lets altair write its
  `plot-<theme>.html` inside the sandbox, where nothing collects it, and hands
  plotnine's `Environment.capture` the plot's frame. The renderer image installs both
  libraries, and the eval fixtures gain 120 cases for them. 264 of 321 plotnine and
  269 of 325 altair files are eligible; `AGENT_LIBRARIES` keeps its default
  `matplotlib,seaborn` until each library's eval matrix reaches 80 %. (#12404)
- **Adopt mode records who wrote the code: `source_model` on
  `impl-generate.yml` and `bulk-generate.yml`.** The optional input names the
  model that wrote an adopted implementation, such as `gemini-4-argon`, and
  becomes the metadata's `generated_by`; without it `generated_by` stays
  `adopted:<ref>`. Every adopted file's metadata also gets a new key,
  `adopted_from: <ref> (<sha>)`, so the source commit survives after the
  `gemini/*` branch is gone. The PR body's `**Generation:**` line, the adopt
  commit and the run notices name the model, and every retry forwards it like
  `source_ref`. The value is checked as a model name and ignored with a
  warning without `source_ref`. Both workflows now reject a malformed
  `source_ref` or `source_model` without echoing it, since a newline in a
  dispatch value would start a workflow command, and `bulk-generate.yml` does
  so before its first dispatch. (#12297)
- **Adopt mode for the implementation pipeline: `source_ref` on
  `impl-generate.yml` and `bulk-generate.yml`.** With it set, impl-generate
  takes the implementation file from that branch, tag or commit SHA instead of
  running Claude, renders it in both themes with the generator's commands,
  checks the canvas with `core.canvas`, and runs every later step unchanged:
  metadata, PR, staging upload, review, repair and merge. It exists so code
  written outside the pipeline, such as a `gemini/*` branch that migrates the
  323 MUI X implementations to MUI X 9, reaches main only through the Opus
  review, with metadata, quality score, GCS promotion and labels still owned by
  the pipeline. An adopted run is always a forced regeneration (`regen:forced`),
  the routed model only runs repair, the PR body and the metadata
  (`generated_by: adopted:<ref>`) name the source, and a missing file or a
  failed render is reported once without a retry, because a retry would read
  the same file. Python and JavaScript only for now. (#12274)
- **The adaptable-code convention in all 15 library prompts.** A new
  implementation keeps one replaceable `# Data` block that ends in a tidy
  DataFrame `df` (or a `tibble`, a Julia `DataFrame`, or JavaScript records),
  names each spec role once as a column constant with a `# role:` comment, lists
  all eight Imprint hues and uses the first `n`, and derives labels, callout
  targets, and limits from the data below the block. People who copy the code
  and the "Use with my data" agent replace the block and the constants, and
  nothing below them. Regenerations of R, Julia, and JavaScript pairs keep
  their regeneration rules, because only Python has a checker so far. (#12261)
- **A Python self-check before every generation commits (Step 3c).**
  `python -m core.smoke_run selfcheck` runs the static adaptability check and
  the perturbation smoke run on the new file, up to three attempts. It never
  blocks the commit, and the commit body records the result, so a first
  generation that still fails merges and converts on its next regeneration.
  (#12261)
- **A record-only smoke run and a predecessor render in `impl-generate.yml`.**
  The step "Adaptability smoke run (record-only)" runs the smoke run on the
  generated file and, on a regeneration, on the predecessor too. It renders both
  sources in the same runner and stages the results and the raw renders under a
  private `adapt/` prefix in GCS staging, which `impl-merge.yml` never promotes.
  `impl-repair.yml` reruns the smoke run after every repair. Identity is measured
  on the raw renders, before the PNGs are quantized. (#12261)
- **A record-only adaptability step in `impl-review.yml`.** The step
  "Adaptability check (record-only)" runs the checker mirror on both sources
  and reads the staged smoke results. It writes one record per source and an
  `adapt_check` notice per side, and it never fails the run. The reviewer never
  sees it, and the review prompt and the rubric are unchanged. (#12261)
- **The adapt route and the adapt regression in the regen gate.** A
  regeneration that converts a Python implementation to the convention now
  merges on render identity, without a visible improvement, when all of these
  hold: the predecessor fails the check and the new source passes it, the two
  renders differ in at most 0.5 % of their pixels in both themes at equal size,
  the new source stays within max(1.25 × prev, prev + 15) lines, and the review
  keeps every technical item at or above its re-score. The reason code is
  `adapt_identity`, and the gate record gains an `adapt` block. A conversion
  that breaks the check (the predecessor passes, the new source fails) is kept
  as `adapt_regression`, on every spec, so converted code stays converted.
  `regen_gate.py adapt-route` evaluates the route before the review. The
  repository variable `ADAPT_REVIEW_FREE` lets identical conversions merge
  without a review. It is off until the owner turns it on. The label
  `regen:adapt` counts the merges on which the route held through the review,
  and `regen:adapt-overruled` counts the PRs whose route held before the review
  and that the review turned off. (#12261)
- **Adaptability checker for Python implementations.** `core/adaptability.py`
  checks a source against the adaptable-code convention
  (`docs/concepts/adaptable-code.md`): one `# Data` block that ends in `df`,
  one column constant per spec role, no sample literals below the block, and
  the full Imprint palette when a role colors the marks. It writes at most one
  CQ-01 `(code)` line per rule class, and classes under 90 % precision on a
  judged sample of 30 are advisory. `python -m core.adaptability report plots/`
  prints the catalogue baseline, and `automation/scripts/adaptability_check.py`
  is its generated single-file mirror for the workflow runner. The pipeline
  does not run it yet, so this changes no score and no workflow. (#12244)
- **Perturbation tables and render identity for the smoke run.**
  `core/perturbation.py` builds the tables the smoke run swaps into the block
  (renamed columns and categories, one more and one fewer group, a single group,
  a tenth and ten times the rows, scaled values) and the source to run on each.
  `core/render_identity.py` measures the share of differing pixels between two
  renders against a bound. (#12244)
- **Dependabot watches the JavaScript render harness.** The root `package.json`
  (Chart.js, D3, ECharts, Highcharts, MUI X) gets weekly grouped minor and
  patch PRs; a major arrives as its own PR, because it changes the API the
  library prompt describes. Playwright and esbuild get a group of their own,
  so a Chromium change never rides along with a chart-library bump. (#12240)
- **A browser check that the site renders, before and after every merge.**
  `scripts/site-smoke.mjs` loads the home page, `/plots` and a spec page in
  headless Chromium and fails on a JavaScript error or an empty page. The
  app-image CI job runs it against the built container, so a dependency bump
  that breaks the boot fails its PR, and a new rule in `CLAUDE.md` (with the
  recipe in the `open-pr` skill and the Dependabot batch command) runs it
  against production after every merge. On 2026-10-22 a vite bump passed
  every check and left every page blank for about 45 minutes. (#12236)
- **Gemini takes coding tasks through `gemini`-labelled issues.** Claude
  writes the task as an issue. The owner works it with Gemini 4 Argon in his
  interactive agy session, in a separate clone with pushing disabled. Claude
  then reviews the branch and ships it as a PR (`/gemini-task`). Gemini's quota
  does the implementation, while credentials and every outside write stay with
  Claude. (#12223)

### Changed

- **The agent chat answers short and asks only when it matters.** The root's new "Replies" rules lead with the
  result in two or three sentences, keep every notice the data rules require (the loader's "reads", "keeps time"
  and "converts" lines, data changes with their counts, `requested_not_found`, refusals and limits), ask a
  question only when the turn cannot go on without it or the answer changes the data or the plot materially, close
  with no offer, and act on the user's answer in the same turn: "the scores are out of 100" now sets the axis to 0
  to 100. On seven chat scenarios from the user test of 2026-11-01, questions per reply fell from 0.75 to 0 and the
  words per reply from 58.7 to 50.4 on average (plot replies from 50 to 37). The version's "what changed" notes are
  written in the language the user chats in, also when the plot keeps another one, and in plain words, without
  the code's own names such as `load_user_data()`.
  (#12506)
- **The agent chat's plot follows the site theme.** On the dark site the
  first render of each plot version is now dark, and on the light site it is
  light. The other theme is still one click away on the light and dark switch,
  and each version still takes one render. The page sends the theme the site
  shows with every turn (`POST .../messages?theme=`). The query parameter lets
  the page, the API and the agents service deploy in any order. A change made
  after a site-theme switch follows the switch. A theme the user asked for in
  the chat holds for later changes of that plot. The admin fan-out
  (`.plot_all()`) plots every library in the same theme. This fixes user test
  E2 of 2026-11-01, where the dark site showed a bright plot card. (#12505)
- **`.plot_all()` plots the confirmed data, whatever its origin.** The admin
  fan-out of the agent chat (`/debug/agent`) has the agents service copy the
  page session's confirmed current data version into each library's session
  (`POST /v1/sessions/{sid}/dataset/copy`), byte for byte with its bindings,
  their confirmation and the session language, instead of posting the paste
  again. A table the assistant changed or computed (`sin x cos x`) now fans
  out too, and every library plots exactly what was confirmed. Both sessions
  must be the caller's, the target a fan-out session without data, the source
  confirmed; a copy parses and judges nothing again, counts as no paste, and
  has a per-user limit of its own. While the panel is open the data card
  waits, so every library copies the same confirmed data. The page falls back
  to posting the paste again while the server has no copy route. (#12501)
- **Pipeline-only implementation PRs start no CI runs.** The five CI workflows
  skip a PR that changes only `plots/*/implementations/**` and
  `plots/*/metadata/**`: GitHub holds the runs of a PR that the pipeline opens
  with `GITHUB_TOKEN` for an approval that never comes, and they ended as a red
  `failure` at the merge without having checked anything. (#12499)
- **The scope judge's example of another library is Excel.** "Gibt es das
  auch in Plotly?" stood for a library the assistant does not adapt; plotly is
  served now, and so is every catalogue library. (#12490)
- **Every profile's URL rule refuses a protocol-relative URL.** The Python, R
  and Julia validators refuse `//host/...`, `ws://`, `wss://`, `blob:` and
  `javascript:` in a string, as the JavaScript one has since JS-3; no catalogue
  file of a served library changes its outcome. (#12490)
- **The PR watchers end on their own.** `watch-deploys.sh` exits 0 with
  `no deploy for <sha>` once 6 polls (about 3 minutes) have found no build
  for a merge whose paths trigger nothing, instead of waiting 30 minutes, and
  exits 2 at once when `gcloud builds list` fails, so a lapsed login never
  reads as "no deploy". `watch-checks.sh` waits 90 polls, about 45 minutes,
  because a PR that builds the renderer image takes 30 to 40, and its
  `TIMEOUT` line names the checks still pending (#12493).
- **The agent rules and skills carry what the 2026-10-31 session retro
  measured.** `CLAUDE.md` adds a delegate stall check (about 30 minutes with
  no commit and no message, and a re-check of every delegate after a context
  compaction), makes a permission-classifier denial final for every agent of
  the session, and puts the first Copilot review at about 5 minutes. The
  `open-pr` skill gains a hadolint gate for the Dockerfiles, tests for new
  code before the PR opens, the 16 real check names, the GraphQL request for
  a further Copilot round, a `git pull --ff-only` of the shared checkout after
  a merge, and a report of worktrees whose branch is gone. `zweitmeinung`
  attaches a diff over about 60 KB instead of inlining it, documents how
  `--attach` resolves paths, and states the measured Gemini costs. Gate
  commands name ruff's `dev` extra (`uv run --extra dev ruff …`), which a
  fresh worktree lacks (#12493).
- **Recipes that lived only in chat are documented.** The single-library
  `impl-generate.yml` dispatch with its optional inputs
  (`docs/workflows/overview.md`), the eval-matrix forms real runs use
  (`agents/README.md`), and the export, edit and import route for a
  second-generation Cloud Build trigger, whose `update github
  --included-files` fails with `INVALID_ARGUMENT`
  (`agentic/docs/project-guide.md`) (#12493).
- **The eval pacing text follows the raised Haiku quota.** The owner raised
  the project's Claude Haiku `eu` overrides on 2026-10-31 to 150 requests,
  1,000,000 input tokens and 200,000 output tokens a minute (from 30
  requests); the agents README, the design doc and the scope and prep evals'
  docstrings say so, and why `--calls-per-minute` keeps its default of 25.
  (#12482)
- **The local Docker backend runs the checkout's browser harness.** A
  JavaScript render or page build mounts `automation/js-render/render.mjs`
  over the image's, as the backend mounts the checkout's `harness.py`, so a
  local run uses the harness under development. (#12480)
- **The agent chat's local mock serves JavaScript versions.** With a
  JavaScript library in `AGENT_LIBRARIES`, `app/scripts/agent-bff-mock.mjs`
  answers `plot.js` and a wrapped `plot.html` per theme, so the download can be
  driven in a browser without the services; it also accepts the cards' usage
  beacon. Its other answers are unchanged. (#12480)
- **The renderer deploy's Chart.js smoke is a gate.** A failed Chart.js render
  of the candidate revision now refuses the promotion, as the Makie render
  does, and the smoke's page reads its table from the job's typed JSON, the
  path every agent job takes. (#12479)
- **The scope judge's example of another library is MATLAB.** It was "this
  plot in JavaScript with Chart.js", which the chat now adapts. (#12479)
- **The assistant names the time-zone notes of every language.** A "what
  changed" line that says R, Julia or JavaScript converted timestamps with an
  offset to UTC is now named in the reply, like the other loader notes.
  (#12479)
- **A loader note never passes the 200-character limit.** With very long
  column names and many changed cells, the first column's name in a note is
  now cut with an ellipsis instead of failing the result. (#12479)
- **`.plot_all()` in the admin agent chat is chosen in the library selector.** An
  `all` pill after the header's library pills turns the composer's create action
  into `.plot_all()`, which replays the confirmed table in every library at
  once; the separate row under the composer is gone. While `all` is pressed the
  page's own session stays the data session; in step 2 the message box waits,
  since the fan-out takes no typed text, while the chat about the data in step 1
  goes on. Any library pill turns `all` off again. Data the assistant changed or
  computed keeps `.plot_all()` disabled, with a line that says why. (#12478)
- **The agent's adapter may think and answer up to about 50,000 tokens.** In the
  Makie eval matrix, 9 of 139 adapter calls stopped at the old cap of 16,384
  tokens with nothing written: each had spent the whole cap thinking, while the
  finished calls thought up to 14,315 tokens. Each such call cost a repair round.
  The Claude adapter's output cap is now 40,960 tokens for edits and for full
  files, with its 8,192 tokens of thinking room on top (49,152). The Vertex
  client sets its own 300-second timeout, because the Anthropic SDK refuses a
  non-streaming request that large otherwise. An answer that needs fewer tokens
  costs and takes what it did before; the root and the reviewer keep their caps.
  (#12475)
- **Gemini reviews its own finished work before it hands over.** In the
  `gemini-task` skill, Gemini starts one fresh subagent as a reviewer once a
  task, single or in packages, or a review round is done. The reviewer sees
  only the brief's Constraints and Acceptance and the diff, reads the whole
  diff for defects, and runs the mutation table plus
  breaks of its own. Gemini fixes the findings that hold up and lists every
  finding in a new `## Self-review` section of the PR body, as fixed or
  declined. Claude's independent Opus review stays, because a reviewer of
  the same model shares the author's blind spots. The owner's reason: code
  quality comes before saving tokens. (#12476)
- **Gemini test tasks prove what their tests catch.** In the `gemini-task`
  skill, a test brief names the files where the behavior lives and carries a
  mutation table in Acceptance: one deliberate break per behavior that must
  turn a test red, and one harmless refactor that must stay green. The review
  subagent runs the table and adds breaks of its own. Larger findings go back
  as a review round, one PR comment with a section per package; Gemini works
  the independent ones in parallel on `gemini/<slug>-r<n>-<k>` branches from
  the task branch and merges them back. In the first parallel run, the section tests passed every
  gate while two of three packages tested copies of the page logic instead of
  the pages. Cleanup now asks before deleting package branches, as
  `CLAUDE.md` requires. (#12474)
- **The agent chat announces timestamps it shows in UTC.** The parser keeps a
  column's one time-zone offset (a column with several is written in UTC with a
  note of its own), and R's and Julia's loaders read a timestamp with an offset
  in UTC, so a plot showed `08:00+01:00` as 07:00 without saying so. The instant
  stays exact, but the clock time moves. Such cells now appear in "what changed",
  counted per column, in the same words for R and Julia ("R converts 4
  timestamps with a time-zone offset to UTC, so the plot shows their UTC clock
  time: 3 in 'Ankunft', 1 in 'Abfahrt'"). `Z`, `+00:00` and a timestamp without
  an offset keep their clock time and are not counted. The status stays as the
  render earns it, as with the other loader notes. The JavaScript runtime will
  use the same count and wording. (#12468)
- **The JavaScript harness reads its packages from `ANYPLOT_NODE_MODULES`.**
  `automation/js-render/render.mjs` keeps finding `node_modules` two levels above
  itself in a checkout, so the pipeline renders as before; the renderer image,
  where the harness sits elsewhere, names the directory. `package.json`,
  `package-lock.json` and `automation/js-render/` join the toolchain's hash, the
  build context and the CI image job's change filter. (#12465)
- **Gemini works independent packages in parallel, in one PR.** When a brief
  task has two or more packages marked `independent`, the `gemini-task` skill
  has Gemini in the owner's agy session start one agy subagent per package, at
  most eight at a time, each in its own Git worktree on its own
  `gemini/<slug>-<k>` branch. Gemini then merges the package branches into
  `gemini/<slug>`, runs the gates on the result, and opens one draft PR with
  one changelog fragment for the whole task; coupled packages still run one
  after another. One start line, `/gemini-task <slug>`, covers every package.
  `/teamwork` is ruled out for this repository because it builds outside it,
  without branches or PRs. The agy permission rules gain the `git -C <clone>`
  forms and the coordinator's `git merge --no-ff`, and the repository no
  longer calls a 2026-10-16 forum reply a Google staff reply. (#12462)
- **PalettePage split into sections.** `PalettePage.tsx` shrinks from 1,783 to
  144 lines: its colour helpers, sub-components (`ChromaWheel`, `CodeBlock`,
  `DeltaEMatrix`), and eight numbered sections move into
  `app/src/sections/palette/`. The page keeps only state, effects, memos, and
  layout, and renders the same markup as before. (#12463)
- **agy works without a prompt for every command.** The `gemini-task` skill
  ships `agy-permissions.json`, the permission rules for the owner's agy
  settings, with a one-line merge for a new machine: the toolchains, file
  tools, local Git, pushes to `gemini/*` branches, GitHub reads, and Gemini's
  own draft PR run without asking; cloud CLIs, network downloads, history
  rewrites, other GitHub writes, `chmod`, and writes to the brief folder are
  denied. (#12461)
- **DebugPage and MapPage split into sections.** `DebugPage.tsx` shrinks from
  1,853 to 541 lines: its KPI grid, charts, tables, and feedback blocks move
  into `app/src/sections/debug/`. `MapPage.tsx` shrinks from 1,291 to 265
  lines: its selection, search, and resize logic moves into hooks with tests,
  and the canvas, legend, hover panel, search pill, and weights panel into
  `app/src/sections/map/`. Both pages render the same markup as before.
  PalettePage stays as it is for now. (#12457)
- **Gemini tasks as brief files instead of issues.** Claude now hands work to
  Gemini in the owner's agy session as a read-only brief in
  `~/projects/anyplot-briefs/`, outside both checkouts; a `gemini`-labelled
  issue is written only when the owner asks for one. The owner starts a task
  with `agy-work` (a shell function the `gemini-task` skill documents) and
  `/gemini-task <slug>`. Large work is cut into packages of at most 20 to 25
  files, each in a fresh session with mechanical convention checks in its
  Acceptance. Claude reviews against the brief, never against Gemini's PR
  text. (#12458)
- **The agents service runs on 1 vCPU and 2 GiB.** `anyplot-agents` was sized
  at 2 vCPU and 4 GiB when it still hosted the sandboxes; over the 14 days to
  2026-10-29 its hourly p99 peaked at 0.46 of a core and 370 MiB, since it
  mostly waits on the model and the renderer. 2 GiB keeps headroom for the
  worst case of about 1.1 GiB (the dataset and render stores' 256 MiB caps, a
  1 MB paste's parse and the PNG gates), because an out-of-memory kill would
  lose every session in memory. The renderer stays at 2 vCPU and 4 GiB. (#12456)
- **The renderer deploy runs on 8 vCPUs with a registry layer cache.**
  `agents/renderer/cloudbuild.yaml` runs on `E2_HIGHCPU_8` with an hour's
  timeout and builds a missing toolchain with BuildKit's registry cache, so a
  change to one toolchain no longer rebuilds the others; `Project.toml` and
  `Manifest.toml` join the toolchain's hash, the build context and the CI
  image job's change filter. (#12455)
- **Stop a Jules session before closing its PR.** The `jules-task` skill now
  tells the session to stop before Claude closes a losing or duplicate PR:
  closing a PR wakes its session, and on 2026-10-29 one pushed a new commit
  and recreated its deleted branch. (#12438)
- **SEO router reuses the shared display-name maps.** `api/routers/seo.py`
  imports `LANGUAGE_NAMES` and `LIBRARY_NAMES` from `core.constants` instead
  of deriving its own copies, so exactly one derived name map exists.
  (#12419)
- **Per-route page metadata uses React 19 native hoisting.** Pages render
  bare `<title>`, `<meta>` and `<link rel="canonical">` elements instead of
  wrapping them in `react-helmet-async`, which is archived upstream; the
  dependency and its `HelmetProvider` are gone. The `/plots` title is now
  declarative too and keeps the route name next to the active filters
  (`lib:matplotlib | plots | anyplot.ai`); `useUrlSync` no longer writes
  `document.title`. (#12424)
- **Delegation lanes after the first Jules test.** The delegation rule in
  `CLAUDE.md` and `.claude/guardrails.md` now gives Sonnet a narrow lane for
  bounded work a command verifies, sends ~30-minute implementation to Jules
  and larger steps to `/gemini-task`, and runs Fable plus Gemini 4 Argon only
  when the owner asks for a second opinion. Claude merges Jules's sub-PRs into
  a `feature/*` branch it leads; every merge into `main` stays with the owner.
  The guardrails record the Gemini 3 Pro against Flash comparison that made
  Flash the Jules model. (#12429)
- **Gemini Flash checks every code PR before it opens.** `/open-pr` now runs
  `/zweitmeinung` with Gemini 3.8 Flash on the branch diff before a code PR
  opens, so Copilot's single round ideally finds nothing. Diffs made only of
  docs, instruction files, changelog fragments, or `plots/`, and diffs under
  about 20 lines, skip it. (#12429)
- **Lint and tests run on pull requests into `feature/**`.** `ci-lint` and
  `ci-tests` now also run for PRs into a feature branch, so every Jules
  sub-PR is checked before Claude merges it. Image builds, migrations,
  CodeQL, and the changelog check stay on PRs into `main`. (#12429)
- **A 1-D NumPy array converts to one column.** "Use with my data" used to refuse a
  plain 1-D `.npy` array as `file_array_shape`; it now becomes one column, `value`,
  which is what a histogram, a box plot or a line over the index needs. An `.npz` of
  two or more plain 1-D arrays of one length, which is what
  `np.savez(path, t=t, y=y)` writes, becomes one table with a column per array named
  after it; scalars saved next to them are left out and named. Any other `.npz` is
  still read one array at a time: a 2-D or structured array before a 1-D one. Still
  refused are 0-D arrays, arrays of three or more dimensions and structured arrays of
  more than one. (#12413)
- **The agents deploy serves all six Python libraries.** `_LIBRARIES` in
  `agents/cloudbuild.yaml` now names plotnine, altair, pygal and lets-plot next to
  matplotlib and seaborn, so the admin can test each one in the live chat; only the
  admin reaches the chat yet. Each library's 80 % eval matrix now gates the public
  release. `AGENT_LIBRARIES` keeps its default `matplotlib,seaborn`. (#12410)
- **R2 refuses a render as blank only when 99.7 % of it is one colour, not 98 %.**
  The agent network's blocking PNG check (`agents/anyplot/render/png.py`) refused
  sparse but complete charts: 33 of the 195 eligible pygal renders and lets-plot's
  point-basic (98.38 %) are 98 % one colour or more, the sparsest pygal one 99.44 %.
  A bare canvas (99.93 %) or a title alone (99.78 %) still fails. The cutoff holds
  for every library, and it refuses nothing the old one accepted. (#12405)
- **`impl-review.yml` runs on the pinned Python.** A setup step reads
  `.python-version` before the first regen tool runs, because the regen gate,
  the provenance script, and the checker mirror use PEP 758 `except A, B:`
  since the move to Python 3.14, and the runner image's own Python is not
  pinned. `impl-merge.yml` now promotes only the `plot-*` files from staging,
  so the private `adapt/` artifacts never reach production. (#12261)
- **Python 3.14 everywhere.** The project floor (`requires-python`), the pinned
  interpreter (`.python-version`, 3.14.9), mypy's target, every workflow's
  `setup-python`, the three service images (`python:3.14-slim` for the API,
  the agents service and the renderer) and the Python runtime the languages
  table reports move from 3.13 to 3.14. 3.13 receives security fixes only since
  October 2026, while 3.14 gets bug fixes until October 2027; 3.15 waits for a
  lets-plot wheel. `google-crc32c` moves from 1.7.1 to 1.9.0 in the lock, because
  1.7.1 publishes no cp314 wheel and the images carry no compiler to build it.
  The steps that ran repository Python on the runner's own `python3` (the spec
  check in CI, impl-merge's write-back, review-retest) now set up the pinned
  interpreter, because the code uses 3.14-only syntax. Rebuild a local
  `anyplot-renderer:dev` image after this change: the local renderer mounts the
  checkout's harness, which no longer parses on 3.13. (#12247)
- **MUI X implementations are generated against @mui/x-charts 9.16, React 19
  and @mui/material 9.5.** The pinned render stack in the root `package.json`
  moves up from @mui/x-charts 7.29.1, React 18.3.1 and @mui/material 5.18.0,
  matching the React and Material versions the frontend already runs.
  `prompts/library/muix.md` gains a "MUI X v9 API" section on the changes that
  break or silently restyle generated code: `ChartsContainer` instead of
  `ChartContainer`, `hideLegend` and the new legend position values, the HTML
  legend's extra height, `position: "none"` instead of `leftAxis={null}`, the
  per-chart CSS classes and `[data-series]`, and the line-mark defaults. The
  Sizing section adds that each axis needs an explicit `height` or `width` once
  its fonts grow, because v9 truncates tick labels that don't fit its band.
  The render harness itself needed no change. Existing MUI X implementations
  were written for v7: 164 of 323 no longer bundle under v9, and most of the
  rest render differently, so they need regeneration before they can be
  re-rendered. (#12243)
- **The spec role parser moved to `core/spec_roles.py`.** The agent and the
  checker now read a spec's `## Data` roles through one parser, which also files
  each spec as a table, matrix, network, generated or map spec and names its
  color-driving role. (#12244)
- **R implementations now render on R 4.6.1 with ggplot2 4.0.3.** The shared R
  setup action installs R 4.6.1 and pins the Posit Package Manager snapshot to
  2026-10-20 (was R 4.4.1 and 2025-01-15, ggplot2 3.5.1). The ggplot2 generator
  prompt gains a "ggplot2 4.0 notes" section for the changes that render
  differently without an error: label borders, binning edges, `theme_void()`
  borders, rotated top-axis text and legend order. All 325 ggplot2
  implementations still render in both themes; existing catalogue images stay
  as they are until an implementation is regenerated. (#12242)
- **The Julia render stack moves to Julia 1.13 and Makie 0.24.** The
  Manifest pins Makie 0.24.16 and CairoMakie 0.15.16, up from the 0.21.9 that
  the QRCoders dependency had forced in June: every QRCoders release caps
  ImageCore at 0.9, while Makie 0.21.10 and later need ImageCore 0.10.
  QRCoders leaves the environment, so qrcode-basic's Makie implementation
  needs a regeneration, and nyquist-basic, which crashed on 0.21.9, renders
  again. The setup action installs Julia 1.13, and the Makie generator prompt
  switches to `Figure(size = …)` and adds notes on the 0.24 APIs that changed
  (arrows, text alignment, layout gaps, and `heatmap!` on a `PolarAxis`,
  which renders a blank figure) (#12245).
- **Highcharts renders with 13.1.1 instead of 12.6.0.** The JavaScript render
  harness pins the latest 13.x release, which also carries the fixes for the
  2026-09 core security advisories (prototype pollution through `series.keys`,
  `javascript:` URLs in `credits.href` and exported markup). The generator
  prompt now pins `palette: { colorScheme: t.theme }`, because Highcharts 13
  takes every default color from CSS variables that otherwise follow the
  viewer's OS dark-mode setting in the interactive HTML. It also covers the
  13.x changes a before/after render of all 323 Highcharts implementations
  surfaced: the `dataLabels.distance` gap, legend symbols that take
  `series.opacity`, near-black default outlines in the dark theme, and the
  cropping of unsorted line data. Existing implementations stay as they are,
  and regeneration refreshes them. (#12246)
- **The frontend tests run on Vitest 5.** `vitest` and `@vitest/coverage-v8`
  in `app/` move from 4.1.11 to 5.0.5, which also resolves `@vitest/mocker`
  5.0.5, outside the range of the two open `@vitest/mocker` advisories. The
  suite needed no config or test changes: it still covers the same 117 files
  with the same 1,168 tests, and the production bundle is unchanged, since
  Vitest is a test-time dependency only. (#12249)
- **Adaptable-code rollout revised after a second opinion.** The design in
  `docs/concepts/adaptable-code.md` now merges a conversion on render identity
  (both sources rendered in the same runner, under 0.5 % of pixels differing
  per theme) instead of a one-point score tolerance, converts the catalogue
  through a capped targeted pass over matplotlib and seaborn instead of one
  spec a night across 15 libraries, drops the first-generation repair trigger
  that collided with the early `ai-approved` label, keeps the Opus review for
  the first 50 identical conversions, perturbs missing values only in the
  dtypes the agent's loader produces, and drops the `fill_value=0` pivot that
  invented zero bars. The
  reasons are recorded next to the owner's decisions of 2026-10-23, so the
  document stays the single source for PR 2. (#12239)
- **Copilot reviews a PR once; another round only while the previous one
  had high or critical findings.** `CLAUDE.md`, the `open-pr` skill and
  `/pull_request` replace "stop once a round yields nothing new", which let
  a round with any findings draw the next one, with the owner's rule of
  2026-10-23: a round with only low and medium findings gets its fixes
  pushed and its threads resolved, and that is the end, because every round
  re-reads the whole diff and costs premium requests. (#12250)
- **Library and runtime versions are read from the pins, never written by
  hand.** `core/library_versions.py` reads `uv.lock`, the root
  `package-lock.json`, `Manifest.toml`, `.python-version`, the setup actions
  and the R snapshot, and the database sync fills the Libraries page from it;
  `core/constants.py` carries no version any more. Ten of its fifteen numbers
  had drifted (matplotlib 3.9.0 against 3.11.2 locked, ECharts 5.5.1 against
  6.1.0), and a Dependabot bump now needs no edit. The library prompts' example
  headers carry no version; every prompt of a locked library (Python,
  JavaScript, Makie) states the API level it writes for, and a test holds it
  to the lock's major. CI now also fails when `uv.lock` is out of date with
  `pyproject.toml`. (#12240)
- **Merged branches are cleaned up locally too.** GitHub deletes a PR's
  remote branch on merge, but never the local copy, and 212 merged local
  branches had piled up by 2026-10-22. After a merge, Claude now removes the
  PR's worktree and local branch without asking (`CLAUDE.md`, the `open-pr`
  and `gemini-task` skills); unmerged branches still need the owner's OK.
  (#12238)
- **Gemini tasks after the first pilot.** The `gemini-task` skill now reads
  issues with `gh issue view --json` and updates PR bodies through `gh api`,
  because both bare commands fail on this repository; asks issue authors for
  cases where the existing rules must still win and for the files the gates
  couple; names the environment sync with the `agents` extra; and has Gemini
  hand over in the repository's PR format. The changelog check names a
  fragment that is on disk but not yet committed. (#12229)
- **Gemini second opinions run through Vertex AI, and Claude no longer runs
  agy.** Google's Antigravity FAQ and a staff reply of 2026-10-16 forbid
  running the Antigravity CLI from third-party coding agents under a consumer
  login, even read-only. The new `zweitmeinung` project skill calls Gemini
  through Vertex AI in project `anyplot` with read-only tools: Gemini 3.8 Flash
  on half-price Flex PayGo for first reviews of normal PRs, and Gemini 4 Argon
  for plans and second opinions. Its script inlines the diff and the changed
  files and reads several files per call, because every tool turn re-sends the
  whole conversation; unit tests pin its read-only confinement and tool loop.
  `CLAUDE.md` and `.claude/guardrails.md` describe the split and its measured
  costs. (#12226)
- **Gemini hands its work over as a draft PR.** In the `gemini-task` skill,
  Gemini pushes its `gemini/*` branch and opens a draft PR labelled `gemini`,
  so CI runs at once while Copilot waits; Claude reviews the draft and marks it
  ready. The owner may let Gemini run tests and builds unattended in his own
  agy session, and only he starts agy. (#12226)
- **Delegation runs in lanes.** The delegation rule in `CLAUDE.md` and
  `.claude/guardrails.md` now sends work by what it needs. Opus handles
  anything that changes state. Haiku only reads, polls, and creates Todoist
  tasks. Fable takes high-risk reviews. Gemini takes credential-free reading,
  first reviews, and implementation. Sonnet no longer has a lane in interactive
  sessions. The guardrails also record why headless Gemini implementation was
  dropped: agy's login is a project-owner token, Google front ends route by
  `Host` header, and proxying the token breaks the Antigravity terms. (#12223)
- **The data box says what it waits for.** While a dropped Parquet, Excel,
  OpenDocument, Feather or NumPy file is read on the server, and while
  `.parse()` runs, the box shows `# reading "x.parquet" on the server … · 4 s`
  or `# parsing your data … · 3 s` over itself: a pulsing `…`, a seconds counter
  and a thin bar along its foot. Before, only the buttons greyed out and a quiet
  line under them changed, so the page looked stuck for the several seconds a
  sandbox read takes. (#12221)
- **The agent chat's windows work in parallel; only their sandbox runs queue.**
  A paste, a chat turn, a data step (bindings, `.confirm()`, `.undo()`,
  `.to_long()`, the language, a library switch), the theme toggle and a file
  conversion in one browser window no longer answer `409 run_active` because
  another window of the same user renders a plot: every exclusion in the
  agents service is now per session (`Runtime.active`, `Runtime.pasting`,
  `Runtime.converting`), and within one session it stays one thing at a time.
  Plot runs and data snippets still share the run queue, at most three per user
  queued or running across windows (`AGENT_USER_MAX_RUNS`); a fourth ends its
  turn with the new stream error `run_limit`, which the page words as "you
  already have 3 plots or data runs in progress in other windows", instead of
  `capacity`. The per-user rate limits and daily budgets are unchanged (owner
  decision of 2026-10-21). (#12220)
- **Dependencies:** 14 Dependabot PRs. Security updates close 60 advisories, four rated
  critical and 32 high: `pillow` 12.3.0 → 13.0.0, a major version, with 39 of them and all
  four critical ones (#12230), `aiohttp` 3.14.3 → 3.14.4 (#12219), `virtualenv` 21.7.13 →
  21.14.9 (#12231), and in `app/` `vite` 8.0.16 → 8.1.6 (#12225), which left the site blank
  until #12235 moved it on to 8.3.5. The grouped python-minor bumps (#12213, #12233) carry
  `anthropic` 1.8.0 → 1.15.0, `mcp` 2.2.0 → 2.3.0, `fastmcp` 4.0.10 → 4.1.1, `pydantic`
  2.13.5 → 2.14.1, `asyncpg` 0.31.0 → 0.32.0, `ruff` 0.16.9 → 0.17.1, `mypy` 2.3.1 → 2.4.0,
  `bokeh` 3.10.0 → 3.10.1, `kaleido` 1.4.0 → 1.5.0 and `python-calamine` 0.8.3 → 0.9.0;
  `certifi` moves to 2026.10.19 (#12234). npm in `app/`: `@mui/material` 9.5.0 (#12161),
  React 19.3.1 (#12215), the react group (#12160) and two npm-minor groups (#12211,
  #12232). GitHub Actions: `claude-code-action` 1.0.240 → 1.0.254 and the setup-uv,
  setup-node, CodeQL and artifact actions (#12164, #12218).

### Removed

- **Google Jules lane.** Google announced on 2026-10-29 that Jules takes no
  new sessions after 2026-11-11 and shuts down on 2026-12-31, so the lane
  leaves `CLAUDE.md`, `.github/copilot-instructions.md`, and the guardrails,
  together with the `jules-task` skill and the Jules MCP server in `.mcp.json`.
  In its three test rounds Jules paid off only for work a command can verify:
  three of nine page-split variants kept their page unchanged. The checks that
  proved it (a jsdom snapshot with the existing test's mocks, a browser
  comparison against the production API) move into the `gemini-task` skill,
  where behaviour-preserving refactors go. The CI conditions that keep Jules
  and Dependabot PRs away from secrets stay until Jules stops taking sessions.
  (#12453)
- **The auto-update workflow for PR branches.** `auto-update-pr-branches.yml`
  merged `main` into every open PR with auto-merge after each push to `main`.
  The `main` ruleset's checks are not strict, so no PR needed it, and its
  merge commits, authored by `github-actions[bot]`, held each PR's CI at
  `action_required` until someone approved the runs by hand (eight times on
  one PR on 2026-10-22). Auto-merge now fires on the PR's own green head.
  (#12237)

### Fixed

- **A follow-up message no longer changes the plot's language.** In the live
  test of 2026-11-01 a German paste gave a German plot, and the English
  follow-up "Use a log scale on y" translated its title and number format while
  the axes and months from the data stayed German; "Make the title German"
  turned the assistant's replies German as well, where now only the plot's
  language changes and the replies stay English. The plot's text has its own
  language (`session_state.plot_language`): the language the user asked for the
  plot, else the language of the session's latest plot, else the session
  language. So the first plot follows the paste, the first typed message or the
  chip as before, and later versions keep it. The root's `set_language` takes
  `applies_to` (`plot`, `replies` or `both`, the default for a request that
  names no target), the chip sets both and now says it names the replies'
  language, and the admin fan-out copies the page's plot language. (#12504)
- **The agent's reply names the texts the plot draws, in all 15 libraries.**
  In the user test of 2026-11-01, replies for Chart.js, bokeh and pygal plots
  said the plot's title and labels could not be read back, and a Makie reply
  offered a title the plot already had. Only matplotlib, seaborn and plotnine
  reported their drawn texts. Now pygal, altair and lets-plot report them
  through the render harness; Chart.js, D3, ECharts, Highcharts, MUI X, plotly
  and bokeh through the browser harness; and ggplot2 and Makie through a text
  probe their renderer rows load, each by the library's own roles (title, axis
  labels, ticks, legend, annotations). The probes are best-effort: a failure
  drops the labels and is logged, never fails the render, and adds at most
  0.55 s (Makie). The requested-text check stays with the reviewer for these
  libraries, and G12 stays matplotlib's. (#12503)
- **A render without drawn texts no longer hands the root a `null`.** The
  root gets `shows` without `texts`, its prompt no longer mentions unread
  texts, and it never claims a text is absent from what `texts` leaves out.
  The eval report counts shipped runs without drawn texts per library
  (`untexted`), quotes in replies that no drawn text holds
  (`unbacked_quotes`), and failed probes. (#12503)
- **The agent chat asks before leaving drops the session.** A reload, a
  closed tab or a link off `/debug/agent` used to end the session unasked,
  with its data and plots, also after a 20-minute `.plot_all()` across 15
  libraries. While the session holds data, a table read from text, a plot or
  work in flight, the page now asks first: the browser's own `beforeunload`
  dialog for a reload or a closed tab, and a `confirm` from the router's
  blocker for a link inside the site or the back button. An empty session,
  the page's own query edits (a library pill, `all`) and the reload links
  after an expired session or no answer ask nothing. Sessions still live in
  memory only. (#12502)
- **The agent chat's URL follows the session.** A library switch writes the
  library's `language` next to `library`, so the query no longer reads
  `library=matplotlib&language=javascript`, and the header's `all` pill is in
  the URL as `&all=1`, which a reload presses again once the libraries are
  known. (#12501)
- **Regenerations re-apply the plot title format.** The regeneration prompt now lists the title format (`{spec-id} · {language} · {library} · anyplot.ai`) under "Base style wins" and in its final check, so a regenerated implementation re-derives the title from the current rule instead of carrying over a predecessor's title that lacks the `{language}` segment; an optional descriptive prefix the previous title had stays. (#12500)
- **The implementation tab shows the date of the last update.** The date under the strengths and weaknesses was the first generation date, so a regenerated implementation showed its original date next to a score and review from the latest run. It now shows the implementation's own last update date, falling back to the generation date and then the spec's creation date. (#12498)
- **The renderer deploys again, with plotly and bokeh.** Cloud Build refused the renderer's
  deploy for PB-2a before its first step ran, because the inline smoke step had grown to
  11,347 characters and Cloud Build accepts at most 10,000 per step argument; the agents
  service deployed and the renderer kept its previous revision. The render probes now live
  in `agents/renderer/deploy_smoke.sh`, which the smoke step calls with the token in the
  environment, a new unit test keeps every Cloud Build config's arguments under the limit,
  and `ci-tests.yml` runs the unit tests when a Cloud Build config or the smoke script
  changes. (#12497)
- **A plotly 3D plot no longer passes as a blank render.** The renderer's
  headless browser draws a 3D scene as nothing but its colour bar, without
  plotly's WebGL notice, and the host gates passed it. A figure with a WebGL
  trace now fails as `draw NoWebGL` before it is drawn, and the readiness scan
  blocks such catalogue files (15 plotly files) until the renderer draws WebGL.
  (#12490)
- **The unit tests run when an agent instruction file changes, and main is green
  again.** #12493 added the section "Long-running work reports progress
  proactively" to `.claude/guardrails.md` but changed no Python, so "Run Tests"
  skipped it and `test_every_companion_section_is_registered` failed on main.
  The section and the classifier-denial rule are now registered with their
  CLAUDE.md anchors, and `ci-tests.yml` also runs the tests for changes to
  `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`,
  `.claude/guardrails.md`, `agentic/docs/project-guide.md`, `.claude/skills/`
  and `agentic/commands/`, which
  `tests/unit/test_agent_instructions.py` and `tests/unit/skills` read. (#12494)
- **No user code runs while a render or data guard is paused.** The harness
  pauses its guard briefly to read a traceback or resolve a path, and code the
  snippet defined could run in that moment and write files the guard refuses:
  an exception class's own `__traceback__` property while a data run printed
  its traceback, and a path that subclasses `str` while a plot's file write was
  checked. The harness now reads the traceback through Python's own
  descriptor, copies a path to a plain string before the check, and compares
  only plain strings while paused. (#12484)
- **A plot can no longer run code of its own as an import.** The render guard
  trusted any code the import machinery ran, so a plot that drove it, with a
  loader of its own or a stock loader on a file it had written, ran a module
  body that read the guard's frames and switched it off. The guard now trusts
  an import only when the interpreter's own loader runs it, with its class as
  it was before the plot started, refuses every code
  read and every native module load outside the installed packages, and
  refuses changing the flags of the output it shares with the screenshot step.
  The plot validator also refuses the package-data reader, the import spec
  builders and the dynamic class builder that matplotlib's bundled dateutil and
  the standard library's `types` module hand out, found by a new walk over
  everything the validator admits. (#12484)
- **The eval matrix's preflight with a MUI X 7 file first.** The preflight
  rendered the catalogue file of each library's first case unchanged, and a MUI X
  file written for MUI X 7 fails the bundle step until the adapter rewrites it,
  so a selection starting with one (`scatter-basic-*`) stopped before any case.
  It now renders the library's first selected case whose file bundles as it
  stands, or, when none does (`scatter-basic-muix-*` alone), the library's smoke
  case, so the case that tests the rewrite can run on its own. (#12483)
- **The page probe hovers the plot, not a legend mark.** `page_probe.mjs`
  hovered the first canvas or svg in the plot's frame, which in a MUI X page is
  a legend entry's 10-pixel mark; it hovers the largest now. The renderer
  image's CI builds and probes a MUI X page next to the Chart.js one. (#12483)
- **The agent network's concept doc described Makie as not served.** The merge
  of the JavaScript toolchain step dropped the doc lines that served Makie;
  they are back, with the JavaScript runtime's. (#12479)
- **Agent telemetry: a turn records the language it set.** `language_source` was read before the turn ran, so
  the turn whose message the language was detected from, or that called `set_language`, recorded the value from
  before; the line now reads the session after the run. (#12477)
- **Gemini's parallel package agents can write in their worktrees.** agy
  creates each subagent's Git worktree under
  `~/.gemini/antigravity-cli/worktrees/`, and the agy permission rules denied
  Gemini's file tools the whole `~/.gemini` folder, so the first parallel run
  fell back to one package after another. `agy-permissions.json` now denies
  reads and writes for each entry of `~/.gemini` and
  `~/.gemini/antigravity-cli` by name, which keeps the agy login and settings
  closed and leaves only `worktrees/` open, with `regex:` rules for `cd` and
  `git -C` into it that refuse `..`. Pushes to `gemini/<slug>` no longer
  prompt: agy matches each word of a rule whole, so the old
  `git push origin gemini/` allow never matched a real branch, and a `regex:`
  rule replaces it. Force pushes and pushes to `main` are denied in every
  `git -C` form, and the push deny rules also match when agy compares a whole
  command against them. (#12467)
- **A failed Julia render lost the line that names its error.** Makie's stack
  traces run to 7,500 characters and more, so the 2,000-character stderr tail
  lost Julia's first `ERROR:` line and the repair read "an error (the tail cut
  off its first line)". The Julia row now keeps that line in front of the
  tail within the same 2,000 characters (`RuntimeCommand.stderr_head`), and
  every other row's tail is unchanged. The Julia error summary also names the
  line of the code the adapter edits, not the line of the code that ran, which
  the loader shifts by 15 lines and more. (#12464)
- **Render cancellation test waits longer and fails clearly.**
  `test_local_backend_kills_the_container_on_cancellation` waited at most 10 s
  for both fake theme containers and then cancelled anyway, so a loaded runner
  could fail with a misleading "only one container killed" assertion. It now
  waits up to 25 s and raises a clear timeout error when the containers never
  start. Written by Google Jules; the race could not be reproduced locally.
  (#12449)
- **One title and description per page.** The SPA shell in `app/index.html`
  kept its default `<title>`, description, and Open Graph and Twitter tags
  after a page rendered its own, so every route carried two of each and the
  shell's description came first. The six defaults are now marked
  `data-shell-default` and step aside only while a page renders a tag of the
  same kind (`watchShellDefaults` in `app/src/main.tsx`), so they still serve
  clients without JavaScript, a route whose chunk is loading, the error
  boundary, and pages without a description of their own; `/debug` has its
  own title. Built from the better of two Google Jules variants, measured on
  the built pages; the other deleted the shell defaults outright. (#12442)
- **A plot without a text probe that showed the requested text still needed attention.**
  R, altair, pygal and lets-plot write no probe, so the agent chat could not
  check a text the user asked for, such as a title or an axis label, and every
  such request shipped as `needs attention` with "the requested texts could not
  be checked", although the image showed the text (ggplot2 live test of
  2026-10-29). The reviewer now checks these texts in the image, in the review
  call it already makes (owner decision of 2026-10-29). Only a render without
  drawn texts on a library that opts in (`RuntimeAdapter.review_texts`) sends
  the texts to the reviewer, so the reviewer prompt and every review request of
  a matplotlib, seaborn or plotnine render stay unchanged. The reviewer reports
  a text it cannot find as an `SC-04` line that quotes it (`SC-02` for a number
  format), and the pipeline handles that line like the probe's miss: under
  `AGENT_EXPECT_CHECK=repair` it sends the round to the repair whatever the
  points, and if no round fixes it, the plot ships with the line and the text in
  `requested_not_found`. The "could not be checked" note now appears only when
  no readable review answered for the texts. (#12454)
- **The scope judge refused served libraries as another library.** Its
  rubric named matplotlib and seaborn as the only libraries the assistant
  adapts, so this plot in plotnine, altair, pygal, lets-plot or ggplot2, all
  served to the admin, could get the `other_library` pointer. The rubric now
  gets the served libraries from `AGENT_LIBRARIES` and the catalogue's others,
  grouped by language, and a question about the session's code is in scope in
  any served language. The fixed `other_library` reply names the served
  libraries in each of its eleven languages instead of "only in Python, with
  matplotlib or seaborn". The adapter prompt's sentences that only matplotlib's
  probe makes true moved into the Python passages, so the R prompt says that
  the host gates judge an R render without a probe. (#12448)
- **Agent result code highlighted in the wrong language.** The result card
  highlighted every version in the page's current language, so after a
  library switch a matplotlib version showed as R; it now takes the language
  of the version's own library. (#12448)
- **The renderer deploy builds its toolchain again: R survives a killed child on
  older kernels.** The first deploy of the toolchain image failed in its R check
  with "Bad system call": the exec filter kills the child R's `popen` and
  `system()` start with `vfork`, and before Linux 5.16 that child's core dump
  killed every process sharing its memory, R included. The preload library now
  makes the process non-dumpable before it installs the filter, so the child dies
  alone on every kernel. (#12427)
- **The eval fixtures count pygal's `histogram-basic` as eligible again.** Its
  regeneration (#12416) dropped the PIL overlay that blocked it, which turned the
  fixture test that still pinned it as blocked red on `main`; only pygal's
  `line-timeseries`, whose regeneration kept the standard `random` module, stays
  blocked. (#12418)
- **Missing values in a converted NumPy array keep their rows.** A row whose cells
  were all missing reached the paste box as a blank line, which the parser skips, so
  every later value moved up one row. The converter now writes such a row as `NaN`,
  which the parser reads as missing and reports. An array without any value is now
  refused as `file_empty` instead of failing later in the paste. (#12413)
- **NavBar debug rapid clicks.** Fixed an issue where clicking the logo a 6th
  time rapidly navigated to home instead of staying in debug. The counter no
  longer resets when reaching 5 clicks. (#12409)
- **Quick feedback widget contrast.** The active/selected background color for
  the reaction toggle buttons was nearly identical to the popover's background
  color. They are now styled with a stronger contrast mix so that the selected
  option clearly stands out. (#12408)
- **The validator no longer lets a renamed save, a rebound `THEME` or a match
  capture through.** In plotnine's profile a save name imported under another name or
  used as a value (`from plotnine import ggsave as keep`, `g = ggsave`,
  `[ggsave][0]`, `functools.partial(ggsave, plot)`) escaped the save rule, so the
  exported code could write anywhere. In the matplotlib, seaborn, plotnine and altair
  profiles a second binding of `THEME` (`THEME = "x/../../elsewhere"` after the theme
  block) moved every save the same way, because the save rule checks the target's
  form, not the value of `THEME`. And a `match` capture could rebind a name that
  plotnine's expression rule read as a fixed string, handing plotnine code to
  evaluate. Every profile now refuses the first as a `banned-call` and any binding of
  `THEME` but its theme block as a `savefig-target`, and the expression rule counts a
  match capture as a binding. (#12405)
- **The fence regex no longer backtracks quadratically on user text.** The tag
  pattern `policy.fence` neutralises fence tags with put two blank runs around an
  optional slash, one ambiguous run that backtracked quadratically on `<` followed
  by a long run of blanks (CodeQL py/polynomial-redos). The blanks after the slash
  now sit inside the slash's own group; the matches are the same. (#12404)
- **JavaScript implementations get exactly one header.** impl-review's header
  writer stopped at a `//# anyplot-orientation:` directive on line 1 and
  prepended the new header above it, so the generator's header stayed below
  the directive with its old score, date and library line, and the site's code
  view showed both. The writer now lives in `automation/scripts/impl_header.py`:
  the header goes on line 1, a directive that sat above it moves directly below
  it, and a stale second header block among the leading lines is dropped. The
  five JavaScript library prompts now place the directive directly below the
  header. The stale block was removed from the 182 catalogue files that carried
  it (139 muix, 19 Highcharts, 14 ECharts, 9 D3, 1 Chart.js). (#12299)
- **The R setup installs packages built for the Ubuntu 26.04 runner image.** The
  setup-r action installed Posit's `noble` (Ubuntu 24.04) binaries. On the 26.04
  image they install without error, but stringi links ICU 74 while 26.04 ships
  ICU 78, so loading stringr fails. No catalogue implementation reaches stringi
  today: all 325 render the same on both builds. A generated implementation that
  used stringr, or tidyr's `separate()` or `extract()`, would have failed
  mid-run. The action now installs the `resolute` binaries from the same
  2026-10-20 snapshot. Its smoke test also loads tidyr and stringr, so a binary
  built for another Ubuntu release fails the setup step instead of a generation
  run. (#12263)
- **The JavaScript render harness installs again on the Ubuntu 26.04 runner
  image.** GitHub moved `ubuntu-latest` to Ubuntu 26.04, and Playwright 1.55.1
  refused to install Chromium there, so every `impl-generate` and `impl-repair`
  run for Chart.js, D3, ECharts, Highcharts and MUI X failed in its setup step.
  Playwright moves to 1.64.1, which knows the new image and brings Chromium 156
  instead of 140; a sample of 17 catalogue snippets in both themes renders
  pixel-identical to the 1.55.1 renders. (#12259)
- **The stuck-launcher executor test no longer fails on a slow CI runner.** The fake
  launcher execs the harness, so the process the test keeps alive carried the job's
  one-second `RLIMIT_CPU`; when the harness start spent that second, the kernel killed
  the "stuck" launcher inside the grace window and `stuck` read 0. The test now gives
  the run the host's full CPU cap, which a real `sandbox do` outside the sandbox always
  has, and asserts that limit on the survivor, so it fails every time without the fix
  (#12260).
- **JavaScript render harness waits 2.5 s, not 30 s, for the ready signal.**
  `automation/js-render/render.mjs` passed the `{ timeout: 2500 }` options to
  `page.waitForFunction` in the argument slot, so every snippet without
  `window.__anyplotReady` sat through Playwright's 30 s default before the
  fonts-ready fallback ran. The options now sit in the third slot, which
  shortens every such render by about 27 s across all JavaScript libraries.
  (#12248)
- **The pipeline installs the Python libraries from `uv.lock`.**
  `impl-generate.yml` and `impl-repair.yml` ran `uv pip install -e ".[lib-X]"`,
  which resolved `pyproject.toml`'s ranges afresh, so Dependabot's lock bumps
  never reached the pipeline and recorded versions drifted from the lock
  (plotnine 0.15.8 recorded, 0.15.7 locked). Both now run
  `uv sync --frozen --extra lib-X`, as the renderer image does. (#12240)
- **Implementation PRs can no longer change dependency files.** #9398 committed
  a `Manifest.toml` that a `Pkg.add` had re-resolved, which moved Makie from
  0.22.10 to 0.21.9 for every Julia implementation. `impl-generate.yml` now
  fails such a generation, `impl-merge.yml` refuses such a PR, and the
  generator and repair prompts say so. (#12240)
- **The site renders again after the Vite 8.1 bump.** Since Vite 8.1.6, every
  page of anyplot.ai stayed blank: Rolldown put its CommonJS runtime helper
  into the app's `theme` chunk, which imports `mui`, while `mui` imported the
  helper back, so the browser threw `t is not a function` on load. Vite 8.3.5
  emits the helper as its own `rolldown-runtime` chunk, which removes the cycle.
  (#12235)
- **Currency columns read three-digit comma groups as thousands.** A pasted
  price column such as `"$1,200"`, `"$950"`, `"$12,500"` (also `1,200 USD`,
  `€ 1,200`, `CHF 12,500`) read as 1.2, 950 and 12.5; it now reads as 1200,
  950 and 12500 with a warning, since a money amount mostly has at most two
  decimals. A cell with a one- or two-digit fraction (`$1,25`) keeps the
  decimal comma, and a file that speaks for decimal commas keeps the question:
  one delimited by semicolons, or with a column of dot groups or of `1.234`
  shapes, so a fuel price of `1,789 €` stays 1.789. (#12228)
- **API redirects stay on https.** A request to `https://api.anyplot.ai/specs/`
  was redirected to `http://api.anyplot.ai/specs`, because uvicorn ignores
  Cloud Run's `X-Forwarded-Proto` header. The API now takes only the scheme from
  that header, so the trailing-slash redirect keeps https, while the client
  address keeps coming from the trusted headers as before. (#12227)
- **Two merges in a row no longer leave production on the older commit.** Two
  builds of the same service deployed side by side, the later deploy moved the
  shared `candidate` tag, and the other build's smoke refused to promote; when
  that was the newer commit's build, the service stayed on the older one until
  the trigger was rerun (`deploy-app` on 2026-10-16 and 2026-10-21, `deploy-api`
  and `deploy-agents` on 2026-10-12). A `wait-turn` step in all four Cloud Build
  configs (`scripts/cloudbuild-wait-turn.sh`) now holds each deploy until every
  older build of the same service has finished, so the newest commit deploys
  last; image builds still run in parallel. (#12222)
- **Related plots load in about a millisecond instead of about 750 ms.** The
  related-plots block on every spec and implementation page was cached per spec,
  library, mode and limit. Those thousands of keys evicted each other from the
  shared 1,000-entry cache, so nearly every call reloaded all specs from the
  database (p50 755 ms, p99 1.6 s in the LinkedIn traffic of 2026-10-18/19).
  `/insights/related` now caches the catalogue once as a plain-value index under
  a single key and ranks against it in memory. The results are identical: 1,266
  spec, library, mode and limit combinations on the live catalogue gave
  byte-equal responses. (#12214)

### Security

- **Gemini reads only the owner's issue comments.** The `gemini-task` skill
  fed every comment on a `gemini` issue to Gemini, while it already filtered
  PR comments to the owner's; on a public repository anyone can comment, so
  issue comments are now filtered the same way. (#12458)
- **No CI on pushes to `feature/**`.** Google Jules names its own branch after
  the feature branch it starts from (`feature/<slug>-<session id>`), and a
  push run has no PR author, so the checks keyed on the PR author treated
  unread Jules code as trusted: the first such push gave `renderer-image` its
  GCP login before the run was cancelled. `ci-lint`, `ci-tests`,
  `ci-migrations`, and `ci-image` no longer run on pushes to `feature/**`;
  feature branches get CI through their pull requests. `Run E2E Tests` and
  `renderer-image` also refuse to run for any `feature/` ref, a merge queue
  into a feature branch, and, for the e2e job, any PR into a feature branch.
  (#12441)
- **Jules and Dependabot PRs run CI without secrets or an OIDC token.**
  `ci-tests.yml` splits into `Run Tests` (unit and integration, no
  `id-token` permission, every author) and `Run E2E Tests`, the only job that
  logs in to GCP, starts the Cloud SQL proxy, and holds the database password;
  it runs after `Run Tests` and skips PRs by `dependabot[bot]` and
  `google-labs-jules[bot]`. `ci-image.yml`'s `renderer-image` skips Jules PRs,
  and Jules opens PRs only into `feature/*`. Before, a Jules PR ran its tests
  with production database access the moment it opened. Every condition uses
  the PR author, because `github.actor` on Jules branches is often the
  repository owner and a re-run can change it. (#12429)
- **Every in-process run requires the harness's exec filter.** The seccomp filter
  that has the kernel refuse every program start was required for lets-plot alone.
  The renderer's logs show that Cloud Run's sandbox admits it, so the renderer and
  the local backend now require it for every render, data run and conversion. A run
  whose filter is not in place stops before its code starts: a
  data run reports that the fault is not the code's, and a conversion answers
  `503 convert_unavailable`. `RENDERER_EXEC_DENY=optional` lifts the requirement
  without a code change, should the platform stop admitting the filter. (#12414)
- **The render harness has the kernel refuse every program start.** Arming a guard
  now installs a seccomp filter (`install_exec_deny` in
  `agents/anyplot/render/harness.py`) under which the kernel refuses every `execve`
  and `execveat` of the process, its threads (those already running included) and
  its children. So native code the audit hook cannot see, such as the ImageMagick
  delegates in lets-plot's bridge, starts no program, whatever is on `PATH`. The
  filter covers every in-process run (Python renders, data runs and conversions);
  `fork` and threads stay allowed. lets-plot's command row requires it
  (`ANYPLOT_DENY_EXEC=required`): without the filter, its render stops before the
  plot. Every other run goes on and reports the filter's state in the harness's end
  line, which the renderer logs with every launch. `ci-image.yml` checks the routes in
  the built image. (#12410)
- **The renderer sandbox stays tight on Python 3.14.** 3.14 raises an audit event
  for every ctypes call, so the plot guard refused the `ctypes.cast` that scipy
  makes while it is imported, and with it every plot that uses scipy, statsmodels,
  scikit-learn or seaborn. The plot guard now lets exactly that call through, and
  only from an import; the same cast from plot code, `memmove`, `memset` and every
  other foreign function stay refused, and the data and convert guards allow none
  (narrowed after a Fable review). The sandbox interpreter also runs with
  `-X disable-remote-debug`, and the guards refuse `sys.remote_exec`, so 3.14's
  remote debugging cannot run a script in it. Subinterpreters (PEP 734, public
  from 3.14), whose code runs outside the guard's audit hook, cannot be created
  or entered, and the validator bans their modules. The code validator bans
  `annotationlib` and `typing.evaluate_forward_ref`, which 3.14 added and which
  evaluate annotation strings. (#12247)

*Catalog: no new implementations and no spec PRs; 138 regenerations. 127 are the MUI X 9
migration (#12264 to #12403), forced regenerations that took 127 of the 323 MUI X
implementations from @mui/x-charts 7.29.1 to 9.16: 118 written by Gemini 4 Argon and fed
in through adopt mode, 8 generated by Opus in the pilot of 2026-10-23, and one adopted from
`main`; the other 196 stay on 7.29.1. 11 are
daily-regen improvements (`ggplot2` 4, `pygal` 2, and one each for `matplotlib`, `altair`,
`letsplot`, `bokeh` and `highcharts`), and 3 kept regenerations stored their re-score
(#12436, #12437, #12492). 315 of 325 specs stay at full 15-library coverage.*

## [3.5.0] — 2026-10-16 — Bring your own data

anyplot 3.5 adds the agent network behind "Use with my data": an admin-only chat that takes a
catalogue plot and redraws it with your own data. It runs in two steps. First the data: a
parser reads pasted or dropped tables, JSON, JSON-stat, spreadsheets and columnar files, and
announces every change it makes to a value. Then the plot: the adapter rewrites the catalogue
code, the `anyplot-renderer` service runs it in a Cloud Run sandbox behind a two-profile code
validator, and the result is reviewed with the catalogue rubric and repaired where it falls short.
Around that core: the design document, the eval and ladder harnesses, quick feedback that
becomes a triage case, content-free usage telemetry with a `/debug` card, a privacy section
for the preview, and nine rounds of fixes from live tests.

### Added

- **Content-free usage telemetry for the agent chat.** The agents service writes four events,
  `data_input`, `chat_turn`, `pipeline_run` and `outcome`, one wide JSON line each, on a logger of
  their own with `log_type: "agent_telemetry"` for a Cloud Logging sink into a 180-day log bucket
  that BigQuery reads. Every field is a closed enum, a bucket, a count or an id from a closed set
  (strict pydantic models, parser warnings mapped to closed codes in
  `agents/anyplot/data/warning_codes.py`), the session is a salted per-process hash, no line carries
  the user id, and a canary test fails if a column name, cell, note, file name or message reaches a
  line. The page reports copies, downloads, saves and feedback through a new beacon
  (`POST /debug/agent/sessions/{sid}/outcome`), and the eval harnesses tag their lines `harness`.
  Committed BigQuery views (`agents/telemetry/views/`) deduplicate by idempotency key and add
  sessions with a 30-minute inactivity rule, usage, failures and cost; `docs/reference/agent-telemetry.md`
  lists the one-time setup. (#12205)
- **Agent usage card on `/debug`.** Sessions, plots shipped, kept and repair rates, and the top specs,
  input formats and refusal codes of the last 7 or 30 days, read through the new admin-only
  `GET /debug/agent-usage` (aggregates only; an empty state while `AGENT_TELEMETRY_DATASET` is unset). (#12205)
- **JSON Lines in the agent chat's data box.** A paste or a dropped file with
  one JSON object per line (a log export, `to_json(lines=True)`) reads as JSON
  records, source format `json_lines`; a line that is no object is refused with
  its line number and the JSON error. A title above the objects becomes a note,
  and a dropped `.jsonl` file of one record is one row. Live test round 6 had
  refused a 600-line `events.ndjson` as unreadable. (#12201)
- **A damaged file names its broken part.** A spreadsheet, Parquet, Arrow or
  NumPy file the converter refuses as damaged says which part is broken: the
  zip container, the workbook, a sheet's cells, a Parquet footer or page, an
  Arrow stream, a NumPy header or its data. The names are a closed set carried
  from the sandbox to the page, never an exception's text (owner decision of
  2026-10-16). (#12201)
- **Daily, weekly and hourly buckets for `prepare_data` aggregates.** `aggregate` takes the
  periods `hour`, `day` and `week` (ISO, each as its Monday) beside `month`, `quarter` and
  `year`, and keeps the key a datetime, so "a daily mean per sensor" over 13-minute readings
  keeps a time axis; the bucket follows the column's own UTC offset as stored, which the
  change line names. A new prep eval case covers it. (#12200)
- **A table picker for pastes with several tables.** A report sheet with two tables one below
  the other (a title, a table, a blank row, a caption, a second table) is read as its first
  table instead of one table with the second header as a data row; a warning names the others,
  and the data panel offers them in a picker that parses the same text again, as the sheet
  picker reads another sheet. (#12200)
- **Excel, OpenDocument, Parquet, Feather, Arrow and NumPy files go into the agent chat's data box.**
  A dropped, chosen or pasted binary file (at most 5 MB) goes to the new
  `POST .../dataset/convert` route, which reads it in the renderer's sandbox
  (`harness.py --convert`, the guard armed after the readers are loaded) and
  answers the text the paste box takes; nothing is stored, and the user's
  `.parse()` sends the text through the ordinary paste route with the file name
  and sheet as `source`. The format comes from the first bytes: workbooks
  through calamine, which reads stored values only (no formula, link or macro
  runs; a formula without a saved value is empty and counted, a sheet of only
  such formulas is refused with "open it in Excel and save it once"), Parquet
  and Arrow through pyarrow (row groups counted first, at most 20,001 rows
  read; slimmed in the image from 163 MB to 99 MB), NumPy with
  `allow_pickle=False`; every zip is checked from its directory and inflated to
  prove its declared sizes, an xlsx sheet's cell span is measured before it is
  loaded, an encrypted workbook gets "remove the password", and pickle, joblib
  and HDF5 are never read. Values keep their precision: timestamps every
  fraction digit and their offset, decimals and 64-bit integers exactly, and
  dropped columns (durations, intervals, binary) are named. A sheet comes as
  its raw cell grid, so a title above the header stays a note; a workbook with
  several sheets gets a sheet picker (empty sheets left out) that reads the
  chosen one again; a table with list columns comes as JSON records, which the
  parser expands into one row per value. Over a cap (20,000 rows, 50 columns,
  1 MB of text) the file is refused with its numbers. Conversions have their own
  limits (5 a minute, 30 a day per user, one at a time, 10 s) and wait behind
  every pipeline render. (#12194)
- **The data parser reads ISO timestamps with fractions and UTC offsets as datetimes.**
  Up to nine fraction digits and an offset (`Z`, `+01`, `+0100`, `+01:00`) are
  kept as written, so the plot's loader reads the column as zone-aware
  timestamps with full precision; a column with several offsets is written in
  UTC with a note, and `prepare_data` keeps fractions and offsets through its
  changes. (#12194)
- **Date column from year and month in the agent chat.** A new `prepare_data`
  operation, `make_date`, builds a date column from whole-number columns that
  hold the parts of a date: a year with a month and an optional day, a quarter,
  or an ISO week. Out-of-range values and rows that are no calendar date are
  refused, never moved. `set_type` to a date also reads `DD/MM/YYYY`,
  `YYYYMMDD`, `YYYYMM`, `YYYY-MM`, `MM/YYYY`, `MM.YYYY` and `YYYY`. The root prompt now
  uses these operations and no longer asks the user to add a column that an
  operation can build. (#12193)
- **Month names, date order and computed roles in the agent chat.** `make_date`
  reads month names and abbreviations in eleven languages. A date column whose
  day and month could be read either way can be switched in both directions,
  also in a later version. A new date column fills an open required date
  role. A role the plot computes, such as the rolling average of
  `line-timeseries-rolling`, takes no column. (#12193)
- **The agent chat reads tables aligned with spaces.** A weather or statistics
  office's `.txt` (MeteoSwiss' homogenised monthly series in the live test of
  2026-10-15) came in as one text column. Where no comma, semicolon, tab or
  pipe finds a table, the parser now splits at runs of two or more spaces, so a
  header such as `Max Temp` stays one name, and at single spaces only for a
  table of numbers; prose, a headerless list (`Hund 7`), a key-value block and a
  table with two-word names still go to the transcriber. A blank cell of a
  fixed-width row stays in its column by position, and a row that does not line
  up is refused rather than guessed. The metadata block above the table becomes
  notes, and a declared mark such as `Missing values: -999` reads as missing in
  number and date columns. (#12191)
- **The agent chat reads JSON as data APIs answer it.** The World Bank's
  `[{page metadata}, [records]]` was refused. Records wrapped with metadata (an
  array beside a metadata object, or `{"data" | "results" | "records": [...]}`
  with sibling fields) and schema-plus-rows payloads (CKAN, Socrata, Frictionless,
  pandas `orient="split"`) now read, the metadata going to the notes; nested
  objects become dotted columns (`country.value`) down to three levels, and
  list fields such as a measured curve's `x` and `y` expand to one row per
  point, with a `record_id` when nothing else tells the records apart. (#12191)
- **Text files go into the agent chat's data box by drop, `.open()` or paste.**
  The browser sniffs the binary formats first (a spreadsheet, Parquet, Arrow or
  NumPy file is answered with "a later step, copy the cells or export as CSV
  for now", pickle and HDF5 with "never"), finds the encoding (UTF-8 with or
  without a byte order mark, Excel's UTF-16LE "Unicode text", UTF-16BE,
  windows-1252 rather than ISO-8859-1, whose C1 range the parser refuses) and
  fills the box with the file's text, line breaks as `\n`; the user presses
  `.parse()`, a box with text asks before it is replaced, and a running step
  refuses the file. The name travels as the dataset route's new `source` field,
  never inside the text and never as a note: the agents service sanitises it,
  screens it on its own call and keeps it as the dataset's `file_name`, which
  the assistant reads fenced as data, a name and never a request, so a file
  named like a wish for the plot is not acted on. Plausible gets
  `agent_data_file{kind, encoding, outcome}`, never the name. (#12192)
- **Agent chat: gates for crowded value labels and the plot language's
  number format.** G11 counts the value labels, dots and shadows the
  catalogue draws once per bar or point and writes a measured VQ-03 line
  when more than 25 crowd a plot, or bar labels are wider than the space
  per bar (the live case: 52 labelled, dotted, shadowed bars of 26
  regions). G12 writes a VQ-06 line when a numeric tick label or annotation
  uses the other decimal mark than the plot language (`5.30` and `6.0 M`
  in a German plot). A server-side table of decimal and thousands marks and
  large-number words per language (`de`: `5,30`, `6,5 Mio.`) goes into the
  adapter's instruction, and the house-style exemption of the reviewer and
  scorer no longer covers elements whose count grows with the data
  (#12184).
- **Agent rules and skills for non-Claude agents.** `AGENTS.md` is a symlink to
  `CLAUDE.md` and `.agents/skills/` a symlink to `.claude/skills/`, so the
  Antigravity CLI (`agy`), Codex, and other tools that read those paths load the
  same rules and skills from one source instead of a third file to keep in sync.
  A unit test fails if either link is replaced by a real file or points
  elsewhere. (#12187)
- **The assistant answers questions about the data without changing it.** A new
  root tool, `query_data`, applies the same closed set of operations as
  `prepare_data` to a copy of the data and returns at most 25 rows in at most 8
  columns; nothing is stored, so the data version, the bindings and the
  confirmation stay as they are. In the live test the root had filtered the
  user's table to one year to answer "which country was highest in 2023?" and
  then asked the user to undo it; the prompt now sends questions to
  `query_data` and keeps `prepare_data` for changes the user asked for. (#12182)
- **A request for the plot in another library gets a pointer, not a strike
  toward closing.** The scope judge has a new verdict, `other_library` ("this
  plot in Chart.js, give me the code"): a fixed answer in 11 languages says the
  chat adapts matplotlib and seaborn and points to the plot's catalogue page,
  which has it in up to 15 libraries. By default it never counts toward
  closing the session (`AGENT_OTHER_LIBRARY_COUNTS`); a live test had refused
  it as the third out-of-scope request and closed the session unwarned
  (#12180).
- **A warning before a chat closes.** The counted refusal one before the
  closing one ends with a fixed sentence in the message's language ("One more
  request outside this scope will close this chat.",
  `AGENT_SESSION_CLOSE_WARNING`) (#12180).
- **Paste limits.** The data panel's paste route now has its own per-user
  limits (`AGENT_USER_PASTES_PER_MINUTE` 10, `AGENT_USER_PASTES_PER_DAY` 100;
  only a paste that reaches the checks counts), one paste per user at a time,
  none while the user's turn runs in any session, and none in a closed session
  (`403 session_closed`); while a paste is in flight, the session's data routes
  (bindings, confirm, undo, `.to_long()`, library) wait for it, so a version
  stored from another tab is never dropped. Each paste spends dataset-judge, notes-judge and
  maybe transcriber calls, and was bounded only by the daily token budget
  (#12180).
- **`derive`, a computed number column in `prepare_data`.** The assistant can
  add a ratio, a difference, a row sum, a share of a group's total, or, in the
  order of a number or date column, a percent change from the previous row, a
  running total or an index (first row = 100), computed server-side in pandas from a closed set
  of formulas (no free expressions), so it answers "which year has the largest
  share of foreigners?" by deriving the share instead of asking you to add the
  column. (#12179)
- **A reply-language check for the assistant.** After each final reply, an
  offline classifier compares the reply's language with the session language;
  on a sure mismatch the assistant is asked once more to write the same reply in
  the session language. (#12179)
- **Data from your own code in "Use with my data".** You can paste or type code that
  generates your data (Python, JavaScript, R, or a formula from a textbook). The
  assistant translates it into Python, and its new `run_data_code` tool runs it in the
  renderer's sandbox through a new `POST /run-data` route. The resulting table becomes a
  new data version that you confirm, and the data panel shows the Python that ran under
  `# code that made this data`. The validator's new DATA profile (which also counts text
  values and repeated lists as written-out rows), an audit hook in the harness (no file
  access, new imports, frames, native code, processes, or sockets), per-user and per-minute
  limits, and the dataset judge on the computed table keep the sandbox to the plot's
  data. The tool never passes the snippet's own output back to the model. A request in
  words that needs a computation (the Lorenz attractor, a random walk) goes this way too;
  a closed formula stays on `generate_data`. (#12172)
- **`422 code` for code pasted into the data field.** A classifier now runs before any
  parser or the transcriber reads a paste. It catches code such as
  `np.linspace(0, 10, 100)`, which used to parse as a one-row table, and the page offers
  to send it to the chat instead. (#12172)
- **The data field reads JSON-stat datasets from statistics offices.** A
  JSON-stat 2.0 dataset as the Swiss BFS PxWeb API, Eurostat, Statistik Austria
  or Statistics Norway answer it (and a JSON-stat 1.x bundle of one dataset) is
  no longer refused as `unparseable`: the parser checks its sizes, categories and
  values strictly and flattens it into one long table, a column per dimension
  with more than one category, named by its label and holding the category
  labels as text, then `value`, the only typed column, in the dataset's own
  order (source format `json_stat`). The dataset's title, source and notes and
  its dimensions of one category become the notes pasted with the data,
  screened like any other note before the assistant reads them, so the table
  stays long and tidy; the status symbols, the update date, the roles and the
  extensions are not carried. (#12173)
- **The assistant reads the notes pasted with a table.** The lines the parser
  leaves out above and below a pasted table (a title, an export's metadata, a
  source line, "time is the date column, make it a line chart") are kept as
  `context_lines`, at most 2,000 characters, instead of vanishing. The dataset
  route runs the cells' pre-filter and then the scope judge on them; a refusal or
  an outage drops only the notes with a warning, stores the table and costs no
  strike. The kept notes reach the root fenced as `<user_notes>` with the
  `summarize_data` turn and through `get_dataset_profile`, travel with every data
  version, and show in the data panel as `# notes sent to the assistant`. The
  root uses them as context for the whole chat and acts on a clear request in
  them right away, the plot still waiting for the user's confirmation; the scope
  rubric and seven new scope-eval cases cover ordinary notes and an injection
  hidden among them. (#12168)
- **Agent experiments on the Claude subscription.** `AGENT_TRANSPORT=claude-cli`
  (development and test only) sends the agents' Claude calls through the local Claude Code
  CLI instead of Vertex AI, below ADK, so an experiment runs the live code unchanged:
  agents, prompts, plugins, pipeline, the deployed renderer and the gates. The root's chat
  with tools stays on Vertex AI. `AGENT_ADAPTER_MODEL` and `AGENT_REVIEWER_MODEL` pick a
  model per agent, `scripts/agents-experiment.sh` runs the harness and the rubric scorer
  in one command, and `agents/evals/score.py --transport claude-cli` and the ladder lab
  use the same transport (#12159).
- **Ladder lab for the agent's repair loop.** `agents/evals/ladder_lab.py` compares, on
  the same seed renders, how much the Opus scorer moves on one render, which rubric
  deductions Haiku, Sonnet, Opus and today's reviewer name, and which repairer and
  feedback form (defect lines, lines plus suggestions, a Sonnet or Opus advisor's plan)
  lifts the score. Every model call goes through the local Claude Code CLI with the
  agent's own prompts and schemas, and every answer through the pipeline's own edit,
  validator, render and gate code (#12158).
- **Agent results scored with the catalogue rubric.** `agents/evals/score.py` scores a
  harness run's first and shipped renders on Claude Opus 5.5 with the catalogue's own
  rubric, read verbatim from `prompts/quality-criteria.md` and the review prompt and
  restricted to the 16 criteria a user sees (`agents/anyplot/scoring.py`,
  `agents/anyplot/prompts/scorer.md`): the code adds up and applies the caps, and the
  report gives the score distributions, what repair 1 gains, the runs each threshold
  would send to an advisor, and the points lost by criterion. The harness keeps every
  attempt's render with `--keep-attempts`. It is the measurement behind the owner's
  quality ladder; the agent itself is unchanged (#12157).
- **A wide table is offered in long form.** A paste such as `Sensor_A,Sensor_B,Sensor_C`
  on a box, violin or strip plot, which wants one category and one value column,
  gets a `# wide table` hint with `.to_long()` in the data card: the agents service
  turns the columns into the plot's category and value columns (date columns kept)
  without a model call, as the next data version with fresh bindings, and `.undo()`
  takes it back. The rule is code (`agents/anyplot/data/shape.py`), and the
  assistant's data summary names the offer (#12156).
- **A chat that made no plot can be reported too.** Below the composer, a session
  without a plot version offers `.feedback()` on the chat itself, the same four
  reactions, text and `# include data.csv`. It is stored as a feedback case with
  `result_version` 0: the conversation, the profile, the bindings and, when ticked,
  the session's current data, but no image and no `plot.py` (`422 no_data` when the
  data is asked for before there is any). The triage labels it `chat, no plot`,
  shows no renders and refuses its promotion (`422 no_plot`), and `import_case`
  refuses it. No migration: `result_version` had no constraint (#12155).
- **Roles that cannot be negative never get a negative column by default.** A radius,
  a size, a count, a standard deviation, a weight, and the value of a pie, donut,
  treemap, sunburst, icicle, waffle, marimekko, sankey, rose or basic funnel need
  values of 0 or more (`agents/anyplot/data/signs.py`): the default bindings pass
  over a column with a negative value, and a binding of one by hand stays valid but
  is warned about in the session block, the `set_bindings` result, the bindings
  route's new `warnings` and under the page's dropdown. Signed plots such as
  waterfall or diverging bars keep their signed `value`. The fixtures are the owner's
  cases of 2026-10-12: a sine as a polar radius, and a signed `y` given to `std`
  (#12154).
- **A repair moves a polar plot's radial labels to a measured free direction.** The
  render probe now describes each polar axes (the radial labels' angle and a
  histogram of the plotted points by angle and radius), and when the labels sit on
  the data the next repair attempt gets the measured target, such as "at 67.5° they
  sit on 10 plotted points → ax.set_rlabel_position(270), 0 points there", instead
  of guessing an angle. The line never starts a repair on its own (#12153).
- **Scripts for the local agent stack and the PR loop.** `scripts/agents-dev.sh`
  starts the agents service, ADK's development UI, the API with the agent routes and
  the app, each against the real models and the deployed renderer, with the identity
  token renewed every 55 minutes and the API keys read from files that are never
  printed; `scripts/agent-cases.sh` reads the production feedback cases. The
  `open-pr` skill bundles the watchers it asks for: the PR's checks, the Copilot
  review rounds with their unresolved threads, and a merge's Cloud Build deploys
  (#12151).
- **The assistant derives a category column from your data.** The new `prepare_data`
  operation `classify` adds a text column whose cells are labels, chosen per row by
  the first of up to ten rules whose conditions hold: two classes ("y above 0 is
  class 1, the rest class 2") or levels ("above 70 high, above 40 medium, else
  low"), so a table of numbers gets a column for a text role such as a
  feature or a category. The conditions are the ones `drop_rows` uses, compared and
  never evaluated; labels are at most 40 characters and stay text in every later
  version. The prep eval gains a case for each (#12148).
- **The agent chat has one session language, shown as a chip.** A `lang: en`
  chip in the chat header, next to the library pills, opens the site's ten most
  used visitor languages in Plausible (en, zh, de, vi, es, fr, nl, pt, ru, it)
  and a field for any other language in Latin letters. The first in-scope typed message sets the language
  it is written in (`lang: de · detected`, with one quiet line in the thread),
  a later message never changes it, and a choice from the chip or a request
  such as "labels in English" (the root's new `set_language` tool,
  `PUT /v1/sessions/{sid}/language` and its BFF mirror) is kept for good
  (`chosen`). English stays the default, also for a German browser, so
  "sin x" gets an English plot; the browser locale is only recorded with a
  feedback case. The `done` event carries `language: {language, source}` so
  the chip follows the chat, and the feedback bundle carries the session's
  language and each version's. (#12145)
- **An eval case and scope cases for the session language.** The hand-written
  case `scatter-basic-matplotlib-german-message` has German column names and a
  German follow-up with no word about the language, so its first plot is
  English and its second must carry German plot text; the full matrix now has
  123 cases. A case may name a `language`, which the harness chooses through
  the language route before the first turn, an imported feedback case carries
  the language its version's text was written in when the session's was
  detected or chosen, and every run records the
  last `done` event's language. Six in-scope scope-eval cases (`plot_language`,
  three English, three German) guard the rubric's new line that a request for
  the plot's own text in another language is no translation. (#12145)
- **Fixed refusals in Chinese, Vietnamese and Russian.** Every chip language
  now has its own hand-written refusals; the Portuguese and Polish lines were
  revised. Without a native speaker at hand, each text passed a
  back-translation review and a separate naturalness review. (#12145)
- **Plot text in many scripts.** The renderer image installs Noto Sans, Noto
  Sans CJK and the Noto Sans faces of the scripts DejaVu Sans lacks (37 files,
  46.8 MB, Regular and Bold, with their OFL notices), and the harness appends
  them to every font lookup after the font the code chose, so a Chinese,
  Japanese, Korean, Arabic, Devanagari or Thai title draws with real glyphs
  while the catalogue's DejaVu Sans stays the first font. The lookup-level
  append is what survives seaborn's `set_theme`, which rewrites `font.family`
  in 306 catalogue files, and a `monospace` or `serif` set on one text. The
  image build fails when a fallback family is missing from the cache. Arabic
  and Hebrew already rendered shaped and right to left through the pinned
  matplotlib's libraqm; the documented limits are `$…$` math text, the Han
  regional forms and the scripts outside the installed set. (#12144)
- **G10, the glyph gate.** The harness records every code point matplotlib
  reports as having no glyph in any font of its text, plain text and `$…$`
  math alike, as `missing_glyphs` in the probe; the host turns it into a
  VQ-01 line that names the count and up to three characters with their code
  points, tells the repair that a user's column name stays as it is, and
  stays in the result's residual lines even after a reviewer `ok`, because a
  measured missing glyph is not a judgement. The CI image job renders a
  seven-script fixture through the image and a DejaVu-only control, and
  asserts the probe on both. (#12144)
- **Agent cases: the triage half of quick feedback.** A new table
  `agent_feedback` (Alembic revision `b4e7a9c2d6f1`) holds one row per feedback
  case of the agent chat. `POST /debug/agent/sessions/{sid}/feedback` inserts it
  right after the case's files are in the private bucket, and answers
  `502 row_missing` with the stored case id when the files are stored but the
  row is not, so the page names that case in its next edit. The debug page's
  new "agent cases" section lists the cases with filters (reaction, status,
  spec, library, model version, tag; superseded cases hidden by default), opens
  one (its PNGs, the code with a unified diff against the catalogue original,
  the transcript, the defect lines, the config stamp, the message), sets its
  status and tags, and promotes it to an eval case, through
  `GET /debug/agent/cases`, `GET /debug/agent/cases/{id}`,
  `GET /debug/agent/cases/{id}/files/{name}` and `PATCH /debug/agent/cases/{id}`.
  An edit's `replaces` supersedes the earlier row only for the same session
  hash and result version. The row is the source of truth for status, tags and
  promotion; the bucket holds the files until its lifecycle rule deletes them,
  and the row keeps the failure-class statistics after that. (#12142)
- **`agents.evals.sync_cases` pulls promoted cases into the harness.** On the
  dev machine it reads the table, downloads each promoted, active case from the
  bucket and imports it through `import_case` into the git-ignored
  `agents/evals/.cases/`, removes the directories of retired, superseded or
  unpromoted cases, and with `--backfill` indexes the cases that reached the
  bucket without a row (a dry run unless `--apply`). (#12142)
- **CI verifies every migration before merge.** The new workflow
  `ci-migrations.yml` (check `Verify Migrations`) runs the checks of
  `/verify-migrations` on a PostgreSQL 18 service container for every PR that
  touches `alembic/`, `alembic.ini`, `core/database/`, `pyproject.toml` or
  `uv.lock`: one head, `upgrade head`, `alembic check`, and a downgrade to the
  base commit's head and back, plus a CHECK-constraint parity query that
  `alembic check` cannot do. Until now the first database to see a new revision
  was production, after the merge. (#12142)
- **Quick feedback on an agent chat result stores the case for tuning.** Every
  result card has a feedback control: thumbs up, thumbs down, bug or idea (the
  site feedback's set), an optional text of at most 500 characters and
  `# include data.csv`, ticked by default for admins in phase 1. `.send()`
  never waits for a turn and never starts one; the card then shows
  `sent · v<n>`, and an edit stores a new case that names the one it replaces
  (`replaces` in its manifest). The BFF's new
  `POST /debug/agent/sessions/{sid}/feedback` fetches that version's bundle from
  the agents service, under the same admin gate, ownership and size cap as
  `.save()`, and writes it to the private bucket `AGENT_CASES_BUCKET`
  (`anyplot-agent-cases`) as `cases/<case_id>/`: the PNG of each rendered theme,
  `plot.py`, `data.csv` only with the box ticked, and `manifest.json` last. The
  manifest carries every column the planned `agent_feedback` table needs, so the
  table can be filled from the cases later. No upload replaces an object, and a
  failed upload answers `502 storage` and leaves no manifest, so a half-written
  case never counts. Analytics: `agent_result_feedback{reaction, include_data}`.
  (#12139)
- **`agents.evals.import_case` turns a real session into an eval case.** It reads
  a bundle that `.save()` downloaded, or a stored case directory, and writes
  `case.json`, `data.csv` and, when the version came from a typed change,
  `change_request.txt` into the git-ignored `agents/evals/.cases/`, which the
  harness runs as promoted cases. It never writes into the committed fixtures,
  because a case holds a user's data. It matches a version's request by
  position only when the transcript's plot turns and the versions agree in
  number, and otherwise lists the turns and asks for `--change-request` or
  `--no-change-request`. (#12139)
- **`.save()` downloads an agent chat session as one JSON file.** The chat
  header's new button saves the feedback case the agents service already
  assembles (the conversation, every version's code, plan, result and PNGs, the
  data profile, the bindings and the config stamp), with each version's
  `data.csv` while `# include data.csv` is ticked, the phase-1 default for
  admins. A session can now be kept and shown to whoever tunes the assistant
  before the stored feedback cases exist. The BFF's new
  `GET /debug/agent/sessions/{sid}/bundle?include_data=&version=` relays the
  agents service's bundle as an attachment (`anyplot-session-<id>.json`) behind
  the same admin gate, ownership and error mapping as the other session routes,
  and compresses it in a worker thread, off the event loop. A bundle over
  32 MiB, Cloud Run's limit on a response that is not streamed, can't be saved:
  the page shows an error line instead of a cut-off file. Analytics:
  `agent_session_saved{include_data}`. (#12138)
- **The assistant computes your data from a formula in step 1.** Ask for a function
  or curve instead of a table ("zeichne sin(x) von -pi bis pi", a parabola, a
  parametric circle, a surface `z = sin(x)*cos(y)`), and the root agent's new
  `generate_data` tool chooses a spec, never rows: one or two variable ranges and one
  to ten series, each an expression over them. The agents service computes the table
  with NumPy (`agents/anyplot/data/generate.py`) through a whitelist over Python's
  `ast` (numbers, the variables, `pi`, `e`, `tau`, `+ - * / ** % //` and a fixed set
  of functions), never `eval`, so a forbidden construct is refused with a message that
  names it ("'^' is not a power; write x**2") and an overflow or a logarithm of a
  negative number becomes an empty cell, never an exception. Every row holds the
  formula for the `x` it shows (the variables are rounded first), and the change line
  quotes only the checked expression. The table is an ordinary dataset version: the
  next one, which `.undo()` takes back, when the session has data, or version 1 when
  it has none, with the default bindings for its columns; the user confirms it like a
  paste, and the plot and its export use it unchanged. `ToolSafety` validates the spec
  against the same model first. (#12134)
- **Formulas pasted into the data field answer `422 formula`.** The dataset route
  refuses text that looks like a formula before the free-text transcriber reads it,
  because that model would compute the rows itself; the BFF passes the code on, and
  the page can point to the chat instead. Text that holds its own values stays data
  ("Mieten von 500 bis 900 Euro pro Quadratmeter: Berlin 12, Hamburg 14, München
  19"), and the transcriber's rubric now says to compute nothing. The `done` event's `dataset` now carries the
  spec's `roles` too, so a first dataset made in the chat has its binding controls. (#12134)
- **The chat page takes a formula from either box.** Until there is data, the data box
  and the chat both name the other source ("or ask for a curve in the chat: y = sin(x),
  x from -pi to pi"), and the chat is open without a paste. A formula pasted into the
  data box gets the server's `422 formula` as a line with `.send()`, not as an error:
  the button sends the text to the chat as a turn and empties the box. The table
  `generate_data` computes arrives like a data change, with its roles: version 1 in a
  session without data, whose `# changed` block names the generated rows and offers no
  `.undo()`, or the next version over data that exists, which `.undo()` takes back. (#12134)
- **Formula cases in the evals.** The scope judge treats a request to draw a function,
  curve or distribution shape as in scope, never `needs_data` (six new English and
  German scope cases), and the prep eval scores `generate_data` calls on four new
  cases (21 in all): two calls match when they compute the same table. The root's
  step-1 rules now read a user who says how a column is meant to be read ("the dates
  are month first") as a request for a change. (#12134)
- **The assistant changes your data in step 1, and you can undo it.** Ask in words
  to read a column as numbers or dates, drop a total row, sum per month, rename,
  sort or pivot, and the root agent's new `prepare_data` tool chooses from a fixed
  set of operations (`rename`, `drop_columns`, `drop_rows`, `set_type`, `aggregate`,
  `sort`, `pivot_longer`, `pivot_wider`, at most five per call) that the agents
  service applies with pandas to the stored canonical CSV (`agents/anyplot/data/prepare.py`)
  and stores as the next dataset version (`agents/anyplot/dataset_versions.py`, the
  last five kept). The model never writes data rows. The turn's `done` event carries
  the new version with one change line per operation, unconfirmed, and
  `POST .../dataset/undo` restores the previous version. `ToolSafety` validates the
  operations against the same models first; a condition value and a rename's name
  are the only tool arguments exempt from the link rule, because they are compared or
  written, never followed. (#12133)
- **The step-1 summary.** The messages action `summarize_data` asks the assistant to
  describe the data in two to four sentences (rows, columns with types and units,
  missing values, percentages, the proposed bindings, one question when something
  is ambiguous) without the scope judge; the profile now carries `mean` and
  `median` for numeric columns, and the model-facing profile JSON leaves empty
  fields out. (#12133)
- **The prep eval.** `python -m agents.evals.prep` drives 17 German and English data
  requests through `/v1` in process with the real model and scores the root's
  `prepare_data` calls by exact operation match, order-insensitive, with an 80 % gate
  (`agents/evals/fixtures/prep/`). (#12133)
- **The data panel shows what the assistant changed, with `.undo()`.** After every
  parse that stores a dataset (a paste, or a transcription's `.use()`) the page asks
  for the step-1 summary, so the assistant's description of the data is the first
  turn in the thread, and the composer takes data requests ("read Anteil as numbers",
  "sum per month") before the confirmation. A turn whose `done` carries a new data
  version replaces the preview, the profile and the bindings, takes the page back to
  step 1 and shows a `# changed` block above the preview with one line per operation
  and `.undo()`, which restores the version before, unconfirmed and without a new
  summary. Two enum-only analytics events count it, `agent_data_prepared{changes}`
  and `agent_data_undo{version}`. (#12133)
- **The mock BFF plays the data changes.** `app/scripts/agent-bff-mock.mjs` answers
  `summarize_data` with a scripted summary, plays a `set_type`, an `aggregate` (by the
  column the message names, such as "gruppier nach x") or a `rename` on messages that
  ask for percentages, grouping or a rename, carries the new version in
  `done.dataset`, and restores it through the undo route. (#12133)
- **The data field reads units, flat objects and Python literals without a
  model.** A column whose every cell carries the same unit (`65 %`, `15,6 h`,
  `€ 5`, `CHF 1.200`) is read as numbers, the unit moving into the column name
  (`Anteil (%)`) with a warning, so a pie chart's numeric role binds to a
  percent column pasted from a spreadsheet; a column where only some cells
  carry a unit, or two units, stays text. A JSON object of plain values and an
  array of `[category, value]` pairs become a two-column table (`category`,
  the keys as text, and `value`; source format `json_pairs`; a repeated key
  keeps its last value with a warning). A Python literal, also behind an
  assignment such as `cat_day = {...}`, with single quotes, trailing commas,
  tuples and `True` / `False` / `None`, is read like JSON: `ast.literal_eval`
  evaluates literals only, a name or a call is refused, and a bracket count
  that skips quoted strings refuses more than 50 nesting levels before anything
  is evaluated, so a 200 KB nested blob never reaches the stack. Text that
  starts with a bare `(` and is no literal stays delimited text. (#12132)
- **The data field reads free text as a table, and you confirm it first.** Pasted
  text that is no table the parser can read, such as "a bar chart with dog 7, cat 3
  and bird 4" or a list typed one value per line, is read by the judge model into a
  table (column names, rows, a short note on anything ambiguous). The page shows that
  table as a preview with `.use()` and `.discard()`, and nothing is stored until you
  use it: the confirmation posts the table's CSV through the ordinary parse, pre-filter
  and judge path. Text over 4,000 characters, JSON arrays and objects, and real tables
  take the old path unchanged. (#12130)
- **A thinking measurement for the agent root and adapter.**
  `AGENT_ROOT_THINKING_BUDGET` and `AGENT_ADAPTER_THINKING_BUDGET` (0, off, by
  default; at most 4,096), set by the eval harness with `--thinking-budget
  ROOT,ADAPTER`, turn on Claude's adaptive thinking for that agent and add the
  budget to its output cap, so the answer keeps its headroom. Claude Haiku 5.5
  takes no thinking budget of its own, so the value is room, not a limit; the
  stamp records it and the summary names the measurement. With both at 0 no
  request changes. (#12124)
- **The agent chat refuses requests for data it would have to fetch.** A
  message that wants stock prices, the weather, inflation figures, exchange
  rates, sports results, the contents of a URL or a public dataset now ends at
  the first turn with a fixed answer, in the user's language, that no internet
  source can be tapped and that the data must be pasted as a table. The scope
  judge has a new verdict `needs_data`, the stream a matching `refusal` code,
  and the chat page counts it as its own `agent_guardrail_block` reason.
  (#12126)
- **A scope eval measures the scope judge.** `python -m agents.evals.scope`
  sends the 176 synthetic cases of `agents/evals/scope.evalset.json` (58 in
  scope, four of them with personal data such as payee names, an e-mail
  address in a byline or a payment reminder on the user's own tax plot; 53
  off-topic; 65 adversarial: overrides, role play,
  German, base64, multi-turn drift, plot-framed and mixed requests,
  advertisements and calls to action in plot text, data to fetch) straight to
  the judge, with no agent and no render, and fails below the design's gates:
  every adversarial case refused and at most 5 % false refusals. A run costs
  about $0.05 and takes about seven minutes, paced below the Vertex quota; a
  `--tags` subset gates only what it measures and writes its own report. The
  first run passed both gates: every adversarial case refused, no false
  refusal. (#12126)
- **`AGENT_KEEP_REFUSALS` and `AGENT_ATTACK_STRIKES`.** With the first switch
  on, the text and verdict of each refused message stay in a bounded in-memory
  ring per session that the feedback bundle of the `/v1` route shows while the
  session lives, a phase-1 stub until refusals are stored with the quick
  feedback. Three `attack` verdicts of the scope or dataset judge in a day, on
  three different messages or datasets, give a user the budget refusal for the
  rest of it. (#12126)
- **Stress cases and a model-free static stage for the agent eval harness.**
  `agents/evals/make_stress.py` writes 23 seeded cases (`stress-*`): data
  exactly at and one past the parser's caps, 100 bars and 30 pie slices,
  degenerate data, prompt injection in a header, row 4 and a long cell, and
  requests that make the code compute mass data. Each case names the bound
  that must stop it. `python -m agents.evals.matrix --cases stress --static`
  runs every step before and around the models (parse, eligibility, bindings,
  the loader, prompt sizes, where injected text lands, and renders of
  hand-written stand-ins for the adapter's answer) without spending a token,
  and exits 1 when a bound did not hold. `--cases full` leaves the stress
  cases out, so a full run and its baseline keep their 122 cases. (#12125)
- **The anyplot-agents image and its Cloud Build deploy.** `agents/Dockerfile`
  builds the private `/v1` service on `python:3.13-slim` with the `agents`
  extra and no plotting extra, because every render goes to anyplot-renderer.
  It copies the source tree rather than a wheel, so the prompts,
  `refusals.yaml`, the footer-strip fonts and the catalogue prompt sources sit
  at the paths the service reads them from. It runs as uid 1000 and fails its
  own build when one of those files is missing, the judge rubrics that the
  service reads only on first use included.
  `agents/cloudbuild.yaml` deploys it with the renderer's steps: a `candidate`
  revision without traffic (the first build creates the service), a smoke on
  the tag URL, and a promote of exactly that revision. The smoke expects
  exactly `403` from Cloud Run IAM for an anonymous `GET /v1/status`, then
  calls it with an ID token of the service account and checks the reported
  provider, model, location and libraries. The deploy uses one instance, 2 vCPU
  and 4 GiB, a concurrency of 20 and a 900 s timeout for the run queue's open
  streams, no sandbox launcher, and `--update-env-vars` only. The provider, the
  models and the libraries are substitutions, so a deploy switches the model
  arm without a code change, while the budgets stay at the settings defaults.
  The deploy refuses to run without the renderer's URL, and it always lets
  anyplot-api's identity and the smoke's account call the service. The config's
  header lists the owner's bootstrap steps. (#12121)
- **A CI job that builds and smokes the agents image before merge.**
  `ci-image.yml` builds `agents/Dockerfile` when the service, `core/`, the
  catalogue prompts it reads or the dependency lock change. It checks that
  `/v1/status` reports the configuration its environment sets, that the
  production default refuses an anonymous caller with `401`, that the prompts
  and fonts are in the image and the eval cases are not, and that the service
  runs as uid 1000. `tests/unit/agents/test_image.py` holds the Dockerfile's
  COPY list, its build check and the root `.dockerignore` against every file
  the service reads, and the deploy's substitutions and variables against the
  settings; it also runs the deploy step's script against a fake `gcloud`.
  (#12121)
- **`AGENT_MAX_ATTEMPTS` bounds the agent pipeline's adapter attempts.** The
  plot pipeline makes 1 to 3 attempts, 2 by default, so the design's "at most
  one repair round" stays what the service runs. The eval harness takes
  `--max-attempts` and records the effective value in the report's stamp, so a
  run can measure what a second repair round buys, or what the first attempt
  achieves without one. Every attempt after the first needs the repair's 75 s
  of the soft deadline and allows a full file, and feedback goes to the next
  attempt before any review while one is left. `PlotResult.attempts` now
  accepts 3, and the report counts a pass from any repair attempt as repaired. (#12119)
- **A footer strip on every user plot the agents service serves.** The PNGs of
  the artifact route and the images of the feedback bundle carry a strip below
  the plot, "made with any.plot()" on the left and "anyplot.ai/<spec-id>" on the
  right, in JetBrains Mono with the dot drawn as a brand-green square (the
  owner's variant `s1c-jb-sq2` of 2026-10-10). `agents/anyplot/render/watermark.py`
  composites it at image level after the run and scales it with the canvas, so
  a 3200x1800 render is served as 3200x1864 and the square format as
  2400x2448; the plot above the strip stays pixel-identical. The gates, the
  reviewer, the render store and the exported `plot.py` keep working with the
  raw render, so the downloaded code reproduces the plot without the strip.
  The route composes it once per theme and caches it in the render store, a
  cache that gives way to new renders before the store reports itself full;
  `AGENT_WATERMARK=false` serves the raw renders, and the eval harness sets it
  so its renders stay comparable with its baselines. JetBrains Mono 2.304 is
  vendored unmodified under the SIL Open Font License 1.1 with a notice in
  `agents/anyplot/render/fonts/` and loads when the service starts. The chat
  page's result card takes the loaded PNG's own aspect instead of a fixed 16:9,
  and the local BFF mock draws the same strip. (#12117)
- **The "Use with my data" chat page, for admins.** `/debug/agent?spec=&library=&language=`
  (`app/src/pages/AgentChatPage.tsx`) talks to the agent chat BFF: paste up to
  200 KB of CSV, TSV, semicolon CSV or JSON, check the 20-row preview, the
  parser's warnings and a column dropdown for every spec role (the server's
  defaults preselected, a series family such as `y1, y2, ...` one dropdown per
  member plus one for the next), then `.create_plot()` and refine in plain
  words. A progress timeline follows the stream's `status` events, a small
  counter in the chat's corner shows the place in the run queue, `.stop()`
  calls the cancel route and waits for the server to end the run, the library
  pills switch the session's library, and refusals and errors show their code
  and request id. The page starts nothing the server would refuse while a
  turn, a theme render, a parse or a binding change is in flight, deletes its
  server session on a reload or a closed tab, and reloads once when an
  expired Cloudflare Access session leaves a request without an answer. It is
  built only with `VITE_ENABLE_AGENT_CHAT=true` (off in `app/cloudbuild.yaml`,
  where the route answers the 404 page and the chunk is not in the bundle) and
  opens only for local development or an admin's browser. (#12114)
- **A result card per plot version.** `app/src/sections/agent-chat/ResultCard.tsx`
  shows the rendered plot from its blob URL with the plot page's overlay
  actions (copy the PNG to the clipboard, with a download where the browser
  cannot, download it, open it full size), a light and dark switch that
  renders the other theme through the theme toggle route without a model call,
  the adapted `plot.py` with syntax highlighting and one-click copy, downloads
  of `plot.py` and `data.csv` under the names the code reads, what changed,
  the residual notes, a refine composer and a slot for the quick-feedback
  control. Earlier versions stay in the thread, collapsed. (#12114)
- **A `.adapt()` button on the plot page.** The fourth overlay button of the
  implementation view opens the chat page for that spec and library with a
  full navigation, so Cloudflare Access can intercept it. It shows only when
  the build has the chat, the browser is in local development or carries the
  admin hint that the debug page now sets after a successful `/debug/status`,
  and the BFF's eligibility route accepts the pair, so a public visitor never
  sends a request to the debug API. (#12114)
- **Analytics for the agent chat, with enum properties only.** The pageview
  `/debug/agent` and the events `agent_open`, `agent_data_parsed`,
  `agent_plot_rendered` and `agent_guardrail_block`, plus `copy_code` with
  `page: agent_chat`; none of them carries message text or data. (#12114)
- **A local mock of the agent chat BFF.** `node app/scripts/agent-bff-mock.mjs`
  serves the documented `/debug/agent/*` routes on the loopback interface, a
  scripted `anyplot/1` stream (queue positions, the pipeline steps, a plot, a
  reply) and PNGs drawn from the pasted data, plus the catalogue routes the
  plot page needs for `scatter-basic` and `line-multi`, so the whole flow runs
  in a browser without the API, the agents service, a model or the production
  database. (#12114)
- **A model-regression harness for the agent network.** `uv run --extra
  agents python -m agents.evals.matrix` runs eval cases through the real
  `/v1` flow in process (the same plugins, run queue, judge, pipeline and
  gates as a user's request) with the models the flags name (`--provider`,
  `--model`, `--judge-model`, `--location`) and the render backend
  `--renderer` names (`remote`, `local`, or `fake` for a dry run). Per case it
  records the status, attempts, gate failures by gate, validator rejections,
  edit-apply failures, the reviewer's verdict, LLM calls, tokens by kind,
  `model_version`, the cost at list price and the latencies, writes a JSON
  report and a Markdown summary, prints a diff table against the pinned
  model's baseline over the cases both runs hold, and exits non-zero when the
  pass rate on those cases drops below it or a run crashes in the harness.
  A preflight render before the first case, an outage stop (the renderer
  unavailable, or three errors in a row) and `--gcloud-token`, which renews
  the developer's renderer token during a long run, keep an outage from
  turning into a matrix of failed runs or a baseline. `--budget-usd` stops a
  run before a case that could take the estimated cost past the budget. A
  review page samples 30 renders that passed the gates with an accept and
  reject pair each and exports the owner's judgements as JSON, so one command
  answers spike X and every later model or prompt comparison. (#12116)
- **A blind two-run review gallery.** `python -m agents.evals.report blind`
  merges two harness reports into one page that shows both runs' renders of
  the same cases in random order without naming the run, and `report score`
  turns the exported judgements into an acceptance rate per run, so spike X
  picks the phase-1 model by an unbiased judgement. (#12116)
- **A catalogue eligibility sweep.** `python -m agents.evals.eligibility`
  normalises and scans every matplotlib and seaborn file in `plots/`, without
  a model call, and counts the eligible, coupled and blocked pairs, the
  blocked ones by reason (SECURITY findings by rule id, a missing `THEME`
  block, a savefig target other than `f"plot-{THEME}.png"`, the map specs).
  (#12116)
- **The spike-X eval cases and the first baseline.** 120 synthetic cases: 10 specs from 10 plot
  families, each eligible in matplotlib and seaborn, times six datasets
  (renamed headers, values times 10, 12 rows, 5,000 rows, `DD.MM.YYYY` and ISO
  dates, and semicolon text with decimal commas), written by the seeded,
  rerunnable `agents/evals/make_fixtures.py`, which a unit test keeps in sync
  with the committed files. The smoke set is 12 of them plus the two
  hand-written cases. `agents/evals/baselines/claude-haiku-5-5.json` is the
  first baseline: the spike-X run of 2026-10-10 on the Claude Haiku 5.5 arm,
  where 102 of the 122 runs passed the gates (83.6 %) at $0.52 list price.
  (#12116)
- **The anyplot-renderer service that runs adapted plot code in Cloud Run
  sandboxes.** `agents/renderer/` is a small FastAPI service with
  `POST /render`, `POST /render/{job_id}/cancel` and `GET /status` behind
  Cloud Run IAM and the same ID-token claims check as the agents service. It
  runs every theme of a job in a sandbox of its own, one at a time, built on
  what spikes S and S2 measured: no `--write` and no egress, an explicit
  `PATH`, the run directories on a 512 MiB in-memory volume that the service
  requires on Cloud Run, a host watchdog that kills a run past 64 MiB,
  10,000 files or a 512 MiB `MemAvailable` floor and checks the directory
  budgets once more after the code exits, a kill that counts only once the
  launcher has exited, one retry when the launcher fails before the harness
  starts, bounded stdout and stderr, a cleaned probe, and the rlimits 60 s
  CPU, 50 MiB per file, 1 GiB address space and 64 processes. `job_id` and
  the requested themes are an idempotency key: a replayed request joins the
  render in flight or gets the stored answer, never a second run, and
  another payload under the same key is refused with `409 job_conflict`. The last caller to leave, or a cancel,
  stops the sandbox, an unexpected error answers a JSON `500 internal`
  without its message, and a launcher that outlives its kill ends the
  instance so Cloud Run starts a fresh one.
  It only runs code; the host gates stay in the agents service. Its image
  installs the plotting libraries without ADK, CI builds it and renders a
  seaborn plot through the harness before merge, and
  `agents/renderer/cloudbuild.yaml` builds it, deploys a candidate (creating
  the service on the first build, and only when the service is not found),
  smokes it with an anonymous call and a real render, and promotes it. (#12115)
- **A `remote` render backend, now the default.** `AGENT_RENDERER=remote`
  sends each render to `AGENT_RENDER_URL` with an ID token from the metadata
  server, or in development from `AGENT_RENDER_TOKEN` or the developer's
  Application Default Credentials, so a local `adk web` and the deployed
  agents service render in the same sandboxes. It rides out a cold start by
  retrying connection errors and Cloud Run front-end 429 and 5xx answers
  after 1, 3, 8 and 15 seconds, asks the renderer to cancel a render it
  abandons, and logs every failure it maps to a renderer error. When the
  renderer stopped a run at a limit, the repair feedback names the limit and
  the measured value. The in-process `sandbox` backend stays as an unused
  stub. (#12115)
- **A run queue in front of every agent chat turn.** The anyplot-agents
  service now runs one pipeline run at a time (`AGENT_RUN_CONCURRENCY`, 1)
  and starts at most one a minute (`AGENT_RUNS_PER_MINUTE`, 1, a sliding
  window), so one 4 GiB instance never holds more than the one sandbox that
  spikes S and S2 showed it serves safely. A turn waits at most
  `AGENT_QUEUE_MAX_WAIT_S` (600 s) and the queue holds as many turns as that
  wait allows (10); past that the turn gets `503 capacity`, or
  `error{code:"capacity"}` when it waited the maximum. While it waits, the
  stream sends `status{step:"queued", position, waiting}` and the request
  deadline has not started; `GET /v1/status` reports `waiting` and
  `in_flight`, and a user with a queued turn gets `409 run_active` like one
  with a running turn. A user already over the daily token budget gets the
  `budget` refusal at once instead of a place in the queue. A `premium` lane
  goes before the normal one but nothing sets it yet. (#12112)
- **Serial renders for every backend.** `AGENT_RENDER_CONCURRENCY` now
  defaults to 1 and is enforced in one place, `SerialRenderer` in front of
  whichever backend renders, one theme per slot, so the sandbox, local and
  fake backends cannot run two renders at once. A freed slot goes to a
  waiting pipeline render before a waiting theme toggle. (#12112)
- **One theme per run, and a theme toggle that costs no tokens.** A run
  renders and reviews only the theme the user asked for (light unless they
  ask for a dark plot), so the host gates, the reviewer's defect lines, the
  padded fallback, the artifacts and the exported `plot.py` run line all name
  that one theme. `POST /debug/agent/sessions/{sid}/versions/{version}/render
  {theme}` (and its `/v1` original) renders the other theme of a finished
  version from its stored code and data through the render backend and the
  host gates, with no adapter, no reviewer and no queue, and answers `ok`,
  `needs_attention` (a padded canvas) or `failed` with the version's
  artifacts. A toggle and a turn refuse each other in a session, a user has
  one run or toggle in flight, a toggle waits at most 120 s for the render
  slot, and a theme that failed the host gates is rendered at most twice. (#12112)
- **A hard cap on one relayed chat turn.** The BFF ends a turn by
  `AGENT_TURN_MAX_S` (590 s), below anyplot-api's 600-second request
  timeout, so every stream still ends with `error` and `done`: a turn still
  queued when its run could no longer finish inside the cap ends with
  `capacity` and leaves the queue before it spends a token. (#12112)
- **The ADK runtime core of the agent network ("Use with my data").**
  `agents/` now runs: the root agent `anyplot` with four session tools and
  the `plot_pipeline` NodeTool, one single-turn adapter per enabled library,
  and a tool-less reviewer that sees both renders; a bounded pipeline (two
  adapter attempts, one review, one repair, a soft deadline and a budget
  check before every model call) that always ends in a `PlotResult`; the
  ScopeGuard, Budget and ToolSafety plugins with a content-free attribution
  log; the render layer (probe harness, R1-R3 host gates with PNG hardening
  and a padding fallback, advisory G-gates, fake and local Docker backends;
  the Cloud Run sandbox backend waits for its spike); and the private `/v1`
  FastAPI service with the `anyplot/1` stream the BFF relays. The model is
  Claude Haiku 5.5 on Vertex AI by default, with Gemini 3.8 Flash as the
  second arm behind `AGENT_PROVIDER`, so price and quality can be compared
  later; ADK 2.11 sends no response schema to Claude, so a structured answer
  goes through a forced tool call. Instructions are composed from prompt
  files plus the catalogue's style guide, library rules and repair and review
  excerpts, read verbatim. `AGENT_DEV_FIXTURE` seeds `adk web` sessions from
  two fixture cases in development only. Untrusted text (pasted headers, spec
  text, model-written notes) reaches every model only inside fences, a render
  error reaches the repair as its exception class and line but never its
  message, a render ships only with both themes, the protected theme lines
  survive any plan, and `ENVIRONMENT` defaults to `production` so a missing
  variable never skips the caller check. (#12111)
- **Deterministic code handling for "Use with my data" in `agents/anyplot/code/`.**
  Plain Python with no ADK import that turns a catalogue implementation into
  code the agent network can adapt and run: `regions.py` finds the THEME
  block, the Imprint palette, the `df = load_user_data()` placeholder, the
  savefig calls and the canvas keywords by AST; `normalise.py` removes the
  catalogue header, empties the catalogue title string (648 of 650 files),
  removes the `sys.path` guard family (`sys`, `__file__`,
  `importlib`, `pathlib`, `os.chdir`) and path-wrapped savefig targets, drops
  `bbox_inches` and rescales the dpi so that `figsize * dpi` renders exactly
  3200x1800 or 2400x2400 (638 of 650 matplotlib and seaborn files; 10 of 10
  rendered legacy `bbox_inches="tight"` files came out exact); `readiness.py`
  classifies a pair as blocked (13 map specs, disabled library, SECURITY
  findings, no THEME block, single-theme or other non-standard savefig
  target), coupled (literal limits, data-coordinate annotations, literal
  statistics, short palettes, fixed date locators, synthetic data, each a
  line-naming hint for the adapter) or clean (78, 535 and 37 of the 650
  matplotlib and seaborn files); `edits.py` applies an
  `AdaptPlan` with exact-once matching and protected regions; `loader.py`
  swaps the placeholder for a relative `pd.read_csv("data.csv", ...)` with
  dtypes from the dataset profile; `export.py` adds the attribution header to
  the downloadable `plot.py`. A catalogue sweep in the unit tests keeps the
  normaliser idempotent and on the canvas for every reachable figure size.
  (#12110)
- **Two-profile AST validator for the plot pipeline.** `agents/anyplot/code/validate.py`
  implements the SECURITY and ADAPTATION profiles of the agent-network design
  (`docs/concepts/agent-network.md`, "Adapt and validate") with no ADK import:
  `validate_security` checks the import surface (COMMON plus the matplotlib or
  seaborn allowlist, every component of an import path so an alias cannot hide
  `pandas.io`, `os` only as the THEME lookup), the banned builtins and
  attributes, every dunder in identifiers and string literals, the pandas and
  numpy I/O calls (also when reached as a string through `df.agg(...)`), classes
  and async or generator statements, URL and oversize literals and the exact
  `f"plot-{THEME}.png"` savefig target; `validate_adaptation` checks the single
  `df = load_user_data()` placeholder, bans random data generation except a seeded
  `default_rng` used for jitter and subsampling, caps numeric literal lists at 20
  values and keeps the Imprint palette prefix, also against later mutation of the
  list. Invalid code never raises: size, encoding and syntax problems, including
  those only the compiler reports, are findings too. The tests cover every rule with a
  failing snippet and its nearest allowed sibling, every bypass the design names,
  and the whole catalogue corpus, which prints a per-rule summary under `-s`.
  (#12107)
- **Vertex AI budget guard.** A Cloud Run function in `automation/gcp/budget-guard/`
  receives the Cloud Billing notifications of the budget `anyplot Vertex AI cap`
  through an Eventarc Pub/Sub trigger and disables `aiplatform.googleapis.com`
  through the Service Usage API once the month's cost reaches the budget amount.
  It acts only on that budget's name, never enables anything, is idempotent
  under Pub/Sub redelivery, logs one structured line per message without the raw
  message, and has a dry-run switch for the first proof at 5 CHF. Budget
  notifications lag the spend by hours, so it bounds the damage rather than
  making the cap exact. Code only, not deployed: the runbook in its README and
  `docs/reference/gcp-budget-guard.md` carry the deploy, test and recovery steps.
  (#12109)
- **Adaptable catalogue code design document.** `docs/concepts/adaptable-code.md`
  describes how catalogue implementations become code that people who copy it
  from the code tab, and the planned "Use with my data" agent, can point at
  other data: one `# Data` block ending in a tidy `df`, domain-named column
  constants with a role comment, a static checker plus a perturbation smoke run
  in impl-generate, the regen gate's adapt route and adapt regression, and a
  rollout through the normal daily regeneration. It records the owner's
  decisions of 2026-10-09 (score-neutral first, all 15 libraries, no targeted
  pass) so the rules PR is reviewable before anything is built. (#12108)
- **Deterministic data handling for the agent network: parser, data roles,
  default bindings and the dataset store.** `agents/anyplot/data/` turns pasted
  CSV, TSV, semicolon, pipe or JSON text (at most 200 KB, 50 columns, 20,000
  rows and 200 characters per cell; control characters refused, zero-width and
  bidi characters stripped) into a canonical `data.csv` with comma delimiters,
  dot decimals, ISO dates and canonical headers, plus the `DatasetProfile`, a
  20-row preview and the dtypes the loader passes to `pd.read_csv`. Typing is
  explicit rather than left to pandas: dates are tried before numbers, so a
  `DD.MM.YYYY` column never reads as a thousands-dot number, and a decimal
  comma is accepted only when the whole column has that shape. The roles
  parser reads a spec's stored `## Data` bullets into typed roles, including
  variadic families such as `y1, y2, ...` (all 325 catalogue specs parse),
  default bindings match role kinds to column dtypes before name similarity,
  `check_bindings` validates roles, columns and dtype compatibility, and an
  in-memory, session-owned dataset store with an idle sweep and a 64 MB cap
  keeps parsed data out of ADK state. None of it imports ADK or ships in a
  service yet. (#12106)
- **Agent chat BFF under `/debug/agent`, shipped dark.** `api/routers/agent.py`
  puts the admin-only routes of the planned "Use with my data" chat in front of
  the private anyplot-agents service: status, eligibility, sessions, dataset,
  bindings, messages, cancel, artifacts, and delete. They sit behind the
  existing `/debug` admin gate, a kill switch (every route answers 404 until
  `AGENT_ENABLED` is on and both `AGENT_SERVICE_URL` and `AGENT_USER_ID_KEY`
  are set), and a CSRF guard (`X-Anyplot-Client` header, Origin check, JSON
  bodies). The agents service sees an HMAC user id, never an email; request
  bodies are allowlisted; a catalogue snapshot comes from the database; and the
  chat stream is re-framed into the `anyplot/1` SSE events, so unknown events,
  `error_details`, and stack traces never reach the browser, and every stream
  ends with `done`. `require_admin_identity()` now returns who passed the admin
  gate, and `require_admin` wraps it unchanged. The deploy writes
  `AGENT_ENABLED=false` and its smoke test expects 401 on
  `/debug/agent/status`; the routes are documented in `docs/reference/api.md`.
  (#12103)
- **Shared canvas gate in `core/canvas.py`.** The canvas check that
  `impl-review.yml` runs inline (3200×1800 or 2400×2400 within ±16 px, the
  nearer target, the signed delta and the per-library likely cause) is now a
  pure function, `check_canvas`, plus a PNG reader that refuses files without
  the PNG signature and a `python -m core.canvas <png>` CLI that prints the
  workflow's lines and exits non-zero on drift. The module also holds the PNG
  auto-reject checks AR-04 (blank) and AR-07 (format), ported from
  `scripts/evaluate-plot.py`. AR-04 counts the most common color instead of
  that script's near-white and near-black thresholds: the near-white rule
  can never flag a blank render on the light `#FAF8F1` page, and the
  near-black rule flagged 6 of 24 sampled dark catalogue renders, while the
  one-color rule flags none of 48. A parity test runs the workflow's own
  script on the same PNGs and requires identical output, so the workflow can
  switch to the module later without changing a byte of the repair feedback.
  (#12102)
- **Review feedback grammar in `core/defects.py`.** The defect-line and
  suggestion-line grammar, the criterion IDs, `nothing_to_repair` and the spec
  characteristics parser now have a canonical, stdlib-only home that the
  planned agents service can import, plus a `format_defect` builder whose
  lines read back through the same parser. `regen_gate.py` keeps its own copy
  for now, because the workflows run it as a single-file copy where `core` is
  not importable; a parity test checks both copies against the catalogue's
  stored weaknesses and every spec. (#12102)
- **`agents/` package skeleton with the ADK pin and the pipeline contracts.**
  The first code of the agent network: optional extras `agents` and
  `agents-eval` pin `google-adk==2.11.0` exactly, `AgentSettings` reads the
  `AGENT_*` variables with the pinned Gemini model, judge model and `eu`
  location as defaults and refuses `-latest` aliases, regional locations such
  as `europe-west4` and the local renderer outside development, and
  `agents/anyplot/schemas.py` holds every contract of the design's "Contracts"
  section with its size limits, including a `Defect.as_line()` that renders
  the regen gate's defect grammar. CI installs the extra for tests and type
  checks `agents/`; the Docker allowlist admits `agents/` and the two prompt
  sources the adapter reads. No agent runtime ships yet, and the API image
  does not grow; its only change is `google-auth` 2.48.0 → 2.61.0 in the
  shared lock, because `google-genai` 2.29 (pulled in by ADK) needs 2.56 or
  later. (#12101)
- **Agent network design document.** `docs/concepts/agent-network.md` describes
  the planned "Use with my data" agent network on Google ADK 2.11 and Gemini
  3.8 Flash through Vertex AI: the agent roster, the adapt, render and review
  pipeline, the two-profile code validator, the Cloud Run sandbox renderer, the
  guardrail layers, quick-feedback capture, a model-version regression harness,
  serving on a separate Cloud Run service behind the `/debug` gate, the phased
  roadmap with spikes and exit criteria, and the owner tasks. Design only; no
  code ships with it, so the decisions are reviewable before anything is built.
  (#12099)

### Changed

- **The privacy policy covers the data assistant preview.** The legal page now says,
  in a part scoped to the people who use it (browsing the catalogue is unaffected),
  what the admin-only "use with my data" chat does with what you give it: Claude models
  through Vertex AI in the EU, in-memory sessions, the content-free and pseudonymous usage
  telemetry (180 days), the HMAC-keyed attribution lines (30 days), the feedback cases
  (files 180 days, the row until you ask), and a legal basis per purpose. The "the ai never
  sees a visitor's request" line now separates browsing the catalogue from using the
  assistant, and the processor table gains an "ai assistant" row (#12208).
- **`.to_long()` names its new columns in the session language.** German sessions get `Wochentag`
  and `Wert` instead of `Weekday` and `Value` (French, Spanish, Italian, Portuguese, Dutch and
  Polish too; English otherwise). The language route and every turn's `done` return the
  recomputed offer, so the data panel's card always names what `.to_long()` applies. (#12207)
- **A session is kept only when the user took a result away and was content.** The `sessions` view
  and the `/debug` card count a copy or a download after the last run without a `thumbs_down` or
  `bug` feedback; a saved session alone is no keep (new states `rejected` and `saved`). The card
  shows the counts behind the kept and repair rates (`5 of 12`), and the `usage` view counts a kept
  session once, under the day, spec and library of its last shipped plot. (#12207)
- **`.to_long()` gives the new columns meaningful names.** The names column says what the melted
  headers are (`Weekday`, `Month`, `Year`) or `Category`, and the values column is `Value`, instead
  of the roles' names `y` and `value`, which became the plot's text; a name an input column already
  has gives way, so the route never fails on pandas' `melt`. The new columns stay
  bound to the roles they were made for whatever their names, and the summary offers a rename when
  the notes or the file name say what the values measure. (#12206)
- **The agents service writes its attribution log to stdout**, so the content-free `pipeline_*`
  lines reach Cloud Logging. (#12204)
- **The adapter keeps the data's first-appearance order for categories** unless they are ordinal,
  and the checklist reviewer can file SC-04 for legend defects. (#12204)
- **Three plot-quality rules from the agent chat's live tests, in the shared
  style guide and rubric.** Ordered categories (Likert levels, grades, sizes)
  take ordered steps of one Imprint ramp in their natural order, with a red or
  green pole only on its matching side (VQ-07); labels that tell the reader
  nothing, such as "100 %" on every bar of a 100 % stacked chart, are clutter
  (VQ-03); axis and legend titles are text for a reader, not raw column
  identifiers (`Reaktionszeit_ms` → "Reaktionszeit (ms)", VQ-06), and a legend
  after a reshape names the level ("Q1"), not the full header (SC-04). They
  live in `prompts/default-style-guide.md` and `prompts/quality-criteria.md`,
  which the catalogue pipeline and the agent's adapter and reviewer both read,
  so one edit changes the rule for both; the agent prompts that used to exempt
  every column name as written now point at the shared rule (#12203).
- **A refused paste says what it fails on.** The agents service answers
  `unparseable` and `too_long` with a `cause`, which the BFF passes on one
  capped line (cut at a word, control characters removed) and the page shows
  in place of its own text: "the header has 3 fields, but line 3 has 4; line 4
  has 2", the line and column of a JSON or Python error counted from the
  paste's first line, the row and length of an over-long cell, the actual row
  count past the cap. Owner rule of 2026-10-16: people paste reasonably clean
  data, but a refusal names its cause. (#12201)
- **Ragged rows are listed, never repaired.** A table with values past its
  header's last column names every ragged line with its field count, short
  ones included; empty fields past the last column are left out with a counted
  warning, and the warning about short rows names their lines. (#12201)
- **Computed roles take a column when the data has one.** A role the plot can
  compute, such as the rolling average of `line-timeseries-rolling`, the
  Bollinger bands of `indicator-bollinger` and the fitness, fatigue and form
  of `line-training-load-pmc`, is now optional. The default bindings bind it to
  a column whose name clearly holds it (`SMA 20`, `BBU_20_2.0`, `Fitness (CTL)`),
  never one a required role needs or whose name says it is something else
  (`Upper Shadow`, `Volume SMA`), and warn when its window differs from the
  spec's (`SMA 200`),
  you can bind any column by hand, and the data panel shows
  `— computed by the plot —` while it is open. The adapter learns per role
  whether to use the bound column or compute the value from the data. (#12195)
- **Catalogue rubric: per-mark labels must fit their marks.** The style
  guide gains a "Per-mark Labels and Decorations" rule (value labels, dots on
  bar ends and shadows drawn once per bar or point stay only while each fits
  its mark, which rarely holds past about 25 marks; otherwise drop them or
  label the extremes), and the VQ-03 rubric and the review's proportional
  sizing check deduct crowded per-mark labels in proportion. The agent's
  adapter now points at this one shared rule instead of carrying its own
  copy (#12189).
- **Copilot gets the "proper lint fixes only" rule.** The lint task line in
  `.github/copilot-instructions.md` now says to fix the cause and never add
  disable comments (`eslint-disable`, `noqa`, and similar) without the owner's
  explicit approval, matching `CLAUDE.md`; the instruction tests pin the rule on
  both sides. (#12190)
- **Copilot instructions agree with CLAUDE.md.** `.github/copilot-instructions.md`
  now carries the "fix small build/test blockers directly, even when out of
  scope" rule (under ~20 lines, ask first above that) instead of telling Copilot
  to leave pre-existing failures alone, drops the `pip` fallback in favour of
  `uv` only (now stated in both guides), and lists new plot types as a
  `spec-request` issue rather than a hand-written implementation. The
  instruction tests pin both rules on both sides. (#12188)
- **The plot of the day features standout plots and rotates without repeats.**
  It used to be a random pick among every implementation scored 90 or more, so
  a plain chart such as a Pygal precision-recall curve could take the front
  page. It now draws from a featured pool (score 92 or more, no `-basic` spec,
  falling back to every 90+ implementation when the pool is empty), walks the
  pool's specs in an order shuffled per cycle so no spec repeats within a
  cycle, and picks the library per day among that spec's featured
  implementations. (#12185)
- **The agent's adapter works to the reviewer's rubric, and fewer plots go to a repair.** The adapter's
  instruction now holds the very rubric sections the reviewer scores with (scoring principles, anchors,
  the 5c and 5d checks) instead of thirteen one-line criteria rows, so the first try knows what will be
  judged. A render needs 95 % of the technical points instead of all of them to skip the repair round
  (`AGENT_REVIEW_BAR`, owner decision pending), measured gate findings such as clipped or overlapping
  text go to the self-review and the review before they start a repair (`AGENT_GATE_REPAIR`), and a
  repair round is no longer proofread before its review (`AGENT_REPAIR_SELF_REVIEW`). (#12178)
- **The G9 plotted-points limit is 500,000.** Dense user data such as 20,000 rows of 24 series no
  longer draws a DQ-03 note; the stress cases' 610,000 and 1,000,000 computed points still do.
  (#12178)
- **Constant text columns of a paste move to the notes.** A pasted column with
  the same text in every row, such as `Kanton` = `Schweiz` in a statistics
  export, becomes a note line (`Kanton: Schweiz`), as a one-category JSON-stat
  dimension already did, unless fewer than two columns would remain; when the
  notes are not kept, the columns come back. (#12179)
- **Pasted data takes up to 1 MB, computed data up to 2 MB.** The paste cap
  rose from 200 KB to 1 MB in the parser, the agents route, the BFF and the
  data card's counter; rows (20,000) and columns (50) keep their caps. Data the
  assistant computes keeps full float precision under its own 2 MB cap, so a
  10,000-step run with six columns (about 1.1 MB) fits as it is. A parse whose
  canonical CSV passes 4 MiB, the render job's limit, is refused. (#12176)
- **Agent chat answers at once; only sandbox work waits in the run queue.** A
  chat turn no longer enters the run queue or the one-start-a-minute rate
  window: a question, a refusal, `prepare_data` and `generate_data` answer
  right away, and only a `plot_pipeline` or `run_data_code` call takes the
  queue's slot and the turn's start, mid-turn, while the stream reports
  `status{step:"queued"}` and the request deadline pauses, resuming with the
  time it had left once the slot comes. A full queue now
  ends the turn with `error{code:"capacity"}` instead of `503 capacity` before
  the stream. To keep chat turns bounded, each user may send 10 messages a
  minute and 200 a day (`AGENT_USER_MESSAGES_PER_MINUTE`,
  `AGENT_USER_MESSAGES_PER_DAY`), checked before the scope judge and answered
  with the fixed `rate_limited` or `daily_limit` refusal, and a session closes
  at its third `out_of_scope` or `attack` refusal (`AGENT_SESSION_REFUSALS`;
  `needs_data` never counts), answering every later turn with
  `session_closed`. Owner decision of 2026-10-14, after a live test in which
  plain answers waited about 60 seconds each. (#12175)
- **The scope judge treats data-generating code as in scope.** A snippet or formula
  whose job is to generate the plot's data is now in scope in any language. Code with
  another purpose is out of scope, and code that touches files, the network, or the
  system is an attack. Scope case `off-053`, a sine wave for homework, is now in scope.
  (#12172)
- **Pasted data sets the chat's language.** When you paste data into "Use with
  my data" before typing anything, the session language follows the notes
  around the table, or else the column names, with the new source `pasted`
  (`lang: de · from data` in the chat header). The two judges that already
  screen a paste name the language, so no model call is added; English or
  unclear notes and headers such as `temperature_2m_max` leave the current
  language unchanged. A typed message still replaces it,
  and a paste never overrides a typed or chosen language. The dataset route
  answers the session language as `language: {language, source}`. (#12171)
- **Pasted data with notes, metadata or a total around the table parses.** The agent's
  parser finds the table among the pasted lines by its data rows: a title, an export's
  metadata (such as the two lines above an Open-Meteo download's header) or a sentence
  that explains the columns above it, a source line or a note below it, and up to three
  summary rows at the end (`Total`, `Summe`, `Mittelwert`…) are left out, each with a
  warning in the preview. Before, the first line was always the header, so a raw
  Open-Meteo download lost its data columns. (#12166)
- **The agent's plot pipeline reviews with the catalogue rubric and proofreads itself.** The
  reviewer now scores each render with the catalogue rubric (the offline scorer's twin; the
  code decides from the points), every round is reviewed and the best-scored version ships,
  and before each review the adapter checks its own render against the rubric's technical
  rows, which never counts as a repair. A shipped plot at or above 95 % of the technical
  points shows without notes. The experiment switches behind it (`AGENT_REVIEWER_MODE`,
  `AGENT_REVIEW_BAR`, `AGENT_STATUS_BAR`, `AGENT_SHIP_BEST`, `AGENT_SELF_REVIEW`, and the
  highlight switches) stay settings. (#12165)
- **A complicated plot gets the time and the tokens to finish.** The adapter and the
  reviewer think at high effort with 8,192 and 4,096 tokens of thinking room (2,048 cut 10
  of 80 first adapter calls on Vertex) and the root at medium; the pipeline's soft deadline
  rises from 140 s to 480 s (hard 540 s, Cloud Run timeouts 1200 s) and the per-request
  token budget to 800k, so a repair round is no longer skipped for time. A repair whose edits do
  not apply gets one retry in the same round, and an unreadable review is asked once more
  instead of shipping the render unreviewed. (#12165)
- **After the first plot, `.create_plot()` is `.start_over()`.** Next to `.send()`,
  which changes the latest version, the button now says what it does: a new plot
  from the catalogue plot with this data, without the earlier changes (#12156).
- **The language example is a real language.** The chip's free-text field and the
  tool descriptions name `Swedish` instead of `Klingon`, an example that invited a
  language the plot text then did not use (#12156).
- **The overlap gate G7 measures every drawn text, not only tick labels.** An axis
  label, title, legend text or annotation that overlaps any other text by more than
  3 px becomes an advisory VQ-02 line naming both roles and the depth, such as "the
  radial axis label overlaps the tick label by 36 px", with a polar hint when polar
  axes are involved. The owner's polar case had the label `y` on the `270°` tick
  label, which the reviewer read as a missing label; the probe now catches it
  (#12152).
- **The plot run's progress is a grid of rounds that says how each round ended.** One
  row per round (`first try`, `repair 1`), the same four steps lined up in the same
  columns, and the outcome on the right: `✓ ok`, `✗ review: 3 findings`,
  `✗ 2 measured`, `✗ code check failed`, or `~ 1 finding open` for a shipped result
  that still needs attention. The step a round stopped at is marked. The pipeline
  reports each round's outcome as `PlotResult.rounds` and on the `repairing` status,
  and the result card keeps the grid under `# rounds` (#12150).
- **A repair reads as one more round, not as every step again.** The chat's progress
  timeline folds a finished round into one entry (`first try done`) and lists only
  the current round's steps, instead of repeating each step with `· attempt 2`; the
  result card says `1 repair` instead of `2 attempts` (#12149).
- **Text in an agent plot follows the session language instead of always
  English.** The adapter writes the title, axis titles, legend entries and
  annotations in it, while column names and labels from the data keep their
  spelling; a change whose base version was written in another language
  rewrites them (`language_changed`, whose 300-character literal budget grows
  by 1.5 times the text the plan replaces, so a long new annotation does not
  ride along); and the reviewer judges the plot text against it under VQ-06,
  fail-open. Code, comments and the internal change notes stay English, and
  earlier versions keep their text. A chosen language is free text, so every
  prompt that carries it, the root's session block included, fences it as
  `<plot_language>`. The refusals sent before the scope judge runs follow the
  session language instead of the browser locale. Prompts changed: `root.md`,
  `adapter.md`, `reviewer.md` and `scope_judge.md`. (#12145)
- **The agent chat shows when it works, and why the controls wait.** After
  `.parse()` the card says `# parsing your data …` under the button, and every
  turn without pipeline steps (the summary, a question, a data request) puts an
  in-progress line in the assistant's slot of the thread, `summarizing your
  data …` or `working on your message …`, until the reply or the first pipeline
  step replaces it; the progress timeline shows only for a plot run, a queue
  position or pipeline steps, so the two never say the same thing. While
  anything is in flight the bindings block says `# bindings and .confirm() wait
  while the assistant works …` instead of leaving the dropdowns silently
  disabled. The lock itself stays, because the server runs one thing per
  session. (#12143)
- **`.create_plot()` is always in the composer once there is data.** Before the
  confirmation it is the quiet button next to `.send()`, and a click calls
  nothing: a notice under the composer says `# confirm the data first ·
  .confirm() sits at the foot of the data card`, and its `.show()` scrolls to
  the button and focuses it (to `.use()` while a table read from text waits;
  the notice follows the card when such a table arrives or is discarded after
  the click). Someone who scrolled to the foot no longer meets a composer that
  hides the step. The server's `data_unconfirmed` stays the backstop. (#12143)
- **A lost confirmation is named where it happens.** When a binding change, a
  data request, an undo or a new paste drops a confirmation the user had given,
  the thread gets a warning notice (`# bindings changed · confirm the data
  again`), the card's step line repeats it next to `.confirm()`, and the pinned
  `! confirm again` header reads as a warning, the phrase in bold on a
  warning-tinted surface, rather than as a neutral line. The step line follows
  the data the card shows: a later data request or undo names the changed
  data, and a later paste, which nobody has confirmed yet, names no loss. The
  first binding setup after a paste, where nothing was confirmed yet, says
  nothing. (#12143)
- **The agent chat has one composer.** The result card no longer carries its
  own `.refine()` box under the code: it duplicated the thread's composer, which
  already reads "ask about this plot, or ask for a change" and sends the same
  turn, and the assistant decides either way whether the text is a change or a
  question. The card keeps the image, the code, the downloads and the
  quick-feedback control; follow-ups go through the one box at the foot of the
  thread. (#12140)
- **The agent chat is one column, and the data is its first turn.** The data card
  (paste, preview, bindings, the `# changed` block with `.undo()`, `.confirm()`) opens
  the thread, the assistant's summary follows it, and a correction in words updates the
  card in place. After `.confirm()` the card collapses into a header pinned at the top
  of the thread, `✓ data fits · N rows · M columns · version V`, whose `.show()` opens
  the full card again without leaving step 2; any binding change, undo, data request or
  new paste takes the page back to step 1 with the card open, and the header stays as
  `! confirm again`, so the card is one `.show()` away from anywhere in the thread. A
  table read from free text holds the page in step 1 until `.use()` or `.discard()`.
  Keyboard focus follows the steps without stealing it from the composer, and a second
  key press never stops the run the first one started. In step 2 the composer's
  filled `.create_plot()` starts the first plot as it is, or, with a note typed first
  ("log scale on y"), sends the note as the turn that makes it; once the library has a
  plot, the composer refines as before. The contracts and the analytics events are
  unchanged; the session hook keeps the confirmation while a table read from text
  waits, so `.discard()` returns to step 2; the root prompt gains two lines: a message in step 2
  before any plot is the first plot with that request (`plot_pipeline` with the
  `change_request`), and numbers about the data in a reply come from the latest tool
  result, never from an earlier turn. (#12137)
- **Step-1 turns skip the run queue's minute rule.** A turn that starts while the
  data is unconfirmed cannot render (the pipeline answers `not_ready`, and nothing can
  confirm the data during a turn), so the queue gives it the slot but counts no start
  in the sliding window: the summary after a paste, a data request and the plot that
  follows the confirmation no longer wait a minute for each other, while whole
  pipeline runs keep one start a minute (`agents/anyplot/run_queue.py`). (#12133)
- **"Use with my data" runs in two steps: the data first, then the plot.** The data
  panel ends step 1 with `.confirm()`: you check the preview and the bindings, confirm
  that they fit, and only then does `.create_plot()` appear. The agents service enforces
  it (`POST .../dataset/confirm`; a plot on unconfirmed data is `not_ready` with
  `data_unconfirmed`), a new paste, a transcription's `.use()` or a binding change drops
  the confirmation, and a library switch keeps it. A step header `1 data · 2 plot` shows
  where you are. The design section "Two steps: data first, then the plot" in the
  agent-network concept doc records the owner's rule and the planned data operations.
  (#12131)
- **The agents think by default.** Claude's adaptive thinking is on for the
  root (`AGENT_ROOT_THINKING_BUDGET`, 1,024 tokens of extra output room) and
  the adapter (`AGENT_ADAPTER_THINKING_BUDGET`, 2,048); 0 turns it off, and
  Gemini ignores both budgets. The measurement of 2026-10-11 on the 122 cases
  through the deployed renderer decided it: with both budgets every run passed
  the gates and 51.6 % ended `ok`, with thinking off 91.0 % and 28.7 % (the
  structured answer then misses its edit anchors in a third of the runs), for a
  median of $0.0063 instead of $0.0038 per plot and a p50 of 31.5 s instead of
  13.6 s. The thinking run is the new Claude baseline
  (`agents/evals/baselines/claude-haiku-5-5.json`). A replayed root thinking block
  whose signature no longer matches the conversation is dropped by the API instead
  of failing the call. (#12129)
- **The API binds the agent user-id secret.** `api/cloudbuild.yaml` adds
  `AGENT_USER_ID_KEY` to the secrets of `anyplot-api`, so the `/debug/agent`
  routes can derive their user ids. Together with `_AGENT_ENABLED=true` and
  `_AGENT_SERVICE_URL` on the deploy-api trigger (set on 2026-10-11), this
  switches the admin-only agent chat on in production (#12128).
- **The agent network's two services are deployed.** The design doc, the
  agents README and the docs index now say that `anyplot-renderer` and
  `anyplot-agents` run in Cloud Run (europe-west4) since 2026-10-11, deployed
  by the `deploy-renderer` and `deploy-agents` triggers, and that owner tasks
  2, 8 and 14 are done except the API trigger's settings; the API side stays
  dark until the user-id secret exists and the API trigger sets the service
  URL and `_AGENT_ENABLED=true`. The recipes stay in the owner tasks for the
  record. (#12127)
- **Claude answers every structured question under a structured-output
  format.** The adapter plan, the reviewer verdict and the judge verdict use
  `output_config.format` with the schema made strict by the SDK's
  `transform_schema`, instead of a forced tool call, so constrained decoding
  guarantees the JSON shape, the types, the enums and the required fields; the
  repairs keep mending the lengths and counts a grammar cannot enforce. Unlike
  a forced tool call, the format lets a thinking model think first. (#12124)
- **The agent validator admits pure computing modules.** By the owner's
  decision, adapted code may import `warnings`, `typing`, `calendar`,
  `decimal`, `fractions`, `zoneinfo`, `enum`, `dataclasses`, `operator`,
  `bisect`, `heapq`, `numbers`, `cmath`, `scipy.fft`, `scipy.linalg` and
  `scipy.constants`. Each was walked for names that read, write, fetch,
  evaluate or set the process locale, and those stay banned, as do `io`, `sys`,
  `pathlib`, `random`, `locale` and `string`. `calendar.main` is banned on the
  calendar module only, so a column read as `df.main` still passes. A banned import's repair line names the module and
  what to use instead, and the eval record counts banned imports by module. The
  log names a module only by a word of a fixed list (the standard library, the
  allowlists and a few known packages), and any other import as `?`, so no word
  the model writes as an import path reaches the log. (#12124)
- **Edits match tolerantly, never fuzzily.** After an exact match, the edit
  applier tries the same text with the blanks before line breaks ignored, then
  whole lines whose words agree once indentation and spaces outside string
  literals are ignored, with the replacement re-indented; a literal's text must
  agree exactly. The first tier with any match decides, and the
  unique-match and protected-region checks stay. A `find` that only matches the
  code before an earlier edit of the same plan gets its own repair line, and
  the eval record counts the edits each tier applied. (#12124)
- **The scope judge refuses mixed and plot-framed requests and sees the last
  turns.** A message that also asks for anything out of scope, text meant for
  use outside the plot (emails, posts, newsletters, summaries, translations)
  and plot text whose purpose is an advertisement, a call to action or a
  message to other people are out of scope, judged by intent, with twelve
  examples in the rubric; the root's prompt says the same. The judge now also
  gets the user's last three turns (1,500 characters at most), so a request
  split across turns is judged as a whole, and after a refusal the refusal
  itself as the last assistant turn. (#12126)
- **Personal data is allowed in plots and in the chat.** A user may plot
  their own tax return, contact list or customer table: names, postal and
  e-mail addresses, phone numbers, web addresses and amounts may appear in
  tick labels, titles, annotations and the conversation, and no guardrail
  refuses them for what they are. Links stay out of what the model writes, as
  link hygiene: a bare web address such as `jana-novak.de` passes, a link
  such as `https://…` or `www.…` is stripped from replies and refused in a
  change request, and a dataset cell plots whatever it holds. The root may name a
  single value of the table but never pastes rows. The guardrails stop misuse
  of the model (spam text, off-topic generation, advertisements, calls to
  action, messages to other people), and the dataset judge and its pre-filter
  look for injection only: no URL scheme refuses a dataset. The agents
  service keeps a session's data in memory for the session's lifetime;
  anyplot stores content only when the user submits quick feedback. That case
  always holds the conversation, the code, the images and the dataset profile
  with its sample rows, any of which can show personal data, and the data
  file only when its data box is ticked. (#12126)
- **Plot text that a change adds is bounded.** A change of a previous version
  may add at most 300 characters of new string literals instead of 2,000, and
  all versions together at most 2,000 against the catalogue code; dataset
  headers and cells are free. The budget bounds how much text the model
  writes, not what it says. (#12126)
- **Root replies over 1,200 characters become the fixed refusal, in every
  language.** The output guard replaces a sanitised reply longer than root.md's
  "two to five sentences, or a short list" allows with the fixed
  `out_of_scope` refusal before it is stored, so it never reaches the next
  turn's context. A turn that ran the plot pipeline is the exception: its
  reply describes a plot the user already has, so it is cut at 1,200
  characters instead of ending in a scope refusal after the plot. The guard
  counts characters, not sentences, and uses no word list, so it works the
  same in every language and script. Root replies were cut at 3,000
  characters before. (#12126)
- **The fixed refusals speak eight languages.** The out-of-scope, data,
  budget and text-only refusals are hand-written in English, German, French,
  Spanish, Italian, Portuguese, Dutch and Polish, in the informal address;
  every other language gets the English text, and no model writes or
  translates a refusal. (#12126)
- **The dataset judge sees what the root and the adapter see.** It now gets the
  same five sample rows and five top values as the profile, cells in full, in
  parts of about 4,000 characters instead of a cut-down view; a deterministic
  pre-filter refuses a header or cell addressed to an AI anywhere in the
  dataset before the judge runs. (#12126)
- **The agent pipeline bounds what the stress cases showed unbounded.** The
  adapter request carries the dataset profile trimmed to 16 KiB (47 text
  columns of long values made it 27,907 characters); the new advisory gate
  G9 reports plots that draw more than 200,000 points, which a
  1,000,000-step Lorenz request reached in 2.0 s of CPU at a 479 MiB peak, far
  under the sandbox limits (10,000,000 steps peak at 889 MiB, within a few
  MiB of the 1 GiB address space); the render probe measures at most 2,000
  texts and keeps the ones past a canvas edge first when it keeps only 400,
  so G3 sees a clipped label drawn late without the probe eating into the
  CPU limit; and a renderer limit that stopped a run is counted as
  `R1-<reason>`. (#12125)
- **The agent pipeline reviews a repaired render once more.** After a
  rejected first review, the render that the repair produced used to ship
  unreviewed (stage `not_rereviewed`, 39 of 244 runs in the rerun of spike X),
  so a repaired run could never end `ok`. The pipeline now makes up to two
  reviewer calls (`MAX_REVIEWS`), and the second verdict decides the shipped
  render; the `pipeline_result` line counts the calls as `reviews`. (#12122)
- **Output caps with ample headroom above the measured answers.** On Claude
  Haiku 5.5 the adapter's edit-only call may now write 8,192 tokens (23 of 244
  first calls were cut off at 2,048), a full-file repair 16,384, the reviewer
  and the root 4,096, and the judges 256. Gemini keeps 8,192 and 12,288 for
  the adapter, which its soft-deadline arithmetic bounds. An answer that
  finishes costs the same under any cap, and a Claude call that uses its whole
  cap still fits the time the deadline check reserves for it. (#12122)
- **The agent token budgets count cost-weighted tokens.** The request,
  user-day and global-day budgets weigh each token by its list price relative
  to an uncached input token (cache read 0.1, cache write 1.25, output 5;
  `BUDGET_WEIGHTS`), the judges included. With a warm prompt cache the median
  run books about 37,000 instead of 70,000 tokens. A cold cache weighs more
  (a reviewed run books about 78,000), so the request budget rises from
  80,000 to 160,000, about 36 % above the costliest reviewed run simulated
  cold with a second review (about 115,000, or 117,300 with three attempts),
  and the user-day and global-day budgets double to 2,000,000 and 6,000,000:
  about 54 warm runs per user, so the 40-run cap binds first, or about 26
  when every request starts cold. A review starts
  only while 35,000 are left for it and the root's closing reply, so a tight
  budget skips the review instead of answering a shipped plot with the
  usage-limit refusal, and once a plot has shipped the root's next call is
  exempt from the budget halt, once and without tools, so it can only be the
  closing reply. The `done` event keeps the plain count. (#12122)
- **The Claude eval baseline is the spike-X rerun on main.**
  `agents/evals/baselines/claude-haiku-5-5.json` now holds the 244 runs of the
  evening of 2026-10-10 (report schema 2, the drawn-text G3 probe, 90.6 %
  passed the gates, 23.4 % ended `ok`) instead of the first spike-X run. Of
  the 50 G3 lines it still reports, the 48 on heatmap-basic seaborn and
  matplotlib and scatter-basic seaborn are real clips that the catalogue
  originals already carry; the 2 on adapted renders were not examined.
  (#12122)
- **The legal page names JetBrains Mono and its own licence.** The typography
  row of the transparency section lists JetBrains Mono 2.304 under the SIL Open
  Font License 1.1, the font that draws the attribution strip under plots
  created from your own data, and the source-code paragraph now says that
  bundled third-party fonts keep their own licences beside the MIT-licensed
  code. The repository has vendored the font since the footer strip landed, so
  "the entire codebase is publicly available under the MIT License" needed that
  qualifier to stay true. (#12120)
- **The eval run record says where each run stopped.** Report schema 2 of
  `agents/evals/matrix.py` records the stage that ended each attempt and the
  run (`adapter_truncated`, `edit_apply`, `validator`, `gates`,
  `reviewer_defects` and so on) instead of the bare `failed (validation)`, the
  shipped and the reviewed attempt, an attempt log with the adapter's outcome,
  finish reason, output tokens and plan shape, every model call's finish
  reason and tokens, and the edit-failure kinds (`zero_match`, `multi_match`,
  `protected:*`, `drift:*`). All of it is content-free, read from the
  pipeline's attribution lines. A schema-1 baseline still loads and diffs.
  An unparseable file now counts as one `syntax` rejection instead of two, so
  `validator_rejections.syntax` reads lower than in older reports. (#12118)
- **More than eight groups have a palette rule.** The adapter keeps the Imprint
  palette one literal list and, past eight groups, draws all but the seven
  largest in the theme's muted ink as one "Other" group, which the reviewer
  accepts under VQ-07. The style guide's small-multiples advice contradicted
  the adapter's "keep the plot" rule. (#12118)
- **The `plot` event carries its version number.** The agents service stores
  an `ok` or `needs_attention` result as the session's next version and sends
  that number as `version`, which the BFF now passes on; a client addresses
  the artifact and theme toggle routes by it instead of counting plot events,
  which showed another version's files when an event got lost. (#12114)
- **The dataset answer lists the spec's data roles.** `POST
  /debug/agent/sessions/{sid}/dataset` now returns `roles`, each
  `{name, kinds, required, variadic, description}`, so a client can offer a
  column choice for every role, and a refused binding set (`422 invalid`)
  keeps the binding check's lines (at most 20) instead of only the code. (#12114)
- **Content-free attribution lines for every pipeline step.** The plot
  pipeline now logs the adapter's outcome, edit-apply failures, blocking
  validator rules, the gate ids that failed or reported with the render time,
  the reviewer's verdict and defect ids, and the run's result with the
  exception class of a run that ended in an error; the model line carries the
  token counts by kind, and the judges report input and output tokens
  separately. The harness prices and counts from these lines, and none of
  them carries code, data or model text. (#12116)
- **The eval harness stays out of the container images.** `.dockerignore`
  excludes `agents/evals/` (about 3 MB of fixture cases, local reports, and
  promoted cases that hold users' data) from the root build context. (#12116)
- **The probe harness reports its own start and end.** It prints a
  `HARNESS` start line before anything else and a closing line with its peak
  memory and CPU time, sets every limit soft and hard alike, takes optional
  address-space and process limits, and copies the image's baked matplotlib
  font cache into the sandbox before matplotlib loads. (#12115)
- **The caller check reads the header Cloud Run verified.** The agents
  service and the renderer read `X-Serverless-Authorization` whenever a
  request carries it, because Cloud Run then checks only that header and
  passes `Authorization` through unverified. (#12115)
- **A chat turn may wait the full queue maximum.** anyplot-api's Cloud Run
  request timeout rises from 600 to 900 seconds and the BFF's turn cap
  `AGENT_TURN_MAX_S` from 590 to 890 seconds. The old cap already ended a
  turn cleanly, but only after about 385 seconds of waiting; now a turn at
  the back of a full run queue (600 seconds of waiting plus the 180-second
  run) reaches its run instead of ending with `capacity`. The design
  document records the owner's decisions of 2026-10-10: the queue's capacity
  formula stays, and one run or theme toggle in flight per user stays. (#12113)

### Removed

- **The unused `agents-eval` extra.** It installed `google-adk[eval]`, whose
  eval stack brought litellm and nltk into `uv.lock` (29 packages in all),
  and with them two Dependabot alerts: litellm's SSRF (no fixed version
  reachable on Python 3.13, because google-cloud-aiplatform caps it below
  1.86) and nltk's path check (no fixed version at all). No workflow, image
  or script used the extra: the evals under `agents/evals/` run on the
  `agents` extra. (#12146)

### Fixed

- **A repair that only changes the protected theme statements still renders.** When an adapter
  answer fails its check only because it changed the `THEME` assignment, a theme token or the final
  savefig, and the round's check retry fails the same way, the pipeline puts the original
  statements back (`edits.restore_protected`) and checks, renders and reviews the rest of the
  repair, instead of ending the round and shipping the earlier render. A theme name bound a second
  time is never restored. `pipeline_check` logs the outcome `drift_restored`, and the
  `pipeline_run` telemetry line and the `pipeline_runs` view gain a `drift_restored` flag. (#12209)
- **A plot request made before the confirmation reaches the first plot.** A title asked for before
  `.confirm()`, or a plot wish in the pasted notes, is kept by the new `keep_plot_request` tool
  without a run, and the next `.create_plot()` draws it. The tool, and a `plot_pipeline` call that
  stopped on unconfirmed data, answer `request_kept`, so the assistant only says a request is kept
  when the server kept it. (#12207)
- **The progress grid shows the repair round.** Rounds are named `first try`, `second try`, and a
  running repair round says what it repairs in words (`repairing text size, layout`, from the
  rubric ids the round before passed on). The result card names the round that shipped when an
  earlier one won (`first try shipped of 2`). (#12207)
- **Review fixes for `.to_long()` and the readiness scan.** `.to_long()` keeps the user's bindings
  on the columns it keeps; weekday headers must all come from one language (Portuguese and Dutch
  names added, and two-letter codes such as `FR, SA, SO` need five distinct days); a line with
  several color-scale literals names all of them once; `center` counts only on seaborn's heatmap
  and clustermap and `levels` only on contours; and the dataset judge reads at most five full
  values per 40-character display copy and 8,000 characters per column. (#12207)
- **The assistant sees every category of a short column.** The dataset profile now lists every value
  of a text column with at most 12 distinct ones (else its five most frequent), so a six-source
  energy mix no longer hides its sixth source, `Übrige`, which the reply had called a row the plot
  added. The dataset judge reads the same values, and a profile over its size cap first drops the
  values past the five most frequent. (#12206)
- **Adapted heatmaps derive their color scale from the data.** The readiness scan now names literal
  color-scale limits, centers and colorbar ticks (`vmin=0, vmax=100, center=50`) and a colorbar at
  literal figure coordinates (`cbar_pos`) as hints for the adapter, so a heatmap of values from 32 to
  93 no longer keeps a 0 to 100 scale and a stray top-left colorbar. (#12206)
- **A wide heatmap matrix is offered in long form instead of plotting nonsense.** A paste such as
  `Stunde;Mo;...;So` on a heatmap or a grouped chart now gets the `.to_long()` offer (row labels
  kept, also a date or hour column; never for flows, hierarchies or color roles), and no role that
  wants labels is bound to one of the side-by-side number columns by default; bound so by hand, the
  data panel and the session block warn and point to `.to_long()`. (#12204)
- **A visible defect the review names gets the repair round.** A review that names clipped text
  (AR-09), unreadable text (VQ-01), overlap (VQ-02) or a cut or crammed layout (VQ-05) sends the
  round to the repair even when its points pass the review bar, and a render that still shows one
  is not clean for ship-best and ships with it as a note. (#12204)
- **Replies no longer claim data changes the plot never made.** A shipped plot result tells the
  assistant `data_changed: false`, and the prompts keep data-change claims to the data tools'
  change lines. (#12204)
- **Months are dates at the paste.** A column of `2025-01` is read as the first day of each month,
  with a warning that names the reading; seasons, bins, quarters and code columns stay text, and a
  label role still takes the months. (#12204)
- **The repair-exhaustion comment of `impl-review` no longer shares a fixed `/tmp` path**, which made
  its test race under parallel runs; it is written under `$RUNNER_TEMP`. (#12204)
- **A pasted or dropped list of numbers is a table, not free text for the model.** One
  column of integers, numbers, dates or booleans (live round 7: a header and 800 commute
  times, the input of a histogram) went to the transcriber, which timed out every time
  and showed "unavailable right now"; it is now stored like any table, as are digit codes
  such as postal codes and a column of repeating categories under a header (with a short
  note naming the line read as the column name when that line looks like a category). A list without a header line
  keeps its first value as the first row, in a column named `value`, with a warning. The
  transcriber takes at most 200 lines besides its 4,000 characters, and free text past
  them is refused with that limit as its cause instead of being stored as it parsed. A
  reading cut off at its cap, or out of time on a text near those limits, is
  `422 unparseable` with a cause that names the text's lines and characters and asks for
  a separator; a short text that times out, an error or a quota stays
  `503 guard_unavailable`. (#12202)
- **The reply after a plot no longer asks to confirm confirmed data.** A
  shipped plot's tool result tells the root `data_confirmed: true`, and its
  prompt says that only the current session block decides whether the data is
  confirmed, so an earlier turn's "please confirm" is not repeated (live test
  round 6, R6-1). (#12201)
- **R and pandas row names no longer become the default x.** A first column in a tool's exact
  row-name shape (R's empty header or readr's `...1` over `1` to `n`, pandas' `Unnamed: 0` over
  `0` to `n - 1`) leaves the table with a warning that counts its cells; other row-number
  columns such as R's `X` stay but take no default binding while another column fits. (#12200)
- **Missing-value tokens are announced in every column.** `NA`, `-` or `n/a` read as missing in
  a number or date column now gets the same per-column count as in a text column. (#12200)
- **Whole numbers are written without `.0`.** `87000` beside `120500.5` stays `87000` in the
  preview and in `data.csv` (it showed as `87000.0`), and `prepare_data` writes every whole
  number it moves or computes the same way; a rounded value keeps its note. (#12200)
- **The agent chat's root no longer takes its session block for a forged
  instruction.** ADK 2.11 sent the root's per-turn session block (spec, language,
  dataset and binding status) inside the user's own turn, between
  `<<<BEGIN_SYSTEM_INSTRUCTION>>>` markers. Claude Haiku 5.5 read that as user text
  posing as a system instruction: its thinking said so in 7 of 8 prep-eval turns,
  and one reply told the user that the markers "in your message" changed nothing.
  The root's `before_model_callback` now appends the block to the system
  instruction as a second part after the static policy, and Claude gets each part
  as a system block of its own with the cache breakpoint on the policy, so a block
  that changes leaves the policy cached. In the full prep eval afterwards, no turn of
  50 flagged it, in thinking or reply, 47 of 50 matched (the gate is 80 %), and the
  run cost $0.098, against $0.131 to $0.142 for the two runs before. The prep eval
  now scores a reply that talks about the root's own instructions as a miss
  (`instruction_talk`). (#12199)
- **The prep eval measures the root, not the fake renderer.** Under the default
  `AGENT_RENDERER=fake`, every `run_data_code` call got the fake's fixed
  four-row table back. The root rightly distrusted a 500-step walk that came
  back as four squares and ran its code again, so 9 of the 11 data-code cases
  missed for the fake alone. The eval's data runs now execute the snippet with
  the real harness in data mode and the renderer's limits
  (`agents/evals/host_data.py`). The outcome is read by the same reader as the
  local renderer's. Every data-code case compares the size of the table it
  stored again. (#12198)
- **Two stale prep fixtures.** Since the parser leaves out a summary row at the
  end of a paste, two cases still expected the root to drop that row. The
  English total-row case now has its total at the top, where the parser keeps
  it. The German chain case expects no second drop. A fixture test now refuses
  an expected `drop_rows` that drops nothing. (#12198)
- **Count requests and filters by place stay in step 1.** The scope judge
  refused "only the orders from Bern that were delivered" as data to fetch, and
  read pasted JavaScript data code as a request for another library. The root
  answered "count the bookings per category" as a question instead of
  aggregating. Both prompts now name these cases, and the scope eval has six
  new cases, two of them filters on an outside source that stay `needs_data`.
  (#12198)
- **Local data runs get the renderer's CPU cap.** The renderer clamps a run's
  CPU seconds to its timeout, 20 s for a data run. The local backend gave data
  runs the render's 60 s. Both now use one helper (`wire.run_cpu_seconds`). An
  oversized `out.csv` also reports its size and cap, as the renderer does.
  (#12198)
- **Measurement curves bind their time to x, never a per-curve value.** Three
  curves pasted as JSON records with list fields put `temperatur_c` (one value
  per curve) on x of a line chart. The profile now names the columns that came
  from the lists (`list_columns`); on a spec with an x axis the other number
  columns of such a table (one value per record) rank like weak measures, a
  parameter before a record number, and x prefers a list column named like an
  independent variable (`zeit_s`, `Frequency (Hz)`). A pasted table binds as
  before, and a bar chart may still show the per-curve value. (#12197)
- **One register per language in the chat.** A German summary said "Aus Ihren
  Notizen" where every other text said "du". The root now keeps the informal
  address the fixed refusals use (du, tu, tú, je), and a unit test checks the
  fixed texts for the formal words of German, French, Spanish and Dutch. (#12197)
- **The data line never nests quotes.** A converted workbook's source reads
  `Museen_2025.xlsx · sheet ‹Übersicht›`, so the data panel shows
  `from "Museen_2025.xlsx · sheet ‹Übersicht›"` instead of quotes inside quotes. (#12197)
- **Month names state their whole range.** A summary called Jan to Jun "Jan bis
  Mai" because the profile lists only five top values. The profile now carries
  the months of a text column of month names (`months`), the root names the
  range from it, and `sort` orders such a column by the calendar instead of the
  alphabet. (#12197)
- **Pasted data keeps every digit, or a warning says what changed.** Owner rule of
  2026-10-15: precision is never lost silently. The exported `plot.py` and the render
  read `data.csv` with `float_precision="round_trip"` (pandas' default reader had
  misread about one in four 17-digit numbers); a number with more digits than a float
  holds, from CSV, JSON or a Python literal, is stored rounded with a warning that
  counts the cells; whole numbers past the 64-bit range stay text; one warning counts
  the numbers whose spelling went (`1.50` as `1.5`, `1e3` as `1000.0`); a text cell
  that lost surrounding spaces or became missing (`None`, `-`), and NFC composition, are
  counted in warnings, and so are JSON's `NaN` and `Infinity`; nanosecond times beside a
  date outside 1677 to 2262 stay text with a warning instead of turning text in the
  loader; the profile's integer `min` and `max` are exact; the data panel's preview
  shows line breaks as `↵`, tabs as `→` and space runs as `·` instead of folding them
  (#12196).
- **Data operations no longer round or wrap numbers without a word.** `set_type number`
  reads whole numbers exactly; an `aggregate` sum of whole numbers no longer wraps
  around past 2^63; `cumsum`, row sums and differences stay whole; `pivot_longer`
  counts the whole numbers its shared column rounds, and no change line can lose its
  count to the length cap. Date-times keep their fraction of a second and their UTC
  offset, a year-first time such as `2024-06-01T13:00:00Z` is no longer read as
  6 January, and `set_type datetime` on different UTC offsets reads them in UTC with a
  change line naming the offsets instead of crashing the operation. Conditions on a
  column with a UTC offset compare moments instead of crashing the tool, and conditions
  on whole numbers compare exactly (#12196).
- **Default bindings skip non-measures and codes.** A number role that holds
  measures no longer takes a constant column, a year, or a month, quarter or
  week number when another column fits. An optional measure role stays empty
  instead. A series or category role prefers a name column such as `Austria`
  over a code column such as `AT` when their names are related. An `x` axis
  keeps a month, rank or year column. Compact date formats take exactly their
  digits, and years outside 1677 to 2262 no longer crash `set_type`. (#12193)
- **The assistant names only controls the chat page has.** Asked to read only
  the table of a paste, it told the user to choose "a separator that recognises
  spaces", a setting that does not exist. Its prompt now lists every control of
  the page and says to suggest re-pasting only the table when its tools cannot
  fix the data; a unit test checks each named control against the page's code.
  (#12191)
- **The dataset pre-filter reads constant columns too.** A constant text column
  moved to the notes returned to the stored table when the notes were dropped,
  without the instruction pre-filter having read it. (#12191)
- **A kept plot note keeps its requested texts.** When a first plot stops
  before the confirmation, the texts and number formats the user asked to see
  (`expected_texts`) are now kept with the note, so the next bare
  `.create_plot()` checks the render for the same title or format; a run that
  brings its own request or texts checks only its own, so a withdrawn title is
  never reported missing. The note follows one lifecycle: kept until a plot
  ships, kept through a binding change that only fills roles that were still
  open, dropped by any other change to the bindings, the data or the library.
  (#12186)
- **Empty columns leave a pasted table.** A column with a header but no value
  in any row (an ECB export carried 14) is dropped with one warning that names
  them, before the 50-column check, for JSON records and column lists too. (#12182)
- **Grouped thousands read as numbers.** `7.184.003`, `1,234,567`, `1,234.5`,
  Swiss `1'234'567` and space-grouped `1 234,5` (also with no-break and thin
  spaces) are numbers instead of text; a `1,234` or `1.234` column follows a
  grouped column of the same file, and a decimal comma keeps no needless warning
  in a file that writes `6,07`. Dotted dates, IP addresses, single space groups
  (`123 456`) and columns named as ids, codes, versions or phone numbers stay as
  they are. (#12182)
- **Default bindings take a measure as the value and a category or the year as
  the category.** A text column of numbers ranks after a year column for a
  category role, a real category of 2 to 60 values ranks first, and a value role
  ranks year columns after every measure; a time axis prefers the year. A price
  in the year range counts as a year only with a year name or a full yearly
  run. (#12182)
- **A step-2 note that drops a line keeps the confirmation and its title.**
  Bindings set by the assistant that only leave out confirmed number series
  ("only co2_per_capita") keep the user's confirmation (`AGENT_NARROWED_BINDINGS`,
  default `keep`), so the plot runs in the same turn; any other binding change
  asks for `.confirm()` again. A first plot's request that stops before the plot
  is kept until a plot ships, and dropped by any later change to the bindings or
  the data. (#12182)
- **Agent replies describe the rendered plot, not the plan.** The render probe now
  reports the drawn texts by role, and the plot result hands them to the root as
  `shows` with the review's verdict. The root names titles, labels and number
  formats only as the plot draws them. Before, its closing reply came from the
  adapter's notes, written before the render, so it claimed "6,5 Mio." on an axis
  that drew "6.0 M". (#12183)
- **Requested texts and number formats are checked in code.** The root lists the
  texts the user wrote out (`expected_texts`), and the pipeline checks the drawn
  texts for each. A miss gets a repair round (`AGENT_EXPECT_CHECK=repair`), and a
  miss that no round fixes stays as a residual line, so the reply says so. (#12183)
- **Data summaries name the real bindings.** `get_dataset_profile` returns the
  bindings in force, so the summary no longer describes the columns the profile
  suggests. (#12183)
- **Titles know where the data comes from.** The adapter and the reviewer get a
  fenced dataset context: the screened notes pasted with the data and the source
  of a computed table (formulas, or the names in the user's code, such as
  `lorenz`). A Lorenz attractor is no longer titled "Trajektorie im Raum". (#12183)
- **`ok` no longer hides a measured defect.** A shipped plot keeps every advisory gate line (clipping,
  overlapping text, annotations outside their axes) in its notes whatever its review score; until now
  only a missing glyph stayed above the ship bar. An optional review-score condition for `ok`
  (`AGENT_STATUS_SCORE`, off by default) waits for the owner's decision. (#12178)
- **Data code that reads a URL is a data request, not an attack.** The scope
  judge classed `pd.read_csv(urlopen("https://…"))` as `attack`, a strike
  toward the day's lockout; it is now `needs_data` with the hint to paste the
  table, and `attack` is kept for code that reaches the system, its
  environment or secrets, or sends data out (#12180).
- **A question about the table's own figures is no data request.** The judge
  never sees the pasted table, so "Welches Jahr hat den grössten
  Ausländeranteil?" read as a statistics lookup and was refused `needs_data`;
  a question that picks, ranks, compares or summarises entries now counts as
  being about the table, in any language and without "my data" (#12180).
- **The strike lockout says what it is.** Three `attack` verdicts in a day now
  answer with their own `locked_out` refusal ("paused until tomorrow after
  several refused requests") instead of the `budget` text "usage limit
  reached", and the paste route answers `429 locked_out` or `429 daily_limit`
  instead of a `rate_limited` whose text read "daily limit reached" (#12180).
- **The render harness refuses frames to plot code.** In plot mode the agent
  chat's audit hook (`PlotGuard`) now refuses `gi_frame`, `cr_frame`,
  `ag_frame`, `tb_frame`, `sys._getframe` and `sys._current_frames` while plot
  code is on the stack, as data mode already did, so a frame's `f_builtins`
  cannot hand out `open` and `__import__` past the validator. Import bodies, a
  short list of library readers (pandas' chained-assignment check, statsmodels'
  graphics, the `traceback` summaries pyparsing builds for mathtext) and the
  traceback the interpreter prints after a failed plot stay allowed; a worker
  thread running a callable the plot submitted gets no frame. Both guards
  refuse `gc.get_objects` and its kin, which hand out the guard, and the
  callbacks that receive real frames: `sys.settrace`, `sys.setprofile`,
  `sys.monitoring` callbacks and signal handlers. A sweep of
  the 572 eligible catalogue matplotlib and seaborn files rendered the same 565
  before and after, with no refusal. (#12181)
- **The code validator bans cache and spill directories.** The keywords
  `memory=`, `temp_folder=` and `cachedir=` and the helpers `Memory`,
  `check_memory` and `Parallel` are findings, so exported code with a
  scikit-learn `Pipeline(memory=...)` no longer writes a cache directory on the
  user's machine. (#12181)
- **A category named `NA` no longer turns into a missing value.** The exported
  loader reads missing values per column when the data has a text column (only
  the empty cell in text, the usual tokens elsewhere), so `NA` (Namibia, North
  America) from a JSON key or a JSON-stat category survives, a pasted `NA` in a
  column of letter codes stays a code, and an R export with `NA` in a number
  column still loads. (#12179)
- **A data snippet over the size cap says how much and what to do.** Cloud Run's
  sandbox launcher reports every non-zero exit as its own SIGPIPE (-13), so a
  10,000-step ODE that broke the 200 KB CSV cap came back as an unnamed error
  twice. The harness now writes its exit code and the measured size and cap to
  `status.json`, the renderer and the local backend read it, and the
  `run_data_code` refusal names the size, the cap and the row step that fits; the
  tool description and the root prompt name the cap and the rounding up front. (#12176)
- **The data summary follows a language set by a pasted CSV.** After a German
  CSV without notes the summary came in English in 3 of 4 probe runs. The
  session block and the action message now name a known session language in
  English words (11 of 11 runs in German afterwards). (#12176)
- **Default bindings never group by a single-valued column.** A categorical,
  text or boolean role such as `series` ranks a column with one distinct value
  after every column with two or more, so a constant `Kanton` no longer takes
  the series from `Staatsangehörigkeit`. (#12176)
- **A transient network glitch no longer leaves a page empty.** A short edge or
  network failure (a request blocked without CORS headers, surfacing as
  "Failed to fetch") used to leave the homepage numbers at "—" and a plot page
  at "Failed to load spec" until a full reload. `apiGet` now retries network
  errors and 408/425/429/500/502/503/504 responses twice with backoff, honouring
  `Retry-After` and the caller's abort signal, while a 404 still fails at once
  and POSTs, the authenticated debug and agent-chat requests and the chat's
  stream never retry; the API exposes `Retry-After` to the page. If a load still
  fails, the plot page and the homepage numbers offer `.retry()`, which reloads
  the data in place. (#12174)
- **No false refusal right after a refusal.** The scope judge saw the previous
  fixed refusal as the assistant's last turn, so after a German weather question
  was refused, the next message, a question about the user's own data, was
  refused as `needs_data` too. The judge now sees the last reply a model wrote,
  never a fixed refusal, and its rubric says that a question about your own
  data ("which day was the warmest?") is in scope. A withheld message's
  placeholder now names its verdict (`[message withheld by scope policy:
  needs_data]`), so "do it anyway" after a data refusal gets the data refusal
  again. Ten scope eval cases reproduce the sequences in German and English.
  (#12171)
- **The plot-code validator refuses frame and generator introspection.** A security review
  of 2026-10-14 found that a generator's frame (`gi_frame`, then `f_builtins`) reached the
  interpreter's builtins without a dunder name, which the SECURITY profile allowed. Frame,
  generator, coroutine, traceback and code-object attributes (`gi_frame`, `gi_code`,
  `cr_frame`, `f_back`, `f_builtins`, `f_globals`, `f_locals`, `tb_frame`, `co_consts` and
  their siblings) are now refused on any object. The renderer's gVisor sandbox (read-only,
  no egress, no secrets in its environment) bounded the exposure; catalogue eligibility is
  unchanged (285 matplotlib and 287 seaborn files). (#12169)
- **The plot result reports the changes the shipped code carries, not the
  proofread's notes.** `PlotResult.changes` came from the plan of the last
  adapter call, which in the live flow is the self-review; when it changed
  nothing its "already present" notes replaced the real changes, and the
  assistant told the user the change might not have run. The changes are now
  the notes of every adapter call up to the shipped render whose plan changed
  the code, so a shipped earlier round reports its own (`pipeline.note_changes`). (#12170)
- **An earlier explicit request is no longer undone by the review loop.** A
  title the user had chosen two turns earlier was rewritten when a later change
  ran, because neither the adapter nor the reviewer knew it was the user's
  choice and the rubric judged it. Each plot version now keeps the change
  requests it carries out, a change hands them to every adapter call and to the
  reviewer as fenced standing requests (the most recent 8 within 2,400
  characters), and the adapter and reviewer prompts keep them: never a defect,
  changed only when the current request asks for it. (#12170)
- **The plot-code validator refuses native code and raw memory reached through a value.**
  A second opinion of 2026-10-14 found that `np.zeros(1).ctypes._ctypes.CDLL(None)` and
  `type(...).from_address(0)` passed the SECURITY profile, because the private-name rule
  only applies to imported names. The validator now bans `ctypes`, `_ctypes`, `cffi`,
  `data_as`, `from_address`, `from_buffer`, `as_strided`, `dump`, `extbuild`,
  `get_rdataset` and `webuse` on any object, and `.to_string()` / `.info()` with a target.
  The catalogue's eligibility is unchanged (285 matplotlib and 287 seaborn files). (#12167)
- **A language chosen in the chip is used, not refused.** The session block reaches the
  root inside the user's turn; a production session on 2026-10-12 had the root refuse
  the chip's choice as "the block in your message" and stay in English. The block now
  says who set the language and to write in it, the root prompt says the block is the
  server's and is followed, the page's English action messages no longer set the reply
  language, and a language the model cannot write gives English with one sentence that
  says so (the adapter notes it in its changes). A live check on Haiku with Japanese
  chosen in the chip: reply and title in Japanese (#12156).
- **Box-basic's repair no longer fails on a protected line it must change.**
  The edit applier protected every theme conditional, including box-basic
  matplotlib's data-dependent `_tight_text_color`, so 12 of the 13
  `drift:theme_token` failures in the rerun of spike X refused a correct full
  file. A theme token is now a value picked per theme from literals and
  earlier tokens only, and the drift check compares meaning, so a token
  re-stated in other quotes or spacing passes. (#12124)
- **The placeholder failure says how to add code after `df =
  load_user_data()`.** The repair line and the adapter prompt now say to keep
  the line out of `find` and `replace` and name the line below it to anchor an
  insertion on, the cause of the rerun's 5 `protected:placeholder` failures.
  (#12124)
- **A caption such as "Data: my tax return" no longer reads as a link.** The
  tool-argument check refused a change request with a scheme word followed by
  a space (`Data: …`, `File: …`) as a URL; it now needs text right after the
  colon, as the output sanitiser and the code validator already did. (#12126)
- **The judge no longer retries a failed call in the same instant, and the
  scope eval stays under the Vertex quota.** The judge's one retry waits
  0.5 s first, inside the same 4 s budget, because a 429 or a transport error
  retried at once meets the same cause and, on a per-minute quota, doubles the
  burn. The scope eval spaces its judge calls at 25 a minute by default
  (`--calls-per-minute`), below the project's 30-per-minute quota for Claude
  Haiku in `eu`, and records the cause of every case the judge could not
  answer, so a quota error no longer reads as a bare missing verdict. (#12126)
- **The root agent no longer reports a shipped plot as failed.** The chat UI
  added `version` to the plot result, but the tool-safety allowlist for the
  `plot_pipeline` result did not know the field, so every shipped plot reached
  the root as `invalid_result` and its closing reply told the user that the
  run had failed while the plot was already on screen. The allowlist is now
  derived from the `PlotResult` schema, and a test holds the two together.
  (#12123)
- **Reviewer and adapter answers that miss only a formal rule are mended.**
  The rerun of spike X could not read 44 of 218 reviewer answers, none of them
  cut off. `schema_guard` now clips over-long texts, keeps the first five
  defects and derives `ok` from them, drops defects whose id is outside the
  checklist (a pass that names only such ids stays a pass, a rejection that
  names only such ids stays unread), and mends change notes and a blank
  `full_code` in adapter plans, then validates the result against the same
  strict schema; the edit contract is never repaired. Each failed answer writes a content-free `answer_schema` line with
  the broken rules, which the eval report counts. (#12122)
- **The agent reviewer judges sizes and colors by the style guide's own
  table.** It called the prescribed sizes (axis titles 10 pt, ticks 8 pt at
  dpi 400) too small in 50 of 56 VQ-01 lines and flagged Imprint colors by
  their look in the render, so repairs enlarged fonts against the house style.
  `reviewer.md` now quotes the table, judges colors from the code, lists what
  is never a defect, and treats a gate note as a measurement to confirm.
  (#12122)
- **The Gemini adapter's edit call has room for its thinking.** Gemini counts
  thinking tokens toward the output cap, and the 2,048-token edit cap ended
  every first adapter call of the spike-X Gemini arm with `MAX_TOKENS`, so no
  run had a repair round. The Gemini edit cap is now 8,192 tokens, which holds
  101 of the run's 112 measured plans; a first answer that still hits the cap
  leaves the repair its time, and the full-file repair runs at 12,288 tokens
  with LOW thinking. Claude stays at 2,048 tokens with thinking disabled. The
  repair also no longer reserves the whole 60 s render timeout, so the first
  attempt keeps 65 s of the 140 s soft deadline instead of 35 s. (#12118)
- **A cut-off adapter answer gets its own repair line.** The repair now hears
  that the previous answer ran out of output tokens instead of a generic
  schema miss, and a cut-off answer is never used as a plan, even when a
  truncated Claude tool input still validates. The schema-miss and
  refused-full-file lines no longer tell the repair to send edits when it may
  send a full file. (#12118)
- **The palette repair target matches the palette rule.** Every soft
  ADAPTATION finding asked the repair to "derive it from df and the Imprint
  palette", while the validator wants a literal list; that finding decided 10
  of Claude Haiku 5.5's 20 non-passes in spike X. Each rule now has its own
  target. (#12118)
- **The G3 probe gate measures only drawn text.** The render probe counted
  tick labels that matplotlib never draws (the locator's edge ticks outside
  the view, labels of hidden axes), so G3 (text beyond the canvas) fired on
  every line plot of spike X and spent the repair before the review. It now
  measures the texts its own draw renders, for G3 and the tick-overlap gate
  G7. Remote renders pick it up when the renderer image is rebuilt. (#12118)
- **The agent BFF accepts every spec role and passes on retryable codes.**
  `PUT /debug/agent/sessions/{sid}/bindings` refused roles such as
  `temperature_K` or `X1`, which 12 catalogue specs use; the BFF now applies
  the agents contract's role pattern. `guard_unavailable`, `capacity`,
  `no_dataset` and `rate_limited` reach the browser by name instead of as
  `upstream` or `invalid`. (#12111)
- **Retest workflow records the action pin it actually runs.** The Dependabot
  bump of `claude-code-action` updated the `uses:` pins of `impl-review.yml`
  and `review-retest.yml` but not the workflow-level `ACTION_SHA` that the
  retest records write into every record, so the unit test that keeps the two
  aligned failed on `main` without CI noticing (the Dependabot PR ran no
  tests). `ACTION_SHA` now matches the pinned action again. (#12099)

### Security

- **The agent chat's code validator closes exec and process routes through
  allowed modules.** It accepted `np.testing.measure("...")`, which compiles
  and runs any string. A survey of every public function and re-exported module
  of the admitted packages now bans their test, build, process and
  import-by-name submodules and helpers (`testing`, `backends`, `animation`,
  `test()`, `switch_backend`, `x13_*`, `mpl.tempfile`, ...), keeps resolved
  attribute paths inside the import surface (`scipy.datasets` after
  `import scipy.stats`), and refuses matplotlib and pandas settings that start
  LaTeX, ffmpeg or Ghostscript or import a backend by name (`rc-key`,
  `usetex=`, `backend=`). A test pins every first-level submodule of the
  packages admitted whole as reviewed or banned, so a library upgrade cannot
  add one unnoticed. (#12177)
- **The render harness arms an audit hook in plot mode too.** `PlotGuard`
  refuses every `exec` of plot code, processes, sockets, native libraries and
  any write beyond the PNG and its probe, while imports, reads and drawing go
  on; all 474 catalogue matplotlib and seaborn files that pass the validator
  render under it. Data mode's `DataGuard` now refuses `exec` and `compile`
  past the snippet's own run, and lets `namedtuple` through, so
  `DataFrame.itertuples()` works in a data snippet. (#12177)
- **The agent validator closes module re-exports and private helpers.** An
  allowed module could hand out a module the import rules keep out
  (`statistics.sys.modules`, `collections._sys`, `enum.bltns`) or a private
  helper that runs `exec` (`dataclasses._FuncBuilder`); some of these passed
  the validator before. Such names are now banned as attributes, as `from`
  imports and as components of an import path below its root, and so is any
  private name or private submodule of an imported module. A module bound by
  `import` may no longer be used as a value, so `[calendar][0]._locale` cannot
  launder it, and the dangerous private helpers a walk of the allowed modules
  found (`_locale`, `_random`, `_tzpath`, `_FuncBuilder`, numpy's `_datasource`
  and a few more) are banned by name on any object. No catalogue file changes
  eligibility. (#12124)

*Catalog: no changes since v3.4.0 — no new implementations, regenerations or spec PRs merged in
the window; 315 of 325 specs stay at full 15-library coverage.*

## [3.4.0] — 2026-10-12 — Earned, not assumed

anyplot 3.4 makes a score something a plot has to earn. A quality review runs on Opus by
default, judges the plot against its own plot type's "What a good version looks like" bullets, scores
without the approval bar or the previous score in view, and names the defect behind each
deduction. A regeneration replaces a live implementation only when it is visibly better, and
the regen gate records why. A retest harness with three hand-labeled sets checks every
rubric change before it ships, and a weekly skill reviews what `daily-regen` changed.
Behind that: a pipeline that no longer strands a PR when a review fails after scoring, MCP
tools that return what an assistant needs, and a `.env` that is read only from the checkout
root.

### Added

- **Weekly regen review skill.** The `review-regen-week` project skill turns a week of `daily-regen`
  regenerations into a dated report: a bundled `collect_week.py` gathers every regen PR's gate record,
  parsed review, write-back and pair artifact into JSON, flags what needs a look (merges without a
  carrier, silent deductions, stranded write-backs, big re-score drops, identical review vectors), and
  picks a render sample. The skill sets targets for each metric, classifies findings by where the fix
  belongs (spec, rubric, generator, gate, workflow, one-off regen), and ships a lessons file that
  distills the scoring and gate work so a reviewer can tell expected behavior from real problems (#12055).
- **Check values.** A spec's Notes may carry a `Check values:` bullet: one
  to three numbers a correct implementation reproduces from its own
  computation. The review verifies each one that applies in the render and
  in the data code, where it must fall out of the computation; a missed
  value is a DQ-03 defect with the expected value, the observed value and
  the delta. Without check values a reviewer can't tell a wrong matrix from
  a right one: a swapped diagonal in `line-tanabe-sugano` scored DQ-03 at
  4 of 4. The spec template names the bullet. (#12046)
- **Review retest set v3: the 15 first generations of
  `line-tanabe-sugano`.** `automation/retest/set-v3.yaml` freezes the first
  spec whose first generations were all reviewed on Opus (#12019 to #12038),
  pinned at `cda962dc3` with the spec text their live reviews saw
  (`ec0619261`). Their live scores sat at 85 to 91, with less spread between
  the libraries than one reviewer shows between two runs, so the set probes
  what sets v1 and v2 can't: how a first review behaves where one point
  decides the verdict. Its 30 renders are frozen under
  `gs://anyplot-images/retest/sets/v3/`, the workflow's `set` input takes
  `v3`, and its labels stay drafts until the owner confirms them. A label may
  carry `spec_source: rules_ref`, which limits it to runs whose reviewer saw
  the spec text at `rules_ref`: a defect that only a later spec clause makes
  one doesn't count against an arm on the pinned text. (#12043)
- **Silent deductions in the retest report.** A technical item (VQ, SC, DQ,
  or CQ) that a review scores below its maximum without a defect line that
  names it leaves a repair nothing to act on. The report and the pull request
  snippet now show the share of such items and the share of runs with at
  least one. It reads only the records' checklist and weaknesses, so a
  rebuilt report of an older arm shows it too: 52 of 266 and 45 of 261 on the
  two arms of the lean-code change. (#12043)
- **A live report on first reviews.** `review_retest.py first-reviews --since
  <date>` reads the review comments of every first-generation pull request
  since a date, read-only and free: the attempt-1 histogram and the share at
  90 or 91, the spread between the libraries of a spec, the criteria no
  library differs on, silent deductions, and per repair the gain on technical
  against judgment items and whether the repair committed anything. The
  retest measures the reviewer on a frozen set; this shows what it did in
  production, batch after batch. (#12043)
- **Review retest set v2: the regen pairs of verification round 1.**
  `automation/retest/set-v2.yaml` freezes the 12 regenerations the gate
  merged on 2026-09-27 (#11951 to #11963 without #11955), each predecessor at
  `0ccb3fec1` and each new version at `28df16aed`, with the spec pinned at
  `0ccb3fec1`. Set v1 has no pair that a suggestion alone could carry, so it
  can't show whether a gate change stops such merges; set v2 can. The
  workflow's new `set` input (`v1` by default, or `v2`) hands the chosen
  manifest and lock to `plan`, `bundle` and `report`. Its 48 renders are
  frozen under `gs://anyplot-images/retest/sets/v2/`, and its labels stay
  drafts until the owner confirms them. (#11966)
- **Forward merges without a labeled carrier.** Regen items can carry a
  `fixes` label: the predecessor defects the forward new version fixes, on
  carrier criteria only (VQ, SC, DQ, CQ), each with a pattern for the
  improvement's `what` text. The report and the PR snippet show the share of
  forward merges in which no counted visible improvement matches such a
  label or cites an affirmative characteristic of the spec
  (`merges_without_carrier`). It reads only fields every rules version
  writes, so a baseline and a candidate arm mean the same by it. Round 1
  replayed through it gives 6 of 12, the number the P3 gate change is
  measured against. (#11966)
- **Review retest harness.** A new dispatch-only workflow,
  `.github/workflows/review-retest.yml`, re-runs the AI quality review on a
  frozen set of implementations and regeneration pairs, several fresh sessions
  per item, for one rules version (`rules_ref`), and reports the pooled score
  spread, verdict flips at 90, weakness-topic agreement, the gate's verdict
  stability and order bias (regen pairs run in both orders), and — once the
  labels are confirmed — named-defect misses and false alarms, with a
  bootstrap comparison against a baseline arm and a snippet for the PR body.
  A review-rubric change used to be observable only on real pipeline runs;
  now it can be measured before it merges. The workflow is measurement-only:
  read-only job tokens without `id-token`, sessions that may not run `gh`,
  `git push` or `git commit`, and nothing written to a PR, an issue, a label,
  `plots/` or GCS; it has no effect until someone dispatches it. It refuses
  while the production pipeline is busy and caps a run at 240 sessions. The
  harness is `automation/scripts/review_retest.py` (with the pure metrics in
  `review_retest_metrics.py`). Set v1 is `automation/retest/set-v1.yaml`
  (15 fresh core items, one per library, and 7 core regen pairs including
  three identity controls, plus a full tier) and is frozen:
  `set-v1.lock.json` pins the sha256 of 94 public renders under
  `gs://anyplot-images/retest/sets/v1/`. The ground-truth labels ship as
  proposals and count only once the owner sets `labels: confirmed`. Every cell
  records the resolved model id, or none, and keeps the alias apart as
  `model_alias`, never in its place. The baseline arm (`rules_ref=0674ab6b5`)
  runs on today's harness: an overlaid `regen_gate.py` only receives the flags
  it already had. How to run and read it: `docs/workflows/review-retest.md`.
  (#11964)
- **Regen gate report.** `review_retest.py gate-report` aggregates the
  production regen gate records from the PR-comment markers: merge rate,
  reason codes, how far re-scored predecessors land from their stored scores
  (comparable decisions apart), the counted visible improvements, how often a
  review cites an "Expected, not a defect" bullet as an improvement, and soft
  alarms. (#11964)
- **A verification loop for review-rubric changes.** `CLAUDE.md` and the
  `open-pr` skill send pull requests that change the review rubric
  (`quality-criteria.md`, `ai-quality-review.md`, `default-style-guide.md`,
  the review rules in `prompts/library/*.md`, the review model routing) to a
  candidate arm of the retest, whose snippet goes into the PR body. (#11964)
- **Review provenance in the metadata.** `impl-review.yml` now stores which
  model and which rules produced a review: `review.model` (the resolved model
  ID from the session's execution file, for example `claude-sonnet-5`, not the
  alias that moves between releases), `review.criteria_version` (the git blob
  IDs of `prompts/quality-criteria.md`, `ai-quality-review.md`,
  `default-style-guide.md` and the library prompt, hashed after the prompt
  overlay, so exactly what the reviewer read), and `review.rendered_at` (the
  staging render's creation time). A new standard-library helper,
  `automation/scripts/review_provenance.py`, computes both. A value the run
  can't determine is left out, never filled with the alias, and a repair
  review drops what the previous review wrote for it. The keys aren't synced
  to the database, and every new step is non-gating. (#11950)
- **Regen gate records.** Every regen gate decision now carries a reason code
  (`merge`, `below_tolerance`, `no_visible_improvement`, `regression`,
  `regen_json_invalid`, …) and leaves a one-line JSON record in the PR comment
  as an invisible `<!-- regen-gate-record:v1 {...} -->` marker: scores,
  improvement and regression counts, the code, and the model and rules version
  of both the new review and the stored one. It holds no model-written text.
  The `::notice::regen_gate` line gains `code=`, `model=` and `criteria=`, and
  each regeneration's before/after pair (both renders, both sources, the
  previous review, the review files, the record) is kept as a 60-day
  `regen-pair-<pr>-<attempt>` artifact — the predecessor's production renders
  are overwritten on the next merge, so it is the only copy. Run logs expire;
  PR comments don't, so the gate can now be monitored after the fact. (#11950)
- **CI checks every spec's "What a good version looks like" section.** The
  required "Run Tests" job now runs `automation/scripts/spec_characteristics_lint.py`
  on every PR and push, even when no Python changed: `contract` checks every
  spec against the shape the regen gate parses (exact heading, last section,
  column-0 `- ` bullets with a kind prefix, 2-8 of them, no duplicates) and
  blocks the merge; `style` warns about house style in the changed specs
  (3-6 one-line bullets, no thresholds, generic ideals or library names, the
  `-basic` variant bullet, possible contradictions with Notes). Before, a
  spec-only PR skipped pytest, so a section the gate would misread could merge
  unchecked. spec-create runs both checks before it commits, and `--strict`
  makes the style rules blocking for the planned backfill. (#11948)

### Changed

- **The frontend toolchain names Node 24.** `app/.nvmrc` moves from 22 to 24,
  the version CI has run since the test workflow pinned it, so `nvm use` in
  `app/` gives the same Node as the pipeline. `engines.node` keeps the build
  path's floor (22.12); the dev-only test stack reaches higher (jsdom 30.1
  installs on `^22.22.2 || ^24.15.0 || >=26.0.0`), which the version `.nvmrc`
  names satisfies. The app image keeps its `node:22-alpine` builder, which
  tracks the 22 line inside that range. (#12141)
- **The backend test job runs on four workers.** "Tests / Run Tests" spent a
  median of 675 s on a PR, 94 % of it in one serial pytest process over 9,183
  tests. It now runs pytest-xdist with `-n 4 --dist worksteal`, one worker per
  CPU of the hosted runner, and coverage measures through `sys.monitoring`
  (`core = "sysmon"`) instead of the C tracer, which cost about 45 % on Python
  3.13. Pinned to four CPUs, the CI-equivalent run took 68.9 s instead of
  300.8 s, with the same 9,162 passed and 21 skipped tests and the same
  coverage total (10,723 statements, 92 %); the PR's first CI run took 245 s
  for the job and 212 s for the pytest step (the medians before: 675 s and
  635 s), with the 62-s picker test as the tail that #12135 removes. The coverage now includes `agents/`, which half of the tests target
  and which was never measured (23,433 statements at 93 % in the pinned run,
  81 s), and the job also runs when `uv.lock`, a workflow or action under
  `.github/`, or a file under `prompts/` changes, because the workflow and
  prompt tests read exactly those files. (#12136) `--durations=25` lists the slowest tests, which the interleaved
  output of four workers no longer shows by timestamp, and the Cloud SQL proxy
  step polls its port every 0.2 s instead of sleeping 5 s. The turn-cap test
  of the agent stream tolerates about 0.5 s of slow start on a busy runner
  instead of 0.2 s, and the MonoLisa font download writes one `.part` file per
  process, so two workers that miss the cache at once no longer truncate each
  other's file.
- **A bare `/regen` picks its spec in about 2.5 s instead of 30 s.** The picker
  (`agentic/workflows/modules/regen/picker.py`) now reads the catalogue on
  `origin/main` with one `git ls-tree` and one `git cat-file --batch`, instead of
  one `git ls-tree` per spec and one `git show` per metadata file — about 2,900
  processes per call — and parses the YAML with libyaml's `CSafeLoader` where
  PyYAML has it (2.0 s instead of 19.8 s for the 2,596 files). The pick is
  unchanged: on the live tree, all 325 specs and every metadata file gave the
  same timestamps as before, and `validate-spec` the same answers. The live test
  `test_pick_oldest_returns_real_spec` drops from 30.3 s to 2.9 s locally (mean
  of three runs) and from 63.7 s to 5.2 s under coverage, as CI runs it; new
  fake-git tests pin the listing, batch-parsing and picking rules in
  milliseconds. (#12135)
- **MCP tools return what an assistant needs and nothing it does not.**
  `get_spec_detail` and `get_implementation` entries now carry `spec_id`,
  strip `# noqa` comments like the REST code endpoint, and leave out the
  review checklist, the review image description and the legacy single-theme
  preview fields: pipeline internals of about 10 KB per implementation that
  made an unfiltered `get_spec_detail` about 0.5 MB. `list_libraries` returns
  the REST `/libraries` fields (language, framework, version, documentation
  URL), so an assistant can pick a library by language without a second call.
  `get_tag_values` returns `{value, count}` pairs, most frequent first, counting
  specs for spec-level and implementations with code for impl-level
  categories. Breaking for clients that read the old shapes; the MCP server is
  not versioned and the old shapes were never what the reference described.
  (#12100)
- **Agent network design records the licensing decision.** The open question
  of where the agent code lives is settled in the decisions table: everything
  stays MIT in this repository, paid AI credits remain a later option, and the
  Highcharts license must be settled before the first paid credit. (#12100)
- **Weekly regen review opens at most 15 renders.** `collect_week.py` now ranks suspicious regenerations
  (merges carried only by `P` or `new` defects, then big re-score drops on keeps, then gate oddities,
  then scores of 90 or more), fills the sample at random up to 15, and lists the suspicious PRs over the
  cap as "not opened". Rows without a pair artifact are never sampled. The skill runs only when the owner asks; there is no schedule (#12056).
- **Review retest labels confirmed for set v3.** The owner confirmed the
  ground-truth labels of the 15 `line-tanabe-sugano` first generations on
  2026-10-07, so `automation/retest/set-v3.yaml` switches to
  `labels: confirmed` and set v3 reports now fill the named-defect and
  false-alarm rates. (#12054)
- **A deduction names its defect.** The 15 first reviews of
  `line-tanabe-sugano` deducted 27 technical items and wrote a defect line for
  20 of them; the same gap was a lost point on one library and a
  `Suggestion:` on another. The 19 technical criteria (VQ, SC, DQ, CQ) now
  start at their maximum, and every point below it is carried by a defect
  line; the five judgment criteria (DE, LM) start at their default and rise
  on named evidence. The review lists defects first, then scores, then adds
  up: it never picks a total, and the "median 72-78" anchor describes where
  written-down defects land a typical plot instead of naming a target.
  `regen_gate.py check-feedback` reports a technical item below its maximum
  that no defect line names, and the workflow's format notice counts them
  (`silent=N`). (#12046)
- **The same gap costs the same criterion on every library.** Each library
  of a spec is reviewed without seeing the others, so `quality-criteria.md`
  gains a routing table ("Which criterion a gap belongs to"): a missed Notes
  bullet is SC-02 when the fix is in the plotting code and DQ-01 when it is
  in the data, a departure from a Data range, an example or a stated
  preference costs nothing unless the Notes require it, a conditional
  requirement whose condition the data doesn't meet costs nothing, and a
  wrong domain value is DQ-03. It routes; it sets no threshold. (#12046)
- **The reviewer scores without the approval bar in view.** The cascade
  (90, 80, 70, 60, 50), what follows from a score, and the expected score
  distribution left `quality-criteria.md`, `ai-quality-review.md`, and
  `quality-evaluator.md`; they stay documented for people in
  `docs/workflows/overview.md`. The reviewer writes no verdict any more (the
  `### Verdict` line, `review_verdict.txt`, and `review_prev.json`'s
  `verdict` are gone; the workflow sets it), and is told not to open earlier
  reviews of the pull request. (#12046)
- **Compliance is not excellence.** A first review used to credit what the
  spec or the style guide already requires as design excellence: "spines
  removed, grid at 15%" raised DE-02 on 15 of 15 reviews. Evidence that
  raises a DE or LM item is now something beyond what the spec's Notes and
  the style guide require. In the DE-01 and DE-02 ladders the style-guide
  baseline no longer earns more than the default, and a forbidden custom
  palette earns nothing. The complete baseline
  earns exactly the defaults (DE-01 = 4, DE-02 = 2), so the 75 cap can't fire
  on a compliant implementation. Scores move down by this change; a score
  under these rules isn't comparable with one stored before them. (#12046)
- **CQ-04's hand-roll list is marked as examples.** The score row read as a
  whitelist ("a KDE, binning, quantiles, ACF/PACF, a fit, a linkage"), and
  "a fit" still named the closed-form slope and intercept the scoring notes
  exempt. The row now says the examples aren't a list to match against and
  narrows the fit to one that takes an iteration or a matrix solve. (#12046)
- **DQ-02's content policy targets real politics, not every parliament.** The
  forbidden-topic line in `prompts/quality-criteria.md`, `prompts/quality-evaluator.md`
  and the workflow reviewer now names real parties, politicians, elections, real
  legislatures and partisan messaging, and states that a clearly fictional
  parliament (invented names carrying no real-world ideology) is not political
  content: it never scores 0 or triggers the cap, invented data the spec asks
  for is not a deduction, and the fix for flat invented names is better
  invented names, never real ones. The old
  blanket "Politics (elections, parties, voting)" read as zeroing
  `parliament-basic` itself, whose spec now requires invented parties. (#12050)
- **A review no longer finds the previous one in its working tree.** After a review, the pull request branch
  carries it in two places: the `Quality: N/100` header and the metadata file
  with the score and the whole review. The second review of an unchanged file
  scored four points higher than the first (#12028), all of them on design
  and library items. `impl-review.yml` now resets the header to
  `Quality: pending` and moves the metadata file out of the workspace while a
  reviewer runs, on every review, and puts both back before it stores the new
  one; the commit that stores a review no longer names the score. A
  regeneration's re-score already hid its predecessor's review this way. The
  branch history and the pull request's comments stay reachable. (#12045)
- **The workflow owns the stored verdict.** `review.verdict` used to be what
  the reviewer wrote in `review_verdict.txt`, which needed the approval bar in
  the reviewer's prompt and was wrong at times (`APPROVED` on a review the
  workflow sent to repair). The metadata step now stores what the workflow
  decided, and a kept regeneration's write-back stores `APPROVED`, because
  the kept implementation stays live; `review_prev.json` no longer needs a
  `verdict`. (#12045)
- **A review with nothing to repair is approved as it stands.** A first
  review below 90 used to go to repair even when it named no defect. A
  repair fixes defect lines, so that cycle bought only a second, noisier
  score. A review at 80 or more with no defect line, every technical
  criterion (VQ, SC, DQ, CQ) at its maximum, and a checklist that adds up to
  its score is now approved, with a comment that says why. Both conditions
  count: a defect line on a design or library criterion is repairable, and a
  technical deduction without a defect line still gets its repair. (#12045)
- **Implementations compute with the runtime's libraries, not by hand.** The
  generator prompt and the review criteria list what each runtime installs —
  numpy, pandas, SciPy, scikit-learn and statsmodels for Python, base `stats`
  and the ggplot2 stat layers for R, Statistics and the Makie recipes for
  Julia, each JavaScript library's own API — and ask for the shortest version
  that reads as well. The review deducts one CQ-04 point, never more, for a
  written-out algorithm an available call provides, or a block a named shorter
  form replaces, and names the call and the line range. A test keeps the two
  copies of the list identical and in step with `pyproject.toml`, the R setup,
  `Project.toml` and the JavaScript render harness. (#12005)
- **The regen gate has a code-only path.** When no improvement fixes a visible
  defect, a regeneration still replaces the live implementation if it fixes a
  `CQ-04 (code)` defect the previous review named, calls the named replacement
  or removes the named code, is shorter, scores CQ-04 higher, and regresses
  nothing. The gate reads both sources for it, counts a call only in executable
  text (a comment, a string literal or a definition of the same name is none),
  and the record counts it as `improvements.code`. (#12005)
- **Polish and optional additions no longer carry a regeneration.** Every
  improvement in a regeneration review now names its kind: a fix, a removal,
  an addition, or polish. Only a fix or a removal can replace the live
  implementation; adding an optional feature the spec only allows, or
  restyling an element the spec's scope excludes, rides along, and an
  improvement without a kind never carries. Feature coverage (DQ-01) no
  longer carries a replacement on its own, like the design and
  library-mastery criteria, and a missing optional feature no longer costs
  DQ-01 points. A kept regeneration stores a predecessor finding of kind
  addition or polish as a suggestion, not a defect, and the gate record and
  `gate-report` count the kinds. (#11977)
- **A kept regeneration stores its re-score.** When the regen gate keeps the
  live implementation, the review's re-score of it (score, weaknesses,
  strengths, image description, checklist and review model) replaces the
  stored review through a metadata pull request that `impl-merge.yml` merges,
  so the next regeneration starts from current problems under the current
  model and rules. The review writes the re-score as `review_prev.json`, its
  checklist equal to the gate's `prev_checklist`; the new
  `automation/scripts/regen_writeback.py` checks it, writes the metadata and
  the `Quality: N/100` header number, and guards the merge (the score, review
  model and rules version must be the kept PR's gate record's, only the review
  keys may change, and `main` must still hold the files the re-score judged). The code and the production
  images stay as they are; the gate record's new `writeback` key and
  `gate-report` count what happened on every keep. (#11972)
- **Review retest labels confirmed for sets v1 and v2.** Both manifests switch
  to `labels: confirmed`, so retest reports now fill the label metrics each
  set supports: named-defect and false-alarm rates, gate accuracy, and (set v2
  only) the carrier metric. The owner's corrections:
  the d3 force-collision pair of set v1 keeps in both orders; in set v2,
  #11960 merges forward on a fixed VQ-02 defect (the gridline through the
  value label), #11963 keeps, and #11953's label-clearance fix is dropped as a
  suggestion. (#11976)
- **Review weaknesses are defects or suggestions, and only a defect carries a
  regeneration.** Each weakness either names the criterion it violates, the
  render and the observed value, or starts with `Suggestion:`; both are stored,
  so the website and the next regeneration see the class. The regen gate
  replaces a live implementation only when a visible improvement fixes a
  visual, spec, data or code defect that scores higher than in the
  predecessor's re-score, or an `A good version shows:` property; design and
  library-mastery points, storytelling layers and taste changes ride along but
  never carry a merge alone. Generation and repair act on defects and decline
  suggestions. (#11967)
- **One unasked layer on a `-basic` spec is already variant creep.** The SC-01
  rule and its mirrors in the review, generation and repair prompts name
  reference lines, highlights and callouts, and one such addition is enough;
  the review no longer suggests adding one. (#11967)
- **Every quality review runs on Opus.** `impl-review.yml` now reviews on Opus
  whatever model generated the implementation, so a regeneration (generated on
  Sonnet) is judged, and its predecessor re-scored, on Opus. The `model` input
  still chooses the generation and repair model; a manual review can pin
  another model with the new `review_model` input. The retest harness's
  `models=production` now runs every cell on Opus. (#11968)
- **An off-canvas predecessor may be frozen for a forward-only pair.**
  `impl-review.yml` shows the reviewer the predecessor's render as
  production stores it, and round 1 had two off-canvas ones (4766 × 2670 and
  4800 × 2700). A regen pair marked `orders: forward` now runs in the forward
  order only, and its `prev` render may keep its production size; the render
  under review (`new`) still has to be on a canonical canvas, as the
  production canvas gate requires. Regen cells also record the spec's characteristic
  count and permissions (`spec_characteristics`), which the carrier metric
  reads. (#11966)
- **`-basic` specs name reference lines, highlights and callouts in their variant bullet.** The 6 seeded
  and 7 bar-family `-basic` specs now list them, because the review and the regeneration read that list as
  complete: an unnamed mean line and callout survived a count-basic regeneration while a named cumulative
  line was removed. Each bullet is edited in place, keeps its `C` id and still names every exclusion it
  named before. A new style-lint warning (W7) flags a `-basic` variant bullet that leaves one out, and the
  spec template asks spec-create to name all three. (#11965)
- **A replaced implementation now gets a PR comment too.** Until now only a
  kept regeneration explained itself; the merge path posted nothing. The
  replace path now posts the same summary (stored, re-scored and new score,
  improvements, regressions, reason) and the gate record before it dispatches
  the merge. A failed comment only logs a warning and never holds up the merge.
  (#11950)
- **Each characteristic bullet states its kind.** Every bullet now opens with
  `A good version shows:` (an affirmative property; missing it deducts, and
  only these can be cited as an improvement) or `Expected, not a defect:`
  (a permission; never penalized, never a target), one kind per bullet. The
  template and both spec-create prompts ask for 3-6 bullets with at least one
  of each, and the eight hand-seeded specs are split accordingly
  (heatmap-basic gains its missing basic-variant bullet). The regen gate no
  longer counts an improvement that cites a permission, and the review and
  generation prompts follow suit: a permission is never a weakness, never a
  DQ-01 aspect and never shaped into the data. The review also scores a
  related but different form (a donut for a pie) as a partial SC-01 on any
  spec, deducts spline overshoot under SC-03, and names missed Notes or
  `A good version shows:` bullets under SC-02. (#11948)
- **A pair's first implementation now runs on Opus, regenerations stay on
  Sonnet.** `impl-generate.yml` resolves the model per (spec, library) pair:
  Opus when the pair has no implementation file on `origin/main` yet, Sonnet
  when it already has one (Opus again for a forced regeneration with
  `regen_gate=false`, which takes the fresh-generation path), and threads the
  result into that PR's review and repairs as before. The `model` input on `impl-generate.yml`,
  `bulk-generate.yml` and `daily-regen.yml` now defaults to `auto` (the
  routing); `haiku`, `sonnet` or `opus` still pins one model for every pair.
  Label-triggered runs, the watchdog's generation retries and the babysit
  backfill scripts (`MODEL` now defaults to `auto`) follow the same routing,
  so a full-catalogue backfill now runs on Opus. The resolved model and its
  reason appear in the run summary and the issue preview comment, and the PR
  body records it (`**Model:** opus`). Review and repair rescues that arrive
  without a model (`impl-review-retry.yml`, the watchdog, a manual rerun)
  read that line back instead of falling back to Sonnet, so an explicit pin
  survives them. Without a readable `origin/main`, generation fails rather
  than guessing a first run. (#11947)
- **`bulk-generate.yml` paces dispatches 180 s apart for Opus runs.** The
  default pause is 180 s for model `auto` or `opus` and stays 120 s for a
  pinned `sonnet` or `haiku`; `pace_seconds` still overrides it. (#11947)
- **The daily-regen spec polish and similarity audit run on Sonnet instead of
  Haiku.** Both pre-flight steps in `daily-regen.yml` stay pinned regardless of
  the run's `model` input. (#11947)
- **The AI review judges each plot against its own plot type.** Specs gain a
  closing `## What a good version looks like` section with 3-6 observable
  properties of a good render, including "expected, not a defect" items;
  spec-create writes it for new specs, spec polish never touches it, and eight
  central specs (bubble, scatter, line, bar, violin, two heatmaps, force-directed
  network) are seeded by hand. The quality criteria and the review prompt score
  against it and add three soft rules from the bubble-basic regen experiment:
  marks sit at their data values (post-hoc displacement deducts SC-03), legend
  glyphs must be visible in both themes (VQ-03), and extra encodings on a
  `-basic` spec count as the wrong variant (SC-01). Regenerations now address
  only the weaknesses that are real per that section, answer overlap with data,
  marker size or alpha instead of moving marks, and keep their data scenario.
  (#11946)
- **Regenerations only replace a live implementation when they are visibly
  better.** A regeneration (an implementation PR for a pair that already has an
  implementation on main, such as every `daily-regen` pick) now gets one review
  and no repair loop. The review scores the new render blind, re-scores the
  predecessor's production renders against the same criteria, and writes a
  before/after judgment to `review_regen.json`; `automation/scripts/regen_gate.py`
  merges only when the new score is at least the re-scored predecessor minus one,
  at least one improvement is visible, and nothing regressed (a replaced data
  scenario or added encodings on a `*-basic` spec count as regressions).
  Otherwise the PR is closed as `regen:kept` and main, GCS production and the
  database stay untouched. Anything missing fails closed to keep. The
  bubble-basic regen experiment showed why: five rounds kept scores flat at
  89–92 while code grew 35 %, three libraries swapped their data scenario, and
  two moved data marks off their values. `regen_gate=false` on `impl-generate.yml`
  and `bulk-generate.yml` forces the old path (`regen:forced`); `daily-regen`
  now counts kept attempts when picking the oldest spec; the watchdog re-closes
  open `regen:kept` PRs and never rescues a regeneration into repair; a failed
  regeneration no longer marks the pair `impl:<lib>:failed`; and the local
  `/regen` withholds `ai-approved` when the new score falls more than one point
  below the stored one. (#11945)
- **Dependencies:** 15 Dependabot PRs. Security updates close 30 advisories, one rated
  critical and 15 high: `pyjwt` 2.13.0 → 2.15.0 (#12007), `virtualenv` 20.36.1 → 21.7.13, a
  major version (#12036), `tornado` 6.5.8 → 6.5.9 (#12006), `urllib3` 2.7.0 → 2.8.0
  (#12009), `multidict` 6.7.0 → 6.9.1 (#12059), `mako` 1.3.12 → 1.4.2 (#12058), and in
  `app/` `brace-expansion` 5.0.9 → 5.0.12 (#12060) and `source-map-js` 1.2.1 → 1.2.2
  (#12057). The grouped python-minor bumps (#11842, #11973) carry `anthropic` 1.3.0 → 1.8.0,
  `mcp` 2.1.1 → 2.2.0, `fastmcp` 4.0.2 → 4.0.7, `alembic` 1.19.2 → 1.20.0 and
  `matplotlib` 3.11.1 → 3.11.2; `pandas-stubs` follows (#11974). npm in `app/`: React 19.3.0
  (#11839) and the npm-minor group (#11840). GitHub Actions: `claude-code-action` 1.0.216 →
  1.0.230 and the Docker, CodeQL and Codecov actions (#11841, #11975).

### Removed

- **`SpecRepository.search_by_tags` and its any-category filter builder.**
  Nothing outside the MCP search used them, and matching a value in any
  category is exactly the bug the new filter fixes. (#12100)

### Fixed

- **`.env` is read only from the checkout root.** The API, the Alembic
  environment, the Postgres sync script, the workflow agent module and the e2e
  test fixtures called `load_dotenv()` without a path, which walks up the
  directory tree from the calling file. In a git worktree under
  `.claude/worktrees/` that walk reaches the main checkout's `.env` and loads the
  production database credentials into a test run, a local server or a
  migration that never asked for them. Each call now names its own checkout's
  `.env`; a missing file is still silently skipped, so Cloud Run and GitHub
  Actions, which set their variables directly, are unchanged. (#12105)
- **A lone surrogate in a JSON body no longer turns a 422 into a 500.** FastAPI's
  default validation handler echoes the offending `input` into the 422 body, and
  Starlette's `JSONResponse` cannot UTF-8-encode a lone surrogate such as the JSON
  string `"\ud800"`, so any schema-violating body holding one answered 500. A
  `RequestValidationError` handler in `api/exceptions.py` now renders the same
  `{"detail": [...]}` body ASCII-escaped, which can always be encoded. The
  "Standard error format" section of `docs/reference/api.md` now matches what the
  API returns, including the 422 shape. (#12104)
- **`POST /feedback` answers 422 for text that is not valid UTF-8.** A lone
  surrogate in any field passed the schema, then made the database driver raise on
  encoding, so the request ended as a 500. `FeedbackRequest` now refuses such
  text up front, before the router or the database sees it. (#12104)
- **MCP tag search scopes values to their category and ANDs the categories.**
  `search_specs_by_tags` flattened every spec-level value into one list and
  matched it in any category, so `plot_type=["scatter"]` with
  `domain=["finance"]` returned the union of both and `plot_type=["finance"]`
  matched finance domains. The new `SpecRepository.search_by_tag_filters`
  keeps each value in the category it was passed in (JSONB containment on
  PostgreSQL, `json_extract` on SQLite), ORs the values within a category and
  ANDs the categories, which is what the MCP reference promised all along.
  (#12100)
- **MCP reference and page describe what the tools return.**
  `docs/reference/mcp.md` and the MCP page carried wrapper objects, limits and
  library lists the server never produced: `list_specs` defaults to 100 and
  returns a bare array with `website_url`, `search_specs_by_tags` also takes
  `patterns`, `dataprep` and `styling`, `get_spec_detail` takes a `libraries`
  filter, and `get_implementation` covers all 15 libraries. (#12100)
- **A stale `ai-review-failed` no longer buys a second review.** When GitHub
  accepted a re-review dispatch but `gh` reported an error, `impl-review.yml`
  labeled the PR `ai-review-failed` beside the re-review that was already
  queued, and the watchdog's next scan dispatched another one. Every review
  run now removes the label when it starts, and the watchdog leaves such a PR
  alone while a review of it is queued or running, or drops the label when
  the PR already has a verdict. (#12041)
- **A verdict label that cannot be added fails the review run.** The early
  verdict step downgraded a failed `regen:kept` add to a warning, so the step
  succeeded without a verdict label and switched off the post-score rescue
  that keys on it. All four verdict labels are now added with three tries and
  fail the step when they do not land. (#12041)
- **The no-score review retry hands over to the watchdog when it cannot start.**
  "Validate review output" posted its retry marker and its dispatch without
  retries, and a failure there left the PR with no label at all. Both are now
  retried three times, the dispatch waits for the marker, and a failure ends
  in `ai-review-failed`. (#12041)
- **impl-repair's crash retry counts its marker across comment pages.** The
  budget read took the per-page counts of `gh api --paginate` as one number,
  so on a PR with more than 100 comments the one-retry cap never held. The
  pages are now summed, and a count that cannot be read counts as spent.
  (#12041)
- **A review that fails after scoring is re-run instead of stranding the PR.**
  `impl-review.yml` retries every call of "Add quality score label" four times
  with backoff, and a run that dies after the score but before any verdict
  label now dispatches one fresh review on its own ref (sharing the existing
  `review-retry` budget), or labels the PR `ai-review-failed` for the watchdog.
  The budget marker is written before the dispatch and an unreadable budget
  counts as spent, so an outage cannot buy a second re-review. The watchdog's
  never-reviewed case also counts a lone `quality:N` as a marker. Before, an
  HTTP 502 on the label left PR #11984 without a verdict for about seven
  hours. (#12004)
- **impl-generate's auto-retry runs on the ref that dispatched it.** A branch
  smoke's failed generation used to retry on main (#11969–#11971); the retry
  now passes `--ref` with the run's own ref, which is `main` for every
  label-triggered run. (#12004)
- **Repair exhaustion no longer pushes to main.** After four failed repairs,
  `impl-review.yml` ran `git push origin main` to delete the pair's
  implementation, which the main ruleset refuses, so the step died after
  closing the PR and before labeling the issue. Only a forced regeneration
  reaches that point with an implementation on main, and that live
  implementation now stays: the issue gets `impl:{library}:done` back. A
  fresh pair is marked `impl:{library}:failed` as before. A stale
  `generate:`/`pending` label that cannot be removed now fails the run
  instead of passing silently. (#12004)
- **Ruff lints `automation/scripts/` and its tests again.** The Ruff
  `exclude` entry `"scripts"` matched every directory of that name, so CI's
  `ruff check .` and `ruff format --check .` skipped `automation/scripts/` and
  `tests/unit/automation/scripts/` along with the top-level one-off scripts it
  was meant for. The entry is now `"./scripts"`, anchored to the project root,
  and the one import-order and three format errors it had hidden are fixed (#12003).
- **Two set v2 fix patterns recognize the P3.1 arm's wording.** The #11960
  gridline fix now also matches "value labels are clear of the grid", and the
  #11954 axis-title fix matches "the count axis now carries an explicit title".
  Both are genuine fixes that the P3.1 arm cited in words the patterns did not
  know, so its forward merges without a labeled carrier drop from 2/18 to 0/18.
  The v2-baseline and p3-v2 reports don't change. (#11979)
- **Weaknesses the spec now permits no longer count as regen improvements.**
  When the review re-scores the predecessor, it marks an older weakness that an
  `Expected, not a defect:` bullet covers as obsolete, with that bullet's id;
  the gate never counts it and the generator declines it. (#11967)
- **Regenerations of 16 implementations with an older review no longer keep
  on a context error.** Their stored checklists carry scalar keys such as
  `total_score` next to the six categories, which made the previous-review
  extraction raise; it now skips them. (#11967)
- **A regeneration no longer shows the review its predecessor's score.** A
  regeneration edits the live file, so its header still read
  `Quality: 92/100` — the stored score, in plain sight of the review that is
  meant to score the new version blind (seen on #11926). `impl-generate.yml`
  now resets it to `Quality: pending` before the PR opens, the state a fresh
  file starts in (`regen_gate.py sanitize-source --pending`); impl-review
  writes the new score afterwards. (#11950)
- **The regen gate reads wrapped characteristic bullets whole.** An indented
  continuation line was dropped, so the gate cited a truncated bullet; it is
  now joined to the bullet above it. The regeneration comparison in the review
  prompt also exempts what SC-03 exempts (categorical jitter, layout-positioned
  types, offsets the spec asks for) from its "marks moved" regression, and no
  longer counts an element the spec requires as an added encoding. (#11948)
- **Approved specifications merge on their own again.** Since GitHub's
  2026-06-11 change, workflow runs on a pull request that `GITHUB_TOKEN` opens
  sit at `action_required` until a human approves them, so the spec PR that
  `spec-create.yml` opened never got the required checks and the merge job
  failed with "the base branch policy prohibits the merge". Claude now opens
  the spec PR as `claude[bot]` with the Claude GitHub App token, the pattern
  daily-regen's spec polish already uses, so CI runs without an approval. The
  merge job acts only on the repository owner's `approved` label and verifies
  the PR fail-closed — Claude app author, `specification/<id>` into `main`,
  the issue referenced, and a diff limited to the spec files
  (`automation/scripts/spec_pr_guard.py`) — before it enables auto-merge
  pinned to the verified head commit. It waits up to 15 minutes for the merge,
  then dispatches `sync-postgres.yml`, because a `GITHUB_TOKEN` merge triggers
  no `push` workflows, and only then labels the issue `spec-ready`. The shared
  `spec-merge-main` concurrency group, which cancelled queued batch approvals,
  is gone, and `auto-update-pr-branches.yml` leaves spec PRs alone so its
  `GITHUB_TOKEN` merge commit cannot stall their checks. (#11868)
- **OG cards render from the 800px derivative again, so the API's memory stays
  flat.** `_fetch_image` in `api/routers/og_images.py` only swapped in the
  800px variant for URLs ending in `/plot.png`, and no preview URL has matched
  since they became `plot-light.png` on 2026-04-23. Every OG cache miss
  therefore decoded the full-size original: a median 22 MiB for a branded
  card, 150-200 MiB for a collage (up to ~430 MiB). The allocator kept those
  freed blocks in the render threads' arenas, so the API's memory climbed in
  70-160 MiB steps after large collage misses and never came back down, with
  a risk of running out when two large collages overlapped. Any full-size
  `*.png` preview now maps to its `_800` sibling, which exists for all 4,848
  implementations, and a failed fetch falls back to the original with a
  logged warning instead of a silent `pass`. In a replay of production
  traffic, retained memory stays flat at about +45 MiB and the render peak
  drops to about 157 MiB from 430-580 MiB. (#11867)

*Catalog: 15 new implementations, all for `line-tanabe-sugano`, the spec v3.3.0 added, now at
all fifteen libraries; 143 regenerations across 9 specs (`bubble-basic` 86, most of them in the
regen-gate verification round of 2026-09-27, `bar-spine` 15, `scatter-connected-temporal` 11,
`line-yield-curve` 11, `count-basic` 10, `bar-error` 5, `line-tanabe-sugano` 2, `acf-pacf` 2,
`parliament-basic` 1) and 14 stored re-scores of kept regenerations; 19 spec-only PRs, mostly
the characteristics backfill of the "What a good version looks like" sections (#11949 to
#12049). 315 of
325 specs now at full 15-library coverage (314 of 324 at v3.3.0).*

## [3.3.0] — 2026-09-27 — Through the front door

anyplot 3.3 lets requests and releases reach production only through the front door. Both
origins now refuse what the Cloudflare edge did not stamp — the API's direct `*.run.app` URL
and the site's own nginx, each behind a shared-secret gate that shipped switched off so that
arming it was a measurement rather than a leap — and `script-src` trades `'unsafe-inline'`
for a per-request nonce. Both services deploy through a candidate revision that is
smoke-tested before it takes traffic, and both images are built and container-tested before
merge. The API runs as one warm instance, so a page load no longer pays for a scale-out cold
start; IndexNow carries changed pages to the search engines beyond Google, and search results
now name a plot's languages and libraries.
Behind that: a deploy trigger that sat red for two days while every PR check stayed green, the
gap backfill that brought 314 of 324 specs to all fifteen libraries, and 👍/👎 directly on the
plot.

### Added

- **The gallery links a spec's own page when it is filtered to that spec.**
  `/plots?spec=manhattan-gwas` shows the same implementations as
  `/manhattan-gwas` but never linked to it; getting there meant opening an
  implementation page first. A `{spec_id}.compare() →` link in the style
  guide's explicit-subject form now sits above the grid whenever exactly one
  known spec is filtered. Its click saves the scroll position like a card click
  does and is tracked as `nav_click` with `source: gallery_spec_hub`; its
  accessible name leads with the visible words, without the `.()` a screen
  reader would spell out. (#11845)
- **👍 / 👎 directly on the plot.** A spec detail view now carries a thumbs-up
  button top-left and a thumbs-down button bottom-left over the image — both
  on the static preview and the interactive surface — so rating an
  implementation is one tap instead of a trip through the floating feedback
  menu. The tap inks the thumb, flashes `>>> .liked` / `>>> .disliked` in the
  center like `.copied` does, and posts a reaction-only entry to `/feedback`
  with `library_id` and `language` (a new Alembic revision adds both columns
  and a `(spec_id, library_id)` index), so votes can be counted per image later
  via `FeedbackRepository.reaction_counts` — nothing is displayed yet. One vote
  per image per session: the choice is remembered in localStorage and the other
  thumb fades out, and the server drops a repeat vote from the same session for
  the same implementation silently, so nobody can flip up and down at will.
  Supersedes the stale PR #8126, which placed both thumbs top-left. (#11827)
- **`.claude/guardrails.md`, the long version of the working rules.** `CLAUDE.md`
  is loaded into every session and pays its cost on every turn, so it states each
  rule as one line; the incident that produced a rule, the recipe it implies and
  the numbers that make it credible now live in a companion file that is read
  only when someone hits the situation. Three sections to start with: the two
  lines every delegate brief has to spell out, the pattern for a prod runbook the
  harness classifier refuses (one script in the scratchpad, one `! bash` line for
  the owner, rollback as its own script, a read-back from the session afterwards),
  and why a one-token substitution is not an exemption from the Edit/Write rule.
  `tests/unit/test_agent_instructions.py` pins the split: every section maps to a
  binding one-liner in `CLAUDE.md`, and the companion file has to say that
  `CLAUDE.md` outranks it. (#11605)
- **CI builds the app image and runs the gate against it.** `app/Dockerfile` was
  hadolinted but never built before Cloud Build, which is after the merge — and
  what it produces is not a program that fails to import but an nginx whose
  config is now RENDERED at container start. The new job in `ci-image.yml` runs
  the real image three ways: off, armed, and armed with no secret, checking the
  403, the exempt path, each verdict, and that the secret reaches neither the
  refusal page nor the container log. (#11221)
- **`check` refuses a fragment that still says `(#NNNNN)`.** The reference is
  appended by `/pull_request` when the PR opens, so a fragment is written
  without one — but the placeholder shipped as written reads as a reference in
  the released section and points nowhere, and nothing caught it. The
  complaint names the file and the line; a placeholder quoted in backticks is
  prose about the rule, not a reference, and passes. The README example no
  longer hands the writer a placeholder to leave behind. (#11219)
- **A shared-secret origin gate closes the direct `*.run.app` door, and the apex Worker's
  source moves into the repository** — the API runs on Cloud Run with `ingress=all`, so it
  answers on two addresses: `api.anyplot.ai`, which Cloudflare proxies, and the raw
  `*.run.app` URL, which it does not. Everything the edge enforces — the bot challenge, the
  WAF, the cache that makes the `max-age=300` reads free — was one URL away from being
  bypassed, and `api/request_context.py` already documented callers doing it. A Cloudflare
  Transform Rule stamps `X-Origin-Secret` on everything it proxies for the API host, and
  `api/origin_gate.py` refuses anything without it with 403 before the request costs
  anything. **Unset means off**, which is what makes the rollback a single variable and
  keeps local development and the test suite untouched: the code can ship long before the
  rule and the secret exist. `/health` reports `origin_gate` (`off` · `off-seen` · `ok` ·
  `missing` · `mismatch`) for the request it was asked with — never the value — so every
  route into the service can be measured *before* the switch is thrown; `off-seen` is the
  state every path that must keep working has to reach first. Exempt, as exact paths with no
  prefixes: `/health` (the deploy smoke reaches the candidate on its `run.app` tag URL, which
  never passes the edge) and, until #11214 gave its caller the header, `/debug/cache/invalidate`
  (`sync-postgres.yml` posts to the direct URL by design, because Cloudflare's bot challenge
  answers an unauthenticated curl POST with a 403 HTML page; that endpoint carries its own
  constant-time token), plus `OPTIONS`, which a browser cannot attach a custom header to.
  `/seo-proxy/…` is deliberately
  **not** exempt although the sibling repo exempts it: the site's nginx fetches those pages
  over `api.anyplot.ai` and so carries the header, while an exemption would leave the API's
  most expensive reads open on the direct URL — a cache miss or an unknown id queries the
  repositories, and a crawler user agent schedules an outbound Plausible event per request.
  Every header secret is now compared through one byte-wise comparator
  (`api/secret_compare.py`, used by the gate and by both `/debug/*` locks), because
  `secrets.compare_digest` raises `TypeError` on a non-ASCII `str` while a header arrives
  latin-1-decoded from the wire: comparing strings handed any caller a one-byte way to turn a
  cheap 401 or 403 into an unhandled, logged 500 — including on `/debug/cache/invalidate`,
  which was exempt from the gate precisely because it has its own lock. The Cloudflare Worker
  behind `anyplot.ai/api/*` now has
  its source in `infra/cloudflare/`, because a Worker subrequest to a host in the same zone
  bypasses that zone's Transform Rules — so the Worker stamps the header itself, deleting
  any inbound one first so a caller cannot supply it. The pre-traffic smoke reads the secret
  at run time and sends it, accepting `off`/`off-seen` so the pipeline keeps working before
  the gate is armed and after a rollback. (#11208)
- **The agent instructions are pinned by a test, and the drift it found is fixed** — `CLAUDE.md`
  and `.github/copilot-instructions.md` both open with the claim that they stay in sync, and both
  are read as binding shorthand, but nothing checked either claim. `tests/unit/test_agent_instructions.py`
  adds four cheap pins with no database, network, or fixtures: every backticked repo path resolves
  (57 across the four agent-facing files), every relative link and same-page anchor resolves, every
  skill the routing table names exists as `.claude/skills/<name>/SKILL.md` (8 of them; the harness
  skill `/update-config` is excluded by name), and seven rules that must reach both audiences are
  present on both sides. The mirroring pin is keywords rather than a text diff, because the two
  files address different readers and paraphrase each other — and the keywords carry the
  prohibition, not just its subject, so a rule cannot be reversed while its pin stays green.
  Anchors are matched against real headings only: fenced blocks are stripped first, since these
  guides are full of shell snippets whose `#` comments would otherwise pass as headings. It found
  one real gap and one dead link, both fixed here: `copilot-instructions.md` described the
  pipeline's lifecycle but never stated the repository's most consequential rule — never merge a
  spec or implementation PR by hand, never write the pipeline's files by hand, and put the
  `approved` label on the issue rather than the PR — which is exactly the rule an agent that opens
  and edits PRs is most able to break; and `agentic/docs/project-guide.md` linked to `/CLAUDE.md`,
  which GitHub resolves as a site-root URL and answers with a 404. Same pin as the sibling repo
  kurrentschrift. (#11210)
- **The bot-serving monitor now raises an alarm instead of only turning a tab red, and
  derives what it asserts from the repo** — `bot-serving-check.yml` gained `issues: write`:
  a failing run opens the fixed-title issue **Bot serving check is red** (or comments on it,
  so a long outage is one thread rather than one issue per night) and the next green run
  comments and closes it. Until now the check could only go red in the Actions tab, which is
  exactly how it sat red for ten consecutive nights unnoticed — caused by the other half of
  this change: hard-coded expectations. The swept routes now come from the
  `@router.get("/seo-proxy/…")` decorators in `api/routers/seo.py` — read off the parsed
  AST, so a decorator in single quotes, wrapped over two lines, carrying kwargs or passing
  its path as `path=` is not silently skipped the way a regex skips it, and a path that is
  no string literal at all fails the run rather than disappearing (10 routes today, and a
  new bot page is covered the moment it lands) — and the expected spec title, YAML-decoded
  and then HTML-escaped the way the renderer escapes it, from
  `plots/<spec>/specification.yaml`, so a copy change can no longer make the alarm lie. The
  per-route assertion is the generated `<link rel="canonical">` — the SPA shell carries none
  at all and the href names the route, so one match proves both that the bot hop ran and
  that the right page came back. Two watchdogs stop a silent no-op: the run fails if the
  sweep found no routes or the spec file no title, and it fails if `seo.py` grows a fourth
  parameterized route beyond the three this file probes by hand. The middle of those three,
  the consolidated `/{spec}/{language}`, gained a probe of its own — it must answer 301, and
  a target still carrying `/seo-proxy` is the redirect loop that once cost 48 Googlebot
  "Redirect error" URLs. A `concurrency` group keeps a manual dispatch from racing the
  nightly run over the same issue, and the two issue-mutating steps run only on the default
  branch, so a dispatch from a feature branch can never raise or close a production
  incident. Timeout recomputed to 62 min by the file's own formula (36 checks x 90 s + five
  non-retried probes; 64 min since #11221 added the `/_health` probe). (#11209)
- **The API image is built and its container smoke-tested before merge, not after** — the
  first build attempt of a changed Dockerfile used to happen in Cloud Build, once the PR was
  already on `main`; that is how the deploy-api trigger sat red from 2026-08-30 until #10821
  with every PR check green throughout. The new `.github/workflows/ci-image.yml` builds
  `api/Dockerfile` with Buildx (`push: false`, `load: true`, GHA layer cache), starts the
  result with no database and no secrets, and asserts what only a running container can show:
  `/health` answers, its `version` equals `pyproject.toml`'s (`api/version.py` falls back to
  `0.0.0+unknown` when the installed dist-info is missing — silently, in a field `/health`,
  `/openapi.json` and the MCP server all report), the OG disk fallback
  `api/static/og-image.png` survived the runtime stage's COPY, and the process runs as uid
  1000. Two hadolint steps gate both Dockerfiles at threshold `warning` with named
  exceptions in `api/Dockerfile` — three at first, two (DL3008, DL3025) since #11211 set
  them inline on the instructions they excuse — so a warning of any other code blocks. Change detection
  excludes `plots/**`: the plot pipeline's PRs touch nothing the image serves. Adopted from the
  sibling repo kurrentschrift, which added the same job after its `pyproject.toml` fell out
  of the runtime stage. (#11205)
- **IndexNow: changed pages are pushed to Bing, Yandex, Seznam, Naver and Yep instead of
  waiting for a crawl** — Bing Webmaster Tools' first recommendation for the site. A public
  key file (`app/public/<key>.txt`, served by an explicit nginx `location` so crawler UAs
  are not proxied away from it) proves control of the host, and the new
  `.github/workflows/indexnow-submit.yml` maps every push to `main` that touches `plots/`
  onto the affected `/{spec}` and `/{spec}/{language}/{library}` URLs and POSTs them to
  `api.indexnow.org` (10,000 per request; a deleted implementation is submitted too).
  `workflow_dispatch` with `scope=sitemap` submits every page the checkout holds — the static
  pages, each spec hub and each implementation page — for the initial load. Google does
  not take part and keeps reading the sitemap. The protocol is free.
  (#11202)

### Changed

- **The R pipeline runtime installs `patchwork`, and the ggplot2 prompt names it.**
  `.github/actions/setup-r/action.yml`, which `impl-generate` and `impl-repair`
  use, adds `patchwork` to the packages it installs, and
  `prompts/library/ggplot2.md` lists it for composing several ggplot objects
  into one mosaic or grid layout; `subplot-mosaic`, `upset-basic` and
  `waffle-basic` use it. The change arrived inside the `subplot-mosaic`
  implementation PR: a repair attempt edited both files beside the plot,
  although the repair prompt stages only the implementation file, and nothing
  in review, merge or the changelog gate refused a pipeline PR touching paths
  outside `plots/`. (#11725)
- **The scheduled regen runs once a day instead of ten times.** `daily-regen.yml`
  now ticks at 02:17 UTC only (it ticked every 2 hours outside the 18–21 UTC quiet
  window), so it regenerates one spec per night and leaves the Claude rate limit
  to interactive work during the day. The workflow had been paused since
  2026-08-18 for the gap backfill and is re-enabled with this cadence. The
  watchdog's cron-liveness rescue moves from >10 h to >26 h of silence: at 10 h
  it would have re-dispatched a second run every day, while 26 h first fires at
  the 06:00 UTC scan after a dropped night tick, which replaces the missed run
  rather than adding one. The rescue's clock also starts at the workflow's
  last enable instead of only its newest run, so re-enabling after a pause no
  longer reads the weeks of deliberate silence as starvation and dispatches a
  run hours before the first scheduled tick. (#11848)
- **A `TEMPLATE_LAST_CHANGED` bump now reaches Bing, Yandex, Seznam, Naver and
  Yep.** `indexnow-submit.yml` also runs on pushes that touch
  `api/routers/seo.py`, and submits the full URL list when the diff adds or
  removes the constant's assignment line. Any other change to that file
  submits nothing. Google learns of a bump from the sitemap's `lastmod`, but
  the IndexNow engines never read it, so the retitling of all 5,172 spec pages
  in #11844 had to be submitted by hand. (#11849)
- **Search results for a plot now name its languages and its other
  libraries.** A hub's title and H1 read `{title} in Python, R, Julia and
  JavaScript`; an implementation page's read `{title} in plotnine (Python)`,
  and its meta description adds "also in 14 other libraries". A lead
  paragraph under each H1 names the libraries by language and, on an
  implementation page, links the hub with the hub's own title. A searcher
  reported that "manhattan plot python" returned "Manhattan Plot for GWAS -
  plotnine" with nothing to say that seven other Python libraries had the same
  plot: the hub's title never named a language, so a single implementation
  page outranked it. Languages now follow the registry order (Python first)
  everywhere on both page types. `TEMPLATE_LAST_CHANGED` moves to 2026-09-26,
  which also signals the library-first meta descriptions of 2026-09-02 that
  shipped without a bump. (#11844)
- **The favicon is drawn from the real MonoLisa outlines.** An SVG favicon
  loads no webfonts, so the `<text>` mark always rendered in the viewer's
  system monospace. `scripts/generate_favicon.py` outlines the `ap` monogram
  from MonoLisa Bold into plain paths on an opaque paper ground (a transparent
  icon with dark ink vanished on dark result pages) and rasterizes the ICO and
  PNG siblings from that one SVG. (#11838)
- **The site's typeface is MonoLisa 3.000: MonoLisa Code everywhere, MonoLisa
  Text registered for experiments.** The v3 webfonts (70 Unicode-range subsets
  per family, variable `wght` + `GRAD`) live under `gs://anyplot-static/fonts/v3/`
  and `app/src/styles/fonts.css` is now generated from the order page's builder
  CSS by `automation/scripts/monolisa_fonts_css.py`, so the next font update is
  a re-run. Two v2 → v3 breaking changes are absorbed: the script italic is
  `ss01` (the old `ss02` tag now means "alt i r"), and the coding ligatures
  moved from `liga` to `dlig`, which `tokens.css` re-enables on `pre`/`code` so
  code blocks look as before. The OG-image renderer loads the v3 Code TTFs from
  the same prefix, sets only the `wght` axis of the now two-axis font, and draws
  the tagline with `ss01`. Family names in CSS are `'MonoLisa Code'` and
  `'MonoLisa Text'` (new `--text` token). The v2 files stay in the bucket; their
  removal is a separate, explicitly authorized step after the cutover is
  verified live. (#11836)
- **Coverage cells read as three states, not a gradient.** The mark grew from
  10 px to 16 px inside a 24 px hit area (WCAG 2.2 SC 2.5.8), and full coverage
  now renders as solid brand green while anything short of it carries an ink
  outline (dashed when a spec has no implementation at all), with a labeled
  legend replacing the less/more ramp.
  The interesting signal is which specs are *not* complete, and those are the
  minority — the old opacity ramp made them the hardest cells to pick out. The
  summary line also names how many specs are below full coverage. (#11835)
- **`anyplot-app` runs as a single instance with concurrency 80 (was max 3,
  concurrency 15).** A static nginx never needed a second instance for capacity —
  its files answer in milliseconds and it sits at 15 MiB of memory — yet every
  crawler burst filled the 15 slots and started one or two more instances (50
  AUTOSCALING starts in the ten days to 2026-09-10), because nginx holds a
  proxied bot request open for as long as the API takes to answer. With the API
  on one warm instance those waits are milliseconds, and one nginx with 80 slots
  absorbs the burst without a cold start. `min-instances` stays 0; the API behind
  it caps its own work at 40 in flight. (#11829)
- **`anyplot-api` runs as a single instance: min 1, max 1, concurrency 40.** Every
  scale-out was a cold start that a live request paid for. Between 2026-08-29 and
  09-10 Cloud Run started 464 extra instances (16–54 a day) while the warm one sat
  at a concurrency of ~2, because a page load fans out 4–6 API calls in the same
  instant, and it pinned one call of each burst to the new instance for its full
  9–13 s start — 8 to 37 browser requests a day with referer anyplot.ai, median
  11.3 s, on `/libraries`, `/languages`, `/stats` and `/specs`. With one instance a
  burst queues on the warm one for milliseconds. The limit has headroom: request
  p50 is 32 ms, CPU p95 6 %, more than 9 concurrent requests occur in about two
  minutes a day, and the window saw no 429. `api/cloudbuild.yaml` pins it; if 429s
  ever appear, max 2 is the next step. (#11828)
- **The startup cache prewarm no longer blocks the port.** uvicorn runs the
  lifespan to completion before it binds the socket, so the six awaited prewarm
  queries added a stable ~2.5 s to every cold start (2.0–3.6 s of an ~11 s start,
  measured over 197 starts). The prewarm is now a background task that runs each
  key through `get_or_set_cache`, so it shares the per-key lock with a request that
  arrives first instead of duplicating its query, and it is canceled on shutdown
  before the DB engine closes. (#11828)
- **OG image compositing runs in a worker thread, at most two at once.** The
  collage and branded-image endpoints called PIL inline in the event loop, which
  stalled every other request on the instance for the 1–3 s a render takes, and a
  handful of concurrent collages produced the 647 MiB memory peak of 2026-08-26
  against the 1 GiB limit. With a single instance both would hit the whole
  service; the renders now go through `asyncio.to_thread` behind a two-slot
  semaphore. (#11828)
- **Reaction-only feedback has its own rate limit.** Free-text entries stay at
  5 per minute per IP, now counted over message-bearing rows only; a 👍/👎 tap
  is capped at 30 per minute, so flipping through the library carousel and
  rating several plots no longer trips the free-text limit or blocks a message
  written right after. (#11827)
- **The Edit/Write rule now says what it outranks.** Auto mode hands a delegated
  agent a reminder that prescribes editing files with `sed`, heredocs and short
  scripts, and it arrives later in the context than `CLAUDE.md`, so it reads as
  the more recent instruction — three agents in the sibling repository followed
  it in one day, two of them for the single-token substitution that fills a PR
  number into a changelog fragment. `CLAUDE.md` now states the precedence
  explicitly, and the delegation rule adds the second line a brief has to carry:
  all `git` stays inside the agent's own worktree, because a `git checkout -b` in
  the shared checkout moves a ref the owner's working tree is sitting on. (#11605)
- **`/open-pr` knows what "ready to merge" means since the review ruleset
  changed.** `review_on_push` is `false` in the "Automated Copilot Code Review"
  ruleset since 2026-09-03, so a fix push starts no Copilot run and the absence
  of a `copilot-*` check on the new head SHA is normal, not a reason to keep
  waiting — the skill's gotcha still claimed the opposite. The merge-on-request
  conditions are now written down: non-Copilot checks completed and green
  (deduped by name, newest wins, so a superseded run is not read as red), a
  Copilot review that actually exists on the PR — the head check run only says
  whether a round is still running, since a run reaches `completed` with
  conclusion `cancelled` and delivers nothing — and zero unresolved threads.
  `mergeable=UNKNOWN` is GitHub still computing; a conflict (`CONFLICTING`,
  `mergeStateStatus` `DIRTY`) gets no CI at all and is reported, not waited out.
  Merging stays the owner's call. (#11605)
- **Commit-message and PR-body files are named after the branch.** The scratchpad
  is shared by every agent of one session, so a generic `commitmsg.txt` or
  `prbody.md` gets overwritten by a parallel agent and a later re-read commits
  someone else's text. `/open-pr` now derives the name from the branch and says
  the part that makes it safe: write and consume the file in the same step — it
  is scratch input to one command, not a record. (#11605)
- **A numeric UI rule is verified against the measured result.**
  `/verify-frontend` gains § 3b: a floor, a minimum size or a cap is read off the
  element in the browser, never off the code that computed it. The case is a
  14 px x-height floor whose planner sized lines from an average advance — the
  plan met the floor and the rendered page came out at 13.9 px, because the
  frame's own padding was never in the budget. (#11605)
- **Shortening a text that carries claims is now a checklist.** `/write-docs`
  gains the claim-by-claim diff duty: shortening drops qualifiers before it drops
  sentences, which is how a privacy section lost an overstated retention period,
  a condition on the right to object and part of a list of rights inside an
  otherwise good edit. The owner's own sentences stay verbatim, and a claim that
  cannot be supported is removed rather than softened. (#11605)
- **The three callers that reach the app origin without the edge now carry the
  header themselves.** The pre-traffic smoke in `app/cloudbuild.yaml` reads
  `ORIGIN_SECRET` inside the step rather than through `availableSecrets`, which
  resolves at build start; `bot-serving-check.yml` sends it from the repository
  secret and reads `/_health` first, so a missing or half-rotated secret fails
  with a message naming itself instead of reporting ~36 crawler checks as a
  broken site; and the apex Worker stamps its `/api/event` branch. A `Host` rule
  would have been a real boundary here — `anyplot.ai` is a Cloud Run domain
  mapping, so `$host` does tell the edge from the raw URL — but the bot monitor
  cannot spoof a Host either, and any exception it could present instead is
  public with this repository. (#11221)
- **The frontend deploy smoke checks the nonce before promoting.** The
  candidate has to serve a shell whose `<script>` tags all carry the nonce from
  that same response's header, fetched with `--compressed` so a precompressed
  shell cannot slip past. A lost stamp leaves a page that looks healthy to every
  other probe and runs no inline script at all, so it is worth the one extra
  curl. (#11220)
- **The privacy policy says what the code actually does, per store.** The section had drifted
  behind a year of features: it promised "no personal data (names, emails, etc.)" while the
  feedback widget asks for exactly that ("Name or email (optional)") and keeps it, with the
  message, the page, the user agent and an IP hash, in a table nothing prunes on a timer. It
  also had no legal basis, no jurisdiction, and a rights list missing restriction, objection
  and the complaint to a supervisory authority. Each store now carries its own retention —
  Cloud Logging's 30 days, a feedback entry until it is deleted by hand — because a single
  blanket figure is the qualifier a shortening pass loses first. Plausible is described by the
  property that matters (no cookies, no cross-site identifier, no IP stored, the browser
  talking only to our domain) rather than the false one it used to claim (the script is
  Plausible's, only served from here), Cloudflare's edge processing of the IP is named, and
  the "all services in the EU" line no longer swallows a global CDN and a separate analytics
  service. The crawler body in `api/routers/seo.py` mirrored the same wrong sentence and was
  corrected with it. (#11217)
- **The API deploy gets the three edges the frontend deploy already had** — the candidate
  rollout `api/cloudbuild.yaml` invented was then improved in `app/cloudbuild.yaml` (#11207)
  and the improvements never came back. Three of them do now. `:latest` waits on `promote`
  instead of on `build-image`: it used to reach the registry before the candidate had been
  deployed, let alone smoked, so a build whose smoke failed still left `:latest` naming the
  image that failed it. The smoke re-asserts the `candidate` tag AFTER its probes as well as
  before — the tag is shared across builds, so a concurrent one could move it mid-smoke and
  this build would promote a revision it only believed it had probed; a competing build only
  ever tags its own revision, so ours at both ends means the tag was never reassigned while
  the probes ran. That detects an observed reassignment rather than proving where a probe
  landed: `status.traffic` is control-plane state, and tag-URL propagation can lag it, which
  is the residual `app/cloudbuild.yaml` already documents at its own smoke step. And the
  probes stop piping into `grep -q`, which exits at the first match and SIGPIPEs
  curl — the form only ever passed because `-ceu` carries no `pipefail`, so a later hardening
  pass adding it would have turned every deploy red. They go through the same `expect` helper
  `app/cloudbuild.yaml` uses, which fetches to a file and names the probe and the missing
  needle when it fails; `/health` keeps a bare variant because reaching it without the origin
  header is exactly what its gate exemption has to prove. (#11212)
- **The agent instructions say what the Copilot review ruleset now does: one review per PR, not
  one per push** — review-on-push was turned off in the "Automated Copilot Code Review" ruleset of
  both repositories on 2026-09-03, so the bot runs once when a PR opens or leaves draft and a push
  triggers nothing. `CLAUDE.md`'s PR follow-through and `agentic/commands/pull_request.md` now say
  so, and say not to re-request one per push: each request is a full re-read of the whole diff, and
  the bot then surfaces "previously missed" findings in files the push never touched — which draws
  another push, and another request (the sibling repo's
  [kurrentschrift#406](https://github.com/MarkusNeusinger/kurrentschrift/pull/406) collected ~15 in
  a day over a one-line docstring fix). A fresh review is requested only after a substantive
  rework, and a PR that is green with no open threads needs no further round. (#11216)
- **Every PR now adds a `changelog.d/` fragment instead of a bullet in `CHANGELOG.md`** — the
  shared `[Unreleased]` section is the one place sibling PRs reliably conflict each other, and on
  the night of 2026-09-02/03 it did so three times in a row: each time a hand-resolved rebase for
  text neither branch disagreed about. The `.gitattributes` line-ending rules do nothing for it, and
  a union merge driver would not fix it either — GitHub's own mergeability check ignores merge
  drivers, and a branch that MOVES changelog lines comes out of a union rebase with the block
  duplicated. Fragments remove the shared spot rather than healing it: a PR writes
  `changelog.d/<slug>.md` in the changelog's own format (`### Category` over bold-titled bullets)
  and touches `CHANGELOG.md` not at all, so two PRs never meet at the same line. `tools/changelog`
  is the standard-library tool behind it — `check` (also the CI job "Changelog (fragment)", which
  refuses a missing fragment AND a bullet added to `[Unreleased]` — since #11219 a re-worded one
  passes), `preview`, and `release`,
  which folds every fragment under the new version heading newest-first, bumps `pyproject.toml`,
  `uv.lock` and `app/package.json`, repoints the compare links at the bottom of the file — a step
  `release.md` called easy to forget, so it is no longer a step — and deletes the fragments. The
  exemptions are the ones this repository already had, now enforced rather than remembered:
  catalog-only PRs under `plots/`, the automated plot pipeline and Dependabot (both by author, so
  the gate never sits red on a bot batch), and the `skip-changelog` label. What the tool
  deliberately does NOT touch is the release's two aggregate lines — the italic *Catalog* line and
  the single **Dependencies:** bullet — because those summarize a window rather than a PR and are
  written at cut time. Ported from the sibling repo kurrentschrift, where the same tool has run
  since 2026-08-30. (#11215)
- **The API image build gets a `.dockerignore` that is actually read, loses 69 MB of dead
  weight and ships its own bytecode** — `api/.dockerignore` never did anything: Docker reads
  the ignore file from the build CONTEXT, and both the Cloud Build step and the pre-merge
  image job build with `.` at the repo root. The file said so itself — it excluded `*.md`
  while the builder's `COPY … README.md` succeeded on every build — and the result was a
  context of roughly 230 MB per build, a 120 MB `.git` and a 69 MB `plots/` foremost. The
  replacement lives at the root and is an **allowlist** (`api`, `core`, `pyproject.toml`,
  `uv.lock`, `README.md`): a denylist that misses a new directory only makes the context
  quietly fatter, while an allowlist that misses one fails at the COPY line. The context
  cannot instead be narrowed to `api/`, which is why this shape: the image needs `core/` and
  the lock files, and they live above it. `COPY plots/ ./plots/` is gone from the runtime
  stage — it was 16.6 MB of every pulled image (69.2 MB unpacked, 9,166 files; layer 10 of
  the `latest` manifest) for a directory nothing reads, because the implementations this API
  serves come from Postgres; `ci-image.yml` already said as much where it explains why
  `plots/**` is not a build trigger. `UV_COMPILE_BYTECODE=1` plus a `compileall` over `api`
  and `core` in the runtime stage put `.pyc` in the image, which takes ~1.8 s off every cold
  start (`import api.main` measured at 3.56–4.43 s with nothing cached against 1.79–2.26 s
  with bytecode present) at the price of a bigger venv layer (686.6 MB unpacked / 210.3 MB
  compressed against 493.1 / 142.3). `uv` itself is pinned — the resolver that reads
  `uv.lock` was the unpinned link in the dependency chain, though the image as a whole
  stays unreproducible on purpose: `python:3.13-slim` is a mutable tag and the apt packages
  are deliberately unversioned — and `UV_PYTHON` names the interpreter so uv can never
  quietly download a managed CPython that the runtime stage does not have at the same path.
  With the pin, hadolint's DL3013 exception disappears; the remaining two (DL3008, DL3025)
  move out of the workflow's file-wide `ignore:` and onto the exact instructions they excuse,
  so a new occurrence elsewhere in the file is caught instead of swallowed. (#11211)
- **The frontend deploys through a candidate revision instead of straight onto live
  traffic** — `app/cloudbuild.yaml` now follows the same candidate-rollout pattern as
  `api/cloudbuild.yaml`: deploy with `--no-traffic --tag=candidate
  --revision-suffix=b$BUILD_ID`, smoke the candidate on its tag URL, then `update-traffic`
  to exactly that revision (the chains were not identical at the time — this one pushed
  `:latest` only after the promotion, where the API still pushed it alongside the deploy;
  the API caught up in #11212). The service
  carries the whole crawler path in `app/nginx.conf` — the `$is_bot` map, the `location =`
  bypasses, the `@seo_proxy` upstream — and that is the file whose breakage served every
  bot an HTTP 502 for four weeks in 2026 while humans, Plausible and CI all saw a healthy
  site; until now a typo in it went live unchecked and the daily bot-serving monitor was
  the only net, a night later. The smoke probes both halves of the split (a browser UA
  must get `<div id="root">`, Googlebot must get the prerendered page — asserted on the
  `<link rel="canonical">`, which the SPA shell carries not at all and whose value names
  the route) on the home page and a deep route, plus `robots.txt` and `llms.txt` from the
  `location =` bypasses and the latter's UTF-8 charset. The candidate tag is re-asserted
  after the probes as well as before, so a concurrent build moving it mid-smoke fails this
  build instead of getting it promoted on someone else's evidence. `:latest` moves only
  after this build's promotion, so the tag can no longer name an image that was never
  rolled out, and the build timeout goes to 20 min to leave room for a cold candidate.
  (#11207)
- **The `babysit-pipeline` skill gains the backfill scheduler and the driver's per-spec
  liveness check** — `run_queue.sh <queue-dir> [slots]` keeps N `run_spec.sh` drivers
  in flight over a queue file, skips libraries already on main and confirmed gaps,
  harvests every driver's result into the ledger, holds launches on throttle signs
  (GitHub quota, ≥3 distinct generate pairs failing within 25 min, rate-limit
  signatures in failed logs), and re-queues outage-hit specs from a rescue list only
  once nothing for them is in flight. `run_spec.sh` now reads liveness per spec (its
  own generate runs and open `implementation/<spec>/*` PRs) instead of "any impl-*
  run active", which had produced false PARTIAL verdicts with several drivers in
  flight. `SKILL.md` §5 documents the slot-count rule, the reporting cycle, and new
  gotchas from the 2026-09-02 run: a provider outage reads like a capability cliff, the
  order in which to rescue an outage-hit spec, and the stuck-PR-object symptom behind
  "Head branch is out of date". (#11201)
- **CodeQL moves to an advanced-setup workflow that skips `plots/**`** — the default
  setup scanned five languages on every push to an `implementation/*` branch and every
  impl-* pull request; during the 4-slot backfill of 2026-09-02 up to 23 CodeQL runs
  waited in the runner queue at once, ahead of the pipeline's own jobs. The new
  `.github/workflows/codeql.yml` keeps the same languages and weekly schedule but ignores
  `plots/**` both as a trigger and inside the analysis, so pipeline PRs no longer start
  a scan. Default setup is switched off in the repository settings, which the workflow's
  uploads require. (#11200)
- **The API image is built in two stages and loses more than half its weight** — the
  single-stage `api/Dockerfile` produced a 1.6 GB image (502 MB compressed in Artifact
  Registry) of which 277 MB compressed was ballast in two layers: `build-essential`,
  which never compiled anything because all 108 packages this image installs ship
  wheels, and a `chown -R appuser:appuser /app` that ran after the venv was in place
  and so rewrote the whole environment into a second layer. The build now installs into
  a builder stage and copies only the finished venv across with `COPY --chown`, which
  sets ownership as the layer is written. Measured: 1.62 GB to 693 MB (#11211 later spent
  part of that on bytecode for faster cold starts and dropped the unread `plots/` copy).
  Less Artifact Registry growth per deploy and a shorter deploy rollout. (#10821)
- **The API deploy smoke-tests a candidate revision before it takes traffic** — the
  pipeline deployed straight onto live traffic, so a broken image served users until
  someone noticed. It now deploys with `--no-traffic --tag=candidate` and a
  deterministic `--revision-suffix`, probes that revision on its tag URL (`/health`,
  `/libraries`, `/languages`, `/plots/filter` for the database path, and `/debug/status`
  for the fail-closed admin gate), and only then shifts traffic to exactly the revision
  it smoked — never `--to-latest`, which could promote a concurrent build's unsmoked
  revision. Adopted verbatim from the sibling repo kurrentschrift, which has had this
  net since its first deploy. (#10821)
- **`anyplot-app` scales to zero** — the frontend service ran a permanently warm
  instance for ~EUR 8.30/month while 99.56% of the paid time was idle. It is a static
  nginx image that boots in ~0.26 s, and a 7-day request trace at one-minute resolution
  shows the longest gap between requests is 11 minutes, against Cloud Run's ~15-minute
  idle window — so the instance is in practice never reclaimed and visitors keep the
  same time to first byte. `anyplot-api` keeps `min-instances=1`: its cold start is
  ~11.6 s and its traffic does leave gaps over 15 minutes. (#10812)
- **The API deploy configures the revision additively — `--update-secrets` and
  `--update-env-vars`, not the `--set-` forms** — both `--set-` flags replace their whole set,
  so anything attached to the service out of band is stripped from every revision the pipeline
  creates. `ORIGIN_SECRET` is exactly such a binding — attached by hand to arm the origin gate,
  removed by hand to roll back — and a secret-backed variable lives in the same revision
  environment as a literal one, so either flag was a way to silently disarm the gate on the
  next deploy. It cannot simply be listed in the flag instead: Cloud Run refuses a deploy
  naming a secret that does not exist, which would break every build until the rollout creates
  it. The cost is that a variable dropped from either line is no longer removed automatically.
  (#11208)
- **The analytics middleware moves inside `CORSMiddleware`** — a consequence of where the
  origin gate has to sit. The gate belongs inside CORS, so its 403 still carries the headers
  a browser needs to read it as a 403 rather than as an opaque network error, and outside
  the bot counter, so a refused request can never fire an outbound Plausible event —
  `track_asset_fetch` fires per request for anything with a crawler user agent, so a caller
  on the direct URL could otherwise turn each of its own refusals into one. Those two are
  only simultaneously possible with the counter inside CORS. The cache-header middleware
  stays outside CORS, where its `setdefault` for the /og/ cards depends on being. `api/main.py`
  now carries the stack order and the reason for each position. (#11208)
- **The frontend declares the Node version it is actually built with, and something
  enforces it** — `app/package.json` asked for `node >=20` while the image that produces
  the deployed bundle builds on Node 22 and CI tests on Node 24, so the only version the
  manifest still admitted was the one nothing tests and that reached end of life in April
  2026. The floor moves to `>=22.12.0` — the version the build path actually requires
  (Vite and rolldown declare `^20.19.0 || >=22.12.0`, so `>=22` would have advertised
  22.0–22.11 as supported and let Vite's own engine check reject them instead) — `app/.nvmrc`
  names 22 for `nvm use` and `setup-node`, and `app/.npmrc` sets `engine-strict=true` so an
  npm install in `app/` refuses an unsupported runtime at install time rather than failing
  later inside the build with a message that never mentions the version (yarn 1, the app's
  package manager, checks `engines` itself). `docs/development.md` said "Node.js 20+" and now
  matches. Same pin as the sibling repo kurrentschrift. (#11206)
- **Dependencies:** 15 Dependabot PRs — four security updates close eight advisories, one
  rated critical and three high: `anyio` 4.11.0 → 4.14.2 (#11837), `tornado` 6.5.7 → 6.5.8
  (#10852), `browserslist` 4.28.2 → 4.28.8 (#10853) and `@humanfs/node` 0.16.7 → 0.16.8
  (#11196); `plotly` 6.9.0 → 7.0.0, a major version (#10819), and `fastmcp` 4.0.0b3 → 4.0.2,
  out of beta (#10820, #11634); the grouped python-minor bumps (#10818, #11634) also carry
  `mcp` 2.0.0 → 2.1.1, `anthropic` 1.0.0 → 1.3.0, `statsmodels` 0.14.6 → 0.15.0 and `kaleido`
  1.3.0 → 1.4.0; npm in `app/`: MUI 9.3.1 → 9.4.0 (#10815) and the react (#10814, #11632) and
  npm-minor (#10817, #11633) groups; GitHub Actions: `claude-code-action` 1.0.199 → 1.0.216 and
  `setup-r` 2.12.1 → 2.13.0 (#10816, #11635).

### Removed

- **The `.report()` flag over the plot.** Reporting stays on the spec hub page
  (`report issue ↗`) and via the GitHub issue template; the in-plot flag was
  the least-used overlay action and its corner now belongs to the vote. (#11827)

### Fixed

- **IndexNow no longer submits `/{spec}/python/` redirects.** Both the full
  list and the per-push diff took every file under `metadata/<language>/` as
  a page, so a `.gitkeep` became an empty library and a URL that answers 301.
  The full list now takes only `.yaml` metadata files, and the diff counts an
  implementation file only beside its metadata `.yaml`. The full list drops
  from 5,187 to 5,182 URLs, the size of the sitemap. The 10 stale `.gitkeep`
  placeholders in five fully implemented spec directories are gone as well. (#11849)
- **`docs/reference/plausible.md` describes the recorded gallery paths again.**
  Filter pageviews have been recorded under `/plots/...` since 2026-07-10, but
  the doc still showed the old root paths and missed the `lang` and `language`
  categories. `docs/reference/seo.md` also still said the `/{spec_id}/{language}`
  crawler redirect pointed at a `/seo-proxy/` path. (#11845)
- **Google had no clean image to show as a result's thumbnail.** The only
  preferred-image signal was `og:image`, the text-heavy branded card. Both page
  types now carry a `WebPage` node (`CollectionPage` on the hub) whose
  `primaryImageOfPage` is the exact URL of the render in the body, and the
  implementation's `SoftwareSourceCode` node is marked as the page's main
  entity. `og:image` stays the card for link previews. (#11844)
- **Scroll-to-top button no longer hides under the feedback button.** On
  `/plots` and `/specs` it sat in the feedback button's bottom-right corner —
  fully covered on desktop, a 28 px overlap on phones. It now sits 8 px to the
  left of the feedback button on the same row, rises with it above the footer
  on phones, and the quick-feedback "Thanks!" appears above the button instead
  of in that slot. One `ScrollToTopFab` replaces the copy each page carried,
  and every floating button reads its position from one shared corner geometry
  (`theme/floating-actions.ts`), so they cannot drift into each other again.
  (#11843)
- **Google showed no icon for anyplot.ai.** Crawlers are routed to the bot HTML
  from `api/routers/seo.py`, whose `<head>` declared no icon, and Google's
  `/favicon.ico` fallback returned 404. The bot template now carries the same
  icon links as `app/index.html`, and `app/public/` ships a real `favicon.ico`
  (16, 32, 48 px) and an `apple-touch-icon.png`. `Organization.logo` points at
  the new square `icon-512.png` instead of the 1200×630 banner. (#11838)
- **Coverage matrix on the stats page counted against 9 libraries instead of
  15.** Every cell tooltip read `15/9` for a fully covered spec, and the
  "possible implementations" total was short by the same factor, because the
  page carried a hardcoded library count from back when nine were supported.
  `/insights/dashboard` now serves `total_libraries` (the canonical
  `SUPPORTED_LIBRARIES` size that already backs `coverage_percent`) and the page
  renders against it, so the denominator follows the library set instead of
  drifting from it. (#11835)
- **An empty MonoLisa cache file no longer disables the brand font.** A failed
  download leaves a 0-byte file under `/tmp/anyplot-fonts/` (the client opens the
  target before it fetches), which `_get_monolisa_font_path` accepted as the
  cached font; PIL then failed to open it on every render and the OG cards
  silently fell back to DejaVu for the life of the instance (and the swash test
  failed locally instead of skipping). Empty files now count as missing, a failed
  download deletes its leftover, and the failure is remembered in-process for ten
  minutes so a GCS outage costs one attempt per cooldown rather than one per
  render. (#11828)
- **`docs/reference/performance.md` describes the live services again.** The
  infrastructure table still listed the frontend at min-instances=1 with 256Mi
  (it has scaled to zero on 512Mi since 2026-08-29) and Cloud SQL as `db-g1-small`
  (it is `db-custom-1-3840` on a 3-year commitment). #11828 and #11829 then edited
  the same frontend row from different branches, so it still carried
  max-instances=3 and concurrency 15 after both had merged; a follow-up aligned it
  with `app/cloudbuild.yaml` (one instance, concurrency 80). (#11828, #11830)
- **`impl-review` retries the staging download instead of reviewing an empty directory** — the
  step swallowed a lost `gsutil cp` (`2>/dev/null || true`), the render check right after it
  then failed on nothing, and because that failure set no `ai-review-failed` label, no watchdog
  case picked the PR up: it waited for a manual re-dispatch (#11360 on 2026-09-05, #11678 on
  2026-09-09, staging complete both times). The download now tries three times with a short
  backoff, stops as soon as both theme renders are on disk, and keeps `gsutil`'s stderr in a
  warning per failed attempt, so a transfer blip heals in the same run and a genuinely empty
  staging folder still fails loudly at the render check. (#11697)
- **A re-dispatched `impl-merge` run can finish the bookkeeping of a PR that is already merged** —
  the merge step has long treated "already merged" as success and continued to promotion,
  labels, issue close and the Postgres sync, which is the whole point of dispatching the
  workflow again after a run that crashed post-merge. It never got there: the completeness
  check before it fetched the PR branch, and `gh pr merge --delete-branch` had removed that
  branch at the merge, so the re-run died on `couldn't find remote ref`. Seen on #11295
  (2026-09-05): the GCP auth step failed 5 s after the squash, the images stayed in staging
  while the metadata on main already pointed at production, and the re-dispatch could not
  repair it. The check now reads the files from `origin/main` when the PR is merged — where
  the squash commit put them — and no longer tries to close a merged PR when they are absent. (#11307)
- **The Worker deploy recipe now uploads a module Cloudflare can find.**
  `infra/cloudflare/README.md`'s `curl` example named the multipart part
  `worker.js=@infra/cloudflare/anyplot-api-proxy.js;type=application/javascript+module`,
  but curl defaults the part's `filename` to the local file's basename
  (`anyplot-api-proxy.js`) unless told otherwise, and Cloudflare resolves the
  metadata's `main_module: "worker.js"` against that filename, not the form
  field — so the API answered `400 — Uncaught Error: No such module:
  worker.js` (observed live 2026-09-04). The example now sets
  `filename=worker.js` explicitly, with a sentence explaining why. (#11222)
- **The README's "needs a redeploy" callout is replaced with the deployed
  state.** The Worker was redeployed from the current `.js` after #11221, the
  Transform Rule now covers `anyplot.ai`, `www.anyplot.ai`, and
  `api.anyplot.ai`, and `/api/event` measured `off-seen` — the callout named a
  pending step that had already happened. (#11222)
- **The python.anyplot.ai spec routes sent the SPA shell with no
  `Cache-Control` at all.** `try_files /index.html =404` answers with the shell
  as a file inside that location, so it never reaches `location =
  /index.html` and never inherited its `no-store` — measured against a local
  nginx while the main host answered correctly on the same path. A stale shell
  asks for `/assets/` hashes a later deploy no longer has; with the nonce it
  would additionally pair an old `nonce="…"` with a fresh header. Both routes
  now send the shell's `Cache-Control` and re-include the security-header
  snippet beside it, since an `add_header` of their own would otherwise have
  dropped the whole inherited set. (#11220)
- **Correcting a bullet in `[Unreleased]` no longer reads as adding one.**
  The fragment gate compared bullet SETS, so re-wording an entry the base
  already carried was indistinguishable from writing a new one and got the
  same refusal — "gained a bullet, it belongs in a fragment" — for a change
  that added nothing. A bullet is now identified by its bold title
  (`tools/changelog`, `bullet_title`), collapsed over the line breaks so a
  correction may reflow the very line the title runs over, and counted rather
  than set-differenced so a second copy of a title cannot slip in behind the
  first: a title the base lacks is an ADDED bullet and is still refused, a
  title it has is a CHANGED one and passes. (#11219)
- **The API host stamps its own security headers, `/_health` stops dropping the site's,
  and the CSP is guarded by a test that pins what a nonce later replaced** — api.anyplot.ai
  is a separate origin with no nginx in front of it, so it inherited none of
  `app/security-headers.conf`: only `/proxy/html` set
  `nosniff` and a `Referrer-Policy`, on that one response. An outermost middleware now
  `setdefault`s both on every response that leaves through the stack — CORS preflights, the
  origin gate's 403, an `HTTPException`'s 4xx — and the unhandled-500 handler stamps the
  same pair through the same helper, because `ServerErrorMiddleware` wraps every user
  middleware and builds that response outside the stack, which is the one exit a middleware
  cannot reach. Deliberately **not** `X-Frame-Options`, because
  the SPA embeds `/proxy/html` cross-origin in an iframe and `SAMEORIGIN` would break
  every interactive preview. On the website, both `/_health` locations set an
  `add_header` of their own without re-including the snippet, and nginx drops every
  inherited header in such a location — the rule the file states at the top and the one
  place that had missed it. Both were found by the new
  `tests/unit/api/test_csp_policy.py`, which also pins that the CSP keeps `object-src
  'none'` and `base-uri 'self'`, that a `report-to` group it names is actually defined by a
  `Reporting-Endpoints` header (reports to an undeclared group go nowhere, and nowhere reads
  exactly like "no violations"), and that the
  three sha256 hashes the policy held in reserve still described `app/index.html`'s
  inline scripts. Those hashes stayed in reserve rather than in force for a measured
  reason: mounted over the live production bundle through a local proxy, a hash-only
  `script-src` blocks exactly one script — the inline one **Cloudflare JavaScript
  Detections injects at the edge**, whose body carries a per-response ray id and so has
  no fixed hash. With `'unsafe-inline'` its hidden iframe appears, with hashes it does
  not and the console reads "The action has been blocked". Hardening with hashes would
  have silently cost bot detection on a site whose origin gate leans on the edge; the way
  out was a nonce (Cloudflare stamps its injected script with the nonce it parses from
  this header), which #11220 shipped a day later with an nginx `sub_filter`. All of it is
  written down at the directive it explains. (#11213)
- **The IndexNow workflow no longer waits eight minutes behind an edge 403** — its
  key-file readiness loop treated every non-200 as "not deployed yet"; a GitHub runner
  that Cloudflare's bot management answers with 403 would have slept the full budget on
  every run. A 403 now ends the wait without claiming anything about the deploy (the
  edge answers before the origin is asked, so it is inconclusive either way; IndexNow's
  own key fetch is the authoritative check), and the final warning names the last
  status seen. The submission body goes
  through a file (a full-sitemap batch is ~260 KB, above the 128 KB command-line
  argument cap that made the first sitemap-scope run report HTTP 000), and a first-use
  `403 SiteVerificationNotCompleted` from IndexNow is retried for up to ten minutes
  before the run fails, so a `changed` run keeps its URL set re-runnable. (#11204)
- **Implementation pages no longer share one meta description per spec** — the SEO
  proxy reused the spec description verbatim as the `<meta name="description">` and OG
  description of every implementation page, so up to 15 library pages and their hub
  carried an identical snippet; 4,254 plot pages had about 334 distinct descriptions,
  which Bing Webmaster Tools flagged as "too many pages with identical meta descriptions".
  The snippet now opens with the page's identity, `{title} in {library} ({language}):
  {description}` (#11844 inserts ", also in N other libraries" before the colon), trimmed
  to 155 characters as before, so a searcher who typed the
  library name sees it in the result. The hub keeps the plain description; body copy
  and JSON-LD are unchanged. (#11203)
- **Infrastructure failures no longer spend a pair's generation budget** — the
  3-attempt cap in `impl-generate.yml` counted every failed run alike, so the Claude
  outage of 2026-09-02 (03:15–03:45 UTC, every run ending in `is_error:true` with an
  "Internal error") burned all three attempts of 27 pairs in twenty minutes, and for the
  rest of the 12-hour window each re-dispatch ran without any auto-retry. The failure
  handler now classifies the run from the step outcomes: both Claude runs dying with a
  provider-side signature in the execution log, a Google Cloud auth/SDK/upload failure,
  or a GitHub API failure at PR creation or review dispatch is an infrastructure failure.
  Those are recorded with an extra `<!-- impl-fail-cause:infra -->` tag, excluded from the
  genuine count, and retried on a separate cap of 5 per window, after which the pair is
  paused without `impl:<lib>:failed` (an incident is not a capability verdict). "Agent
  reports success but writes no file" and a missing theme render still count as before.
  (#11199)
- **A merged implementation now clears its `impl:<lib>:failed` label and the watchdog's
  retry marker** — impl-merge removed the stale labels in one comma-separated
  `gh issue edit`, and `gh` rejects the whole call when any name in the list is not a
  repository label (`impl:<lib>:pending` only exists on demand), so the fallback added
  `impl:<lib>:done` and left `impl:<lib>:failed` in place. Issues #3343 and #3650 ended
  the 2026-09-02 outage rescue with both labels for the same libraries, and every
  watchdog scan since reported those pairs as "already retried — needs manual
  attention". The labels are now removed one at a time, each call tolerated, and
  `watchdog:retried-<lib>` goes with them. (#11197)
- **The watchdog now rescues a repair that crashed after a rejection** — a PR carrying
  `ai-rejected` and `ai-attempt-N` is the state impl-review leaves behind when it
  dispatches a repair that then dies (its crash-retry exhausted). Case 2 excluded
  `ai-rejected` and case 4 required no attempt label, so the state matched nothing:
  after the Claude outage of 2026-09-02 (03:15–03:45 UTC) three PRs sat in it for hours
  until a human re-dispatched the repair. New case 2b re-dispatches `impl-repair` with
  the highest attempt number, bounded by the same `watchdog:repair-rescued-<N>` marker.
  (#11198)
- **Watchdog generation retries go straight to `impl-generate` and are marked only once
  the run exists** — the issue scan dispatched `bulk-generate.yml`, which serializes on
  one global concurrency group; GitHub keeps a single pending run per group and cancels
  the older pending run whenever a newer one queues. Nine rescues fired 5 s apart on
  2026-09-02 produced two runs and seven silent `cancelled`s, yet every pair had already
  been labeled `watchdog:retried-<lib>` and so dropped out of all future scans. The
  rescue now dispatches `impl-generate.yml` (concurrency group per pair, `issue_number`
  passed through), waits up to 60 s for the run to appear, and sets the marker only
  then. Every rescue marker moves behind its dispatch the same way, and `dispatch()`
  reports the outcome after the attempt and returns non-zero instead of aborting the
  scan under `set -e`, so one failed `gh workflow run` no longer leaves every later PR
  unscanned. (#11198)
- **OG cards render MonoLisa's italic swashes in production again — the API image installs
  `libraqm0`, after the guard added on the way had blocked every deploy since 2026-08-30** —
  the live `api.anyplot.ai/og/home.png` was pixel-identical to a render forced onto Pillow's
  BASIC layout engine: the deployed container's Pillow had no libraqm, so the `ss02`
  stylistic set on `— any library.` was dropped and no text was kerned, while the helper
  that draws feature runs swallowed the exception and the endpoint kept returning a valid
  200 PNG. The fallback now warns once per process and the API logs the shaping capability
  at startup. The build-time assertion on `features.check('raqm')` that came with it assumed
  the locked Pillow 12.3.0 manylinux wheel bundles libraqm. It does not: the wheel
  `dlopen()`s libraqm at runtime, so in a bare `python:3.13-slim` the check is `False` and
  both HarfBuzz and FriBiDi report no version at all. The assertion therefore failed every
  build of this image and the `deploy-api` trigger stayed red, so the API kept serving the
  v3.2.0 image of 2026-08-28 until the Debian `libraqm0` package (32 KB plus its HarfBuzz/FriBiDi
  dependencies) turned the check `True`, verified in the built image. The assertion also
  moved to the runtime stage, where it checks the image that actually serves: in the
  builder stage it would pass on a venv whose runtime never got the library, which is
  exactly the false green the guard exists to prevent. (#10813, #10821)

### Security

- **The site's own origin has a gate now, and it ships switched off.** The API's
  shared-secret gate closed one of two doors; `anyplot-app` stood with
  `ingress=all` beside it, serving the whole site from its `*.run.app` URL with
  no bot challenge, no WAF and no rate limit — and relaying any crawler user
  agent through `@seo_proxy` into a repository query and a Plausible event.
  `app/origin-gate.conf.template` is the nginx half: the base image's own
  envsubst entrypoint renders the maps with the secret before nginx starts, and
  every server block refuses what the Cloudflare edge did not stamp.
  `ORIGIN_GATE` unset means off, `on` means 403, and armed with no secret fails
  CLOSED — the map keys are tagged so an empty value cannot become "match
  anything". The header is consumed by that server and never forwarded: every
  `proxy_pass` clears it, so the Plausible hops cannot hand a third party the
  key both services take. Nothing is armed by merging: the rollout, the
  hostnames the Transform Rule has to cover and the rollback are in
  `infra/cloudflare/README.md`. Both gates have since been armed: the direct
  `*.run.app` URLs of `anyplot-api` and `anyplot-app` answer 403, and `/health`
  and `/_health` report `ok` through the edge (checked 2026-09-27). (#11221)
- **`X-Origin-Gate` on `/_health` makes arming a measurement rather than a
  leap.** The same five verdicts the API reports — `off`, `off-seen`, `ok`,
  `missing`, `mismatch` — for the request they were asked with, never the value.
  Ask every route into the container while the gate is still off and arm only
  once each one that must keep working reports the header arriving. The apex
  Worker's path cannot be asked that way, so `/api/event` reports it too: that
  is the one path the Worker sends to this container, a Worker subrequest skips
  its own zone's Transform Rules, and arming it blind would have answered every
  Plausible pageview on the site with a 403. (#11221)
- **`script-src` drops `'unsafe-inline'` for a per-request nonce.** nginx mints
  one from `$request_id` — 16 random bytes as 32 hex digits — sends it in the
  policy and stamps the same value onto every `<script>` tag of the shell with
  `sub_filter`, in both server blocks. The measurement that stopped the hash
  version a day earlier is what makes this the right shape: Cloudflare
  JavaScript Detections injects an inline script at the edge whose body carries
  a per-response ray id, so it has no listable hash — but Cloudflare documents
  that it copies a nonce out of the response header onto that script, which a
  hash could never be. Cache safety comes from three sides: the shell is
  `no-store`, `sub_filter` clears `ETag` and `Last-Modified` on its own, and
  `index.html` is now excluded from build-time precompression, because
  `gzip_static` would otherwise serve an unstamped `.gz` and quietly block
  every inline script on the page. (#11220)
- **The origin gate loses its last real exemption: the cache flush now carries the edge's
  header instead of being waved through** — `/debug/cache/invalidate` was exempt because
  `sync-postgres.yml` has no front door to come through: it posts from a GitHub runner to
  the direct `*.run.app` URL on purpose, since Cloudflare's bot challenge answers an
  unauthenticated curl POST against `api.anyplot.ai` with a 403 HTML page. The workflow now
  sends `X-Origin-Secret` itself, out of an `ORIGIN_SECRET` repository secret, so the
  exemption is gone and `EXEMPT_PATHS` holds exactly one entry — `/health`, which the deploy
  smoke needs on the candidate's tag URL. The trade is worth naming: an exempt path is one
  anybody may POST to from anywhere with only `CACHE_INVALIDATE_TOKEN` behind it, whereas a
  caller that carries the header needs no hole at all. The two locks now sit in series, and
  the test suite pins both ends — 403 without the header, 503 (the endpoint's own
  fail-closed answer) with it. A missing repository secret fails that step with a message
  naming it, rather than leaving the cache to go quietly stale. The second door the gate
  did not close — a crawler user agent reaching the prerendered pages through the APP
  service's raw `run.app` URL — was measured rather than suspected (a Googlebot UA got
  HTTP 200 and the correct canonical), and `api/origin_gate.py` records the two facts that
  decide how it can be closed: Cloud Run answers a foreign `Host` header with its own 404,
  so a host rule in `app/nginx.conf` would be a real boundary rather than theatre — and
  `bot-serving-check.yml` probes exactly that origin and cannot spoof the host either, so
  the exception it needs has to be the shared secret: templating the app's nginx,
  attaching the secret to `anyplot-app`, and a Cloudflare Transform Rule for the
  `anyplot.ai` host. Four coordinated changes, two in the dashboard, one able to lock out
  every visitor if it landed out of order — #11221 shipped the app's gate switched off, and
  the Transform Rule now covers `anyplot.ai`, `www.anyplot.ai` and `api.anyplot.ai`
  (#11222). (#11214)
- **`click` 8.3.1 → 8.3.3 closes PYSEC-2026-2132** — the only advisory `pip-audit`
  reports against the resolved runtime dependency set (`uv export --no-dev`), which now
  comes back clean. A transitive dependency, so the fix is a lock-file bump with no
  `pyproject.toml` constraint, per the repository's dependency rule. The bump is the
  minimal one that clears the advisory; `click` 8.5.0 exists and is left to Dependabot,
  where a minor bump of the library behind every console script gets its own PR and its
  own CI run. (#11206)

*Catalog: 966 new implementations across 146 specs — the gap backfill of 2026-09-01 to 09-10
(ECharts 145, D3 145, Chart.js 144, Highcharts 144, MUI X Charts 144, Makie 144, ggplot2 99,
plotnine 1) — and 1 regeneration, daily-regen having been paused for the backfill; 314 of 324
specs now at full 15-library coverage (174 at v3.2.0), the other 10 short by 12 recorded gaps
(Chart.js 4, plotnine 4, Highcharts 2, MUI X Charts 2); 1 new spec (line-tanabe-sugano, not yet
implemented); 4,848 implementations across 324 of 325 specs; 27,367 stale GCS objects (old-layout renders,
python/highcharts orphans, staging leftovers) moved to an archive prefix on 2026-09-16.*

## [3.2.0] — 2026-08-29 — Findable by assistants

anyplot 3.2 makes the catalogue findable by assistants, not only legible to them. The sister
project showed that an assistant's fetch tool often follows only URLs it has already seen in
fetched text, so the machine guide and one complete, callable example per surface now stand
wherever an agent actually reads — the SPA shell, both `robots.txt` files, every bot page. The
whole catalogue is one fetch (`llms-full.txt`), the MCP server tells the truth for all fifteen
libraries, and the bot site finally counts the crawler reads Plausible had been discarding.
Behind that: a generation retry cap that had parked 87 library pairs for good, a frontend deploy
that had failed silently, and a masthead that had claimed v1.0 through two releases.

### Added

- **LLM discoverability sync from kurrentschrift** — the sister project's
  assistant-protocol findings (2026-08-28) carried over: assistants' fetch tools often allow
  only URLs that already appeared verbatim in fetched content, so the machine guide and one
  complete, callable example per surface now stand wherever an agent actually reads. The SPA
  shell carries a `<link rel="alternate" href="/llms.txt">` and a `<noscript>` block with
  absolute URLs (guide, `llms-full.txt`, one code endpoint, one render PNG, OpenAPI, MCP);
  `/.well-known/llms.txt` redirects to the guide instead of soft-404ing with the shell, and
  `api.anyplot.ai/llms.txt` redirects to the site file instead of 404ing; both `robots.txt`
  files name `llms.txt` and the OpenAPI spec (two terse lines at the very top of the site
  file, a fuller block beside `Sitemap:`, the API host's comment head); every bot page links
  the guide from its footer nav, and every implementation page spells out its own code URL
  and carries a visible JSON retrieval record beside the JSON-LD (HTML-to-Markdown converters
  drop `<script>`, keep `<pre>`). The nginx map and `AI_AGENTS` gain `xai` (a `xAI-Bot` UA
  fell through to the empty shell) and the bare `grok` token that was prerendered but never
  counted. A new `asset_fetch` event on `bots.anyplot.ai` records which implementation's
  code and which spec's detail assistants fetch through the API (cache misses — see
  `docs/reference/plausible.md`). Guards: `app/src/routes/seoCoverage.test.ts` pins llms.txt
  ↔ route registry ↔ robots.txt ↔ shell; `bot-serving-check` adds the `.well-known`
  redirect, the robots/sitemap bypasses, the site card, a real 404 and a deep-route SPA
  control. Doctrine: `docs/reference/seo.md` "Discoverability for assistants" (#10808).
- **`llms-full.txt` — the whole catalogue in one fetch** — a new
  `GET /llms-full.txt` lists every spec on one line (id, title, hub URL, implemented
  libraries) under a header that documents the retrieval recipes that work for *every*
  HTTP client: the code endpoint, the GCS render URL pattern (light/dark, responsive
  widths, WebP), OpenAPI and the MCP endpoint. Until now an agent had to walk the 400 KB
  sitemap or guess URL shapes; the prerendered pages that carry this information are
  user-agent-gated, so most agents never saw them (AI-access audit 2026-08-19) (#10487).
- **MCP `get_spec_detail` takes a `libraries` filter** — a 15-library spec's full response
  carries every implementation's complete source (~0.5 MB, a context-window hazard for the
  agents the tool serves); passing `libraries=["seaborn", "d3"]` now trims it to the
  implementations actually asked for (#10489).

### Fixed

- **`uv.lock` was unparseable after three Dependabot merges landed in sequence** — #10614,
  #10615 and #10616 each carried the new `httpx2` and `httpx2-jsfetch` package blocks, and the
  three squash merges kept every copy, so `uv lock` and every `uv run` on `main` failed with
  "Dependency `httpx2` has missing `source` field but has more than one matching package". The
  duplicate blocks are removed and the lock re-validated; found by this release's version bump,
  the first Python-touching change after the three merges (#10811).
- **Crawler reads on the bot site were mostly dropped by Plausible** — on the prerender path
  (Cloud Run app → Cloudflare → API) `cf-connecting-ip` is the app container's Google egress
  address, exactly the "hosting provider IP" Plausible discards, and `visitor_ip` preferred
  it over the forwarded list where the crawler actually stands. kurrentschrift measured one
  counted read in twenty with probe events (2026-08-28). `visitor_ip` now reads the leftmost
  valid `x-forwarded-for` entry first and falls back to `cf-connecting-ip`; nginx's
  `@seo_proxy` forwards the crawler in `X-Forwarded-For` explicitly (#10808).
- **`robots.txt` carried an invalid `use=reference` Content-Signal token** — the
  contentsignals.org vocabulary is exactly `search`, `ai-input` and `ai-train`; a strict
  parser may discard the whole line over an unknown token, taking the three real signals with
  it. Dropped from both groups; `seoCoverage.test.ts` pins the vocabulary (#10808).
- **The generation retry cap counted a library's entire failure history, not the current
  run** — `impl-generate.yml` derives its "3 attempts" budget from hidden marker comments
  on the spec issue, and nothing ever deletes those markers. A `(spec, library)` pair that
  failed twice at any point in the past was therefore capped forever: every later dispatch
  got a single attempt, and one hit of the intermittent "agent reports success but writes
  no implementation file" failure (8 of 85 generate runs on 2026-08-24) parked it under
  `impl:<library>:failed`, which nothing retries — the watchdog only reports it as needing
  manual attention. Repo-wide that state had accumulated on **87 `(spec, library)` pairs**.
  Marker counting is now scoped to a 12-hour campaign window, so stale history ages out and
  a fresh dispatch gets its full three attempts. The fail-closed behaviour on an unreadable
  counter (issue #1010: ~1,200 runs in 38 h) is untouched (#10627).
- **A failed library no longer claims three attempts it never made** — the cap message read
  `Marking <lib> as failed: 3 generation attempts` even when the run made exactly one, which
  reads as "tried repeatedly, must be a genuine capability gap". It now names the counted
  failures and the window. Three pairs written off under the old wording on 2026-08-24
  succeeded on the very next dispatch (#10627).
- **A disabled `daily-regen` no longer fails every watchdog scan** — the watchdog's
  cron-liveness rescue read the growing silence of a manually disabled schedule as
  starvation and tried to dispatch it; GitHub answers `workflow_dispatch` on a disabled
  workflow with HTTP 422, so the scan step died under `set -e` after sections A and B had
  already run, and the run reported failure. The rescue now checks the workflow's state
  first and skips with a notice when it is not `active` (#10540).
- **Image structured data carries the licensing fields Google recommends** — Search
  Console flagged every implementation page's `ImageObject` for missing `creator`,
  `copyrightNotice`, `creditText`, and `acquireLicensePage`. The bot-page JSON-LD now
  ships all four (creator/credit: anyplot; MIT copyright notice; `/legal` as the
  license page), completing the image-metadata rich result beside the existing
  `license` field (#10537).
- **Top-rated thumbnails follow the theme** — the stats page picks a preview per theme, but
  `/insights/dashboard` never shipped one: its `TopImpl` response model carried only the
  legacy `preview_url` (a synonym for the light render), so the top-rated grid showed
  light-styled plots on a dark page. The model now carries `preview_url_light` and
  `preview_url_dark`, like every other themed payload in the router (#10536).
- **The MCP server now tells the truth for the whole catalogue** — `get_implementation`
  called the repository without a language, whose `python` default made all 1,004
  R/Julia/JavaScript implementations (28% of the catalogue) answer a false "not found";
  the language now comes from the library's own row. Every discovery tool's `website_url`
  pointed at `anyplot.ai/python/{spec}`, which 301s into a 404 — now the hub. And
  `get_spec_detail`'s per-implementation URLs, silently discarded by Pydantic coercion,
  survive the roundtrip. Stateless HTTP mode is finally real: it is passed explicitly to
  `http_app()` — the env-var route ran after fastmcp's settings were read and never
  engaged, leaving MCP sessions pinned to one Cloud Run instance (#10489).
- **Plot renders embed cross-origin** — the `anyplot-images` GCS bucket sent no CORS
  headers at all, so chat UIs that fetch image bytes in-page (the way AI assistants
  inline a remote image) were blocked by the browser even though the objects are public.
  A read-only bucket CORS policy (`GET`/`HEAD`, any origin) fixes the whole failure
  class; the policy and re-apply procedure are recorded in the project guide because
  bucket metadata does not deploy with the repo (#10489).
- **The bot-served `/mcp` page now says how to connect** — the one page whose entire
  audience is AI agents rendered as title + one-line description; it now carries the
  endpoint URL, a `claude mcp add` setup snippet, the six tools, and pointers to the
  JSON API and llms-full.txt for clients without MCP support (#10489).
- **Live-verification follow-ups** — a 49-check production sweep across every access
  path (crawler UAs, machine files, REST, images/CORS, JSON-LD, MCP) found four small
  leftovers: og cards sent no `Access-Control-Allow-Origin` to foreign origins (the same
  in-page-fetch blocker fixed for the GCS bucket — now `*` via the cache-header
  middleware); `llms-full.txt` lines now list implementations as `{language}/{library}`
  so the render URL is buildable from the file alone; error responses on prerendered
  pages no longer echo the internal `/seo-proxy` path prefix; and MCP `serverInfo` now
  reports the app version instead of fastmcp's package version (#10490).

- **The API host no longer forbids itself to AI agents** — `api.anyplot.ai/robots.txt`
  served `Disallow: /` (only `/og/` excepted), telling every robots-compliant assistant
  that the REST endpoints, `openapi.json` and the MCP transport were off-limits — on the
  very host `llms.txt` advertises as the machine interface. The read API is now open;
  only `/debug` and `/proxy` stay excluded (#10487).
- **Non-Python code is reachable at the obvious URL** — `/specs/{id}/{library}/code`
  defaulted its `language` parameter to `python`, so the natural URL 404'd for all seven
  R/Julia/JavaScript libraries (28% of the catalogue) with a misleading "not found".
  Library ids are globally unique, so the language now resolves from the registry;
  an explicit `?language=` still wins (#10487).
- **HEAD requests answered 405 across the whole API** — FastAPI's `@router.get` registers
  GET-only routes, so agents and link checkers that preflight with HEAD concluded every
  page was unavailable. An ASGI middleware now answers HEAD like GET without a body
  (and without doubling the documented surface in openapi.json) (#10487).
- **Structured data hands agents the plot, not the branding card** — the per-implementation
  `SoftwareSourceCode` JSON-LD declared the 1200×630 og card as its `image`; it now carries
  the actual render as an `ImageObject` (full-size + 1200px thumbnail) plus the fields an
  assistant checks before reusing code: `license` (MIT), `codeRepository`, `dateModified`,
  `keywords`, `author`, `isBasedOn` — previously present only in the SPA's JSON-LD, which
  no crawler executes. Spec-hub bot pages likewise show the best real render (with the
  full asset list) instead of the og collage, and their `ItemList` names each
  implementation's render URL (#10487).
- **One version, everywhere** — `openapi.json` claimed 1.0.0 and "9 libraries", `/health`
  said 0.2.0, pyproject said 3.1.0. All surfaces now report the packaged version and a
  registry-derived library/language count, and `openapi.json` names its production server
  so the spec is usable standalone (#10487).

- **Deploy checks could report another project's builds** — the runbook's recipe for
  "did this actually deploy?" flagged `--region` as the easy thing to forget and treated
  `--project` as incidental. It is not. A gcloud install whose default project is a
  different one returns *that* project's builds, and when its triggers happen to carry
  the same names in the same region, the wrong answer is indistinguishable from the
  right one — no error, just a credible list of `deploy-api` runs that stop a few days
  ago. It produced a false "nothing has deployed since 2026-08-16" on a day with a dozen
  deploys. `agentic/docs/project-guide.md` now names both flags and the context check
  that settles it (#10484).
- **The frontend deploy was broken by the version fix that preceded it** — #10485 read the version
  from the repo-root `pyproject.toml` at build time, but the frontend image is built with
  `docker build -f app/Dockerfile app`: the build context is `app/` alone, so nothing above it
  exists and `vite build` died with `ENOENT .../pyproject.toml`. Cloud Build failed, Cloud Run kept
  serving the previous revision, and the CSP fix never reached anyplot.ai even though every PR
  check was green — the exact failure mode `CLAUDE.md` warns about. The version now comes from
  `app/package.json`, which is always inside the build context, and
  `tests/unit/test_version_sync.py` holds it equal to the `pyproject.toml` `[project]` version.
  That test runs on every PR touching `pyproject.toml`, so release PRs cannot reintroduce the
  drift that left `app/package.json` at 2.0.0 through the whole 3.x line (#10486).
- **The client bundle no longer ships the frontend dependency list** — `global-config.ts` imported
  `package.json` as a default import, which inlined the entire manifest (every dependency name and
  version range) into a shipped chunk. It now imports only the `version` named export (#10486).
- **The masthead had been advertising v1.0 since the security-headers rollout** — the version next
  to `~/anyplot.ai` comes from the GitHub releases API, and the CSP shipped in the 2026-07-16 audit
  never listed `api.github.com` under `connect-src`. Every browser blocked that request, the hook
  returned `null`, and the masthead fell back to a hardcoded `'v1.0'` — so the v3.0.0 and v3.1.0
  releases both went out to a site claiming to be v1.0. Returning visitors kept seeing a plausible
  number from their `localStorage` cache, which is why this survived two releases. `api.github.com`
  is now allowed in `connect-src` (#10485).
- **The version fallback no longer invents a number** — the fallback is on screen for every cold
  load while the API call is in flight, and stays there whenever GitHub is unreachable or
  rate-limits the visitor's IP (60 requests/hour, unauthenticated). It now renders the build-time
  project version, injected by Vite from the `[project]` version in `pyproject.toml` — the same
  field the release flow bumps — instead of a literal that nobody would think to update. A test
  asserts the injected value matches `pyproject.toml`, so the two cannot drift (#10485).
- **The crawler allowlist no longer misses documented crawlers — or Grok** — nginx's UA map
  lacked `Amazonbot` and `meta-externalagent` (both documented crawler tokens; the existing
  `amzn-*` / `meta-externalfetcher` entries never matched them) and matched xAI only via
  `grokbot`/`xai-grok`/`grok-deepsearch`, so a bare `Grok` UA fell through to the empty SPA
  shell — the exact "insufficient relevant content" a user's Grok session reported. The map now
  matches `~*grok` (subsuming all three), Amazonbot, meta-externalagent, Diffbot and Firecrawl,
  and the daily bot-serving monitor covers the new tokens (#10488).
- **JS-less clients no longer see a completely empty page** — the SPA shell was
  `<div id="root">` with no `<noscript>`, so any fetcher missing from the UA allowlist rendered
  literally nothing. A noscript block now points such clients at `llms.txt`, `llms-full.txt`,
  the JSON API and the GitHub repository (#10488).
- **Text files declare UTF-8** — `llms.txt` and `robots.txt` carry em dashes and arrows but
  were served as bare `text/plain`, which a strict client decodes as Latin-1 mojibake. nginx now
  declares `charset utf-8` on text responses in both server blocks, and the daily bot-serving
  monitor asserts it on `llms.txt` (#10492).
- **The image bucket is no longer publicly listable** — `allUsers` held
  `roles/storage.objectViewer` on `anyplot-images`, whose bundled `storage.objects.list` let
  anyone enumerate the whole bucket, including the `staging/` prefix where unreviewed pre-merge
  renders sit indistinguishable from promoted ones. Swapped to `roles/storage.legacyObjectReader`
  (get-only): every render URL keeps working (verified live incl. CORS), only the directory
  listing is gone. Applied 2026-08-19 via gcloud — bucket IAM does not deploy with the repo; the
  policy and re-apply procedure are recorded in the project guide (#10493).

### Changed

- **GitHub releases are the CHANGELOG section condensed, never copied** — a release body now
  carries an intro line (merge count, PR range, link to this file), the section's own headings,
  one bullet per notable entry at most two lines long (bold title, one clause with the essence or
  the headline number, PR reference) and a compare link as the last line; chores, dependency bumps
  and small fixes stay out, numbers are copied exactly, only PR numbers from the section are
  cited, and the full text lives only here. The v3.1.0 release page was the whole section copied
  — 640 lines. The rule lives in `CLAUDE.md` § "Changelog + releases",
  `.github/copilot-instructions.md`, this file's header and `agentic/commands/release.md` — the
  same rule kurrentschrift adopted on 2026-08-28 (#10810).
- **`open-pr` skill: the post-merge Cloud Build watch names the region** — `gcloud builds
  list` without `--region=europe-west4` answers with months-old global builds (all `SUCCESS`,
  none from today), which reads like "nothing was triggered" while both regional deploys are
  already done; the #10808 follow-through polled that list for 20 minutes. The command now
  carries the region and a `SHORT_SHA` column to match against the merge commit (#10809).
- **`babysit-pipeline`'s gap-backfill guidance corrected against a completed run** — the
  section shipped in #10628 was written mid-backfill and three of its claims did not
  survive the rest of it. The halt-on-cluster threshold counted raw failed runs, but one
  impossible pair now burns three runs on its own retries, so two bad pairs tripped it
  while the pipeline was healthy; it counts distinct `(spec, library)` pairs now. The
  "static library against an interactive or 3D spec is the gap that is usually real"
  gotcha is replaced by its opposite: every category-level prediction made during the
  backfill was wrong — 17 of 20 parked pairs generated fine, and `bar-3d-categorical`
  succeeded in plotnine while `scatter-3d` did not — so a gap counts as real only after
  three attempts under a fresh budget. Added: spec IDs harvested from issue titles must be
  intersected with the actual `plots/` directories (14 of 26 pointed at specs that no
  longer exist), and a `TIMEOUT` with zero recent failures means the failures aged out of
  the driver's window, not that nothing failed. `run_spec.sh` also retries its
  `git fetch`: two drivers polling one checkout collide on the `origin/main` ref lock,
  and a lost fetch made the poller read stale metadata and understate progress (#10660).
- **`babysit-pipeline` learned gap backfill** — closing coverage gaps across the catalogue is
  a different job from watching one fresh spec, and the skill only described the latter. It
  now documents reading the missing set from `plots/*/metadata/` instead of from labels
  (most affected specs have closed issues, so their labels are absent or stale), the
  per-spec `run_spec.sh` driver, two-specs-in-parallel pacing, and the one-retry rule. Four
  new gotchas record traps that cost real implementations during the 2026-08-24 backfill:
  the failure-marker count spanning more than the current run, `impl:<lib>:failed` being
  both terminal and unreliable (42 of 87 sat on implementations that had since landed), the
  intermittent "reports success, writes no file" generation failure, and the one gap shape
  that usually is real — a static library against an interactive or 3D spec (#10628).
- **llms.txt now tells agents how to actually fetch things** — the file linked nine human-facing
  HTML pages and named no machine endpoint. New sections document the REST API (base URL, the
  retrieval endpoints, OpenAPI), the GCS render URL pattern (themes, responsive widths, WebP),
  the CORS-open GitHub raw source URLs, and a worked three-step "fetch one plot" recipe — plus an
  honest note that prerendered page HTML is gated on a crawler user agent while these URLs are
  not. `anyplot.ai/llms-full.txt` is now proxied to the API's generated catalogue index instead
  of soft-404ing to the homepage shell, and the daily monitor asserts it (#10488).
- **The five doc pages carry real content for crawlers** — the bot renderings of
  `/libraries`, `/stats`, `/about`, `/legal` and `/palette` were 29–59-word title+description
  stubs, so a crawler following llms.txt's own link descriptions found none of the promised
  content (AI-access audit 2026-08-19). They now serve the full library registry (derived from
  `core/constants.py`), the live catalogue counts (reusing the cached `/stats` data), the
  pipeline story, the operator/privacy/transparency facts, and the actual palette hex values
  (straight from `core/palette.py`) — each derived from its single source of truth so the pages
  cannot drift (#10491).
- **Dependencies:** 10 Dependabot PRs — `mcp` 1.28.1 → 2.0.0 (#10615), `anthropic` 0.122.0 →
  1.0.0 (#10616), jsdom 29.1.1 → 30.0.1 (#10183), the MUI group (#8820), plus the grouped
  python-minor (#10315, #10614), npm-minor (#10312, #10612) and actions (#10313, #10613) bumps.

### Removed

- **Stray tracked plot renders** — `plots/bar-basic/implementations/python/plot-{dark,light}.png`
  were committed render outputs violating the previews-live-in-GCS rule (flagged by the
  2026-08-17 license audit, removal approved 2026-08-20); the served previews come from GCS and
  are unaffected (#10503).

*Catalog: 302 new implementations across 82 specs — the JavaScript backfill (MUI X Charts 71,
Highcharts 67, D3 47, ECharts 46, Chart.js 45) plus Makie 9, ggplot2 7 and 10 across the Python
libraries; no new specs; 3,704 implementations over 324 specs.*

## [3.1.0] — 2026-08-19 — Legible to machines

anyplot 3.1 makes the catalogue readable by machines. An assistant asked about a plot can now find
it, open one library's page, read the runnable source, fetch the rendered image and cite the URL —
a path that was broken at four separate points, each invisible to anyone browsing the site by hand.
Googlebot had been walking an infinite redirect; a trailing slash sent crawlers to a host that
forbids crawling; unknown library names produced an unbounded supply of indexable near-duplicates;
and seven AI fetchers were served an empty shell. The crawler policy that used to decline training
crawlers is now open to every operator that follows the rules, which is also the only way Gemini
could ever cite the catalogue. Two Plausible sites now separate what people read from what machines
do.

Behind that: a Search Console integration that had never once worked, a synthetic monitor that had
been failing unnoticed for ten days, three new verification skills, and a security-headers and
audit sweep across the stack.

### Added

- **You can now see which assistants read the catalogue** — a `bot_fetch` event records every AI
  and search agent that reads a page, with `assistant` (claude, chatgpt, gemini, mistral, …),
  `path`, and a `kind` that separates the case worth knowing: `user_directed` means a person asked
  their assistant to open the page and is a **reader**, against `index`, `search`, `inspection` and
  `training`, which are machines with nobody waiting. Recorded against a **separate Plausible site**
  (`bots.anyplot.ai`) rather than the main one, because every Plausible event creates a visitor and
  mixing these in would re-introduce the ~40% inflation that audit 2026-07-08 removed. Classic
  search crawlers are included on purpose: per-engine crawl frequency is otherwise only visible by
  sampling Search Console one URL at a time, which is how a months-long recrawl gap went unnoticed.
  Hooked in as a router dependency rather than per handler, so the next endpoint added cannot go
  unrecorded (#10471).

- **Dead URLs are now visible in analytics** — a new `page_not_found` Plausible event fires when a
  visitor reaches a URL the app cannot serve, carrying the requested `path` and a `source` that
  separates the kinds of miss: `catch_all` (matches no route — usually a bad inbound link) from
  `spec_missing` (the route resolved but the content is gone — the pattern a library migration
  leaves behind), plus `language_params` and `route_error`. Instrumented once inside
  `NotFoundPage.tsx`, which covers all four call sites, and read from `window.location` rather than
  router context, because the same component is the fallback inside `RouteErrorBoundary` where that
  context is what may have failed. A fifth source, `impl_missing`, is reported from `SpecPage.tsx`,
  which redirects such visitors to the hub instead of rendering a 404 — without it the event would
  have missed the exact case it was built for, since that silent redirect is what a library
  migration produces. Documented in `docs/reference/plausible.md` (#10453 covers the crawler-facing
  half; bots run no JavaScript, so the two never overlap) (#10465).
- **Search Console API access, documented and reproducible** — `docs/reference/seo.md` gains a
  "Search Console API access" section: the domain property (`sc-domain:anyplot.ai`), the
  Application Default Credentials login that carries the `webmasters.readonly` scope, a
  verification snippet, and the two failure modes that otherwise cost a session — the gcloud CLI
  token can never hold the scope, and the localhost callback flow dies with `missing_code` on
  WSL2 before you finish the consent screen. Machine-specific values move to `.env`
  (`SEARCH_CONSOLE_PROPERTY`, `SEARCH_CONSOLE_ACCOUNT`, documented in `.env.example`), so a
  second machine is one login away from full-mode audits (#10452).

- **Three new verification skills** — `/verify-migrations` runs the Alembic chain against a
  throwaway Postgres (Docker, or a rootless `pgserver` fallback; single-head check,
  `upgrade head`, `alembic check` drift, downgrade roundtrip) so the shared prod DB never sees
  an untested revision — no CI job covers this at PR time, and with no `DATABASE_URL` exported
  alembic silently falls back to the `.env` connection, which in this repo's local-dev setup is
  the shared production DB; `/audit-licenses` sweeps tracked binaries, hidden base64/SVG payloads, git
  history, and font bundling for provenance violations (first run recorded a verified baseline
  and flagged `plots/bar-basic`'s two tracked plot renders as a known wart); `/write-docs` is
  the docs editing contract (layer choice, `docs/index.md` sync surfaces, cross-file sync
  duties). All three are wired into the CLAUDE.md skill-routing table and the `/open-pr` gates
  (#10316).
- **AI crawler policy, written down and served** — `app/public/robots.txt` now states the whole
  policy itself (content signals incl. the Art. 4 EU-DSM training reservation, the welcomed
  retrieval/citation agents, the declined training collectors), so it holds with or without
  Cloudflare's managed block; `app/nginx.conf` routes `Claude*`, `GPTBot`, `OAI-SearchBot`,
  `ChatGPT-User` and `Perplexity*` to the prerendered seo-proxy pages like the search engines
  (they run no JavaScript and were being served the empty SPA shell); the daily
  `bot-serving-check` now covers an AI UA and `llms.txt` under an AI UA. `docs/reference/seo.md`
  documents the decision, the measured edge behaviour and the Cloudflare steps that lift the
  403 (#9898, decision #9633).
- **`CODE_OF_CONDUCT.md`** — Contributor Covenant 2.1, linked from `docs/contributing.md`
  (closes the last repo-health gap from audit 2026-07-15 Medium#29) (#9644).
- **Bot-served pages got a real SEO surface** — `seo_home()` now emits the site-level JSON-LD
  (`WebApplication`, `WebSite`+`SearchAction`, `Organization`) that previously only lived in the
  SPA shell nginx never serves to bots, plus a descriptive title/meta and real body copy;
  `/seo-proxy/plots` and `/seo-proxy/specs` render a server-side link to every spec hub, so
  crawlers can reach all 324 hubs (they were orphans); `Google-InspectionTool`/`GoogleOther`
  UAs are now routed to the bot pages like Googlebot (audit 2026-07-15 High#10/#11,
  Medium#40/#41) (#9642).
- **`core/palette.py` unit tests** — the last untested core module now has coverage: pool
  contract, semantic anchors, theme-adaptive neutrals, lazy cmaps and the
  matplotlib-free-import guarantee (audit 2026-07-15 Medium#28) (#9642).
- **Impl check constraints exist as a migration** — `ck_quality_score_range` /
  `ck_review_verdict_valid` lived only in the ORM; a new alembic migration adds them (with
  pre-normalization of violating rows and a real downgrade) (audit 2026-07-15 Medium#18) (#9642).
- **Repo health:** PR template with changelog/docs checklist and an `.editorconfig` mirroring
  ruff + frontend conventions (audit 2026-07-15 Medium#29) (#9642).
- **Full 2026-07-15 codebase audit report** — persisted output of a 16-auditor `/audit` run
  with domain-routed cross-validation (`agentic/audits/2026-07-15-all.md`, mirrored to
  `latest.md`). Health Score 30/100 with correctness (C, 60) as the weak pillar; headlines are a
  live `heatmap-calendar` retry loop (#1010), 15-library pipeline/config drift, dark-mode
  white-surface leaks, and 97 reviewer-rejected implementations live on main, plus an open-issue
  triage with a recommended work queue. Report only, no source changes (#9641).
- **`llms.txt` for AI agents** — `/llms.txt` previously fell through to the SPA shell (flagged
  by Lighthouse's Agentic Browsing audit as non-conformant); now a spec-conformant file per
  llmstxt.org (H1 + summary blockquote + H2 link sections) covering catalog, docs, the MCP
  endpoint and the repo, served directly in nginx like robots.txt so mapped crawler UAs aren't
  proxied into a `/seo-proxy/llms.txt` 404 (#9618).
- **`bot-serving-check.yml` synthetic monitor** — daily scheduled workflow that curls the
  Cloud Run origin with Googlebot/Twitterbot UAs plus a human-UA control (and an `llms.txt`
  check) and fails on non-200 or missing per-route titles, so the crawler-only serving path can
  never break silently again. Targets the origin because Cloudflare's bot management 403s
  GitHub-runner IPs (#9617, #9619).
- **Product/UX audit 2026-07-08** (`agentic/audits/2026-07-08-product-ux.md`) — 8-auditor
  workflow run scoped to pipeline, rating criteria, tabs, and product qualities; Health Score 43,
  headlined by a critical crawler outage (every bot UA gets 502 from the `@seo_proxy` hop) and
  quality-score calibration drift (#9616).
- **Legal page "other projects" block** — below the disclaimer, cross-linking the maintainer's
  other projects kurrentschrift.ink and cite-citadel, tracked as `external_link` with
  destinations `kurrentschrift` / `cite_citadel`; deliberately without `noreferrer` so the
  target sites' analytics can attribute the traffic (#9616).

- **Project skill layer under `.claude/skills/`** — six skills, ported from the kurrentschrift
  and cite-citadel setups and adapted to anyplot: `verify-frontend` (browser-drive changed flows,
  both viewports × both themes, cloud playwright-core fallback probe), `verify-api` (read sweep +
  shared-prod-DB discipline), `verify-core` (pytest/ruff/mypy gates + registry smoke), `open-pr`
  (gates → PR → CI watch → review-thread resolution with runnable GraphQL recipes),
  `optimize-skills` (session-transcript retro mining), and `babysit-pipeline` (bulk-generate
  monitoring with the battle-tested poller scripts promoted from gitignored local state).
  CLAUDE.md gained a Self-Verification routing table wiring diff paths to the skills (#9615).
- **`/dependabot` and `/catalog-status` commands** — batch-processing of Dependabot PRs with the
  GITHUB_TOKEN/auto-merge gotchas encoded, and a reproducible catalog-status report (light/dark
  migration counts, per-spec library coverage, open impl-PR classification). Both derived from a
  13-session transcript retro; the same retro added working rules to CLAUDE.md (explicit
  authorization for external writes, proactive progress reporting, absolute-path discipline)
  (#9615).
- **`CHANGELOG.md` introduced, with the v1.0.0–v3.0.0 history backfilled** from the GitHub
  releases. The per-PR changelog contract is wired into `CLAUDE.md`,
  `.github/copilot-instructions.md`, and `/pull_request`; a new `/release` command
  (`agentic/commands/release.md`) codifies the version-bump → tag → GitHub-release flow (#9614).
- **Design-sync inputs for the anyplot.ai Design System.** `.design-sync/` carries the app-shape
  sync inputs so the Design System on claude.ai/design can be synced from `app/` via
  `/design-sync`; MonoLisa is fetched from GCS and never committed (#9213).

### Changed

- **Implementation pages now show the plot, not the card it sits inside** — the bot page's only
  image was the 1200×630 `og:image`, in which the render is a thumbnail surrounded by branding
  chrome with its cell labels barely legible. Right for a shared link, useless to an assistant asked
  to show the plot. The body now carries the actual render as a `<picture>` with both themes, using
  the `_400`/`_800`/`_1200` derivatives the pipeline already writes beside every plot, whose suffix
  is the true pixel width. The full-size original stays out of the `srcset` — its width varies per
  plot (2400, 3200, 4766 among those measured), so it has no honest `w` descriptor — and gets its
  own link; `src` points at the 1200px variant so a consumer ignoring `srcset` does not pull a
  five-megapixel file. `og:image` is unchanged, and attribution is not lost either way: every
  render's title reads `{spec} · {language} · {library} · anyplot.ai`. Below it, a list names every
  asset in words — a `<picture>` tells a browser which file to take but tells a reader nothing about
  which is which — including the **interactive version**, which exists for 2,229 of 3,583
  implementations, is publicly fetchable, and was mentioned nowhere machine-readable before.

- **`og_image_view` is split by who fetched the image** — a social or messenger preview means a
  human shared a link, which is a product signal and stays on the main site; a search or AI crawler
  fetching the same image is not a share and now goes to `bots.anyplot.ai`. The distinction matters
  from now on rather than in principle: `robots.txt` only began permitting `/og/` in the same
  release, so crawler fetches of the 3,913 preview images would otherwise have arrived in volume on
  the main site, drowning the sharing signal and inflating visitor counts. Machine-side events carry
  the same `assistant` and `kind` props as `bot_fetch`, so both slice alike (#10475).
- **The crawler policy is open to every operator** — retrieval, citation, search indexing and model
  training are now permitted for all of them, replacing the retrieval-yes / training-no split from
  #9633. That split was never coherent for an MIT-licensed catalogue published to be reused:
  declining a training crawler protected nothing the licence had not already granted, while costing
  reach. It also had an unintended consequence — Google's `Google-Extended` token governs Gemini
  **grounding and training together**, with no finer control, so declining it kept anyplot out of
  Gemini's answers entirely. The `Content-Signal` line moves to `ai-train=yes` and the Article 4
  reservation is gone rather than left contradicting the licence beside it. `Bytespider` remains
  declined on bandwidth grounds, not principle: it is documented as ignoring robots.txt and crawling
  far harder than this catalogue can justify serving. Verified against Python's `urllib.robotparser`
  across eleven agent/path pairs. **Requires a Cloudflare dashboard change to take effect** — the
  edge still 403s GPTBot, CCBot, Amazonbot, meta-externalagent and Google-CloudVertexBot, and a
  permission the edge blocks is a published lie (#10474).

- **Repository prose now follows the Google developer documentation style guide** — the
  `write-docs` skill gains a "Writing style" section anchoring
  [Google style](https://developers.google.com/style) as the baseline for `docs/`, `README.md`,
  `agentic/docs/`, changelog entries, and PR/issue text (second person, sentence-case headings,
  numbered procedures, no emoji in headings, no "just/easy/simply"), with
  `docs/reference/style-guide.md` staying the exempt authority for website/brand surfaces (its
  new scope note documents the boundary); `CLAUDE.md` and `.github/copilot-instructions.md`
  carry the rule in sync. A cleanup pass applies the cheap fixes across the doc corpus —
  Title Case headings to sentence case, emoji and status glyphs out of headings, banned
  filler words, README exclamation-mark tone — while procedure restructuring and remaining
  deviations migrate on touch (#10363).
- **Working guardrails adopted from sibling projects into `CLAUDE.md`** — delegated agents
  default to `model: opus` (Fable only for hard reasoning, Sonnet/Haiku for mechanical work,
  with an explicit decide-and-document vs. return-as-finding split); secret values are never
  echoed into transcripts; destructive prod operations require a sanity-checked snapshot first;
  the named-authorization rule now covers Cloud SQL/GCS/Secret Manager/Cloud Build actions;
  manual user-only steps get filed as tasks in the Todoist project "Anyplot"; structural fixes
  beat symptomatic ones (incl. never bending working code to a broken test); repo files are
  modified via Edit/Write tools only in interactive sessions; PR follow-through gains the
  merge-race rule (hold pushes after "green and review-clean", recover via fresh branch +
  cherry-pick); and `CLAUDE.md` ↔ `.github/copilot-instructions.md` carry a general
  keep-in-sync duty (#10316).
- **`/open-pr` works in cloud sessions** — a new §0 detects `gh` vs. GitHub MCP tooling and
  maps every PR/CI/review step to its `mcp__github__*` equivalent (subscribe instead of
  polling; the Cloud Build deploy watch stays local-only); the gates table now routes
  `alembic/` diffs to `/verify-migrations` and `docs/` diffs to `/write-docs` (#10316).
- **`docs/workflows/report-issue.md` is indexed** — the doc existed but was missing from all
  three `docs/index.md` surfaces (Quick Links, structure tree, layer section); found by the new
  `/write-docs` drift check (#10316).
- **Hot listing paths stop fetching every code blob** — MCP `list_specs` /
  `search_specs_by_tags` and `/libraries/{id}/images` used `get_all_with_code()`, dragging the
  full multi-MB code corpus through the DB per request; the MCP tools now resolve code
  *presence* via a lightweight id probe (`get_ids_with_code`) and the images endpoint fetches
  only its own library's code (`get_by_library_with_code`); the now-unused `get_all_with_code()`
  was removed (audit 2026-07-15 Medium#5, issue #7696) (#9644).
- **Frontend a11y pass** — card actions reveal on `:focus-within` and stay visible on touch
  devices instead of hover-only; the NavBar search button and nav links have `:focus-visible`
  outlines; mobile nav/theme-toggle tap targets reach 44px; off-palette Tailwind green and a
  rogue Python-blue were replaced with imprint palette hues; `AppDataProvider`/theme context
  values are memoized so consumers stop re-rendering every frame (audit 2026-07-15
  Medium#7/#10/#11/#12).
- **Frontend production image builds on `node:22-alpine`** — `node:20` is EOL April 2026; 22
  matches the JS render harness (audit 2026-07-15 Medium#16) (#9642).
- **Spec-detail tabs are self-explanatory now** — the Code tab (Spec tab on hub pages) starts
  open instead of everything collapsed, the selected tab shows a small caret signaling the
  click-to-collapse toggle, the quality tab reads "Quality 91" (with an explanatory
  `aria-label`) instead of a bare number, and tabs↔panels got standard `id`/`aria-controls`
  wiring (audit 2026-07-08 High#5 + Low#1) (#9622).
- **Bot-served pages now carry the site's actual content** — the crawler-facing HTML
  (`/seo-proxy/*`, what Googlebot & social bots see) grows from a title+description shell to a
  real document: spec hubs list and link every implementation, implementation pages embed the
  full source in a `<pre>` block plus hub/sibling links, both carry the preview image and
  JSON-LD (`BreadcrumbList`, `ItemList`, `SoftwareSourceCode`), and every bot page ends with a
  site-wide nav. Display names derive from `core/constants.py`, never hand-maintained (audit
  2026-07-08 High#6) (#9621).
- **Gallery cold path prewarmed** — the startup cache prewarm now also computes the two
  heaviest user-facing payloads, `/plots/filter` (`filter:all`) and `/specs/map`, so the first
  visitor of a fresh Cloud Run instance no longer waits on the full DB roundtrip for the
  gallery or the map page (audit 2026-07-08 Quick Win 2) (#9620).
- **ECharts upgraded 5.5.1 → 6.1.0** — major bump of a rendered charting library; echarts
  previews regenerate against the new major through the regular pipeline (#9609).
- **Post-restructure `app/` cleanup:** dead components removed and stale doc paths fixed (#8630);
  ECharts / MUI X labels shortened in the `/stats` library list (#8666).
- **Dependencies:** 32 grouped bumps across Python (starlette, cryptography, python-multipart,
  sqlalchemy, uvicorn, pydantic, the python-minor group), npm (esbuild, undici, vite, react, the
  npm-minor and mui groups) and GitHub Actions (#8330, #8668, #8823, #8824, #8864, #8977, #8978,
  #8979, #8980, #9074, #9513, #9515, #9613, #9640, #9643, #9647, #9648, #9650, #9652, #9653, #9654,
  #9657, #9673, #9674, #9955, #9957, #9960, #9961, #9962, #10017, #10067, #10115, #10178). One of
  them, the vite 8.1.5 bump in #9657, took the site down and is written up under Fixed.

### Removed

- **Catalog curation: 13 interactive-first specs removed** — plot types whose value is inherently
  interactive don't fit a static-first catalog (#8645).

### Fixed

- **The sitemap was telling Google nothing had changed** — `lastmod` came from an implementation's
  `updated` column, which does not move when the page's *rendering* changes. So after a day of work
  that gave every implementation page the real render, both themes, the interactive version and a
  rewritten description, the sitemap still reported the old dates, and Google — last seen fetching
  some of those pages three weeks earlier — had no reason to return. `lastmod` is now the later of
  the record's date and `TEMPLATE_LAST_CHANGED`, a constant to bump only when the rendered page
  changes for every URL; claiming 3,900 changes casually is how a site teaches Google to ignore its
  `lastmod` (#10483).

- **CodeQL alert #103** — an ECharts tooltip called `.replace("\n", " ")` with a string argument,
  which replaces only the first occurrence
  (`plots/bar-heart-rate-zones/implementations/javascript/echarts.js`). Nothing renders differently
  today, since every zone label carries exactly one newline; the defect is latent, and a label
  gaining a second line break would put a raw newline inside the tooltip's HTML. The pattern occurs
  exactly once across the catalogue — were it recurring it would belong in the generation prompt,
  since `plots/` is pipeline output and a regeneration overwrites this file (#10480).

- **A database outage would have reopened the hole #10453 closed** — with no catalogue to check
  against, the bot routes answered 200 with a fabricated page for any string, self-canonicalising,
  exactly the defect that PR removed. Degraded pages now carry `noindex`. The path is unreachable in
  production, where the database is configured, but it is one misconfiguration away from indexable.
  `bot_fetch` also moved from a router dependency to a middleware and gained a `status` property: a
  dependency runs before the handler and cannot see the response, so every 404 was being recorded as
  a successful page read (#10479).

- **Documentation that still described the superseded crawler policy** — `docs/reference/seo.md`
  said `gptbot`, `meta-externalagent` and `amazonbot` were "declined in robots.txt" and
  `app/nginx.conf` carried the same claim in a comment. Both were written about an hour before
  #10474 opened the policy and never reconciled, so the page contradicted itself. The measured
  edge-state table was stale for the opposite reason: the dashboard unblock it prescribed had since
  been done. A docstring also pointed at `app/src/router.tsx`, which does not exist — the routing
  lives in `app/src/routes/index.tsx` (#10479).
- **The bot analytics recorded nothing at all** — Plausible identifies crawler user agents and
  discards their events, so forwarding the real one guaranteed an empty dashboard. Verified against
  the live API: the same event sent as `Claude-User` never appears, sent as a browser agent it does,
  and both are acknowledged with `202 ok` — Plausible always accepts, then drops. There is no
  documented bypass, so machine-side events now travel under a neutral agent; nothing is lost,
  because the user agent only feeds browser/OS detection, which is meaningless for a crawler, while
  the identity rides in the `assistant` and `kind` properties. A second silent drop was found in the
  same pass: the [Events API docs](https://plausible.io/docs/events-api) state that forwarding an
  infrastructure address rather than the visitor's makes Plausible discard the event, and analytics
  was reusing the rate limiter's IP resolver — which deliberately returns the *rightmost* forwarded
  entry, ours. Analytics now has its own `visitor_ip`, and `api/request_context.py` records why the
  two must not be merged (#10477).
- **The daily bot-serving monitor had been red for ten days** — it greps for an exact home-page
  title, the copy changed to "anyplot.ai — AI-generated plot catalog for 15 libraries", and every
  scheduled run since 2026-08-09 failed on that one line. Nothing else was wrong, and nobody looked:
  this run of SEO work edited the workflow twice and cited it repeatedly as the regression cover for
  changes that have no local verification loop, while it was failing daily. It now matches on the
  prefix, which still separates the prerendered page from the SPA shell — the property actually
  under test — and no longer breaks on copy. The trailing-slash check also no longer passes when
  there is no redirect at all: an empty `%{redirect_url}` printed "OK" and returned success, which
  Copilot raised on two separate PRs (#10478).

- **The trailing-slash redirect leaked the internal port** — #10473 removed a redirect to
  `http://api.anyplot.ai/seo-proxy/…` and replaced it with `http://anyplot.ai:8080/…`: a smaller
  version of the same defect, since nginx builds a `permanent` rewrite's Location from
  `$scheme://$host:$server_port`, and behind Cloud Run that is plain http on port 8080.
  `absolute_redirect off` makes the Location relative, which the client resolves against the URL it
  actually requested — the only value here guaranteed to be right. The daily `bot-serving-check`
  would have caught this on its next run, since it already rejects an `http://` target; it now
  rejects an internal port explicitly too. `agentic/docs/project-guide.md` also gains the step that
  makes this checkable at all: the deploy triggers are **regional** (`europe-west4`), so a
  `gcloud builds list` without `--region` returns builds from early 2026 and reads as "nothing has
  deployed for months" — a wrong conclusion drawn in this session and corrected by the repo owner
  (#10476).

- **Preview images were forbidden to every crawler that follows the rules** — `api.anyplot.ai`
  served a blanket `Disallow: /`, while every prerendered page references its preview image at
  `api.anyplot.ai/og/…png`. The image answered HTTP 200 and the host forbade fetching it, so an
  assistant asked to show a plot could read the code and not the picture, and Google Images could
  index none of the 3,913 previews. Link-preview bots were unaffected either way — they do not
  consult robots.txt, which is why this went unnoticed. `/og/` is now allowed, with `Allow` placed
  before `Disallow` so first-match parsers see the exception; verified against Python's
  `urllib.robotparser`, which is exactly such a parser (#10472).

- **The SEO proxy no longer invents pages** — `/{spec}/{language}/{library}` served HTTP 200 with
  a self-referencing canonical for *any* language and library string, because neither segment is
  validated against a vocabulary: `/bar-basic/klingon/matplotlib` and
  `/bar-basic/python/erfundenelib` were both indexable pages. That is an unbounded supply of thin
  near-duplicates competing with the 3,913 real URLs for the same crawl budget, and it is why 161
  URLs from the highcharts Python→JS migration (#8516) were still indexed months after those
  implementations were deleted. Unknown combinations now return 404, and the 404 is not cached so
  a later regen becomes visible immediately. The stale URLs are dropped rather than redirected:
  measured over 28 days they carry 4.4% of impressions and 10 clicks in total (#10453).
- **A trailing slash sent crawlers to a crawl-blocked URL** — `/box-basic/` answered `307` to
  `http://api.anyplot.ai/seo-proxy/box-basic`: the internal proxy path, on the API host, over plain
  http, and that host's `robots.txt` disallows everything. FastAPI's `redirect_slashes` built the
  Location from the *proxied* request, and `@seo_proxy` set no `X-Forwarded-Proto`, so the scheme
  came out wrong too. Humans never saw it — only bots take the proxy path — and every inbound link
  written with a trailing slash, which is common, dead-ended there; some of the 48 Search Console
  "Redirect error" URLs came from this. nginx now normalises the trailing slash to the canonical URL
  before any routing, the proxy declares the scheme, and `bot-serving-check` fails if a
  trailing-slash redirect ever again points at `/seo-proxy` or downgrades to http (#10473).

- **AI assistants asked about a plot page saw nothing** — seven user-directed fetchers (eight UA
  patterns; NotebookLM and Mariner each answer to two) were absent from the `$is_bot` map in
  `app/nginx.conf` and received the empty SPA shell instead of the prerendered page: `Google-GeminiNotebook`, `Google-NotebookLM`, `Gemini-Deep-Research`,
  `GoogleAgent-Mariner`, `Meta-ExternalFetcher`, `MistralAI-User` and `DuckAssistBot`, each
  verified live against the site before the fix. The map now also carries the vendor-documented
  retrieval agents that were never listed (`MistralAI-Index`, `Amzn-SearchBot`, `Amzn-User`,
  `Meta-WebIndexer`) and, as best-effort, the community-reported ones (`GrokBot`, `xAI-Grok`,
  `Grok-DeepSearch`, `YouBot`, `cohere-ai`) — mapping is not permission, so over-listing costs
  nothing while under-listing is what caused this. These arrive because a human asked their
  assistant to open a page, and Google documents its own as generally ignoring robots.txt — so
  this map, not the crawler policy, is the only control point for them. The daily
  `bot-serving-check` now covers all of them, since the failure is invisible to every human
  visitor and would otherwise regress unnoticed (#10470).

- **Home-page filter params were self-canonicalising** — the bot page built its canonical from the
  request query string, so `/?spec=point-basic` declared itself a page in its own right rather than
  a view of the home page, and Search Console had it indexed as one (last crawled 2026-05-26). Every
  filter combination was a candidate. The canonical and `og:url` are now always `https://anyplot.ai/`;
  `og:image` and `og:url` still carry them: neither is a canonicalisation signal, and `og:url` is
  where a shared card sends its reader, so dropping it there would land every shared filter link on
  the bare home page and defeat the tracking the params exist for. The bot template's `og:url` and
  `canonical` slots, previously one value, are now separate — defaulting to identical, so every
  other handler is unchanged. Verified that `?view=` and `?language=` on implementation and hub
  pages were already correct. Verified that `?view=` and `?language=` on implementation and
  hub pages were already correct (#10462).
- **Meta descriptions were three times too long to survive a search result** — every prerendered
  page passed the full spec description straight into `<meta name="description">`. Measured across
  40 live pages: median 424 characters, longest 801, and all 40 over Google's ~155-character
  truncation point, so the sentence that decides the click was never the one being written. The
  2026-05-05 audit recorded this and it had not moved since. The meta and OG tags now carry a trim
  that ends on the last full sentence that fits (falling back to a word boundary), taking the same
  sample to a median of 142 with none over the limit. Visible body copy and JSON-LD keep the full
  description — the trim is for the snippet, not the content — and it runs on the raw text before
  escaping, so it can never cut through an HTML entity (#10458).
- **Googlebot was walking an infinite redirect on every `/{spec}/{language}` URL** — the handler
  answered `Location: /seo-proxy/{spec}`, its own internal path. nginx serves crawlers by
  prepending `/seo-proxy` to the request URI, so the bot fetched `anyplot.ai/seo-proxy/{spec}`,
  which arrived as `/seo-proxy/seo-proxy/{spec}` and re-matched the same route with
  `spec_id="seo-proxy"` — redirecting again, forever. `curl -A Googlebot` gives up after 50 hops
  at `anyplot.ai/seo-proxy/seo-proxy`; a normal user agent never saw it, because only bots take
  the proxy path. Search Console recorded it as 48 URLs under **Redirect error**. The Location is
  now the public URL, and a regression test asserts both that it never starts with `/seo-proxy`
  and that re-entering with the prefix nginx adds resolves instead of bouncing (#10455).
- **`seo-auditor` could never reach Search Console** — its auth contract probed
  `gcloud auth print-access-token`, which mints the gcloud CLI credential; that credential's
  scope set is fixed and can never include `webmasters.readonly`, so every audit since the
  command was written reported `Search Console mode: structural-only` (2026-04-26, 2026-05-05,
  2026-07-08). It now probes Application Default Credentials. The same contract also forbade
  every non-`GET` call while asking for query data — Search Analytics is a `POST` — so the
  auditor was told to collect data it was simultaneously barred from fetching; read-ness is now
  anchored to the `webmasters.readonly` scope rather than the HTTP verb, which additionally
  unlocks `urlInspection`. Its Coverage guidance no longer asks for the page-indexing report
  buckets, which have no API at all (#10452).

- **Model↔migration index drift fixed before it could drop production indexes** — seven
  migration-created indexes (`ix_specs_issue`, `ix_specs_tags` GIN, `ix_impls_library_id`,
  `ix_impls_quality_score`, `ix_impls_impl_tags` GIN, `ix_feedback_created_at` DESC,
  `ix_feedback_ip_hash_created_at`) were never declared on the ORM models, so any future
  `alembic revision --autogenerate` would have proposed dropping them; found by the first
  `/verify-migrations` run (`alembic check`), the models now declare all seven (#10316).
- **Plot of the day now respects dark mode** — the landing-page terminal card always showed the
  light preview image because `GET /insights/plot-of-the-day` only returned the legacy
  `preview_url` (a synonym for the light variant); the response now carries
  `preview_url_light` / `preview_url_dark`, so the already theme-aware frontend picks the dark
  render automatically (user bug report, in German, on `/roc-curve/python/altair`) (#10308).
- **A correctly rejected plot was reported as a crashed review, deadlocking the PR** —
  `impl-review.yml` used quality score `0` as its sentinel for "the AI review produced no
  output", but `0` is also a score the review prompt *mandates*: the Stage 1 auto-reject gates
  (`AR-08` clipped element, `AR-09` mandatory title not visible) require exactly
  "Score = 0, verdict = REJECTED". Every plot that tripped those gates therefore hit
  `Validate review output` → `::error::AI Review did not produce valid output files` →
  `ai-review-failed` → `exit 1`, which skipped the verdict step — the pipeline's *only*
  hand-off point — so `impl-repair` was never dispatched and the missing title was never fixed.
  The retry listener rescued once, the re-review scored `0` again (deterministically: the plot
  was unchanged), and the resulting `ai-review-failed` + `ai-review-rescued` pair matches no
  watchdog case, stranding the PR for good. Six PRs sat in exactly that state (#10152, #10130,
  #10009, #10003, #9968, #9776), all with an `AR-09` verdict in hand. Output presence is now
  tracked as its own `has_output` step output, so a score of `0` flows into the normal
  rejected → repair path and only genuinely absent output raises `ai-review-failed`. The
  comment fallback also now reads the last **`claude[bot]`** comment posted by the *current* run,
  instead of the last comment overall — on a retry the bot's own "auto-retrying" notice landed
  last and shadowed the score, while an unscoped author filter would have reused a previous
  attempt's score (#9948 still shows `Score: 89/100` from its first review). Verified with a
  harness that extracts the step body verbatim from the YAML and exercises 17 cases (score 0 via
  file and via comment fallback, stale-score reuse, normal scores, and the five genuine
  no-output shapes) (#10179).
- **CI lint went red on every PR after a ruff minor bump** — `pyproject.toml` pins
  `ruff>=0.15.21` without an upper bound, CI resolved **0.16.0**, and that version started
  formatting Python code blocks inside Markdown: 20 tracked `.md` files suddenly "would be
  reformatted", none of them touched by the PR that hit it. Ruff's exclude list now carries
  `*.md`. Deliberately not fixed by reformatting those files — nine of them are
  `prompts/library/*.md`, whose snippets steer code generation, so rewriting quote style there
  is a pipeline change wearing a formatting costume. Verified against both 0.15.21 and 0.16.0
  (`format --check` + `check` clean on 148 files) (#9899).
- **A GitHub API brown-out could strand implementation PRs permanently — the hand-off calls
  are now retried** — on 2026-07-24 (~16:05–16:26 UTC) GitHub returned HTTP 502 on the
  workflow-dispatch endpoint and HTTP 504 on GraphQL, and four `radar-basic` PRs fell out of
  the pipeline: #9742 was already `ai-approved` but `impl-merge`'s condition check died on a
  `gh pr view` (so it never merged), and #9744/#9749/#9751 were `ai-rejected` but their
  `impl-repair` dispatch never landed. `impl-review`'s verdict step is the pipeline's only
  hand-off point — every downstream workflow starts from a call made there — so an unretried
  blip did not merely fail a step, it left a PR with a verdict label and nothing listening.
  All API calls in that step and in `impl-merge`'s condition check now retry 3× with linear
  backoff, and the repair dispatch is issued *before* the attempt label so a label problem can
  never suppress it. If the dispatch still exhausts its retries, the step now drops the
  `ai-rejected` label on the way out: `ai-rejected` + `ai-attempt-N` matches no watchdog case,
  whereas the label-less state is exactly Case 2, which re-dispatches the repair at the right
  attempt number (#9772).
- **The 4th repair attempt was silently dead — `ai-attempt-4` never existed as a label** — the
  attempt label is what encodes the cascading review threshold (90 → 80 → 70 → 60 → 50), but
  the repo only ever had `ai-attempt-1..3`, so on the 4th repair the add failed every time and
  was swallowed by `|| true` (PRs #7268/#7039 reached "Repair Attempt 4/4" carrying only
  `ai-attempt-1..3`). Every 4th review therefore re-applied the ≥ 90 attempt-0 bar, and the
  "all attempts exhausted" branch — which closes the PR and removes the stale implementation —
  could never be reached. The label is now created on demand (#9772).
- **A merged implementation PR could end up with none of its bookkeeping** — `impl-merge`'s
  5× merge retry re-invoked `gh pr merge` without re-reading state, so a merge that succeeded
  server-side but lost its HTTP response failed four more times with "already merged" and then
  exited 1. All post-merge steps are gated on `should_run == 'true'` (implicit `success()`), so
  GCS promotion, the `impl:{lib}:done` label, closing the issue and the Postgres sync were all
  skipped on an already-merged PR — the silent partial completion CLAUDE.md warns about. The
  loop now checks for `MERGED` first and continues to the post-merge steps (#9772).
- **Dependabot PRs could never merge while the plot pipeline was running** —
  `auto-update-pr-branches.yml` called `update-branch` on Dependabot PRs too, but that push is
  authored by `github-actions[bot]` and GitHub gates every workflow run it triggers behind
  manual approval (`action_required`). Because `main` advances every few minutes while impl PRs
  merge, each branch was re-updated long before anyone could approve, so CI never completed and
  auto-merge never fired: PR #9674 accumulated 174 runs in 22 h — 162 `action_required` against
  only 4 green (the original `dependabot[bot]` push). Dependabot branches are now skipped.
  They merge fine while behind (the `main` ruleset is not strict — the file's header claimed
  otherwise and has been corrected). An already-updated branch needs its gated run approved
  once; that now sticks, because nothing pushes to the branch again. `/dependabot`'s playbook
  told operators to run that same harmful `update-branch` by hand and now says the opposite
  (#9772).
- **anyplot.ai white-screen outage (2026-07-23, ~22:15–23:00 UTC): vite pinned back to
  8.0.16** — the npm-minor Dependabot group (#9657) bumped vite 8.0.16 → 8.1.5, whose rolldown
  1.1.5 bundler emits a broken `mui`/`@emotion` chunk under our `manualChunks` split; the
  deployed app died at chunk init (`TypeError: t is not a function`) into a blank page while
  every HTTP check stayed 200 and all CI stayed green (jsdom tests never execute the built
  bundle). Bisect across builds pinned it byte-exactly: with vite 8.0.16 the mui chunk hash
  reverts to the known-good build's. Dependabot now ignores vite minor/major bumps until the
  upstream codegen issue is verified fixed in a real browser.
- **Scheduled implementation regeneration is harder to starve silently** — `daily-regen.yml`'s
  cron had gone silent for multi-day stretches (a mix of GitHub's documented top-of-hour
  scheduler overload and the workflow being manually disabled), and because every run that did
  start was green, nothing alarmed. The cron now fires at :17 instead of :00, and
  `watchdog-stuck-jobs.yml` gained a cron-liveness rescue that re-dispatches daily-regen
  whenever main has seen no new run created for >10 h outside the Berlin-evening quiet window
  (a manually disabled workflow stays disabled — the rescue cannot and does not re-enable it),
  capping scheduler-side starvation at typically ~half a day instead of weeks (#9649).
- **The whole Claude pipeline generates again — CI runs pass the repo's permission allowlist
  explicitly** — since the July 5 `claude-code-action` bump (bundled CLI 2.1.170 → 2.1.195, by
  now 2.1.211), Claude Code ignores `permissions.allow` from a committed `.claude/settings.json`
  in untrusted workspaces, and a CI checkout is never trusted; every impl-generate/repair, spec-create, polish and similarity run
  had its Write/Edit/Bash calls silently denied (19–20 denials per run, zero files produced,
  zero implementations generated repo-wide since July 1). All 12 `claude-code-action` steps now
  pass `--settings .claude/settings.json` in `claude_args`, which the trust gate honors as an
  explicit opt-in (#9651).
- **Metadata step no longer executes a comment as a command** — a backtick-quoted fragment
  inside the double-quoted Python heredoc of impl-generate's "Create library metadata file"
  step was command-substituted by bash (`--model: command not found` in every run log); the
  comment now uses single quotes (#9651).
- **Tag search uses the GIN index and stops treating `%`/`_` as wildcards** —
  `SpecRepository.search_by_tags` cast the JSONB `tags` column to text and ran LIKE, which the
  `ix_specs_tags` GIN index can never serve (sequential scan on every MCP tag search) and which
  let LIKE metacharacters in tag values wildcard-match; on PostgreSQL it now emits per-category
  JSONB containment (`tags @> …`), and the SQLite test fallback escapes LIKE metacharacters
  (audit 2026-07-15 Medium#17) (#9644).
- **Feedback rate limiting no longer trusts a spoofable header entry** — `/feedback` keyed its
  per-IP rate limit and duplicate suppression on the client-controlled *first* `x-forwarded-for`
  entry, so a caller could evade the limit or poison another user's bucket; it now prefers
  Cloudflare's `cf-connecting-ip` and otherwise uses the rightmost, infrastructure-appended
  entry (audit 2026-07-15 Medium#20) (#9644).
- **Runaway impl-generate retry loop can no longer self-amplify** — the 3-attempt cap counted
  prior failures by paginating issue comments and fell back to "0 failures" whenever the count
  API call rate-limited, so every failure re-dispatched forever (issue #1010 flooded ~1,200
  Actions runs in 38h). The counter now fails closed (an unreadable count = cap reached, no
  auto-retry) and correctly sums per-page counts on issues with >100 comments (audit 2026-07-15
  Critical#1).
- **`spec-create.yml` PR/issue bodies show real content again** — three quoted heredocs
  (`<<'EOF'`) never expanded variables, shipping literal `$SPEC_CONTENT` into PR bodies; bodies
  are now built via unquoted heredocs (literal backticks escaped so no command substitution)
  and passed with `--body-file`. The post-merge comment also lists all 15 generate labels
  (audit 2026-07-15 High#3) (#9642).
- **`impl-merge.yml` no longer closes issues early** — the auto-close step read a stale
  hardcoded 11-library list while 4 JS libraries were still pending; it now derives the list
  from `core/constants.py` `SUPPORTED_LIBRARIES` at run time (audit 2026-07-15 High#4) (#9642).
- **Local evaluator accepts what the pipeline actually emits** — `scripts/evaluate-plot.py`
  looked for `plot.png` while implementations emit `plot-{light,dark}.png`, auto-rejecting
  every compliant impl; it is now theme-aware via `ANYPLOT_THEME` (legacy `plot.png` still
  accepted), runs impls with the theme env set, and its big static rubric is sent as a cached
  system prompt (Anthropic prompt caching) instead of being re-billed per call
  (audit 2026-07-15 High#5, Medium#25) (#9642).
- **Async Cloud SQL fallback actually works** — the Cloud SQL connector path wrapped a sync
  pg8000 engine in `async_sessionmaker`, deferring a crash to the first request; it now uses
  the connector's async path (`create_async_engine` + `async_creator` with asyncpg) and closes
  via `close_async()` (audit 2026-07-15 High#6) (#9642).
- **API robustness triple** — MCP `search_specs_by_tags` no longer crashes on impls with NULL
  `impl_tags`; `DatabaseQueryError` returns a generic client message instead of reflecting raw
  SQLAlchemy error text (full detail still logged server-side); `api/cache.py` prunes per-key
  locks when a factory raises (404-probe traffic no longer grows `_locks` unbounded) and holds
  strong references to background refresh tasks so stale-while-revalidate can't be jammed by
  GC (audit 2026-07-15 Medium#1/#3/#4/#22) (#9642).
- **Library/language registry updates reach the prod DB** — the Postgres seed switched from
  `on_conflict_do_nothing` to an upsert, so version/description changes in `core/constants.py`
  propagate instead of being silently dropped (audit 2026-07-15 Medium#2) (#9642).
- **Dark-mode overlay controls and dropdown surfaces** — the copy button, action pills and
  loading pill on catalog/spec cards reused hardcoded white; they now share the theme-aware
  `overlayButtonSx` helper, and MUI Menu/Popover papers are wired to `var(--bg-elevated)` /
  `var(--ink)` so filter dropdowns follow the theme (audit 2026-07-15 High#1/#2) (#9642).
- **CORS origins come from config again** — `api/main.py` hardcoded `https://anyplot.ai`,
  leaving the promised `https://www.anyplot.ai` origin blocked and `settings.cors_origins`
  dead; the middleware now reads the settings list (audit 2026-07-15 Low) (#9642).
- **Agentic runbook fixes** — workflow-module artifacts land in `agentic/runs/` again (a
  doubled path segment wrote to `agentic/agentic/runs/`), and the run-timeout error derives
  its duration from the actual timeout instead of a hardcoded "5 minutes"
  (audit 2026-07-15 Medium#30, Low) (#9642).
- **Documentation reconciled with the 15-library reality** — generation/similarity/repair
  prompts, `prompts/workflow-prompts/README.md`, `/prime`, `.github/copilot-instructions.md`,
  and `agentic/docs/project-guide.md` no longer claim 9/11 Python-only libraries; the repair
  prompt says attempt `{ATTEMPT}/4` matching the workflow; `docs/reference/plausible.md` drops
  the removed `potd_dismiss`/PlotOfTheDay events; the README documents Streamable HTTP as the
  only MCP transport (the SSE endpoint is gone); stale `plot.png` code examples are
  theme-aware; a leaked personal `file://` path was scrubbed from a palette doc
  (audit 2026-07-15 Medium#14/#24/#26/#27/#31/#32/#33) (#9642).
- **Global keyboard shortcuts no longer hijack focused elements on `/plots`** — the
  window-level Space/Enter/Backspace handler now bails out when the keystroke targets an
  interactive element (button, link, focused card/chip/toggle), so keyboard-activating a card
  no longer double-fires with a random-plot jump (audit 2026-07-08 Quick Win 1) (#9620).
- **Dark-mode contrast for stock MUI components** — the MUI palette is locked to light-mode
  hexes (it can't hold CSS variables), so unselected tab labels, dividers, skeletons, and
  alerts rendered light-theme colors on dark backgrounds (~2.1:1 label contrast). MuiTab,
  MuiDivider, MuiSkeleton, and MuiAlert are now wired to the CSS-var system
  (`--ink-soft`/`--rule`/`--bg-elevated`), and the two `borderColor: 'divider'` usages in
  SpecTabs/RelatedSpecs use `var(--rule)` (audit 2026-07-08 High#4) (#9622).
- **Review rubric finally knows all 15 libraries** — the workflow-active reviewer prompt and
  scoring criteria still described the 9-Python-library era: the file-extension guide called
  highcharts Python and knew no `.js`/`.tsx`, SC-04's title rule rejected `javascript` (and in
  `quality-criteria.md` even `julia`) as a language token — silently costing every correct
  JS/Julia title points — `${LANGUAGE}`/`${EXT}` were referenced in the prompt but never passed
  by `impl-review.yml`, the interactive-fairness rules (don't penalize hover/zoom invisible in
  the PNG) lived only in a file no workflow reads, and the step-10 `review_checklist.json`
  example still showed the pre-rebalance 5-category shape (`library_features`, 40/25/20/10/5
  maxima) that corrupted ~6% of stored checklists. All lists are corrected to the canonical
  registry, the fairness rules (plus a JS-harness note for CQ-05) moved into the running prompt,
  AR-05 gained rows for chartjs/d3/echarts/muix, and new registry-derived tests in
  `tests/unit/prompts/` fail on any future library-list drift (audit 2026-07-08 Medium#1 +
  Medium#12) (#9623).
- **15-library drift sweep across secondary surfaces** — four independent audit findings traced
  to the same root cause: the library expansion never propagated beyond the pipeline.
  `core/constants.py` now derives `LIBRARY_NAMES`/`LANGUAGE_NAMES` from the canonical registry
  and `insights.py`/`debug.py` import them instead of hand-written maps (the `/debug` page
  showed raw ids for all four JS libraries), `app/index.html` meta/OG/Twitter/JSON-LD copy and
  the landing tagline no longer say "9 python libraries" (now 15 libraries across Python, R,
  Julia & JavaScript; JSON-LD keywords refreshed, stale okabe-ito reference replaced by the
  Imprint palette), and `scripts/evaluate-plot.py` dropped its dead Python-era highcharts
  pattern block and derives the AR-07 static-library set from the registry (audit 2026-07-08
  Medium#5 + Medium#6 + Low#8) (#9624).
- **Analytics hygiene: bots out, /plots visible, docs in sync** — nginx's `/api/event`
  Plausible proxy now returns 202 (without forwarding) for crawler UAs and headless/automation
  clients (HeadlessChrome, puppeteer/playwright/selenium, scripted HTTP libraries, empty UA) —
  the unfiltered synthetic waves inflated visitor counts ~40% and broke trend lines. Pageview
  URLs keep the real pathname for reserved pages, so `/plots` no longer records as `/` (the
  site's #2 page was invisible in Plausible; filter paths move from `/lib/x` to `/plots/lib/x`),
  and `/debug` fires a pageview at all. `docs/reference/plausible.md` caught up with the shipped
  product: `/map` + `/debug` pages, `nav_map` source, the previously undocumented
  `library_filter` event with its `framework` prop, and the 15-library value list (audit
  2026-07-08 High#7 repo-side + Medium#10 + Low#12/#15) (#9625).
- **Crawler 502 outage fixed** — since at least 2026-06-12, every crawler UA (googlebot,
  bingbot, twitterbot, discord, whatsapp, …) received HTTP 502 on every page: the nginx
  `@seo_proxy` hop verifies the upstream TLS chain of `api.anyplot.ai`, which is 4 certificates
  deep (leaf → Let's Encrypt YE1 → ISRG Root YE cross-sign → ISRG Root X2), while nginx's
  default `proxy_ssl_verify_depth` is 1. Depth raised to 4 in both proxy locations — humans saw
  a healthy site the whole time, making this a de-facto site-wide noindex (#9617).
- **All react-refresh ESLint warnings resolved** — `PALETTE` / `snippet()` extracted from
  `PalettePage.tsx` into `PalettePage.helpers.ts` (following the `MapPage.helpers.ts` pattern),
  and the `react-refresh/only-export-components` rule scoped off for test modules
  (`*.test.{ts,tsx}`, `test-utils.tsx`), which never participate in Fast Refresh (#9616).

### Security

- **Issue templates no longer auto-apply workflow trigger labels** — `spec-request` /
  `report-pending` previously flowed unauthenticated issue text straight into write-privileged
  Claude agents; the labels must now be added by a maintainer (GitHub requires triage rights to
  label), which puts a human review in front of every agent run (audit 2026-07-15 High#7) (#9642).
- **Composite actions SHA-pinned** — `setup-node`/`setup-r`/`setup-julia` used floating tags
  while every workflow pins to SHAs; all four `uses:` refs are now SHA-pinned and the
  Dependabot `github-actions` entry covers the composite-action directories so the pins stay
  fresh (audit 2026-07-15 Medium#13) (#9642).
- **Frontend nginx ships security headers** — new `app/security-headers.conf` (CSP tuned to
  Plausible/GCS/API needs, `nosniff`, `X-Frame-Options SAMEORIGIN`, `Referrer-Policy`, HSTS)
  included in both server blocks and re-included in every `add_header` location
  (audit 2026-07-15 Medium#21) (#9642).

*Catalog: 1,607 implementation merges across 15 libraries and 10 new plot types (heatmap-periodic-table, line-cycle-seasonal, depth-order-book, climograph-walter-lieth, audiogram-clinical, burndown-sprint, bar-heart-rate-zones, gauge-activity-rings, curve-power-duration, line-training-load-pmc); the catalogue stands at 324 specifications.*

## [3.0.0] — 2026-06-10 — Julia & JavaScript, 15 libraries & the Imprint palette

anyplot 3.0 doubles the language count — Julia and JavaScript join Python and R, growing the
catalog from 10 to 15 libraries, including the first browser-rendered and first React libraries —
and re-colors every existing implementation with the new Imprint palette. One clean break earns
the major version: Highcharts is now native JavaScript.

### Added

- **Julia / Makie.jl — 3rd language.** Julia 1.11 + CairoMakie with full pipeline support: CI
  runtime via `setup-julia`, `Project.toml` environment, makie arms in every impl workflow,
  dedicated prompts, Julia syntax highlighting in the code viewer (#7613).
- **JavaScript — 4th language: Chart.js, D3.js, Apache ECharts.** First browser-rendered runtime:
  a Node 22 + Playwright headless-Chromium harness (`automation/js-render/render.mjs`) renders
  each snippet at exact gallery pixels and emits both the PNG and a self-contained interactive
  HTML (#8244); JS implementations get the Interactive toggle on the site (#8251). The library
  registry gained a `framework` field and per-library file-extension overrides (#8244).
- **MUI X Charts — first React library.** Community `@mui/x-charts` as the first
  `framework: react` / `.tsx` library; the render harness gained an esbuild branch that bundles
  React components in a theme-aware MUI `ThemeProvider` (#8517).
- **Imprint — anyplot's own palette.** 8-hue colorblind-safe categorical palette + 3 semantic
  anchors replacing Okabe-Ito project-wide, with a named API in `core/palette.py` and
  `imprint_seq` / theme-adaptive `imprint_div` colormaps (#7692). `/palette` rebuilt: per-pixel
  OKLCH color wheel, chroma/ΔE/WCAG metrics, compare-with overlays, unified `IMPRINT` copy-paste
  object for Python/R/Julia/JS, pairwise ΔE matrices for normal + CVD vision (#7692, #8125).
- **Frontend CI gates:** Prettier, sorted imports, unused-import lint, and full type-checking now
  run on every PR (#8519); new `app/ARCHITECTURE.md` documents the structure (#8596).

### Changed

- **Frontend restructure (11 PRs):** `routes/` registry, `layouts/` + `sections/` split, feature
  folders, central API client, theme module, typed global config, `src/*` aliases (#8519–#8581).
- **Render canvas halved** to 3200×1800 / 2400×2400 with proportional-sizing review rules,
  validated by a 540-render style experiment (#7387); typography recalibrated across all
  libraries (#7389, #7391–#7428); hard canvas-size gate (±16 px) enforced pre-review (#7517);
  AR-09 edge-clipping auto-reject (#7528).
- **Palette migration:** ~1,300 existing implementations re-colored in a one-shot deterministic
  hex-swap wave (#7776–#7798), with semantic red/amber/green restored where color carries
  meaning (#7777).
- **Pipeline & ops:** watchdog rescues stale `ai-approved`, attempt-less `ai-rejected`, and
  label-less impl PRs (#7687); impl-merge sweeps stale failure labels (#7616); daily-regen
  rebalanced to 10×/day on Sonnet (#7717, #7286); impl-generate can overlay `prompts/` from the
  trigger branch for experiments (#7385); `/audit` retooled as goal-directed across 6 graded
  dimensions (#8023, #8024).
- **Dependencies:** 21 updates including playwright 1.55, esbuild 0.25, aiohttp 3.14,
  claude-code-action 1.0.133, plus grouped python/npm/MUI/react/actions bumps.

### Removed

- **Breaking: Highcharts Python wrapper.** Highcharts is now native `highcharts.js` instead of
  the `highcharts-core` Python wrapper, following the most-used-variant rule; all 322 legacy
  Python implementations and their metadata were removed — old Python deep links fall back to
  the spec hub (#8516).

### Fixed

- **Frontend performance:** above-the-fold landing counts no longer stall up to 2 s, `/specs`
  thumbnails lazy-load, `/stats` uses aggregate COUNT queries, empty-filter fast path (#7694).
- Tag chips correctly filter `/plots` again (#7516); visitors chart includes today (#7610);
  masthead on xs (#7891); dark-mode overlay buttons (#8021).
- Dual alembic heads that had stalled the production Postgres sync (#7285); silent chartjs/d3
  version-lookup failures (#8248); duplicate ruff key breaking main (#7683).

*Catalog: 885 regenerations + 310 new implementations across 15 libraries; 46 automated
spec-polish PRs; R/ggplot2 coverage 30 → 126; first 8 specs at full 15/15 coverage; 327 specs.*

## [2.4.0] — 2026-05-18 — R/ggplot2, multi-language pipeline & in-app feedback

anyplot is no longer Python-only — R / ggplot2 is the 10th supported library, riding on a new
multi-language pipeline that generalizes the spec → impl → review → merge flow beyond Python.

### Added

- **R / ggplot2 — 10th library, 2nd language** with the generalized multi-language pipeline:
  spec, generation, review, merge, code viewer, libraries page, language counts (#6944, #6961).
- **In-app feedback widget** reachable from any page (#7143), with dark-mode adaptation and
  clearer placeholder copy (#7282).
- **`/stats`:** Plausible visitors chart and a daily-impl timeline (#6608).
- **Language-aware navigation:** `/plots?lang=` filtering, cross-language carousel on plot pages,
  language in cards, titles, and analytics (#7141, #7142, #7144).
- **Ops:** review-retry listener + stuck-jobs watchdog workflows (#6084); local style-variant
  experimentation script (#6378).

### Changed

- Pseudo-function styling for 404 page, footer, empty state, and library card (#6436);
  daily-regen cadence 2 h → hourly (#6943).
- **Dependencies:** 13 Dependabot bumps across Python (mypy, urllib3, authlib), npm (react, mui),
  and GitHub Actions.

### Fixed

- Non-Python pipeline hardening: `renv` stdout suppression in the version probe (#6948), broken
  `renv.lock` removed (#6950), `prism/r` type shim so `tsc` no longer blocks Cloud Build (#7052).
- Language preserved through `/debug` deep links (#7066); no horizontal scroll on `/stats` and
  `/mcp` (#6902); breadcrumb truncation + initial FAB lift on deep links (#7283); lowercase
  language in plot-page SEO titles (#7206).

*Catalog: 30 ggplot2 implementations at release across foundational plot types; ~1,200
regenerations rolled across all 10 libraries during the window.*

## [2.3.0] — 2026-05-07 — 10 new plot types & end-to-end auto-merge

### Added

- **`/map` page** — force-directed spec map clustered by tag similarity, with a landing-page
  teaser (#5647, #5649, #5665).
- **OG images redesigned** in the any.plot() visual identity — branded cards with light/dark
  variants (#5659).
- **Mobile debug:** on-device console + richer ErrorBoundary (#5808); avatar in the legal page
  operator block (#5726).
- **10 new plot types** across 9 libraries: area-stacked, bar-horizontal, bland-altman-basic,
  count-basic, ice-basic, radar-multi, scatter-embedding, scatter-regression-polynomial,
  shap-waterfall, spiral-timeseries.

### Changed

- **Tag-vocabulary policy is now asymmetric** (#5856, #5859): `plot_type` is canonical (table
  authoritative, new types via PR); `data_type` / `domain` / `features` are advisory — polish
  only moves misclassified tags or canonicalizes synonyms, and no longer strips valid niche tags.
- **End-to-end auto-merge:** polish and impl PRs squash-merge themselves once green via
  `gh pr merge --auto` set on creation (#5955); behind branches auto-update after every push to
  `main` (#5957, #5958).
- **Pipeline:** autonomous spec polish + cross-library similarity audit in daily-regen pre-flight
  (#5714); daily-regen gained `spec_id` and `model` inputs (#5706); resumable single-step regen
  (#5650); transient-retry hardening across impl-generate/review (#5819, #5725, #5724);
  evaluate-plot switched to the canonical 6-category rubric (#5818).
- **Repo:** implementations moved under `plots/{spec}/implementations/python/{library}.py` to
  make room for other languages (#5648); 64 `Optional[X]` → `X | None` modernizations (#5727).
- **Docs:** library-expansion roadmap (#5951); FCP/TTFB Web-Vitals events documented and
  `/seo-proxy/map` handler added so bots get a real title for the map (#5818).

### Fixed

- iOS Safari load failure — `requestIdleCallback` polyfilled (#5816).
- POTD GitHub source link includes the language segment (#5663); letterbox strips around the
  preview removed (#5943).
- Frontend lint 32 → 0 errors, including React 19 `set-state-in-effect` refactors (#5818);
  fire-and-forget analytics tasks could be GC'd mid-flight — now held in a module-level set
  (#5727).

*Catalog: coverage filled for horizon-basic/seaborn (#5851).*

## [2.2.0] — 2026-04-29 — Regen wave, Cloudflare Access on /debug & 4-attempt pipeline

### Added

- **Cloudflare Access on `/debug`** with a service-token fallback for CI (#5522); same-origin
  `/api` proxy fixes the cookie scope (#5551); hard reload fires the page gate cleanly when the
  JWT lapses (#5552).
- **`/regen` command** for unattended library regeneration; `/audit` framework split into
  per-agent files with 7 new auditors (#5413, #5451).
- **Mandatory PR follow-through** codified in `CLAUDE.md` (#5553).

### Changed

- Repair budget bumped 3 → 4 attempts with cascading quality thresholds (90/80/70/60/50);
  `ADMIN_TOKEN` PAT for impl-merge ruleset bypass (#5523, #5521).
- Daily-regen runs on Sonnet (#5452) and skips the 20:00–24:00 Berlin window (#5517).
- **Dependencies:** 8 Dependabot bumps (uvicorn, setuptools, sqlalchemy, matplotlib,
  react-router-dom, grouped npm/python/actions).

*Catalog: 12-spec regen wave at ~3.5× v2.1.0 throughput; network-basic filled to 9/9;
area-mountain-panorama gained bokeh.*

## [2.1.0] — 2026-04-25 — Tri-state theme, pipeline resilience & 2 new plot types

### Added

- **Tri-state theme mode** — system / light / dark with live OS sync; the site follows the OS
  theme by default while respecting an explicit override (#5412).
- **2 new plot types:** venn-labeled-items (9/9) and area-mountain-panorama, whose spec was
  refined mid-flight to require jagged piecewise-linear ridgelines (#5411).
- Landing-page interaction analytics for hero/libraries/palette/nav/footer (#5400).

### Changed

- **Self-healing pipeline** against transient Claude Code Action failures (#5410): generate retry
  budget 2 → 3, repair and review auto-retry once; marker counts paginate properly.
- In-memory caching for spec lookups; review feedback from prior attempts is passed back into
  regeneration runs; code-view paper aesthetic (#5401).

### Fixed

- Scroll restoration on route change (#5403, #5404); mobile search width (#5363).

*Catalog: coverage filled (donut-basic/plotnine, contour-basic/pygal); 5 specs regenerated.*

## [2.0.0] — 2026-04-23 — anyplot.ai Relaunch

The project rebrands from pyplots.ai to anyplot.ai, ships a redesigned homepage, the Okabe-Ito
color palette, and first-class dark mode for the site and every plot preview. Major because
URLs, schema, and the public domain all change. (The annotated tag `v1.1.0-pyplots-final`,
2026-04-14, marks the last pyplots.ai state before the rebrand.)

### Added

- **New homepage & visual identity:** hero, libraries / palette / specifications sections,
  MonoLisa typography, Okabe-Ito colorblind-safe palette, theme-adaptive chrome.
- **Dark mode (site + plots):** every plot ships `plot-light` and `plot-dark` variants; theme
  tokens drive all chrome; mandatory theme-readability check in the AI quality pipeline.

### Changed

- **Breaking: domain migration** `pyplots.ai` → `anyplot.ai` (bookmarks and MCP clients should
  switch), with nginx redirect-loop fixes.
- **Breaking: URL restructure** — canonical spec URL is `/{specId}/{language}/{library}`; hub
  view consolidated under `/{specId}` with optional `?language=` filter; Catalog → Plots rename.
- **Breaking: schema** — multi-language restructure with a new `languages` table; implementations
  expose `preview_url_light` / `preview_url_dark` (legacy `preview_url` aliases the light
  variant).
- **CI/infrastructure:** 6 workflows migrated from service-account keys to Workload Identity
  Federation; bulk-generate moved to paced sequential dispatch with a global mutex; daily cron
  regenerates the oldest not-recently-updated spec on a 4 h cadence with a Berlin-evening
  blackout.
- **Dependencies:** MUI 7 → 9, Vite 7 → 8, FastMCP v3, FastAPI 0.136, anthropic 0.97, plus
  security bumps (cryptography, mako, authlib, python-multipart).

## [1.1.0] — 2026-04-10 — Visual Redesign & Theme Tokenization

### Added

- **Theme tokenization:** 80+ hardcoded hex colors and font strings centralized into
  `app/src/theme/index.ts`, with new tokens, shared style constants, and a central `LIB_ABBREV`
  map; full style-guide doc.

### Changed

- **Plot of the Day redesign:** terminal-style frame with a `$ python plots/...` prompt linking
  to the GitHub source, split layout, real library + Python versions.
- Responsive polish: mobile breadcrumb abbreviations, smoother RelatedSpecs grid progression.

### Fixed

- **WCAG AA:** 15+ contrast violations fixed; all text meets 4.5:1; keyboard-accessible zoom
  container with focus-visible.
- Pre-existing lint errors (setState in useEffect → render-time ref); AbortController fetch
  cleanup on unmount.

## [1.0.0] — 2026-04-07 — pyplots.ai launch

First formal release of pyplots.ai — an AI-powered platform for Python data-visualization
examples. At launch: 309 specifications, 2,668 implementations across 9 libraries, and 1,798
interactive HTML previews.

### Added

- Browse, filter, and search plots across 11 tag categories with AND/OR logic.
- Implementation pages: syntax-highlighted code, AI quality reviews, interactive previews; copy
  code, download PNG, fullscreen.
- `/stats` dashboard, Plot of the Day, and similar specifications/implementations via tag-based
  Jaccard similarity.
- MCP server for AI-assistant integration.
- Stack: FastAPI + async SQLAlchemy + PostgreSQL; React 19 + Vite + MUI + TypeScript; 13 GitHub
  Actions workflows (spec creation, impl generation, AI review, auto-merge); Cloud Run +
  Cloud SQL + GCS; 1,081 unit tests.

[Unreleased]: https://github.com/MarkusNeusinger/anyplot/compare/v4.1.0...HEAD
[4.1.0]: https://github.com/MarkusNeusinger/anyplot/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/MarkusNeusinger/anyplot/compare/v3.6.0...v4.0.0
[3.6.0]: https://github.com/MarkusNeusinger/anyplot/compare/v3.5.0...v3.6.0
[3.5.0]: https://github.com/MarkusNeusinger/anyplot/compare/v3.4.0...v3.5.0
[3.4.0]: https://github.com/MarkusNeusinger/anyplot/compare/v3.3.0...v3.4.0
[3.3.0]: https://github.com/MarkusNeusinger/anyplot/compare/v3.2.0...v3.3.0
[3.2.0]: https://github.com/MarkusNeusinger/anyplot/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/MarkusNeusinger/anyplot/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.4.0...v3.0.0
[2.4.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/MarkusNeusinger/anyplot/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/MarkusNeusinger/anyplot/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/MarkusNeusinger/anyplot/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/MarkusNeusinger/anyplot/releases/tag/v1.0.0
