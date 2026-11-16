### Fixed

- **The palette strip on the landing page fits a phone.** At 320 to 390 px,
  all eight swatches now show and each name sits centred under its own
  swatch. Before, the hidden hex label gave every swatch a minimum width of
  about 70 px, so the last three or four swatches were clipped and the names
  drifted under the wrong colours. Each name now moves with its colour when
  one expands; while a colour is expanded, only its name shows. Keyboard
  focus now expands a colour and shows its hex as a hover does, and the
  strip no longer animates when reduced motion is turned on.
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
  `free for non-commercial use` on the libraries page and the landing page.
  A licence note now has its own line above `.explore()`, and MUI X's
  `MIT · community` moved there from beside it. The Highcharts note stays
  on one line at every width from 320 px, and `.explore()` stays level with
  the cards beside it. This adds a 19 px line to both cards.
- **The landing page no longer jumps when the plot of the day arrives.** The
  terminal frame is reserved, empty, while the plot loads, and keeps its
  height when the plot arrives and when `.use_my_data()` joins its header
  after the plot. The header and the footer have a number of rows
  that depends only on the card's width: below 560 px, on a phone and in the
  narrow two-column card from 900 px, the header's actions and the footer's
  library each take a second row in every state. A filename or title too
  long for its row is cut with an ellipsis instead of wrapping. With the
  plot-of-the-day answer delayed by 1.5 s, the layout shift on a tablet
  (820 px) drops from 0.18 to under 0.001. On a phone (390 px) with the card
  in view, the late `.use_my_data()` shifted the page by 0.18 and now by
  under 0.001. If the request fails, the frame stays and says
  `plot of the day did not load`, with `.retry()`. The request, with its
  retries, stops when the visitor leaves the page or asks again.
- **A failed load on the plots page clears and can be retried.** The error
  banner is cleared when the next fetch starts. It says `plots did not load`
  instead of the raw exception with status and URL, and offers `.retry()`.
  While it shows, the page shows no plots of an earlier filter and no longer
  claims that no plots match, and the search menu offers no counts of an
  earlier filter. The banner sits 16 px below the masthead's rule instead of
  on it.
