# anyplot.ai
# ternary-basic: Basic Ternary Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-08-04

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const GRID     = RGBA(INK.r, INK.g, INK.b, 0.15)
const BRAND    = colorant"#009E73"  # Imprint palette position 1

# --- Data: simulated stainless-steel alloy compositions (wt%, sum to 100) --
n_alloys     = 90
iron_pct     = 55.0 .+ 20.0 .* rand(n_alloys)
chromium_pct = 8.0 .+ 12.0 .* rand(n_alloys)
nickel_pct   = 100.0 .- iron_pct .- chromium_pct

# --- Barycentric -> Cartesian (equilateral triangle, unit side) -------------
# Vertices: Iron=(0,0), Chromium=(1,0), Nickel=(0.5, sqrt(3)/2)
bary_to_xy(b, c) = (b / 100 + 0.5 * c / 100, (sqrt(3) / 2) * c / 100)
xy = bary_to_xy.(chromium_pct, nickel_pct)
xs = first.(xy)
ys = last.(xy)

# --- Plot ---------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title            = "ternary-basic · julia · makie · anyplot.ai",
    titlesize        = 20,
    titlecolor       = INK,
    backgroundcolor  = PAGE_BG,
    aspect           = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)

# Triangle outline
lines!(ax, [0.0, 1.0, 0.5, 0.0], [0.0, 0.0, sqrt(3) / 2, 0.0];
       color = INK_SOFT, linewidth = 2.0)

# Grid lines at 20% intervals — three families, each parallel to one edge
for t in 0.2:0.2:0.8
    # constant iron (parallel to the chromium-nickel edge)
    lines!(ax, [1 - t, 0.5 * (1 - t)], [0.0, (sqrt(3) / 2) * (1 - t)];
           color = GRID, linewidth = 1.0)
    # constant chromium (parallel to the iron-nickel edge)
    lines!(ax, [t, t + 0.5 * (1 - t)], [0.0, (sqrt(3) / 2) * (1 - t)];
           color = GRID, linewidth = 1.0)
    # constant nickel (parallel to the iron-chromium edge)
    lines!(ax, [0.5 * t, 1 - 0.5 * t], [(sqrt(3) / 2) * t, (sqrt(3) / 2) * t];
           color = GRID, linewidth = 1.0)
end

# Vertex labels, offset outward from the centroid
centroid = (0.5, sqrt(3) / 6)
for (vx, vy, label) in [
    (0.0, 0.0, "Iron (Fe)"),
    (1.0, 0.0, "Chromium (Cr)"),
    (0.5, sqrt(3) / 2, "Nickel (Ni)"),
]
    dx, dy = vx - centroid[1], vy - centroid[2]
    d = sqrt(dx^2 + dy^2)
    text!(ax, vx + 0.14 * dx / d, vy + 0.14 * dy / d;
          text = label, color = INK, fontsize = 16, align = (:center, :center))
end

# Edge tick labels — each edge scales the component of its own vertex
for t in 0.2:0.2:0.8
    text!(ax, t, -0.035; text = string(round(Int, (1 - t) * 100)),
          color = INK_SOFT, fontsize = 11, align = (:center, :top))
    text!(ax, 0.5 * t - 0.03, (sqrt(3) / 2) * t; text = string(round(Int, t * 100)),
          color = INK_SOFT, fontsize = 11, align = (:right, :center))
    text!(ax, 1 - 0.5 * t + 0.03, (sqrt(3) / 2) * t; text = string(round(Int, (1 - t) * 100)),
          color = INK_SOFT, fontsize = 11, align = (:left, :center))
end

# Data points — single series, Imprint brand green
scatter!(ax, xs, ys; color = BRAND, markersize = 12, strokewidth = 1.0, strokecolor = PAGE_BG)

xlims!(ax, -0.18, 1.18)
ylims!(ax, -0.12, 1.06)

# --- Save --------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
