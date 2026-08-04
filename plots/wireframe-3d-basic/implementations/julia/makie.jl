# anyplot.ai
# wireframe-3d-basic: Basic 3D Wireframe Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 77/100 | Created: 2026-08-04

using CairoMakie
using Colors

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND    = colorant"#009E73"  # Imprint palette position 1 — ALWAYS first series

# --- Data ---------------------------------------------------------------
# Ripple function z = sin(r) / (r + 1) evaluated on a 24x24 grid
grid_points = range(-10, 10; length = 24)
x = collect(grid_points)
y = collect(grid_points)
radius = [sqrt(xi^2 + yi^2) for xi in x, yi in y]
z = sin.(radius) ./ (radius .+ 1)

# --- Plot -----------------------------------------------------------------
title_text = "wireframe-3d-basic · julia · makie · anyplot.ai"
title_fontsize = round(Int, 20 * min(1.0, 67 / length(title_text)))

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis3(
    fig[1, 1];
    title             = title_text,
    titlesize         = title_fontsize,
    titlecolor        = INK,
    xlabel            = "X",
    ylabel            = "Y",
    zlabel            = "Z",
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    zlabelcolor       = INK,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    zticklabelcolor   = INK_SOFT,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    zgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xspinecolor_1     = INK_SOFT,
    yspinecolor_1     = INK_SOFT,
    zspinecolor_1     = INK_SOFT,
    xspinecolor_2     = INK_SOFT,
    yspinecolor_2     = INK_SOFT,
    zspinecolor_2     = INK_SOFT,
    xspinecolor_3     = INK_SOFT,
    yspinecolor_3     = INK_SOFT,
    zspinecolor_3     = INK_SOFT,
    xypanelcolor      = PAGE_BG,
    xzpanelcolor      = PAGE_BG,
    yzpanelcolor      = PAGE_BG,
    azimuth           = deg2rad(45 + 90),
    elevation         = deg2rad(30),
    aspect            = (1, 1, 0.6),
)

wireframe!(ax, x, y, z; color = BRAND, linewidth = 1.3)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
