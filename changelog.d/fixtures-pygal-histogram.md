### Fixed

- **The eval fixtures count pygal's `histogram-basic` as eligible again.** Its
  regeneration (#12416) dropped the PIL overlay that blocked it, which turned the
  fixture test that still pinned it as blocked red on `main`; only pygal's
  `line-timeseries`, whose regeneration kept the standard `random` module, stays
  blocked.
