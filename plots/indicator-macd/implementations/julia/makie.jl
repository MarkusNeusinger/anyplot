# anyplot.ai
# indicator-macd: MACD Technical Indicator Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette — MACD line uses blue so it never blends into the green
# gain bars; histogram keeps the sanctioned green/red finance semantic.
const MACD_COLOR   = colorant"#4467A3"  # Imprint position 3 — blue
const SIGNAL_COLOR = colorant"#C475FD"  # Imprint position 2 — lavender
const GAIN_COLOR   = colorant"#009E73"  # semantic: bullish histogram bars (finance profit/up → green)
const LOSS_COLOR   = colorant"#AE3030"  # semantic: bearish histogram bars (finance loss/down → red)

# Data: simulate 120 trading days of closing prices, derive MACD/signal/histogram
n_days = 120
daily_returns = randn(n_days) .* 1.2
trend = 8 .* sin.(range(0, 4π, length = n_days))
closing_prices = 150 .+ cumsum(daily_returns) .+ trend

function ema(values, span)
    alpha = 2 / (span + 1)
    smoothed = similar(values, Float64)
    smoothed[1] = values[1]
    for i in 2:length(values)
        smoothed[i] = alpha * values[i] + (1 - alpha) * smoothed[i - 1]
    end
    return smoothed
end

ema_fast = ema(closing_prices, 12)
ema_slow = ema(closing_prices, 26)
macd_line = ema_fast .- ema_slow
signal_line = ema(macd_line, 9)
macd_histogram = macd_line .- signal_line

trading_day = 1:n_days
bar_colors = [value >= 0 ? GAIN_COLOR : LOSS_COLOR for value in macd_histogram]

# Crossover points (MACD line crosses the signal line) reinforce the
# buy/sell-signal narrative called out in the spec's Applications section.
crossover_idx = [i for i in 2:n_days if sign(macd_histogram[i - 1]) != sign(macd_histogram[i])]
crossover_x = trading_day[crossover_idx]
crossover_y = macd_line[crossover_idx]
crossover_bullish = [macd_histogram[i] >= 0 for i in crossover_idx]
crossover_colors = [bullish ? GAIN_COLOR : LOSS_COLOR for bullish in crossover_bullish]
crossover_markers = [bullish ? :utriangle : :dtriangle for bullish in crossover_bullish]

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "indicator-macd · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Trading Day",
    ylabel            = "MACD Value",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

barplot!(ax, trading_day, macd_histogram; color = bar_colors, width = 0.8, strokewidth = 0)
hlines!(ax, [0]; color = INK_SOFT, linewidth = 1.5, linestyle = :dash)
lines!(ax, trading_day, macd_line; color = MACD_COLOR, linewidth = 3, label = "MACD (12, 26)")
lines!(ax, trading_day, signal_line; color = SIGNAL_COLOR, linewidth = 3, label = "Signal (9)")
scatter!(
    ax, crossover_x, crossover_y;
    color = crossover_colors, marker = crossover_markers,
    markersize = 16, strokewidth = 1.5, strokecolor = PAGE_BG,
)

axislegend(ax; position = :lt, framevisible = false, labelcolor = INK, labelsize = 12)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
