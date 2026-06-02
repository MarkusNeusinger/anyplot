# anyplot.ai
# bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint palette — semantic: green = high/upside, red = low/downside
const COLOR_HIGH = colorant"#009E73"  # Imprint position 1
const COLOR_LOW  = colorant"#AE3030"  # Imprint position 5 (semantic anchor: downside)

# NPV sensitivity analysis — capital investment project, values in millions USD
const BASE_NPV = 120.0

parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Operating Costs",
    "Terminal Value Multiple",
    "Market Share",
    "Tax Rate",
    "Capex Intensity",
    "Working Capital",
    "Inflation Rate",
]
low_values  = [155.0,  95.0, 142.0, 102.0, 104.0, 135.0, 131.0, 126.0, 123.0]
high_values = [ 87.0, 148.0,  99.0, 141.0, 138.0, 109.0, 112.0, 114.0, 116.0]

# Sort ascending by sensitivity range — widest bar plots at top (highest y index)
ranges = abs.(high_values .- low_values)
order  = sortperm(ranges)
n      = length(parameters)
params = parameters[order]
lows   = low_values[order]
highs  = high_values[order]

low_deltas  = lows  .- BASE_NPV
high_deltas = highs .- BASE_NPV

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

title_str = "NPV Sensitivity Analysis · bar-tornado-sensitivity · julia · makie · anyplot.ai"
title_fs  = round(Int, 20 * 67 / length(title_str))

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = title_fs,
    titlecolor         = INK,
    xlabel             = "Net Present Value (millions USD)",
    xlabelcolor        = INK,
    xlabelsize         = 14,
    xticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelsize     = 12,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    ygridvisible       = false,
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

# Tornado bars — low and high input scenarios
barplot!(ax, 1:n, low_deltas;
    direction   = :x,
    offset      = BASE_NPV,
    color       = COLOR_LOW,
    strokewidth = 0,
)
barplot!(ax, 1:n, high_deltas;
    direction   = :x,
    offset      = BASE_NPV,
    color       = COLOR_HIGH,
    strokewidth = 0,
)

# Reference line at base case NPV
vlines!(ax, BASE_NPV; color = INK, linewidth = 2.0, linestyle = :dash)

# Y-axis parameter labels and limits
ax.yticks = (1:n, params)
ylims!(ax, 0.3, Float64(n) + 0.7)

# Legend
elem_high = PolyElement(color = COLOR_HIGH, strokecolor = :transparent)
elem_low  = PolyElement(color = COLOR_LOW,  strokecolor = :transparent)
Legend(
    fig[1, 2],
    [elem_high, elem_low],
    ["High Input Scenario", "Low Input Scenario"];
    framecolor      = INK_SOFT,
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK_SOFT,
    labelsize       = 12,
    rowgap          = 8,
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
