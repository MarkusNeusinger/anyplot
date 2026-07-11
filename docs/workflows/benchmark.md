# LLM Benchmark Generation (Vertex AI)

> Foundation for [#6913 — LLM Benchmark: Compare model performance across specs and libraries](https://github.com/MarkusNeusinger/anyplot/issues/6913).

`benchmark-generate.yml` generates the same (spec, library) implementation with several
different LLMs served by **Google Vertex AI**, so models can be compared on identical
inputs. One GCP authentication (the repo's existing Workload Identity Federation) covers
every model family — adding a model to the comparison is just another id in the `models`
input, no new secrets or SDK integrations:

| Model family | Example id | Vertex surface |
|---|---|---|
| Google Gemini | `gemini-2.5-pro` or `google/gemini-2.5-pro` | OpenAI-compatible chat-completions endpoint |
| Anthropic Claude | `claude-sonnet-4-5@20250929` or `anthropic/claude-sonnet-4-5@20250929` | Anthropic SDK Vertex transport (`AnthropicVertex`) |
| Model Garden MaaS partners | `meta/llama-3.3-70b-instruct-maas`, `mistralai/mistral-large-2411`, `qwen/…`, `deepseek-ai/…` | OpenAI-compatible chat-completions endpoint |

## How it differs from impl-generate

`impl-generate` runs Claude Code **agentically** (it iterates in a shell, renders, self-checks,
commits). Benchmark generation is deliberately **single-shot with error feedback**: every model
gets the exact same context the pipeline reads (base rules, Imprint style guide, library rules,
spec) and must answer with one self-contained code block. Render errors are fed back for up to
`max_attempts` tries. That keeps the comparison model-neutral — no model gets an agent harness
another lacks.

Benchmark output is **never** committed to `plots/` and never touches the catalog, metadata, or
GCS. Results are uploaded as a workflow artifact and summarized in the job summary.

## Running a benchmark

```bash
gh workflow run benchmark-generate.yml \
  -f specification_id=scatter-basic \
  -f library=matplotlib \
  -f models='google/gemini-2.5-pro,anthropic/claude-sonnet-4-5@20250929,meta/llama-3.3-70b-instruct-maas'
```

Inputs:

| Input | Default | Notes |
|---|---|---|
| `specification_id` | — | Any spec under `plots/` |
| `library` | `matplotlib` | **Python libraries only in v1** (they run on the workflow's own interpreter); R/Julia/JS reuse the existing setup actions in a later iteration |
| `models` | Gemini 2.5 Pro + Claude Sonnet 4.5 | Comma-separated Vertex model ids |
| `max_attempts` | `3` | Render errors are fed back to the model between attempts |
| `location` | `us-central1` | Region for Gemini / Model Garden |
| `anthropic_location` | `us-east5` | Claude on Vertex lives in its own region set |

Locally (with `gcloud auth application-default login`):

```bash
uv pip install -e ".[lib-matplotlib]" google-auth  # google-auth: ADC tokens for the Vertex client
python -m automation.benchmark.generate \
  --spec-id scatter-basic --library matplotlib \
  --model gemini-2.5-pro --output-dir benchmark-results
```

(`google-auth` usually arrives transitively via `google-cloud-storage`, but the
Vertex client imports it directly — install it explicitly to be safe.)

## Output layout

```
benchmark-results/<spec>/<library>/<model-slug>/
├── <library>.py               # last generated implementation
├── plot-light.png             # theme renders (when successful)
├── plot-dark.png
├── attempt-N-response.md      # raw model response per attempt
└── result.yaml                # accounting: provider, success, attempts,
                               # latency, tokens, canvas gate (both themes),
                               # fenced-output contract compliance, error
```

`result.yaml` is the record the future `/benchmark` leaderboard aggregates
(per issue #6913: quality scoring via the existing review rubric, persistence,
and site integration are follow-up phases).

## GCP prerequisites (one-time)

The workflow reuses the existing `google-github-actions/auth` WIF setup. For it to reach
Vertex AI, the project additionally needs:

1. **Vertex AI API enabled**: `gcloud services enable aiplatform.googleapis.com`
2. **IAM**: the WIF service account needs `roles/aiplatform.user`
3. **Partner models enabled once in the console** (Claude, Llama, Mistral, … each have an
   "Enable" step in Model Garden; Gemini needs no enablement)

Model availability is regional — if a call returns 404 for a model you enabled, check the
region inputs against the model's supported regions.
