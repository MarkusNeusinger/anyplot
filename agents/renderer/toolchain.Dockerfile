# anyplot-toolchain: the language toolchains the renderer runs in exec mode, on the
# renderer's own base (agentic/specs/261024-agent-all-libraries.md, step 2a). The
# renderer's Dockerfile builds FROM this image (TOOLCHAIN_IMAGE and TOOLCHAIN_TAG), its
# builder stage included, so the venv and the runtime see the same Python.
#
# It is built only when its inputs change. `agents/renderer/toolchain.py tag` hashes
# this file, agents/renderer/toolchain/ and agents/renderer/execdeny/; the deploy
# (agents/renderer/cloudbuild.yaml) builds and pushes `anyplot-toolchain:<hash>` to the
# private Artifact Registry repository only when that tag is missing, and the CI job
# (ci-image.yml, renderer-image) pulls the tag or builds it. Locally:
#
#   docker build -f agents/renderer/toolchain.Dockerfile -t anyplot-toolchain:dev .
#
# One stage per toolchain, each into its own prefix, so a later toolchain (Julia, Node
# with Chromium) adds a stage and a COPY. The build CONTEXT is the repo root and the
# root `.dockerignore` admits agents/.
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


FROM base
ARG R_RUNTIME_LIBS
ARG R_VERSION=4.6.1
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
# The base image's shell, so the renderer's RUN lines keep theirs.
SHELL ["/bin/sh", "-c"]
