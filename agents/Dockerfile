# anyplot-agents: the private `/v1` service in front of the ADK runner
# (agents/main.py, docs/concepts/agent-network.md "Serving and infrastructure").
#
# The service composes prompts, calls the models, runs the deterministic gates and
# keeps the sessions in memory. It runs no user code: every render goes to the
# anyplot-renderer service through the `remote` backend, so this image carries no
# sandbox launcher, no harness entry point and no baked matplotlib font cache
# (those belong to agents/renderer/Dockerfile). Build it from the repository root:
#
#   docker build -f agents/Dockerfile -t anyplot-agents:dev .
#
# Same two-stage shape as api/Dockerfile (read its comments for the uv pin, the
# bytecode trade and why both stages share one base image). The build CONTEXT is
# the repo root, and the root `.dockerignore` is an allowlist: `agents` (without
# `agents/evals`), `core`, the catalogue prompt files below, `pyproject.toml`,
# `uv.lock` and `README.md` are in it, so the COPYs below see them and nothing else.

FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv==0.10.9

ENV UV_COMPILE_BYTECODE=1
ENV UV_PYTHON=/usr/local/bin/python3.14
ENV UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock README.md ./

# The base dependencies carry FastAPI, uvicorn, pydantic-settings, Pillow (the
# footer strip), PyYAML (the refusals), httpx and google-auth (the renderer's ID
# token); the `agents` extra adds ADK and the Claude backend. No plotting extra:
# nothing this service imports draws a plot (an import of `agents.main` loads
# neither matplotlib nor seaborn). The project itself IS installed, unlike in the
# renderer image, because `GET /v1/status` reports its version from the installed
# distribution's metadata (`importlib.metadata.version("anyplot")`).
RUN uv venv && uv sync --frozen --extra agents

# tree-sitter-language-pack 0.13.0 bundles about 170 compiled grammars, 184 MB
# installed, so that nothing is downloaded at run time. The service reads only the
# grammars of its code profiles (`GRAMMARS` in agents/anyplot/code/treesitter.py:
# R and Julia, 0.6 MB and 2.7 MB, and since JS-3 JavaScript and TSX for the five
# JavaScript libraries, 0.5 MB and 1.6 MB; each later profile adds its own here), so every
# other one goes, `typescript` (TypeScript without JSX) among them, and the build fails
# when a kept grammar no longer loads. The pack's own imports (tree_sitter_c_sharp, _yaml,
# _embedded_template) stay: it imports them on load.
# tests/unit/agents/code/test_treesitter.py ties this list to `GRAMMARS`.
ARG TREE_SITTER_GRAMMARS="r julia javascript tsx"
RUN bindings=.venv/lib/python3.14/site-packages/tree_sitter_language_pack/bindings \
    && for library in "$bindings"/*.so; do \
         grammar="$(basename "$library")"; \
         case " $TREE_SITTER_GRAMMARS " in *" ${grammar%%.*} "*) ;; *) rm "$library" ;; esac; \
       done \
    && .venv/bin/python -c "import sys, tree_sitter_language_pack as pack; [pack.get_language(g) for g in sys.argv[1:]]" \
         $TREE_SITTER_GRAMMARS


FROM python:3.14-slim

WORKDIR /app

# Create the non-root user BEFORE the copies, so `COPY --chown` can name it.
RUN useradd -m -u 1000 appuser

COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv

# The source tree, not a wheel: the service reads files next to its modules, and
# package data is not in a wheel. Each COPY keeps the repository's relative path,
# because the readers resolve them from `__file__`:
#
# - `agents/` brings the prompts (`agents/anyplot/prompts/*.md`, `refusals.yaml`),
#   the footer-strip fonts (`agents/anyplot/render/fonts/`, read at import, so a
#   missing file stops the service at start) and `agents/renderer/wire.py`, the
#   JSON contract the `remote` backend shares with the renderer. The root
#   `.dockerignore` keeps `agents/evals` out: its promoted cases hold users' data.
# - `core/` for the palette, the canvas checks and the catalogue constants.
# - The catalogue prompt sources the adapter and the reviewer read verbatim from
#   `prompts/` (agents/anyplot/policy.py): the style guide, every library file and
#   three excerpts cut out by heading.
#
# tests/unit/agents/test_image.py holds this list against every non-Python file the
# service reads, and against the root `.dockerignore`.
COPY --chown=appuser:appuser agents/ ./agents/
COPY --chown=appuser:appuser core/ ./core/
COPY --chown=appuser:appuser prompts/default-style-guide.md prompts/quality-criteria.md ./prompts/
COPY --chown=appuser:appuser prompts/library/ ./prompts/library/
COPY --chown=appuser:appuser prompts/workflow-prompts/impl-repair-claude.md prompts/workflow-prompts/ai-quality-review.md ./prompts/workflow-prompts/

USER appuser

# Our code arrives through the COPYs without bytecode (the root `.dockerignore`
# drops `__pycache__`), so compile it here, as appuser, like api/Dockerfile does.
RUN .venv/bin/python -m compileall -q agents core

# Fail the build, not the first request, when a prompt source or a font is
# missing: `agent.py` composes every static instruction at import and
# `render/watermark.py` parses both font files at import, and both raise on a
# missing file or a renamed heading. The judge model's three rubrics are read on
# first use, so the check reads them explicitly, and so does the scorer's prompt
# (`scoring.system_prompt`: `prompts/scorer.md` plus sections cut by heading from the
# catalogue rubric, with the experiment's highlight rule), and both reviewer
# instructions: the agent imports with one mode and switches at runtime
# (`AGENT_REVIEWER_MODE`), and the experiment prompts for highlights. The import builds the
# adapters of the default libraries only, so the check composes one adapter instruction per
# language with a runtime (`policy.RUNTIME_PROMPTS`: matplotlib for Python, ggplot2 for R, Makie
# for Julia, Chart.js for JavaScript), which reads that language's runtime prompt and the
# library rules. None of it needs credentials or makes a network call.
# tests/unit/agents/test_image.py runs this command and holds it against every file the
# service reads.
RUN .venv/bin/python -c "import agents.main; from agents.anyplot import policy, scoring; policy.scope_rubric(); policy.data_rubric(); policy.transcribe_rubric(); scoring.system_prompt(highlights=True); policy.catalogue_reviewer_instruction(); policy.reviewer_instruction(); policy.highlights_prompt('python'); policy.highlights_prompt('r'); policy.highlights_prompt('julia'); policy.highlights_prompt('javascript'); policy.adapter_instruction('matplotlib'); policy.adapter_instruction('plotly'); policy.adapter_instruction('bokeh'); policy.adapter_instruction('ggplot2'); policy.adapter_instruction('makie'); policy.adapter_instruction('chartjs')"

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080

# No HEALTHCHECK: Cloud Run ignores it, and the deploy smoke (agents/cloudbuild.yaml)
# asks `GET /v1/status` through Cloud Run IAM instead.
CMD [".venv/bin/uvicorn", "agents.main:app", "--host", "0.0.0.0", "--port", "8080"]
