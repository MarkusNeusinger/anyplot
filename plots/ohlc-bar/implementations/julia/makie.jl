# anyplot.ai
# ohlc-bar: OHLC Bar Chart
# Library: CairoMakie 0.12 | Julia 1.11
# Quality: pending | Created: 2026-09-02

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

# --- Data: 45 trading sessions of a synthetic tech stock --------------------
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
    open_prices[i] = price
    close_prices[i] = max(price + randn() * 2.2, 5.0)
    high_prices[i] = max(open_prices[i], close_prices[i]) + abs(randn()) * 1.6
    low_prices[i] = min(open_prices[i], close_prices[i]) - abs(randn()) * 1.6
    global price = close_prices[i]
end

bar_up = close_prices .>= open_prices
bar_colors = [up ? UP_COLOR : DOWN_COLOR for up in bar_up]

# --- Plot ---------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "ohlc-bar · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "2024 Trading Sessions",
    ylabel             = "Share Price (USD)",
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

range_points = Point2f[]
open_points = Point2f[]
close_points = Point2f[]
for i in 1:n_days
    x = xs[i]
    push!(range_points, Point2f(x, low_prices[i]), Point2f(x, high_prices[i]))
    push!(open_points, Point2f(x - tick_width, open_prices[i]), Point2f(x, open_prices[i]))
    push!(close_points, Point2f(x, close_prices[i]), Point2f(x + tick_width, close_prices[i]))
end
segment_colors = repeat(bar_colors, inner = 2)

linesegments!(ax, range_points; color = segment_colors, linewidth = 2.5)
linesegments!(ax, open_points; color = segment_colors, linewidth = 2.5)
linesegments!(ax, close_points; color = segment_colors, linewidth = 2.5)

tick_step = 5
tick_positions = collect(1:tick_step:n_days)
ax.xticks = (Float32.(tick_positions), [Dates.format(trading_dates[i], "u dd") for i in tick_positions])
xlims!(ax, 0, n_days + 1)

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
