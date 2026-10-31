### Added

- **A Chart.js, D3, ECharts or Highcharts plot plays in the result card.**
  `.interactive()` on the image shows the plot's `plot.html` in the card, in
  the theme on screen, with its tooltips and hover; `.preview()` brings the
  image back, and a theme switch shows that theme's page. Nothing loads before
  the click: the chat then fetches the very page the download serves, through
  the same authenticated route, and holds the session while the server builds
  it. The page reaches the card through a relay on the API, so no token or
  cookie ever meets the plot code, and the site's content security policy is
  unchanged. The frame takes the plot's orientation from the page itself, and
  collapsing the card drops the preview's pages. Opening the preview is its
  own usage outcome, `opened_preview`, a look that counts as no keep. (#12482)
- **The relay page of the chat's interactive preview, `GET /preview/relay`.**
  A static, unauthenticated page of 1 KB on the API, outside `/debug/*`,
  served with `Content-Security-Policy: sandbox allow-scripts`, the browser
  harness's policy and `frame-ancestors` for the site's origins and local dev
  servers, so it runs in an opaque origin without network that no other site
  can frame. Its only message is a constant ready signal without content to
  its parent; the chat posts the page only on that signal from the relay's own
  frame, so a page that stands in at the relay's URL, such as an error page of
  the edge, never receives it, and the card says `relay_unavailable` when no
  signal comes. The relay takes one page, the first that its parent posts from
  an allowed origin, writes it into an `<iframe sandbox="allow-scripts">`
  through the `srcdoc` property and ignores everything else. The BFF mock
  serves the same relay. (#12482)
- **A probe of the relay in the renderer image's CI.** The page probe's new
  relay mode serves the relay with its real headers on an origin of its own,
  frames it scaled from an allowed origin that waits for the signal, and posts
  the CI page's wrapper: the chart draws and answers a hover in a frame of
  origin `null`, the plot code cannot navigate the wrapper or the relay, post
  a page into it or fake the signal, a second page and pages from sibling
  frames and from another origin are ignored, another origin cannot frame the
  relay, and a listening 404 page at the relay's URL receives nothing. The
  image test runs it for all four libraries. (#12482)

### Changed

- **The eval pacing text follows the raised Haiku quota.** The owner raised
  the project's Claude Haiku `eu` overrides on 2026-10-31 to 150 requests,
  1,000,000 input tokens and 200,000 output tokens a minute (from 30
  requests); the agents README, the design doc and the scope and prep evals'
  docstrings say so, and why `--calls-per-minute` keeps its default of 25.
  (#12482)
