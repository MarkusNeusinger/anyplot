# anyplot.ai
# line-filled: Filled Line Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 79/100 | Created: 2026-09-05

using CairoMakie
using Colors
using ColorSchemes
using Random

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
const BRAND = IMPRINT_PALETTE[1]

# --- Data ---------------------------------------------------------------
days = 0:119
trend = 40.0 .+ 0.6 .* days
seasonal = 8.0 .* sin.(2π .* days ./ 30)
noise = 5.0 .* randn(length(days))
daily_active_users = max.(trend .+ seasonal .+ noise, 2.0)

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-filled · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Day Since Launch",
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
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    yminorgridvisible  = false,
)

y_top = maximum(daily_active_users) * 1.18

# A vertical gradient (faint near the baseline, richer near the line) reads
# less flat than a single-tone fill. Painted as a heatmap so the shading is
# a single seamless raster rather than many stacked translucent polygons,
# then masked back to the page background above the curve so only the area
# under the line stays tinted. Bin *edges* (not centers) are passed on both
# axes so the heatmap cells land exactly on [first(days), last(days)] with
# no half-cell overhang past the mask.
x_edges = Float64[first(days), last(days)]
y_edges = collect(range(0.0, y_top; length = 201))
gradient_z = reshape([(y_edges[j] + y_edges[j + 1]) / 2 for j in 1:200], 1, 200)
heatmap!(ax, x_edges, y_edges, gradient_z;
    colormap = cgrad([RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.04),
                       RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.40)]),
    colorrange = (0.0, y_top))
band!(ax, days, daily_active_users, fill(y_top, length(days)); color = PAGE_BG)

lines!(ax, days, daily_active_users; color = BRAND, linewidth = 2.0)
ylims!(ax, 0, y_top)

# Callout marking the peak day, giving the chart a storytelling focal point.
peak_idx = argmax(daily_active_users)
peak_day = days[peak_idx]
peak_value = daily_active_users[peak_idx]
scatter!(ax, [peak_day], [peak_value]; color = BRAND, markersize = 14,
    strokewidth = 2, strokecolor = PAGE_BG)
text!(ax, peak_day, peak_value;
    text = "Peak: $(round(Int, peak_value))k DAU",
    align = (:right, :bottom), offset = (-10, 10),
    color = INK, fontsize = 13)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
