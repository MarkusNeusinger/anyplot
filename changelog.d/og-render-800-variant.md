### Fixed

- **OG cards render from the 800px derivative again, so the API's memory stays
  flat.** `_fetch_image` in `api/routers/og_images.py` only swapped in the
  800px variant for URLs ending in `/plot.png`, but since preview URLs became
  `plot-light.png` in April no URL matched. Every OG cache miss downloaded and
  decoded the full-size original: a median 22 MiB for a branded card and
  150-200 MiB for a collage (up to ~430 MiB). glibc kept the freed Pillow
  blocks in the render threads' arenas, so the resident size climbed in
  70-160 MiB steps after large collage misses and never came back down — most
  of the multi-day climb, and a risk of running out of memory when two large
  collages overlapped. Now any full-size `*.png` preview maps to its `_800`
  sibling (`plot-light_800.png`, `plot-dark_800.png`, legacy `plot_800.png`),
  which exists for all 4,848 implementations. A failed fetch falls back to the
  original with a logged warning instead of a silent `pass`, so a future
  naming change cannot turn the shortcut off unnoticed. In a replay of the
  production traffic, retained memory stays flat at about +45 MiB instead of
  climbing, and the render peak drops to about 157 MiB from 430-580 MiB. The
  tests now use production-shaped `plot-light.png` URLs; the legacy
  `plot.png` fixtures are why the dead branch stayed green.
