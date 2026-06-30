# anyplot.ai
# errorbar-basic: Basic Error Bar Plot
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-30

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — first categorical series (Imprint brand green)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data: Mean seedling height (cm) under 6 light intensity levels
# Standard deviation from 20 replicate seedlings per condition
light_levels = ["50 lux", "100 lux", "200 lux", "400 lux", "800 lux", "1600 lux"]
mean_height  = [1.2, 2.8, 4.5, 6.1, 7.3, 7.8]
std_height   = [0.35, 0.42, 0.51, 0.68, 0.72, 0.85]
n = length(light_levels)
x_pos = collect(1:n)

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "errorbar-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Light Intensity",
    ylabel             = "Mean Seedling Height (cm)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
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
    ygridcolor         = RGBAf(Float32(INK.r), Float32(INK.g), Float32(INK.b), 0.15f0),
    yminorgridvisible  = false,
    xticks             = (x_pos, light_levels),
)

errorbars!(ax, x_pos, mean_height, std_height;
    color        = IMPRINT_PALETTE[1],
    linewidth    = 2.5,
    whiskerwidth = 12,
)

lines!(ax, x_pos, mean_height;
    color     = IMPRINT_PALETTE[1],
    linewidth = 2.0,
)

scatter!(ax, x_pos, mean_height;
    color       = IMPRINT_PALETTE[1],
    markersize  = 14,
    strokewidth = 1.5,
    strokecolor = PAGE_BG,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
