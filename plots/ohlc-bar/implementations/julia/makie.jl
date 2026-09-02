# anyplot.ai
# ohlc-bar: OHLC Bar Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Dates
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const UP_COLOR    = colorant"#009E73"  # Imprint position 1 — bullish (close >= open)
const DOWN_COLOR  = colorant"#AE3030"  # Imprint semantic anchor — bearish (close < open)

# --- Data: 45 trading sessions of a fictional robotics stock (SLRA) ---------
start_date = Date(2024, 3, 1)
calendar_days = start_date:Day(1):(start_date + Day(90))
trading_dates = filter(d -> dayofweek(d) <= 5, collect(calendar_days))[1:45]

n_days = length(trading_dates)
open_prices = zeros(n_days)
high_prices = zeros(n_days)
low_prices = zeros(n_days)
close_prices = zeros(n_days)

price = 185.0
for i in 1:n_days
    # Sessions 20-27 simulate an earnings-reaction stretch with wider ranges
    vol_mult = (20 <= i <= 27) ? 2.6 : 1.0
    open_prices[i] = price
    close_prices[i] = max(price + randn() * 2.2 * vol_mult, 5.0)
    high_prices[i] = max(open_prices[i], close_prices[i]) + abs(randn()) * 1.6 * vol_mult
    low_prices[i] = min(open_prices[i], close_prices[i]) - abs(randn()) * 1.6 * vol_mult
    global price = close_prices[i]
end

bar_up = close_prices .>= open_prices
bar_colors = [up ? UP_COLOR : DOWN_COLOR for up in bar_up]

peak_idx = argmax(high_prices)
trough_idx = argmin(low_prices)

# --- Plot ---------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "ohlc-bar · julia · makie · anyplot.ai",
    titlesize          = 25,
    titlecolor         = INK,
    xlabel             = "2024 Trading Sessions",
    ylabel             = "SLRA Share Price (USD)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 11,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelrotation = pi / 6,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

tick_width = 0.32
xs = Float32.(1:n_days)

open_points = Point2f[]
close_points = Point2f[]
for i in 1:n_days
    x = xs[i]
    push!(open_points, Point2f(x - tick_width, open_prices[i]), Point2f(x, open_prices[i]))
    push!(close_points, Point2f(x, close_prices[i]), Point2f(x + tick_width, close_prices[i]))
end
tick_colors = repeat(bar_colors, inner = 2)

rangebars!(ax, xs, low_prices, high_prices; color = bar_colors, linewidth = 2.5)
linesegments!(ax, open_points; color = tick_colors, linewidth = 2.5)
linesegments!(ax, close_points; color = tick_colors, linewidth = 2.5)

text!(
    ax, xs[peak_idx], high_prices[peak_idx];
    text = "Swing high", align = (:center, :bottom), offset = (0, 6),
    fontsize = 11, color = INK_SOFT,
)
text!(
    ax, xs[trough_idx], low_prices[trough_idx];
    text = "Swing low", align = (:center, :top), offset = (0, -6),
    fontsize = 11, color = INK_SOFT,
)

tick_step = 5
tick_positions = collect(1:tick_step:n_days)
ax.xticks = (Float32.(tick_positions), [Dates.format(trading_dates[i], "u dd") for i in tick_positions])
xlims!(ax, 0, n_days + 1)
ylims!(ax, minimum(low_prices) - 6, maximum(high_prices) + 6)

legend_elements = [
    LineElement(color = UP_COLOR, linewidth = 2.5),
    LineElement(color = DOWN_COLOR, linewidth = 2.5),
]
axislegend(
    ax, legend_elements, ["Up (close ≥ open)", "Down (close < open)"];
    position = :lt, framevisible = false, labelcolor = INK_SOFT, labelsize = 12,
)

# --- Save ---------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
