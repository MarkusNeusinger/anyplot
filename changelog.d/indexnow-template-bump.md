### Changed

- **A `TEMPLATE_LAST_CHANGED` bump now reaches Bing, Yandex, Seznam, Naver and
  Yep.** `indexnow-submit.yml` also runs on pushes that touch
  `api/routers/seo.py`, and submits the full URL list when the diff adds or
  removes the constant's assignment line. Any other change to that file
  submits nothing. Google learns of a bump from the sitemap's `lastmod`, but
  the IndexNow engines never read it, so the retitling of all 5,172 spec pages
  in #11844 had to be submitted by hand. (#11849)

### Fixed

- **IndexNow no longer submits `/{spec}/python/` redirects.** Both the full
  list and the per-push diff took every file under `metadata/<language>/` as
  a page, so a `.gitkeep` became an empty library and a URL that answers 301.
  The full list now takes only `.yaml` metadata files, and the diff counts an
  implementation file only beside its metadata `.yaml`. The full list drops
  from 5,187 to 5,182 URLs, the size of the sitemap. The 10 stale `.gitkeep`
  placeholders in five fully implemented spec directories are gone as well. (#11849)
