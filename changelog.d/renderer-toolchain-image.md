### Added

- **The renderer builds on a toolchain image with R 4.6.1 and an exec filter for
  exec-mode runtimes.** `anyplot-toolchain` (`agents/renderer/toolchain.Dockerfile`)
  is `python:3.14-slim`, pinned by digest, with Posit's R 4.6.1 for Debian 13, the
  pipeline's ggplot2 package set plus readr as Package Manager binaries, and a
  preload library whose constructor kills every later program start before user
  code runs. The deploy builds and pushes it to Artifact Registry only when the hash
  of its inputs is new, and the CI job pulls it or builds it. The Python renders of
  all six libraries stay byte-identical; R is not served yet (step 2 of the
  all-libraries plan, revised after a second opinion). (#12423)
