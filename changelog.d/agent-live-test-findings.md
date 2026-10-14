### Changed

- **Pasted data takes up to 1 MB, computed data up to 2 MB.** The paste cap
  rose from 200 KB to 1 MB in the parser, the agents route, the BFF and the
  data card's counter; rows (20,000) and columns (50) keep their caps. Data the
  assistant computes keeps full float precision under its own 2 MB cap, so a
  10,000-step run with six columns (about 1.1 MB) fits as it is. A parse whose
  canonical CSV passes 4 MiB, the render job's limit, is refused. (#12176)

### Fixed

- **A data snippet over the size cap says how much and what to do.** Cloud Run's
  sandbox launcher reports every non-zero exit as its own SIGPIPE (-13), so a
  10,000-step ODE that broke the 200 KB CSV cap came back as an unnamed error
  twice. The harness now writes its exit code and the measured size and cap to
  `status.json`, the renderer and the local backend read it, and the
  `run_data_code` refusal names the size, the cap and the row step that fits; the
  tool description and the root prompt name the cap and the rounding up front. (#12176)
- **The data summary follows a language set by a pasted CSV.** After a German
  CSV without notes the summary came in English in 3 of 4 probe runs. The
  session block and the action message now name a known session language in
  English words (11 of 11 runs in German afterwards). (#12176)
- **Default bindings never group by a single-valued column.** A categorical,
  text or boolean role such as `series` ranks a column with one distinct value
  after every column with two or more, so a constant `Kanton` no longer takes
  the series from `Staatsangehörigkeit`. (#12176)
