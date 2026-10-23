### Fixed

- **JavaScript implementations get exactly one header.** impl-review's header
  writer stopped at a `//# anyplot-orientation:` directive on line 1 and
  prepended the new header above it, so the generator's header stayed below
  the directive with its old score, date and library line, and the site's code
  view showed both. The writer now lives in `automation/scripts/impl_header.py`:
  the header goes on line 1, a directive that sat above it moves directly below
  it, and a stale second header block among the leading lines is dropped. The
  five JavaScript library prompts now place the directive directly below the
  header. The stale block was removed from the 182 catalogue files that carried
  it (139 muix, 19 Highcharts, 14 ECharts, 9 D3, 1 Chart.js). (#12299)
