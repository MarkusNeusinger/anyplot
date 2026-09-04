# anyplot.ai
# bar-3d-categorical: 3D Bar Chart for Categorical Comparison
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 80/100 | Created: 2026-09-04

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint continuous colormap — single-polarity (revenue magnitude has no natural midpoint)
IMPRINT_SEQ = [colorant"#009E73", colorant"#4467A3"]

# Data — quarterly revenue by product category and sales region
product_categories = ["Electronics", "Apparel", "Home & Garden", "Sports", "Books"]
regions = ["North", "South", "East", "West"]
n_products = length(product_categories)
n_regions = length(regions)

base_revenue = [82.0, 61.0, 48.0, 55.0, 39.0]
region_factor = [1.15, 0.85, 1.00, 0.95]

revenue = Array{Float64}(undef, n_products, n_regions)
for i in 1:n_products, j in 1:n_regions
    revenue[i, j] = base_revenue[i] * region_factor[j] + randn() * 4
end

# Plot — see default-style-guide.md "Visual Sizing Defaults" for the canvas + sizing values
fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis3(
    fig[1, 1];
    title = "bar-3d-categorical · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    xlabel = "Product Category",
    ylabel = "Region",
    zlabel = "Revenue (\$k)",
    xlabelsize = 14,
    ylabelsize = 14,
    zlabelsize = 14,
    xlabelcolor = INK,
    ylabelcolor = INK,
    zlabelcolor = INK,
    xticklabelsize = 12,
    yticklabelsize = 12,
    zticklabelsize = 12,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    zticklabelcolor = INK_SOFT,
    xticks = (1:n_products, product_categories),
    yticks = (1:n_regions, regions),
    azimuth = deg2rad(225),   # spec calls for ~45°; 225° keeps the tallest bars in front, unoccluded
    elevation = deg2rad(30),
    backgroundcolor = PAGE_BG,
    xypanelcolor = PAGE_BG,
    xzpanelcolor = PAGE_BG,
    yzpanelcolor = PAGE_BG,
    xgridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    zgridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xspinecolor_1 = INK_SOFT, xspinecolor_2 = INK_SOFT, xspinecolor_3 = INK_SOFT,
    yspinecolor_1 = INK_SOFT, yspinecolor_2 = INK_SOFT, yspinecolor_3 = INK_SOFT,
    zspinecolor_1 = INK_SOFT, zspinecolor_2 = INK_SOFT, zspinecolor_3 = INK_SOFT,
    protrusions = 70,
)

# Bar bases sit on a unit grid; markersize < 1 in x/y leaves a gap between neighbors for depth cues
bar_gap = 0.2
bar_positions = Point3f[]
bar_sizes = Vec3f[]
bar_values = Float64[]
for i in 1:n_products, j in 1:n_regions
    push!(bar_positions, Point3f(i - (1 - bar_gap) / 2, j - (1 - bar_gap) / 2, 0))
    push!(bar_sizes, Vec3f(1 - bar_gap, 1 - bar_gap, revenue[i, j]))
    push!(bar_values, revenue[i, j])
end

meshscatter!(
    ax, bar_positions;
    marker = Rect3(Point3f(0, 0, 0), Vec3f(1, 1, 1)),
    markersize = bar_sizes,
    color = bar_values,
    colormap = IMPRINT_SEQ,
    colorrange = extrema(bar_values),
    # Directional lighting on adjacent instanced Rect3 faces causes a
    # visible z-fight crease on tall bars near the axis corner; flat
    # per-value color reads more accurately against the Colorbar anyway.
    shading = NoShading,
)

Colorbar(
    fig[1, 2];
    limits = extrema(bar_values),
    colormap = IMPRINT_SEQ,
    label = "Revenue (\$k)",
    labelcolor = INK,
    ticklabelcolor = INK_SOFT,
    tickcolor = INK_SOFT,
)
colsize!(fig.layout, 1, Relative(0.85))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
