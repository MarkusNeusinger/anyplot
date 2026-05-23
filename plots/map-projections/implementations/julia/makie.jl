# anyplot.ai
# map-projections: World Map with Different Projections
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-05-23

using CairoMakie
using Colors
using Random

Random.seed!(42)

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND       = colorant"#009E73"

d2r(x) = x * π / 180.0

# --- Projection functions ---

function proj_mercator(lon_deg, lat_deg)
    lat = clamp(lat_deg, -85.0, 85.0)
    return d2r(lon_deg), log(tan(π / 4 + d2r(lat) / 2))
end

function mollweide_theta(lat_deg)
    abs(lat_deg) >= 89.9 && return sign(lat_deg) * (π / 2)
    phi   = d2r(lat_deg)
    theta = phi
    rhs   = π * sin(phi)
    for _ in 1:60
        denom = 2.0 + 2.0 * cos(2theta)
        abs(denom) < 1e-14 && break
        theta -= (2theta + sin(2theta) - rhs) / denom
    end
    return theta
end

function proj_mollweide(lon_deg, lat_deg)
    theta = mollweide_theta(lat_deg)
    return (2sqrt(2) / π) * d2r(lon_deg) * cos(theta), sqrt(2) * sin(theta)
end

function proj_orthographic(lon_deg, lat_deg)
    lam = d2r(lon_deg)
    phi = d2r(lat_deg)
    cos(phi) * cos(lam) < 0.0 && return (NaN, NaN)
    return cos(phi) * sin(lam), sin(phi)
end

const EE_M  = sqrt(3.0) / 2.0
const EE_A1 = 1.340264
const EE_A2 = -0.081106
const EE_A3 = 0.000893
const EE_A4 = 0.003796

function proj_equal_earth(lon_deg, lat_deg)
    lam    = d2r(lon_deg)
    phi    = d2r(lat_deg)
    theta  = asin(clamp(EE_M * sin(phi), -1.0, 1.0))
    theta2 = theta * theta
    P      = EE_A1 + theta2 * (EE_A2 + theta2 * (EE_A3 + theta2 * EE_A4))
    return lam * cos(theta) / (EE_M * P), theta * P
end

# --- Drawing helpers ---

function draw_lines_nan!(ax, xs, ys; color, linewidth)
    n = length(xs)
    i = 1
    while i <= n
        if !isnan(xs[i]) && !isnan(ys[i])
            j = i + 1
            while j <= n && !isnan(xs[j]) && !isnan(ys[j])
                j += 1
            end
            j > i + 1 && lines!(ax, xs[i:j-1], ys[i:j-1]; color=color, linewidth=linewidth)
            i = j
        else
            i += 1
        end
    end
end

function draw_graticule!(ax, proj_fn; lon_step=30, lat_step=30, n_pts=200,
                         color=BRAND, linewidth=0.7)
    for lon in -180:lon_step:180
        lats = range(-89.9, 89.9; length=n_pts)
        xs = Float64[]; ys = Float64[]
        for lat in lats
            x, y = proj_fn(lon, lat)
            push!(xs, x); push!(ys, y)
        end
        draw_lines_nan!(ax, xs, ys; color=color, linewidth=linewidth)
    end
    for lat in -90:lat_step:90
        lons = range(-180, 180; length=n_pts)
        xs = Float64[]; ys = Float64[]
        for lon in lons
            x, y = proj_fn(lon, lat)
            push!(xs, x); push!(ys, y)
        end
        draw_lines_nan!(ax, xs, ys; color=color, linewidth=linewidth)
    end
end

function draw_tissot!(ax, proj_fn; fill_color=BRAND, r_deg=7.0, n_pts=60)
    for lon in -150:60:150, lat in -60:30:60
        cos_lat = max(cosd(lat), 0.01)
        pts     = Point2f[]
        any_nan = false
        for k in 0:n_pts-1
            ang    = 2π * k / n_pts
            x, y   = proj_fn(lon + r_deg * sin(ang) / cos_lat,
                             clamp(lat + r_deg * cos(ang), -89.0, 89.0))
            if isnan(x) || isnan(y)
                any_nan = true
            else
                push!(pts, Point2f(x, y))
            end
        end
        !any_nan && length(pts) >= 3 && poly!(ax, pts;
            color=(fill_color, 0.20f0),
            strokecolor=(fill_color, 0.85f0),
            strokewidth=0.9)
    end
end

# --- Projection boundary shapes ---

function boundary_rect(x0, x1, y0, y1)
    [Point2f(x0, y0), Point2f(x1, y0), Point2f(x1, y1), Point2f(x0, y1)]
end

function boundary_ellipse(a, b; n=300)
    ts = range(0, 2π; length=n)
    [Point2f(a * cos(t), b * sin(t)) for t in ts]
end

function boundary_equal_earth(; n=200)
    lats      = collect(range(-90, 90; length=n))
    right     = [Point2f(proj_equal_earth(180, lat)...)  for lat in lats]
    top_pole  = [Point2f(proj_equal_earth(lon, 90)...)   for lon in range(180, -180; length=60)]
    left      = [Point2f(proj_equal_earth(-180, lat)...) for lat in reverse(lats)]
    bot_pole  = [Point2f(proj_equal_earth(lon, -90)...)  for lon in range(-180, 180; length=60)]
    vcat(right, top_pole, left, bot_pole)
end

# --- Layout ---

const merc_y85   = proj_mercator(0, 85.0)[2]
const grat_color = RGBAf(Float32(BRAND.r), Float32(BRAND.g), Float32(BRAND.b), 0.55f0)
const bord_color = RGBAf(Float32(INK_SOFT.r), Float32(INK_SOFT.g), Float32(INK_SOFT.b), 1.0f0)

fig = Figure(size=(1600, 900), fontsize=14, backgroundcolor=PAGE_BG)

Label(fig[0, 1:2];
    text="map-projections · julia · makie · anyplot.ai",
    fontsize=20, color=INK, tellwidth=false, padding=(0, 0, 6, 0))

specs = [
    (proj_mercator,     "Mercator — Conformal",       1, 1,
     boundary_rect(-π, π, -merc_y85, merc_y85),
     (-π * 1.06, π * 1.06, -merc_y85 * 1.08, merc_y85 * 1.08)),
    (proj_mollweide,    "Mollweide — Equal-Area",      1, 2,
     boundary_ellipse(2sqrt(2), sqrt(2)),
     (-3.05, 3.05, -1.52, 1.52)),
    (proj_orthographic, "Orthographic — Perspective",  2, 1,
     boundary_ellipse(1.0, 1.0),
     (-1.12, 1.12, -1.12, 1.12)),
    (proj_equal_earth,  "Equal Earth — Equal-Area",    2, 2,
     boundary_equal_earth(),
     (-2.9, 2.9, -1.48, 1.48)),
]

for (proj_fn, title, row, col, bnd_pts, (xlo, xhi, ylo, yhi)) in specs
    ax = Axis(fig[row, col];
        title              = title,
        titlesize          = 14,
        titlecolor         = INK,
        backgroundcolor    = PAGE_BG,
        topspinevisible    = false,
        rightspinevisible  = false,
        leftspinevisible   = false,
        bottomspinevisible = false,
        xticksvisible      = false,
        yticksvisible      = false,
        xticklabelsvisible = false,
        yticklabelsvisible = false,
        xgridvisible       = false,
        ygridvisible       = false,
    )
    xlims!(ax, xlo, xhi)
    ylims!(ax, ylo, yhi)
    poly!(ax, bnd_pts; color=ELEVATED_BG, strokewidth=0)
    draw_graticule!(ax, proj_fn; color=grat_color, linewidth=0.7)
    draw_tissot!(ax, proj_fn; fill_color=BRAND)
    poly!(ax, bnd_pts; color=(:white, 0.0f0), strokecolor=bord_color, strokewidth=1.5)
end

rowgap!(fig.layout, 8)
colgap!(fig.layout, 8)

save("plot-$(THEME).png", fig; px_per_unit=2)
