### Added

- **The renderer runs R plots in exec mode under the exec filter.** The R row of
  the command table starts R's own binary with `--file=plot.R` and the environment
  R's start script would set (UTF-8 locale included), and the harness preloads the
  exec filter into it: every program the plot starts is killed, and a run whose
  filter did not report `on` is refused with exit code 3 (`RENDERER_EXEC_DENY=optional`
  stays the switch). Each row now says whether it needs the filter; only the
  JavaScript row, whose Node and Chromium start their own processes, has it off. The
  agents service does not send R jobs yet.
