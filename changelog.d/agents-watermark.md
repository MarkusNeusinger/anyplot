### Added

- **A footer strip on every user plot the agents service serves.** The PNGs of
  the artifact route and the images of the feedback bundle carry a strip below
  the plot, "made with any.plot()" on the left and "anyplot.ai/<spec-id>" on the
  right, in JetBrains Mono with the dot drawn as a brand-green square (the
  owner's variant `s1c-jb-sq2` of 2026-10-10). `agents/anyplot/render/watermark.py`
  composites it at image level after the run and scales it with the canvas, so
  a 3200x1800 render is served as 3200x1864 and the square format as
  2400x2448; the plot above the strip stays pixel-identical. The gates, the
  reviewer, the render store and the exported `plot.py` keep working with the
  raw render, so the downloaded code reproduces the plot without the strip.
  The route composes it once per theme and caches it in the render store, a
  cache that gives way to new renders before the store reports itself full;
  `AGENT_WATERMARK=false` serves the raw renders, and the eval harness sets it
  so its renders stay comparable with its baselines. JetBrains Mono 2.304 is
  vendored unmodified under the SIL Open Font License 1.1 with a notice in
  `agents/anyplot/render/fonts/` and loads when the service starts. The chat
  page's result card takes the loaded PNG's own aspect instead of a fixed 16:9,
  and the local BFF mock draws the same strip.
