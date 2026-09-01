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

FROM python:3.13-slim AS builder

WORKDIR /app

# No build-essential: the image's actual install set is 108 packages and every
# one of them ships a wheel, so nothing is ever compiled here. (The two
# sdist-only entries in uv.lock, esprima and matplotlib-venn, belong to the
# `plotting` extra, which this image does not install.) The toolchain was
# ~110 MB that only ever sat there. If a future dependency arrives sdist-only,
# the build fails loudly at this step — the right place to notice.
RUN pip install --no-cache-dir uv

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

# Copy application code
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser core/ ./core/
COPY --chown=appuser:appuser plots/ ./plots/

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

# Expose port 8000 for FastAPI
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Run FastAPI app with uvicorn
# Cloud Run provides PORT env var, default to 8000
CMD [".venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
