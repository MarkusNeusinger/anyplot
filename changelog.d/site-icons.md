### Fixed

- **Google showed no icon for anyplot.ai.** Crawlers are routed to the bot HTML
  from `api/routers/seo.py`, whose `<head>` declared no icon, and Google's
  `/favicon.ico` fallback returned 404. The bot template now carries the same
  icon links as `app/index.html`, and `app/public/` ships a real `favicon.ico`
  (16, 32, 48 px) and an `apple-touch-icon.png`. `Organization.logo` points at
  the new square `icon-512.png` instead of the 1200×630 banner. (#11838)

### Changed

- **The favicon is drawn from the real MonoLisa outlines.** An SVG favicon
  loads no webfonts, so the `<text>` mark always rendered in the viewer's
  system monospace. `scripts/generate_favicon.py` outlines the `ap` monogram
  from MonoLisa Bold into plain paths on an opaque paper ground (a transparent
  icon with dark ink vanished on dark result pages) and rasterizes the ICO and
  PNG siblings from that one SVG. (#11838)
