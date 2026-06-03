# anyplot.ai
# scatter-ashby-material: Ashby Material Selection Chart
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-03

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const IMPRINT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
    colorant"#954477",
]

# Convex hull via Andrew's monotone chain
function cross2d(o, a, b)
    (a[1] - o[1]) * (b[2] - o[2]) - (a[2] - o[2]) * (b[1] - o[1])
end

function convex_hull_pts(pts)
    n = length(pts)
    n < 3 && return pts
    sorted_pts = sort(pts, by = p -> (p[1], p[2]))
    lower = similar(pts, 0)
    for p in sorted_pts
        while length(lower) >= 2 && cross2d(lower[end-1], lower[end], p) <= 0
            pop!(lower)
        end
        push!(lower, p)
    end
    upper = similar(pts, 0)
    for p in reverse(sorted_pts)
        while length(upper) >= 2 && cross2d(upper[end-1], upper[end], p) <= 0
            pop!(upper)
        end
        push!(upper, p)
    end
    vcat(lower[1:end-1], upper[1:end-1])
end

function expand_hull(hull, pad)
    cx = mean(p -> p[1], hull)
    cy = mean(p -> p[2], hull)
    [(cx + (p[1] - cx) * (1 + pad), cy + (p[2] - cy) * (1 + pad)) for p in hull]
end

# Material families: (density kg/m³, Young's modulus GPa)
const families = ["Metals", "Ceramics", "Polymers", "Composites", "Elastomers", "Foams", "Natural"]

const family_data = [
    # Metals — dense and stiff
    [(2700, 70.0), (7850, 210.0), (4500, 115.0), (8900, 120.0), (8900, 210.0),
     (7200, 170.0), (1740, 45.0), (6000, 200.0), (19300, 411.0), (3100, 80.0),
     (8960, 128.0), (7900, 193.0), (4500, 105.0), (2690, 69.0)],
    # Ceramics — varied density, very stiff
    [(2500, 70.0), (3900, 370.0), (3200, 410.0), (2300, 30.0), (3180, 300.0),
     (2200, 72.0), (3990, 400.0), (6050, 540.0), (2650, 90.0), (3580, 310.0),
     (3100, 380.0), (2700, 200.0)],
    # Polymers — low density, low stiffness
    [(950, 0.8), (1190, 3.4), (1050, 2.3), (1150, 2.0), (1400, 3.5),
     (900, 1.0), (1200, 3.0), (1350, 4.0), (1380, 2.4), (1020, 1.5),
     (1100, 2.8), (960, 0.9), (1300, 3.8)],
    # Composites — medium density, medium-high stiffness
    [(1600, 120.0), (1800, 25.0), (1400, 80.0), (1500, 60.0), (2200, 180.0),
     (1750, 45.0), (1600, 150.0), (2000, 100.0), (1450, 90.0), (1700, 70.0),
     (1550, 110.0), (1900, 55.0)],
    # Elastomers — moderate density, very low stiffness
    [(1000, 0.002), (1200, 0.0015), (1500, 0.008), (1100, 0.003),
     (1300, 0.005), (1050, 0.001), (1400, 0.006), (1250, 0.004),
     (1150, 0.0025), (1350, 0.007)],
    # Foams — very low density, very low stiffness
    [(50, 0.003), (100, 0.012), (200, 0.055), (30, 0.0008),
     (150, 0.022), (300, 0.15), (80, 0.007), (250, 0.08), (400, 0.28),
     (70, 0.005), (180, 0.035)],
    # Natural materials (wood, bamboo, bone — tight cluster)
    [(500, 12.0), (2000, 20.0), (500, 25.0), (700, 15.0),
     (800, 10.0), (1200, 18.0), (400, 8.0), (1800, 22.0),
     (600, 13.0), (900, 16.0), (1500, 21.0)],
]

# Transform to log10 space — poly! on linear axes works correctly
log_family_data = [
    [(log10(Float64(p[1])), log10(Float64(p[2]))) for p in pts]
    for pts in family_data
]

# Manual log-scale ticks (positions are log10 values, labels show original units)
x_tick_pos = [log10(10), log10(100), log10(1000), log10(10000)]
x_tick_labels = ["10", "100", "1000", "10⁴"]

y_tick_pos = [log10(0.001), log10(0.01), log10(0.1), log10(1.0),
              log10(10.0),  log10(100.0), log10(1000.0)]
y_tick_labels = ["10⁻³", "10⁻²", "10⁻¹", "1", "10", "100", "10³"]

# Figure
fig = Figure(
    size = (1600, 900),
    fontsize = 14,
    backgroundcolor = PAGE_BG,
)

title_str = "scatter-ashby-material · julia · makie · anyplot.ai"
title_n = length(title_str)
title_sz = title_n > 67 ? round(Int, 20 * 67 / title_n) : 20

ax = Axis(
    fig[1, 1];
    title = title_str,
    titlesize = title_sz,
    titlecolor = INK,
    xlabel = "Density  (kg m⁻³)",
    ylabel = "Young's Modulus  (GPa)",
    xlabelsize = 14,
    ylabelsize = 14,
    xlabelcolor = INK,
    ylabelcolor = INK,
    xticks = (x_tick_pos, x_tick_labels),
    yticks = (y_tick_pos, y_tick_labels),
    xticklabelsize = 12,
    yticklabelsize = 12,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xtickcolor = INK_SOFT,
    ytickcolor = INK_SOFT,
    leftspinecolor = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    topspinevisible = false,
    rightspinevisible = false,
    backgroundcolor = PAGE_BG,
    xgridcolor = RGBAf(Float32(red(INK)), Float32(green(INK)), Float32(blue(INK)), 0.12f0),
    ygridcolor = RGBAf(Float32(red(INK)), Float32(green(INK)), Float32(blue(INK)), 0.12f0),
    xgridvisible = true,
    ygridvisible = true,
)

# Convex hull regions drawn in log10 space (linear axes → poly! works)
for (i, (fam, log_pts)) in enumerate(zip(families, log_family_data))
    hull = convex_hull_pts(log_pts)
    exp_hull = length(hull) >= 3 ? expand_hull(hull, 0.16) : expand_hull(log_pts, 0.16)
    poly_pts = Point2f[Point2f(Float32(p[1]), Float32(p[2])) for p in exp_hull]
    clr = IMPRINT_PALETTE[i]
    poly!(ax, poly_pts;
        color = (clr, 0.22),
        strokecolor = (clr, 0.80),
        strokewidth = 1.8,
    )
end

# Scatter points in log10 space
for (i, (fam, log_pts)) in enumerate(zip(families, log_family_data))
    xs = Float32[Float32(p[1]) for p in log_pts]
    ys = Float32[Float32(p[2]) for p in log_pts]
    clr = IMPRINT_PALETTE[i]
    scatter!(ax, xs, ys;
        color = clr,
        markersize = 10,
        strokecolor = PAGE_BG,
        strokewidth = 0.8,
    )
end

# Family labels — centroid with per-family vertical offsets for legibility
# (Foams sits above its thin diagonal cluster; Elastomers to the right)
label_y_offset = [0.0, 0.0, 0.0, 0.0, 0.12, 0.45, 0.0]
label_x_offset = [0.0, 0.0, 0.0, 0.0, 0.0,  0.0,  0.0]

for (i, (fam, log_pts)) in enumerate(zip(families, log_family_data))
    cx = Float32(mean(p -> p[1], log_pts) + label_x_offset[i])
    cy = Float32(mean(p -> p[2], log_pts) + label_y_offset[i])
    clr = IMPRINT_PALETTE[i]
    text!(ax, cx, cy;
        text = fam,
        color = clr,
        fontsize = 12,
        align = (:center, :center),
    )
end

# Guide line: E^(1/2)/ρ = c  (stiffness-to-weight index for plate bending)
# log10(E) = 2·log10(ρ) + C  → slope 2 in log-log space
log_rho = range(log10(20.0), log10(25000.0), length=300)
C = -7.2
log_E = 2.0 .* log_rho .+ C
y_min = log10(5e-4); y_max = log10(1500.0)
valid = (log_E .>= y_min) .& (log_E .<= y_max)
if count(valid) > 2
    lines!(ax, collect(log_rho[valid]), collect(log_E[valid]);
        color = (INK_MUTED, 0.55),
        linewidth = 1.3,
        linestyle = :dash,
    )
    last_vi = findlast(valid)
    text!(ax, Float32(log_rho[last_vi] - 0.1), Float32(log_E[last_vi] + 0.25);
        text = "E^½/ρ = c",
        color = INK_MUTED,
        fontsize = 9,
        align = (:right, :bottom),
    )
end

save("plot-$(THEME).png", fig; px_per_unit = 2)
