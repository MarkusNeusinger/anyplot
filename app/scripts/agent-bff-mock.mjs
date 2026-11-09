#!/usr/bin/env node
/**
 * A local mock of the agent chat BFF (`/debug/agent/*`) plus the few catalogue
 * routes the plot page needs, for driving the "Use with my data" UI in a
 * browser without the real API, the agents service, a model or a database.
 *
 *   node app/scripts/agent-bff-mock.mjs            # http://localhost:8010, loopback only
 *   cd app && VITE_ENABLE_AGENT_CHAT=true \
 *     VITE_API_URL=http://localhost:8010 VITE_DEBUG_API_URL=http://localhost:8010 yarn dev
 *   open http://localhost:3000/scatter-basic/python/matplotlib   (the .use_my_data() entry)
 *   open http://localhost:3000/agent?spec=scatter-basic&library=matplotlib&language=python
 *   open http://localhost:3000/agent?spec=line-multi&library=matplotlib&language=python
 *     (one page since 2026-11-06: local development counts as the admin hint, so the page
 *     checks `/debug/agent/status` here and runs the admin lane, `/debug/agent/*`; the admin
 *     menu's "view as visitor", or a build without development mode and without the hint, runs
 *     the public lane, `/agent/*`; MOCK_PUBLIC_LANE=closed keeps its door shut;
 *     MOCK_TURNSTILE=require|refuse|down plays the bot check, with the page built with
 *     VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA, Cloudflare's always-passing test key)
 *
 * It follows the documented contract (docs/reference/api.md, "Agent chat"):
 * the CSRF header on every POST, PUT and DELETE, `{detail, ref}` errors with
 * an `X-Request-Id`, the spec's `roles` in the dataset answer, the binding
 * check's `errors` lines on a refused binding set, and a scripted `anyplot/1`
 * stream with `ready`, two `queued` statuses and the wait's end (`started`), the pipeline steps, `plot` (with
 * the stored `version`), `message` and `done`, with `: ping` comments in
 * between. Three specs exist: scatter-basic (`x`, `y`), line-multi (`x`, the
 * series family `y1, y2, ...`, an optional `series`) and box-basic (`category`,
 * `value`; for the data step only: a wide paste such as `Sensor_A,Sensor_B`
 * carries the `suggestion` and `POST .../dataset/to_long` applies it, like the
 * service's `data/shape.py`). Plots are drawn here as
 * PNGs from the pasted data (a scatter of the bound x and y columns, in the
 * theme's colours), in the spirit of the fake render backend's fixture PNG
 * (agents/anyplot/render/backends/fake.py); no code runs. Like the agents
 * service, the mock appends the footer strip below every plot it serves
 * (1600x900 becomes 1600x932); catalogue previews stay without it. Pasted text
 * that is no table ("Hund 7 Katze 3 und Vogel 4") comes back as the service's
 * transcribed answer (`transcribed: true`, the table's CSV in `text`, nothing
 * stored), so the confirmation card can be driven without a model. Step 1 ends
 * with `POST .../dataset/confirm`, which marks the stored dataset and its
 * bindings as checked (`422 no_dataset` without one); a stored parse or an
 * applied binding change clears the mark, and until it holds every pipeline
 * run answers `plot{status: not_ready, reason: data_unconfirmed}`. Every
 * `done` carries the session's `bindings` and `data_confirmed`, as the service
 * syncs them after a run, `language` (`{language, source}`, the session
 * language) and `dataset` after a turn that changed the data.
 * `PUT .../language` (the header's language chip, or an offer's `.switch()`)
 * validates `{language, via?}` like the BFF (`^[A-Za-z][A-Za-z -]{0,39}$` on the
 * value as sent, `via` `header` or `offer`, no other field), stores it in the
 * service's normalised form (a known name or endonym of the ten common languages
 * as its code, a two-letter value in lower case, anything else as typed) with
 * the source `chosen`, or `offer` for an accepted offer, answers
 * `{language, source}`, and `409 run_active` while a turn runs.
 * `GET .../bundle?include_data=&version=` (the page's `.save()`) answers the
 * session's feedback case from the mock's state, with the agents service's
 * top-level keys (the transcript of the turns, every version's code, result and
 * PNGs as base64, the profile, the bindings, a config stamp; each version's
 * `data.csv` only with `include_data`) and the BFF's attachment headers.
 * `POST .../feedback` (the result card's quick feedback) validates the body
 * like the BFF (`reaction` from the site's set, `message` at most 500
 * characters after the strip, `include_data` a boolean, `result_version` 0 to
 * 999, `replaces` a case id or absent, no other field), answers `404
 * not_found` for a version the session does not have (0 is the chat itself,
 * stored without image or plot.py; `422 no_data` with `include_data` before the
 * session has data), records the submission
 * on the session per version (a later one replaces it and keeps the `replaces`
 * it named; `GET /mock/feedback` lists them) and answers `201 {case_id,
 * stored}` with the file names the BFF would store. A message containing "502"
 * answers `502 storage` instead, so the failure line can be driven.
 *
 * `POST /sessions` answers the spec's `roles` with the session, as the service
 * does for the page header's columns ⓘ. The action `{action: "example_data"}`
 * (`.example_data()`) answers after a few seconds with a made-up table that
 * fits the spec (new data without data, the next version otherwise) and a
 * reply naming it, as the root's `run_data_code` with `source_language`
 * `example` does.
 *
 * The step-1 data changes (the service's `prepare_data` tool) in miniature:
 * the action `{action: "summarize_data"}` answers a scripted summary of the
 * profile. A paste is unsummarized until the first turn on it, as the service's
 * `summary_pending`: a typed message then is the note sent with the attachment,
 * which the mock answers with the summary and the note acted on in one reply
 * ("nur 2024" or "only 2024" keeps that year's rows, "dezimalkomma",
 * "decimal comma", "tausender" or "thousands" reads a column of `1.234` dots as
 * thousands separators); a note with "weather" or "joke" is refused and leaves
 * the paste unsummarized for the page's summary action, and a confirmation ends
 * it, as the service's confirm route does. A message containing
 * "prozent" or "percent" plays a `set_type`
 * (number) on the second column (a unit such as `%` removed, a decimal comma
 * read), "gruppier" or "group" an `aggregate` (a numeric column summed by the
 * column the message names, "gruppier nach x", else by the first text column),
 * "umbenenn" or "rename" a `rename` of the second column. Each stores the result as the next dataset version (the previous one
 * kept, at most five, the bindings carried over, the confirmation dropped) and
 * the turn's `done.dataset` carries `{preview, profile, bindings, warnings,
 * roles, changes, version, can_undo, original_version}` like the service;
 * `POST .../dataset/undo` restores the previous version under its own number
 * (`422 nothing_to_undo` at the paste). The versions are numbered once per
 * session, as the service numbers them: a paste, a change, an undo and a change
 * are 1, 2, 1 and 3, and a second paste is 4.
 *
 * The service's `generate_data` tool (a table computed from a formula) in
 * miniature: a message that contains "sin(" or "cos(" or "x**2", or "= " together
 * with "pi", "from" or "von", is a formula. A tiny fixed evaluator computes
 * `sin(x)`, `cos(x)` or `x**2` over 200 evenly spaced points (or the "N points"
 * the message names) of the range it names ("from -pi to pi", "von -3 bis 3"; by
 * default -pi to pi, -3 to 3 for the parabola), and the turn's `done.dataset`
 * carries the result: new data in a session without data (the roles included,
 * since the page has none yet), the next version otherwise, unconfirmed either
 * way. Pasted text that looks like a formula ("zeichne sin(x) von -pi bis pi",
 * "y = x**2") answers `422 formula` instead of the transcription, as the
 * service does, because a model must never compute rows. Before any parse, as the
 * service's `classify_paste` does, pasted code (an import, a definition, a call of
 * `np.`, `pd.` or `Math.`, an R assignment; at least half of its lines shaped like
 * code) answers `422 code` at any length, and a one-line request for data
 * ("Beispieldaten", "random numbers with 3 categories") answers `422 data_request`:
 * the page sends either to the chat, or asks to shorten code over 2,000 characters.
 *
 * The session language in miniature: every session starts at `en`/`default`
 * and stays there until the user picks another. A paste whose notes or column
 * names read German, or a typed message that is not refused and reads German
 * (an umlaut or ß, or a word such as "bitte", "und", "die", "mach", "zeichne",
 * "beschriftung"), offers German once: the dataset answer or the turn's `done`
 * carries `language: {language, source, offer: {language, basis}}`. After the
 * user took German (`PUT .../language` with `via: offer`, source `offer`), an
 * English message of three words or more offers English back, once. "labels in
 * german", "beschriftung auf englisch" or "auf deutsch bitte" (english, german,
 * french, spanish; deutsch, englisch, französisch, spanisch) is the root's
 * `set_language`: `chosen`, after which nothing is offered, and a reply; when
 * the session has a plot, the refinement below follows. A question ("…?") in a
 * German session gets the German reply.
 *
 * Scripted behaviour of a chat message:
 * - contains "weather" or "joke": the fixed out-of-scope refusal;
 * - contains "stock price" or "unemployment rate": the fixed data refusal (`needs_data`), except
 *   in the note sent with a paste, which the summary answers as any note;
 * - contains "busy": `error {code: capacity}`;
 * - contains "swap": the root's `set_bindings` in miniature, swapping the
 *   columns of `x` and the first `y` (which drops the confirmation), and a reply;
 * - a formula (see above): `generate_data`, and a reply naming the rows;
 * - code or a request for data (the dataset route's `422 code` and `422 data_request`
 *   guards): `run_data_code`, the spec's made-up table as `.example_data()` makes it;
 * - contains "prozent"/"percent", "gruppier"/"group" or "umbenenn"/"rename":
 *   a data change, see above, and a reply naming it; with "instead of" (or "statt") also a
 *   plot the server refuses after it (`plot{not_ready, data_unconfirmed}`), as a root that read
 *   the change as a plot change too called it;
 * - ends with "?": a reply only, no pipeline run;
 * - anything else: a refinement with a repair round, shipped as
 *   `needs_attention`; the word "dark" or "light" in the text renders that theme.
 * A plot renders in the site theme the page sends (`POST .../messages?theme=`), unless
 * the text asked for a theme or the refined version was asked for one (`pipeline.run_theme`).
 * Pasted data containing "ignore previous" answers `403 data_refused`; pasted
 * text that looks like a formula answers `422 formula`. `POST .../dataset/convert`
 * (a dropped binary file) answers by the first bytes: a zip is a workbook with two
 * sheets, Parquet one table, bytes holding "TOO_MANY_ROWS" the row-cap refusal.
 * Pasted text with two or more comma tables separated by a blank line answers
 * `tables` and `table` and reads the first one, or the body's `table`.
 *
 * JavaScript plots (JS-4b): with a JavaScript library in `AGENT_LIBRARIES`
 * (chartjs, d3, echarts, highcharts), a session of it gets JavaScript versions,
 * whose artifacts are `plot-<theme>.png`, `plot.js`, `plot.html` and `data.csv`.
 * `GET .../artifacts/plot.html?v=&theme=` builds the page on demand (MOCK_PAGE_MS)
 * in the theme asked for, the version's by default: a small inline chart page
 * under the harness's policy (the bound x and y on a canvas, with a hover
 * readout; no library bundle) in the agents service's wrapper
 * (`agents/anyplot/render/page.py`: no script of its own, the policy plus
 * `frame-src 'none'`, a sandboxed `srcdoc` frame), with the headers both
 * download routes set; `409 run_active` while a turn runs. Without such a
 * library the mock answers exactly as before. `POST .../outcome` (the cards'
 * usage beacon after a copy or a download) checks the body like the BFF and
 * answers `204`. `GET /preview/relay`, the card's interactive preview (JS-4b-2),
 * is the API's own relay page with its headers, which the mock reads from
 * `python3 api/preview_relay.py` at start (`503` when python3 cannot run it).
 * The card frames the relay at `VITE_API_URL` (`PREVIEW_RELAY_URL`), while the
 * chat's own requests go to `VITE_DEBUG_API_URL`: point both at the mock, as
 * above, or the frame comes from another host's relay (the production API's
 * with only `VITE_DEBUG_API_URL` set), and the browser runs that relay instead
 * of the checkout's.
 *
 *   AGENT_LIBRARIES=matplotlib,seaborn,chartjs node app/scripts/agent-bff-mock.mjs
 *   open http://localhost:3000/agent?spec=scatter-basic&library=chartjs&language=javascript
 *
 * Environment: PORT (8010), MOCK_STEP_MS (700, per pipeline step),
 * MOCK_QUEUE_MS (2500, per queue position), MOCK_QUEUE (2, the starting
 * position of a turn; 0 skips the queue), MOCK_STOP_MS (2000, how long a run
 * stopped during a pipeline step takes to finish that step before `done`,
 * like the real run, which notices the abort only between steps; a turn that
 * still waits in the queue leaves it at once), MOCK_START_MS (0, how long a
 * pipeline run takes from leaving the queue to its first step, so the page's
 * `starting…` stays visible), MOCK_REPAIR (`1`: a first plot, too, fails its
 * first review and runs a repair round, as a refinement always does),
 * MOCK_REPLY_MS (half a step, how long the reply takes after the plot, the
 * root's call that writes it), MOCK_PARSE_MS (400, how long a
 * parse takes, the dataset judge's call in production; a transcription takes
 * 900 ms more), MOCK_OPEN_MS (0, how long `POST /sessions` takes, so the page's
 * opening state, where the bot check runs on the public lane, stays visible),
 * MOCK_DONE_MS (0, how long a turn's `done` waits after its last event, so the
 * marks that come with it, a question's `?` and its answer label, arrive visibly
 * after the reply), MOCK_MEMORY_FIELD (`0`: a shipped plot names no
 * `memory`, as an older server's, so its card shows no kept label).
 * The load mood and the admin meters (slice 8+9): MOCK_MAX_ATTEMPTS (unset: no field; else the
 * run's round cap, `max_attempts` on every pipeline step, as the service's `AGENT_MAX_ATTEMPTS`
 * sends it), MOCK_WAITING (0, other turns that wait in the run queue besides the mock's own, which
 * `/status` counts in `waiting`), MOCK_PAUSED (`1`: `/status` says the day budget is spent,
 * `paused` until the next 00:00 UTC, `resets_at`) and MOCK_BUDGET_PCT (62, the share of the day
 * budget `GET /debug/agent/budget` reports spent, the admin lane only).
 * Slowed down, the page's working states stay visible:
 *
 *   MOCK_OPEN_MS=2500 MOCK_PARSE_MS=4000 MOCK_QUEUE=0 MOCK_STEP_MS=3000 node app/scripts/agent-bff-mock.mjs
 *
 * A cut stream: every turn event carries the SSE id `<run_id>.<n>`, and `GET .../turn` with
 * `Last-Event-ID` streams the session's latest turn after that event, live until it ends (`404
 * not_found` for another turn, `422 invalid` for an id of another form), as the agents service's
 * turn log does. MOCK_CUT_AFTER (0: never) drops a session's first plot turn's connection after
 * that many events, the way the edge loses one, while the turn runs on to its end;
 * MOCK_RESUME_FAILS (0) drops a session's first that many reads of a turn, so the page's
 * reconnecting line stays visible:
 *
 *   MOCK_QUEUE=0 MOCK_STEP_MS=3000 MOCK_CUT_AFTER=3 MOCK_RESUME_FAILS=2 node app/scripts/agent-bff-mock.mjs
 *
 * The admin fan-out (`.plot_all()`): `POST .../dataset/copy` with `{from_session}` copies the source session's
 * confirmed data, bindings and session language into a session opened with `source: fanout`, with the service's
 * refusals (`404 session_expired`, `409 has_dataset`, `422 no_dataset`, `422 unconfirmed`, `422 invalid`).
 * MOCK_NO_COPY=1 answers it `404 not_found`, as an agents service deployed before the route does, so the page's
 * fallback (the paste posted again, or `copy_unavailable`) can be driven.
 *
 * The library switch and the plot memory (since 2026-11-02): `POST .../library` answers `target` and `carry`
 * (`{decisions, newer, target_has_plot, from_plot, offer}`) like the service's `switch.summary`: a switch away
 * from a library with a plot (or on from one whose carry has not run, or with remembered decisions alone)
 * writes a carry for the new library, and `offer` holds while something carries and the new library has no
 * plot or a plot older than some decisions. A shipped typed change remembers one decision in the user's words
 * (its kind read from keywords such as "title", "label", "line", "red", "log"; a title, a label, a scale or a
 * colour replaces the one of its kind and axis, a line or a marker is added beside the others, at most 30); a
 * shipped `create_plot` keeps the memory, which only the user clears; `{action: "carry_plot"}` plots from the
 * catalogue code like `create_plot`, in the theme the user asked for in the library before, and spends the
 * carry. `GET .../memory` lists the entries with `written` (the memory ever held one), `DELETE .../memory/{id}`
 * removes one (`404 not_found`, `409 run_active`) and `DELETE .../memory` forgets all. A shipped plot's event
 * names the memory its version stands on, `memory: {kept, added}` by entry id, settled before the event as the
 * service does. A typed plot wish before the data is confirmed (also in the note sent with a paste), while the
 * library has no plot of this data (a plot of data a new paste replaced is none), is kept for its first plot as
 * the root's `keep_plot_request` keeps it, which the stream shows nothing of; that plot then remembers it. Every
 * new data version (a paste, a change, an undo) drops the carry, and a switch takes only the asked theme of a plot
 * of another data version. The paste answer's `columns_changed` says that a column the replaced data was bound to is not in the
 * new data (by its exact name), as the service's does (owner decisions of 2026-11-08).
 *
 * What a turn changed: every `done` of a turn that ended well carries `turn` (`answer`, `data`, `plot`,
 * `language` or `kept`, the service's `stream.turn_outcome` for the paths the mock plays): a question, a
 * summary and a note without a change are `answer`, a refusal, an error or a stop carry none.
 *
 * The data panel's full view (`.view_all()`): `GET .../dataset/data.csv` answers the current version's CSV
 * (`422 no_dataset` without data). A chat message naming a size such as "10000 rows x 30 columns" (also `×` or
 * `by`, at most 20,000 rows and 50 columns) is a table the assistant computed, like `generate_data`: a fixed
 * pseudo-random mix of an id, a date, a text column with a comma, a quote and a space run, and number columns with
 * a gap every few rows, past the paste's 1 MB, so the view can be driven at size.
 */

import { execFileSync } from 'node:child_process';
import http from 'node:http';
import { randomBytes, randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import zlib from 'node:zlib';

const PORT = Number(process.env.PORT || 8010);
const STEP_MS = Number(process.env.MOCK_STEP_MS || 700);
const QUEUE_MS = Number(process.env.MOCK_QUEUE_MS || 2500);
const QUEUE_START = Number(process.env.MOCK_QUEUE ?? 2);
const STOP_MS = Number(process.env.MOCK_STOP_MS ?? 2000);
const START_MS = Number(process.env.MOCK_START_MS ?? 0);
const REPLY_MS = process.env.MOCK_REPLY_MS ? Number(process.env.MOCK_REPLY_MS) : null;
// The wait between a turn's last event and its `done` (MOCK_DONE_MS), so the page's marks that come
// with `done` (a question's `?`, its answer label) can be watched arriving after the reply.
const DONE_MS = Number(process.env.MOCK_DONE_MS ?? 0);
// MOCK_MEMORY_FIELD=0 plays a server that names no version memory (`plot.memory`), as an older one.
const MEMORY_FIELD = process.env.MOCK_MEMORY_FIELD !== '0';
const REPAIR = process.env.MOCK_REPAIR === '1';
const PARSE_MS = Number(process.env.MOCK_PARSE_MS ?? 400);
const OPEN_MS = Number(process.env.MOCK_OPEN_MS ?? 0);
const NO_COPY = process.env.MOCK_NO_COPY === '1';
const CUT_AFTER = Number(process.env.MOCK_CUT_AFTER ?? 0);
const RESUME_FAILS = Number(process.env.MOCK_RESUME_FAILS ?? 0);
// The run's round cap on the pipeline steps (`max_attempts`); unset sends no field, as an older server.
const MAX_ATTEMPTS = process.env.MOCK_MAX_ATTEMPTS ? Number(process.env.MOCK_MAX_ATTEMPTS) : null;
// Other turns in the run queue, which `/status` counts in `waiting` (the page's mood reads `busy`).
const OTHERS_WAITING = Number(process.env.MOCK_WAITING ?? 0);
// The day budget is spent: `/status` says `paused` until the next 00:00 UTC.
const PAUSED = process.env.MOCK_PAUSED === '1';
// The share of the day budget spent, for the admin lane's `GET /budget`.
const BUDGET_PCT = Number(process.env.MOCK_BUDGET_PCT ?? 62);
/** The public lane's door (`GET /agent/lane`): open unless `MOCK_PUBLIC_LANE=closed`. */
const PUBLIC_LANE_OPEN = process.env.MOCK_PUBLIC_LANE !== 'closed';
/**
 * The bot check (api/turnstile.py) on the public `POST /sessions`, the public feedback and the
 * site's `POST /feedback`: off by default; `MOCK_TURNSTILE=require` refuses a call without an
 * `X-Turnstile-Token` (`403 bot_check_failed`), `MOCK_TURNSTILE=refuse` refuses every call,
 * `MOCK_TURNSTILE=down` answers `503 bot_check_unavailable`. Cloudflare's test keys answer the
 * same dummy token every time, so the mock cannot play siteverify's single use. `GET
 * /mock/turnstile` lists the calls it let through, in order, with the path and the token.
 */
const TURNSTILE_MODE = process.env.MOCK_TURNSTILE || 'off';
const turnstilePassed = [];

/** The bot check's refusal for this request, or null when it may pass. */
function botCheckRefusal(req, path) {
  if (TURNSTILE_MODE === 'off') return null;
  if (TURNSTILE_MODE === 'down') return [503, 'bot_check_unavailable'];
  const token = String(req.headers['x-turnstile-token'] || '');
  if (TURNSTILE_MODE === 'refuse' || !token) return [403, 'bot_check_failed'];
  turnstilePassed.push({ path, token });
  return null;
}
const BASE = `http://localhost:${PORT}`;

/**
 * The preview relay (`GET /preview/relay`, JS-4b-2), exactly as the API serves it: its page and headers come from
 * `api/preview_relay.py` itself (`python3 api/preview_relay.py`), so the mock holds no copy of the relay's script.
 * The relay admits every `http://localhost:*` parent, the dev server's included. Null when python3 cannot run it.
 */
function loadRelay() {
  try {
    const script = fileURLToPath(new URL('../../api/preview_relay.py', import.meta.url));
    return JSON.parse(execFileSync('python3', [script], { encoding: 'utf-8' }));
  } catch {
    return null;
  }
}
const RELAY = loadRelay();

const role = (name, kinds, description, { required = true, variadic = false } = {}) => ({
  name,
  kinds,
  required,
  variadic,
  description,
});

// Two catalogue specs with the roles the agents service parses from their
// `## Data` bullets: scatter-basic (two single roles) and line-multi (a
// variadic series family `y1, y2, ...` and an optional role).
const SPECS = {
  'scatter-basic': {
    id: 'scatter-basic',
    title: 'Basic Scatter Plot',
    description:
      'A fundamental 2D scatter plot that displays the relationship between two numeric variables.',
    data: [
      '`x` (numeric) - Independent variable values plotted on the horizontal axis',
      '`y` (numeric) - Dependent variable values plotted on the vertical axis',
    ],
    notes: ['Points should have moderate transparency (alpha ~0.7) to reveal overlapping data'],
    roles: [
      role('x', ['numeric'], 'Independent variable values plotted on the horizontal axis'),
      role('y', ['numeric'], 'Dependent variable values plotted on the vertical axis'),
    ],
  },
  'line-multi': {
    id: 'line-multi',
    title: 'Multi-Line Comparison Plot',
    description:
      'A multi-line plot displays multiple data series on the same axes for direct comparison.',
    data: [
      '`x` (numeric/datetime) - Shared sequential or time values for alignment',
      '`y1, y2, ...` (numeric) - Multiple continuous series to compare',
      '`series` (categorical) - Optional grouping variable if data is in long format',
    ],
    notes: ['Use distinct colors for each series'],
    roles: [
      role('x', ['numeric', 'datetime'], 'Shared sequential or time values for alignment'),
      role('y', ['numeric'], 'Multiple continuous series to compare', { variadic: true }),
      role('series', ['categorical'], 'Optional grouping variable if data is in long format', {
        required: false,
      }),
    ],
  },
  // A long-data spec: a wide paste (`Sensor_A,Sensor_B,...`) gets the `.to_long()` offer.
  // The mock's plot drawing knows only x and y, so this spec is for the data step.
  'box-basic': {
    id: 'box-basic',
    title: 'Basic Box Plot',
    description: 'A box plot that compares the distribution of a numeric value across categories.',
    data: [
      '`category` (string) - group labels for comparison',
      '`value` (numeric) - numerical values to plot',
    ],
    notes: ['Show the median line clearly'],
    roles: [
      role('category', ['text'], 'group labels for comparison'),
      role('value', ['numeric'], 'numerical values to plot'),
    ],
  },
};
/** The enabled libraries, as the deploy's `AGENT_LIBRARIES` (comma-separated) would name them. */
const AGENT_LIBRARIES = process.env.AGENT_LIBRARIES?.split(',').filter(Boolean) ?? [
  'matplotlib',
  'seaborn',
];
/**
 * The JavaScript libraries the agents service serves (`runtimes.JAVASCRIPT_LIBRARIES`). A session of one,
 * enabled through `AGENT_LIBRARIES`, gets JavaScript versions: `plot.js` instead of `plot.py`, and the
 * self-contained `plot.html`, which the artifact route builds per theme (JS-4b).
 */
const JS_LIBRARIES = {
  chartjs: 'Chart.js',
  d3: 'D3',
  echarts: 'ECharts',
  highcharts: 'Highcharts',
};
const isJs = library => Object.hasOwn(JS_LIBRARIES, library);
/** How long a page build takes: the renderer's `POST /page`, about 0.6 s with the container's start. */
const PAGE_MS = Number(process.env.MOCK_PAGE_MS || 600);
const MAX_DATASET_BYTES = 1024 * 1024;
/** The chat's message cap (`schemas.MAX_MESSAGE_CHARS`): only a data request within it moves to the chat. */
const MAX_MESSAGE_CHARS = 2000;
/** What the agents service stores as the user's message of an action turn (`ACTION_MESSAGES`). */
const ACTION_MESSAGES = {
  create_plot: '[action] Create the plot from my dataset and bindings.',
  carry_plot:
    '[action] Create the plot from my dataset and bindings, with the decisions I made so far.',
  summarize_data: '[action] Summarize the dataset for the user.',
  example_data: '[action] Make example data to try this plot.',
};
/** The plot memory's caps (`agents/anyplot/memory.py`): a new entry past them is refused, never an old one dropped. */
const MAX_MEMORY_ENTRIES = 30;
const MAX_MEMORY_TEXT_CHARS = 200;

// ---------------------------------------------------------------- PNG drawing

const THEMES = {
  light: { bg: [0xfa, 0xf8, 0xf1], ink: [0x1a, 0x1a, 0x17], grid: [0xe4, 0xe1, 0xd8] },
  dark: { bg: [0x1a, 0x1a, 0x17], ink: [0xf0, 0xef, 0xe8], grid: [0x33, 0x33, 0x2e] },
};
const IMPRINT = ['#009E73', '#C475FD', '#4467A3', '#BD8233', '#AE3030', '#2ABCCD'].map(hex => [
  parseInt(hex.slice(1, 3), 16),
  parseInt(hex.slice(3, 5), 16),
  parseInt(hex.slice(5, 7), 16),
]);

const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}
function chunk(type, data) {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([length, body, crc]);
}

class Canvas {
  constructor(width, height, bg) {
    this.width = width;
    this.height = height;
    this.rgb = Buffer.alloc(width * height * 3);
    for (let i = 0; i < width * height; i += 1) this.rgb.set(bg, i * 3);
  }
  rect(x0, y0, x1, y1, color, alpha = 1) {
    for (let y = Math.max(0, Math.round(y0)); y < Math.min(this.height, Math.round(y1)); y += 1) {
      for (let x = Math.max(0, Math.round(x0)); x < Math.min(this.width, Math.round(x1)); x += 1) {
        this.blend(x, y, color, alpha);
      }
    }
  }
  disc(cx, cy, r, color, alpha) {
    for (let y = Math.floor(cy - r); y <= Math.ceil(cy + r); y += 1) {
      for (let x = Math.floor(cx - r); x <= Math.ceil(cx + r); x += 1) {
        if (x < 0 || y < 0 || x >= this.width || y >= this.height) continue;
        if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r) this.blend(x, y, color, alpha);
      }
    }
  }
  blend(x, y, color, alpha) {
    const i = (y * this.width + x) * 3;
    for (let c = 0; c < 3; c += 1) {
      this.rgb[i + c] = Math.round(this.rgb[i + c] * (1 - alpha) + color[c] * alpha);
    }
  }
  png() {
    const stride = this.width * 3;
    const raw = Buffer.alloc((stride + 1) * this.height);
    for (let y = 0; y < this.height; y += 1) {
      this.rgb.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
    }
    const header = Buffer.alloc(13);
    header.writeUInt32BE(this.width, 0);
    header.writeUInt32BE(this.height, 4);
    header.set([8, 2, 0, 0, 0], 8);
    return Buffer.concat([
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
      chunk('IHDR', header),
      chunk('IDAT', zlib.deflateSync(raw)),
      chunk('IEND', Buffer.alloc(0)),
    ]);
  }
}

// ---------------------------------------------------------------- the footer strip

// The agents service appends a footer strip below every PNG it serves
// (agents/anyplot/render/watermark.py): defined on the 3200 px canvas and scaled
// with the width, so the mock's 1600x900 plots arrive as 1600x932. The mock draws
// the same layout with a 5x9 pixel font instead of JetBrains Mono, which is close
// enough to judge the result card at the served aspect.
const FOOTER = { strip: 64, text: 22, inset: 40, capEm: 0.73, dotEm: 1.45 };
const BRAND = [0x00, 0x9e, 0x73];
// Rows top to bottom; rows 0-6 sit above the baseline, rows 7-8 are descenders. Bit 4 is the left column.
const GLYPHS = {
  a: [0, 0, 14, 1, 15, 17, 15, 0, 0],
  b: [16, 16, 22, 25, 17, 17, 30, 0, 0],
  c: [0, 0, 14, 16, 16, 17, 14, 0, 0],
  d: [1, 1, 13, 19, 17, 17, 15, 0, 0],
  e: [0, 0, 14, 17, 31, 16, 14, 0, 0],
  f: [6, 9, 8, 28, 8, 8, 8, 0, 0],
  g: [0, 0, 15, 17, 17, 17, 15, 1, 14],
  h: [16, 16, 22, 25, 17, 17, 17, 0, 0],
  i: [4, 0, 12, 4, 4, 4, 14, 0, 0],
  j: [2, 0, 6, 2, 2, 2, 2, 18, 12],
  k: [16, 16, 18, 20, 24, 20, 18, 0, 0],
  l: [12, 4, 4, 4, 4, 4, 14, 0, 0],
  m: [0, 0, 26, 21, 21, 21, 21, 0, 0],
  n: [0, 0, 22, 25, 17, 17, 17, 0, 0],
  o: [0, 0, 14, 17, 17, 17, 14, 0, 0],
  p: [0, 0, 30, 17, 17, 17, 30, 16, 16],
  q: [0, 0, 15, 17, 17, 17, 15, 1, 1],
  r: [0, 0, 22, 25, 16, 16, 16, 0, 0],
  s: [0, 0, 15, 16, 14, 1, 30, 0, 0],
  t: [8, 8, 28, 8, 8, 9, 6, 0, 0],
  u: [0, 0, 17, 17, 17, 19, 13, 0, 0],
  v: [0, 0, 17, 17, 17, 10, 4, 0, 0],
  w: [0, 0, 17, 17, 21, 21, 10, 0, 0],
  x: [0, 0, 17, 10, 4, 10, 17, 0, 0],
  y: [0, 0, 17, 17, 17, 17, 15, 1, 14],
  z: [0, 0, 31, 2, 4, 8, 31, 0, 0],
  '-': [0, 0, 0, 0, 14, 0, 0, 0, 0],
  '/': [1, 2, 2, 4, 8, 8, 16, 0, 0],
  '(': [2, 4, 8, 8, 8, 4, 2, 0, 0],
  ')': [8, 4, 2, 2, 2, 4, 8, 0, 0],
};
const DOT = null;

function footerHeight(width) {
  return Math.round((FOOTER.strip * width) / 3200);
}

/** "made with any.plot()" and "anyplot.ai/<spec>" in the strip below the plot's `top` rows. */
function drawFooter(canvas, theme, specId, top) {
  const { ink } = THEMES[theme];
  const scale = canvas.width / 3200;
  const size = FOOTER.text * scale;
  const inset = FOOTER.inset * scale;
  const cell = Math.round(0.6 * size); // a monospaced advance
  const dot = FOOTER.dotEm * size;
  const side = Math.max(1, Math.round(0.185 * dot));
  const baseline = top + Math.round((footerHeight(canvas.width) + FOOTER.capEm * size) / 2);
  const widthOf = parts =>
    parts.reduce((sum, part) => sum + (part === DOT ? 0.64 * dot : part[0].length * cell), 0);
  const draw = (parts, start) => {
    let x = start;
    for (const part of parts) {
      if (part === DOT) {
        const x0 = Math.round(x + 0.251 * dot);
        canvas.rect(x0, baseline - side, x0 + side, baseline, BRAND, 0.9);
        x += 0.64 * dot;
        continue;
      }
      const [text, bold, alpha] = part;
      for (const ch of text) {
        (GLYPHS[ch] ?? []).forEach((bits, row) => {
          const mask = bold ? (bits << 1) | bits : bits << 1; // bold doubles each column
          for (let column = 0; column < 6; column += 1) {
            if (mask & (32 >> column)) {
              const px = Math.round(x) + column;
              const py = baseline - 7 + row;
              canvas.rect(px, py, px + 1, py + 1, ink, alpha);
            }
          }
        });
        x += cell;
      }
    }
  };
  canvas.rect(0, top, canvas.width, top + 1, ink, 0.15);
  const madeWith = [
    ['made with ', false, 0.56],
    ['any', true, 0.7],
    DOT,
    ['plot', true, 0.7],
    ['()', false, 0.315],
  ];
  draw(madeWith, inset);
  const address = [['anyplot', true, 0.7], DOT, ['ai', true, 0.7], [`/${specId}`, false, 0.56]];
  draw(address, canvas.width - inset - widthOf(address));
}

/**
 * A plot-like PNG: axes, a light grid, and either a scatter of each series in
 * `series` or bars; with `footer` (a spec id), the served footer strip below it.
 */
function drawPlot(
  theme,
  series,
  { width = 1600, height = 900, firstColor = 0, footer = null } = {}
) {
  const { bg, ink, grid } = THEMES[theme];
  const canvas = new Canvas(width, footer ? height + footerHeight(width) : height, bg);
  const left = width * 0.09;
  const right = width * 0.96;
  const top = height * 0.08;
  const bottom = height * 0.88;
  for (let i = 1; i <= 4; i += 1) {
    const y = bottom - ((bottom - top) * i) / 4;
    canvas.rect(left, y, right, y + 2, grid);
    const x = left + ((right - left) * i) / 4;
    canvas.rect(x, top, x + 2, bottom, grid);
  }
  canvas.rect(left, top, left + 3, bottom + 3, ink);
  canvas.rect(left, bottom, right, bottom + 3, ink);
  const all = (series ?? []).flat();
  if (all.length > 1) {
    const xs = all.map(p => p[0]);
    const ys = all.map(p => p[1]);
    const [xmin, xmax] = [Math.min(...xs), Math.max(...xs)];
    const [ymin, ymax] = [Math.min(...ys), Math.max(...ys)];
    const sx = v => left + 30 + ((v - xmin) / (xmax - xmin || 1)) * (right - left - 60);
    const sy = v => bottom - 30 - ((v - ymin) / (ymax - ymin || 1)) * (bottom - top - 60);
    series.forEach((points, index) => {
      const color = IMPRINT[(firstColor + index) % IMPRINT.length];
      for (const [x, y] of points) canvas.disc(sx(x), sy(y), height * 0.016, color, 0.72);
    });
  } else {
    const bar = (right - left) / 12;
    IMPRINT.forEach((c, i) => {
      const x0 = left + bar * 0.6 + i * bar * 1.6;
      canvas.rect(x0, bottom - (i + 2) * ((bottom - top) / 9), x0 + bar, bottom - 2, c);
    });
  }
  if (footer) drawFooter(canvas, theme, footer, height);
  return canvas.png();
}

const catalogueImages = new Map();
function cataloguePng(theme) {
  if (!catalogueImages.has(theme)) catalogueImages.set(theme, drawPlot(theme, null));
  return catalogueImages.get(theme);
}

// ---------------------------------------------------------------- data parsing

function splitLine(line, delimiter) {
  const cells = [];
  let cell = '';
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (quoted) {
      if (ch === '"' && line[i + 1] === '"') {
        cell += '"';
        i += 1;
      } else if (ch === '"') quoted = false;
      else cell += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === delimiter) {
      cells.push(cell.trim());
      cell = '';
    } else cell += ch;
  }
  cells.push(cell.trim());
  return cells;
}

/**
 * The transcribed answer of `POST .../dataset` for text that is no table: every
 * `<label> <number>` pair becomes a row of `category,value`, and the CSV goes
 * through `parseDataset` so the preview and profile match a later `.use()`.
 * Returns null when the text holds no such pair (the real service answers 422).
 */
function transcribeFreeText(text) {
  const pairs = [...text.matchAll(/([\p{L}][\p{L}\p{N}_-]*)\s+(-?\d+(?:[.,]\d+)?)\b/gu)];
  if (!pairs.length) return null;
  const rows = pairs.map(([, label, number]) => [label, number.replace(',', '.')]);
  const csv = ['category,value', ...rows.map(row => row.join(','))].join('\n') + '\n';
  const parsed = parseDataset(csv);
  return {
    transcribed: true,
    text: csv,
    preview: parsed.preview,
    profile: parsed.profile,
    warnings: parsed.warnings,
    note: rows.length < 3 ? 'only two values found; check the text' : '',
  };
}

function parseDataset(text) {
  const trimmed = text.replace(/^﻿/, '').trim();
  let header;
  let rows;
  let format;
  if (trimmed.startsWith('[')) {
    const records = JSON.parse(trimmed);
    if (!Array.isArray(records) || !records.length || typeof records[0] !== 'object') {
      throw new Error('unparseable');
    }
    header = Object.keys(records[0]);
    rows = records.map(record => header.map(name => String(record[name] ?? '')));
    format = 'json_records';
  } else {
    const lines = trimmed.split(/\r\n|\r|\n/).filter(line => line.trim());
    if (lines.length < 2) throw new Error('unparseable');
    const candidates = [
      [',', 'csv'],
      [';', 'semicolon'],
      ['\t', 'tsv'],
      ['|', 'pipe'],
    ];
    const [delimiter, name] = candidates
      .map(([d, n]) => [d, n, splitLine(lines[0], d).length])
      .sort((a, b) => b[2] - a[2])[0];
    header = splitLine(lines[0], delimiter);
    if (header.length < 2) throw new Error('unparseable');
    rows = lines.slice(1).map(line => splitLine(line, delimiter));
    format = name;
  }
  const warnings = [];
  header = header.map((name, index) => {
    if (name) return name.slice(0, 64);
    warnings.push(`column ${index + 1} has no name; it is called 'column_${index + 1}'`);
    return `column_${index + 1}`;
  });
  rows = rows.map(row => header.map((_, index) => row[index] ?? ''));
  const columns = header.map((name, index) => {
    const cells = rows.map(row => row[index]);
    const present = cells.filter(cell => cell !== '');
    const numeric =
      present.length > 0 && present.every(cell => /^-?\d+(\.\d+)?(e[+-]?\d+)?$/i.test(cell));
    const integer = numeric && present.every(cell => /^-?\d+$/.test(cell));
    const date =
      !numeric && present.length > 0 && present.every(c => /^\d{4}-\d{2}(-\d{2})?$/.test(c));
    const dtype = integer ? 'integer' : numeric ? 'number' : date ? 'datetime' : 'text';
    const values = numeric ? present.map(Number) : [];
    const counts = new Map();
    for (const cell of present) counts.set(cell, (counts.get(cell) ?? 0) + 1);
    const missing = cells.length - present.length;
    if (missing)
      warnings.push(`column '${name}': ${missing} missing value${missing > 1 ? 's' : ''}`);
    const sorted = [...values].sort((a, b) => a - b);
    const median = sorted.length
      ? sorted.length % 2
        ? sorted[(sorted.length - 1) / 2]
        : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : null;
    return {
      name,
      dtype,
      missing,
      unique: counts.size,
      min: numeric ? Math.min(...values) : (present[0] ?? null),
      max: numeric ? Math.max(...values) : (present[present.length - 1] ?? null),
      // The service's statistics of a numeric column (six significant digits), for the step-1 summary.
      mean: numeric
        ? Number((values.reduce((a, b) => a + b, 0) / values.length).toPrecision(6))
        : null,
      median: numeric ? Number(median.toPrecision(6)) : null,
      top: [...counts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([cell]) => cell.slice(0, 40)),
    };
  });
  return {
    header,
    rows,
    profile: {
      rows: rows.length,
      columns,
      sample: rows.slice(0, 5),
      source_format: format,
      decimal: '.',
      warnings,
    },
    preview: rows.slice(0, 20).map(row => row.map(cell => cell.slice(0, 40))),
    warnings,
  };
}

// The agents service's ACCEPTS table (agents/anyplot/data/bindings.py), without the tiers.
const ACCEPTS = {
  numeric: ['number', 'integer'],
  categorical: ['text', 'boolean', 'integer'],
  text: ['text', 'boolean', 'integer'],
  boolean: ['boolean', 'integer'],
  datetime: ['datetime'],
};
const accepts = (spec, dtype) =>
  !spec.kinds.length || spec.kinds.some(kind => ACCEPTS[kind]?.includes(dtype));

/** The role a binding name refers to: an exact single role, else the family `<name><digits>`. */
function resolveRole(roles, name) {
  return (
    roles.find(r => !r.variadic && r.name === name) ??
    roles.find(r => r.variadic && new RegExp(`^${r.name}\\d+$`).test(name)) ??
    null
  );
}

/** Like `check_bindings`: the error lines, or the stored set with its completeness. */
function checkBindings(session, bindings) {
  const roles = SPECS[session.specId].roles;
  const columns = new Map(session.dataset.profile.columns.map(c => [c.name, c]));
  const errors = [];
  // A column may serve several roles, but once per variadic family (the same series twice).
  const members = new Map();
  const seenRoles = new Set();
  const bound = new Set();
  for (const { role: name, column } of bindings) {
    const spec = resolveRole(roles, name);
    const family = roles.find(r => r.variadic && r.name === name);
    if (!spec) {
      errors.push(
        family
          ? `role '${name}' takes numbered members such as '${name}1'`
          : `unknown role '${name}'`
      );
    }
    // In the service's order: a role bound twice is an error after the unknown-role line, whatever the column.
    if (seenRoles.has(name)) errors.push(`role '${name}' is bound more than once`);
    seenRoles.add(name);
    if (!spec) continue;
    const held = members.get(spec.name) ?? new Set();
    if (!columns.has(column)) errors.push(`column '${column}' is not in the dataset`);
    else if (spec.variadic && held.has(column)) {
      errors.push(`column '${column}' is bound to more than one member of '${spec.name}'`);
    } else if (!accepts(spec, columns.get(column).dtype)) {
      errors.push(
        `role '${name}' needs ${spec.kinds.join(' or ')} data, but column '${column}' is ${columns.get(column).dtype}`
      );
    } else bound.add(spec.name);
    // Only a column the dataset has counts as a family member's, as `check_bindings` keeps it.
    if (spec.variadic && columns.has(column)) members.set(spec.name, held.add(column));
  }
  const missing = roles.filter(r => r.required && !bound.has(r.name)).map(r => r.name);
  return { errors, bindings, complete: !errors.length && !missing.length, missing_roles: missing };
}

/** Required roles first; a family takes every unused numeric column, a single role the first fit. */
function defaultBindings(session, profile) {
  const roles = SPECS[session.specId].roles;
  const used = new Set();
  const bindings = [];
  const order = [...roles.filter(r => r.required), ...roles.filter(r => !r.required)];
  for (const spec of order) {
    const free = profile.columns.filter(c => !used.has(c.name) && accepts(spec, c.dtype));
    if (spec.variadic) {
      const numeric = free.filter(c => c.dtype !== 'datetime');
      numeric.slice(0, 12).forEach((c, i) => {
        bindings.push({ role: `${spec.name}${i + 1}`, column: c.name });
        used.add(c.name);
      });
    } else if (free.length) {
      bindings.push({ role: spec.name, column: free[0].name });
      used.add(free[0].name);
    }
  }
  return bindings;
}

// The helpers below read `dataset` and `bindings` from whatever holds them: the
// session while a run is in progress, or a version afterwards. A version keeps the
// dataset and bindings it was made from (the session replaces, never mutates,
// both on a reparse or a binding change), so its code, its CSV and a later theme
// render stay its own after the admin pastes new data, like the real service's
// stored run form.

function csvText(holder) {
  const quote = cell => (/[",\n]/.test(cell) ? `"${cell.replace(/"/g, '""')}"` : cell);
  return [holder.dataset.header, ...holder.dataset.rows]
    .map(row => row.map(quote).join(','))
    .join('\n')
    .concat('\n');
}

const columnOf = (holder, name) => holder.bindings.find(b => b.role === name)?.column;
/** The bound y columns: `y` of scatter-basic, or every member `y1, y2, ...` of line-multi. */
const yColumns = holder => holder.bindings.filter(b => /^y\d*$/.test(b.role)).map(b => b.column);

/** One point list per y column; a non-numeric x (a date) plots by row order. */
function points(holder) {
  const names = holder.dataset.header;
  const x = names.indexOf(columnOf(holder, 'x'));
  if (x < 0) return null;
  return yColumns(holder).map(column => {
    const y = names.indexOf(column);
    return holder.dataset.rows
      .map((row, index) => [
        Number.isFinite(Number(row[x])) ? Number(row[x]) : index,
        Number(row[y]),
      ])
      .filter(([a, b]) => Number.isFinite(a) && Number.isFinite(b));
  });
}

function plotPy(session, version) {
  const x = columnOf(version, 'x') ?? 'x';
  const y = yColumns(version)[0] ?? 'y';
  const markerSize = version.number > 1 ? 160 : 110;
  return `# Adapted by anyplot.ai from ${session.specId} (${version.library}) for your data.csv; run: \`ANYPLOT_THEME=${version.theme} python plot.py\`
import os

import matplotlib.pyplot as plt
import pandas as pd

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
GRID = "#E4E1D8" if THEME == "light" else "#33332E"
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

df = pd.read_csv("data.csv")

fig, ax = plt.subplots(figsize=(16, 9), dpi=200, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.scatter(df[${JSON.stringify(x)}], df[${JSON.stringify(y)}], s=${markerSize}, alpha=0.7, color=IMPRINT[0], edgecolor=PAGE_BG, linewidth=0.8)
ax.set_xlabel(${JSON.stringify(x)}, fontsize=20, color=INK)
ax.set_ylabel(${JSON.stringify(y)}, fontsize=20, color=INK)
ax.set_title("", fontsize=24, color=INK)
ax.tick_params(colors=INK, labelsize=16)
ax.grid(True, color=GRID, linewidth=1)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK)

fig.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)
`;
}

/** A JavaScript version's exported code: the run form under the JavaScript header (`code/export.py`). */
function plotJs(session, version) {
  const x = columnOf(version, 'x') ?? 'x';
  const y = yColumns(version)[0] ?? 'y';
  return `// Adapted by anyplot.ai from ${session.specId} (${version.library}) for your data.csv;
// run: open plot.html in a browser, which runs this code with the chart library, the ${version.theme} theme and your data

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

const data = window.ANYPLOT_DATA;
const X = ${JSON.stringify(x)};
const Y = ${JSON.stringify(y)};

const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);
new Chart(canvas, {
  type: "scatter",
  data: { datasets: [{ data: data.map((d) => ({ x: d[X], y: d[Y] })), backgroundColor: t.palette[0] }] },
  options: { animation: false, scales: { x: { title: { display: true, text: X } }, y: { title: { display: true, text: Y } } } },
});
`;
}

/** The harness's sandbox policy (`render.mjs`, `CONTENT_SECURITY_POLICY`), which the page carries. */
const PAGE_POLICY =
  "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; " +
  "form-action 'none'; base-uri 'none'";
const PAGE_BACKGROUNDS = { light: '#FAF8F1', dark: '#1A1A17' };
const PAGE_INK = { light: '#1A1A17', dark: '#F0EFE8' };
const PAGE_SCALES = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25];
/** What could close the page's JSON element or break its script, escaped as the harness does (`render.mjs`). */
const SCRIPT_BREAKING = new RegExp('[<\\u2028\\u2029]', 'g');

/**
 * A stand-in for the harness's page of a JavaScript version in `theme`: the policy, the typed table in a
 * JSON element (`<` and the line separators escaped), and a small inline script that draws the bound x
 * and y on a canvas with a hover readout, instead of the library bundle (no code of the version runs).
 */
function chartPage(version, theme) {
  const series = points(version)?.[0] ?? [];
  const table = JSON.stringify({ columns: ['x', 'y'], data: series }).replace(
    SCRIPT_BREAKING,
    char => `\\u${char.charCodeAt(0).toString(16).padStart(4, '0')}`
  );
  const ink = PAGE_INK[theme];
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta http-equiv="Content-Security-Policy" content="${PAGE_POLICY}" />
<title>anyplot</title>
<style>
  html, body { margin: 0; padding: 0; background: ${PAGE_BACKGROUNDS[theme]}; overflow: hidden; }
  #container { width: 1600px; height: 900px; position: relative; color: ${ink}; font: 24px sans-serif; }
  #readout { position: absolute; top: 24px; right: 40px; }
</style>
</head>
<body>
<div id="container" data-library="${version.library}" data-theme="${theme}"><canvas width="1600" height="900"></canvas><div id="readout"></div></div>
<script type="application/json" id="anyplot-data">${table}</script>
<script>
  window.__anyplotError = null;
  var table = JSON.parse(document.getElementById("anyplot-data").textContent);
  var canvas = document.querySelector("canvas");
  var context = canvas.getContext("2d");
  var xs = table.data.map(function (p) { return p[0]; });
  var ys = table.data.map(function (p) { return p[1]; });
  var span = function (values) { var lo = Math.min.apply(null, values), hi = Math.max.apply(null, values); return [lo, hi === lo ? lo + 1 : hi]; };
  var sx = span(xs.length ? xs : [0]), sy = span(ys.length ? ys : [0]);
  var px = function (v) { return 100 + (v - sx[0]) / (sx[1] - sx[0]) * 1400; };
  var py = function (v) { return 800 - (v - sy[0]) / (sy[1] - sy[0]) * 700; };
  context.strokeStyle = ${JSON.stringify(ink)};
  context.lineWidth = 2;
  context.beginPath(); context.moveTo(100, 100); context.lineTo(100, 800); context.lineTo(1500, 800); context.stroke();
  context.fillStyle = "#009E73";
  table.data.forEach(function (p) { context.beginPath(); context.arc(px(p[0]), py(p[1]), 9, 0, 2 * Math.PI); context.fill(); });
  canvas.addEventListener("mousemove", function (event) {
    var box = canvas.getBoundingClientRect(), mx = (event.clientX - box.left) * 1600 / box.width, best = null;
    table.data.forEach(function (p) { if (best === null || Math.abs(px(p[0]) - mx) < Math.abs(px(best[0]) - mx)) best = p; });
    document.getElementById("readout").textContent = best ? "x " + best[0] + ", y " + best[1] : "";
  });
</script>
</body>
</html>`;
}

/**
 * The downloadable `plot.html` (`agents/anyplot/render/page.py`, `wrap_page`): no script of its own, the
 * page's policy plus `frame-src 'none'`, and the page in a single-quoted `srcdoc` of a frame sandboxed to
 * `allow-scripts`, scaled down in steps by media queries until it fits the window.
 */
function wrapPage(page, theme, title) {
  const [width, height] = [1600, 900];
  const rules = [
    `.frame { width: ${width}px; height: ${height}px; }`,
    `iframe { width: ${width}px; height: ${height}px; transform-origin: 0 0; }`,
  ];
  PAGE_SCALES.slice(1).forEach((scale, index) => {
    const larger = PAGE_SCALES[index];
    rules.push(
      `@media (max-width: ${Math.round(width * larger) + 31}px), (max-height: ${Math.round(height * larger) + 31}px) { ` +
        `.frame { width: ${Math.round(width * scale)}px; height: ${Math.round(height * scale)}px; } ` +
        `iframe { transform: scale(${scale}); } }`
    );
  });
  const escaped = page.replace(/&/g, '&amp;').replace(/'/g, '&#39;');
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta http-equiv="Content-Security-Policy" content="${PAGE_POLICY}; frame-src 'none'" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${title}</title>
<style>
  html, body { margin: 0; padding: 0; background: ${PAGE_BACKGROUNDS[theme]}; }
  .frame { margin: 16px auto; overflow: hidden; }
  iframe { display: block; border: 0; }
  ${rules.join('\n  ')}
</style>
</head>
<body>
<div class="frame"><iframe sandbox="allow-scripts" title="${title}" srcdoc='${escaped}'></iframe></div>
</body>
</html>
`;
}

/** The headers both download routes set on `plot.html` (`agents/main.py` and the BFF, `PAGE_HEADERS`). */
const PAGE_HEADERS = {
  'Content-Disposition': 'attachment; filename="plot.html"',
  'Content-Security-Policy': 'sandbox',
  'X-Content-Type-Options': 'nosniff',
  'Cache-Control': 'private, no-store',
  'Referrer-Policy': 'no-referrer',
};

/** A version's artifacts in the service's order: the rendered PNGs, the code, a JavaScript plot's page, the data. */
function artifactNames(version) {
  const pngs = ['light', 'dark'].filter(t => version.pngs[t]).map(t => `plot-${t}.png`);
  return isJs(version.library)
    ? [...pngs, 'plot.js', 'plot.html', 'data.csv']
    : [...pngs, 'plot.py', 'data.csv'];
}

// ---------------------------------------------------------------- sessions

const sessions = new Map();
let waitingTurns = 0;
let runsInFlight = 0;
/** When the mock started, the usage book's `started_at`. */
const MOCK_STARTED_AT = new Date().toISOString();

/** The next 00:00 UTC, when the service's day budget starts again (`ledger.next_reset`). */
function nextUtcMidnight(now = new Date()) {
  return new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1)
  ).toISOString();
}

function renderVersion(session, version, theme) {
  version.pngs[theme] = drawPlot(theme, points(version), {
    firstColor: version.number > 1 ? 2 : 0,
    footer: session.specId,
  });
}

// ---------------------------------------------------------------- HTTP helpers

function cors(req, res) {
  const origin = req.headers.origin;
  if (origin && /^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Vary', 'Origin');
  }
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'Content-Type, Accept, Last-Event-ID, X-Anyplot-Client, X-Admin-Token, X-Anyplot-Anon, X-Anyplot-Session, X-Turnstile-Token'
  );
  res.setHeader('Access-Control-Expose-Headers', 'X-Request-Id');
}

function json(res, status, body, ref) {
  const headers = { 'Content-Type': 'application/json', 'Cache-Control': 'private, no-store' };
  if (ref) headers['X-Request-Id'] = ref;
  res.writeHead(status, headers);
  res.end(JSON.stringify(body));
}

function fail(res, status, detail, ref) {
  json(res, status, ref ? { detail, ref } : { detail }, ref);
}

async function readBody(req) {
  const chunks = [];
  for await (const part of req) chunks.push(part);
  const text = Buffer.concat(chunks).toString('utf8');
  return text ? JSON.parse(text) : null;
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// ---------------------------------------------------------------- the chat turn

async function streamTurn(req, res, session, body, ref, siteTheme = null) {
  const text = typeof body.text === 'string' ? body.text : '';
  const lower = text.toLowerCase();
  let closed = false;
  // The edge lost the connection (MOCK_CUT_AFTER): the turn runs on, its events go to the log alone.
  let detached = false;
  req.on('close', () => {
    if (!detached) closed = true;
  });
  res.writeHead(200, {
    'Content-Type': 'text/event-stream; charset=utf-8',
    'Cache-Control': 'private, no-store',
    'X-Request-Id': ref,
    'X-Accel-Buffering': 'no',
  });
  const log = {
    runId: randomBytes(8).toString('hex'),
    events: [],
    ended: false,
    readers: new Set(),
  };
  session.turnLog = log;
  const send = (event, data) => {
    // The bundle's transcript: the user's words or action and the assistant's replies.
    if (event === 'message') session.transcript.push({ role: 'assistant', text: data.text });
    const numbered = `id: ${log.runId}.${log.events.length + 1}\nevent: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
    log.events.push(numbered);
    for (const reader of log.readers) reader();
    if (!closed && !detached) res.write(numbered);
    if (
      CUT_AFTER &&
      !session.cutDone &&
      PLOT_ACTIONS.has(body.action) &&
      log.events.length === CUT_AFTER
    ) {
      session.cutDone = true;
      detached = true;
      res.destroy();
    }
  };
  session.transcript.push({
    role: 'user',
    text: body.action ? (ACTION_MESSAGES[body.action] ?? `[action] ${body.action}`) : text,
  });
  // The user turn's number, which a version and a remembered decision carry (`newer` of a switch).
  session.turns += 1;
  const ping = () => {
    if (!closed && !detached) res.write(': ping\n\n');
  };
  const stopped = () => closed || session.cancelled;
  // Like the real queue, a cancel or a disconnect ends the wait at once.
  const wait = async ms => {
    for (let left = ms; left > 0 && !stopped(); left -= 100) await sleep(Math.min(100, left));
  };
  session.active = true;
  session.cancelled = false;
  session.changed = null; // set by a data change of this turn, carried in `done.dataset`
  // What the turn changed (`done.turn`, the service's `stream.turn_outcome`): `answer` until a path
  // names its change; `null` for a refusal or an error, whose `done` carries none, as a stop's.
  let turn = 'answer';
  // The language the scope judge found in the typed message, offered with `done` (`offerLanguage`).
  let turnOffer = null;
  try {
    send('ready', { v: 'anyplot/1', run_id: log.runId });
    // Pretend `QUEUE_START - 1` other turns wait ahead of this one.
    let queued = Math.max(0, QUEUE_START);
    waitingTurns += queued;
    try {
      for (let position = queued; position >= 1; position -= 1) {
        send('status', { step: 'queued', position, waiting: waitingTurns });
        await wait(QUEUE_MS / 2);
        ping();
        await wait(QUEUE_MS / 2);
        waitingTurns -= 1;
        queued -= 1;
        if (stopped()) return;
      }
    } finally {
      waitingTurns -= queued;
    }
    // The wait's end, as the service's `TurnSlot.take` sends it once a turn that waited holds its slot.
    if (QUEUE_START > 0) send('status', { step: 'started' });
    runsInFlight += 1;
    try {
      // The scope judge's detection (a typed message it accepts) and the root's
      // `set_language`, in miniature; `done` carries the result. A message the
      // judge refuses is refused as a whole: it never reaches the root, so it
      // neither detects nor sets a language.
      const outOfScope = /weather|joke/.test(lower);
      // A request for figures to fetch is `needs_data`, except in the note sent with a paste,
      // which is about the data that came with it.
      const needsData =
        /stock price|unemployment rate/.test(lower) && !(session.summaryPending && session.dataset);
      if (typeof body.text === 'string' && !outOfScope && !needsData) {
        turnOffer = offerLanguage(session, text, text.trim().split(/\s+/).length);
      }
      const asked = outOfScope || needsData ? null : requestedLanguage(lower);
      if (asked) {
        session.language = asked.code;
        session.languageSource = 'chosen';
        // The root's `set_language`; a data change or a plot of the same turn names the turn first.
        turn = 'language';
        if (session.versions.length === 0) {
          await sleep(STEP_MS);
          send('message', {
            text: `From now on the plot text and my replies are in ${asked.name}; the next plot uses it.`,
          });
          return;
        }
        // With a plot, the root then makes the next version in the new language.
      }
      if (body.action === 'summarize_data') {
        await sleep(STEP_MS * 2);
        session.summaryPending = false;
        send('message', { text: summarizeData(session) });
        return;
      }
      // The note typed with the attachment, the first turn on the paste: the summary, then the note acted on.
      if (
        typeof body.text === 'string' &&
        session.summaryPending &&
        session.dataset &&
        !outOfScope
      ) {
        await sleep(STEP_MS * 2);
        const summary = summarizeData(session);
        const year = lower.match(/\b(?:nur|only)\s+(\d{4})\b/);
        // A plot wish in the note (a title, a label, a scale…) is kept for the first plot, as the
        // root's `keep_plot_request`; a question about the data changes nothing.
        const wish = !year && plotWish(lower) && !libraryHasPlotOfThisData(session);
        const acted = year
          ? keepYear(session, year[1])
          : /dezimal|decimal comma|tausender|thousands/.test(lower)
            ? dotsAsThousands(session)
            : wish
              ? keepWish(session, text)
              : `Noted: ${text.trim()}`;
        session.summaryPending = false;
        turn = session.changed ? 'data' : asked ? 'language' : wish ? 'kept' : 'answer';
        send('message', { text: `${summary} ${acted}` });
        return;
      }
      // The scope judge answers before any agent: a request for figures to fetch ends here.
      if (needsData) {
        await sleep(STEP_MS);
        turn = null;
        send('refusal', {
          code: 'needs_data',
          text: 'I cannot fetch data from the internet or any other source. Please get the data you want to plot yourself first, then paste it into the message box as a table or open its file with .open().',
        });
        return;
      }
      if (body.action === 'example_data') {
        // The root's `get_spec_brief` and a sandbox run take a few seconds: the page's working line counts them.
        await sleep(STEP_MS * 6);
        turn = 'data';
        send('message', { text: exampleData(session) });
        return;
      }
      // Code or a request for data that the dataset route sent to the chat (`422 code`,
      // `422 data_request`): the root's `run_data_code` in miniature, the same made-up table.
      if (typeof body.text === 'string' && (looksLikeCode(text) || asksForData(text))) {
        await sleep(STEP_MS * 4);
        turn = 'data';
        send('message', { text: exampleData(session, looksLikeCode(text)) });
        return;
      }
      const size = wideTableSize(lower);
      if (size) {
        await sleep(STEP_MS * 2);
        turn = 'data';
        send('message', { text: generateWideTable(session, size) });
        return;
      }
      if (asksForFormula(lower)) {
        await sleep(STEP_MS * 2);
        turn = 'data';
        send('message', { text: generateData(session, lower) });
        return;
      }
      const change = /prozent|percent/.test(lower)
        ? setTypeNumber
        : /gruppier|group/.test(lower)
          ? s => aggregateSum(s, lower)
          : /umbenenn|rename/.test(lower)
            ? s => renameSecond(s, /umbenenn/.test(lower))
            : null;
      if (change) {
        await sleep(STEP_MS * 2);
        if (!session.dataset) {
          send('message', { text: 'Paste your data first.' });
          return;
        }
        const reply = change(session);
        if (session.changed) turn = 'data';
        // "instead of" plays the root that read the change as a plot change too and called the
        // plot after its own data change: the server refuses it, before the turn's `done`.
        if (/instead of|statt/.test(lower)) {
          send('plot', {
            status: 'not_ready',
            reason: 'data_unconfirmed',
            attempts: 0,
            artifacts: [],
            changes: [],
            residual_defects: [],
          });
        }
        send('message', { text: reply });
        return;
      }
      if (outOfScope) {
        await sleep(STEP_MS);
        turn = null;
        send('refusal', {
          code: 'out_of_scope',
          text: 'I can only help with this plot and your data for it: choosing columns, adapting, styling and exporting the plot, and questions about its code.',
        });
        return;
      }
      if (lower.includes('busy')) {
        await sleep(STEP_MS);
        turn = null;
        send('error', { code: 'capacity', ref });
        return;
      }
      if (lower.includes('swap')) {
        await sleep(STEP_MS);
        turn = 'data';
        send('message', { text: swapBindings(session) });
        return;
      }
      if (text.trim().endsWith('?')) {
        await sleep(STEP_MS * 2);
        send('message', {
          text:
            session.language === 'de'
              ? 'Die x-Achse zeigt die Spalte, die du x zugeordnet hast; die Markergröße ist das Argument s= von ax.scatter, Zeile 18 von plot.py.'
              : 'The x axis uses the column you bound to x; the marker size is the s= argument of ax.scatter, line 18 of plot.py.',
        });
        return;
      }
      if (!session.dataset || !session.complete || !session.confirmed) {
        await sleep(STEP_MS);
        const reason = !session.dataset
          ? 'no_dataset'
          : !session.complete
            ? 'incomplete_bindings'
            : 'data_unconfirmed';
        // A typed plot wish before the data is confirmed, while this library has no plot of this
        // data yet: the root's `keep_plot_request` keeps it for the first plot, which the stream
        // shows nothing of.
        if (
          reason === 'data_unconfirmed' &&
          typeof body.text === 'string' &&
          !libraryHasPlotOfThisData(session)
        ) {
          // A language the same message chose comes first in the service's order.
          if (turn !== 'language') turn = 'kept';
          send('message', { text: keepWish(session, text) });
          return;
        }
        // A run stopped for missing data or roles shows a failed card; one refused for unconfirmed
        // data shows none and changes nothing.
        if (reason !== 'data_unconfirmed') turn = 'plot';
        send('plot', {
          status: 'not_ready',
          reason,
          attempts: 0,
          artifacts: [],
          changes: [],
          residual_defects: [],
        });
        send('message', {
          text:
            reason === 'data_unconfirmed'
              ? 'Check the preview and the bindings, then press .create_plot().'
              : 'Paste your data and bind the required roles first.',
        });
        return;
      }
      // `create_plot` and `carry_plot` start from the catalogue code; a typed change refines the latest version.
      const refine = body.action !== 'create_plot' && body.action !== 'carry_plot';
      // A refinement repairs once; with MOCK_REPAIR=1 a first plot does too, as a first try the review fails.
      const repaired = refine || REPAIR;
      const steps = repaired
        ? [
            ['adapting', 1],
            ['checking', 1],
            ['rendering', 1],
            ['reviewing', 1],
            ['repairing', 2],
            ['checking', 2],
            ['rendering', 2],
            ['reviewing', 2],
          ]
        : [
            ['adapting', 1],
            ['checking', 1],
            ['rendering', 1],
            ['reviewing', 1],
          ];
      // How each round ends, as the service's `PlotResult.rounds`: a repaired run's first try has
      // two review findings, its repair round one that stays open; a first plot passes at once.
      const rounds = repaired
        ? [
            {
              attempt: 1,
              outcome: 'review',
              findings: 2,
              step: 'reviewing',
              shipped: false,
              defects: ['VQ-01', 'VQ-05'],
            },
            { attempt: 2, outcome: 'review', findings: 1, step: 'reviewing', shipped: true },
          ]
        : [{ attempt: 1, outcome: 'ok', findings: 0, step: 'reviewing', shipped: true }];
      // The run's start before its first step (the root's call that hands over to the pipeline).
      await wait(START_MS);
      for (const [step, attempt] of steps) {
        if (stopped()) return;
        // The step that opens a repair round says how the round before it ended.
        const before = step === 'repairing' ? rounds[attempt - 2] : null;
        // The run's round cap rides on every step, as the service's `pipeline.run` sends it.
        const cap = MAX_ATTEMPTS ? { max_attempts: MAX_ATTEMPTS } : {};
        send(
          'status',
          before
            ? {
                step,
                attempt,
                ...cap,
                outcome: before.outcome,
                findings: before.findings,
                defects: before.defects ?? [],
              }
            : { step, attempt, ...cap }
        );
        await wait(STEP_MS);
        // A stopped run finishes the step in progress before it ends.
        if (session.cancelled && !closed) await sleep(STOP_MS);
      }
      if (stopped()) return;
      // The service's `pipeline.run_theme`: a theme asked for (the word "dark" or "light" in the text), the
      // asked theme of the version a refinement changes, the site theme of the turn, else the version it
      // changes or light.
      // The version a refinement changes is this library's latest, as `latest_rendered(library=)` picks it.
      const previous = refine
        ? session.versions.findLast(item => item.library === session.library)
        : undefined;
      // A switch's carry for this library (`switch.Carry`): the first run here takes it, a fresh
      // `create_plot` never does; it brings the theme the user asked for in the library before.
      const carried =
        session.carry?.target === session.library && body.action !== 'create_plot'
          ? session.carry
          : null;
      let askedTheme = previous?.themeAsked ? previous.theme : (carried?.theme ?? null);
      if (/\blight\b/.test(lower)) askedTheme = 'light';
      else if (/\bdark\b/.test(lower)) askedTheme = 'dark';
      const theme = askedTheme ?? siteTheme ?? previous?.theme ?? 'light';
      const version = {
        number: session.versions.length + 1,
        library: session.library,
        // The user turn it shipped in: a switch counts the decisions remembered after it (`newer`).
        turn: session.turns,
        theme,
        themeAsked: askedTheme !== null,
        dataset: session.dataset,
        // The data version it drew (`CodeVersion.data_version`).
        dataNumber: session.version,
        bindings: session.bindings,
        // The session language the version's text was written in, as the service keeps it.
        language: session.language,
        pngs: {},
      };
      renderVersion(session, version, theme);
      // The library's first plot of this data: a wish kept for it in step 1 is its request.
      const firstHere = !libraryHasPlotOfThisData(session);
      session.versions.push(version);
      const x = columnOf(version, 'x');
      const y = yColumns(version).join(', ');
      // Kept on the version for the bundle, like the service's stored `PlotResult`.
      version.result = {
        status: repaired ? 'needs_attention' : 'ok',
        reason: null,
        attempts: repaired ? 2 : 1,
        artifacts: artifactNames(version),
        changes: refine
          ? ['Applied your change request', 'Marker size raised from 110 to 160']
          : [`x now reads ${x}, y reads ${y}`, 'Axis labels name your columns'],
        // In the review's grammar, as the service writes them: the card reads them in plain words.
        residual_defects: repaired
          ? [
              'VQ-03 (light): two markers overlap the y axis label → every marker clear of the label (+6 px). Likely cause: the y axis limits in ax.set_ylim.',
              'VQ-01 (light): the tick labels are set at 7 pt → 8 pt or larger (+1 pt). Likely cause: labelsize=7 in ax.tick_params.',
            ]
          : [],
        // The stored version's number, which the artifact and theme routes take.
        version: version.number,
        rounds,
      };
      // The plot memory, settled with the version before its event (`pipeline.settle_memory`): a
      // typed change keeps its decision, the first plot of a library the wish kept for it in step
      // 1, a start over keeps the memory as it is (only the user clears it), and the switch's carry
      // is spent. The event names what the version stands on (`pipeline.memory_ids`): the kept
      // entries from before the run and the added ones; one a change replaced is in neither.
      const before = new Set(session.memory.map(entry => entry.id));
      if (refine) rememberChange(session, text);
      else if (session.keptWish && firstHere) {
        rememberChange(session, session.keptWish);
        session.keptWish = null;
      }
      if (carried) session.carry = null;
      if (MEMORY_FIELD) {
        version.result.memory = {
          kept: session.memory.filter(entry => before.has(entry.id)).map(entry => entry.id),
          added: session.memory.filter(entry => !before.has(entry.id)).map(entry => entry.id),
        };
      }
      turn = 'plot';
      send('plot', version.result);
      // The root writes its reply after the plot: seconds in production (MOCK_REPLY_MS).
      await sleep(REPLY_MS ?? STEP_MS / 2);
      const decisions = session.memory.length;
      send('message', {
        text: refine
          ? 'Done. One note remains: two markers sit close to the y axis label.'
          : body.action === 'carry_plot'
            ? `Here is the plot in ${session.library}, from its catalogue code${decisions ? ` with your ${decisions} decision${decisions === 1 ? '' : 's'}` : ''}.`
            : `Here is ${SPECS[session.specId].title.toLowerCase()} with your data: ${x} on x and ${y} on y.`,
      });
    } finally {
      runsInFlight -= 1;
    }
  } finally {
    if (DONE_MS > 0 && !closed) await sleep(DONE_MS);
    session.active = false;
    // The sync fields: the session's bindings and step state after the run, and the
    // new dataset version after a turn that changed the data; what the turn changed, for a
    // turn that ended well (no refusal, no error, no stop).
    send('done', {
      llm_calls: 4,
      tokens: 18734,
      bindings: session.bindings,
      data_confirmed: session.confirmed,
      language: languageBody(session, turnOffer),
      ...(session.dataset ? { suggestion: longSuggestion(session, session.dataset) } : {}),
      ...(session.changed ? { dataset: session.changed } : {}),
      ...(turn && !session.cancelled && !closed ? { turn } : {}),
    });
    log.ended = true;
    for (const reader of log.readers) reader();
    res.end();
  }
}

/** The turns MOCK_CUT_AFTER cuts: a session's first plot turn only, so its next one runs through. */
const PLOT_ACTIONS = new Set(['create_plot', 'carry_plot']);

/**
 * `GET .../turn`: the session's latest turn after the event `Last-Event-ID` names, then live until
 * it ends, with a ping every 15 s, as the agents service's turn log answers it.
 */
function readTurn(req, res, session, ref) {
  const named = /^([0-9a-f]{16})\.([0-9]{1,6})$/.exec(req.headers['last-event-id'] ?? '');
  if (!named) return fail(res, 422, 'invalid', ref);
  const log = session.turnLog;
  if (!log || log.runId !== named[1] || Number(named[2]) > log.events.length) {
    return fail(res, 404, 'not_found', ref);
  }
  session.resumeFailed ??= 0;
  if (session.resumeFailed < RESUME_FAILS) {
    session.resumeFailed += 1;
    req.socket.destroy(); // no answer at all, as while the network is gone
    return;
  }
  res.writeHead(200, {
    'Content-Type': 'text/event-stream; charset=utf-8',
    'Cache-Control': 'private, no-store',
    'X-Request-Id': ref,
    'X-Accel-Buffering': 'no',
  });
  let index = Number(named[2]);
  const flush = () => {
    while (index < log.events.length) res.write(log.events[index++]);
    if (log.ended) finish();
  };
  const ping = setInterval(() => res.write(': ping\n\n'), 15_000);
  const finish = () => {
    clearInterval(ping);
    log.readers.delete(flush);
    res.end();
  };
  log.readers.add(flush);
  req.on('close', () => {
    clearInterval(ping);
    log.readers.delete(flush);
  });
  flush();
}

// ---------------------------------------------------------------- plot memory

/** The kinds a single entry holds (`memory.py`): a new one of the same kind and target replaces it. */
const ADDITIVE_KINDS = new Set(['reference_line', 'annotation', 'marker', 'other']);

/**
 * The root's `remember` in miniature: a shipped change keeps one decision in the user's words, its
 * kind read from a few keywords. A full memory refuses the new entry, as the service does.
 */
/** A decision's kind, read from a few keywords of the user's words (`memory.py`'s closed set). */
function memoryKind(lower) {
  return /\btitle\b|titel/.test(lower)
    ? 'title'
    : /label|beschrift/.test(lower)
      ? 'axis_label'
      : /\blog\b|scale|skala/.test(lower)
        ? 'scale'
        : /\bline\b|linie/.test(lower)
          ? 'reference_line'
          : /colou?r|farbe|\bred\b|\bblue\b|\brot\b|\bblau\b/.test(lower)
            ? 'color'
            : /marker|star|stern/.test(lower)
              ? 'marker'
              : /annot|formula|formel/.test(lower)
                ? 'annotation'
                : /\bdark\b|\blight\b/.test(lower)
                  ? 'theme'
                  : 'other';
}

/** Whether a message is a wish for the plot (a title, a label, a scale…), not a question. */
const plotWish = lower => !lower.trim().endsWith('?') && memoryKind(lower) !== 'other';

/** Whether the session's library has a plot yet. */
const libraryHasPlot = session => session.versions.some(item => item.library === session.library);

/**
 * Whether the library has a plot of the current data: a version whose data number is the paste's
 * or later (`CodeVersion.earlier_data` on the service). A wish for the first plot of this data is
 * kept until then, also when the library has a plot of data a new paste replaced (2026-11-08).
 */
const libraryHasPlotOfThisData = session =>
  session.versions.some(
    item => item.library === session.library && (item.dataNumber ?? 0) >= session.first
  );

/**
 * The root's `keep_plot_request` in miniature: a plot wish before the data is confirmed is kept
 * for the library's first plot (`session.keptWish`, the service's held request), which changes
 * nothing the stream shows; that plot keeps its decision once it shipped. Answers the reply's line.
 */
function keepWish(session, text) {
  const words = text.trim().replace(/\s+/g, ' ');
  session.keptWish = words;
  return `I kept "${words}" for the first plot.`;
}

function rememberChange(session, text) {
  const words = text.trim().replace(/\s+/g, ' ');
  if (!words) return;
  const lower = words.toLowerCase();
  const kind = memoryKind(lower);
  const target = /\by\b|y-ax/.test(lower) ? 'y' : /\bx\b|x-ax/.test(lower) ? 'x' : null;
  const kept = ADDITIVE_KINDS.has(kind)
    ? session.memory
    : session.memory.filter(entry => !(entry.kind === kind && entry.target === target));
  if (kept.length >= MAX_MEMORY_ENTRIES) return;
  session.memorySeq += 1;
  session.memory = [
    ...kept,
    {
      id: `m${session.memorySeq}`,
      kind,
      target,
      text: words.slice(0, MAX_MEMORY_TEXT_CHARS),
      expect: null,
      turn: session.turns,
    },
  ];
}

/** `GET` and `DELETE .../memory`'s answer. */
const memoryPayload = session => ({
  entries: session.memory,
  max_entries: MAX_MEMORY_ENTRIES,
  written: session.memorySeq > 0,
});

// ---------------------------------------------------------------- session language

/** The service's `LANGUAGE_PATTERN` (`agents/anyplot/language.py`). */
const LANGUAGE_RE = /^[A-Za-z][A-Za-z -]{0,39}$/;
/** The English names and endonyms the service stores as their code. */
const LANGUAGE_NAMES = {
  english: 'en',
  german: 'de',
  deutsch: 'de',
  french: 'fr',
  francais: 'fr',
  spanish: 'es',
  espanol: 'es',
  italian: 'it',
  italiano: 'it',
  portuguese: 'pt',
  portugues: 'pt',
  dutch: 'nl',
  nederlands: 'nl',
  polish: 'pl',
  polski: 'pl',
  chinese: 'zh',
  vietnamese: 'vi',
  russian: 'ru',
  japanese: 'ja',
};

/** The service's `normalise`: one space between words, a known name as its code, a code in lower case. */
function normaliseLanguage(value) {
  const text = value.split(/\s+/).filter(Boolean).join(' ');
  const code = LANGUAGE_NAMES[text.toLowerCase()];
  if (code) return code;
  return text.length === 2 ? text.toLowerCase() : text;
}

const GERMAN = /[äöüß]|\b(bitte|und|der|die|das|mit|zeichne|beschriftung|mach)\b/i;

/**
 * The service's `language.offer`, in miniature: the judges' `lang` (`de` for German text,
 * else `en`) never sets the session language, it is offered once, as `{language, basis}`,
 * and recorded as offered. `words` is a typed message's word count, `null` for a paste's
 * notes and column names. Nothing after a pick (`chosen`), nothing for the session's own
 * language or one offered before, and `en` only for a message of three words or more (the
 * judge also answers `en` when it cannot tell, so "sin x" offers nothing), never for data.
 */
function offerLanguage(session, text, words) {
  if (session.languageSource === 'chosen') return null;
  const code = GERMAN.test(text) ? 'de' : 'en';
  if (code === session.language || session.languageOffered.includes(code)) return null;
  if (code === 'en' && (words === null || words < 3)) return null;
  session.languageOffered.push(code);
  return { language: code, basis: words === null ? 'data' : 'message' };
}

/**
 * The session language as the service answers it, `{language, source}`, with `offer` while it
 * holds: never after a pick (the root's `set_language` may have made one in the same turn) and
 * never for the language the session has now.
 */
function languageBody(session, offer) {
  const body = { language: session.language, source: session.languageSource };
  if (offer && session.languageSource !== 'chosen' && offer.language !== session.language) {
    body.offer = offer;
  }
  return body;
}

const ASKED_LANGUAGES = {
  english: ['en', 'English'],
  englisch: ['en', 'English'],
  german: ['de', 'German'],
  deutsch: ['de', 'German'],
  french: ['fr', 'French'],
  französisch: ['fr', 'French'],
  spanish: ['es', 'Spanish'],
  spanisch: ['es', 'Spanish'],
};

/**
 * "labels in german", "beschriftung auf englisch", "auf deutsch bitte": the root's
 * `set_language` request, or `null`.
 */
function requestedLanguage(lower) {
  const match =
    lower.match(/\blabels? in (english|german|french|spanish)\b/) ??
    lower.match(/\bbeschriftung (?:bitte )?auf (deutsch|englisch|französisch|spanisch)/) ??
    lower.match(/^\s*auf (deutsch|englisch|französisch|spanisch)(?: bitte)?\W*$/);
  if (!match) return null;
  const [code, name] = ASKED_LANGUAGES[match[1]];
  return { code, name };
}

/**
 * The root's `set_bindings` in miniature: swap the columns of `x` and the first
 * `y`, as the binding check allows it. An applied change drops the confirmation.
 */
function swapBindings(session) {
  const x = session.bindings.find(b => b.role === 'x');
  const y = session.bindings.find(b => /^y1?$/.test(b.role));
  if (!session.dataset || !x || !y) return 'There is nothing to swap yet: paste your data first.';
  const swapped = session.bindings.map(b =>
    b === x ? { ...b, column: y.column } : b === y ? { ...b, column: x.column } : b
  );
  const { errors, complete } = checkBindings(session, swapped);
  if (errors.length) return `I cannot swap them: ${errors[0]}.`;
  session.bindings = swapped;
  session.complete = complete;
  session.confirmed = false;
  return `Swapped: x now reads ${y.column} and ${y.role} reads ${x.column}. Check the bindings, then press .create_plot().`;
}

// ---------------------------------------------------------------- data versions (prepare_data in miniature)

const MAX_DATASET_HISTORY = 5;

/** The CSV of a header and rows, for a re-parse through `parseDataset` after an operation. */
function toCsv(header, rows) {
  const quote = cell => (/[",\n]/.test(cell) ? `"${cell.replace(/"/g, '""')}"` : cell);
  return [header, ...rows].map(row => row.map(quote).join(',')).join('\n') + '\n';
}

/**
 * `carry_bindings`: the bindings still valid for the new profile stay, the roles left
 * (a family counts as bound while one member stays) get the defaults, computed on the
 * columns no kept binding uses, so a role whose first choice is taken gets its next one.
 */
function carryBindings(session, bindings, profile) {
  const holder = { specId: session.specId, dataset: { profile } };
  const kept = bindings.filter(b => !checkBindings(holder, [b]).errors.length);
  if (kept.length === bindings.length) return bindings;
  const used = new Set(kept.map(b => b.column));
  const bound = new Set(kept.map(b => b.role.replace(/\d+$/, '')));
  const free = { ...profile, columns: profile.columns.filter(c => !used.has(c.name)) };
  for (const b of defaultBindings(session, free)) {
    if (!bound.has(b.role.replace(/\d+$/, ''))) kept.push(b);
  }
  return kept;
}

/** Store `parsed` as the session's next dataset version; the previous one joins the history (at most five). */
function storeVersion(session, parsed, changes) {
  session.history.push({
    dataset: session.dataset,
    bindings: session.bindings,
    number: session.version,
  });
  session.history = session.history.slice(-MAX_DATASET_HISTORY);
  session.dataset = parsed;
  session.bindings = carryBindings(session, session.bindings, parsed.profile);
  session.complete = checkBindings(session, session.bindings).complete;
  session.confirmed = false; // the user confirms every version they see
  session.top += 1;
  session.version = session.top;
  session.changed = { ...datasetPayload(session), roles: SPECS[session.specId].roles, changes };
  // A new data version drops the switch's carry and a wish kept for the first plot, as the
  // service's version delta does (2026-11-08).
  session.carry = null;
  session.keptWish = null;
}

/**
 * New data (a paste, a copy, a table computed without data): its first version, under the
 * session's next number, with no history to undo. A switch's carry and a kept wish go with the
 * data before.
 */
function newData(session) {
  session.history = [];
  session.top += 1;
  session.version = session.top;
  session.first = session.top;
  session.carry = null;
  session.keptWish = null;
}

/**
 * `{preview, profile, bindings, warnings, version, can_undo, original_version}`: a dataset as
 * the routes and `done.dataset` answer it.
 */
function datasetPayload(session) {
  return {
    preview: session.dataset.preview,
    profile: session.dataset.profile,
    bindings: session.bindings,
    warnings: session.dataset.warnings,
    suggestion: longSuggestion(session, session.dataset),
    version: session.version,
    can_undo: session.history.length > 0,
    original_version: session.first,
  };
}

/**
 * The service's wide-table offer (`agents/anyplot/data/shape.py`): the spec wants one
 * label role and one numeric role, the table holds 2 to 20 numeric columns and no text
 * column (dates are kept as keys).
 */
function longSuggestion(session, dataset) {
  const roles = SPECS[session.specId].roles;
  const numericOnly = r => r.kinds.length === 1 && r.kinds[0] === 'numeric';
  if (roles.some(r => r.variadic && numericOnly(r))) return null;
  const single = roles.filter(r => !r.variadic && r.required);
  const labels = single.filter(
    r => r.kinds.length && r.kinds.every(kind => kind === 'categorical' || kind === 'text')
  );
  const values = single.filter(numericOnly);
  // Exactly one of each, as on the service: two labels would leave one open.
  if (labels.length !== 1 || values.length !== 1) return null;
  const columns = dataset.profile.columns;
  if (columns.some(c => c.dtype === 'text' || c.dtype === 'boolean')) return null;
  const numeric = columns.filter(c => c.dtype === 'integer' || c.dtype === 'number');
  const keys = columns.filter(c => c.dtype === 'datetime').map(c => c.name);
  if (numeric.length < 2 || numeric.length > 20 || numeric.length + keys.length !== columns.length)
    return null;
  // The new columns' names are generated text in the session language (`shape.LONG_NAMES`), as on the service.
  const words = LONG_WORDS[session.language] ?? LONG_WORDS.en;
  return {
    kind: 'to_long',
    columns: numeric.map(c => c.name),
    names_to: words[0],
    values_to: words[1],
    keys,
    rows: dataset.profile.rows * numeric.length,
  };
}

/** The `.to_long()` names column (a category) and values column by session language; English otherwise. */
const LONG_WORDS = {
  en: ['Category', 'Value'],
  de: ['Kategorie', 'Wert'],
  fr: ['Catégorie', 'Valeur'],
  es: ['Categoría', 'Valor'],
  it: ['Categoria', 'Valore'],
  pt: ['Categoria', 'Valor'],
  nl: ['Categorie', 'Waarde'],
  pl: ['Kategoria', 'Wartość'],
};

/** The unit token at either end of a cell (`12,5 %`, `€ 12`), or null; a plain number has none. */
function unitOf(cell) {
  const match = cell.match(/^(?:([^\d\s+-][^\d]*?)\s*)?[+-]?[\d.,' ]*\d(?:\s*([^\d\s][^\d]*))?$/);
  return match ? (match[1] ?? match[2] ?? null) : null;
}

/** "nur 2024", "only 2024": the rows of that year, the root's `drop_rows` in miniature, as the next version. */
function keepYear(session, year) {
  const { header, rows } = session.dataset;
  const index = header.findIndex((_, column) => rows.some(row => row[column] === year));
  if (index < 0) return `There is no ${year} in the data, so nothing changed.`;
  const kept = rows.filter(row => row[index] === year);
  const dropped = rows.length - kept.length;
  storeVersion(session, parseDataset(toCsv(header, kept)), [
    `dropped ${dropped} ${dropped === 1 ? 'row' : 'rows'} where ${header[index]} is not ${year}`,
  ]);
  return `I kept the rows of ${year}: ${kept.length} of ${rows.length}.`;
}

/** "the dots are thousands separators": a column of `1.234` shapes read again from its cells as pasted. */
function dotsAsThousands(session) {
  const { header, rows } = session.dataset;
  const index = header.findIndex(
    (_, column) =>
      rows.every(row => !row[column] || /^\d{1,3}(\.\d{3})+$|^\d+$/.test(row[column])) &&
      rows.some(row => row[column].includes('.'))
  );
  if (index < 0) return 'No column reads its dots as decimal points, so nothing changed.';
  const read = rows.map(row =>
    row.map((cell, column) => (column === index ? cell.replace(/\./g, '') : cell))
  );
  storeVersion(session, parseDataset(toCsv(header, read)), [
    `${header[index]}: ${rows.length} cells read as numbers`,
  ]);
  return `I read ${header[index]} with its dots as thousands separators.`;
}

/** `set_type number` on the second column: the unit removed, thousands separators dropped, a decimal comma read. */
function setTypeNumber(session) {
  const { header, rows } = session.dataset;
  if (header.length < 2) return 'There is no second column to read as numbers.';
  const index = 1;
  const column = header[index];
  if (session.dataset.profile.columns[index].dtype !== 'text')
    return `${column} already holds numbers; nothing changed.`;
  const decimalComma = rows.some(row => /\d,\d/.test(row[index]));
  const units = new Set();
  let failed = 0;
  const converted = rows.map(row => {
    const cell = row[index];
    if (!cell) return '';
    const unit = unitOf(cell);
    if (unit) units.add(unit);
    let body = unit ? cell.replace(unit, '').trim() : cell;
    body = body.replace(/[\s']/g, '').replace(decimalComma ? /\./g : /,/g, '');
    if (decimalComma) body = body.replace(',', '.');
    if (!/^[+-]?\d+(\.\d+)?$/.test(body)) {
      failed += 1;
      return '';
    }
    return body;
  });
  if (units.size > 1)
    return `I cannot read ${column} as numbers: it mixes ${units.size} different units.`;
  const present = rows.filter(row => row[index]).length;
  if (present && failed / present > 0.1)
    return `I cannot read ${column} as numbers: ${failed} of ${present} cells are no number.`;
  const parsed = parseDataset(
    toCsv(
      header,
      rows.map((row, i) => row.map((c, j) => (j === index ? converted[i] : c)))
    )
  );
  let change = `${column}: ${present - failed} cells read as numbers`;
  if (units.size) change += `, unit '${[...units][0]}' removed`;
  if (failed)
    change += `, ${failed} cell${failed > 1 ? 's' : ''} could not be read and ${failed > 1 ? 'are' : 'is'} now missing`;
  storeVersion(session, parsed, [change]);
  // As the root's reply after `prepare_data`: the change and its counts; the page says what to do next.
  return `I read ${column} as numbers${units.size ? ` and removed the unit '${[...units][0]}'` : ''}.`;
}

/**
 * `aggregate`: the first other numeric column summed by the column the message
 * names after "nach", "by", "per" or "pro" ("gruppier nach Monat"), else by the
 * first text column; the other columns go.
 */
function aggregateSum(session, lower) {
  const { header, rows, profile } = session.dataset;
  const escape = name => name.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const named = header.findIndex(name =>
    new RegExp(`(?:nach|by|per|pro)\\s+${escape(name)}(?![\\p{L}\\p{N}_])`, 'u').test(lower)
  );
  const key = named >= 0 ? named : profile.columns.findIndex(c => c.dtype === 'text');
  const value = profile.columns.findIndex(
    (c, i) => i !== key && (c.dtype === 'number' || c.dtype === 'integer')
  );
  if (key < 0 || value < 0) return 'I need a column to group by and a number column to sum.';
  const sums = new Map();
  for (const row of rows) {
    const number = Number(row[value]);
    if (!row[value] || !Number.isFinite(number)) continue;
    sums.set(row[key], (sums.get(row[key]) ?? 0) + number);
  }
  const grouped = [...sums.entries()]
    .sort(([a], [b]) => a.localeCompare(b, 'en', { numeric: true }))
    .map(([k, v]) => [k, String(v)]);
  if (!grouped.length) return 'There is nothing to sum.';
  const parsed = parseDataset(toCsv([header[key], header[value]], grouped));
  const other = header.length - 2;
  let change = `summed ${header[value]} by ${header[key]}: ${grouped.length} row${grouped.length > 1 ? 's' : ''}`;
  if (other) change += `, ${other} other column${other > 1 ? 's' : ''} dropped`;
  storeVersion(session, parsed, [change]);
  return `I summed ${header[value]} per ${header[key]}: ${grouped.length} rows.`;
}

/** `rename`: the second column gets a new name. */
function renameSecond(session, german) {
  const { header, rows } = session.dataset;
  if (header.length < 2) return 'There is no second column to rename.';
  const name = german ? 'Wert' : 'Value';
  if (header.includes(name)) return `A column named '${name}' already exists.`;
  const renamed = header.map((h, i) => (i === 1 ? name : h));
  const parsed = parseDataset(toCsv(renamed, rows));
  storeVersion(session, parsed, [`renamed '${header[1]}' to '${name}'`]);
  return `I renamed ${header[1]} to ${name}.`;
}

// ---------------------------------------------------------------- formulas (generate_data in miniature)

/** Whether a chat message asks for a formula: `sin(`, `cos(` or `x**2`, or `= ` with "pi", "from" or "von". */
function asksForFormula(lower) {
  return (
    /\b(?:sin|cos)\(|x\*\*2/.test(lower) ||
    (lower.includes('= ') && /\bpi\b|\bfrom\b|\bvon\b/.test(lower))
  );
}

/**
 * The dataset route's guard, a short form of the service's `looks_like_formula`. Text
 * that holds its own values (three numbers or more besides its ranges, expressions and
 * point counts) is data. Otherwise a line or sentence of at most 300 characters asks
 * for a formula with a call whose argument holds a variable (`sin(x)`, never `Max(3)`),
 * an assignment of an expression to a short name (`y = x**2`, never `Äpfel = 3x`), or
 * a range phrase with numbers or pi next to pi, a one-letter variable before it, a
 * power (never a unit such as `m²`) or a curve's name such as "Parabel" (never a word
 * that data has as well, such as "curve" or "Quadratmeter").
 */
function looksLikeFormula(text) {
  const trimmed = text.trim();
  if (!trimmed || trimmed.length > 4000) return false;
  const lines = trimmed.split(/\r\n|\r|\n/).filter(line => line.trim());
  const delimiter = [',', ';', '\t', '|'].find(mark => lines[0].includes(mark));
  if (lines.length > 1 && delimiter && lines.filter(line => line.includes(delimiter)).length >= 2) {
    return false; // a table, perhaps a broken one
  }
  const end = String.raw`[-+]?\s*(?:\d+(?:[.,]\d+)?\s*\*?\s*(?:pi)?|pi)`;
  const phrase = String.raw`\b(?:from|von|between|zwischen)\s+(${end})\s+(?:to|bis|and|und)\s+(${end})(?!\w)`;
  const range = new RegExp(phrase, 'gi');
  const call = /(?<![\w.])(?:sin|cos|tan|exp|log|sqrt|abs|min|max)\s*\(([^()]*)\)/gi;
  const stop = String.raw`(?=\s+(?:from|von|for|für|mit|with)\b|[,;\n]|$)`;
  const name = String.raw`(?<![\w.])(?:[a-z]\w?|[a-z]\w*\([a-z]\))`;
  const assignment = new RegExp(String.raw`${name}\s*=\s*([^=\n,;]*?)${stop}`, 'gi');
  const power = /\*\*|(?<=[\w)])\s?\^|(?<![a-z])[a-ln-z]\s?[²³]/i;
  const shape = /\b(?:sinus\w*|[ck]osinus\w*|parab\w*|squared|normalverteilung|gau\w*kurve)/i;
  const subject = /(?<![\w.,-])(?<!\bin )[b-df-z](?:\s+(?:and|und)\s+[b-df-z])?\s+$/;
  let formula = false;
  for (const segment of trimmed.split(/\n|(?<=[.!?;])\s+/).filter(part => part.length <= 300)) {
    for (const match of segment.matchAll(call)) {
      const argument = match[1].trim();
      const lowercase = /^[a-z]/.test(match[0]);
      if (/[a-z]/i.test(argument) && (lowercase || /^[a-z]$|[-+*/^]/i.test(argument))) {
        formula = true;
      }
    }
    for (const match of segment.matchAll(assignment)) {
      const right = match[1].trim();
      if (/[a-z]/i.test(right) && /\*\*|[*^/+-]|\(|^[a-z]\w?$/i.test(right)) {
        formula = true;
      }
    }
    for (const match of segment.matchAll(range)) {
      const constant = /pi/i.test(match[1] + match[2]);
      const variable = subject.test(segment.slice(0, match.index));
      if (constant || variable || power.test(segment) || shape.test(segment)) {
        formula = true;
      }
    }
  }
  const rest = trimmed
    .replace(range, ' ')
    .replace(call, match => (/[a-z]/i.test(match.slice(match.indexOf('('))) ? ' ' : match))
    .replace(assignment, ' ')
    .replace(/\d+\s*(?:points?|punkte?n?)\b/gi, ' ');
  const value = /(?<![\w.^*/+-])[-+]?\d+(?:[.,]\d+)?(?![*^/]|[a-z]?\s*[*^/]|[a-z]\s*[+-])/gi;
  return formula && (rest.match(value) ?? []).length < 3;
}

// ---------------------------------------------------------------- code and data requests (classify_paste in miniature)

const CODE_MODULES = String.raw`(?:np|numpy|pd|pandas|math|Math|random|scipy|stats|rng|R)`;
/** A line no table has, a short form of the service's `_STRONG`: an import, a definition, a loop, a data call. */
const CODE_STRONG = new RegExp(
  [
    String.raw`^(?:import\s+[A-Za-z_][\w.]*(?:\s+as\s+\w+)?;?$`,
    String.raw`from\s+[A-Za-z_][\w.]*\s+import\s+\S`,
    String.raw`(?:library|require)\s*\(\s*['"]?\w+['"]?\s*\)`,
    String.raw`def\s+[A-Za-z_]\w*\s*\(`,
    String.raw`(?:async\s+)?function\s*\*?\s*[A-Za-z_$]?[\w$]*\s*\(`,
    String.raw`(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=`,
    String.raw`[A-Za-z_.][\w.]*\s*<-\s*\S`,
    String.raw`for\s*\(|while\s*\(|for\s+[A-Za-z_]\w*\s+in\s+\S.*:$`,
    String.raw`(?:print|console\.log|set\.seed|cat|plot|hist|lines)\s*\(`,
    String.raw`${CODE_MODULES}\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\s*\(`,
    String.raw`[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*=\s*${CODE_MODULES}\.[A-Za-z_][\w.]*\s*\(`,
    String.raw`[A-Za-z_]\w*\s*=\s*(?:rnorm|runif|seq|rep|c|data\.frame)\s*\()`,
  ].join('|')
);
const CODE_ARROW = /\)[ \t]*=>|\b[A-Za-z_$][\w$]*[ \t]*=>/;
/** A line code has as well, which alone proves nothing: a comment, a brace, `return`, a line ending in `;`, `{`, `:`. */
const CODE_SHAPED =
  /^(?:#|\/\/|\/\*|\*|[{}\])]+;?$|return\b|else\b|elif\b|if\s*\(|if[ \t]+\S.*:$|end$)|[;{:]$/;

/**
 * The dataset route's code guard, a short form of the service's `looks_like_code`: at least one
 * line no table has, and code-shaped lines at least half of the first 200 non-empty ones, so a
 * table with a stray `print(...)` cell stays a table.
 */
function looksLikeCode(text) {
  const lines = text
    .split(/\r\n|\r|\n/)
    .map(line => line.trim().slice(0, 400))
    .filter(Boolean)
    .slice(0, 200);
  const strong = line => CODE_STRONG.test(line) || CODE_ARROW.test(line);
  if (!lines.some(strong)) return false;
  return lines.filter(line => strong(line) || CODE_SHAPED.test(line)).length / lines.length >= 0.5;
}

/** A phrase that asks for made-up data, a short form of the service's `_REQUEST` (German and English only). */
const DATA_REQUEST =
  /\b(?:(?:beispiel|test|dummy|demo|zufalls|fake)[- ]?(?:daten|werte|zahlen|tabelle)|(?:example|sample|test|dummy|fake|random|made[- ]up|synthetic)\s+(?:\w+\s+)?(?:data(?:set)?|values|numbers|table)|(?:generate|create|make|give)\s+(?:(?:me|some|a|an|random|example|sample)\s+){0,3}(?:data(?:set)?|values|numbers|table))\b/i;

/**
 * The service's `looks_like_data_request` in short: one line of at most 30 words that the chat
 * takes, no JSON, with such a phrase and fewer than three values of its own.
 */
function asksForData(text) {
  const trimmed = text.trim();
  if (!trimmed || trimmed.length > MAX_MESSAGE_CHARS || /[\r\n]/.test(trimmed)) return false;
  if (/^[[{]/.test(trimmed) || trimmed.split(/\s+/).length > 30) return false;
  return DATA_REQUEST.test(trimmed) && (trimmed.match(/\d+(?:[.,]\d+)?/g) ?? []).length < 3;
}

/** A range end the message names: a number, `pi`, `-pi`, `2 pi` or `2*pi`; null for anything else. */
function rangeEnd(text) {
  const match = text.trim().match(/^([+-])?\s*(\d+(?:[.,]\d+)?)?\s*\*?\s*(pi|π)?$/);
  if (!match || (!match[2] && !match[3])) return null;
  const number = match[2] ? Number(match[2].replace(',', '.')) : 1;
  return (match[1] === '-' ? -1 : 1) * number * (match[3] ? Math.PI : 1);
}

/** A value close to the parser's number text: eight significant digits, `1.0` for a whole one, no `-0.0`. */
function pyFloat(value) {
  if (!Number.isFinite(value)) return '';
  const rounded = Number(value.toPrecision(8));
  if (rounded === 0) return '0.0';
  if (Number.isInteger(rounded) && Math.abs(rounded) < 1e16) return rounded.toFixed(1);
  return String(rounded).replace(/e([+-])(\d)$/, 'e$10$2'); // Python writes 1e-07 where JS writes 1e-7
}

/**
 * `generate_data` in miniature: `sin(x)`, `cos(x)` or `x**2` over the range the message
 * names, stored as new data in a session without data (default bindings, no history) or
 * as the next version (`storeVersion`), unconfirmed either way, like the service.
 */
function generateData(session, lower) {
  const [formula, f, defaultStart, defaultStop] = lower.includes('cos(')
    ? ['cos(x)', Math.cos, -Math.PI, Math.PI]
    : lower.includes('sin(')
      ? ['sin(x)', Math.sin, -Math.PI, Math.PI]
      : ['x**2', x => x * x, -3, 3];
  let [start, stop] = [defaultStart, defaultStop];
  const range = lower.match(
    /\b(?:from|von)\s+(.+?)\s+(?:to|bis)\s+([-+]?\s*[\d.,]*\s*\*?\s*(?:pi|π)?)(?![\w.])/
  );
  if (range) {
    const [a, b] = [rangeEnd(range[1]), rangeEnd(range[2])];
    if (a !== null && b !== null && a !== b) [start, stop] = [a, b];
  }
  const named = lower.match(/(\d+)\s*(?:points|punkte)/);
  const points = named ? Math.min(Math.max(Number(named[1]), 2), 5000) : 200;
  const rows = Array.from({ length: points }, (_, i) => {
    const x = i === points - 1 ? stop : start + ((stop - start) * i) / (points - 1);
    return [pyFloat(x), pyFloat(f(x))];
  });
  const parsed = parseDataset(toCsv(['x', 'y'], rows));
  const short = value => String(Number(value.toPrecision(5)));
  const span = `x from ${short(start)} to ${short(stop)}`;
  const changes = [`generated ${points} rows: ${span}, y = ${formula}`];
  const first = !session.dataset;
  if (first) {
    session.dataset = parsed;
    session.bindings = defaultBindings(session, parsed.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    session.confirmed = false;
    newData(session);
    session.changed = { ...datasetPayload(session), roles: SPECS[session.specId].roles, changes };
  } else {
    storeVersion(session, parsed, changes);
  }
  const undo = first
    ? ''
    : ' as a new version of your data; .undo() in the data panel takes it back';
  return `I generated ${points} rows from y = ${formula} for ${span}${undo}. Check the preview, then press .create_plot().`;
}

/** `{rows, columns}` of a message such as "10000 rows x 30 columns", or null; capped like the service's tables. */
function wideTableSize(lower) {
  const match = lower.match(/(\d[\d,]*)\s*rows?\s*(?:x|×|by)\s*(\d+)\s*col/);
  if (!match) return null;
  const rows = Number(match[1].replace(/,/g, ''));
  const columns = Number(match[2]);
  if (!rows || columns < 3) return null;
  return { rows: Math.min(rows, 20000), columns: Math.min(columns, 50) };
}

/**
 * A computed table of the asked size for the full view, stored like `generate_data`'s: an id, a date, a text column
 * whose values hold a comma, a quote and a run of spaces, then integer and number columns with a gap every 97th
 * cell. A fixed linear congruential sequence makes every run the same table.
 */
function generateWideTable(session, size) {
  let seed = 20261101;
  const next = () => {
    seed = (Math.imul(seed, 1103515245) + 12345) >>> 0;
    return seed / 4294967296;
  };
  const stations = ['Nord', 'Süd, alt', 'Ost "neu"', 'West  2', 'Mitte', 'Hafen'];
  const header = ['id', 'date', 'station'];
  for (let c = 3; c < size.columns; c += 1)
    header.push(c % 2 ? `reading_${c - 2}` : `count_${c - 2}`);
  const start = Date.UTC(2020, 0, 1);
  const rows = Array.from({ length: size.rows }, (_, r) => {
    const row = [
      String(r + 1),
      new Date(start + r * 86400000).toISOString().slice(0, 10),
      stations[Math.floor(next() * stations.length)],
    ];
    for (let c = 3; c < size.columns; c += 1) {
      if ((r * size.columns + c) % 97 === 0) row.push('');
      else if (c % 2) row.push((next() * 2000 - 500).toFixed(2));
      else row.push(String(Math.floor(next() * 1000)));
    }
    return row;
  });
  const parsed = parseDataset(toCsv(header, rows));
  const changes = [`generated ${size.rows} rows × ${size.columns} columns of test data`];
  if (!session.dataset) {
    session.dataset = parsed;
    session.bindings = defaultBindings(session, parsed.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    session.confirmed = false;
    newData(session);
    session.changed = { ...datasetPayload(session), roles: SPECS[session.specId].roles, changes };
  } else {
    storeVersion(session, parsed, changes);
  }
  return `I generated ${size.rows.toLocaleString('en-US')} rows and ${size.columns} columns. Check the preview, or .view_all() to see every row.`;
}

/**
 * The root's answer to `{action: "example_data"}` (`.example_data()`, root.md "Example data")
 * in miniature: a made-up table that fits the spec, which `run_data_code` with `source_language`
 * `example` would compute, as version 1 of a session without data (the next version otherwise).
 * `fromCode`: the user's own code, forwarded from the data box as a chat turn, which the root's
 * `run_data_code` runs; the mock answers it with the same table and says it ran the code.
 */
function exampleData(session, fromCode = false) {
  let seed = 42;
  const next = () => {
    seed = (Math.imul(seed, 1103515245) + 12345) >>> 0;
    return seed / 4294967296;
  };
  const tables = {
    'scatter-basic': () => ({
      header: ['Ad Spend', 'Sales'],
      rows: Array.from({ length: 40 }, () => {
        const spend = 5 + next() * 45;
        return [spend.toFixed(1), (20 + 2.4 * spend + (next() - 0.5) * 30).toFixed(1)];
      }),
    }),
    'line-multi': () => ({
      header: ['Month', 'Alpha', 'Beta', 'Gamma'],
      rows: Array.from({ length: 12 }, (_, m) => [
        `2025-${String(m + 1).padStart(2, '0')}-01`,
        ...[100, 80, 60].map(base => (base + m * 4 + next() * 12).toFixed(1)),
      ]),
    }),
    'box-basic': () => ({
      header: ['Region', 'Delivery Days'],
      rows: Array.from({ length: 60 }, (_, i) => [
        ['North', 'South', 'East', 'West'][i % 4],
        (3 + (i % 4) + next() * 4).toFixed(1),
      ]),
    }),
  };
  const { header, rows } = tables[session.specId]();
  const parsed = parseDataset(toCsv(header, rows));
  const changes = [
    `${fromCode ? 'computed from your code' : 'generated example data'}: ${rows.length} rows, ${header.length} columns`,
  ];
  if (!session.dataset) {
    session.dataset = parsed;
    session.bindings = defaultBindings(session, parsed.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    session.confirmed = false;
    newData(session);
    session.changed = { ...datasetPayload(session), roles: SPECS[session.specId].roles, changes };
  } else {
    storeVersion(session, parsed, changes);
  }
  const named = header.join(', ').replace(/, ([^,]*)$/, ' and $1');
  if (fromCode) {
    return `I ran your code in a sandbox: ${rows.length} rows of ${named}. Check the preview, then press .create_plot().`;
  }
  return `I generated example data to try the plot: ${rows.length} rows of ${named}, all made up. Check them in the data panel, then press .create_plot().`;
}

/**
 * The step-1 summary the root writes after `summarize_data`, from the profile alone, in root.md's
 * shape: the counts and the bindings in a sentence or two, columns in backticks as the root
 * writes them, what is missing only when something is, and a question only when it matters.
 */
function summarizeData(session) {
  if (!session.dataset) return 'Paste your data first; then I can summarize it.';
  const { profile } = session.dataset;
  const missing = profile.columns.filter(c => c.missing).map(c => `${c.missing} in \`${c.name}\``);
  const percent = profile.columns.find(c => c.top.some(v => /%$/.test(v)));
  const bound = session.bindings.map(b => `${b.role} is \`${b.column}\``).join(', ');
  return [
    `${profile.rows} rows and ${profile.columns.length} columns${bound ? `; ${bound}` : ''}.`,
    missing.length ? `Missing values: ${missing.join(', ')}.` : '',
    percent
      ? `\`${percent.name}\` looks like percentages written as text; should I read it as numbers?`
      : '',
  ]
    .filter(Boolean)
    .join(' ');
}

// ---------------------------------------------------------------- routes

const LIBRARY_META = {
  matplotlib: { id: 'matplotlib', name: 'matplotlib', language: 'python' },
  seaborn: { id: 'seaborn', name: 'seaborn', language: 'python' },
  // A JavaScript library only when `AGENT_LIBRARIES` enables it, so the default catalogue stays as it was.
  ...Object.fromEntries(
    AGENT_LIBRARIES.filter(isJs).map(id => [
      id,
      { id, name: JS_LIBRARIES[id], language: 'javascript' },
    ])
  ),
};

function implementation(specId, library) {
  const base = `${BASE}/mock/plots/${specId}/${library}`;
  return {
    library_id: library,
    library_name: library,
    language: isJs(library) ? 'javascript' : 'python',
    preview_url: `${base}/plot-light.png`,
    preview_url_light: `${base}/plot-light.png`,
    preview_url_dark: `${base}/plot-dark.png`,
    quality_score: 92,
    code: isJs(library)
      ? `// ${specId} (${library}) — catalogue code served by the mock\nconst t = window.ANYPLOT_TOKENS;\n`
      : `# ${specId} (${library}) — catalogue code served by the mock\nimport matplotlib.pyplot as plt\n`,
    library_version: isJs(library) ? '4.5.1' : '3.10.0',
  };
}

async function route(req, res) {
  const url = new URL(req.url, BASE);
  const path = url.pathname;
  const method = req.method;
  cors(req, res);
  if (method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Catalogue routes the layout and the plot page call.
  if (method === 'GET' && path === '/health') return json(res, 200, { status: 'ok' });
  if (method === 'GET' && path === '/preview/relay') {
    if (!RELAY) return fail(res, 503, 'relay_unavailable');
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', ...RELAY.headers });
    res.end(RELAY.html);
    return;
  }
  if (method === 'GET' && path === '/specs')
    return json(
      res,
      200,
      Object.values(SPECS).map(({ id, title, description }) => ({ id, title, description }))
    );
  if (method === 'GET' && path === '/libraries')
    return json(res, 200, { libraries: Object.values(LIBRARY_META) });
  if (method === 'GET' && path === '/languages')
    return json(res, 200, {
      languages: [
        { id: 'python', name: 'Python' },
        ...(AGENT_LIBRARIES.some(isJs) ? [{ id: 'javascript', name: 'JavaScript' }] : []),
      ],
    });
  if (method === 'GET' && path === '/stats')
    return json(res, 200, { specs: 2, plots: 4, libraries: 2 });
  const specMatch = path.match(/^\/specs\/([a-z0-9-]+)$/);
  if (method === 'GET' && specMatch && SPECS[specMatch[1]]) {
    const spec = SPECS[specMatch[1]];
    return json(res, 200, {
      id: spec.id,
      title: spec.title,
      description: spec.description,
      data: spec.data,
      notes: spec.notes,
      tags: { plot_type: [spec.id.split('-')[0]] },
      implementations: AGENT_LIBRARIES.map(library => implementation(spec.id, library)),
    });
  }
  const codeMatch = path.match(/^\/specs\/([a-z0-9-]+)\/([a-z0-9]+)\/code$/);
  if (method === 'GET' && codeMatch)
    return json(res, 200, { code: implementation(codeMatch[1], codeMatch[2]).code });
  if (method === 'GET' && path.startsWith('/insights/related/'))
    return json(res, 200, { related: [] });
  if (method === 'GET' && path === '/plots/filter')
    return json(res, 200, { images: [], total: 0, counts: {}, globalCounts: {} });
  const imageMatch = path.match(/^\/mock\/plots\/.+\/plot-(light|dark)/);
  if (method === 'GET' && imageMatch) {
    res.writeHead(200, { 'Content-Type': 'image/png', 'Cache-Control': 'no-store' });
    res.end(cataloguePng(imageMatch[1]));
    return;
  }

  // The site's feedback widget and plot votes (api/routers/feedback.py), behind the bot check.
  if (method === 'POST' && path === '/feedback') {
    const refused = botCheckRefusal(req, path);
    if (refused) return json(res, refused[0], { status: refused[0], message: refused[1], path });
    return json(res, 200, { status: 'ok' });
  }
  if (method === 'GET' && path === '/mock/turnstile')
    return json(res, 200, { mode: TURNSTILE_MODE, passed: turnstilePassed });

  // The recorded quick feedback of every open session, per result version (a mock-only route).
  if (method === 'GET' && path === '/mock/feedback')
    return json(
      res,
      200,
      Object.fromEntries([...sessions].map(([sid, session]) => [sid, session.feedback]))
    );

  // The public lane (`/agent/*`, api/routers/agent_public.py): the door, then the admin lane's
  // routes with the session id in `X-Anyplot-Session` instead of the path and the tab id in
  // `X-Anyplot-Anon`; the admin-only routes do not exist there.
  let sub = null;
  if (path === '/agent/lane' || path.startsWith('/agent/')) {
    if (!PUBLIC_LANE_OPEN) return fail(res, 404, 'agent chat is not enabled');
    if (path === '/agent/lane' && method === 'GET') {
      res.setHeader('Cache-Control', 'public, max-age=60');
      return json(res, 200, { open: true });
    }
    if (!/^[A-Za-z0-9_-]{22,64}$/.test(String(req.headers['x-anyplot-anon'] || '')))
      return fail(res, 400, 'anon_required');
    const rest = path.slice('/agent'.length);
    if (rest === '/session' || rest.startsWith('/session/')) {
      const sid = String(req.headers['x-anyplot-session'] || '');
      if (!/^[A-Za-z0-9_-]{1,128}$/.test(sid)) return fail(res, 422, 'invalid');
      sub = `/sessions/${sid}${rest.slice('/session'.length)}`;
    } else {
      sub = rest;
    }
    if (
      sub === '/budget' ||
      sub.startsWith('/cases') ||
      sub.endsWith('/dataset/copy') ||
      sub.endsWith('/bundle')
    )
      return fail(res, 404, 'not_found');
  } else if (!path.startsWith('/debug/agent')) return fail(res, 404, 'not_found');

  // The BFF's CSRF guard.
  if (method !== 'GET' && req.headers['x-anyplot-client'] !== 'agent-chat/1')
    return fail(res, 403, 'client_header_required');
  const hasBody = req.headers['content-length'] && req.headers['content-length'] !== '0';
  if (hasBody && !String(req.headers['content-type'] || '').startsWith('application/json'))
    return fail(res, 403, 'json_required');

  const ref = randomUUID();
  const publicLane = sub !== null;
  sub ??= path.slice('/debug/agent'.length);
  let body = null;
  try {
    body = method === 'GET' ? null : await readBody(req);
  } catch {
    return fail(res, 422, 'invalid', ref);
  }
  // The public lane's bot check: opening a session and storing a feedback case.
  if (
    publicLane &&
    method === 'POST' &&
    (sub === '/sessions' || /^\/sessions\/[^/]+\/feedback$/.test(sub))
  ) {
    const refused = botCheckRefusal(req, path);
    if (refused) return fail(res, refused[0], refused[1], ref);
  }

  if (method === 'GET' && sub === '/status')
    return json(
      res,
      200,
      {
        libraries: AGENT_LIBRARIES,
        model: 'claude-haiku-5-5',
        location: 'eu',
        provider: 'anthropic-vertex',
        version: 'mock',
        waiting: waitingTurns + OTHERS_WAITING,
        in_flight: runsInFlight,
        user_max_runs: 3,
        // The service's `ledger.paused()`: every turn would get `service_paused` until the reset.
        ...(PAUSED ? { paused: true, resets_at: nextUtcMidnight() } : {}),
        enabled: true,
      },
      ref
    );
  // The day's usage book (`agents/main.py` `budget`), the admin lane only: the public lane's
  // `/budget` is refused above. Counts and times only, as the service answers them.
  if (method === 'GET' && sub === '/budget') {
    const budgetTokens = 2_000_000;
    const startOfDay = new Date();
    startOfDay.setUTCHours(0, 0, 0, 0);
    return json(
      res,
      200,
      {
        since: startOfDay.toISOString(),
        started_at: MOCK_STARTED_AT,
        resets_at: nextUtcMidnight(),
        paused: PAUSED,
        tokens: Math.round((budgetTokens * BUDGET_PCT) / 100),
        budget_tokens: budgetTokens,
        usd: null,
        budget_usd: null,
        users: 3,
        users_at_limit: 0,
        limits: {},
      },
      ref
    );
  }
  if (method === 'GET' && sub === '/eligibility') {
    const library = url.searchParams.get('library');
    const eligible = !!SPECS[url.searchParams.get('spec')] && AGENT_LIBRARIES.includes(library);
    return json(
      res,
      200,
      {
        eligible,
        status: eligible ? 'coupled' : 'blocked',
        reasons: eligible ? [] : ['library-disabled'],
      },
      ref
    );
  }
  if (method === 'POST' && sub === '/sessions') {
    if (OPEN_MS > 0) await sleep(OPEN_MS);
    if (!SPECS[body?.spec_id]) return fail(res, 404, 'not_found', ref);
    if (!AGENT_LIBRARIES.includes(body.library)) return fail(res, 422, 'not_eligible', ref);
    const sid = randomBytes(18).toString('base64url');
    sessions.set(sid, {
      specId: body.spec_id,
      library: body.library,
      dataset: null,
      bindings: [],
      complete: false,
      // Step 1's confirmation of the dataset and its bindings.
      confirmed: false,
      // The dataset versions, numbered once per session as the service numbers them: every
      // stored version takes the next number (`top`), never one twice, and an undo makes the
      // version it restores current under its own; `first` is the current data's first number.
      history: [],
      version: 1,
      top: 0,
      first: 1,
      changed: null,
      versions: [],
      // `{role, text}` per user message or action and per assistant reply, for the bundle.
      transcript: [],
      // The quick feedback per result version: the latest submission, with its case id.
      feedback: {},
      // The session language: English by default, whatever the browser's locale, and the
      // languages offered so far (each comes once).
      language: 'en',
      languageSource: 'default',
      languageOffered: [],
      // Opened by the admin's `.plot_all()` (`source: fanout`): the only kind of session a copy may go into.
      fanout: body.source === 'fanout',
      // The plot memory (`{id, kind, target, text, expect, turn}`, oldest first), its next id, the
      // user turns so far, and a library switch's carry (`{target, fromPlot, theme}`) until it is spent.
      memory: [],
      memorySeq: 0,
      turns: 0,
      carry: null,
      // A plot wish kept for the library's first plot in step 1 (`keep_plot_request`), until it ships.
      keptWish: null,
      active: false,
      cancelled: false,
    });
    // The spec's roles, as the service answers them since the header's columns ⓘ reads them.
    return json(
      res,
      200,
      {
        session_id: sid,
        eligibility: { eligible: true, status: 'coupled', reasons: [] },
        roles: SPECS[body.spec_id].roles,
      },
      ref
    );
  }

  const sessionMatch = sub.match(/^\/sessions\/([A-Za-z0-9_-]+)(\/.*)?$/);
  if (!sessionMatch) return fail(res, 404, 'not_found', ref);
  const [, sid, rest = ''] = sessionMatch;
  const session = sessions.get(sid);
  if (!session) return fail(res, 404, 'session_expired', ref);

  if (method === 'DELETE' && rest === '') {
    sessions.delete(sid);
    res.writeHead(204, { 'X-Request-Id': ref });
    res.end();
    return;
  }
  if (method === 'POST' && rest === '/library') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (body?.source !== undefined && !['menu', 'chat'].includes(body.source))
      return fail(res, 422, 'invalid', ref);
    if (!AGENT_LIBRARIES.includes(body?.library)) return fail(res, 422, 'not_eligible', ref);
    // Another spec waits for the plot-type switch.
    if (body.spec_id && body.spec_id !== session.specId) return fail(res, 422, 'invalid', ref);
    // The service's `switch.carry_for` and `switch.summary` in miniature: the source's latest plot
    // carries (its asked theme), else a carry not yet run moves on, else the memory alone.
    const target = body.library;
    const latestIn = library => session.versions.findLast(item => item.library === library);
    if (target !== session.library) {
      // A plot of another data version carries its asked theme too; its texts and requests, which
      // the mock does not carry, stay behind on the service (`switch.source_plot`, 2026-11-09).
      const plot = latestIn(session.library);
      const pending = session.carry;
      session.carry =
        plot || pending || session.memory.length
          ? {
              target,
              fromPlot: !!plot || !!pending?.fromPlot,
              theme: plot ? (plot.themeAsked ? plot.theme : null) : (pending?.theme ?? null),
            }
          : null;
    }
    const targetPlot = latestIn(target);
    const carry = session.carry?.target === target ? session.carry : null;
    const decisions = session.memory.length;
    const newer = targetPlot
      ? session.memory.filter(entry => entry.turn > targetPlot.turn).length
      : decisions;
    const offer = !!carry && (decisions > 0 || carry.fromPlot) && (!targetPlot || newer > 0);
    session.library = target;
    return json(
      res,
      200,
      {
        session_id: sid,
        eligibility: { eligible: true, status: 'coupled', reasons: [] },
        target: { spec_id: session.specId, library: target },
        carry: {
          decisions,
          newer,
          target_has_plot: !!targetPlot,
          from_plot: !!carry?.fromPlot,
          offer,
        },
      },
      ref
    );
  }
  if (method === 'GET' && rest === '/memory') return json(res, 200, memoryPayload(session), ref);
  if (method === 'DELETE' && rest === '/memory') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    session.memory = [];
    return json(res, 200, memoryPayload(session), ref);
  }
  const memoryMatch = rest.match(/^\/memory\/(m[0-9]{1,6})$/);
  if (method === 'DELETE' && memoryMatch) {
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (!session.memory.some(entry => entry.id === memoryMatch[1]))
      return fail(res, 404, 'not_found', ref);
    session.memory = session.memory.filter(entry => entry.id !== memoryMatch[1]);
    return json(res, 200, memoryPayload(session), ref);
  }
  if (method === 'POST' && rest === '/dataset') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    const text = typeof body?.text === 'string' ? body.text : '';
    if (Buffer.byteLength(text, 'utf8') > MAX_DATASET_BYTES) return fail(res, 413, 'too_long', ref);
    if (/ignore previous/i.test(text)) return fail(res, 403, 'data_refused', ref);
    await sleep(PARSE_MS);
    // Before any parser, as the service's `classify_paste`: code at any length (it is never a
    // table), a request for data only when the chat takes it.
    if (looksLikeCode(text)) return fail(res, 422, 'code', ref);
    if (asksForData(text)) return fail(res, 422, 'data_request', ref);
    // Several tables, each under its own header after a blank line (the service's `_one_table`): the mock reads
    // blocks of three or more comma lines (a caption line above them left out), the first one or the chosen `table`.
    const blocks = text
      .split(/\r?\n\s*\r?\n/)
      .map(block => {
        const lines = block.trim().split(/\r?\n/);
        const start = lines.findIndex(line => line.includes(','));
        return start < 0 ? [] : lines.slice(start);
      })
      .filter(lines => lines.length >= 3);
    const table = Number.isInteger(body?.table) ? body.table : 1;
    if (blocks.length < 2 && table > 1) return fail(res, 422, 'unparseable', ref);
    if (blocks.length >= 2 && table > blocks.length) return fail(res, 422, 'unparseable', ref);
    const tables =
      blocks.length >= 2
        ? blocks.map(lines => `${lines[0].split(',').join(', ')} · ${lines.length - 1} rows`)
        : null;
    let parsed;
    try {
      parsed = parseDataset(tables ? blocks[table - 1].join('\n') : text);
    } catch {
      // A formula ("zeichne sin(x) von -pi bis pi") is never transcribed: a model would compute
      // its rows. The service answers 422 formula; the page points to the chat's generate_data.
      if (looksLikeFormula(text)) return fail(res, 422, 'formula', ref);
      // Free text (no delimiter, "Hund 7 Katze 3 und Vogel 4"): the real service has a model read
      // it into a table and answers it unstored, for the user to confirm. The mock pairs each
      // word with the number after it.
      const transcribed = body?.confirmed ? null : transcribeFreeText(text);
      if (!transcribed) return fail(res, 422, 'unparseable', ref);
      await sleep(900);
      return json(res, 200, transcribed, ref);
    }
    // A column the replaced data was bound to that the new data lacks (the service's `columns_changed`,
    // which matches by name and meaning; the mock by the exact name).
    const header = new Set(parsed.profile.columns.map(column => column.name));
    const columnsChanged =
      !!session.dataset && session.bindings.some(binding => !header.has(binding.column));
    session.dataset = parsed;
    session.bindings = defaultBindings(session, parsed.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    session.confirmed = false; // a new dataset is unchecked
    newData(session); // the session's next number, no history
    session.summaryPending = true; // the first turn on it summarizes it: the action, or the note
    const dataOffer = offerLanguage(session, text, null);
    return json(
      res,
      200,
      {
        ...datasetPayload(session),
        // A dropped file's name, kept apart from the notes as the service does (unscreened here).
        ...(typeof body?.source === 'string' ? { file_name: body.source.slice(0, 80) } : {}),
        ...(tables ? { tables, table } : {}),
        columns_changed: columnsChanged,
        roles: SPECS[session.specId].roles,
        language: languageBody(session, dataOffer),
      },
      ref
    );
  }
  if (method === 'POST' && rest === '/dataset/to_long') {
    // `.to_long()`: the offer recomputed here, applied without a model, as the next version.
    if (session.active) return fail(res, 409, 'run_active', ref);
    const offer = session.dataset && longSuggestion(session, session.dataset);
    if (!offer) return fail(res, 422, 'no_suggestion', ref);
    const { header, rows } = session.dataset;
    const at = name => header.indexOf(name);
    const long = [];
    for (const column of offer.columns)
      for (const row of rows)
        long.push([...offer.keys.map(k => row[at(k)]), column, row[at(column)]]);
    const parsed = parseDataset(toCsv([...offer.keys, offer.names_to, offer.values_to], long));
    const changes = [
      `pivoted ${offer.columns.length} columns into ${offer.names_to}/${offer.values_to}: ${long.length} rows`,
    ];
    storeVersion(session, parsed, changes);
    session.changed = null; // answered here, not by a turn's `done`
    // A new shape: the default bindings for its columns, as `rebind` on the service.
    session.bindings = defaultBindings(session, parsed.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    return json(
      res,
      200,
      { ...datasetPayload(session), roles: SPECS[session.specId].roles, changes },
      ref
    );
  }
  if (method === 'POST' && rest === '/dataset/copy') {
    // The admin fan-out's copy (`agents/main.py` `copy_dataset`): the source session's confirmed version, as it is.
    if (NO_COPY) return fail(res, 404, 'not_found', ref);
    const keys = body && typeof body === 'object' ? Object.keys(body) : [];
    const from = body?.from_session;
    if (keys.length !== 1 || typeof from !== 'string' || !/^[A-Za-z0-9_-]{1,128}$/.test(from))
      return fail(res, 422, 'invalid', ref);
    if (from === sid) return fail(res, 422, 'invalid', ref);
    const origin = sessions.get(from);
    if (!origin) return fail(res, 404, 'session_expired', ref);
    if (session.active || origin.active) return fail(res, 409, 'run_active', ref);
    if (!session.fanout || origin.specId !== session.specId) return fail(res, 422, 'invalid', ref);
    if (session.dataset) return fail(res, 409, 'has_dataset', ref);
    if (!origin.dataset) return fail(res, 422, 'no_dataset', ref);
    if (!origin.confirmed) return fail(res, 422, 'unconfirmed', ref);
    session.dataset = structuredClone(origin.dataset);
    session.bindings = origin.bindings.map(binding => ({ ...binding }));
    const checked = checkBindings(session, session.bindings);
    session.complete = checked.complete;
    session.confirmed = true; // the source's confirmation comes along
    newData(session); // the fan-out session's first version, 1
    session.language = origin.language;
    session.languageSource = origin.languageSource;
    session.languageOffered = [...origin.languageOffered]; // the page's offers stand: a copy never offers
    return json(
      res,
      200,
      {
        ...datasetPayload(session),
        roles: SPECS[session.specId].roles,
        language: { language: session.language, source: session.languageSource },
        confirmed: true,
        complete: checked.complete,
        missing_roles: checked.missing_roles,
        copied_from: origin.version,
      },
      ref
    );
  }
  if (method === 'GET' && rest === '/dataset/data.csv') {
    // Read-only, so a turn in flight does not block it, as in the service.
    if (!session.dataset) return fail(res, 422, 'no_dataset', ref);
    res.writeHead(200, {
      'Content-Type': 'text/csv; charset=utf-8',
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Request-Id': ref,
    });
    res.end(csvText(session));
    return;
  }
  if (method === 'POST' && rest === '/dataset/undo') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    const previous = session.history.pop();
    if (!previous) return fail(res, 422, 'nothing_to_undo', ref);
    session.dataset = previous.dataset;
    session.bindings = carryBindings(session, session.bindings, previous.dataset.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    session.confirmed = false; // restored, but confirmed again by the user
    session.version = previous.number; // its own number again; the undone one is never given again
    // A new data version drops the switch's carry and a kept wish (2026-11-08).
    session.carry = null;
    session.keptWish = null;
    return json(res, 200, { ...datasetPayload(session), roles: SPECS[session.specId].roles }, ref);
  }
  if (method === 'PUT' && rest === '/bindings') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (!session.dataset) return fail(res, 422, 'no_dataset', ref);
    const wanted = (Array.isArray(body) ? body : []).filter(b => b && b.column);
    const { errors, ...checked } = checkBindings(session, wanted);
    // The BFF passes the check's lines of a refused set on (at most 20).
    if (errors.length)
      return json(res, 422, { detail: 'invalid', ref, errors: errors.slice(0, 20) }, ref);
    session.bindings = checked.bindings;
    session.complete = checked.complete;
    session.confirmed = false; // the confirmation covered the previous set
    return json(res, 200, checked, ref);
  }
  if (method === 'PUT' && rest === '/language') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    // The BFF's strict body: `language` and `via` (`header` or `offer`), matched as sent.
    const extra =
      body &&
      typeof body === 'object' &&
      Object.keys(body).some(k => k !== 'language' && k !== 'via');
    const value = typeof body?.language === 'string' ? body.language : '';
    const via = body?.via ?? 'header';
    if (extra || !LANGUAGE_RE.test(value) || !['header', 'offer'].includes(via)) {
      return fail(res, 422, 'invalid', ref);
    }
    session.language = normaliseLanguage(value);
    // An accepted offer keeps a pick final: `offer` only while the user picked none.
    session.languageSource =
      via === 'offer' && session.languageSource !== 'chosen' ? 'offer' : 'chosen';
    // With data, the `.to_long()` offer recomputed in the new language, as the service answers it.
    const offer = session.dataset ? { suggestion: longSuggestion(session, session.dataset) } : {};
    return json(
      res,
      200,
      { language: session.language, source: session.languageSource, ...offer },
      ref
    );
  }
  if (method === 'POST' && rest === '/dataset/convert') {
    // The renderer reads the file in production; here the first bytes pick a canned answer. A zip is a
    // workbook with the sheets "2024" and "2025", Parquet a single table, a file whose bytes hold
    // "TOO_MANY_ROWS" the row-cap refusal with its counts, anything else `file_unsupported`.
    if (typeof body?.data_base64 !== 'string') return fail(res, 422, 'invalid', ref);
    const bytes = Buffer.from(body.data_base64, 'base64');
    if (bytes.length > 5 * 1024 * 1024) return fail(res, 413, 'too_long', ref);
    await sleep(PARSE_MS);
    if (bytes.includes('TOO_MANY_ROWS')) {
      res.writeHead(422, { 'Content-Type': 'application/json', 'X-Request-Id': ref });
      res.end(JSON.stringify({ detail: 'file_too_many_rows', ref, measured: 48213, limit: 20000 }));
      return;
    }
    const head = bytes.subarray(0, 4).toString('latin1');
    if (head === 'PK\u0003\u0004') {
      const sheet = body.sheet ?? '2024';
      if (!['2024', '2025'].includes(sheet)) return fail(res, 422, 'file_sheet_not_found', ref);
      const year = Number(sheet);
      const text = `Umsatz ${year}\n\nmonth,revenue\n${year}-01,${year - 1900}\n${year}-02,${year - 1880}\n${year}-03,${year - 1870}\n`;
      return json(
        res,
        200,
        {
          text,
          format: 'csv',
          kind: 'xlsx',
          rows: 5,
          columns: 2,
          sheet,
          sheets: ['2024', '2025'],
          sheet_count: 2,
          warnings: { formulas_without_value: 2, hidden_sheets: 1 },
        },
        ref
      );
    }
    if (head === 'PAR1') {
      return json(
        res,
        200,
        {
          text: 'station,temp_c\nNord,4.5\nSüd,7.25\n',
          format: 'csv',
          kind: 'parquet',
          rows: 2,
          columns: 2,
          sheet: null,
          sheets: [],
          sheet_count: 0,
          warnings: {},
        },
        ref
      );
    }
    return fail(res, 422, 'file_unsupported', ref);
  }
  if (method === 'POST' && rest === '/dataset/confirm') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (!session.dataset) return fail(res, 422, 'no_dataset', ref);
    session.confirmed = true;
    session.summaryPending = false; // the user saw the data: the plot's request after it is no note
    return json(
      res,
      200,
      {
        confirmed: true,
        rows: session.dataset.profile.rows,
        columns: session.dataset.profile.columns.length,
      },
      ref
    );
  }
  if (method === 'POST' && rest === '/messages') {
    // The page's site theme rides in the query, as at the BFF; any other value is its `422`.
    const siteTheme = url.searchParams.get('theme');
    if (siteTheme !== null && siteTheme !== 'light' && siteTheme !== 'dark')
      return fail(res, 422, 'invalid', ref);
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (typeof body?.text === 'string' && body.text.length > 2000)
      return fail(res, 413, 'too_long', ref);
    return streamTurn(req, res, session, body ?? {}, ref, siteTheme);
  }
  if (method === 'POST' && rest === '/outcome') {
    // The content-free usage beacon (`telemetry.OutcomeAction`): checked like the BFF's body, answered 204.
    const actions = [
      'copied_code',
      'copied_image',
      'downloaded_png',
      'downloaded_code',
      'downloaded_page',
      'opened_preview',
      'opened_data_view',
      'downloaded_data',
    ];
    const valid =
      body &&
      [...actions, 'saved_session', 'feedback'].includes(body.action) &&
      (body.version === undefined ||
        (Number.isInteger(body.version) && body.version >= 0 && body.version <= 999)) &&
      (body.action === 'feedback'
        ? FEEDBACK_REACTIONS.includes(body.reaction)
        : body.reaction === undefined) &&
      Object.keys(body).every(key => ['action', 'version', 'reaction'].includes(key));
    if (!valid) return fail(res, 422, 'invalid', ref);
    res.writeHead(204, { 'X-Request-Id': ref });
    res.end();
    return;
  }
  if (method === 'GET' && rest === '/turn') return readTurn(req, res, session, ref);
  if (method === 'POST' && rest === '/cancel') {
    session.cancelled = true;
    res.writeHead(204, { 'X-Request-Id': ref });
    res.end();
    return;
  }
  const renderMatch = rest.match(/^\/versions\/(\d+)\/render$/);
  if (method === 'POST' && renderMatch) {
    if (session.active) return fail(res, 409, 'run_active', ref);
    const number = Number(renderMatch[1]);
    const version = number
      ? session.versions.find(v => v.number === number)
      : session.versions[session.versions.length - 1];
    if (!version) return fail(res, 404, 'not_found', ref);
    const theme = body?.theme === 'dark' ? 'dark' : 'light';
    if (!version.pngs[theme]) {
      await sleep(1500);
      renderVersion(session, version, theme);
    }
    return json(res, 200, { status: 'ok', reason: null, artifacts: artifactNames(version) }, ref);
  }
  const artifactMatch = rest.match(/^\/artifacts\/([a-z.-]+)$/);
  if (method === 'GET' && artifactMatch) {
    const number = Number(url.searchParams.get('v') || 0);
    const version = number
      ? session.versions.find(v => v.number === number)
      : session.versions[session.versions.length - 1];
    if (!version) return fail(res, 404, 'not_found', ref);
    const name = artifactMatch[1];
    const headers = {
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Request-Id': ref,
    };
    const js = isJs(version.library);
    if (name === 'plot.py' && !js) {
      res.writeHead(200, { ...headers, 'Content-Type': 'text/x-python; charset=utf-8' });
      res.end(plotPy(session, version));
      return;
    }
    if (name === 'plot.js' && js) {
      res.writeHead(200, { ...headers, 'Content-Type': 'text/javascript; charset=utf-8' });
      res.end(plotJs(session, version));
      return;
    }
    if (name === 'plot.html') {
      // Built on demand in the theme asked for, like the agents service; the session's turn and the build
      // exclude each other there (`409 run_active`).
      if (!js) return fail(res, 404, 'not_found', ref);
      if (session.active) return fail(res, 409, 'run_active', ref);
      const asked = url.searchParams.get('theme');
      if (asked !== null && asked !== 'light' && asked !== 'dark')
        return fail(res, 422, 'invalid', ref);
      const theme = asked ?? version.theme;
      await sleep(PAGE_MS);
      const title = `${session.specId} · ${version.library} · v${version.number} · anyplot.ai`;
      res.writeHead(200, {
        ...PAGE_HEADERS,
        'Content-Type': 'text/html; charset=utf-8',
        'X-Request-Id': ref,
      });
      res.end(wrapPage(chartPage(version, theme), theme, title));
      return;
    }
    if (name === 'plot.py' || name === 'plot.js') return fail(res, 404, 'not_found', ref);
    if (name === 'data.csv') {
      res.writeHead(200, { ...headers, 'Content-Type': 'text/csv; charset=utf-8' });
      res.end(csvText(version));
      return;
    }
    const pngTheme = { 'plot-light.png': 'light', 'plot-dark.png': 'dark' }[name];
    if (!pngTheme || !version.pngs[pngTheme]) return fail(res, 404, 'not_found', ref);
    res.writeHead(200, { ...headers, 'Content-Type': 'image/png' });
    res.end(version.pngs[pngTheme]);
    return;
  }
  if (method === 'GET' && rest === '/bundle') {
    // `.save()`: the feedback case, as the BFF relays the agents service's bundle.
    const flag = (url.searchParams.get('include_data') ?? 'false').toLowerCase();
    const includeData = ['true', '1', 'yes', 'on'].includes(flag);
    const rawVersion = url.searchParams.get('version');
    const number = rawVersion === null ? 0 : Number(rawVersion);
    if (
      (!includeData && !['false', '0', 'no', 'off'].includes(flag)) ||
      !Number.isInteger(number) ||
      number < 0 ||
      number > 999
    )
      return fail(res, 422, 'invalid', ref);
    const versions = number ? session.versions.filter(v => v.number === number) : session.versions;
    if (number && versions.length === 0) return fail(res, 404, 'not_found', ref);
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Content-Disposition': `attachment; filename="anyplot-session-${sid.slice(0, 8)}.json"`,
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Request-Id': ref,
    });
    res.end(JSON.stringify(sessionBundle(session, versions, includeData)));
    return;
  }
  if (method === 'POST' && rest === '/feedback') {
    // The quick feedback: the BFF stores the version's case in the private bucket.
    const problem = feedbackProblem(body);
    if (problem) return json(res, 422, { detail: [{ msg: problem }] }, ref);
    // Version 0 is the chat itself, for a session without a plot: no image, no plot.py.
    const chat = body.result_version === 0;
    const version = chat ? null : session.versions.find(v => v.number === body.result_version);
    if (!chat && !version) return fail(res, 404, 'not_found', ref);
    if (chat && body.include_data && !session.dataset) return fail(res, 422, 'no_data', ref);
    const message = typeof body.message === 'string' ? body.message.trim() || null : null;
    await sleep(600);
    if (message?.includes('502')) return fail(res, 502, 'storage', ref);
    const caseId = `${new Date()
      .toISOString()
      .replace(/[-:]/g, '')
      .replace(/\.\d+Z$/, 'Z')}-${randomBytes(4).toString('hex')}`;
    const stored = [
      ...(version
        ? ['light', 'dark'].filter(theme => version.pngs[theme]).map(theme => `plot-${theme}.png`)
        : []),
      ...(version ? ['plot.py'] : []),
      ...(body.include_data ? ['data.csv'] : []),
      'manifest.json',
    ];
    session.feedback[body.result_version] = {
      case_id: caseId,
      reaction: body.reaction,
      message,
      include_data: body.include_data,
      replaces: body.replaces ?? null,
    };
    return json(res, 201, { case_id: caseId, stored }, ref);
  }
  return fail(res, 404, 'not_found', ref);
}

const FEEDBACK_REACTIONS = ['thumbs_up', 'thumbs_down', 'bug', 'idea'];
const FEEDBACK_FIELDS = new Set([
  'reaction',
  'message',
  'include_data',
  'result_version',
  'replaces',
]);
/** The BFF's case id: the UTC time in ISO 8601 basic format and 8 random hex digits. */
const CASE_ID = /^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$/;

/** Why the BFF would refuse a feedback body with a 422, or `null` when it takes it. */
function feedbackProblem(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return 'a JSON object is required';
  const extra = Object.keys(body).filter(key => !FEEDBACK_FIELDS.has(key));
  if (extra.length) return `unknown field ${extra[0]}`;
  if (!FEEDBACK_REACTIONS.includes(body.reaction)) return 'reaction must be one of the set';
  if (body.message != null && typeof body.message !== 'string') return 'message must be text';
  // Code points, as the BFF counts them, not UTF-16 units.
  if (typeof body.message === 'string' && [...body.message.trim()].length > 500)
    return 'message must be 500 characters or fewer';
  if (typeof body.include_data !== 'boolean') return 'include_data is required';
  const version = body.result_version;
  if (!Number.isInteger(version) || version < 0 || version > 999)
    return 'result_version must be 0 to 999';
  if (body.replaces != null && (typeof body.replaces !== 'string' || !CASE_ID.test(body.replaces)))
    return 'replaces must be a case id';
  return null;
}

/**
 * The agents service's feedback case (`GET /v1/sessions/{sid}/bundle`) from the mock's
 * state: the same top-level keys, the PNGs the artifact route serves as base64, and the
 * mock's one code form standing in for the working, run and exported code.
 */
function sessionBundle(session, versions, includeData) {
  return {
    session: {
      spec_id: session.specId,
      library: session.library,
      locale: 'en',
      plot_language: session.language,
      plot_language_source: session.languageSource,
    },
    snapshot: { spec_id: session.specId, library_version: '3.10.0' },
    transcript: session.transcript,
    versions: versions.map(version => {
      const js = isJs(version.library);
      const code = js ? plotJs(session, version) : plotPy(session, version);
      return {
        number: version.number,
        language: version.language,
        title: SPECS[session.specId].title,
        working: code,
        run_form: code,
        plot_py: code,
        ...(js ? { code_artifact: 'plot.js' } : {}),
        plan: null,
        result: version.result,
        theme: version.theme,
        themes: Object.fromEntries(
          Object.keys(version.pngs).map(theme => [theme, { status: 'ok', reason: null }])
        ),
        images: Object.fromEntries(
          Object.entries(version.pngs).map(([theme, png]) => [theme, png.toString('base64')])
        ),
        data_csv: includeData ? csvText(version) : null,
      };
    }),
    profile: session.dataset ? session.dataset.profile : null,
    bindings: session.bindings,
    config: {
      provider: 'mock',
      model: 'claude-haiku-5-5',
      judge_model: 'claude-haiku-5-5',
      location: 'eu',
      adk_version: 'mock',
      service_version: 'mock',
      prompt_hashes: {},
    },
  };
}

http
  .createServer((req, res) => {
    route(req, res).catch(err => {
      console.error(err);
      if (!res.headersSent) fail(res, 500, 'internal');
      else res.end();
    });
  })
  // Loopback only: the mock echoes pasted data back as images, so it must not
  // be reachable from the local network.
  .listen(PORT, '127.0.0.1', () => {
    console.log(
      `agent BFF mock on ${BASE} (step ${STEP_MS} ms, queue ${QUEUE_START} x ${QUEUE_MS} ms)`
    );
  });
