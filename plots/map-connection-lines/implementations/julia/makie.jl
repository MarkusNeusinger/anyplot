# anyplot.ai
# map-connection-lines: Connection Lines Map (Origin-Destination)
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-05-28

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const GRAT_ALPHA  = THEME == "light" ? 0.08f0 : 0.13f0
const GRAT_COLOR  = THEME == "light" ?
    RGBAf(26f0/255f0, 26f0/255f0, 23f0/255f0, GRAT_ALPHA) :
    RGBAf(240f0/255f0, 239f0/255f0, 232f0/255f0, GRAT_ALPHA)

# Sequential colormap: anyplot brand green → blue (single-polarity continuous)
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])
# Endpoint components for inline linear interpolation
const SEQ_R1, SEQ_G1, SEQ_B1 = 0f0/255f0,  158f0/255f0, 115f0/255f0   # #009E73
const SEQ_R2, SEQ_G2, SEQ_B2 = 68f0/255f0, 103f0/255f0, 163f0/255f0   # #4467A3

# Data: major world airports (lat, lon)
const airport_names = [
    "London", "New York", "Dubai", "Singapore",
    "Tokyo", "Sydney", "Paris", "Los Angeles",
    "Hong Kong", "Frankfurt",
]
const airport_lats = Float64[
     51.5,  40.7,  25.2,   1.4,
     35.7, -33.9,  48.9,  34.1,
     22.3,  50.0,
]
const airport_lons = Float64[
     -0.1, -74.0,  55.4, 103.8,
    139.7, 151.2,   2.4, -118.2,
    114.2,   8.6,
]

# Connections: (origin_idx, dest_idx, annual_passengers_millions)
const connections = [
    (1, 2, 12.5),   # London – New York
    (1, 3,  8.3),   # London – Dubai
    (1, 9,  6.1),   # London – Hong Kong
    (1, 4,  5.2),   # London – Singapore
    (2, 8,  9.8),   # New York – Los Angeles
    (2, 7,  5.7),   # New York – Paris
    (3, 9,  7.2),   # Dubai – Hong Kong
    (3, 4,  4.1),   # Dubai – Singapore
    (9, 4,  6.8),   # Hong Kong – Singapore
    (4, 5,  4.8),   # Singapore – Tokyo
    (4, 6,  3.4),   # Singapore – Sydney
    (5, 9,  5.3),   # Tokyo – Hong Kong
    (5, 8,  4.2),   # Tokyo – Los Angeles
    (7, 2,  5.7),   # Paris – New York
    (10, 2, 3.9),   # Frankfurt – New York
]

const volumes = Float64[c[3] for c in connections]
const vmin = minimum(volumes)
const vmax = maximum(volumes)

# Figure (landscape 1600×900 → 3200×1800 at px_per_unit=2)
const title_str = "Global Air Routes · map-connection-lines · julia · makie · anyplot.ai"
const title_sz  = round(Int, 20 * min(1.0, 67 / length(title_str)))

fig = Figure(
    size            = (1600, 900),
    fontsize        = 12,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title               = title_str,
    titlesize           = title_sz,
    titlecolor          = INK,
    xlabel              = "Longitude",
    ylabel              = "Latitude",
    xlabelsize          = 13,
    ylabelsize          = 13,
    xlabelcolor         = INK,
    ylabelcolor         = INK,
    xticklabelsize      = 10,
    yticklabelsize      = 10,
    xticklabelcolor     = INK_SOFT,
    yticklabelcolor     = INK_SOFT,
    xtickcolor          = INK_SOFT,
    ytickcolor          = INK_SOFT,
    backgroundcolor     = PAGE_BG,
    topspinevisible     = false,
    rightspinevisible   = false,
    leftspinecolor      = INK_SOFT,
    bottomspinecolor    = INK_SOFT,
    xgridvisible        = false,
    ygridvisible        = false,
    limits              = (-180, 180, -90, 90),
    xticks              = -180:60:180,
    yticks              = -90:30:90,
)

# Graticule: lines every 30° for geographic context
for lon in -180:30:180
    lines!(ax, [Float64(lon), Float64(lon)], [-90.0, 90.0];
        color = GRAT_COLOR, linewidth = 0.5)
end
for lat in -90:30:90
    lines!(ax, [-180.0, 180.0], [Float64(lat), Float64(lat)];
        color = GRAT_COLOR, linewidth = 0.5)
end

# Connection arcs: great-circle paths colored by passenger volume
for (oi, di, volume) in connections
    φ1 = deg2rad(airport_lats[oi]);  λ1 = deg2rad(airport_lons[oi])
    φ2 = deg2rad(airport_lats[di]);  λ2 = deg2rad(airport_lons[di])
    d_ang = acos(clamp(sin(φ1) * sin(φ2) + cos(φ1) * cos(φ2) * cos(λ2 - λ1), -1.0, 1.0))

    arc_lons = Float64[]
    arc_lats = Float64[]
    n_pts = 80
    for i in 0:n_pts
        t = i / n_pts
        A = sin((1 - t) * d_ang) / sin(d_ang)
        B = sin(t * d_ang) / sin(d_ang)
        x = A * cos(φ1) * cos(λ1) + B * cos(φ2) * cos(λ2)
        y = A * cos(φ1) * sin(λ1) + B * cos(φ2) * sin(λ2)
        z = A * sin(φ1) + B * sin(φ2)
        lon_pt = rad2deg(atan(y, x))
        lat_pt = rad2deg(atan(z, sqrt(x^2 + y^2)))
        if !isempty(arc_lons) && abs(lon_pt - arc_lons[end]) > 180
            push!(arc_lons, NaN)
            push!(arc_lats, NaN)
        end
        push!(arc_lons, lon_pt)
        push!(arc_lats, lat_pt)
    end

    nv = Float32((volume - vmin) / (vmax - vmin))
    arc_color = RGBAf(
        SEQ_R1 + (SEQ_R2 - SEQ_R1) * nv,
        SEQ_G1 + (SEQ_G2 - SEQ_G1) * nv,
        SEQ_B1 + (SEQ_B2 - SEQ_B1) * nv,
        0.75f0,
    )
    lines!(ax, arc_lons, arc_lats;
        color     = arc_color,
        linewidth = 1.0 + 3.5 * nv,
    )
end

# Airport markers
scatter!(ax, airport_lons, airport_lats;
    color       = colorant"#009E73",
    markersize  = 10,
    strokewidth = 1.5,
    strokecolor = INK,
)

# Airport labels (lon offset, lat offset) to avoid overlap with markers
const label_offsets = [
    (-5.0,  4.0),   # London
    (-7.0, -5.5),   # New York
    ( 4.0,  3.5),   # Dubai
    ( 5.0, -5.5),   # Singapore
    ( 5.0,  3.5),   # Tokyo
    ( 5.0, -5.5),   # Sydney
    ( 4.0,  3.5),   # Paris
    (-7.0, -5.5),   # Los Angeles
    ( 5.0,  3.5),   # Hong Kong
    ( 4.0, -5.5),   # Frankfurt
]

for (i, name) in enumerate(airport_names)
    dx, dy = label_offsets[i]
    text!(ax, airport_lons[i] + dx, airport_lats[i] + dy;
        text     = name,
        fontsize = 10,
        color    = INK_SOFT,
        align    = (:center, :center),
    )
end

# Colorbar: passenger volume → sequential colormap
Colorbar(fig[1, 2];
    colormap       = ANYPLOT_SEQ,
    limits         = (vmin, vmax),
    label          = "Passengers (M / year)",
    labelsize      = 12,
    labelcolor     = INK,
    ticklabelsize  = 10,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    width          = 18,
    tellheight     = false,
)

colsize!(fig.layout, 2, Fixed(90))

save("plot-$(THEME).png", fig; px_per_unit = 2)
