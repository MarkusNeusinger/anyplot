# anyplot-renderer: the Cloud Run service that runs adapted plot code in sandboxes
# (agents/renderer/, docs/concepts/agent-network.md "Render" and "Serving and
# infrastructure").
#
# Two jobs in one image. The service process (uvicorn agents.renderer.main:app)
# launches sandboxes through Cloud Run's `sandbox do`, and every sandbox runs
# `/app/.venv/bin/python -I /opt/anyplot/harness.py plot.py` from this same image:
# a sandbox sees the image read-only (spike S), so the venv and the harness here
# are what model-written code runs with. The local Docker backend
# (AGENT_RENDERER=local, development only) runs this image too:
#
#   docker build -f agents/renderer/Dockerfile -t anyplot-renderer:dev .
#
# Same two-stage shape as api/Dockerfile (read its comments for the uv pin, the
# bytecode trade and why both stages share one base image). The build CONTEXT is
# the repo root, and the root `.dockerignore` is an allowlist: `agents`,
# `pyproject.toml`, `uv.lock` and `README.md` are in it, so the COPYs below see them.

FROM python:3.13-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv==0.10.9

ENV UV_COMPILE_BYTECODE=1
ENV UV_PYTHON=/usr/local/bin/python3.13
ENV UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock README.md ./

# The base dependencies carry the service (fastapi, uvicorn, pydantic-settings) and
# the two extras carry the phase-1 plotting stack. No ADK: nothing in the renderer
# imports it. `--no-install-project` keeps the project itself out of the venv, so a
# sandbox's interpreter finds no anyplot package on its path; the service imports
# `agents.renderer` from the working directory, which uvicorn puts on `sys.path`.
RUN uv venv && uv sync --frozen --no-install-project --extra lib-matplotlib --extra lib-seaborn

# The image does not install the project, so its version is written to a file
# that `GET /status` reports.
RUN .venv/bin/python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" > VERSION


FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

# Only the renderer package and the package marker of `agents/`: the rest of
# agents/ (the ADK runtime, the prompts) has no business in an image whose files
# every sandbox can read.
COPY agents/__init__.py ./agents/__init__.py
COPY agents/renderer/ ./agents/renderer/
COPY --from=builder /app/VERSION ./agents/renderer/VERSION
COPY agents/anyplot/render/harness.py /opt/anyplot/harness.py

# Bake the matplotlib font cache. A sandbox starts with an empty private /tmp, and
# the harness copies this directory into MPLCONFIGDIR=/tmp/mpl before matplotlib
# loads (spike S: faster than rebuilding the cache in every render).
RUN mkdir -p /opt/mplconfig \
    && MPLCONFIGDIR=/opt/mplconfig .venv/bin/python -c "import matplotlib.font_manager as fm; fm.findfont('DejaVu Sans')" \
    && chmod -R a+rX /opt/mplconfig /opt/anyplot

RUN .venv/bin/python -m compileall -q agents

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080

# No `USER`: the service runs as the image default, root. `sandbox do` creates
# gVisor sandboxes (namespaces, mounts, the gofer that serves /work), which the
# launcher only does for root; spikes S and S2 ran the supervisor as root for that
# reason. What runs as root is the supervisor alone, which holds no secret and no
# role (its service account `anyplot-renderer@` has none). The model-written code
# runs inside the sandbox: uid 0 there too, but behind gVisor, with no network,
# no metadata server, a read-only root filesystem and the harness's rlimits.
CMD [".venv/bin/uvicorn", "agents.renderer.main:app", "--host", "0.0.0.0", "--port", "8080"]
