# anyplot.ai
# indicator-bollinger: Bollinger Bands Indicator Chart
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-02

using CairoMakie
using Colors
using Random
using Statistics
using Dates

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — first series ALWAYS brand green
IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (price line)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue (band envelope)
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# --- Data -----------------------------------------------------------------
# Daily closing prices for a 120-trading-day window, with an engineered
# volatility squeeze followed by a breakout to demonstrate band behavior.
n_days = 120
window = 20

trading_dates = Date[]
current_date = Date(2024, 1, 2)
while length(trading_dates) < n_days
    if Dates.dayofweek(current_date) <= 5
        push!(trading_dates, current_date)
    end
    global current_date += Day(1)
end

calm_returns = randn(45) .* 2.2
squeeze_returns = randn(35) .* 0.6
breakout_returns = randn(n_days - 80) .* 2.8 .+ 0.9
daily_returns = vcat(calm_returns, squeeze_returns, breakout_returns)
close_price = 150.0 .+ cumsum(daily_returns)

trading_day = 1:n_days
band_range = window:n_days
sma = [mean(close_price[(i - window + 1):i]) for i in band_range]
band_std = [std(close_price[(i - window + 1):i]) for i in band_range]
upper_band = sma .+ 2 .* band_std
lower_band = sma .- 2 .* band_std

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "indicator-bollinger · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Date",
    ylabel            = "Price (USD)",
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

tick_positions = 1:15:n_days
ax.xticks = (tick_positions, Dates.format.(trading_dates[tick_positions], "u d"))

band_plot = band!(
    ax, band_range, lower_band, upper_band;
    color = (IMPRINT_PALETTE[3], 0.18),
)
lines!(ax, band_range, upper_band; color = IMPRINT_PALETTE[3], linewidth = 1.5)
lines!(ax, band_range, lower_band; color = IMPRINT_PALETTE[3], linewidth = 1.5)
sma_line = lines!(ax, band_range, sma; color = INK, linestyle = :dash, linewidth = 2)
close_line = lines!(
    ax, trading_day, close_price;
    color = IMPRINT_PALETTE[1], linewidth = 3,
)

Legend(
    fig[1, 2],
    [close_line, sma_line, band_plot],
    ["Close price", "20-day SMA", "Bands (±2σ)"];
    framevisible   = false,
    labelcolor     = INK,
    backgroundcolor = :transparent,
)
colsize!(fig.layout, 1, Relative(0.86))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
