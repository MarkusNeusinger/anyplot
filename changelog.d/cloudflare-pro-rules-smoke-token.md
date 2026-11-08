### Added

- **The zone's security rules are written down.** The Cloudflare Pro rules
  applied on 2026-11-09 live only in the dashboard, so `infra/cloudflare/README.md`
  now records each one with its phase, expression, action, and purpose: the
  Cloudflare Managed Ruleset and the OWASP Core Ruleset at paranoia level 1, both
  answering with a Managed Challenge and the first sparing the free-text routes;
  the transform rule that hands `cf.verified_bot_category` to the API; the kept
  custom, rate-limit, and cache rules; the Super Bot Fight Mode settings with the
  planned switch; and the principle that no rule hard-blocks traffic that could
  be a human.
- **The site smoke gets past Super Bot Fight Mode.** With `SMOKE_TOKEN` set,
  `scripts/site-smoke.mjs` sends `X-Smoke-Token` to the site's own origin and
  nowhere else, so a Cloudflare skip rule lets the headless run through once
  automated traffic is challenged. A page Cloudflare challenges anyway reads
  `SKIP` and the run exits 2, because a challenge page says nothing about the
  site; before, it would have read as an outage. A change to the script now also
  runs CI's app-image smoke.
