### Changed

- **`/audit` covers the agent network and the public surfaces, and says who
  meets each finding.** No auditor read `agents/`, the largest code area of
  the repository, and the live site was judged from the code alone. Six
  auditors join the sixteen: `agents-auditor` (the data and orchestration
  layer), `sandbox-auditor` (the code validator and the render sandbox),
  `public-lane-auditor` (limits, authentication, and privacy of the public
  chat), `chat-frontend-auditor`, `site-auditor` (the rendered pages in a
  headless browser of its own, through the new helper `site-shots.mjs`), and
  `landing-auditor` (the repository page as a stranger reads it). Every
  finding now carries `SEEN_BY` (a visitor of the site, a visitor of the
  repository page, a reader of the code, or nobody outside) and its primary
  `EVIDENCE`, and the report lists what an outside reader meets in a section
  of its own, because severity alone ranks a typo on the landing page below a
  rare race in a script nobody opens. Cross-validation now also checks a
  medium finding that a visitor meets. The auditors that read code lose their
  cap of thirty tool calls, which could not read a module of four thousand
  lines, and report what they read and what they did not reach. Each auditor
  runs on the model its roster row names (Fable for the three high-risk
  reviews), passed explicitly instead of inherited from the session. The
  shared rules gain the limits for the live site: no agent runs, at most two
  loads of `/agent`, no shared browser.
- **A persisted audit report says that it is a snapshot.** A report opens
  with a status line and describes an incident in the past tense of its own
  date. The report of 2026-07-15, still the newest one, headlined a Health
  Score of 30 and a retry loop "still going" that was fixed the next day; it
  now says so.

### Fixed

- **The auditor prompts name paths, routes, and services that exist, and a
  test keeps it so.** The PageSpeed auditor pointed at `/catalog` and
  `/spec/…`, routes that are gone, and called its API key optional although
  every anonymous call of six audits was refused; the Cloud auditor named two
  Cloud Run services that were renamed; the catalogue auditor counted nine
  Python libraries where the catalogue holds fifteen in four languages; the
  quality auditor asked for community files the repository has had for
  months. `tests/unit/test_agent_instructions.py` now fails when an auditor
  file names a path that does not exist, when the roster, the prompt index,
  and the auditor files disagree, when a roster row names no model, or when
  a tracked top-level directory has neither an auditor nor a stated reason
  to have none.

### Security

- **No auditor prints a secret or connects to production.** The Plausible
  auditor read its API key with a command that wrote the key to the
  transcript and fell back to reading it from Secret Manager; it now reads
  the key into a variable and reports `blocked` without one. The database
  auditor was allowed `alembic check`, which loads `.env` and so connects to
  the shared production database; drift is read from the `Verify Migrations`
  job instead, and only `alembic heads`, which reads the revision files,
  stays allowed.
