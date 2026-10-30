# anyplot-toolchain: the language toolchains the renderer runs in exec mode, on the
# renderer's own base (agentic/specs/261024-agent-all-libraries.md, step 2a). The
# renderer's Dockerfile builds FROM this image (TOOLCHAIN_IMAGE and TOOLCHAIN_TAG), its
# builder stage included, so the venv and the runtime see the same Python.
#
# It is built only when its inputs change. `agents/renderer/toolchain.py tag` hashes
# this file, agents/renderer/toolchain/, agents/renderer/execdeny/, the repository's
# Project.toml and Manifest.toml, its package.json and package-lock.json and
# automation/js-render/; the deploy (agents/renderer/cloudbuild.yaml) builds and
# pushes `anyplot-toolchain:<hash>` to the private Artifact Registry repository only when
# that tag is missing, and the CI job (ci-image.yml, renderer-image) pulls the tag or
# builds it. Locally:
#
#   docker build -f agents/renderer/toolchain.Dockerfile -t anyplot-toolchain:dev .
#
# One stage per toolchain, each `FROM base` into its own prefix, so a toolchain's change
# rebuilds its own stage and never another's (R's packages do not rerun Julia's
# precompile, and the reverse; Node with Chromium is the third). The build CONTEXT is the
# repo root and the root `.dockerignore` admits agents/, Project.toml, Manifest.toml,
# package.json, package-lock.json and automation/js-render/.
#
# The base is python:3.14-slim (Debian 13, owner decision of 2026-10-28), pinned by
# digest in the `base` stage below. Dependabot bumps the digest (.github/dependabot.yml,
# docker), which changes the hash, so the next deploy rebuilds the toolchain with the
# base's security updates. DL3008 (pin the apt versions) is declined for the reason
# agents/renderer/Dockerfile gives.

# The shared libraries R 4.6.1 and the CRAN binaries of r-packages.txt link, found with
# `ldd` on Posit's build and on every package's `.so` (2026-10-28), so R's own package,
# whose Depends pull in compilers, `-dev` packages, Tcl/Tk and X11, is unpacked without
# them. Reference BLAS and LAPACK, not OpenBLAS: they start no threads, which
# RLIMIT_NPROC counts. No Pango: only grDevices' cairo devices link it (every
# catalogue file saves through ragg::agg_png), and libpango-1.0-0 depends on the
# `fontconfig` package, whose fc-list and fc-match agents/renderer/delegates.py
# refuses on the sandbox's PATH. The `ldd` check below fails the build on a library
# this list misses.
ARG R_RUNTIME_LIBS="libblas3 liblapack3 libgomp1 libtirpc3t64 libicu76 libdeflate0 \
    libcurl4t64 libcairo2 libpng16-16t64 libtiff6 libjpeg62-turbo libwebp7 libwebpmux3 \
    libfreetype6 libfontconfig1 libharfbuzz0b libfribidi0"

# Julia's version is the one Manifest.toml was resolved with (`julia_version`), and its
# CPU target the one the renderer's Julia row sets at run time (JULIA_CPU_TARGET in
# agents/renderer/commands.py); tests/unit/agents/renderer/test_toolchain.py pins both.
# The target is the generic x86-64 code plus two clones, so one depot serves whichever
# x86-64 host Cloud Run schedules the renderer on.
ARG JULIA_VERSION=1.13.2
ARG JULIA_CPU_TARGET="generic;sandybridge,-xsaveopt,clone_all;haswell,-rdrnd,base(1)"

# The shared libraries Playwright's Chromium headless shell links, found with `ldd` on revision
# 1248 in this base (2026-10-30), and libdrm2 for the libgbm the `node` stage unpacks. None of
# them brings the `fontconfig` package or Pango: the shell links neither, and its built-in
# fontconfig reads the configuration that libfontconfig1 (R_RUNTIME_LIBS) installs. The `ldd`
# check below fails the build on a library this list misses.
ARG NODE_RUNTIME_LIBS="libasound2t64 libatk-bridge2.0-0t64 libatk1.0-0t64 libatspi2.0-0t64 libdbus-1-3 \
    libdrm2 libexpat1 libglib2.0-0t64 libnspr4 libnss3 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 \
    libxfixes3 libxkbcommon0 libxrandr2"


FROM python:3.14-slim@sha256:cd89c30eda26ee911a4611b18680086e0ea42e6f5f8cbe653d07fa7958c9cec8 AS base


# The exec filter of the exec-mode rows (agents/renderer/execdeny/execdeny.c, step 2b):
# compiled here, so the toolchain image carries no compiler.
FROM base AS execdeny

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*
COPY agents/renderer/execdeny/execdeny.c /src/execdeny.c
RUN mkdir -p /out && gcc -O2 -Wall -Wextra -Werror -shared -fPIC -o /out/libexecdeny.so /src/execdeny.c


# R: Posit's build of R 4.6.1 for debian-13, checked against its SHA-256, under
# /opt/R/4.6.1, and the packages of r-packages.txt as compiled binaries from the Posit
# Package Manager snapshot in r-repos.txt (trixie, the date `.github/actions/setup-r`
# pins), into R's own library. R's user agent makes the Package Manager serve
# binaries. `dependencies` is setup-r's: Depends, Imports and LinkingTo. `make` only runs
# the parallel installs (`Ncpus`); this stage's tools never reach the final image, which
# copies /opt/R alone.
FROM base AS r
ARG R_RUNTIME_LIBS
ARG R_VERSION=4.6.1
ARG R_DEB_SHA256=a4eb31ba37476102b92e171bcc654cfd935675d5993269bc0948ee44b4b55ca1
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl make ${R_RUNTIME_LIBS} \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL -o /tmp/r.deb "https://cdn.posit.co/r/debian-13/pkgs/r-${R_VERSION}_1_amd64.deb" \
    && echo "${R_DEB_SHA256}  /tmp/r.deb" | sha256sum -c - \
    && dpkg-deb -x /tmp/r.deb / \
    && rm /tmp/r.deb
COPY agents/renderer/toolchain/r-packages.txt agents/renderer/toolchain/r-repos.txt /opt/anyplot/toolchain/
RUN /opt/R/${R_VERSION}/bin/Rscript -e ' \
      packages <- readLines("/opt/anyplot/toolchain/r-packages.txt"); \
      packages <- packages[nzchar(packages) & !startsWith(packages, "#")]; \
      options(repos = c(CRAN = readLines("/opt/anyplot/toolchain/r-repos.txt", n = 1)), Ncpus = parallel::detectCores()); \
      install.packages(packages, lib = .Library, dependencies = c("Depends", "Imports", "LinkingTo")); \
      missing <- setdiff(packages, rownames(installed.packages())); \
      if (length(missing)) stop("not installed: ", paste(missing, collapse = ", ")) \
    ' \
    # No display and no Tk in a sandbox: the X11 device and data editor modules and the tcltk package go,
    # and with them the only links to X11, Xt, Tcl and Tk; grDevices' cairo devices (png(type = "cairo"),
    # cairo_pdf, svg) go with the only link to Pango. Docs, help and the package sources are not read at
    # run time.
    && rm -rf /opt/R/${R_VERSION}/lib/R/modules/R_X11.so /opt/R/${R_VERSION}/lib/R/modules/R_de.so \
       /opt/R/${R_VERSION}/lib/R/library/grDevices/libs/cairo.so /opt/R/${R_VERSION}/lib/R/library/tcltk \
       /opt/R/${R_VERSION}/lib/R/doc/manual /opt/R/${R_VERSION}/lib/R/library/*/doc \
       /opt/R/${R_VERSION}/lib/R/library/*/html /opt/R/${R_VERSION}/lib/R/library/*/help


# Julia (step 5): the official build of Julia for generic Linux on x86-64, checked against
# its SHA-256, under /opt/julia-<version>. The checksum is the line for
# julia-1.13.2-linux-x86_64.tar.gz in the file julialang publishes next to its downloads,
# https://julialang-s3.julialang.org/bin/checksums/julia-1.13.2.sha256 (read on 2026-10-29).
# The build brings its own libraries, and CairoMakie's JLL artifacts theirs (FreeType,
# HarfBuzz, Cairo, Fontconfig), so the base distribution does not change a render.
#
# The project is the repository's Project.toml and Manifest.toml, the catalogue pipeline's
# own (.github/actions/setup-julia), under /opt/julia-project; it is instantiated and
# precompiled into the depot /opt/julia-depot for JULIA_CPU_TARGET. The precompile is the
# slow step (245 s on 8 CPUs, 198 s on 32, measured on 2026-10-29: Makie alone takes about
# two minutes), and this stage is the only one that reruns it. The sandbox stacks a writable /tmp/depot in front of the depot
# and loads with --compiled-modules=strict, so a package image that does not match fails in
# about a second instead of compiling under the render's timeout; the final stage's smoke
# proves that every package loads that way.
#
# The precompile workload (J1.1): agents/renderer/toolchain/AnyplotWarmup is developed into
# this image's copy of the project, never the repository's, and precompiled after the
# catalogue's packages, so a change to the workload reruns only its own precompile (64 s on
# 32 CPUs, 2026-10-29) and the image's Manifest differs from the repository's by the
# package's entry and project_hash alone (its Project.toml by the package's [deps] and
# [sources] lines). `develop` resolves against the registry that
# `instantiate` installed, offline and with PRESERVE_ALL, so it fails rather than move any
# version; the registries go after it, because nothing at run time resolves a package
# (JULIA_PKG_OFFLINE). The renderer's Julia row loads the package with `-L` before the plot.
FROM base AS julia
ARG JULIA_VERSION
ARG JULIA_CPU_TARGET
ARG JULIA_SHA256=2ecdfc9890ab0a565fdd92404c915ba2a04a933dbd5d292cc224d13819d17d07
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL -o /tmp/julia.tar.gz \
       "https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_VERSION%.*}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz" \
    && echo "${JULIA_SHA256}  /tmp/julia.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/julia.tar.gz -C /opt \
    && rm /tmp/julia.tar.gz \
    && test -x "/opt/julia-${JULIA_VERSION}/bin/julia"
COPY Project.toml Manifest.toml /opt/julia-project/
ENV JULIA_DEPOT_PATH=/opt/julia-depot \
    JULIA_CPU_TARGET=${JULIA_CPU_TARGET} \
    JULIA_PKG_PRECOMPILE_AUTO=0
RUN "/opt/julia-${JULIA_VERSION}/bin/julia" --project=/opt/julia-project --startup-file=no \
    -e 'using Pkg; Pkg.instantiate()'
RUN "/opt/julia-${JULIA_VERSION}/bin/julia" --project=/opt/julia-project --startup-file=no \
    -e 'using Pkg; Pkg.precompile(strict = true, timing = true)'
COPY agents/renderer/toolchain/AnyplotWarmup /opt/julia-project/AnyplotWarmup
RUN JULIA_PKG_OFFLINE=true "/opt/julia-${JULIA_VERSION}/bin/julia" --project=/opt/julia-project --startup-file=no \
    -e 'using Pkg; Pkg.develop(path = "/opt/julia-project/AnyplotWarmup"; preserve = Pkg.PRESERVE_ALL); Pkg.precompile(strict = true, timing = true)' \
    && rm -rf /opt/julia-depot/registries /opt/julia-depot/logs \
    && du -sh "/opt/julia-${JULIA_VERSION}" /opt/julia-depot /opt/julia-depot/compiled/v*/AnyplotWarmup


# Node and the JavaScript render harness (step 3): the official Node build for Linux on x86-64,
# checked against its SHA-256, under /opt/node. The checksum is the line for
# node-v22.23.4-linux-x64.tar.xz in the file nodejs.org publishes next to its downloads,
# https://nodejs.org/dist/v22.23.4/SHASUMS256.txt (read on 2026-10-30). The major is the one the
# catalogue pipeline renders with (.github/actions/setup-node, `node-version: "22"`), which
# tests/unit/agents/renderer/test_toolchain.py pins; Node runs the harness, esbuild and Playwright's
# driver, and the page itself renders in Chromium. The headers, the docs, npm and corepack leave
# the install once the packages are in: nothing at run time installs a package.
#
# The packages are the repository's package.json and package-lock.json, installed with `npm ci`
# as setup-node installs them, into /opt/anyplot/node_modules: the whole lock, devDependencies
# included, because the harness's own esbuild and playwright are filed there. `--ignore-scripts`
# runs no package's install script (esbuild's, the lock's only one, checks its binary, which
# esbuild's API finds without it). Playwright's CLI from that install puts the Chromium headless
# shell alone under /opt/pw-browsers (`--only-shell`; a headless launch runs the shell, not the
# full Chromium), at the revision the lock's playwright-core pins, downloaded over HTTPS as the
# pipeline's `npx playwright install` downloads it.
#
# The import allowlist of MUI X snippets (agents/renderer/toolchain/import_allowlist.py) is
# derived here from the installed packages' exports maps; a package that exports a pattern
# fails the build.
#
# Liberation Sans, Serif and Mono (SIL OFL 1.1, with their copyright notice) for the JavaScript
# row alone, in a directory of their own that only its fontconfig file names
# (agents/renderer/toolchain/js-fonts.conf, FONTCONFIG_FILE in the row): the catalogue's page font
# stack asks for Helvetica and Arial, which the pipeline's runner resolves to Liberation Sans
# through fontconfig's metric aliases, and without it Chromium falls back to another, wider
# sans-serif face of the image (DejaVu or Noto). Installed system-wide, the same fonts change pygal's and altair's renders of files that
# name Arial (3 of 40 sampled Python renders, measured on 2026-10-30, the plan's "What JS-1
# built"), so they stay out of /usr/share/fonts.
FROM base AS node
ARG NODE_VERSION=22.23.4
ARG NODE_SHA256=1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl xz-utils fonts-liberation \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL -o /tmp/node.tar.xz "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
    && echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c - \
    && mkdir /opt/node \
    && tar -xJf /tmp/node.tar.xz -C /opt/node --strip-components=1 \
    && rm /tmp/node.tar.xz \
    && test "$(/opt/node/bin/node --version)" = "v${NODE_VERSION}" \
    && mkdir -p /opt/anyplot/js-fonts/doc \
    && for face in Sans-Regular Sans-Bold Sans-Italic Sans-BoldItalic Serif-Regular Serif-Bold Serif-Italic \
        Serif-BoldItalic Mono-Regular Mono-Bold Mono-Italic Mono-BoldItalic; do \
        cp "/usr/share/fonts/truetype/liberation/Liberation$face.ttf" /opt/anyplot/js-fonts/; \
    done \
    && cp /usr/share/doc/fonts-liberation/copyright /opt/anyplot/js-fonts/doc/fonts-liberation.copyright \
    && dpkg-query -W fonts-liberation > /opt/anyplot/js-fonts/doc/versions.txt
COPY package.json package-lock.json /opt/anyplot/
WORKDIR /opt/anyplot
# Neither esbuild nor a page reads the packages' type declarations or source maps (98 MB of the
# 262 MB on disk, measured on 2026-10-30), and only a video recording would run Playwright's ffmpeg.
RUN PATH="/opt/node/bin:$PATH" npm ci --ignore-scripts --no-audit --no-fund \
    && PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers /opt/node/bin/node node_modules/playwright/cli.js install --only-shell chromium \
    && rm -rf /opt/node/include /opt/node/share /opt/node/lib/node_modules /opt/node/bin/npm /opt/node/bin/npx \
       /opt/node/bin/corepack /opt/node/*.md package.json package-lock.json /opt/pw-browsers/ffmpeg-* \
    && find node_modules -type f \( -name '*.map' -o -name '*.d.ts' -o -name '*.d.mts' -o -name '*.d.cts' \) -delete \
    && test -x /opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell \
    && du -sh /opt/node /opt/anyplot/node_modules /opt/pw-browsers
# The shell links libgbm, whose Debian package depends on Mesa's drivers and LLVM (about 200 MB):
# only its backend module, which a GBM device loads, links them, and a headless page never opens
# one. So the library alone is unpacked from the package, as R's package is; libdrm2 and libexpat1,
# which it links, are in NODE_RUNTIME_LIBS.
WORKDIR /tmp/gbm
RUN apt-get update && apt-get download libgbm1 && rm -rf /var/lib/apt/lists/* \
    && dpkg-deb -x libgbm1_*.deb /tmp/gbm/root \
    && mkdir -p /opt/gbm/lib /opt/gbm/doc \
    && cp -a /tmp/gbm/root/usr/lib/x86_64-linux-gnu/libgbm.so.1* /opt/gbm/lib/ \
    && cp /tmp/gbm/root/usr/share/doc/libgbm1/copyright /opt/gbm/doc/copyright \
    && dpkg-deb -f libgbm1_*.deb Package Version > /opt/gbm/doc/version.txt
COPY agents/renderer/toolchain/import_allowlist.py /opt/anyplot/toolchain/import_allowlist.py
RUN mkdir -p /opt/anyplot/js-render \
    && python3 -I /opt/anyplot/toolchain/import_allowlist.py /opt/anyplot/node_modules > /opt/anyplot/js-render/import-allowlist.json
WORKDIR /


FROM base
ARG R_RUNTIME_LIBS
ARG R_VERSION=4.6.1
ARG JULIA_VERSION
ARG JULIA_CPU_TARGET
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends ${R_RUNTIME_LIBS} \
    && rm -rf /var/lib/apt/lists/*

COPY --from=r /opt/R /opt/R
COPY --from=r /opt/anyplot/toolchain /opt/anyplot/toolchain
COPY --from=execdeny /out/libexecdeny.so /opt/anyplot/libexecdeny.so
COPY agents/renderer/toolchain/smoke.R /opt/anyplot/toolchain/smoke.R

# Every shared object R can load resolves (a library missing from R_RUNTIME_LIBS fails
# here, not in a render), and R's binary is dynamically linked: a static binary would
# ignore LD_PRELOAD and run without the exec filter.
RUN r=/opt/R/${R_VERSION}/lib/R \
    && ldd "$r/bin/exec/R" | grep 'libc\.so' > /dev/null \
    && for f in "$r/bin/exec/R" "$r"/lib/*.so "$r"/modules/*.so "$r"/library/*/libs/*.so; do \
         LD_LIBRARY_PATH="$r/lib" ldd "$f" | sed -n "s|^\(.*not found.*\)$|$f: \1|p"; \
       done > /tmp/missing \
    && if [ -s /tmp/missing ]; then cat /tmp/missing; exit 1; fi \
    && rm /tmp/missing

# The check of the toolchain as the renderer's exec mode will run it (step 2b): R's binary
# directly, not Rscript, under the exec filter in required mode, with the environment R's
# bin/R script would set and a UTF-8 locale. smoke.R loads every package, sees its
# `system()` refused and writes a PNG with a non-ASCII title.
WORKDIR /tmp
RUN r=/opt/R/${R_VERSION}/lib/R \
    && env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8 R_HOME="$r" LD_LIBRARY_PATH="$r/lib" \
       R_SHARE_DIR="$r/share" R_INCLUDE_DIR="$r/include" R_DOC_DIR="$r/doc" \
       LD_PRELOAD=/opt/anyplot/libexecdeny.so ANYPLOT_DENY_EXEC=required \
       "$r/bin/exec/R" --no-echo --no-restore --no-save --file=/opt/anyplot/toolchain/smoke.R \
    && rm -rf /tmp/*
WORKDIR /

# Julia after R, so a Julia change reruns only these lines of this stage and an R change
# only copies the cached Julia stage again.
COPY --from=julia /opt/julia-${JULIA_VERSION} /opt/julia-${JULIA_VERSION}
COPY --from=julia /opt/julia-project /opt/julia-project
COPY --from=julia /opt/julia-depot /opt/julia-depot
COPY agents/renderer/toolchain/smoke.jl agents/renderer/toolchain/warmup.jl /opt/anyplot/toolchain/

# Julia's launcher is dynamically linked (a static one would ignore LD_PRELOAD and run
# without the exec filter), and it and the runtime libraries it loads resolve every
# shared object. The rest of lib/julia is the system image, whose libraries the running
# process provides, Julia's own test libraries, and the libraries Julia opens by path.
RUN j="/opt/julia-${JULIA_VERSION}" \
    && ldd "$j/bin/julia" | grep 'libc\.so' > /dev/null \
    && for f in "$j/bin/julia" "$j"/lib/libjulia.so* "$j"/lib/julia/libjulia-*.so*; do \
         ldd "$f" | sed -n "s|^\(.*not found.*\)$|$f: \1|p"; \
       done > /tmp/missing \
    && if [ -s /tmp/missing ]; then cat /tmp/missing; exit 1; fi \
    && rm /tmp/missing

# The check of the toolchain as the renderer's Julia row will run it (agents/renderer/commands.py):
# the julia binary directly with the row's flags and environment, under the exec filter in
# required mode. --compiled-modules=strict makes a package image the depot holds but this run
# cannot load (other cache flags, another CPU target, a stale source) an error within a second,
# so a depot that would compile at run time fails the build here. Like a render, it loads the
# precompile workload with `-L warmup.jl` first; smoke.jl checks that it did, loads every
# package of the image's Project.toml, sees a program start refused, reads a fixed offset
# through TimeZones and writes a PNG with a non-ASCII title. On a failure the loading log
# names the rejected image.
# Cairo's fontconfig (Fontconfig_jll) caches the font directories it scanned in
# /var/cache/fontconfig, writable only here: those caches go, since the renderer image adds
# fonts after this stage and a sandbox's root filesystem is read-only.
WORKDIR /tmp
RUN j="/opt/julia-${JULIA_VERSION}" \
    && run() { \
         env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8 XDG_CACHE_HOME=/tmp "$@" \
           JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 JULIA_DEPOT_PATH=/tmp/depot:/opt/julia-depot \
           "JULIA_CPU_TARGET=${JULIA_CPU_TARGET}" JULIA_PKG_OFFLINE=true JULIA_PKG_PRECOMPILE_AUTO=0 \
           LD_PRELOAD=/opt/anyplot/libexecdeny.so ANYPLOT_DENY_EXEC=required \
           "$j/bin/julia" --project=/opt/julia-project --startup-file=no --history-file=no \
           --compiled-modules=strict --heap-size-hint=1536M -L /opt/anyplot/toolchain/warmup.jl \
           /opt/anyplot/toolchain/smoke.jl; \
       } \
    && if ! run; then \
         run JULIA_DEBUG=loading 2>&1 | grep -iE 'reject|not available|stale|error' | head -n 60; \
         exit 1; \
       fi \
    && rm -rf /tmp/* /var/cache/fontconfig/*.cache-*
WORKDIR /

# Node after Julia, so a Node change reruns only these lines of this stage: its libraries, the
# install, the harness's packages, the headless shell, the row's fonts and the harness itself
# (automation/js-render, the pipeline's own) with the import allowlist next to it.
ARG NODE_RUNTIME_LIBS
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends ${NODE_RUNTIME_LIBS} \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node /opt/gbm/lib/ /usr/lib/x86_64-linux-gnu/
COPY --from=node /opt/gbm/doc/ /usr/share/doc/libgbm1/
COPY --from=node /opt/node /opt/node
COPY --from=node /opt/pw-browsers /opt/pw-browsers
COPY --from=node /opt/anyplot/node_modules /opt/anyplot/node_modules
COPY --from=node /opt/anyplot/js-fonts /opt/anyplot/js-fonts
COPY automation/js-render/ /opt/anyplot/js-render/
COPY --from=node /opt/anyplot/js-render/import-allowlist.json /opt/anyplot/js-render/import-allowlist.json
COPY agents/renderer/toolchain/js-fonts.conf /opt/anyplot/js-fonts.conf
COPY agents/renderer/toolchain/smoke.js agents/renderer/toolchain/smoke.tsx /opt/anyplot/toolchain/

# Node and the headless shell resolve every shared object they and the shell's own libraries
# link (a library missing from NODE_RUNTIME_LIBS fails here, not in a render).
RUN ldconfig \
    && shell=$(echo /opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64) \
    && for f in /opt/node/bin/node "$shell/chrome-headless-shell" "$shell"/*.so*; do \
         ldd "$f" | sed -n "s|^\(.*not found.*\)$|$f: \1|p"; \
       done > /tmp/missing \
    && if [ -s /tmp/missing ]; then cat /tmp/missing; exit 1; fi \
    && rm /tmp/missing

# The check of the toolchain as the renderer's JavaScript row will run it
# (agents/renderer/commands.py): Node by its path with the row's environment, the harness on a
# Chart.js chart and on a MUI X component (esbuild bundles it from the image's packages), each a
# 3200x1800 PNG. The fontconfig caches the shell writes under XDG_CACHE_HOME go with /tmp.
WORKDIR /tmp
RUN smoke() { \
      env -i PATH=/usr/bin:/bin HOME=/tmp ANYPLOT_THEME=light \
        PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers ANYPLOT_NODE_MODULES=/opt/anyplot/node_modules \
        FONTCONFIG_FILE=/opt/anyplot/js-fonts.conf TZ=UTC LANG=C.UTF-8 XDG_CACHE_HOME=/tmp XDG_CONFIG_HOME=/tmp \
        /opt/node/bin/node /opt/anyplot/js-render/render.mjs "--library=$1" "/opt/anyplot/toolchain/$2" \
      && python3 -I -c "import struct, sys; png = open('plot-light.png', 'rb').read(); \
           assert png[1:4] == b'PNG' and struct.unpack('>II', png[16:24]) == (3200, 1800), sys.argv[1]; \
           print(sys.argv[1], 'plot-light.png 3200x1800,', len(png), 'bytes')" "$1" \
      && rm plot-light.png plot-light.html; \
    } \
    && smoke chartjs smoke.js \
    && smoke muix smoke.tsx \
    && rm -rf /tmp/* /var/cache/fontconfig/*.cache-*
WORKDIR /
# The base image's shell, so the renderer's RUN lines keep theirs.
SHELL ["/bin/sh", "-c"]
