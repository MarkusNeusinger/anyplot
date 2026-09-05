# anyplot.ai
# indicator-rsi: RSI Technical Indicator Chart
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-05

using CairoMakie
using Colors
using Dates
using Random
using Statistics

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint palette — first series always brand green
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const RSI_COLOR        = IMPRINT_PALETTE[1]  # brand green
const OVERBOUGHT_COLOR = IMPRINT_PALETTE[5]  # matte red — semantic: reversal risk
const OVERSOLD_COLOR   = IMPRINT_PALETTE[3]  # blue — semantic: cool / opportunity

# Data — simulated daily closing prices over trading days (weekends skipped)
n_days = 141
start_date = Date(2024, 3, 1)
all_days = collect(start_date:Day(1):(start_date + Day(260)))
trading_days = filter(d -> dayofweek(d) <= 5, all_days)[1:n_days]

# Three drift regimes (rally, selloff, choppy recovery) so RSI visibly
# crosses both the overbought and oversold thresholds, not just the middle band.
prices = Vector{Float64}(undef, n_days)
prices[1] = 148.0
for i in 2:n_days
    drift = i <= 40 ? 0.55 : (i <= 75 ? -0.60 : 0.05)
    sigma = i <= 40 ? 0.9 : (i <= 75 ? 1.0 : 1.4)
    prices[i] = prices[i - 1] + randn() * sigma + drift
end

changes = diff(prices)
period = 14
gains = max.(changes, 0.0)
losses = max.(-changes, 0.0)

# Wilder's smoothing for the 14-period RSI
avg_gain = zeros(length(gains))
avg_loss = zeros(length(gains))
avg_gain[period] = mean(gains[1:period])
avg_loss[period] = mean(losses[1:period])
for i in (period + 1):length(gains)
    avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
    avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period
end
rs = avg_gain ./ avg_loss
rsi_full = 100.0 .- 100.0 ./ (1.0 .+ rs)
rsi_values = rsi_full[(period + 1):end]
rsi_dates = trading_days[(period + 2):end]
x = 1:length(rsi_values)

# Plot
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "indicator-rsi · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Trading Date",
    ylabel            = "RSI (14-period)",
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
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xgridvisible      = false,
    xticks            = (x[1:20:end], Dates.format.(rsi_dates[1:20:end], "u d")),
    xticklabelrotation = pi / 6,
)

ylims!(ax, 0, 100)

# Overbought / oversold reference zones
hspan!(ax, 70, 100; color = RGBAf(OVERBOUGHT_COLOR.r, OVERBOUGHT_COLOR.g, OVERBOUGHT_COLOR.b, 0.12))
hspan!(ax, 0, 30; color = RGBAf(OVERSOLD_COLOR.r, OVERSOLD_COLOR.g, OVERSOLD_COLOR.b, 0.12))

# Threshold and centerline references
hlines!(ax, [70, 30]; color = INK_SOFT, linestyle = :dash, linewidth = 1.5)
hlines!(ax, [50]; color = INK_MUTED, linestyle = :dot, linewidth = 1.2)

lines!(ax, x, rsi_values; color = RSI_COLOR, linewidth = 3)

text!(ax, x[1], 96; text = "Overbought", color = INK_SOFT, fontsize = 12, align = (:left, :top))
text!(ax, x[1], 4; text = "Oversold", color = INK_SOFT, fontsize = 12, align = (:left, :bottom))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
