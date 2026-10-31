### Added

- **A Chart.js, D3, ECharts or Highcharts plot plays in the result card.**
  `.interactive()` on the image shows the plot's `plot.html` in the card, in
  the theme on screen, with its tooltips and hover; `.preview()` brings the
  image back, and a theme switch shows that theme's page. Nothing loads before
  the click: the chat then fetches the very page the download serves, through
  the same authenticated route, and holds the session while the server builds
  it. The page reaches the card through a relay on the API, so no token or
  cookie ever meets the plot code, and the site's content security policy is
  unchanged. Opening the preview is its own usage outcome, `opened_preview`,
  a look that counts as no keep.
- **The relay page of the chat's interactive preview, `GET /preview/relay`.**
  A static, unauthenticated page of 1 KB on the API, outside `/debug/*`,
  served with `Content-Security-Policy: sandbox allow-scripts`, the browser
  harness's policy and `frame-ancestors` for the site's origins and local dev
  servers, so it runs in an opaque origin without network that no other site
  can frame. Its script takes one page, the first that its parent posts from
  an allowed origin, writes it into an `<iframe sandbox="allow-scripts">`
  through the `srcdoc` property, ignores everything else and sends nothing
  back. The BFF mock serves the same relay.
- **A probe of the relay in the renderer image's CI.** The page probe's new
  relay mode serves the relay with its real headers on an origin of its own,
  frames it scaled from an allowed origin and posts the CI page's wrapper: the
  chart draws and answers a hover in a frame of origin `null`, the plot code
  cannot navigate the wrapper or the relay or post a page into it, pages from
  sibling frames and from another origin are ignored, and another origin
  cannot frame the relay. The image test runs it for all four libraries.

### Changed

- **The eval pacing text follows the raised Haiku quota.** The owner raised
  the project's Claude Haiku `eu` overrides on 2026-10-31 to 150 requests,
  1,000,000 input tokens and 200,000 output tokens a minute (from 30
  requests); the agents README, the design doc and the scope and prep evals'
  docstrings say so, and why `--calls-per-minute` keeps its default of 25.
