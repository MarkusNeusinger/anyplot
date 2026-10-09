### Added

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
  model's baseline, and exits non-zero when the pass rate drops below it.
  `--budget-usd` stops a run once its estimated cost passes the budget. A
  blind review page samples 30 renders with an accept and reject pair each
  and exports the owner's judgements as JSON, so one command answers spike X
  and every later model or prompt comparison.
- **The spike-X eval cases.** 120 synthetic cases: 10 specs from 10 plot
  families, each eligible in matplotlib and seaborn, times six datasets
  (renamed headers, values times 10, 12 rows, 5,000 rows, `DD.MM.YYYY` and ISO
  dates, and semicolon text with decimal commas), written by the seeded,
  rerunnable `agents/evals/make_fixtures.py`, which a unit test keeps in sync
  with the committed files. The smoke set is 12 of them plus the two
  hand-written cases.

### Changed

- **Content-free attribution lines for every pipeline step.** The plot
  pipeline now logs the adapter's outcome, edit-apply failures, blocking
  validator rules, the gate ids that failed or reported with the render time,
  the reviewer's verdict and defect ids, and the run's result; the model line
  carries the token counts by kind, and the judges report input and output
  tokens separately. The harness prices and counts from these lines, and
  none of them carries code, data or model text.
