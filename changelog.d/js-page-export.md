### Added

- **A Chart.js, D3, ECharts or Highcharts plot downloads as an interactive
  `plot.html`.** The result card's `.download('plot.html')` saves the
  self-contained page in the theme on screen: the chart library, the theme,
  the user's table and the plot code, which opens in any browser without a
  server. The agents service builds it on demand, never stored, through the
  renderer's new `POST /page`, where the browser harness writes the page a
  render would screenshot and starts no browser (`ANYPLOT_PAGE_ONLY=1`). The
  download is a wrapper with no script of its own: the harness's content
  security policy plus `frame-src 'none'`, and the page in an
  `<iframe sandbox="allow-scripts" srcdoc=...>`, so the plot code runs in an
  opaque origin that cannot navigate the window, open popups, fetch, or read
  cookies and storage. Both download routes answer it as an attachment with
  `Content-Security-Policy: sandbox`. A renderer deployed before the route
  answers `503 page_unavailable`. While the page builds, the chat holds its
  composer, theme switches and data edits back, as for a theme render. The
  download is its own usage outcome, `downloaded_page`; the telemetry views
  that list the outcomes still need re-creating. A JavaScript version now
  lists five artifacts at most (two PNGs, the code, the page and the data),
  and the assistant names the button and the page's place in running
  `plot.js`.
- **A probe of the page's boundary in the renderer image's CI.** It builds a
  Chart.js page with the image, wraps it with the agents' wrapper and opens it
  from `file://` in the image's Chromium: the chart drew and answers a hover,
  the frame's origin is `null`, and the plot code's attempts to set
  `top.location`, call `window.open` and `fetch`, read storage and cookies,
  and navigate its own frame to an http URL all fail.

### Changed

- **The local Docker backend runs the checkout's browser harness.** A
  JavaScript render or page build mounts `automation/js-render/render.mjs`
  over the image's, as the backend mounts the checkout's `harness.py`, so a
  local run uses the harness under development.
- **The agent chat's local mock serves JavaScript versions.** With a
  JavaScript library in `AGENT_LIBRARIES`, `app/scripts/agent-bff-mock.mjs`
  answers `plot.js` and a wrapped `plot.html` per theme, so the download can be
  driven in a browser without the services; it also accepts the cards' usage
  beacon. Its other answers are unchanged.
