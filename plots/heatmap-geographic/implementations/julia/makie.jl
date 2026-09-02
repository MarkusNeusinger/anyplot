# anyplot.ai
# heatmap-geographic: Geographic Heatmap for Spatial Density
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 80/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential colormap — density is single-polarity (never negative)
ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# --- Data: simulated wildfire ignitions across the western US ---------------
# Bounding box for the plotted region
LON_MIN, LON_MAX = -125.0, -103.0
LAT_MIN, LAT_MAX = 31.0, 49.0

# Wildfire-prone regions with an average burn severity (acres) per cluster
cluster_lon      = [-119.5, -121.5, -108.0, -116.0, -112.5]
cluster_lat      = [37.5, 44.0, 39.5, 40.5, 33.0]
cluster_spread   = [1.6, 1.3, 1.7, 1.9, 1.4]
cluster_severity = [320.0, 260.0, 220.0, 190.0, 160.0]
points_per_cluster = 300

longitudes = Float64[]
latitudes = Float64[]
acres_burned = Float64[]
for c in 1:length(cluster_lon)
    append!(longitudes, cluster_lon[c] .+ cluster_spread[c] .* randn(points_per_cluster))
    append!(latitudes, cluster_lat[c] .+ 0.75 * cluster_spread[c] .* randn(points_per_cluster))
    append!(acres_burned, cluster_severity[c] .* exp.(0.6 .* randn(points_per_cluster)))
end
longitudes = clamp.(longitudes, LON_MIN, LON_MAX)
latitudes = clamp.(latitudes, LAT_MIN, LAT_MAX)
n_points = length(longitudes)
weights = acres_burned ./ mean(acres_burned)

# --- Kernel density estimation on a regular lon/lat grid ---------------------
# Silverman's rule of thumb bandwidth, per dimension
bw_lon = std(longitudes) * n_points^(-1 / 6)
bw_lat = std(latitudes) * n_points^(-1 / 6)

grid_n = 100
lon_grid = range(LON_MIN, LON_MAX; length=grid_n)
lat_grid = range(LAT_MIN, LAT_MAX; length=grid_n)
norm_factor = 1.0 / (2 * pi * bw_lon * bw_lat)

density = zeros(grid_n, grid_n)
for i in 1:grid_n
    gx = lon_grid[i]
    for j in 1:grid_n
        gy = lat_grid[j]
        acc = 0.0
        for k in 1:n_points
            dx = (gx - longitudes[k]) / bw_lon
            dy = (gy - latitudes[k]) / bw_lat
            acc += weights[k] * exp(-0.5 * (dx^2 + dy^2))
        end
        density[i, j] = acc * norm_factor
    end
end

# --- Title (fontsize scales down once the descriptive prefix pushes past the
# ~67-char mandated-title baseline) -------------------------------------------
title_str = "Wildfire Ignition Density, Western US · heatmap-geographic · julia · makie · anyplot.ai"
title_ratio = length(title_str) > 67 ? 67 / length(title_str) : 1.0
title_size = round(Int, 20 * title_ratio)

# --- Plot ---------------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = title_size,
    titlecolor        = INK,
    xlabel            = "Longitude (°)",
    ylabel            = "Latitude (°)",
    xlabelsize        = 16,
    ylabelsize        = 16,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 13,
    yticklabelsize    = 13,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    aspect            = DataAspect(),
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridvisible      = false,
)

hm = heatmap!(ax, lon_grid, lat_grid, density; colormap=ANYPLOT_SEQ)

# Raw ignition points, faint, for spatial context under the density layer
scatter!(ax, longitudes, latitudes;
    color       = (PAGE_BG, 0.45),
    markersize  = 3,
    strokewidth = 0,
)

Colorbar(fig[1, 2], hm;
    label          = "Weighted ignition density",
    labelsize      = 15,
    labelcolor     = INK,
    ticklabelsize  = 12,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
)

# --- Save ---------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit=2)
