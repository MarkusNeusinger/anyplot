### Changed

- **SEO router reuses the shared display-name maps.** `api/routers/seo.py`
  imports `LANGUAGE_NAMES` and `LIBRARY_NAMES` from `core.constants` instead
  of deriving its own copies, so exactly one derived name map exists.
