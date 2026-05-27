# anyplot.ai
# map-tile-background: Map with Tile Background
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 72/100 | Created: 2026-05-27

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const GRID_COLOR  = THEME == "light" ? RGBAf(0.102, 0.102, 0.09, 0.12) : RGBAf(0.941, 0.937, 0.91, 0.12)

# Sequential colormap for continuous data (anyplot imprint_seq)
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# Data: Major global tourist destinations with annual visitor counts (millions)
city_names = [
    "Paris", "London", "New York", "Tokyo", "Barcelona",
    "Rome", "Dubai", "Istanbul", "Amsterdam", "Singapore",
    "Sydney", "Bangkok", "Mumbai", "Berlin", "Prague",
    "Vienna", "Budapest", "Lisbon", "Copenhagen", "Stockholm"
]

lons = Float64[
    2.35, -0.12, -74.0, 139.7, 2.17,
    12.5, 55.3, 28.98, 4.9, 103.8,
    151.2, 100.5, 72.88, 13.41, 14.42,
    16.37, 19.04, -9.14, 12.57, 18.07
]

lats = Float64[
    48.85, 51.51, 40.71, 35.68, 41.39,
    41.9, 25.2, 41.01, 52.37, 1.35,
    -33.87, 13.75, 19.08, 52.52, 50.08,
    48.21, 47.5, 38.72, 55.68, 59.33
]

# Annual visitors in millions (approximate)
visitors = Float64[
    34.0, 31.0, 13.6, 12.9, 9.0,
    9.7, 16.7, 14.0, 8.6, 19.1,
    3.8, 22.8, 7.0, 5.3, 4.4,
    6.8, 4.4, 4.1, 2.7, 2.9
]

min_v = minimum(visitors)
max_v = maximum(visitors)
v_norm = (visitors .- min_v) ./ (max_v - min_v)
marker_sizes = 10.0 .+ 28.0 .* v_norm

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "map-tile-background · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Longitude",
    ylabel             = "Latitude",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = GRID_COLOR,
    ygridcolor         = GRID_COLOR,
)

scatter!(
    ax, lons, lats;
    color       = v_norm,
    colormap    = ANYPLOT_SEQ,
    markersize  = marker_sizes,
    strokewidth = 1.5,
    strokecolor = PAGE_BG,
)

# Label the top 8 most-visited cities
top_indices = sortperm(visitors, rev=true)[1:8]
for i in top_indices
    text!(
        ax, lons[i], lats[i];
        text     = city_names[i],
        fontsize = 10,
        color    = INK,
        offset   = (8, 5),
        align    = (:left, :bottom),
    )
end

Colorbar(
    fig[1, 2];
    colormap       = ANYPLOT_SEQ,
    limits         = (min_v, max_v),
    label          = "Annual Visitors (millions)",
    labelcolor     = INK,
    tickcolor      = INK_SOFT,
    ticklabelcolor = INK_SOFT,
    width          = 16,
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
