# anyplot.ai
# hexbin-map-geographic: Hexagonal Binning Map
# Library: makie 0.24.16 | Julia 1.13.4
# Quality: 82/100 | Updated: 2026-11-26

using CairoMakie
using Colors
using DataFrames
using Random

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const GRID_COLOR  = THEME == "light" ?
    RGBAf(26/255f0, 26/255f0, 23/255f0, 0.12f0) :
    RGBAf(240/255f0, 239/255f0, 232/255f0, 0.12f0)

# Water fill and coastline colors for the geographic base map
const WATER_FILL  = THEME == "light" ?
    RGBAf(0.58f0, 0.75f0, 0.88f0, 0.60f0) :
    RGBAf(0.18f0, 0.35f0, 0.56f0, 0.70f0)
const COAST_LINE  = THEME == "light" ?
    RGBAf(0.20f0, 0.38f0, 0.55f0, 0.95f0) :
    RGBAf(0.50f0, 0.70f0, 0.88f0, 0.90f0)

# Imprint sequential ramp for density (fields: colored cells fill the map)
const ANYPLOT_SEQ_FIELDS = THEME == "light" ?
    cgrad([colorant"#66E2B2", colorant"#009E73", colorant"#024582", colorant"#351E45"], [0.0, 0.369, 0.803, 1.0]) :
    cgrad([colorant"#404C02", colorant"#009E73", colorant"#CDD9FF"], [0.0, 0.487, 1.0])

# Columns
const LON = "Longitude"  # role: x
const LAT = "Latitude"   # role: y

# Map extent
const LON_LO, LON_HI = -122.515, -122.360
const LAT_LO, LAT_HI =   37.700,   37.835

# Simplified coastlines (Makie auto-closes last -> first).
# SF Bay water: the eastern SF waterfront (south -> north), then the box corners.
bay_pts = Point2f[
    (-122.374, 37.700), (-122.376, 37.748), (-122.381, 37.762),
    (-122.386, 37.776), (-122.393, 37.790), (-122.400, 37.800),
    (-122.407, 37.805), (-122.414, 37.808), (-122.432, 37.804),
    (-122.443, 37.803), (-122.455, 37.803), (-122.464, 37.804),
    (-122.479, 37.808),                       # Golden Gate Bridge, SF side
    (-122.479, LAT_HI), (LON_HI, LAT_HI), (LON_HI, LAT_LO),
]

# Pacific Ocean: the western SF coast (north -> south), then the box corners.
pac_pts = Point2f[
    (-122.479, 37.808),                       # Golden Gate Bridge, SF side
    (-122.484, 37.800), (-122.493, 37.798),
    (-122.499, 37.794), (-122.505, 37.789),
    (-122.509, 37.782), (-122.511, 37.770),
    (-122.512, 37.748), (-122.511, 37.710),
    (LON_LO, LAT_LO), (LON_LO, LAT_HI),
    (-122.479, LAT_HI),
]

# Ray-casting point-in-polygon test, used to keep ride starts on land
function in_polygon(x, y, poly)
    inside = false
    j = length(poly)
    for i in eachindex(poly)
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi
            inside = !inside
        end
        j = i
    end
    return inside
end

# Data: synthetic bike-share ride starts in San Francisco, land only
Random.seed!(42)
cluster_centers = [
    (-122.4090, 37.7830),  # Union Square / Downtown
    (-122.4194, 37.7599),  # Mission District
    (-122.4030, 37.7700),  # SoMa
    (-122.4352, 37.7940),  # Marina
    (-122.4447, 37.7698),  # Haight-Ashbury
]
cluster_weights = [0.33, 0.22, 0.20, 0.13, 0.12]
cluster_stds    = [0.011, 0.012, 0.009, 0.008, 0.013]

n_total = 14000
lons = Float64[]
lats = Float64[]
for ((cx, cy), w, σ) in zip(cluster_centers, cluster_weights, cluster_stds)
    n_i = round(Int, n_total * w)
    append!(lons, cx .+ σ .* randn(n_i))
    append!(lats, cy .+ σ .* randn(n_i))
end

on_land = [
    LON_LO <= x <= LON_HI && LAT_LO <= y <= LAT_HI &&
    !in_polygon(x, y, bay_pts) && !in_polygon(x, y, pac_pts)
    for (x, y) in zip(lons, lats)
]
df = DataFrame(LON => lons[on_land], LAT => lats[on_land])

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "SF Bike-Share · hexbin-map-geographic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = LON,
    ylabel             = LAT,
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
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
    xgridcolor         = GRID_COLOR,
    ygridcolor         = GRID_COLOR,
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

# Base map: water bodies drawn before the hexbins so the shoreline shows through
poly!(ax, bay_pts; color = WATER_FILL, strokecolor = COAST_LINE, strokewidth = 1.2)
poly!(ax, pac_pts; color = WATER_FILL, strokecolor = COAST_LINE, strokewidth = 1.2)

# Hexagonal density map overlaid on the base map
hb = hexbin!(ax, df[!, LON], df[!, LAT];
    cellsize    = 0.009,
    colormap    = ANYPLOT_SEQ_FIELDS,
    alpha       = 0.82,
    threshold   = 1,
    strokecolor = PAGE_BG,
    strokewidth = 0.5,
)

Colorbar(fig[1, 2], hb;
    label           = "Ride Count",
    labelsize       = 13,
    labelcolor      = INK,
    ticklabelsize   = 11,
    ticklabelcolor  = INK_SOFT,
    tickcolor       = INK_SOFT,
    width           = 18,
)

limits!(ax, LON_LO, LON_HI, LAT_LO, LAT_HI)
colgap!(fig.layout, 12)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
