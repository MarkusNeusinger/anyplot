# Eval baselines

Each file here is a full report of the regression harness (`agents/evals/matrix.py`), named after the model it ran: `claude-haiku-5-5.json` for the pinned default, `gemini-3.8-flash.json` for the Gemini arm. A harness run compares itself with the pinned model's baseline by default, over the cases both reports hold, and exits with code 1 when its pass rate on those cases falls more than the tolerance below the baseline's.

`claude-haiku-5-5.json` is the first spike-X run on the Claude arm (2026-10-10: 122 cases, 102 passed the gates, $0.52 at list price). The Gemini arm's run creates `gemini-3.8-flash.json` the same way (see "Run spike X" in `agents/README.md`):

```bash
uv run --extra agents python -m agents.evals.matrix --cases full --save-baseline ...
```

Review the run's gallery before you commit the file. `--save-baseline` refuses a run that stopped early, included promoted cases (`agents/evals/.cases/`, which hold users' data, while a baseline is committed), or has any run that ended in an error (a harness crash or a pipeline `error`, which measures an outage or a bug, not the model). Once a baseline exists, `tests/unit/agents/evals/test_baselines.py` requires one for the pinned model, so a model bump adds the new model's baseline in the same PR.
