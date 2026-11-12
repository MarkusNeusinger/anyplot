### Changed

- **A crawler Cloudflare verified gets the prerendered page without a token in
  nginx's list.** Until now only a user agent the `$is_bot` map names was
  served the page; every other crawler got the app's empty shell. In the
  seven days to 2026-11-12 that was 13,525 page fetches by verified bots:
  ExaSearchBot (7,971) runs no JavaScript and read nothing, Parallel's ShapBot
  (3,954) rendered the app itself at about 1.7 API reads per page. nginx's
  new `$prerender` is "a token, or a verified bot of a category that reads
  content": Search Engine Crawler, AI Search, AI Crawler, Page Preview,
  Archiver, Aggregator, Feed Fetcher and Academic Research. Cloudflare keeps
  the members of each, so a new crawler is served the day it is verified.
  Every other category keeps the app, because "verified" is not "never a
  person": Cloudflare's signed agents are remote browsers a person directs,
  its Search Engine Optimization category holds Google Lighthouse, GTmetrix
  and Pingdom, and monitors, security and accessibility scanners exist to
  test what people get. The crawlers of the SEO tools (Semrush, Ahrefs,
  DataForSEO, Majestic, Moz, Haloscan) join the token list instead. The
  analytics shield on `/api/event` keeps reading the user agent alone. The
  daily bot serving check and the deploy smoke probe both sides of the
  verdict at the origin.
