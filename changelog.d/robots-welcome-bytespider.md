### Changed

- **robots.txt welcomes every crawler, Bytespider included.** The group that
  declined Bytespider on bandwidth grounds is gone from `app/public/robots.txt`,
  matching the deletion of its Cloudflare block on 2026-11-09: the owner decided
  that every crawler is welcome, and blocking returns only on evidence from the
  request logs. The deploy smoke in `app/cloudbuild.yaml` and the daily
  `bot-serving-check` now recognise the static file by its `Sitemap:` line, the
  one directive the API's own robots.txt does not share, so a misrouted request
  still fails them. `docs/reference/seo.md` and the `app/nginx.conf` comment
  follow.
