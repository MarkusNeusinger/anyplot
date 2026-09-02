# anyplot.ai
# indicator-sma: Simple Moving Average (SMA) Indicator Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-02

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
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------
n = 300
daily_returns = 0.0004 .+ 0.013 .* randn(n)
close = 180.0 .* cumprod(1.0 .+ daily_returns)
trading_day = 1:n

window_short  = 20
window_medium = 50
window_long   = 200

sma_short  = [i < window_short ? NaN : mean(close[(i - window_short + 1):i]) for i in 1:n]
sma_medium = [i < window_medium ? NaN : mean(close[(i - window_medium + 1):i]) for i in 1:n]
sma_long   = [i < window_long ? NaN : mean(close[(i - window_long + 1):i]) for i in 1:n]

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "indicator-sma · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Trading Day",
    ylabel             = "Closing Price (\$)",
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
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xgridvisible       = false,
)

lines!(ax, trading_day, close; color = IMPRINT_PALETTE[1], linewidth = 2.0, label = "Close")
lines!(ax, trading_day, sma_short; color = IMPRINT_PALETTE[2], linewidth = 2.0, label = "SMA 20")
lines!(ax, trading_day, sma_medium; color = IMPRINT_PALETTE[3], linewidth = 2.0, label = "SMA 50")
lines!(ax, trading_day, sma_long; color = IMPRINT_PALETTE[4], linewidth = 2.5, label = "SMA 200")

axislegend(ax; position = :lt, labelcolor = INK, framevisible = false, labelsize = 13)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
