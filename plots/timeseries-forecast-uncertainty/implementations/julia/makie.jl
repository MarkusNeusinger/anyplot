# anyplot.ai
# timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random
using Dates
using Statistics

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

# --- Data --------------------------------------------------------------------
# Monthly sales, 3 years of history plus a 6-month forecast with 80/95% bands.
n_hist = 36
n_fcst = 6
n_total = n_hist + n_fcst

months = collect(0:(n_total - 1))
trend = 1000.0 .+ 12.0 .* months
seasonal = 120.0 .* sin.(2π .* months ./ 12)
noise = randn(n_total) .* 35.0
series = trend .+ seasonal .+ noise

actual = fill(NaN, n_total)
actual[1:n_hist] .= series[1:n_hist]

forecast = fill(NaN, n_total)
forecast[n_hist:n_total] .= series[n_hist:n_total]

horizon = 1:n_fcst
spread_80 = 40.0 .+ 14.0 .* horizon
spread_95 = 65.0 .+ 22.0 .* horizon

lower_80 = fill(NaN, n_total)
upper_80 = fill(NaN, n_total)
lower_95 = fill(NaN, n_total)
upper_95 = fill(NaN, n_total)
lower_80[n_hist:n_total] .= [series[n_hist]; series[(n_hist + 1):n_total] .- spread_80]
upper_80[n_hist:n_total] .= [series[n_hist]; series[(n_hist + 1):n_total] .+ spread_80]
lower_95[n_hist:n_total] .= [series[n_hist]; series[(n_hist + 1):n_total] .- spread_95]
upper_95[n_hist:n_total] .= [series[n_hist]; series[(n_hist + 1):n_total] .+ spread_95]

start_date = Date(2023, 1, 1)
dates = [start_date + Month(m) for m in months]
x = Float64.(months)
date_labels = Dict(m => Dates.format(start_date + Month(m), "yyyy-mm") for m in months)
tick_positions = collect(0:6:(n_total - 1))
tick_labels = [date_labels[m] for m in tick_positions]

# --- Plot ---------------------------------------------------------------------
title_str = "timeseries-forecast-uncertainty · julia · makie · anyplot.ai"

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Month",
    ylabel             = "Sales (units)",
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
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    xticks             = (tick_positions, tick_labels),
    xticklabelrotation = π / 6,
)

# Forecast start marker
vlines!(ax, [Float64(n_hist - 1)]; color = INK_SOFT, linestyle = :dot, linewidth = 1.5)

# 95% band (lighter), then 80% band (darker) nested on top
band!(ax, x, lower_95, upper_95; color = (IMPRINT_PALETTE[3], 0.20), label = "95% interval")
band!(ax, x, lower_80, upper_80; color = (IMPRINT_PALETTE[3], 0.38), label = "80% interval")

lines!(ax, x, actual; color = IMPRINT_PALETTE[1], linewidth = 3, label = "Historical")
lines!(ax, x, forecast; color = IMPRINT_PALETTE[3], linewidth = 3, linestyle = :dash, label = "Forecast")

axislegend(ax; position = :lt, framevisible = false, labelcolor = INK_SOFT, labelsize = 12)

# --- Save ----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
