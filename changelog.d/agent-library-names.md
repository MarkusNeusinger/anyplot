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
  4 of 12 such requests, all of which now go through.
- **A refusal keeps the session language.** A message without a clear language,
  such as "d3.js", got its refusal in English in a German session. Once the
  session language is recorded or chosen, every refusal after the scope check
  is in it, as the assistant's replies are; before that, a message of fewer
  than three words that the judge reads as English keeps the session's
  language.
