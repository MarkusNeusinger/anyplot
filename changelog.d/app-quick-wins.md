### Fixed

- **`/specs` thumbnails follow the site theme, and every library has its short
  name.** The spec list showed the light render in dark mode; it now picks the
  render the gallery cards pick. The compact gallery cards and the mobile
  library carousel read the shared 15-library abbreviation map, so MUI X,
  ggplot2 and Makie show `mui.tsx`, `gg.r` and `mk.jl` instead of their full ids
  (#12546).
- **Links and copy that pointed at the wrong place or said the wrong thing.**
  `libraries.all()` on the landing page opens `/libraries`, not `/plots`; the
  palette link on `/about` navigates inside the app instead of reloading the
  page; `request_plot()` opens the plot request form instead of a blank issue
  with a label and a title prefix. The `/plots` description drops its stale
  "2,600+" count and `/specs` no longer calls the specifications Python-only;
  `/mcp` lists every tag filter `search_specs_by_tags` takes; `llms.txt` names
  the "Use with my data" chat (#12546).
- **Page metadata matches the bot HTML.** Spec pages name Julia and JavaScript
  in the `SoftwareSourceCode` language, carry the bot's breadcrumb (home, spec,
  library), and share the spec card as `og:image` on the hub. The shell's
  `og:image` is the card the bot serves for `/`, and its `theme-color` is the
  page background. `/map` is titled `map | anyplot.ai` with a canonical URL, and
  the chat tab names the plot instead of its spec id (#12546).
- **Toggle state reaches assistive technology on `/palette` and `/map`.** The
  sort buttons carry `aria-pressed`, and the legend and weights toggles carry
  `aria-expanded` (#12546).
