# Multi-stage Dockerfile for the anyplot FastAPI backend on Cloud Run.
#
# Same shape as app/Dockerfile: a builder stage that installs, and a clean
# runtime stage that only receives the finished artefacts. The single-stage
# version this replaces carried 276.6 MB of ballast in a 502.0 MB image (55 %),
# in two layers that each had a named cause — see the comments at the apt and
# the COPY --chown lines below. The sibling repo kurrentschrift has the same
# fix; keep the two Dockerfiles in the same shape.
#
# Both stages MUST use the same base image: `uv venv` records the interpreter
# path in .venv/pyvenv.cfg and writes /app/.venv/bin shebangs, so the runtime
# stage has to offer the same interpreter at the same path (hence WORKDIR /app
# on both sides too).
#
# The build CONTEXT is the repo root — `core/`, `pyproject.toml` and `uv.lock`
# all live above `api/` — and what that context may contain is decided by the
# root `.dockerignore`, not by one under `api/`. Read that file before adding a
# COPY: it is an allowlist, so a path it does not name simply is not there.

FROM python:3.13-slim AS builder

WORKDIR /app

# No build-essential: the image's actual install set is 108 packages and every
# one of them ships a wheel, so nothing is ever compiled here. (The two
# sdist-only entries in uv.lock, esprima and matplotlib-venn, belong to the
# `plotting` extra, which this image does not install.) The toolchain was
# ~110 MB that only ever sat there. If a future dependency arrives sdist-only,
# the build fails loudly at this step — the right place to notice.
#
# uv is PINNED — the unpinned link in the DEPENDENCY chain, nothing wider than
# that. uv.lock fixes every package, but the resolver that reads it floated on
# whatever PyPI served that morning, and a resolver change is exactly the kind
# of difference that makes "it built yesterday" true and useless. The image as
# a whole is still not reproducible: `python:3.13-slim` is a mutable tag, and
# the apt packages in the runtime stage are deliberately unpinned for the reason
# given at their DL3008 line. Pinning uv also retires the DL3013 exception.
RUN pip install --no-cache-dir uv==0.10.9

# Write .pyc next to every installed module. Without this the venv ships source
# only — and the root `.dockerignore` excludes `__pycache__`, so the COPYs bring
# none either — which leaves every cold start compiling the whole import graph.
# Measured on this dependency set (2026-09-03): `import api.main` takes
# 3.56–4.43 s with nothing cached against 1.79–2.26 s with bytecode present,
# i.e. ~1.8 s off every cold start. It is not free — the compiled venv is
# 686.6 MB unpacked / 210.3 MB compressed against 493.1 / 142.3 — so the trade
# is ~68 MB of pulled layer against ~1.8 s of every container's first request.
ENV UV_COMPILE_BYTECODE=1
# Which interpreter the venv is built on, said out loud. uv otherwise picks one
# by discovery and may DOWNLOAD a managed CPython — a different build of 3.13
# than the runtime stage offers at the same path, which is the one thing the
# two-stage split cannot survive (see the note above about pyvenv.cfg).
ENV UV_PYTHON=/usr/local/bin/python3.13
ENV UV_PYTHON_DOWNLOADS=never

# Copy requirements first for better caching.
COPY pyproject.toml uv.lock README.md ./

# `--frozen` honors uv.lock instead of re-resolving from pyproject.toml —
# without it, uv picked up greenlet 3.5.0, which only ships macOS/Windows
# wheels and breaks the linux/amd64 Cloud Build image.
RUN uv venv && uv sync --frozen


FROM python:3.13-slim

WORKDIR /app

# curl serves the HEALTHCHECK below. libraqm0 is what actually turns Pillow's
# text shaping on: the manylinux wheel does NOT vendor Raqm, it dlopen()s
# libraqm at runtime, so in a bare python:3.13-slim `features.check('raqm')` is
# False and HarfBuzz/FriBiDi report no version at all. That is the whole of
# #10813's regression — and why the guard it added has failed every build of
# this image since (the deploy-api trigger has been red since 2026-08-30).
# The Debian package is 32 KB plus its HarfBuzz/FriBiDi dependencies.
#
# DL3008 (pin the apt versions) is declined here, not repo-wide: pinning a
# Debian point release breaks the build on every security update of the base
# image, and these two packages carry no version-sensitive behaviour.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libraqm0 \
    && rm -rf /var/lib/apt/lists/*

# Create the non-root user BEFORE the copies, so `COPY --chown` can name it.
RUN useradd -m -u 1000 appuser

# `COPY --chown` sets ownership as the layer is written. The old
# `RUN chown -R appuser:appuser /app` did it afterwards, which rewrites every
# touched file into a fresh layer and so duplicated the entire venv: 156.0 MB
# for a permission bit. The venv's executables keep their modes across COPY,
# so the `chmod -R 755 .venv/bin` that used to ride along is gone too.
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv

# Copy application code. `plots/` used to be copied here too and was never read:
# the implementations this API serves come from Postgres (core/database), and
# nothing under api/ or core/ opens a path below plots/ — ci-image.yml already
# says so where it explains why plots/** is not a build trigger. It cost 16.6 MB
# of every pulled image (69.2 MB unpacked, 9,166 files), measured as layer 10 of
# the `latest` manifest on 2026-09-03.
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser core/ ./core/

# Fail the build if Pillow cannot shape text. Without it Pillow falls back to
# its BASIC layout engine: the OG cards lose MonoLisa's italic `ss02` swashes
# and all kerning, and nothing in the response signals it — the only symptom is
# an off-brand PNG (#10813). This runs in the RUNTIME stage on purpose: the
# check is only meaningful against the image that actually serves. In the
# builder stage it would pass on a venv whose runtime never got libraqm0, which
# is precisely the false green this guard exists to prevent.
RUN .venv/bin/python -c "\
from PIL import features; \
assert features.check('raqm'), \
'Pillow cannot shape text — OG image text shaping would be disabled. The manylinux wheel dlopen()s libraqm at runtime, so the runtime stage must install libraqm0.'"

# Switch to non-root user
USER appuser

# The other half of UV_COMPILE_BYTECODE above: that one covers the venv, this
# one covers OUR code, which arrives through the COPYs and therefore has no
# .pyc of its own. Run as appuser, after the USER switch, so the __pycache__
# directories belong to the process that will read them — a root-owned cache in
# an appuser tree works, but only by accident of file modes.
# `-q` keeps the build log readable; a compile error still fails the build,
# which is the second thing this line buys: a syntax error in a module that
# only some request path imports now stops the IMAGE instead of a request.
RUN .venv/bin/python -m compileall -q api core

# Expose port 8000 for FastAPI
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check. DL3025 wants the JSON exec form, which cannot express the
# `|| exit 1` fallback — that needs a shell.
# hadolint ignore=DL3025
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Run FastAPI app with uvicorn
# Cloud Run provides PORT env var, default to 8000
CMD [".venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
