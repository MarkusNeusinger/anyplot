# anyplot.ai
# line-timeseries-rolling: Time Series with Rolling Average Overlay
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random
using Statistics
using Dates

Random.seed!(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome") ---
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const BRAND       = colorant"#009E73"  # Imprint palette position 1 — ALWAYS first series

# --- Data: SaaS product daily active users with a 30-day rolling average -------
n_days = 220
window = 30
start_date = Date(2024, 1, 1)
dates = start_date .+ Day.(0:(n_days - 1))
day_of_week = Dates.dayofweek.(dates)

trend = range(52.0, 84.0; length = n_days)
weekend_dip = [dow in (6, 7) ? -6.0 : 0.0 for dow in day_of_week]
noise = randn(n_days) .* 3.5
daily_active_users = collect(trend) .+ weekend_dip .+ noise

rolling_days = window:n_days
rolling_avg = [mean(daily_active_users[(i - window + 1):i]) for i in rolling_days]

tick_positions = collect(1:30:n_days)
if tick_positions[end] != n_days
    push!(tick_positions, n_days)
end
tick_labels = Dates.format.(dates[tick_positions], "u dd")

# --- Plot ------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-timeseries-rolling · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Date",
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
    xticks             = (tick_positions, tick_labels),
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = true,
    ygridvisible       = true,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

lines!(
    ax, 1:n_days, daily_active_users;
    color = (INK_MUTED, 0.55), linewidth = 1.5, label = "Raw Data",
)
lines!(
    ax, rolling_days, rolling_avg;
    color = BRAND, linewidth = 3.5, label = "$(window)-Day Rolling Average",
)

axislegend(
    ax;
    position        = :lt,
    labelcolor      = INK,
    backgroundcolor = ELEVATED_BG,
    framevisible    = false,
)

# --- Save --------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
