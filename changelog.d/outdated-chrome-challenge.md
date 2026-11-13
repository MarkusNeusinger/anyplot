### Changed

- **The crawler farm is challenged at the edge by its Chrome version.** The
  Cloudflare challenge for four hosting networks left the farm's residential
  share alone, and that share grew from about 25 to 30 dashboard visitors a
  day to 488 of the 598 counted on 2026-11-13. A second Managed Challenge now
  answers a desktop user agent with Chrome 151 or older on the site hosts,
  with verified bots, phones, self-declared headless clients, and browsers
  that name themselves (Edge, Opera, Vivaldi, Yandex) left out. A person on
  an old Chrome sees the challenge and passes it; of the 880 challenges the
  hosting-network rule issued in a day, 15 were solved. The cut-off is the
  owner's "most used version minus five": of 208 desktop Chrome visitors who
  came from a search engine in a week, nine were on 151 or older. The rule
  lives in Cloudflare; `infra/cloudflare/README.md` is its written record,
  and `docs/reference/plausible.md` says how to read the dashboard around a
  farm. (#13087)
