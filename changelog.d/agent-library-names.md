### Fixed

- **The chat recognises a library however you write its name.** "erstell das
  bitte mal in d3" and "d3.js" got the pointer to the catalogue as another
  library, and only "D3.js" switched the plot. A code check now lets every
  request through that names only libraries the chat serves, in any case, with
  or without `.js` or `.jl`, with any separator, and in the well-known short
  forms (`ggplot`, `mpl`, `mui x`, `CairoMakie`, `apache echarts`); the library
  switch reads the name the same way. One table in `core/library_names.py`
  holds the names. A request for a tool outside the catalogue (Vega-Lite,
  Excel, Plots.jl) still gets the pointer, and an attack or a data request that
  names a library keeps its refusal. In the scope eval the judge itself refused
  4 of 12 such requests, all of which now go through. (#12855)
