### Fixed

- **OG cards render from the 800px derivative again, so the API's memory stays
  flat.** `_fetch_image` in `api/routers/og_images.py` only swapped in the
  800px variant for URLs ending in `/plot.png`, and no preview URL has matched
  since they became `plot-light.png` on 2026-04-23. Every OG cache miss
  therefore decoded the full-size original: a median 22 MiB for a branded
  card, 150-200 MiB for a collage (up to ~430 MiB). The allocator kept those
  freed blocks in the render threads' arenas, so the API's memory climbed in
  70-160 MiB steps after large collage misses and never came back down, with
  a risk of running out when two large collages overlapped. Any full-size
  `*.png` preview now maps to its `_800` sibling, which exists for all 4,848
  implementations, and a failed fetch falls back to the original with a
  logged warning instead of a silent `pass`. In a replay of production
  traffic, retained memory stays flat at about +45 MiB and the render peak
  drops to about 157 MiB from 430-580 MiB.
