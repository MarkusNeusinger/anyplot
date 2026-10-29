### Added

- **The Julia (Makie) code profile for "Use with my data", not served yet.**
  `agents/anyplot/code/profiles/julia/` reads Makie code with the pinned
  tree-sitter grammar for Julia (the agents image now keeps the R and Julia
  grammars): the protected regions, a normaliser that strips the header,
  blanks the catalogue title, saves into the working directory, renames
  the deprecated `resolution` keyword to `size` and sets only the save's
  `px_per_unit` for CairoMakie's rounding, the SECURITY and ADAPTATION
  validator that refuses by shape (process starts, file I/O, `ENV`,
  evaluation, reflection, native code, computed callees, string
  interpolation walked as code, a `using` allowlist) with the named
  bypasses as tests, the readiness scan (0 clean, 308 coupled, 17
  blocked), a `CSV.read` loader typed from the data's kinds that reads
  every integer exactly and turns timestamps into UTC through TimeZones.jl
  (the kinds count the cells below the millisecond that Julia truncates),
  and an error grammar that never quotes Julia's message. The edit applier
  gains a Julia dialect and the export the run line `julia --project=.
  plot.jl`, with Python's and R's output unchanged; the runtime, the
  prompts and the fixtures follow in the next step.
