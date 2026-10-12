# anyplot-renderer: the Cloud Run service that runs adapted plot code in sandboxes
# (agents/renderer/, docs/concepts/agent-network.md "Render" and "Serving and
# infrastructure").
#
# Two jobs in one image. The service process (uvicorn agents.renderer.main:app)
# launches sandboxes through Cloud Run's `sandbox do`, and every sandbox runs
# `/app/.venv/bin/python -I /opt/anyplot/harness.py plot.py` from this same image:
# a sandbox sees the image read-only (spike S), so the venv and the harness here
# are what model-written code runs with. The `fonts` stage below supplies the
# multi-script fallback fonts the harness appends to every lookup. The local
# Docker backend (AGENT_RENDERER=local, development only) runs this image too:
#
#   docker build -f agents/renderer/Dockerfile -t anyplot-renderer:dev .
#
# The builder and the runtime stage have the two-stage shape of api/Dockerfile
# (read its comments for the uv pin, the bytecode trade and why the stages share
# one base image); the `fonts` stage between them only stages font files. The
# build CONTEXT is the repo root, and the root `.dockerignore` is an allowlist:
# `agents`, `pyproject.toml`, `uv.lock` and `README.md` are in it, so the COPYs
# below see them.

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


# Fonts for plot text in any script (docs/concepts/agent-network.md "Render"):
# the harness appends these families to every font lookup, after the font the
# code chose, so DejaVu Sans stays the catalogue's look and Chinese, Japanese,
# Korean, Arabic, Hebrew, Thai, the Indic scripts, Khmer, Myanmar, Ethiopic and
# the symbol blocks still draw. A stage of its own: the runtime image gets the
# font files, the two copyright notices (OFL 1.1) and the package versions, never
# apt's lists or dpkg's database. Only the 37 allowlisted files are staged (46.8 MB; the whole packages
# are 134 MB, the Serif CJK pair alone 51 MB), Regular and Bold where the
# package has one, and `cp` fails the build on a file the package stops shipping.
# The family names the harness uses (FALLBACK_FAMILIES in harness.py) are the
# name-table names of these files; the cache bake below checks each one resolves.
#
# DL3008 (pin the apt versions) is declined here for the reason api/Dockerfile
# gives: a pinned Debian point release breaks the build on the next security
# update of the base image, and font packages carry no version-sensitive
# behaviour that a pin would protect. The installed versions travel with the
# notices (versions.txt), and the CI job prints them.
FROM python:3.13-slim AS fonts

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-core \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /fonts/noto /fonts/doc \
    && for family in NotoSans NotoSansArabic NotoSansHebrew NotoSansThai NotoSansDevanagari \
        NotoSansBengali NotoSansTamil NotoSansTelugu NotoSansGujarati NotoSansGurmukhi \
        NotoSansKannada NotoSansMalayalam NotoSansSinhala NotoSansKhmer NotoSansMyanmar \
        NotoSansEthiopic NotoSansSymbols; do \
        cp "/usr/share/fonts/truetype/noto/$family-Regular.ttf" \
           "/usr/share/fonts/truetype/noto/$family-Bold.ttf" /fonts/noto/; \
    done \
    && cp /usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf /fonts/noto/ \
    && cp /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
          /usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc /fonts/noto/ \
    && cp /usr/share/doc/fonts-noto-core/copyright /fonts/doc/fonts-noto-core.copyright \
    && cp /usr/share/doc/fonts-noto-cjk/copyright /fonts/doc/fonts-noto-cjk.copyright \
    && dpkg-query -W fonts-noto-core fonts-noto-cjk > /fonts/doc/versions.txt


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

# The fallback fonts and their OFL notices. matplotlib scans /usr/share/fonts
# recursively without fontconfig (font_manager.findSystemFonts), so one
# directory is enough; it must be in place before the cache bake below.
COPY --from=fonts /fonts/noto /usr/share/fonts/noto
COPY --from=fonts /fonts/doc /usr/share/doc/fonts-noto

# Bake the matplotlib font cache. A sandbox starts with an empty private /tmp, and
# the harness copies this directory into MPLCONFIGDIR=/tmp/mpl before matplotlib
# loads (spike S: faster than rebuilding the cache in every render). The same
# import builds the cache, and `check_fonts` fails the build when DejaVu Sans or
# a family of FALLBACK_FAMILIES is not in it (a renamed or dropped font file).
RUN mkdir -p /opt/mplconfig \
    && MPLCONFIGDIR=/opt/mplconfig .venv/bin/python -I -c "import sys; sys.path.insert(0, '/opt/anyplot'); import harness; harness.check_fonts()" \
    && chmod -R a+rX /opt/mplconfig /opt/anyplot /usr/share/fonts/noto /usr/share/doc/fonts-noto

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
