# anyplot.ai
# hexbin-map-geographic: Hexagonal Binning Map
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-05-27

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const GRID_COLOR  = THEME == "light" ?
    RGBAf(26/255f0, 26/255f0, 23/255f0, 0.12f0) :
    RGBAf(240/255f0, 239/255f0, 232/255f0, 0.12f0)

# Anyplot sequential colormap for density (single-polarity)
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# Data: synthetic bike-share ride starts in San Francisco
# Clusters at major transit hubs and popular neighborhoods
cluster_centers = [
    (-122.4057, 37.7871),  # Union Square / Downtown
    (-122.4194, 37.7599),  # Mission District
    (-122.3971, 37.7749),  # SoMa
    (-122.4352, 37.8012),  # Marina
    (-122.4447, 37.7698),  # Haight-Ashbury
]
cluster_weights = [0.33, 0.22, 0.20, 0.13, 0.12]
cluster_stds    = [0.013, 0.012, 0.011, 0.010, 0.013]

n_total = 14000
lons = Float64[]
lats = Float64[]

for ((cx, cy), w, σ) in zip(cluster_centers, cluster_weights, cluster_stds)
    n_i = round(Int, n_total * w)
    append!(lons, cx .+ σ .* randn(n_i))
    append!(lats, cy .+ σ .* randn(n_i))
end

# Clip to SF peninsula bounds
lon_lo, lon_hi = -122.525, -122.355
lat_lo, lat_hi = 37.700,   37.840
mask = (lons .>= lon_lo) .& (lons .<= lon_hi) .& (lats .>= lat_lo) .& (lats .<= lat_hi)
lons = lons[mask]
lats = lats[mask]

# Figure — landscape 3200 × 1800
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

# Title length: "SF Bike-Share · hexbin-map-geographic · julia · makie · anyplot.ai" = 66 chars → keeps default 20
ax = Axis(
    fig[1, 1];
    title              = "SF Bike-Share · hexbin-map-geographic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Longitude",
    ylabel             = "Latitude",
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

# Hexagonal density map
hb = hexbin!(ax, lons, lats;
    cellsize    = 0.009,
    colormap    = ANYPLOT_SEQ,
    threshold   = 1,
    strokecolor = PAGE_BG,
    strokewidth = 0.5,
)

# Colorbar
Colorbar(fig[1, 2], hb;
    label           = "Ride Count",
    labelsize       = 13,
    labelcolor      = INK,
    ticklabelsize   = 11,
    ticklabelcolor  = INK_SOFT,
    tickcolor       = INK_SOFT,
    width           = 18,
)

limits!(ax, lon_lo, lon_hi, lat_lo, lat_hi)
colgap!(fig.layout, 12)

save("plot-$(THEME).png", fig; px_per_unit = 2)
