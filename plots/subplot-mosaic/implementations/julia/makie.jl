# anyplot.ai
# subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-09

using CairoMakie
using Colors
using Random
using Statistics: mean

Random.seed!(42)

# --- Theme tokens ------------------------------------------------------------
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const GRID_RGBA = RGBAf(INK.r, INK.g, INK.b, 0.15)
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------------
# Household energy dashboard, one day at 10-minute resolution.
n_steps = 144
time_hours = collect(range(0, 24; length = n_steps))

outdoor_temp = 18 .+ 8 .* sin.(2π .* (time_hours .- 9) ./ 24) .+ randn(n_steps) .* 0.6
heating_load = 0.06 .* max.(outdoor_temp .- 19, 0.0) .^ 1.5
evening_bump = 0.5 .* (sin.(2π .* (time_hours .- 18) ./ 24) .+ 1) .^ 2
power_draw = 0.9 .+ heating_load .+ evening_bump .+ 0.08 .* randn(n_steps)
power_draw = max.(power_draw, 0.3)

device_categories = ["HVAC", "Water Heater", "Appliances", "Lighting", "Electronics"]
device_avg_draw = [1.32, 0.58, 0.44, 0.21, 0.29]

humidity = 55 .+ 10 .* sin.(2π .* (time_hours .- 3) ./ 24) .+ randn(n_steps) .* 3
sample_idx = 1:3:n_steps

period_labels = ["Night", "Morning", "Afternoon", "Evening"]
period_bounds = [(0, 6), (6, 12), (12, 18), (18, 24)]
period_avg_draw = [
    mean(power_draw[(time_hours .>= lo) .& (time_hours .< hi)]) for (lo, hi) in period_bounds
]

electricity_rate = 0.18  # $/kWh
cumulative_cost = cumsum(power_draw .* (10 / 60) .* electricity_rate)

# --- Plot -----------------------------------------------------------------
# Mosaic pattern encoded via GridLayout spans (Makie has no string-mosaic
# parser, so spans are the native equivalent of "AAAAAA;BBBCCC;DDEEFF"):
#   row 1: A A A A A A   (wide overview — dominant)
#   row 2: B B B C C C   (two medium detail panels)
#   row 3: D D E E F F   (three small metric panels)
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

Label(
    fig[0, 1:6],
    "subplot-mosaic · julia · makie · anyplot.ai";
    fontsize = 22,
    color    = INK,
    font     = :bold,
    padding  = (0, 0, 8, 0),
)

chrome = (;
    backgroundcolor   = PAGE_BG,
    titlecolor        = INK,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    topspinevisible   = false,
    rightspinevisible = false,
    xminorgridvisible = false,
    yminorgridvisible = false,
)

ax_overview = Axis(
    fig[1, 1:6];
    title        = "Household Power Draw — 24 Hours",
    titlesize    = 17,
    xlabel       = "Hour of Day",
    ylabel       = "Power (kW)",
    xlabelsize   = 14,
    ylabelsize   = 14,
    xgridvisible = false,
    ygridcolor   = GRID_RGBA,
    chrome...,
)

ax_devices = Axis(
    fig[2, 1:3];
    title          = "Average Draw by Device",
    titlesize      = 15,
    ylabel         = "Power (kW)",
    ylabelsize     = 14,
    xticklabelrotation = π / 6,
    xgridvisible   = false,
    ygridcolor     = GRID_RGBA,
    chrome...,
)

ax_temp = Axis(
    fig[2, 4:6];
    title       = "Temperature vs. Draw",
    titlesize   = 15,
    xlabel      = "Outdoor Temp (°C)",
    ylabel      = "Power (kW)",
    xlabelsize  = 14,
    ylabelsize  = 14,
    xgridcolor  = GRID_RGBA,
    ygridcolor  = GRID_RGBA,
    chrome...,
)

ax_period = Axis(
    fig[3, 1:2];
    title          = "Draw by Period",
    titlesize      = 13,
    ylabel         = "kW",
    ylabelsize     = 12,
    xticklabelsize = 11,
    yticklabelsize = 11,
    xgridvisible   = false,
    ygridvisible   = false,
    chrome...,
)

ax_cost = Axis(
    fig[3, 3:4];
    title          = "Cumulative Cost",
    titlesize      = 13,
    xlabel         = "Hour",
    ylabel         = "USD",
    xlabelsize     = 12,
    ylabelsize     = 12,
    xticklabelsize = 11,
    yticklabelsize = 11,
    xgridvisible   = false,
    ygridvisible   = false,
    chrome...,
)

ax_humidity = Axis(
    fig[3, 5:6];
    title          = "Humidity vs. Draw",
    titlesize      = 13,
    xlabel         = "Humidity (%)",
    ylabel         = "kW",
    xlabelsize     = 12,
    ylabelsize     = 12,
    xticklabelsize = 11,
    yticklabelsize = 11,
    xgridvisible   = false,
    ygridvisible   = false,
    chrome...,
)

# A — wide overview: total draw with a band down to its daily floor
band!(
    ax_overview, time_hours, fill(minimum(power_draw), n_steps), power_draw;
    color = (IMPRINT_PALETTE[1], 0.12),
)
lines!(ax_overview, time_hours, power_draw; color = IMPRINT_PALETTE[1], linewidth = 2.5)

# B — medium detail: categorical bar, canonical Imprint order
barplot!(
    ax_devices, 1:length(device_categories), device_avg_draw;
    color = IMPRINT_PALETTE[1:length(device_categories)],
    strokewidth = 0.5, strokecolor = PAGE_BG,
)
ax_devices.xticks = (1:length(device_categories), device_categories)

# C — medium detail: scatter relationship
scatter!(
    ax_temp, outdoor_temp, power_draw;
    color = IMPRINT_PALETTE[6], markersize = 9, strokewidth = 0,
)

# D — small metric panel: period bars
barplot!(
    ax_period, 1:length(period_labels), period_avg_draw;
    color = IMPRINT_PALETTE[1:length(period_labels)],
    strokewidth = 0.5, strokecolor = PAGE_BG,
)
ax_period.xticks = (1:length(period_labels), period_labels)

# E — small metric panel: cumulative cost trend
lines!(ax_cost, time_hours, cumulative_cost; color = IMPRINT_PALETTE[7], linewidth = 2.0)

# F — small metric panel: sparse scatter (subsampled for a clean small panel)
scatter!(
    ax_humidity, humidity[sample_idx], power_draw[sample_idx];
    color = IMPRINT_PALETTE[8], markersize = 8, strokewidth = 0,
)

rowsize!(fig.layout, 1, Relative(0.42))
rowsize!(fig.layout, 2, Relative(0.34))
rowsize!(fig.layout, 3, Relative(0.24))
colgap!(fig.layout, 20)
rowgap!(fig.layout, 22)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
