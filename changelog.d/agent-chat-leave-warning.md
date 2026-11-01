### Fixed

- **The agent chat asks before leaving drops the session.** A reload, a
  closed tab or a link off `/debug/agent` used to end the session unasked,
  with its data and plots, also after a 20-minute `.plot_all()` across 15
  libraries. While the session holds data, a table read from text, a plot or
  work in flight, the page now asks first: the browser's own `beforeunload`
  dialog for a reload or a closed tab, and a `confirm` from the router's
  blocker for a link inside the site or the back button. An empty session,
  the page's own query edits (a library pill, `all`) and the reload links
  after an expired session or no answer ask nothing. Sessions still live in
  memory only. (#12502)
