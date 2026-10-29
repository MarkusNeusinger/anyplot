### Added

- **The renderer's Julia row loads a precompile workload before every plot.** The
  toolchain image develops a small package, `AnyplotWarmup`, into its own copy of
  the Julia project and precompiles a `PrecompileTools` workload of the calls the
  catalogue's Makie files make most and of the agent's data loader (a typed
  `CSV.read`, datetimes through TimeZones, plots from DataFrame columns); the row
  loads it with `-L /opt/anyplot/toolchain/warmup.jl`, so `plot.jl` stays the
  program and its error frames and exit codes do not change. CSV, DataFrames and
  TimeZones invalidate much of Makie's precompiled code, so an adapted Makie render
  took 16 to 18 s locally at 2 CPUs; with the workload it takes 5 s, and catalogue
  files gain 6 to 63 %. The repository's `Project.toml` and `Manifest.toml` do not
  change; the images grow by about 100 MB. (#12460)
