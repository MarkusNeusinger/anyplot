# Makie.jl

Makie.jl is the high-performance visualization ecosystem for Julia. This is
anyplot's first Julia-language entry; the file extension is **`.jl`** and the
runtime is **`julia --project=.`**, not Python and not Rscript.

anyplot uses the **CairoMakie** backend exclusively — pure-Cairo, headless,
PNG/SVG/PDF out of the box, no GPU or display server required. `GLMakie` and
`WGLMakie` are interactive backends that are explicitly out of scope.

## IMPORTANT: No Workarounds

**If Makie cannot implement a plot type natively, DO NOT shell out to
matplotlib, Python, R, or another backend.**

Makie is a complete visualization grammar. If a spec genuinely cannot be
expressed with Makie + the recipe ecosystem, the implementation should FAIL
rather than fall back to another library.

Out of native CairoMakie scope:
- True interactivity (hover, zoom, brush, animation) — needs `GLMakie` /
  `WGLMakie`
- WebGL-only effects
- Embedded D3-style network layouts — `NetworkLayout.jl` is **not**
  installed in the CI runtime, so do not `using NetworkLayout`. Network /
  graph specs whose primary value is the layout itself should return
  `NOT_FEASIBLE` rather than improvise.

## Interactive Spec Handling

CairoMakie produces **static PNG only**. Same model as matplotlib / seaborn /
plotnine / ggplot2. When implementing specs that mention interactive
features:

- Specs whose PRIMARY value is interactivity (hover, zoom, click, brush) →
  **NOT_FEASIBLE**
- Specs with animation → use small multiples (facetted `Axis` grid) as a
  static alternative
- Mixed specs (static + interactive) → implement static features only, omit
  interactive silently
- **NEVER** simulate tooltips, hover states, or controls. See AR-08 in
  `prompts/quality-criteria.md`.

---

## Imports

```julia
using CairoMakie
using Makie
using DataFrames
using Colors
using ColorSchemes
using Random
using Statistics
```

Optional dataset packages available in the CI runtime: `RDatasets` (gives
`iris`, `mtcars`, `diamonds` cross-language-compatibly), `PalmerPenguins`.
`CSV` is available for ad-hoc data loading but anyplot implementations
should generate data in-memory.

## Reproducibility

```julia
Random.seed!(42)
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate
in `impl-review.yml` rejects anything off by more than 16 px and re-triggers
repair):

| Orientation | `Figure(resolution=...)` × `save(..., px_per_unit=...)` | Final PNG     |
|-------------|----------------------------------------------------------|---------------|
| Landscape   | `resolution = (1600, 900)`, `px_per_unit = 2`            | 3200 × 1800   |
| Square      | `resolution = (1200, 1200)`, `px_per_unit = 2`           | 2400 × 2400   |

Pick the orientation that suits the spec. CairoMakie honours `resolution`
and `px_per_unit` exactly — no padding or cropping, so the saved PNG lands
on target without extra tricks. Do **not** deviate from these pairs.

## Figure Size & Sizing for 3200×1800 px (starting values — review loop tunes)

Makie's text sizes are scaled by `px_per_unit`. With `px_per_unit = 2` and
the landscape canvas, the values below produce a comfortable proportional
result; tune up or down if review feedback says so.

```julia
fig = Figure(
    resolution = (1600, 900),
    fontsize   = 14,        # base font; px_per_unit doubles this on save
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title       = "scatter-basic · julia · makie · anyplot.ai",
    titlesize   = 20,
    xlabel      = "X",
    ylabel      = "Y",
    xlabelsize  = 14,
    ylabelsize  = 14,
    xticklabelsize = 12,
    yticklabelsize = 12,
    backgroundcolor = PAGE_BG,
)
```

Geom-equivalent sizing (Makie plot primitives):
- `scatter!(ax, x, y; markersize = 12)` — sparse data; bump down for dense.
- `lines!(ax, x, y; linewidth = 2.5)` — sparse; ~1.5 for dense overlays.

## Save (PNG, both themes)

```julia
save("plot-$(THEME).png", fig; px_per_unit = 2)
```

`px_per_unit = 2` doubles the resolution at write time — combined with the
canonical `resolution` values above, this is what produces 3200×1800 or
2400×2400 pixels.

## Colors

Use the anyplot palette (see `prompts/default-style-guide.md`
"Categorical Palette"). First series is **always** `#009E73`.

```julia
const ANYPLOT_PALETTE = [
    colorant"#009E73",  # 1 — first categorical series (anyplot brand green)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red (semantic anchor for bad / loss / error)
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]
const ANYPLOT_AMBER = colorant"#DDCC77"  # warning / caution (outside the categorical pool)

# Single-series
scatter!(ax, x, y; color = ANYPLOT_PALETTE[1])

# Multi-series — categorical
scatter!(ax, x, y; color = group, colormap = ANYPLOT_PALETTE)

# Continuous — only the two anyplot palette-derived cmaps are allowed.
using ColorSchemes
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])                                    # sequential / single-polarity
const _midpoint   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"                         # theme-adaptive
const ANYPLOT_DIV = cgrad([colorant"#AE3030", _midpoint, colorant"#4467A3"])                         # diverging
# Sequential heatmap:  heatmap!(ax, z; colormap = ANYPLOT_SEQ)
# Diverging heatmap:   heatmap!(ax, z; colormap = ANYPLOT_DIV)
```

Never use `:viridis`, `:cividis`, `:BrBG`, `:Reds`/`:Blues`/`:Greens`,
`:rainbow`, `:jet`, `:hsv`, `:gist_rainbow`, or any other named
colormap — only the two anyplot stops above are allowed.

## Theme-adaptive Chrome (Makie mapping)

Read `ANYPLOT_THEME` from the environment and flip chrome tokens. Data
colors stay identical between themes — only the surrounding chrome changes.

```julia
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    backgroundcolor   = PAGE_BG,
    titlecolor        = INK,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    topspinevisible   = false,
    rightspinevisible = false,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible = false,
    yminorgridvisible = false,
)
```

## Plot Primitives (most common)

```julia
scatter!(ax, x, y)              # scatter
lines!(ax, x, y)                # line
barplot!(ax, x, y)              # bar from precomputed values
hist!(ax, x; bins = 30)         # histogram
density!(ax, x)                 # density
heatmap!(ax, z)                 # heatmap
contour!(ax, x, y, z)           # contour
boxplot!(ax, group, value)      # boxplot
violin!(ax, group, value)       # violin

# Small multiples: layout into a grid
ax1 = Axis(fig[1, 1]); ax2 = Axis(fig[1, 2])
```

## Script Skeleton

A complete Makie implementation reads `ANYPLOT_THEME`, generates data,
builds the figure, and saves both themed PNGs by being invoked twice with
different env values. The same single `.jl` file handles both themes — no
two-file split.

```julia
using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const ANYPLOT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -------------------------------------------------------------------
x = randn(100)
y = randn(100)

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "scatter-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "X",
    ylabel             = "Y",
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

scatter!(ax, x, y; color = ANYPLOT_PALETTE[1], markersize = 12, strokewidth = 0)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/julia/makie.jl` —
  executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` (CairoMakie is
  PNG-only in this catalog; no HTML variant — GLMakie / WGLMakie are out
  of scope).

## Header Style

Julia has no docstring syntax in the Python sense. anyplot uses a `#`
comment block at the top of every `.jl` file, mirroring the conventions
for Python (triple-quoted docstring) and R (`#'` roxygen block).

```julia
# anyplot.ai
# scatter-basic: Basic Scatter Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-05-22
```

The pipeline's `impl-review.yml` header-rewrite step replaces the leading
block with the canonical four-line header once a quality score is
assigned. If the file has no leading `#` block, the rewrite prepends one.

## Julia / Makie-Specific Gotchas

- `using CairoMakie` is enough — do **not** also `import Plots`. Plots.jl
  is the alternative ecosystem and is out of scope for this entry.
- Never call `display(fig)` instead of `save(...)` — `display` opens an
  interactive backend, which CI does not have.
- `@show` and bare expressions at the script level pollute stdout in
  the runner; keep the script silent except for the `save` call.
- `colorant"#RRGGBB"` (from `Colors`) is the canonical hex-to-color
  helper. Prefer it over manual `RGB(r/255, g/255, b/255)` constructors.
- For multi-series categorical color, pass an `ANYPLOT_PALETTE[1:n]` slice to
  `colormap = ...` rather than letting Makie's default cycle pick the
  first color (which is **not** anyplot brand green).
- The implementation file must end with a trailing newline — Julia
  parses fine without it, but the impl-review header rewrite assumes
  one.
