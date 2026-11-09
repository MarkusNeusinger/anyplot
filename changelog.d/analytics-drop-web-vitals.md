### Removed

- **Core Web Vitals no longer go to Plausible.** The site stops sending `LCP`, `CLS`, `INP`, `FCP` and
  `TTFB` as custom events, and the `web-vitals` dependency goes with them. They were 44 % of the billable
  events (17,044 of 38,818 in 28 days), `FCP` and `TTFB` had no dashboard goal, and every one of them
  un-bounced its visit: visits with a vitals event bounced at 0 %, visits without at 88 %, so the
  dashboard's bounce rate of about 5 % was an artifact and rises to a realistic value from here. Core Web
  Vitals come from PageSpeed Insights when needed, and the privacy text on `/legal` no longer lists them.
  (#12860)
- **The automatic `Form: Submission` goal is off.** `formSubmissions: false` in the Plausible init: the
  agent chat's message box is a form, so the goal counted chat messages that the chat's own events
  already count, 144 of its 146 events the admin's own. (#12860)

### Fixed

- **A crawler farm no longer counts as visitors.** Since 2026-11-03 a farm has loaded about 17 spec pages
  an hour from a new exit IP on almost every request, with plain Windows 10 Chrome 103 to 138 user
  agents, so the nginx analytics shield caught 6 of 16,195 of its event posts in 44 hours, and its
  residential share made up 675 of 1,451 dashboard visitors in 7 days. One more `$is_headless_client`
  entry matches exactly that shape (Windows 10, Chrome 100 to 139, an anchored `Safari/537.3x` tail),
  which keeps Edge, Opera, Windows 7/8.1 and Chrome 140+ out and costs about 2 % of real visits, those on
  a pinned old Chrome. A unit test holds the map against the farm's user agents and current browsers, and
  `docs/reference/plausible.md` carries the review rule for the version ceiling. (#12860)
