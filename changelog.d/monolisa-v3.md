### Changed

- **The site's typeface is MonoLisa 3.000: MonoLisa Code everywhere, MonoLisa
  Text registered for experiments.** The v3 webfonts (70 Unicode-range subsets
  per family, variable `wght` + `GRAD`) live under `gs://anyplot-static/fonts/v3/`
  and `app/src/styles/fonts.css` is now generated from the order page's builder
  CSS by `automation/scripts/monolisa_fonts_css.py`, so the next font update is
  a re-run. Two v2 → v3 breaking changes are absorbed: the script italic is
  `ss01` (the old `ss02` tag now means "alt i r"), and the coding ligatures
  moved from `liga` to `dlig`, which `tokens.css` re-enables on `pre`/`code` so
  code blocks look as before. The OG-image renderer loads the v3 Code TTFs from
  the same prefix, sets only the `wght` axis of the now two-axis font, and draws
  the tagline with `ss01`. Family names in CSS are `'MonoLisa Code'` and
  `'MonoLisa Text'` (new `--text` token). The v2 files stay in the bucket until
  the cutover is verified, then move to their own domain.
