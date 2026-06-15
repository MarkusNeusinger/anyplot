# anyplot.ai
# line-cycle-seasonal: Cycle Plot (Seasonal Subseries)
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-06-15

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
    colorant"#954477",
    colorant"#99B314",
]

# Data: Monthly average temperature (°C), mid-latitude city, 1994–2023
const N_YEARS     = 30
const N_MONTHS    = 12
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
const BASE_TEMPS  = [-3.2, -1.8, 4.5, 11.2, 17.8, 22.5, 25.1, 24.3, 18.6, 12.1, 4.8, -1.5]
const WARMING_RATE = 0.04  # °C per year

temps = [BASE_TEMPS[mi] + WARMING_RATE * (yi - 1) + randn() * 1.2
         for yi in 1:N_YEARS, mi in 1:N_MONTHS]

# Title with length-scaled fontsize
const TITLE      = "Monthly Temperature Cycles · line-cycle-seasonal · julia · makie · anyplot.ai"
const TITLE_LEN  = length(TITLE)
const TITLE_SIZE = round(Int, 20 * (TITLE_LEN > 67 ? 67 / TITLE_LEN : 1.0))

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = TITLE,
    titlesize          = TITLE_SIZE,
    titlecolor         = INK,
    xlabel             = "Month",
    ylabel             = "Average Temperature (°C)",
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
    xticks             = (collect(1:N_MONTHS), MONTH_NAMES),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

xlims!(ax, 0.5, 12.5)

# Seasonal groups: each month centered at its integer position ±GROUP_HALF
const GROUP_HALF    = 0.35
const SUBSERIES_COL = IMPRINT_PALETTE[1]   # #009E73 – brand green (annual subseries)
const MEAN_COL      = IMPRINT_PALETTE[3]   # #4467A3 – blue (monthly mean reference)

for mi in 1:N_MONTHS
    center     = float(mi)
    x_range    = range(center - GROUP_HALF, center + GROUP_HALF; length = N_YEARS)
    y_vals     = temps[:, mi]
    group_mean = mean(y_vals)

    # Chronological subseries line within this month group
    lines!(ax, collect(x_range), y_vals;
           color     = (SUBSERIES_COL, 0.72),
           linewidth = 1.8)

    # Horizontal mean reference line — the key seasonal comparison element
    lines!(ax, [center - GROUP_HALF, center + GROUP_HALF], [group_mean, group_mean];
           color     = MEAN_COL,
           linewidth = 3.5)

    # Subtle vertical divider between month groups
    if mi < N_MONTHS
        vlines!(ax, center + 0.5;
                color     = RGBAf(INK.r, INK.g, INK.b, 0.10),
                linewidth = 0.8)
    end
end

# Legend
elem_sub  = LineElement(color = SUBSERIES_COL, linewidth = 1.8)
elem_mean = LineElement(color = MEAN_COL,       linewidth = 3.5)
Legend(
    fig[1, 2],
    [elem_sub, elem_mean],
    ["Annual observations\n(1994–2023)", "Monthly mean"];
    framecolor      = RGBAf(INK_SOFT.r, INK_SOFT.g, INK_SOFT.b, 0.35f0),
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK_SOFT,
    labelsize       = 12,
    patchsize       = (25, 14),
    padding         = (12, 12, 10, 10),
)

colsize!(fig.layout, 1, Relative(0.84))

save("plot-$(THEME).png", fig; px_per_unit = 2)
