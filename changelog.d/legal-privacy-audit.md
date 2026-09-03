### Changed

- **The privacy policy says what the code actually does, per store.** The section had drifted
  behind a year of features: it promised "no personal data (names, emails, etc.)" while the
  feedback widget asks for exactly that ("Name or email (optional)") and keeps it, with the
  message, the page, the user agent and an IP hash, in a table nothing prunes on a timer. It
  also had no legal basis, no jurisdiction, and a rights list missing restriction, objection
  and the complaint to a supervisory authority. Each store now carries its own retention —
  Cloud Logging's 30 days, a feedback entry until it is deleted by hand — because a single
  blanket figure is the qualifier a shortening pass loses first. Plausible is described by the
  property that matters (no cookies, no cross-site identifier, no IP stored, the browser
  talking only to our domain) rather than the false one it used to claim (the script is
  Plausible's, only served from here), Cloudflare's edge processing of the IP is named, and
  the "all services in the EU" line no longer swallows a global CDN and a separate analytics
  service. The crawler body in `api/routers/seo.py` mirrored the same wrong sentence and was
  corrected with it (#11217).
