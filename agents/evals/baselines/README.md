# Eval baselines

Each file here is a full report of the regression harness (`agents/evals/matrix.py`), named after the model it ran: `claude-haiku-5-5.json` for the pinned default, `gemini-3.8-flash.json` for the Gemini arm. A harness run compares itself with the pinned model's baseline by default, over the cases both reports hold, and exits with code 1 when its pass rate on those cases falls more than the tolerance below the baseline's.

`claude-haiku-5-5.json` is the rerun of spike X on main in the evening of 2026-10-10: 122 cases with 2 runs each, at most 2 attempts per run, on `eu` through the remote renderer with the drawn-text G3 probe. Its stamp names commit `6d0de1e0acd7`, which is main at `8de9fb737` plus the `AGENT_MAX_ATTEMPTS` setting at its default of 2, so the pipeline behaves as on main. 221 of 244 runs passed the gates (90.6 %), 57 ended `ok` (23.4 %), and the run cost $0.99 at list price. It replaces the first spike-X run of the same morning (122 runs, 83.6 % passed), which the probe's G3 false positive and the report schema 1 made a weaker reference. The Gemini arm's run creates `gemini-3.8-flash.json` the same way (see "Run spike X" in `agents/README.md`):

```bash
uv run --extra agents python -m agents.evals.matrix --cases full --save-baseline ...
```

Review the run's gallery before you commit the file. `--save-baseline` refuses a run that stopped early, included promoted cases (`agents/evals/.cases/`, which hold users' data, while a baseline is committed), or has any run that ended in an error (a harness crash or a pipeline `error`, which measures an outage or a bug, not the model). Once a baseline exists, `tests/unit/agents/evals/test_baselines.py` requires one for the pinned model, so a model bump adds the new model's baseline in the same PR.
