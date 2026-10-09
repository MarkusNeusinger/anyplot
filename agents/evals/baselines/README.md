# Eval baselines

Each file here is a full report of the regression harness (`agents/evals/matrix.py`), named after the model it ran: `claude-haiku-5-5.json` for the pinned default, `gemini-3.8-flash.json` for the Gemini arm. A harness run compares itself with the pinned model's baseline by default and exits non-zero when its pass rate falls more than the tolerance below it.

No baseline is committed yet. The first spike-X run on the Claude arm creates `claude-haiku-5-5.json`:

```bash
uv run --extra agents python -m agents.evals.matrix --cases full --save-baseline ...
```

Review the run's gallery before you commit the file. `--save-baseline` refuses a run that stopped early or included promoted cases (`agents/evals/.cases/`), because those hold users' data and a baseline is committed. Once a baseline exists, `tests/unit/agents/evals/test_baselines.py` requires one for the pinned model, so a model bump adds the new model's baseline in the same PR.
