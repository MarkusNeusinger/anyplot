# anyplot.ai
# density-basic: Basic Density Plot
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-05-30

using CairoMakie
using Colors
using Random

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

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
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

density!(ax, bike_times;
    color       = (IMPRINT_PALETTE[1], 0.30),
    strokecolor = IMPRINT_PALETTE[1],
    strokewidth = 2.5,
    label       = "Bicycle",
)

density!(ax, bus_times;
    color       = (IMPRINT_PALETTE[3], 0.30),
    strokecolor = IMPRINT_PALETTE[3],
    strokewidth = 2.5,
    label       = "Bus",
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
