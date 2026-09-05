# anyplot.ai
# scatter-color-mapped: Color-Mapped Scatter Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# --- Data ---------------------------------------------------------------
n = 250
easting = rand(n) .* 120                                             # meters east of survey origin
northing = rand(n) .* 80                                              # meters north of survey origin
trend(e, no) = 40.0 + 25.0 * (e / 120) + 10.0 * sin(no / 12)          # deterministic spatial gradient
concentration = trend.(easting, northing) .+ 15.0 .* randn(n)
concentration = clamp.(concentration, 5.0, 100.0)
color_range = (5.0, 100.0)

# Smooth backdrop of the underlying spatial trend (noise-free) so the
# eastward concentration gradient reads at a glance, not only via the colorbar.
trend_xs = range(0.0, 120.0; length = 60)
trend_ys = range(0.0, 80.0; length = 40)
trend_zs = [trend(e, no) for e in trend_xs, no in trend_ys]

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "scatter-color-mapped · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Easting (m)",
    ylabel            = "Northing (m)",
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
)

heatmap!(
    ax, trend_xs, trend_ys, trend_zs;
    colormap   = IMPRINT_SEQ,
    colorrange = extrema(trend_zs),
    alpha      = 0.18,
)

sc = scatter!(
    ax, easting, northing;
    color       = concentration,
    colormap    = IMPRINT_SEQ,
    colorrange  = color_range,
    markersize  = 16,
    alpha       = 0.85,
    strokewidth = 0.75,
    strokecolor = PAGE_BG,
)

Colorbar(
    fig[1, 2], sc;
    label          = "Mineral Concentration (ppm)",
    labelsize      = 14,
    labelcolor     = INK,
    ticklabelsize  = 12,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
