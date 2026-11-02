# anyplot-renderer: the Cloud Run service that runs adapted plot code in sandboxes
# (agents/renderer/, docs/concepts/agent-network.md "Render" and "Serving and
# infrastructure").
#
# Two jobs in one image. The service process (uvicorn agents.renderer.main:app)
# launches sandboxes through Cloud Run's `sandbox do`, and every sandbox runs
# `/app/.venv/bin/python -I -X disable-remote-debug /opt/anyplot/harness.py plot.py` from this same image:
# a sandbox sees the image read-only (spike S), so the venv and the harness here
# are what model-written code runs with. The `fonts` stage below supplies the
# multi-script fallback fonts the harness appends to every lookup. The local
# Docker backend (AGENT_RENDERER=local, development only) runs this image too:
#
#   docker build -f agents/renderer/toolchain.Dockerfile -t anyplot-toolchain:dev .
#   docker build -f agents/renderer/Dockerfile -t anyplot-renderer:dev .
#
# The base is the toolchain image (agents/renderer/toolchain.Dockerfile, step 2a of
# agentic/specs/261024-agent-all-libraries.md): python:3.14-slim with the language
# toolchains of the exec-mode rows and the exec filter's preload library.
# TOOLCHAIN_IMAGE and TOOLCHAIN_TAG name it; the deploy and the CI job pass the
# repository and the tag of the toolchain's input hash with its digest
# (`t-<hash>@sha256:<digest>`, agents/renderer/toolchain.py), and the defaults are the
# local build above. Two arguments rather than one reference, so the FROM line names a
# tag.
#
# The builder and the runtime stage have the two-stage shape of api/Dockerfile
# (read its comments for the uv pin, the bytecode trade and why the stages share
# one base image: here both are the toolchain); the `fonts` stage between them only
# stages font files. The build CONTEXT is the repo root, and the root
# `.dockerignore` is an allowlist: `agents`, `pyproject.toml`, `uv.lock` and
# `README.md` are in it, so the COPYs below see them.
ARG TOOLCHAIN_IMAGE=anyplot-toolchain
ARG TOOLCHAIN_TAG=dev

FROM ${TOOLCHAIN_IMAGE}:${TOOLCHAIN_TAG} AS toolchain

FROM toolchain AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv==0.10.9

ENV UV_COMPILE_BYTECODE=1
ENV UV_PYTHON=/usr/local/bin/python3.14
ENV UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock README.md ./

# The base dependencies carry the service (fastapi, uvicorn, pydantic-settings) and
# the six `lib-*` extras carry the Python plotting stack the harness runs in process:
# matplotlib and seaborn (phase 1), plotnine and altair (step 1b of
# agentic/specs/261024-agent-all-libraries.md), pygal and lets-plot (step 1c).
# altair renders through vl-convert, a self-contained binary (V8 and resvg) that
# needs no browser and no system library. pygal's PNG export is cairosvg, which
# loads libcairo through cairocffi: the runtime stage installs `libcairo2`.
# lets-plot rasterises in its own native bridge (Kotlin/Native with ImageMagick
# and fontconfig linked in), which needs only the libraries the slim image has.
# Their fonts are set up in the runtime stage below. The bridge's ImageMagick is a
# zero-configuration build: it reads no policy.xml from any path (MAGICK_CONFIGURE_PATH,
# MAGICK_HOME and $HOME included, 2026-10-26), so no policy file can narrow it, and
# its compiled-in delegates run gs, curl, soffice, ffmpeg and others by name. This
# image installs none of them; ci-image.yml fails when one is on the sandbox's PATH.
# No ADK: nothing in the renderer imports it. `--no-install-project` keeps the
# project itself out of the venv, so a sandbox's interpreter finds no anyplot
# package on its path; the service imports `agents.renderer` from the working
# directory, which uvicorn puts on `sys.path`.
# The `convert` extra (python-calamine, pyarrow) is the file conversion's readers
# (`harness.py --convert`, agents/anyplot/render/convert.py).
# plotly and bokeh (PB-1 of step 4) run in the harness's figure mode: the plot
# writes its figure as JSON, and the JavaScript row's harness draws it with the
# package's own bundled JavaScript (plotly's package_data/plotly.min.js, bokeh's
# server/static/js/*.min.js), so the page's version is the plot's. Their image
# export stacks stay out: kaleido with choreographer and logistro, Selenium with
# webdriver-manager, trio and the WebSocket clients. Each starts a browser, which
# the plot guard refuses anyway, and Selenium alone carries 27 MB of drivers; a
# plot that saves through them fails with the package's own "not installed"
# message instead. What the two extras add is plotly, bokeh, tornado and
# xyzservices.
RUN uv venv && uv sync --frozen --no-install-project --extra lib-matplotlib --extra lib-seaborn \
    --extra lib-plotnine --extra lib-altair --extra lib-pygal --extra lib-letsplot --extra convert \
    --extra lib-plotly --extra lib-bokeh \
    --no-install-package kaleido --no-install-package choreographer --no-install-package logistro \
    --no-install-package simplejson --no-install-package selenium --no-install-package webdriver-manager \
    --no-install-package trio --no-install-package trio-websocket --no-install-package outcome \
    --no-install-package sortedcontainers --no-install-package wsproto --no-install-package websocket-client \
    --no-install-package pysocks

# pyarrow ships far more than the converter reads (owner decision of 2026-10-15: slim it).
# The conversion needs the core, compute, IPC, Feather and Parquet; it never touches
# Flight, the cloud and HDFS filesystems, ORC, Substrait's Python module, Parquet
# encryption or the C++ test module, nor the headers, Cython sources and tests a build
# against pyarrow would use. libarrow_substrait itself stays: `lib` links it. Of the
# three identical copies of libarrow_python only the one the modules load by its soname
# stays. 163 MB installed become 99 MB; the CI job converts every format inside the
# built image (`tests/image/convert_smoke.py`), so a removed file that is needed fails it.
RUN p=.venv/lib/python3.14/site-packages/pyarrow \
    && du -sh "$p" \
    && rm -rf "$p/include" "$p/includes" "$p/src" "$p/tests" \
    && find "$p" \( -name '*.pxd' -o -name '*.pyx' -o -name '*.pxi' \) -delete \
    && rm -f "$p"/_flight.cpython-*.so "$p"/libarrow_flight.so.* "$p"/libarrow_python_flight.so* \
        "$p"/_s3fs.cpython-*.so "$p"/libarrow_s3.so.* \
        "$p"/_azurefs.cpython-*.so "$p"/_gcsfs.cpython-*.so "$p"/_hdfs.cpython-*.so \
        "$p"/_orc.cpython-*.so "$p"/_dataset_orc.cpython-*.so \
        "$p"/_substrait.cpython-*.so "$p"/_pyarrow_cpp_tests.cpython-*.so \
        "$p"/_parquet_encryption.cpython-*.so "$p"/_dataset_parquet_encryption.cpython-*.so \
        "$p"/libarrow_python_parquet_encryption.so* \
        "$p"/libarrow_python.so "$p"/libarrow_python.so.*.*.* \
    && du -sh "$p" \
    && .venv/bin/python -c "import pyarrow.parquet, pyarrow.feather, pyarrow.ipc, pyarrow.compute"

# plotly and bokeh ship JavaScript that neither step of figure mode reads (PB-1): plotly's
# JupyterLab extension and Jupyter widget bundle, bokeh's TypeScript compiler for custom
# models (it runs Node, which plot code cannot start), its ES module sources and the
# unminified twins of its bundles. The page loads the minified bundles alone
# (`automation/js-render/render.mjs`, FIGURES), which stay with MathJax's, and so does every
# Python module. The two packages' 94 MB installed (bytecode included) become 68 MB, and the
# image grows by 69 MB in all (2026-10-31); the imports below and the CI job's plotly and
# bokeh renders fail on a file that is needed.
RUN p=.venv/lib/python3.14/site-packages \
    && du -shc "$p/plotly" "$p/bokeh" \
    && rm -rf "$p/plotly/labextension" "$p/plotly/package_data/widgetbundle.js" \
        "$p/bokeh/server/static/js/compiler.js" "$p/bokeh/server/static/js/lib" \
    && for f in bokeh bokeh-api bokeh-gl bokeh-mathjax bokeh-tables bokeh-widgets; do \
         test -s "$p/bokeh/server/static/js/$f.min.js" && rm "$p/bokeh/server/static/js/$f.js"; \
       done \
    && du -shc "$p/plotly" "$p/bokeh" \
    && .venv/bin/python -c "import plotly.graph_objects, plotly.express, plotly.io, bokeh.plotting, bokeh.embed, bokeh.models, bokeh.layouts"

# The image does not install the project, so its version is written to a file
# that `GET /status` reports.
RUN .venv/bin/python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" > VERSION


# Multi-script fallback fonts for plot text (docs/concepts/agent-network.md "Render"):
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
FROM python:3.14-slim AS fonts

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


FROM toolchain

WORKDIR /app

# libcairo for cairosvg, pygal's PNG export (cairocffi finds it with `ldconfig -p`;
# the harness loads it before the plot guard is armed, `warm_cairo`). Without the
# recommends it brings libfontconfig1, fontconfig-config (which writes
# /etc/fonts/fonts.conf), fonts-dejavu-core and fonts-dejavu-mono (DejaVu Sans,
# Serif and Sans Mono, Regular and Bold, under /usr/share/fonts/truetype/dejavu),
# libfreetype6, libpixman-1-0, libpng16-16t64 and the X11 client libraries
# cairo links. No `fontconfig` package, so no `fc-list` for matplotlib to call.
# DL3008 is declined for the reason the `fonts` stage gives.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv ./.venv

# Only the renderer package and the package marker of `agents/`: the rest of
# agents/ (the ADK runtime, the prompts) has no business in an image whose files
# every sandbox can read.
COPY agents/__init__.py ./agents/__init__.py
COPY agents/renderer/ ./agents/renderer/
COPY --from=builder /app/VERSION ./agents/renderer/VERSION
COPY agents/anyplot/render/harness.py /opt/anyplot/harness.py
COPY agents/anyplot/render/convert.py /opt/anyplot/convert.py
# The R and Julia rows' text probes (R_TEXT_PROBE and JULIA_TEXT_PROBE in agents/renderer/commands.py).
COPY agents/anyplot/render/text_probe.R agents/anyplot/render/text_probe.jl /opt/anyplot/

# lets-plot's native ImageMagick starts its delegate programs (Ghostscript, curl,
# ffmpeg, ...) by name from PATH, where the plot guard's audit hook cannot see a
# process start, and it reads no policy that could forbid them. The build fails when
# one of them is on the sandbox's PATH (agents/renderer/delegates.py), so every build
# of this file enforces it: the Cloud Build deploy as well as the CI image job.
RUN .venv/bin/python -m agents.renderer.delegates

# The fallback fonts and their OFL notices. matplotlib scans /usr/share/fonts
# recursively without fontconfig (font_manager.findSystemFonts), so one
# directory is enough; it must be in place before the cache bake below.
COPY --from=fonts /fonts/noto /usr/share/fonts/noto
COPY --from=fonts /fonts/doc /usr/share/doc/fonts-noto

# vl-convert (altair) scans /usr/share/fonts, so the fallback fonts above reach it
# too, and it carries Liberation Sans for `sans-serif`. `serif` and `monospace` (7
# catalogue altair files) resolve only to DejaVu Serif and DejaVu Sans Mono and draw
# no text at all without them (measured 2026-10-25). lets-plot's bridge draws its
# default text in DejaVu Sans and falls back to a Noto Sans face without it; with
# it, a render in this image is byte-identical to one on a developer machine
# (spike of 2026-10-26). matplotlib ships all three families in four styles, so
# they are linked here, not copied: no new font file and no size. matplotlib still
# resolves every family to its own mpl-data copy, which comes first in its font
# list: Debian's builds of the Regular and Bold faces that libcairo2 brings (other
# bytes, same names) changed none of ci-image.yml's seaborn, plotnine, altair and
# multi-script renders against the image without them (2026-10-26). `ls -L` fails
# the build on a dangling link.
RUN d=/app/.venv/lib/python3.14/site-packages/matplotlib/mpl-data/fonts/ttf \
    && mkdir -p /usr/share/fonts/dejavu \
    && for f in DejaVuSans DejaVuSans-Bold DejaVuSans-Oblique DejaVuSans-BoldOblique \
        DejaVuSerif DejaVuSerif-Bold DejaVuSerif-Italic DejaVuSerif-BoldItalic \
        DejaVuSansMono DejaVuSansMono-Bold DejaVuSansMono-Oblique DejaVuSansMono-BoldOblique; do \
        ln -s "$d/$f.ttf" "/usr/share/fonts/dejavu/$f.ttf"; \
    done \
    && ls -L /usr/share/fonts/dejavu/*.ttf > /dev/null

# lets-plot's bridge links its own fontconfig, which finds no configuration in this
# image's layout and writes "Fontconfig error: Cannot load default config file" to
# stderr on every export. Its command row points FONTCONFIG_FILE here
# (agents/renderer/commands.py): one <dir> and no <cachedir>, so it scans the fonts
# above and never writes a cache (the root filesystem is read-only anyway).
COPY agents/renderer/fonts.conf /opt/anyplot/fonts.conf

# Bake the matplotlib font cache. A sandbox starts with an empty private /tmp, and
# the harness copies this directory into MPLCONFIGDIR=/tmp/mpl before matplotlib
# loads (spike S: faster than rebuilding the cache in every render). The same
# import builds the cache, and `check_fonts` fails the build when DejaVu Sans or
# a family of FALLBACK_FAMILIES is not in it (a renamed or dropped font file).
# The `chmod` names this file's own entries under /opt/anyplot: the toolchain's
# (the exec filter, the JavaScript row's packages, fonts and harness) are
# world-readable already, and a recursive `chmod` would copy all 170 MB of them into
# this layer.
RUN mkdir -p /opt/mplconfig \
    && MPLCONFIGDIR=/opt/mplconfig .venv/bin/python -I -c "import sys; sys.path.insert(0, '/opt/anyplot'); import harness; harness.check_fonts()" \
    && chmod -R a+rX /opt/mplconfig /opt/anyplot/harness.py /opt/anyplot/convert.py /opt/anyplot/fonts.conf \
       /opt/anyplot/text_probe.R /opt/anyplot/text_probe.jl \
       /usr/share/fonts/noto /usr/share/doc/fonts-noto

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
