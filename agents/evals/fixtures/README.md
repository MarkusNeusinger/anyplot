# Eval fixture cases

Each directory under `cases/` is one case of the regression harness (`agents/evals/matrix.py`) and a development seed for `adk web` (`AGENT_DEV_FIXTURE=<case-id>`):

| File | Contents |
|---|---|
| `case.json` | `spec_id`, `library`, `locale`, `bindings` (`[{"role", "column"}]`), `expected` (`accepted`, `rejected` or `unknown`), `tags`, and optionally `perturbation` and `source` (where the data comes from) |
| `data.csv` | The dataset, synthetic; sent to the `/dataset` route exactly as a user would paste it |
| `snapshot.json` | Optional: the catalogue snapshot (`spec_id`, `title`, `description`, `data_roles`, `notes`, `code`, `library_version`). Without it the snapshot is built from `plots/<spec_id>/` in this checkout |
| `change_request.txt` | Optional: a follow-up message the harness sends after the plot is created |
| `standin.txt` | Stress cases only, optional: the middle of a hand-written working form, a stand-in for the adapter's answer that the static stage renders without a model |

A stress case's `case.json` also carries `bound_expected` (the gate, limit or error that must bound it), `needs_model`, `static` and `render` (what the static stage must measure), and for an injection case `marker`; `agents/evals/make_stress.py` documents each field.

There are 145 cases:

- **120 generated cases** `<spec>-<library>-<perturbation>`: 10 specs times matplotlib and seaborn times 6 perturbations (`renamed`, `x10`, `n12`, `n5000`, `date`, `decimal-comma`), written by `agents/evals/make_fixtures.py`. Never edit them by hand: change the generator and rerun `uv run --extra agents python -m agents.evals.make_fixtures`. Its docstring lists the specs, why each was chosen, and what each perturbation does.
- **2 hand-written cases**, `scatter-basic-matplotlib` and `bar-grouped-seaborn`, which the runtime tests also use.
- **23 stress cases** `stress-<name>`, written by `agents/evals/make_stress.py` (rerun `uv run --extra agents python -m agents.evals.make_stress`): data at and one past the parser's caps, many categories, degenerate data, prompt injection, and requests that make the code compute mass data. They carry the tag `stress`; `--cases stress` selects them and `--cases full` leaves them out, so a full run keeps its 122 cases.

The tag `smoke` marks the 12 cases of `--cases smoke`: one generated case per spec, cycling through the perturbations and both libraries, plus the two hand-written cases.

Fixture data is invented. Never commit a user's data here: everything under `fixtures/` ships under the repository's MIT licence. Promoted feedback cases live in the private case bucket and are synced into the git-ignored `agents/evals/.cases/`, which the image build also excludes.
