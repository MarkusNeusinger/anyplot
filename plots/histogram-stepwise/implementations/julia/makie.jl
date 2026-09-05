# anyplot.ai
# histogram-stepwise: Step Histogram
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — 8 hues, theme-independent, hybrid-v3 sort
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green, ALWAYS first series
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3", colorant"#BD8233", colorant"#AE3030",
    colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------
# One-way commute times (minutes) for two travel modes — overlaid step
# histograms let the shapes be compared without one distribution occluding
# the other, which is exactly what stepwise outlines are for.
n = 900
cyclist_commutes = max.(28.0 .+ 6.0 .* randn(n), 3.0)

# Drivers show a right-skewed secondary mode: roughly a quarter of trips hit
# heavy traffic and run noticeably longer, giving the distribution real shape
# beyond a plain bell curve.
driver_base       = 36.0 .+ 7.0 .* randn(n)
congestion_hit    = rand(n) .< 0.28
driver_commutes   = max.(driver_base .+ congestion_hit .* (16.0 .+ 8.0 .* rand(n)), 3.0)

cyclist_median = median(cyclist_commutes)
driver_median  = median(driver_commutes)

# --- Plot -----------------------------------------------------------------
title_str = "histogram-stepwise · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 23,
    titlecolor         = INK,
    xlabel             = "Commute Time (minutes)",
    ylabel             = "Number of Commuters",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = true,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
)

stephist!(ax, cyclist_commutes; bins = 30, color = IMPRINT_PALETTE[1],
          linewidth = 3.0, label = "Cyclists")
stephist!(ax, driver_commutes; bins = 30, color = IMPRINT_PALETTE[2],
          linewidth = 4.0, label = "Drivers")

# Dashed median markers give each distribution a focal point and make the
# ~10-minute commute-time gap between modes visible at a glance.
vlines!(ax, [cyclist_median]; color = (IMPRINT_PALETTE[1], 0.5), linewidth = 2,
        linestyle = :dash)
vlines!(ax, [driver_median]; color = (IMPRINT_PALETTE[2], 0.5), linewidth = 2,
        linestyle = :dash)

axislegend(ax; position = :rt, framevisible = false, labelcolor = INK_SOFT)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
