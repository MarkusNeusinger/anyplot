### Added

- **Makie in "Use with my data", for the admin's live tests.** `JuliaRuntime`
  (`agents/anyplot/render/runtimes/julia.py`) serves Makie on the Julia code
  profile: `plot.jl` renders through the renderer's Julia row in exec mode
  under the preloaded exec filter, with the precompiled depot and the
  precompile workload, and the export downloads as `plot.jl` with `julia
  --project=. plot.jl` in its header. The admin deploy names Makie next to the
  six Python libraries and ggplot2, and its 80 % eval matrix gates the public
  release. ADAPTATION refuses a working form that keeps a dataset package
  (RDatasets, PalmerPenguins). When the loader cuts a timestamp's digits below
  the millisecond, which Julia's `DateTime` cannot hold, the first entry of
  the version's "what changed" list names the columns and counts the cells,
  and the plot's status stays its own. A scripted identity adaptation of the
  smoke fixture renders 3200x1800 in both themes through the local Docker
  backend in about 5.7 s with `exec_deny: on`. (#12464)
- **A Julia adapter prompt.** `adapter_julia.md` fills the shared adapter
  prompt's slots for Julia: the placeholder `df = load_user_data()` and how the
  loader types each column, column constants read as `df[!, COL]`, the
  protected statements, the packages the adapter may load, a number formatter
  that writes the plot language's decimal and thousands marks, and what Makie
  0.24 refuses that the catalogue never meets (a date column with a missing
  cell, spans and bands on a time axis, text as `barplot!`'s x). A test runs
  its idioms through both Julia validator profiles, and an image test renders
  them. Python's prompt is unchanged, and its SHA-256 pin holds. (#12464)
- **Makie eval fixtures.** The ten matrix specs for Makie (60 cases, 480
  generated in all) with the smoke case `scatter-basic-makie-renamed`; the
  eligibility sweep covers Makie (325 files: 0 clean, 308 coupled, 17
  blocked). (#12464)

### Fixed

- **A failed Julia render lost the line that names its error.** Makie's stack
  traces run to 7,500 characters and more, so the 2,000-character stderr tail
  lost Julia's first `ERROR:` line and the repair read "an error (the tail cut
  off its first line)". The Julia row now keeps that line in front of the
  tail within the same 2,000 characters (`RuntimeCommand.stderr_head`), and
  every other row's tail is unchanged. The Julia error summary also names the
  line of the code the adapter edits, not the line of the code that ran, which
  the loader shifts by 15 lines and more. (#12464)
