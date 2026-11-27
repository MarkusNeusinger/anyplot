# anyplot.ai
# map-connection-lines: Connection Lines Map (Origin-Destination)
# Library: makie 0.24.16 | Julia 1.13.4
# Quality: pending | Updated: 2026-11-26

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

# Land and coastline colors (theme-adaptive)
const LAND_FILL   = THEME == "light" ?
    RGBAf(0.87f0, 0.85f0, 0.80f0, 1.0f0) :
    RGBAf(0.24f0, 0.24f0, 0.22f0, 1.0f0)
const COAST_COLOR = THEME == "light" ?
    RGBAf(0.58f0, 0.56f0, 0.52f0, 1.0f0) :
    RGBAf(0.40f0, 0.40f0, 0.37f0, 1.0f0)

const GRAT_ALPHA  = THEME == "light" ? 0.08f0 : 0.13f0
const GRAT_COLOR  = THEME == "light" ?
    RGBAf(26f0/255f0, 26f0/255f0, 23f0/255f0, GRAT_ALPHA) :
    RGBAf(240f0/255f0, 239f0/255f0, 232f0/255f0, GRAT_ALPHA)

# Imprint sequential ramp, marks stops (colored lines on the page), per theme
const IMPRINT_SEQ_MARKS = THEME == "light" ?
    cgrad([colorant"#009E73", colorant"#024582", colorant"#351E45"], [0.0, 0.687, 1.0]) :
    cgrad([colorant"#6F7E20", colorant"#009E73", colorant"#CDD9FF"], [0.0, 0.21, 1.0])

# Airport data: (name, lat, lon)
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

# Connections: (origin_idx, dest_idx, annual_passengers_millions, both directions)
const connections = [
    (1, 2, 3.4), (1, 3, 2.0), (1, 9, 1.0), (1, 4, 1.4),
    (2, 8, 3.0), (2, 7, 1.9), (3, 9, 0.9), (3, 4, 1.1),
    (9, 4, 2.0), (4, 5, 1.2), (4, 6, 1.5), (5, 9, 2.4),
    (5, 8, 1.0), (7, 3, 1.2), (10, 2, 1.6),
]

const volumes = Float64[c[3] for c in connections]
const vmin = minimum(volumes)
const vmax = maximum(volumes)

# Hand-digitised land outlines as (lon, lat) vertices: continents, major islands and
# the inland seas that cut into them, so the shorelines follow the real coasts.
# poly! auto-closes each polygon (last point connects back to first).
const _LAND_RAW = [
    # North America
    [(-168,65.5),(-165,68.5),(-156,71.3),(-141,69.7),(-128,70),(-115,68),(-95,68),(-95,72),
     (-88,68),(-82,69),(-82,66),(-90,64),(-94,61),(-93,58.5),(-85,55.5),(-82,52.5),(-79,51.5),
     (-79,55),(-77,60),(-72,62),(-65,60.5),(-61.5,56),(-56,52),(-64,50),(-60,47),(-64,45),
     (-66,44.5),(-70,43.5),(-70,41.7),(-74,40.5),(-76,37),(-75.5,35.2),(-81,31.5),(-80,27),
     (-80.5,25.2),(-82,26.5),(-82.8,29.5),(-85,29.7),(-89,30.2),(-91,29.3),(-94,29.5),
     (-97.2,27.5),(-97.5,22),(-95,18.5),(-91,18.7),(-90.5,21),(-87,21.5),(-88,16),(-84,15.5),
     (-83.5,11),(-81.5,8.8),(-79,9.4),(-77.3,8.6),(-80,7.3),(-83,8.3),(-86,11),(-90,13.5),
     (-94.5,16),(-97,15.8),(-105.5,20),(-105.5,23),(-109,26),(-112.5,30),(-114.8,31.7),
     (-114.5,30),(-112,26.5),(-109.5,23),(-112,24.7),(-114.5,28),(-115.5,30),(-117,32.5),
     (-120.5,34.5),(-122.5,37.5),(-124,40.5),(-124.5,43),(-124,46.5),(-123,48.5),(-127,51),
     (-130.5,54.5),(-134,57),(-138,59),(-146,60.7),(-152,59.3),(-154,57),(-158,56),
     (-163,54.8),(-157.5,58.5),(-162,59.5),(-165,61),(-165,64),(-161.5,64.5)],
    # South America
    [(-77.3,8.6),(-75.5,10.8),(-71.5,12),(-68,10.6),(-62,10.7),(-60,8.5),(-57,6),(-52,5),
     (-50,1.5),(-50,0),(-44,-2.5),(-39,-3.5),(-35,-5.5),(-35,-9),(-39,-13.5),(-39,-18),
     (-41,-22),(-44,-23),(-48,-26),(-48.7,-28.5),(-52,-32),(-54,-34.5),(-57,-35),(-58,-38),
     (-62,-39),(-65,-41),(-63.5,-42.5),(-65.5,-45),(-67.5,-46.5),(-66,-48),(-69,-51),
     (-68.5,-52.5),(-65,-55),(-72,-54),(-75,-50),(-74,-45),(-73.5,-40),(-71.5,-32),
     (-71.5,-28),(-70,-18),(-76,-14),(-79,-8),(-81,-5),(-80,-2),(-80,1),(-78,2.5),(-77.5,6)],
    # Eurasia (Iberia, Italy, Greece, Anatolia, Arabia, India and Southeast Asia included)
    [(-9,37),(-9,43),(-2,43.5),(-1,46),(-4.5,48.5),(2,51),(5,53),(8,54),(8.5,57),(10.5,57.5),
     (10,54.5),(14,54),(19,54.5),(21,57),(24,57.5),(24,59.5),(30,60),(23,60),(21.5,63),
     (25,65.5),(22,65.8),(17.5,62),(19,60),(16.5,57),(13,55.5),(11,59),(8,58),(5,59),(5,62),
     (14,67),(20,70),(28,71),(40,67),(44,68),(60,69),(70,73),(80,73),(100,77),(113,74),
     (130,71),(150,71),(170,70),(180,68),(180,65),(178,64.5),(170,60),(163,60),(163,56),
     (156,51),(156,57),(160,61),(155,59),(143,59),(135,55),(141,53),(140,48),(135,43),
     (130,42),(129,36),(126,35),(126,38),(125,40),(122,40),(118,39),(122,37),(119,35),
     (122,31),(121,28),(117,23.5),(110,21),(108,21.5),(106,19),(109,12),(105,9),(103,10.5),
     (100,13),(99,9),(101,6.5),(103.5,1.5),(100.5,3.5),(98,8),(98.5,16),(94,18),(92,22),
     (90,22),(87,21),(80,15.5),(80,10),(77.5,8),(76,11),(73,17),(72.8,21),(70,21),(67,24.5),
     (62,25),(57,25.5),(56.5,27),(54,26.7),(51,28),(48.5,30),(48,29.5),(50,26.5),(51.5,24.5),
     (54,24.2),(56,26),(56.5,24.5),(59.5,22.5),(58.5,20),(55,17),(52,16),(45,12.8),(43,13),
     (42.5,16),(39,21.5),(35,28),(34.5,29.5),(34.2,31.2),(35,33),(36,36),(32,36.5),(29,36.5),
     (27,37),(26.5,40),(24,40.5),(23,40),(23,38),(22,37),(21,38),(19.5,40.5),(19,42),(15,45),
     (12.5,45.5),(13.5,43.5),(16,41.5),(18.5,40),(16,38),(15.7,40),(12,42),(10,44),(7,43.5),
     (3,43.2),(3,42),(0,39.5),(-1,37.5),(-5,36)],
    # Africa
    [(-17,21),(-13,27.5),(-9.5,30),(-6,35.8),(-2,35),(3,36.8),(10,37.3),(11,35),(10,34),
     (15,32.3),(20,30.3),(20,32),(25,31.7),(32,31.2),(34,30.5),(35,24),(37.5,18),(39,15.5),
     (43,12.5),(51,11.8),(51,10.5),(48,5),(41,-2),(39,-5),(40,-10.5),(40.5,-15),(35,-20),
     (35.5,-24),(32.5,-26),(32,-29),(28,-33),(20,-34.8),(18.3,-34),(15,-27),(11.8,-17),
     (13.5,-12),(12,-5),(9,-1),(9.5,4),(5,6),(-2,5),(-8,4.5),(-13,8),(-17,13.5),(-16.5,20)],
    # Australia
    [(113.5,-22),(114,-26),(115,-34),(118,-35),(123,-34),(129,-31.5),(132,-32),(135.5,-34.8),
     (138,-35),(140,-38),(146,-39),(150,-37.5),(153,-31),(153.5,-26),(149,-21),(146,-18.5),
     (145.5,-15),(143.5,-14),(142.5,-10.7),(141.5,-13),(141,-17),(139,-17.5),(136,-15),
     (137,-12),(132,-11.3),(130,-12.5),(129,-15),(126,-14),(122.5,-17.5),(121,-19.5),(117,-20.7)],
    # Japan: Honshu, Hokkaido, Kyushu
    [(130.9,34),(132.5,35.5),(136,36),(137,37.3),(140,39.5),(140,41.5),(141.5,41),(142,39),
     (141,37),(140.8,35.7),(139.8,35),(137,34.6),(135.2,33.5),(134.5,34.5),(132.5,34),(131,33.9)],
    [(140,41.7),(141,45.4),(145.5,43.3),(143,42),(141,42.5)],
    [(129.7,33),(131,33.8),(131.9,33),(131,31.2),(130.2,31.3)],
    # Greenland
    [(-73,78),(-60,82),(-30,83.5),(-20,82),(-18,76),(-22,70),(-32,68),(-40,65),(-43,60),
     (-48,61),(-52,65),(-54,69),(-58,75)],
    # Great Britain, Ireland, Iceland, Cuba
    [(-5.5,50),(1.5,51),(1.7,52.8),(-0.5,54),(-2,56),(-2,57.6),(-3.5,58.6),(-5.5,58.5),
     (-6,56.5),(-5,55),(-3,54.8),(-3,53.5),(-4.5,53.3),(-5,51.8)],
    [(-10,52),(-6,52),(-6,54.3),(-8,55.2),(-10,54)],
    [(-24,65.5),(-22,66.4),(-14.5,66),(-13.5,64.5),(-18,63.4),(-22.5,63.8)],
    [(-85,22),(-82,23.2),(-74,20),(-77.5,19.8),(-81,22)],
    # Madagascar, Sri Lanka, Philippines (Luzon), Indonesia, New Guinea, New Zealand
    [(43.5,-24),(47,-25),(50,-15.5),(49.5,-12),(47,-15),(44,-17)],
    [(80,9.7),(81.8,7.5),(80.5,6),(79.8,7.5)],
    [(120,18.5),(122,18.3),(122,14),(124,13),(121,13.7),(120,16)],
    [(95.5,5.5),(98,4),(104,-1),(106,-3),(105.5,-5.8),(102,-4),(98.5,1),(95.5,3.5)],
    [(105.5,-6.5),(111,-6.5),(114.5,-7.8),(106,-7.5)],
    [(109,1.5),(111,1.8),(114,4.5),(117,7),(119,5),(117.5,1),(116.5,-3),(114,-4),(110.5,-3),(109.5,-1)],
    [(131,-1),(135,-3.3),(141,-2.6),(147,-6),(150,-10.5),(143,-9),(138,-8.3),(134,-4)],
    [(173,-35),(175.5,-37),(178,-37.7),(176,-41.5),(174.5,-39.5),(174,-37.5)],
    [(172.5,-40.5),(174,-41.5),(171,-44.5),(169,-46.6),(166.5,-46),(170.5,-43)],
    # Chukotka beyond the antimeridian
    [(-180,68),(-170,66),(-180,65)],
]
# Inland seas drawn over the land in the page color
const _SEAS_RAW = [
    [(28,42),(28,44.5),(30,46),(33,46),(35,45),(38,47),(40,45),(41.5,42),(36,41.5),(32,41.8)],  # Black Sea
    [(47,45),(50,46),(53,45),(53,41),(54,37),(50,37),(49,40),(47,43)],                           # Caspian Sea
]
const LAND = [[Point2f(p[1], p[2]) for p in c] for c in _LAND_RAW]
const SEAS = [[Point2f(p[1], p[2]) for p in c] for c in _SEAS_RAW]

# Figure: landscape 1600×900 → 3200×1800 at px_per_unit=2
const title_str = "Global Air Routes · map-connection-lines · julia · makie · anyplot.ai"
const title_sz  = round(Int, 20 * min(1.0, 67 / length(title_str)))

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title               = title_str,
    titlesize           = title_sz,
    titlecolor          = INK,
    xlabel              = "Longitude",
    ylabel              = "Latitude",
    xlabelsize          = 14,
    ylabelsize          = 14,
    xlabelcolor         = INK,
    ylabelcolor         = INK,
    xticklabelsize      = 14,
    yticklabelsize      = 14,
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
    limits              = (-180, 180, -50, 75),
    xticks              = -180:60:180,
    yticks              = [-30, 0, 30, 60],
)

# Base map: land fills and coastlines (drawn first, behind all other elements)
for (shapes, fill) in ((LAND, LAND_FILL), (SEAS, PAGE_BG))
    for pts in shapes
        poly!(ax, pts; color = fill, strokewidth = 0)
        lines!(ax, vcat(pts, pts[1:1]); color = COAST_COLOR, linewidth = 0.6)
    end
end

# Graticule: reference grid lines for geographic context
for lon in -180:30:180
    lines!(ax, [Float64(lon), Float64(lon)], [-50.0, 75.0];
        color = GRAT_COLOR, linewidth = 0.5)
end
for lat in -30:30:60
    lines!(ax, [-180.0, 180.0], [Float64(lat), Float64(lat)];
        color = GRAT_COLOR, linewidth = 0.5)
end

# Connection arcs: great-circle paths via SLERP, colored by passenger volume
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
    base_c = get(IMPRINT_SEQ_MARKS, nv)
    arc_color = RGBAf(red(base_c), green(base_c), blue(base_c), 0.60f0)  # spec: 0.3-0.6
    lines!(ax, arc_lons, arc_lats;
        color     = arc_color,
        linewidth = 2.0 + 3.0 * nv,
    )
end

# Airport endpoint markers
scatter!(ax, airport_lons, airport_lats;
    color       = colorant"#009E73",
    markersize  = 10,
    strokewidth = 1.5,
    strokecolor = INK,
)

# Airport labels with manual offsets to minimise overlap in dense clusters
const label_offsets = [
    (-6.5,  4.0),   # London
    (-7.0, -5.5),   # New York
    ( 4.0,  3.5),   # Dubai
    ( 5.0, -5.5),   # Singapore
    ( 5.0,  3.5),   # Tokyo
    ( 5.0, -5.5),   # Sydney
    (-6.0, -4.5),   # Paris
    (-7.0, -5.5),   # Los Angeles
    ( 5.0,  3.5),   # Hong Kong
    ( 6.5, -4.0),   # Frankfurt
]

for (i, name) in enumerate(airport_names)
    dx, dy = label_offsets[i]
    text!(ax, airport_lons[i] + dx, airport_lats[i] + dy;
        text     = name,
        fontsize = 13,
        color    = INK_SOFT,
        align    = (:center, :center),
    )
end

# Colorbar: maps passenger volume (M/year) to the sequential palette
Colorbar(fig[1, 2];
    colormap       = IMPRINT_SEQ_MARKS,
    limits         = (vmin, vmax),
    label          = "Passengers (M / year)",
    labelsize      = 14,
    labelcolor     = INK,
    ticklabelsize  = 12,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    width          = 18,
    tellheight     = false,
)

colsize!(fig.layout, 2, Fixed(90))

save("plot-$(THEME).png", fig; px_per_unit = 2)
