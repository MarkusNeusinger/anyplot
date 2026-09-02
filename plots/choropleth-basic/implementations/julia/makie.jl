# anyplot.ai
# choropleth-basic: Choropleth Map with Regional Coloring
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 74/100 | Created: 2026-09-02

using CairoMakie
using Colors
using ColorSchemes
using Random

Random.seed!(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const MUTED    = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint sequential colormap — single-polarity continuous data
const IMPRINT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# --- Data: renewable-energy share by U.S. state (%) -------------------------
# CairoMakie has no geographic-projection support in this runtime (no
# GeoMakie / shapefile access), so states are laid out on a schematic
# west-to-east, north-to-south grid instead of true polygon boundaries —
# a standard "tile grid map" technique for choropleth-style regional
# shading that needs no shapefile dependency. Each cell holds (col, row).
const STATE_GRID = Dict(
    "AK" => (0, 0), "ME" => (11, 0),
    "WA" => (1, 1), "ID" => (2, 1), "MT" => (3, 1), "ND" => (4, 1),
    "MN" => (5, 1), "WI" => (6, 1), "MI" => (7, 1), "NY" => (9, 1),
    "VT" => (10, 1), "NH" => (11, 1),
    "OR" => (1, 2), "NV" => (2, 2), "WY" => (3, 2), "SD" => (4, 2),
    "IA" => (5, 2), "IL" => (6, 2), "IN" => (7, 2), "OH" => (8, 2),
    "PA" => (9, 2), "MA" => (10, 2), "RI" => (11, 2),
    "CA" => (1, 3), "UT" => (2, 3), "CO" => (3, 3), "NE" => (4, 3),
    "MO" => (5, 3), "KY" => (6, 3), "WV" => (7, 3), "VA" => (8, 3),
    "MD" => (9, 3), "NJ" => (10, 3), "CT" => (11, 3),
    "AZ" => (2, 4), "NM" => (3, 4), "KS" => (4, 4), "AR" => (5, 4),
    "TN" => (6, 4), "NC" => (7, 4), "SC" => (8, 4), "DE" => (9, 4),
    "TX" => (3, 5), "OK" => (4, 5), "LA" => (5, 5), "MS" => (6, 5),
    "AL" => (7, 5), "GA" => (8, 5),
    "FL" => (8, 6),
    "HI" => (0, 7),
)

states = sort(collect(keys(STATE_GRID)))
renewable_share = Dict(s => round(15 + 70 * rand(), digits=1) for s in states)

# A few states have not reported yet — rendered as muted "no data" tiles
for s in ("MT", "SD", "WY")
    renewable_share[s] = NaN
end

data_values = [v for v in values(renewable_share) if !isnan(v)]
vmin, vmax = extrema(data_values)

# --- Plot ---------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title           = "choropleth-basic · julia · makie · anyplot.ai",
    titlesize       = 20,
    titlecolor      = INK,
    backgroundcolor = PAGE_BG,
    aspect          = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)

tile = 0.86  # tile side length; the 0.14 gap reads as grid seams between states

for s in states
    col, row = STATE_GRID[s]
    x, y = Float64(col), -Float64(row)
    v = renewable_share[s]
    missing_data = isnan(v)
    fill_color = missing_data ? MUTED : IMPRINT_SEQ[(v - vmin) / (vmax - vmin)]
    # MUTED flips from medium-dark (light theme) to medium-light (dark theme),
    # so the "no data" tile needs the opposite text tone from data tiles.
    text_color = missing_data ? (THEME == "light" ? ELEVATED : colorant"#1A1A17") : ELEVATED

    poly!(ax, Rect2f(x - tile / 2, y - tile / 2, tile, tile);
          color = fill_color, strokewidth = 2, strokecolor = PAGE_BG)
    text!(ax, Point2f(x, y); text = s, align = (:center, :center),
          fontsize = 13, color = text_color)
end

Colorbar(fig[1, 2];
    limits         = (vmin, vmax),
    colormap       = IMPRINT_SEQ,
    label          = "Renewable Energy Share (%)",
    labelcolor     = INK,
    ticklabelcolor = INK_SOFT,
    labelsize      = 14,
    ticklabelsize  = 12,
    width          = 20,
)
colgap!(fig.layout, 20)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
