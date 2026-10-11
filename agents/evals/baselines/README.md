# Eval baselines

Each file here is a full report of the regression harness (`agents/evals/matrix.py`), named after the model it ran: `claude-haiku-5-5.json` for the pinned default, `gemini-3.8-flash.json` for the Gemini arm. A harness run compares itself with the pinned model's baseline by default, over the cases both reports hold, and exits with code 1 when its pass rate on those cases falls more than the tolerance below the baseline's.

`claude-haiku-5-5.json` is the thinking arm of the measurement of 2026-10-11 on main at `e2e25ef61` (the reviewer package, the stress cases, the guardrails and the adapter hardening merged), rerun with the thinking-block binding control: 122 cases with 1 run each, at most 2 attempts per run, root thinking 1,024 and adapter thinking 2,048 (the defaults since that day), on `eu` through the deployed `anyplot-renderer`. All 122 runs passed the gates (100 %, no error runs), 62 ended `ok` (50.8 %), the median cost per passed plot was $0.0062 and the run cost $0.75 at list price; the first thinking run of that day, without the binding control, had 2 error runs and 51.6 % `ok`. It replaces the rerun of spike X of 2026-10-10 (244 runs, 90.6 % passed, 23.4 % `ok`, thinking off), kept in the git history. The Gemini arm's run creates `gemini-3.8-flash.json` the same way (see "Run spike X" in `agents/README.md`):

```bash
uv run --extra agents python -m agents.evals.matrix --cases full --save-baseline ...
```

Review the run's gallery before you commit the file. `--save-baseline` refuses a run that stopped early, included promoted cases (`agents/evals/.cases/`, which hold users' data, while a baseline is committed), or has any run that ended in an error (a harness crash or a pipeline `error`, which measures an outage or a bug, not the model). Once a baseline exists, `tests/unit/agents/evals/test_baselines.py` requires one for the pinned model, so a model bump adds the new model's baseline in the same PR.
