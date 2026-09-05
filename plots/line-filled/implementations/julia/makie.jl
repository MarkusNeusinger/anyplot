# anyplot.ai
# line-filled: Filled Line Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]

# --- Data ---------------------------------------------------------------
days = 0:119
trend = 40.0 .+ 0.6 .* days
seasonal = 8.0 .* sin.(2π .* days ./ 30)
noise = 5.0 .* randn(length(days))
daily_active_users = max.(trend .+ seasonal .+ noise, 2.0)

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-filled · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Day Since Launch",
    ylabel             = "Daily Active Users (thousands)",
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
)

baseline = zeros(length(days))
band!(ax, days, baseline, daily_active_users; color = (BRAND, 0.35))
lines!(ax, days, daily_active_users; color = BRAND, linewidth = 2.5)
ylims!(ax, 0, nothing)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
