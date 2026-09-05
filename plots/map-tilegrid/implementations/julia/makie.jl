# anyplot.ai
# map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: pending | Created: 2026-09-05

using CairoMakie
using ColorSchemes
using Colors
using Random

Random.seed!(42)

# --- Theme tokens ------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Continuous, single-polarity metric (share of electricity, %) -> imprint_seq
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])
const TILE_LABEL  = colorant"#FAF8F1"  # constant across themes: sits on data color, not page bg
const TILE_OUTLINE = colorant"#1A1A17"  # constant across themes: text outline for legibility

# --- Data ----------------------------------------------------------------
# European countries laid out on an equal-area tile grid, approximating true
# geographic position (row 0 = north, col 0 = west). Renewable electricity
# share is a unipolar metric, so it uses the sequential Imprint colormap.
codes = [
    "IS", "NO", "SE", "FI",
    "IE", "UK", "DK", "EE",
    "NL", "DE", "CZ", "PL", "LV",
    "BE", "FR", "CH", "AT", "SK", "LT",
    "PT", "ES", "IT", "HU", "RO",
    "HR", "GR", "BG",
]
rows = [
    0, 0, 0, 0,
    1, 1, 1, 1,
    2, 2, 2, 2, 2,
    3, 3, 3, 3, 3, 3,
    4, 4, 4, 4, 4,
    5, 5, 5,
]
cols = [
    0, 3, 4, 5,
    0, 1, 4, 6,
    1, 3, 4, 5, 6,
    1, 2, 3, 4, 5, 6,
    0, 1, 3, 4, 5,
    3, 5, 6,
]
base_renewable_pct = [
    100.0, 98.0, 75.0, 55.0,
    40.0, 43.0, 65.0, 25.0,
    33.0, 46.0, 18.0, 17.0, 45.0,
    25.0, 27.0, 75.0, 78.0, 20.0, 30.0,
    61.0, 42.0, 35.0, 15.0, 42.0,
    40.0, 30.0, 20.0,
]
renewable_pct = clamp.(
    round.(base_renewable_pct .+ (rand(length(base_renewable_pct)) .- 0.5) .* 6, digits=1),
    0.0, 100.0,
)

n_cols = maximum(cols) + 1
n_rows = maximum(rows) + 1
value_min, value_max = extrema(renewable_pct)
norm_values = (renewable_pct .- value_min) ./ (value_max - value_min)
tile_colors = [get(ANYPLOT_SEQ, t) for t in norm_values]

tile_gap = 0.05
tile_rects = [
    Rect2f(c + tile_gap, -(r + 1 - tile_gap), 1 - 2tile_gap, 1 - 2tile_gap)
    for (r, c) in zip(rows, cols)
]
label_positions = [Point2f(c + 0.5, -(r + 0.5)) for (r, c) in zip(rows, cols)]

# --- Plot ----------------------------------------------------------------
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title           = "map-tilegrid · julia · makie · anyplot.ai",
    titlesize       = 20,
    titlecolor      = INK,
    backgroundcolor = PAGE_BG,
    aspect          = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)
xlims!(ax, -0.3, n_cols + 0.3)
ylims!(ax, -(n_rows + 0.3), 0.3)

poly!(ax, tile_rects; color = tile_colors, strokecolor = PAGE_BG, strokewidth = 5)
text!(
    ax, label_positions;
    text        = codes,
    align       = (:center, :center),
    fontsize    = 16,
    color       = TILE_LABEL,
    strokecolor = TILE_OUTLINE,
    strokewidth = 2,
)

Colorbar(
    fig[2, 1];
    colormap      = ANYPLOT_SEQ,
    limits        = (value_min, value_max),
    vertical      = false,
    flipaxis      = false,
    label         = "Renewable Energy Share (%)",
    labelcolor    = INK,
    labelsize     = 14,
    ticklabelsize = 12,
    ticklabelcolor = INK_SOFT,
    tickcolor     = INK_SOFT,
    height        = 40,
)
rowsize!(fig.layout, 1, Relative(0.88))
rowgap!(fig.layout, 18)

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
