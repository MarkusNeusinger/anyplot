# anyplot.ai
# streamline-basic: Basic Streamline Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-09

using CairoMakie
using LinearAlgebra

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# --- Data: wind spiraling into a low-pressure system (Rankine vortex core --
# with a mild radial inflow), the classic cyclone pattern in synoptic charts.
function wind_velocity(x, y)
    r = sqrt(x^2 + y^2) + 1.0e-6
    core_radius = 20.0
    omega = 0.6
    tangential = r <= core_radius ? omega * r : omega * core_radius^2 / r
    inflow = -0.05 * r
    theta = atan(y, x)
    u = -tangential * sin(theta) + inflow * cos(theta)
    v = tangential * cos(theta) + inflow * sin(theta)
    return Point2f(u, v)
end

imprint_seq = cgrad([colorant"#009E73", colorant"#4467A3"])

# --- Plot ---------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "streamline-basic · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Distance East of Center (km)",
    ylabel            = "Distance North of Center (km)",
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
    xgridvisible      = false,
    ygridvisible      = false,
    aspect            = DataAspect(),
)

streamlines = streamplot!(
    ax, wind_velocity, -60.0 .. 60.0, -60.0 .. 60.0;
    color = p -> norm(p),
    colormap = imprint_seq,
    gridsize = (32, 32),
    arrow_size = 14,
    linewidth = 2.5,
)

Colorbar(
    fig[1, 2], streamlines;
    label = "Wind Speed (m/s)",
    labelsize = 14,
    labelcolor = INK,
    ticklabelsize = 12,
    ticklabelcolor = INK_SOFT,
    tickcolor = INK_SOFT,
)

colsize!(fig.layout, 1, Relative(0.88))

# --- Save ----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
