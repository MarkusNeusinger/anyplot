### Changed

- **The legal page is shorter and states only the current state.** Its visible text drops from 1,805 to 1,059
  words (the privacy policy from 1,546 to 762): what is processed, where it runs, how long each store keeps it, the
  three legal bases and the data assistant's terms now sit in short fact tables with row headers, each fact said
  once. The notes on log entries written before the move to europe-west4 and on older unsalted feedback hashes are
  gone; both conditions ended on 2026-11-02. The crawler version (`/seo-proxy/legal`, 393 words, 370 before) drops
  the same history and now carries every fact the page states: the stored feedback fields, all three legal bases,
  your rights, the telemetry retention, the no-training line and the running costs (#12538).
- **The transparency section lists the whole stack and what running the site costs.** Eight grouped rows (site,
  api, catalogue pipeline, data assistant, Google Cloud, edge and analytics, reviews, editor and typography) replace
  the old list, which named neither the data assistant nor most of the Google Cloud services. The cost table shows
  October 2026 as paid after commitments and credits, about $60 a month with the assistant's model, in place of a
  $34 estimate of hosting alone (#12538).

### Fixed

- **A link to a section of the legal page lands on its heading.** The route loads lazily, so a fresh load of
  `/legal#assistant`, which the chat's notice opens in a new tab, stayed at the top of the page; it now scrolls to
  the section once the page renders, below the sticky masthead. The code and docs that still promised a migration
  for the old unsalted feedback IP hashes now say they were cleared once by hand on 2026-11-02 after a snapshot
  (#12538).
