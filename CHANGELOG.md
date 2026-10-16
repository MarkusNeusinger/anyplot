# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning is product communication
rather than library SemVer: major for milestone releases, minor for feature batches, patch for
fix-only (see `agentic/commands/release.md`).

**Do not add to this file in a feature PR.** Every non-exempt PR adds one fragment,
`changelog.d/<slug>.md`, in this file's own format, each bullet with its PR reference. The shared
`[Unreleased]` spot is where sibling PRs used to conflict each other, so the CI job
"Changelog (fragment)" refuses both a missing fragment and a bullet added in here directly
(format and exemptions: `changelog.d/README.md`). Correcting an entry `[Unreleased]` already
carries is allowed — a bullet is identified by its bold title, so a re-worded body is a change,
and only a NEW title (or one more copy of a title already there) is an added bullet. A release runs
`uv run python -m tools.changelog release X.Y.Z --title "<codename>"`, which folds every fragment
under a new version heading (`## [X.Y.Z] — YYYY-MM-DD — <codename>`), bumps `pyproject.toml`
(`project.version`), `uv.lock` and `app/package.json`, repoints the compare links at the bottom of
this file and deletes the fragments — one commit, via a PR (procedure:
`agentic/commands/release.md`). After the merge the tag goes on the
merge commit and the GitHub release is created from the section — condensed, never copied (rule
of 2026-08-28): an intro line with the merge count, the PR range and a link to this file; the
section's own headings in the section's order (an empty one is omitted); one bullet per NOTABLE
entry — chores, dependency bumps and small fixes are left out, and there is no fixed count — at
most two lines each: its bold title, one clause with the essence or the headline number, its PR
reference; a compare link as the last line. Numbers are copied exactly and only PR numbers from
the section are cited; the full text lives only here — the release page is the index into it.
Product, pipeline-infrastructure, and
docs changes are covered here. **Exempt:** the automated plot pipeline's routine output
(spec-create, impl-generate/review/repair/merge, spec auto-polish, and daily-regen PRs) and
individual Dependabot bumps — listing those per entry would drown the file (900+ automated
commits per release window). Where the release window had such activity, they are summarized in
aggregate instead: an italic *Catalog* line at the end of the version section and a single
**Dependencies:** bullet under `### Changed`, both created or updated at release time.

## [Unreleased]

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

[Unreleased]: https://github.com/MarkusNeusinger/anyplot/compare/v3.5.0...HEAD
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
