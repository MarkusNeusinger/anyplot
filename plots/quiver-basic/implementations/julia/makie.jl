# anyplot.ai
# quiver-basic: Basic Quiver Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-07-24

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential colormap — magnitude is single-polarity (speed >= 0)
const IMPRINT_SEQ = [colorant"#009E73", colorant"#4467A3"]

# --- Data: cyclonic vortex wind field ---------------------------------------
# Rankine vortex: solid-body rotation inside the eyewall (speed rises with r),
# then decays with 1/r outside it — mirrors a real cyclone's wind profile and
# gives the magnitude colormap a full, meaningful range across the domain.
nx, ny = 20, 12
xs = range(-8.0, 8.0; length = nx)
ys = range(-4.5, 4.5; length = ny)

x = vec([xi for xi in xs, yi in ys])
y = vec([yi for xi in xs, yi in ys])

r = sqrt.(x .^ 2 .+ y .^ 2)
theta = atan.(y, x)
core_radius = 3.0
v_max = 1.5
speed = ifelse.(r .<= core_radius, v_max .* r ./ core_radius, v_max .* core_radius ./ max.(r, 1e-6))
u = -speed .* sin.(theta)
v = speed .* cos.(theta)

# --- Plot ---------------------------------------------------------------
fig = Figure(resolution = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title = "quiver-basic · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    xlabel = "X position (km)",
    ylabel = "Y position (km)",
    xlabelsize = 14,
    ylabelsize = 14,
    xlabelcolor = INK,
    ylabelcolor = INK,
    xticklabelsize = 12,
    yticklabelsize = 12,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xtickcolor = INK_SOFT,
    ytickcolor = INK_SOFT,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinecolor = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    xgridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible = false,
    yminorgridvisible = false,
    aspect = DataAspect(),
)

arrow_plot = arrows!(
    ax,
    x,
    y,
    u,
    v;
    arrowsize = 14,
    lengthscale = 0.55,
    linewidth = 2.5,
    color = speed,
    colormap = IMPRINT_SEQ,
)

Colorbar(
    fig[1, 2],
    arrow_plot;
    label = "Wind speed (m/s)",
    labelcolor = INK,
    labelsize = 14,
    ticklabelsize = 12,
    ticklabelcolor = INK_SOFT,
    tickcolor = INK_SOFT,
)

xlims!(ax, -9, 9)
ylims!(ax, -5.5, 5.5)

colsize!(fig.layout, 1, Relative(0.88))

# --- Save --------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
