### Added

- **Julia in the renderer's toolchain image, not served yet.** The toolchain
  image (`agents/renderer/toolchain.Dockerfile`) gains a Julia stage of its
  own: the official Julia 1.13.2 build, checked against julialang's SHA-256,
  and the catalogue's `Project.toml` and `Manifest.toml` precompiled into a
  depot, so the renderer runs the pipeline's Makie 0.24.16. The renderer's
  Julia row starts the launcher by its path under the preloaded exec filter
  with `--compiled-modules=strict`: a package image that does not load fails
  a render in about a second instead of compiling for minutes under its
  timeout, which the image build, CI and the deploy's candidate smoke each
  check with a Makie render. The agent chat does not offer Makie yet.
  TimeZones.jl becomes a direct dependency of the Julia project, for the
  loader that turns datetimes with offsets into UTC.

### Changed

- **The renderer deploy runs on 8 vCPUs with a registry layer cache.**
  `agents/renderer/cloudbuild.yaml` runs on `E2_HIGHCPU_8` with an hour's
  timeout and builds a missing toolchain with BuildKit's registry cache, so a
  change to one toolchain no longer rebuilds the others; `Project.toml` and
  `Manifest.toml` join the toolchain's hash, the build context and the CI
  image job's change filter.
