# anyplot.ai
# bubble-map-geographic: Bubble Map with Sized Geographic Markers
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-01

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens ------------------------------------------------------------
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const LAND_FILL = THEME == "light" ?
    RGBAf(0.87f0, 0.85f0, 0.80f0, 1.0f0) :
    RGBAf(0.24f0, 0.24f0, 0.22f0, 1.0f0)
const COAST_COLOR = THEME == "light" ?
    RGBAf(0.58f0, 0.56f0, 0.52f0, 1.0f0) :
    RGBAf(0.40f0, 0.40f0, 0.37f0, 1.0f0)

const GRAT_ALPHA = THEME == "light" ? 0.08f0 : 0.13f0
const GRAT_COLOR = RGBAf(INK.r, INK.g, INK.b, GRAT_ALPHA)

# Imprint categorical palette — 6 world regions, canonical order (abstract categories)
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — Asia
    colorant"#C475FD",  # 2 — Africa
    colorant"#4467A3",  # 3 — Europe
    colorant"#BD8233",  # 4 — North America
    colorant"#AE3030",  # 5 — South America
    colorant"#2ABCCD",  # 6 — Oceania
]
const REGION_NAMES = ["Asia", "Africa", "Europe", "North America", "South America", "Oceania"]

# --- Data: major world cities by metro population (millions) -----------------
# (name, latitude, longitude, population_millions, region_index)
const cities = [
    ("Tokyo", 35.68, 139.65, 37.4, 1), ("Delhi", 28.61, 77.23, 32.9, 1),
    ("Shanghai", 31.23, 121.47, 29.9, 1), ("Dhaka", 23.81, 90.41, 22.4, 1),
    ("Beijing", 39.90, 116.41, 21.9, 1), ("Mumbai", 19.08, 72.88, 21.3, 1),
    ("Osaka", 34.69, 135.50, 19.1, 1), ("Karachi", 24.86, 67.01, 16.8, 1),
    ("Istanbul", 41.01, 28.98, 15.5, 1), ("Manila", 14.60, 120.98, 14.4, 1),
    ("Bangkok", 13.76, 100.50, 10.7, 1), ("Seoul", 37.57, 126.98, 9.8, 1),
    ("Cairo", 30.04, 31.24, 21.3, 2), ("Lagos", 6.52, 3.38, 15.4, 2),
    ("Kinshasa", -4.32, 15.31, 15.6, 2), ("Johannesburg", -26.20, 28.05, 6.2, 2),
    ("Nairobi", -1.29, 36.82, 5.1, 2),
    ("Moscow", 55.76, 37.62, 12.6, 3), ("Paris", 48.86, 2.35, 11.1, 3),
    ("London", 51.51, -0.13, 9.5, 3), ("Madrid", 40.42, -3.70, 6.7, 3),
    ("Berlin", 52.52, 13.40, 3.7, 3),
    ("Mexico City", 19.43, -99.13, 22.1, 4), ("New York", 40.71, -74.01, 18.9, 4),
    ("Los Angeles", 34.05, -118.24, 12.4, 4), ("Chicago", 41.88, -87.63, 8.9, 4),
    ("Toronto", 43.65, -79.38, 6.3, 4),
    ("Sao Paulo", -23.55, -46.63, 22.6, 5), ("Buenos Aires", -34.60, -58.38, 15.6, 5),
    ("Rio de Janeiro", -22.91, -43.17, 13.7, 5), ("Bogota", 4.71, -74.07, 11.3, 5),
    ("Lima", -12.05, -77.04, 11.0, 5),
    ("Sydney", -33.87, 151.21, 5.4, 6), ("Melbourne", -37.81, 144.96, 5.2, 6),
    ("Auckland", -36.85, 174.76, 1.7, 6),
]

const lats   = Float64[c[2] for c in cities]
const lons   = Float64[c[3] for c in cities]
const pops   = Float64[c[4] for c in cities]
const region = Int[c[5] for c in cities]

# Area-proportional bubble size: markersize scales with sqrt(population), not
# population itself, so visual AREA (not radius) tracks the data value.
const POP_MIN, POP_MAX = minimum(pops), maximum(pops)
const SIZE_MIN, SIZE_MAX = 15.0, 150.0
const sizes = SIZE_MIN .+ (SIZE_MAX - SIZE_MIN) .*
    (sqrt.(pops) .- sqrt(POP_MIN)) ./ (sqrt(POP_MAX) - sqrt(POP_MIN))

# --- Simplified continent basemap (own approximate coastlines) ---------------
# poly! auto-closes each polygon (last point connects back to first).
const _CONTINENTS_RAW = [
    # North America
    [(-165,68),(-140,60),(-125,49),(-117,32),(-105,20),(-90,15),(-80,8),
     (-77,25),(-75,45),(-65,45),(-55,50),(-65,60),(-80,62),(-95,55),
     (-110,58),(-130,55),(-150,60),(-165,68)],
    # South America
    [(-79,9),(-77,1),(-50,0),(-35,-8),(-35,-23),(-48,-28),(-58,-35),
     (-68,-55),(-75,-45),(-72,-20),(-70,-5),(-79,9)],
    # Europe
    [(-10,36),(-9,43),(-1,51),(5,58),(15,55),(25,55),(30,60),(30,70),
     (20,71),(10,63),(5,50),(-5,43),(-10,36)],
    # Africa
    [(-17,15),(-15,5),(9,5),(20,-5),(35,-5),(40,-15),(35,-28),(20,-35),
     (14,-22),(10,0),(15,10),(30,32),(10,37),(-6,35),(-17,15)],
    # Asia
    [(27,40),(45,15),(60,20),(75,10),(90,20),(100,10),(110,5),(122,10),
     (125,25),(120,35),(130,45),(140,50),(150,60),(120,72),(90,72),
     (65,72),(45,60),(35,50),(27,40)],
    # Australia
    [(114,-22),(116,-33),(129,-32),(138,-35),(148,-38),(153,-28),
     (146,-19),(136,-12),(125,-15),(114,-22)],
    # New Zealand
    [(166,-46),(168,-44),(174,-41),(174,-38),(172,-40),(167,-45),(166,-46)],
]
const CONTINENTS = [[Point2f(p[1], p[2]) for p in c] for c in _CONTINENTS_RAW]

# --- Figure: landscape 1600x900 -> 3200x1800 at px_per_unit=2 ----------------
const title_str = "World's Largest Cities by Population · bubble-map-geographic · julia · makie · anyplot.ai"
const title_sz  = round(Int, 20 * min(1.0, 67 / length(title_str)))

fig = Figure(
    size            = (1600, 900),
    fontsize        = 12,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = title_sz,
    titlecolor        = INK,
    xlabel            = "Longitude",
    ylabel            = "Latitude",
    xlabelsize        = 13,
    ylabelsize        = 13,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 10,
    yticklabelsize    = 10,
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
    limits            = (-180, 180, -58, 78),
    xticks            = -180:60:180,
    yticks            = [-60, -30, 0, 30, 60],
)

# Land basemap, drawn first so bubbles sit on top of it
for pts in CONTINENTS
    poly!(ax, pts; color = LAND_FILL, strokecolor = COAST_COLOR, strokewidth = 0.6)
end

# Graticule: reference grid lines for geographic context
for lon in -180:30:180
    lines!(ax, [Float64(lon), Float64(lon)], [-58.0, 78.0]; color = GRAT_COLOR, linewidth = 0.5)
end
for lat in -60:30:60
    lines!(ax, [-180.0, 180.0], [Float64(lat), Float64(lat)]; color = GRAT_COLOR, linewidth = 0.5)
end

# Bubbles, one scatter! call per region so each becomes a labeled legend entry
for r in 1:length(REGION_NAMES)
    mask = region .== r
    scatter!(ax, lons[mask], lats[mask];
        markersize  = sizes[mask],
        color       = IMPRINT_PALETTE[r],
        alpha       = 0.65,
        strokewidth = 1.0,
        strokecolor = PAGE_BG,
        label       = REGION_NAMES[r],
    )
end

# --- Legends: region color key + bubble size key, stacked in a side column ---
legend_col = fig[1, 2] = GridLayout()

Legend(legend_col[1, 1], ax;
    title          = "Region",
    titlesize      = 13,
    titlecolor     = INK,
    labelsize      = 11,
    labelcolor     = INK_SOFT,
    framevisible   = false,
    patchsize      = (14, 14),
    rowgap         = 4,
)

const legend_pops  = [2.0, 15.0, 35.0]
const legend_sizes = SIZE_MIN .+ (SIZE_MAX - SIZE_MIN) .*
    (sqrt.(legend_pops) .- sqrt(POP_MIN)) ./ (sqrt(POP_MAX) - sqrt(POP_MIN))
const size_elements = [
    MarkerElement(color = RGBAf(INK_MUTED.r, INK_MUTED.g, INK_MUTED.b, 0.65f0),
                  marker = :circle, markersize = s, strokewidth = 0)
    for s in legend_sizes
]

Legend(legend_col[2, 1], size_elements, ["$(round(Int, p))M" for p in legend_pops];
    title        = "Population",
    titlesize    = 13,
    titlecolor   = INK,
    labelsize    = 11,
    labelcolor   = INK_SOFT,
    framevisible = false,
    patchsize    = (160, 160),
    rowgap       = 10,
)

colsize!(fig.layout, 2, Fixed(190))

save("plot-$(THEME).png", fig; px_per_unit = 2)
