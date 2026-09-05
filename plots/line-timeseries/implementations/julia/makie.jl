# anyplot.ai
# line-timeseries: Time Series Line Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-05

using CairoMakie
using Colors
using Dates
using Random

Random.seed!(42)

# --- Theme tokens ------------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
BRAND    = colorant"#009E73"  # Imprint palette position 1 — always first series

# --- Data ----------------------------------------------------------------------
# Daily average temperature readings across a full year, in degrees Celsius.
start_date = Date(2024, 1, 1)
n_days = 365
dates = start_date .+ Day.(0:(n_days - 1))
day_offset = Float64.(Dates.value.(dates .- start_date))

seasonal_cycle = 14.0 .+ 11.0 .* sin.(2π .* day_offset ./ 365 .- (π / 2))
daily_noise = randn(n_days) .* 2.2
temperature_c = seasonal_cycle .+ daily_noise

# Smart tick locator: one tick per month, labeled with the abbreviated month name.
month_starts = unique(Date.(year.(dates), month.(dates), 1))
tick_positions = Float64.(Dates.value.(month_starts .- start_date))
tick_labels = Dates.format.(month_starts, "u")

# --- Plot ------------------------------------------------------------------------
title_str = "Average Daily Temperature (2024) · line-timeseries · julia · makie · anyplot.ai"
n_chars = length(title_str)
title_fontsize = n_chars > 67 ? max(14, round(Int, 20 * 67 / n_chars)) : 20

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = title_fontsize,
    titlecolor        = INK,
    xlabel            = "Month",
    ylabel            = "Temperature (°C)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    xticks            = (tick_positions, tick_labels),
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible = false,
    yminorgridvisible = false,
)

lines!(ax, day_offset, temperature_c; color = BRAND, linewidth = 2.5)

# --- Save --------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
