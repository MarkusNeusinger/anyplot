# anyplot.ai
# density-basic: Basic Density Plot
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-05-30

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens — Imprint palette
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (always first)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data — daily commute durations (minutes) for two transport modes
n_bike = 280
n_bus  = 320

bike_times = clamp.(randn(n_bike) .* 5.0  .+ 22.0,  8.0, 50.0)
bus_times  = clamp.(randn(n_bus)  .* 11.0 .+ 38.0, 10.0, 85.0)

mean_bike = mean(bike_times)
mean_bus  = mean(bus_times)
mean_diff = round(Int, mean_bus - mean_bike)

# Theme-adaptive fill alpha: dark background absorbs low-alpha fills — boost for visibility
bike_alpha = THEME == "dark" ? 0.42 : 0.30
bus_alpha  = THEME == "dark" ? 0.48 : 0.30

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

Label(fig[0, 1],
    "Bus commutes average ~$(mean_diff) min longer — bicycle wins for most urban trips";
    color     = INK_SOFT,
    fontsize  = 11,
    halign    = :left,
    tellwidth = false,
)

ax = Axis(
    fig[1, 1];
    title              = "density-basic · julia · makie · anyplot.ai",
    titlesize          = 22,
    titlecolor         = INK,
    xlabel             = "Commute Duration (minutes)",
    ylabel             = "Density",
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
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    yminorgridvisible  = false,
    xminorgridvisible  = false,
)

# Density curves with theme-adaptive fills
density!(ax, bike_times;
    color       = (IMPRINT_PALETTE[1], bike_alpha),
    strokecolor = IMPRINT_PALETTE[1],
    strokewidth = 2.5,
    label       = "Bicycle",
)

density!(ax, bus_times;
    color       = (IMPRINT_PALETTE[3], bus_alpha),
    strokecolor = IMPRINT_PALETTE[3],
    strokewidth = 2.5,
    label       = "Bus",
)

# Mean reference lines — dashed verticals highlight the distributional gap
vlines!(ax, mean_bike;
    color     = (IMPRINT_PALETTE[1], 0.65),
    linestyle = :dash,
    linewidth = 1.5,
)
vlines!(ax, mean_bus;
    color     = (IMPRINT_PALETTE[3], 0.65),
    linestyle = :dash,
    linewidth = 1.5,
)

# Rug plot — individual observations as tick marks along x-axis baseline
scatter!(ax, bike_times, zeros(n_bike);
    marker      = :vline,
    markersize  = 10,
    color       = (IMPRINT_PALETTE[1], 0.30),
    strokewidth = 0,
)
scatter!(ax, bus_times, zeros(n_bus);
    marker      = :vline,
    markersize  = 10,
    color       = (IMPRINT_PALETTE[3], 0.30),
    strokewidth = 0,
)

axislegend(ax;
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK_SOFT,
    framecolor      = INK_SOFT,
    framevisible    = true,
    position        = :rt,
    labelsize       = 12,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
