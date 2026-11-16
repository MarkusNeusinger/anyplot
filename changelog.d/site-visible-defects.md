### Fixed

- **The palette strip on the landing page fits a phone.** At 320 to 390 px,
  all eight swatches now show and each name sits centred under its own
  swatch. Before, the hidden hex label gave every swatch a minimum width of
  about 70 px, so the last three swatches were clipped and the names drifted
  under the wrong colours.
- **The swatch labels on the palette page use the ink with the higher
  contrast.** The helper now compares the WCAG contrast ratio of both inks
  against each swatch instead of cutting at a luminance of 0.5. Every
  categorical hue now reaches at least 4.5:1, where five of them had 1.99 to
  2.97:1. Brand green, cyan, lime, lavender and ochre, and the dark-theme
  muted anchor, now take the dark ink. The hex line no longer fades to
  0.85 opacity, which put it under 4.5:1 again.
- **The library cards on the libraries page line up.** The cards in a row
  are now the same height, so their version and docs lines sit at the same
  height. Before, they were up to 42 px apart on desktop.
- **The Highcharts card notes its licence.** The card reads
  `free · non-commercial`, beside the note MUI X already had, on the
  libraries page and the landing page.
- **The landing page no longer jumps when the plot of the day arrives.** The
  terminal frame is reserved, empty, while the plot loads. On a tablet the
  layout shift drops from 0.18 to under 0.001.
- **A failed load on the plots page clears and can be retried.** The error
  banner is cleared when the next fetch starts. It says `plots did not load`
  instead of the raw exception with status and URL, and offers `.retry()`.
  While it shows, the page no longer also claims that no plots match.
