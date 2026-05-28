# anyplot.ai
# bar-basic: Basic Bar Chart
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 90/100 | Created: 2026-05-28

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const ANYPLOT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = ANYPLOT_PALETTE[1]

# Data — average monthly household energy consumption by appliance (kWh)
appliances = ["Air Conditioning", "Water Heater", "Washer / Dryer", "Refrigerator", "Lighting", "TV / Electronics", "Dishwasher"]
monthly_kwh = [215.0, 185.0, 90.0, 55.0, 45.0, 30.0, 22.0]

n = length(appliances)

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title                = "bar-basic · julia · makie · anyplot.ai",
    titlesize            = 20,
    titlecolor           = INK,
    xlabel               = "Appliance",
    ylabel               = "Avg. Monthly Consumption (kWh)",
    xlabelcolor          = INK,
    ylabelcolor          = INK,
    xlabelsize           = 14,
    ylabelsize           = 14,
    xticklabelcolor      = INK_SOFT,
    yticklabelcolor      = INK_SOFT,
    xticklabelsize       = 12,
    yticklabelsize       = 12,
    xticklabelrotation   = π / 6,
    xtickcolor           = INK_SOFT,
    ytickcolor           = INK_SOFT,
    backgroundcolor      = PAGE_BG,
    topspinevisible      = false,
    rightspinevisible    = false,
    leftspinecolor       = INK_SOFT,
    bottomspinecolor     = INK_SOFT,
    xgridvisible         = false,
    ygridcolor           = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible    = false,
    yminorgridvisible    = false,
)

barplot!(ax, 1:n, monthly_kwh;
    color       = BRAND,
    strokewidth = 0,
)

ax.xticks = (1:n, appliances)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
