# anyplot.ai
# dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-05-23

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

const IMPRINT = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#AE3030",
    colorant"#4467A3",
    colorant"#99B314",
    colorant"#954477",
    colorant"#BD8233",
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

valid_idx = findall(!isnan, rsi)
rsi_days  = days[valid_idx]
rsi_vals  = rsi[valid_idx]

# Crosshair at RSI overbought peak — narrative snapshot of when RSI peaked above 70
overbought = filter(i -> !isnan(rsi[i]) && rsi[i] > 70, 1:n)
cx = isempty(overbought) ? valid_idx[argmax(rsi_vals)] : overbought[argmax(rsi[overbought])]
cx_price  = price[cx]
cx_volume = volume[cx]
cx_rsi    = rsi[cx]

# Price / volume bounds for panel label positioning
price_lo, price_hi = extrema(price)
vol_hi = maximum(volume)

# Shared grid color (10% opacity INK)
grid_col = RGBAf(INK.r, INK.g, INK.b, 0.10)

# Zone fill colors — very low alpha so data is not obscured
overbought_fill = RGBAf(IMPRINT[3].r, IMPRINT[3].g, IMPRINT[3].b, 0.10)
oversold_fill   = RGBAf(IMPRINT[1].r, IMPRINT[1].g, IMPRINT[1].b, 0.10)

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
    titlesize          = 19,
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

# Price line — palette position 1
lines!(ax1, days, price; color = IMPRINT[1], linewidth = 2.0)

# Volume bars — palette position 2 (canonical order)
barplot!(ax2, days, volume; color = IMPRINT[2], strokewidth = 0, width = 0.9)

# RSI overbought/oversold zone fills using band! — highlights the threshold regions
band!(ax3, days, fill(70.0, n), fill(100.0, n); color = overbought_fill)
band!(ax3, days, fill(0.0, n), fill(30.0, n);  color = oversold_fill)

# RSI line — palette position 3 (canonical order)
lines!(ax3, rsi_days, rsi_vals; color = IMPRINT[3], linewidth = 2.0)

# RSI overbought / oversold reference lines
hlines!(ax3, [30.0, 70.0];
    color     = RGBAf(INK_MUTED.r, INK_MUTED.g, INK_MUTED.b, 0.5),
    linewidth = 1.0,
    linestyle = :dash,
)

# RSI zone labels — anchored inside the zone, left side
text!(ax3, 5.0, 85.0;
    text = "Overbought", color = INK_MUTED, fontsize = 10, align = (:left, :center))
text!(ax3, 5.0, 15.0;
    text = "Oversold", color = INK_MUTED, fontsize = 10, align = (:left, :center))

# Panel labels in top-left corner of each axis for quick scannability
text!(ax1, 5.0, price_lo + 0.93 * (price_hi - price_lo);
    text = "PRICE", color = INK_SOFT, fontsize = 12, font = :bold, align = (:left, :top))
text!(ax2, 5.0, 0.93 * vol_hi;
    text = "VOLUME", color = INK_SOFT, fontsize = 12, font = :bold, align = (:left, :top))
text!(ax3, 5.0, 95.0;
    text = "RSI", color = INK_SOFT, fontsize = 12, font = :bold, align = (:left, :top))

# Synchronized crosshair at RSI overbought peak — vertical line spans all three panels
cx_line_col = RGBAf(INK.r, INK.g, INK.b, 0.45)
vlines!(ax1, [Float64(cx)]; color = cx_line_col, linewidth = 1.5, linestyle = :dash)
vlines!(ax2, [Float64(cx)]; color = cx_line_col, linewidth = 1.5, linestyle = :dash)
vlines!(ax3, [Float64(cx)]; color = cx_line_col, linewidth = 1.5, linestyle = :dash)

# Value markers at the crosshair position
scatter!(ax1, [Float64(cx)], [cx_price];
    color = IMPRINT[1], markersize = 10,
    strokewidth = 1.5, strokecolor = PAGE_BG)
scatter!(ax2, [Float64(cx)], [cx_volume];
    color = IMPRINT[2], markersize = 10,
    strokewidth = 1.5, strokecolor = PAGE_BG)
scatter!(ax3, [Float64(cx)], [cx_rsi];
    color = IMPRINT[3], markersize = 10,
    strokewidth = 1.5, strokecolor = PAGE_BG)

# Value annotations at crosshair — offset right; for RSI clamp downward when near ceiling
text!(ax1, cx + 4.0, cx_price;
    text = "$(round(cx_price, digits=1))",
    color = INK_SOFT, fontsize = 12, align = (:left, :center))
text!(ax2, cx + 4.0, cx_volume;
    text = "$(round(Int, cx_volume / 1000))K",
    color = INK_SOFT, fontsize = 12, align = (:left, :center))

# RSI annotation: position below dot when near ceiling, label the peak clearly
rsi_ann_y  = cx_rsi > 82.0 ? cx_rsi - 10.0 : cx_rsi + 3.0
rsi_ann_va = cx_rsi > 82.0 ? :top : :bottom
text!(ax3, cx + 4.0, rsi_ann_y;
    text = "$(round(cx_rsi, digits=1)) ← peak",
    color = INK_SOFT, fontsize = 11, align = (:left, rsi_ann_va))

# Row proportions: price panel tallest, volume and RSI smaller
rowsize!(fig.layout, 1, Relative(0.42))
rowsize!(fig.layout, 2, Relative(0.30))
rowsize!(fig.layout, 3, Relative(0.28))
rowgap!(fig.layout, 5)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
