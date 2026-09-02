# anyplot.ai
# voronoi-basic: Voronoi Diagram for Spatial Partitioning
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-02

using CairoMakie
using Random

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential colormap (brand green -> blue) for continuous cell coloring
imprint_seq = cgrad([colorant"#009E73", colorant"#4467A3"])

# Data — retail store locations across a city grid, colored by daily foot traffic
n_stores = 26
store_x = rand(n_stores) .* 12.0
store_y = rand(n_stores) .* 6.5
daily_visits = 300.0 .+ 1400.0 .* rand(n_stores)

# Plot — see default-style-guide.md "Visual Sizing Defaults" for the canvas + sizing values
fig = Figure(resolution = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title             = "voronoi-basic · julia · makie · anyplot.ai",
    titlesize         = 29,
    titlecolor        = INK,
    xlabel            = "X Position (km)",
    ylabel            = "Y Position (km)",
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickformat       = xs -> string.(round.(xs, digits = 1)),
    ytickformat       = ys -> string.(round.(ys, digits = 1)),
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    aspect            = DataAspect(),
)

# Bounding box the Voronoi cells are clipped to, so unbounded edge regions never appear
bbox = Rect2f(Point2f(-0.5, -0.5), Vec2f(13.0, 7.5))

vp = voronoiplot!(
    ax, store_x, store_y, daily_visits;
    colormap    = imprint_seq,
    colorrange  = (minimum(daily_visits), maximum(daily_visits)),
    strokecolor = INK,
    strokewidth = 1.5,
    markercolor = INK,
    markersize  = 17,
    clip        = bbox,
)
xlims!(ax, -0.5, 12.5)
ylims!(ax, -0.5, 7.0)

# Emphasize the busiest store — a focal highlight ring for data storytelling
top_idx = argmax(daily_visits)
scatter!(
    ax, [store_x[top_idx]], [store_y[top_idx]];
    markersize  = 30,
    color       = :transparent,
    strokewidth = 2.5,
    strokecolor = INK,
)

# Style
Colorbar(
    fig[1, 2], vp;
    label         = "Daily Visits",
    labelcolor    = INK,
    ticklabelcolor = INK_SOFT,
    tickcolor     = INK_SOFT,
    width         = 28,
)
colgap!(fig.layout, 1, 15)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
