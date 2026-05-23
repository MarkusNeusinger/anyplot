# anyplot.ai
# dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-05-23

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const ANYPLOT_PALETTE = [
    colorant"#009E73",
    colorant"#9418DB",
    colorant"#B71D27",
    colorant"#16B8F3",
    colorant"#99B314",
    colorant"#D359A7",
    colorant"#BA843E",
]

# Data: 200 simulated trading days (stock price, volume, RSI)
n = 200
days = Float64.(1:n)

log_returns = 0.0008 .+ 0.012 .* randn(n)
price = 100.0 .* cumprod(1.0 .+ log_returns)

volume = 800_000.0 .+ 400_000.0 .* abs.(randn(n))

# RSI (14-period) computed inline
period = 14
delta = diff(price)
gains_raw = max.(delta, 0.0)
losses_raw = abs.(min.(delta, 0.0))
avg_gain = zeros(n)
avg_loss = zeros(n)
for i in 1:(n - 1)
    s = max(1, i - period + 1)
    avg_gain[i + 1] = mean(gains_raw[s:i])
    avg_loss[i + 1] = mean(losses_raw[s:i])
end
rsi = 100.0 .- 100.0 ./ (1.0 .+ avg_gain ./ (avg_loss .+ 1e-10))
rsi[1:period] .= NaN

# Crosshair anchored at day 120 (static demonstration of the crosshair layout)
cx = 120
cx_price  = price[cx]
cx_volume = volume[cx]
cx_rsi    = rsi[cx]

valid_idx = findall(!isnan, rsi)
rsi_days  = days[valid_idx]
rsi_vals  = rsi[valid_idx]

# Shared grid color (10% opacity INK)
grid_col = RGBAf(INK.r, INK.g, INK.b, 0.10)

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

# Axis 1: Price
ax1 = Axis(
    fig[1, 1];
    title              = "dashboard-synchronized-crosshair · julia · makie · anyplot.ai",
    titlesize          = 16,
    titlecolor         = INK,
    ylabel             = "Price (USD)",
    ylabelsize         = 13,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = grid_col,
    ygridwidth         = 1.0,
)
hidexdecorations!(ax1; ticklabels = true, ticks = false, label = false,
    grid = false, minorgrid = false, minorticks = false)

# Axis 2: Volume
ax2 = Axis(
    fig[2, 1];
    ylabel             = "Volume",
    ylabelsize         = 13,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = grid_col,
    ygridwidth         = 1.0,
    ytickformat        = vs -> ["$(round(Int, v / 1000))K" for v in vs],
)
hidexdecorations!(ax2; ticklabels = true, ticks = false, label = false,
    grid = false, minorgrid = false, minorticks = false)

# Axis 3: RSI
ax3 = Axis(
    fig[3, 1];
    xlabel             = "Trading Day",
    ylabel             = "RSI (14)",
    xlabelsize         = 13,
    ylabelsize         = 13,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = grid_col,
    ygridwidth         = 1.0,
    yticks             = [30, 50, 70],
    limits             = (nothing, (0.0, 100.0)),
)

linkxaxes!(ax1, ax2, ax3)

# Price line
lines!(ax1, days, price; color = ANYPLOT_PALETTE[1], linewidth = 2.0)

# Volume bars
barplot!(ax2, days, volume; color = ANYPLOT_PALETTE[4], strokewidth = 0, width = 0.9)

# RSI line
lines!(ax3, rsi_days, rsi_vals; color = ANYPLOT_PALETTE[2], linewidth = 2.0)

# RSI overbought / oversold reference lines
hlines!(ax3, [30.0, 70.0];
    color     = RGBAf(INK_MUTED.r, INK_MUTED.g, INK_MUTED.b, 0.5),
    linewidth = 1.0,
    linestyle = :dash,
)

# Synchronized crosshair at day 120 — vertical line spans all three panels
cx_line_col = RGBAf(INK.r, INK.g, INK.b, 0.45)
vlines!(ax1, [Float64(cx)]; color = cx_line_col, linewidth = 1.5, linestyle = :dash)
vlines!(ax2, [Float64(cx)]; color = cx_line_col, linewidth = 1.5, linestyle = :dash)
vlines!(ax3, [Float64(cx)]; color = cx_line_col, linewidth = 1.5, linestyle = :dash)

# Value markers at the crosshair position
scatter!(ax1, [Float64(cx)], [cx_price];
    color = ANYPLOT_PALETTE[1], markersize = 10,
    strokewidth = 1.5, strokecolor = PAGE_BG)
scatter!(ax2, [Float64(cx)], [cx_volume];
    color = ANYPLOT_PALETTE[4], markersize = 10,
    strokewidth = 1.5, strokecolor = PAGE_BG)
scatter!(ax3, [Float64(cx)], [cx_rsi];
    color = ANYPLOT_PALETTE[2], markersize = 10,
    strokewidth = 1.5, strokecolor = PAGE_BG)

# Value annotations at the crosshair
text!(ax1, cx + 4.0, cx_price;
    text = "$(round(cx_price, digits=1))",
    color = INK_SOFT, fontsize = 12, align = (:left, :center))
text!(ax2, cx + 4.0, cx_volume;
    text = "$(round(Int, cx_volume / 1000))K",
    color = INK_SOFT, fontsize = 12, align = (:left, :center))
text!(ax3, cx + 4.0, cx_rsi;
    text = "$(round(cx_rsi, digits=1))",
    color = INK_SOFT, fontsize = 12, align = (:left, :center))

# Row proportions: price panel tallest, volume and RSI smaller
rowsize!(fig.layout, 1, Relative(0.42))
rowsize!(fig.layout, 2, Relative(0.30))
rowsize!(fig.layout, 3, Relative(0.28))
rowgap!(fig.layout, 5)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
