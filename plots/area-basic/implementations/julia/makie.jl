# anyplot.ai
# area-basic: Basic Area Chart
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: pending | Created: 2026-05-28

using CairoMakie
using Colors
using DataFrames
using Random

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# Columns: set these to your table's column names
const HOUR = "Hour"                       # role: x
const CPU = "CPU Utilization (%)"         # role: y

# Data: hourly CPU utilization over 48 hours (diurnal workload pattern)
Random.seed!(42)
n = 48
hours = collect(0:(n - 1))
base_load = 30.0 .+ 28.0 .* sin.(2π .* (hours .- 6) ./ 24)
noise = 5.0 .* randn(n)
df = DataFrame(HOUR => hours, CPU => clamp.(base_load .+ noise, 5.0, 95.0))

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "area-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = HOUR,
    ylabel             = CPU,
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
    ygridcolor         = RGBAf(Float32(INK.r), Float32(INK.g), Float32(INK.b), 0.15f0),
    yminorgridvisible  = false,
    xminorgridvisible  = false,
)

x = df[!, HOUR]
y = df[!, CPU]

# Area fill (semi-transparent)
band!(ax, x, zeros(length(y)), y; color = (IMPRINT_PALETTE[1], 0.35))

# Line on top
lines!(ax, x, y; color = IMPRINT_PALETTE[1], linewidth = 2.5)

ylims!(ax, 0, maximum(skipmissing(y)) * 1.15)
xlims!(ax, minimum(x), maximum(x))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
