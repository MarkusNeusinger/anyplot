### Added

- **Chart.js, D3, ECharts and Highcharts in "Use with my data", for the
  admin's live tests.** `JavaScriptRuntime`
  (`agents/anyplot/render/runtimes/javascript.py`) serves the four libraries on
  the JavaScript code profile: `plot.js` renders through the renderer's
  JavaScript row, the catalogue's browser harness in its sandbox mode, and the
  page reads the user's table as typed JSON that Python writes from the
  canonical CSV (`RenderJob.data_json`), so the theme toggle renders the other
  theme from the same table. The admin deploy names the four libraries next to
  the eight served before, and each library's 80 % eval matrix gates the public
  release. Highcharts is served under its non-commercial licence (owner
  decision). When the typing changes a value, the first entries of the
  version's "what changed" list count the integers past 2^53, the timestamps
  cut to the millisecond and the timestamps converted to UTC, per column, and
  the plot's status stays its own. The PNG and `plot.js` download now; the
  interactive `plot.html` the code file's header names comes in the next step.
- **A JavaScript adapter prompt.** `adapter_javascript.md` fills the shared
  adapter prompt's slots for JavaScript: the placeholder
  `const data = loadUserData();` and how the table is typed, column constants
  read as `d[COL]`, the protected token lines and orientation directive, `null`
  dropped before any conversion or statistic, a number formatter for every
  library's value axis that writes the plot language's marks, time axes kept in
  UTC so an exported page shows the same dates in every time zone, and Chart.js
  dates on a category or linear axis, since the page has no date adapter. A
  test runs its idioms through both validator profiles for each library, and an
  image test renders them from a table with missing cells.
- **JavaScript eval fixtures.** The ten matrix specs for Chart.js, D3, ECharts
  and Highcharts (240 cases, 720 generated in all) with one smoke case each;
  the eligibility sweep covers the four libraries (none `clean`; 306 of 321
  Chart.js, 311 of 325 D3, 311 of 325 ECharts and 310 of 323 Highcharts files
  eligible).

### Changed

- **The renderer deploy's Chart.js smoke is a gate.** A failed Chart.js render
  of the candidate revision now refuses the promotion, as the Makie render
  does, and the smoke's page reads its table from the job's typed JSON, the
  path every agent job takes.
- **The scope judge's example of another library is MATLAB.** It was "this
  plot in JavaScript with Chart.js", which the chat now adapts.
- **The assistant names the time-zone notes of every language.** A "what
  changed" line that says R, Julia or JavaScript converted timestamps with an
  offset to UTC is now named in the reply, like the other loader notes.
- **A loader note never passes the 200-character limit.** With very long
  column names and many changed cells, the first column's name in a note is
  now cut with an ellipsis instead of failing the result.

### Fixed

- **The agent network's concept doc described Makie as not served.** The merge
  of the JavaScript toolchain step dropped the doc lines that served Makie;
  they are back, with the JavaScript runtime's.
