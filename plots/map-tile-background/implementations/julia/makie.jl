# anyplot.ai
# map-tile-background: Map with Tile Background
# Library: makie 0.24.16 | Julia 1.13.4
# Quality: pending | Updated: 2026-11-26

using CairoMakie
using Colors
using Random
using Downloads
using PNGFiles

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
# Imprint sequential ramp for marks (colored points on the page)
const ANYPLOT_SEQ = THEME == "light" ?
    cgrad([colorant"#009E73", colorant"#4467A3", colorant"#002850"], [0.0, 0.338, 1.0]) :
    cgrad([colorant"#007755", colorant"#009E73", colorant"#CDD9FF"], [0.0, 0.32, 1.0])

# OpenStreetMap tiles; the dark theme inverts their lightness (keyless dark
# basemaps now serve watermarked tiles)
const TILE_URL    = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
const TILE_CREDIT = "© OpenStreetMap contributors"

# City data: major tourist destinations with annual visitor counts (millions)
const city_names = [
    "Paris", "London", "New York", "Tokyo", "Barcelona",
    "Rome", "Dubai", "Istanbul", "Amsterdam", "Singapore",
    "Sydney", "Bangkok", "Mumbai", "Berlin", "Prague",
    "Vienna", "Budapest", "Lisbon", "Copenhagen", "Stockholm",
]
const lons = Float64[
    2.35, -0.12, -74.0, 139.7, 2.17,
    12.5, 55.3, 28.98, 4.9, 103.8,
    151.2, 100.5, 72.88, 13.41, 14.42,
    16.37, 19.04, -9.14, 12.57, 18.07,
]
const lats = Float64[
    48.85, 51.51, 40.71, 35.68, 41.39,
    41.9, 25.2, 41.01, 52.37, 1.35,
    -33.87, 13.75, 19.08, 52.52, 50.08,
    48.21, 47.5, 38.72, 55.68, 59.33,
]
const visitors = Float64[
    34.0, 31.0, 13.6, 12.9, 9.0,
    9.7, 16.7, 14.0, 8.6, 19.1,
    3.8, 22.8, 7.0, 5.3, 4.4,
    6.8, 4.4, 4.1, 2.7, 2.9,
]

# Convert latitudes to Mercator Y for correct Web Mercator projection
y_merc       = log.(tan.(lats .* π ./ 180) .+ 1 ./ cos.(lats .* π ./ 180))
v_min        = minimum(visitors)
v_max        = maximum(visitors)
v_norm       = (visitors .- v_min) ./ (v_max - v_min)
marker_sizes = 10.0 .+ 28.0 .* v_norm

# Padded axis extent (12 % padding in each direction)
lon_pad      = (maximum(lons)   - minimum(lons))   * 0.12
merc_pad     = (maximum(y_merc) - minimum(y_merc)) * 0.12
ax_lon_min   = minimum(lons)   - lon_pad
ax_lon_max   = maximum(lons)   + lon_pad
ax_merc_min  = minimum(y_merc) - merc_pad
ax_merc_max  = maximum(y_merc) + merc_pad
pad_lat_north = atan(sinh(ax_merc_max)) * 180 / π
pad_lat_south = atan(sinh(ax_merc_min)) * 180 / π

# Tile grid parameters
const ZOOM    = 3
const TILE_PX = 256

n_zoom = 1 << ZOOM   # tiles per axis (EPSG:3857 slippy-map convention)
tx_min = clamp(floor(Int, (ax_lon_min + 180) / 360 * n_zoom), 0, n_zoom - 1)
tx_max = clamp(floor(Int, (ax_lon_max + 180) / 360 * n_zoom), 0, n_zoom - 1)
# north edge → smaller tile y index, south edge → larger
ty_min = clamp(floor(Int, (π - log(tan(pad_lat_north * π / 180) + 1 / cos(pad_lat_north * π / 180))) / (2π) * n_zoom), 0, n_zoom - 1)
ty_max = clamp(floor(Int, (π - log(tan(pad_lat_south * π / 180) + 1 / cos(pad_lat_south * π / 180))) / (2π) * n_zoom), 0, n_zoom - 1)

n_tx = tx_max - tx_min + 1
n_ty = ty_max - ty_min + 1

# Stitched raster: [pixel_x, pixel_y] where x = west→east, y = north→south
stitched = fill(RGBA{Float32}(0.87f0, 0.87f0, 0.87f0, 1.0f0), TILE_PX * n_tx, TILE_PX * n_ty)

mktempdir() do tmpdir
    for iy in 0:(n_ty - 1), ix in 0:(n_tx - 1)
        tx  = tx_min + ix
        ty  = ty_min + iy
        url = replace(TILE_URL,
            "{z}" => string(ZOOM), "{x}" => string(tx), "{y}" => string(ty))
        fpath = joinpath(tmpdir, "$(tx)_$(ty).png")
        try
            Downloads.download(url, fpath;
                headers = ["User-Agent" =>
                    "anyplot.ai static visualization; contact@anyplot.ai"])
            tile_mat = PNGFiles.load(fpath)   # size = (height, width) = [row, col] = [y, x]
            # Transpose to [x, y] layout expected by the stitched array
            tile_rgba = RGBA{Float32}.(tile_mat)
            if THEME == "dark"   # invert lightness into dark greys
                lum = 0.299f0 .* red.(tile_rgba) .+ 0.587f0 .* green.(tile_rgba) .+ 0.114f0 .* blue.(tile_rgba)
                g = 0.07f0 .+ 0.30f0 .* (1f0 .- lum)
                tile_rgba = RGBA{Float32}.(g, g, g .* 1.04f0, 1f0)
            end
            tile_t = permutedims(tile_rgba, (2, 1))
            stitched[ix*TILE_PX+1:(ix+1)*TILE_PX, iy*TILE_PX+1:(iy+1)*TILE_PX] = tile_t
        catch e
            @warn "Tile ($tx, $ty) unavailable" exception = e
        end
    end
end

# Geographic bounds of the full stitched raster
img_lon_west   = tx_min / n_zoom * 360 - 180
img_lon_east   = (tx_max + 1) / n_zoom * 360 - 180
img_merc_north = π * (1 - 2 * ty_min / n_zoom)
img_merc_south = π * (1 - 2 * (ty_max + 1) / n_zoom)

# Flip y so index 1 maps to the south (Makie image! convention: y increases upward)
img_makie = reverse(stitched, dims = 2)

# Latitude tick marks in Mercator Y with degree labels
lat_ticks_deg = filter(l -> pad_lat_south < l < pad_lat_north, [-30.0, 0.0, 30.0, 60.0])
lat_tick_merc = log.(tan.(lat_ticks_deg .* π ./ 180) .+ 1 ./ cos.(lat_ticks_deg .* π ./ 180))
lat_tick_strs = [l >= 0 ? "$(round(Int, l))°N" : "$(round(Int, -l))°S" for l in lat_ticks_deg]

lon_ticks_deg = filter(l -> ax_lon_min < l < ax_lon_max, [-60.0, 0.0, 60.0, 120.0])
lon_tick_strs = [l >= 0 ? "$(round(Int, l))°E" : "$(round(Int, -l))°W" for l in lon_ticks_deg]

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "map-tile-background · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Longitude",
    ylabel             = "Latitude",
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
    ygridvisible       = false,
    xticks             = (lon_ticks_deg, lon_tick_strs),
    yticks             = (lat_tick_merc, lat_tick_strs),
    limits             = (ax_lon_min, ax_lon_max, ax_merc_min, ax_merc_max),
)

# Tile background layer
image!(ax, (img_lon_west, img_lon_east), (img_merc_south, img_merc_north), img_makie)

# Data layer: scatter by visitor count (size + color)
scatter!(ax, lons, y_merc;
    color       = v_norm,
    colormap    = ANYPLOT_SEQ,
    markersize  = marker_sizes,
    strokewidth = 1.5,
    strokecolor = PAGE_BG,
)

# Labels for top 8 most-visited cities
top8 = sortperm(visitors, rev = true)[1:8]
for i in top8
    text!(ax, lons[i], y_merc[i];
        text     = city_names[i],
        fontsize = 11,
        color    = INK,
        offset   = city_names[i] == "London" ? (-8, 5) : (8, 5),   # London's label goes west, clear of Amsterdam
        align    = (city_names[i] == "London" ? :right : :left, :bottom),
    )
end

# Tile provider attribution (bottom-right)
text!(ax, ax_lon_max, ax_merc_min;
    text     = TILE_CREDIT,
    fontsize = 10,
    color    = INK_SOFT,
    align    = (:right, :bottom),
    offset   = (-4, 4),
)

Colorbar(
    fig[1, 2];
    colormap       = ANYPLOT_SEQ,
    limits         = (v_min, v_max),
    label          = "Annual Visitors (millions)",
    labelcolor     = INK,
    tickcolor      = INK_SOFT,
    ticklabelcolor = INK_SOFT,
    width          = 20,
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
