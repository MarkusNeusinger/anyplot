# anyplot.ai
# drawdown-basic: Drawdown Chart
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-05-23

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
# Drawdown = loss → semantic red (anyplot palette position 3)
const DRAW_RED = colorant"#B71D27"

# Data: simulate 756 trading days (~3 years) of a diversified portfolio NAV
# Phase structure ensures a realistic peak-trough-recovery scenario
n_days = 756
phase_returns = vcat(
    0.0008 .+ 0.012 .* randn(175),   # bull market: strong growth
    -0.003 .+ 0.018 .* randn(95),    # correction: ~-25% drawdown
    0.0010 .+ 0.013 .* randn(215),   # recovery: partial bounce-back
    0.0006 .+ 0.011 .* randn(271),   # consolidation: steady drift
)
nav = 100.0 .* cumprod(1.0 .+ phase_returns)

# Drawdown: percentage decline from running all-time high
running_peak = accumulate(max, nav)
drawdown = (nav .- running_peak) ./ running_peak .* 100.0

max_dd_idx = argmin(drawdown)
max_dd_val = drawdown[max_dd_idx]

days = collect(1:n_days)

# Figure
fig = Figure(
    resolution = (1600, 900),
    fontsize = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title = "drawdown-basic · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    xlabel = "Trading Day",
    ylabel = "Drawdown (%)",
    xlabelsize = 14,
    ylabelsize = 14,
    xticklabelsize = 12,
    yticklabelsize = 12,
    xlabelcolor = INK,
    ylabelcolor = INK,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xtickcolor = INK_SOFT,
    ytickcolor = INK_SOFT,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinecolor = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    xticks = ([1, 252, 504, 756], ["Start", "Year 1", "Year 2", "Year 3"]),
    xgridvisible = false,
    ygridcolor = RGBAf(INK.r, INK.g, INK.b, 0.10),
    yminorgridvisible = false,
    xminorgridvisible = false,
)

# Filled drawdown area — slightly more opaque on dark theme for visibility
fill_alpha = THEME == "light" ? 0.28 : 0.48
band!(ax, days, drawdown, zeros(n_days); color = (DRAW_RED, fill_alpha))

# Drawdown line
lines!(ax, days, drawdown; color = DRAW_RED, linewidth = 2.2)

# Zero baseline reference
hlines!(ax, [0.0]; color = INK_SOFT, linewidth = 1.0)

# Max drawdown marker — hollow circle for visibility on both themes
scatter!(ax, [Float64(max_dd_idx)], [max_dd_val];
    color = PAGE_BG, markersize = 16,
    strokewidth = 2.5, strokecolor = DRAW_RED)

# Annotation: max drawdown value at mid-depth to the right of the trough
ann_x = min(Float64(max_dd_idx) + 25, Float64(n_days) - 120)
ann_y = max_dd_val * 0.55
text!(ax, ann_x, ann_y;
    text = "Max DD: $(round(max_dd_val, digits=1))%",
    align = (:left, :center),
    color = INK,
    fontsize = 14,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
