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

## Stress cases: what bounds them

Measured with the static stage on 2026-10-10 (WSL2, 32 cores; the stand-ins rendered through `harness.py` with the renderer's limits: 60 s CPU, 1 GiB address space, one BLAS thread). Parse times are the in-process `parse_dataset`; the renderer's 2 vCPU are slower. "Adapter request" is the rendered adapter input in characters, catalogue code included. CPU and peak memory are the harness's own end line; wall time is the harness process from start to exit. Launch the harness from a shell when you measure it again: `ru_maxrss` keeps a parent's peak across `exec`, so a harness that a Python process starts reports at least that process's memory.

| Case | Bound | Measured |
|---|---|---|
| `cap-rows` | accepted at 204,800 bytes and 20,000 rows | parse 51 ms; adapter request 3,402 characters |
| `cap-columns` | accepted at 50 columns, 200-character cells, Unicode and bidi | parse 32 ms; profile 10,936 characters, untrimmed |
| `cap-profile` | `MAX_ADAPTER_PROFILE_BYTES` (16,384 bytes of UTF-8) trims the adapter's profile | full profile 27,907 characters (30,487 bytes), sent 7,225; adapter request 35,231 before the cap, 14,594 after |
| `csv-expansion` | the renderer's 2 MiB `data_csv` limit | canonical `data.csv` 771,800 bytes, 3.8 times the input |
| `over-bytes` | `413 too_long` before the parse | refused at 205,824 bytes |
| `over-rows`, `over-columns`, `over-cell` | `422 unparseable` (`too_many_rows`, `too_many_columns`, `cell_too_long`) | refused within 10 ms |
| `bar-100-categories` | G7 (advisory) | 99 overlapping tick-label pairs; 310 texts of the probe's 400; 1.8 s CPU (1.9 s wall), 131 MiB peak |
| `pie-30-slices` | the reviewer only | no gate fires: 92 texts, the legend covers the pie, small slices pile their labels; 1.0 s CPU (1.2 s wall), 127 MiB peak |
| `all-nan-column`, `mixed-decimals` | `422 invalid` at `PUT /bindings` | the column is typed text |
| `dates-centuries` | none needed | the parse types the column as a date (`date_columns` 1) and pandas 3 reads dates from 1066 to 2999 as datetime |
| `inject-header` | the `<user_data>` fence | judge, root, adapter and reviewer see it, always fenced |
| `inject-row4` | the `<user_data>` fence | the judge's three sample rows miss it; the adapter's five carry it, fenced |
| `inject-long-cell` | none in text; the reviewer sees it as pixels | no prompt carries it; only `data.csv` does |
| `compute-lorenz` | G9 (advisory) | 1,000,000 line points; 2.0 s CPU (2.1 s wall), 479 MiB peak; still renders with the address space cut to 610 MiB, fails at 605 MiB. At dt = 0.0001 (10,000,000 points) it peaks at 889 MiB (5.8 s CPU) and fails from 1,015 MiB down, a few MiB under the 1 GiB limit, so the case uses dt = 0.001 |
| `compute-oversample` | G9 (advisory) | 610,000 line points; 2.8 s CPU (2.9 s wall), 234 MiB peak |
| `compute-distances` | R1: `_ArrayMemoryError` under `RLIMIT_AS` | fails after 0.4 s CPU (0.6 s wall) asking for 18.6 GiB |

The other degenerate cases (`single-row`, `constant-series`, `duplicate-headers`, `empty-strings`) parse, bind and load; how the plot copes needs a model run.

Fixture data is invented. Never commit a user's data here: everything under `fixtures/` ships under the repository's MIT licence. Promoted feedback cases live in the private case bucket and are synced into the git-ignored `agents/evals/.cases/`, which the image build also excludes.
