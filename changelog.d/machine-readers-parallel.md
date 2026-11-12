### Added

- **Parallel's crawlers have a name in the machine-read numbers.** ShapBot,
  which indexes pages for Parallel's web APIs, and Shap-User, which fetches a
  page for a person's agent, are in the vendor table as `parallel`. ShapBot
  made 8,878 reads on 2026-11-10 that Cloudflare verified as `AI Search` and
  that counted under `other`, because the table didn't know it. It runs a
  browser, so it reads a page through the app and needs no prerendered copy.
