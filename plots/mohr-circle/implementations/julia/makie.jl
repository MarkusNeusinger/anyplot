# anyplot.ai
# mohr-circle: Mohr's Circle for Stress Analysis
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 90/100 | Created: 2026-05-30

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens — Imprint palette, theme-adaptive chrome
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (Imprint palette — always first series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red (semantic anchor for critical values)
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Stress state: steel plate under combined biaxial loading and shear (MPa)
# Pythagorean triple (3-4-5) gives clean radius = 50 MPa
const sigma_x = 80.0
const sigma_y = 20.0
const tau_xy  = 40.0

# Mohr's circle geometry
const center_c    = (sigma_x + sigma_y) / 2.0
const radius      = sqrt(((sigma_x - sigma_y) / 2.0)^2 + tau_xy^2)
const sigma1      = center_c + radius
const sigma2      = center_c - radius
const tau_max     = radius
const two_theta_p = atan(tau_xy, sigma_x - center_c)

# Circle (parametric, 360 points)
const n_pts    = 360
const angles   = LinRange(0.0, 2π, n_pts)
const circle_x = center_c .+ radius .* cos.(angles)
const circle_y = radius .* sin.(angles)

# Title
const title_str = "mohr-circle · julia · makie · anyplot.ai"
const n_title   = length(title_str)
const title_sz  = round(Int, 20 * (n_title > 67 ? 67.0 / n_title : 1.0))

# Figure — square canvas (2400×2400 via px_per_unit=2) for true circle aspect ratio
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = title_sz,
    titlecolor         = INK,
    xlabel             = "Normal Stress σ (MPa)",
    ylabel             = "Shear Stress τ (MPa)",
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
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.10),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.10),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    aspect             = DataAspect(),
)

# Axis limits — equal ranges so DataAspect() fills the square canvas
const pad = 30.0
xlims!(ax, sigma2 - pad, sigma1 + pad)
ylims!(ax, -(tau_max + pad), tau_max + pad)

# Reference line: σ-axis (τ = 0)
hlines!(ax, [0.0]; color = (INK_SOFT, 0.55), linewidth = 1.2)

# Reference line: vertical through center C
vlines!(ax, [center_c]; color = (INK_SOFT, 0.4), linewidth = 1.0, linestyle = :dash)

# Mohr's circle — primary element, Imprint palette position 1 (green)
lines!(ax, circle_x, circle_y; color = IMPRINT_PALETTE[1], linewidth = 2.8)

# Diameter line from A to B (construction line)
lines!(ax, [sigma_x, sigma_y], [tau_xy, -tau_xy];
    color = (INK_MUTED, 0.55), linewidth = 1.4, linestyle = :dash)

# Arc showing the principal-plane angle 2θp (measured at center C)
const arc_r    = radius * 0.30
const arc_angs = LinRange(0.0, two_theta_p, 50)
const arc_x    = center_c .+ arc_r .* cos.(arc_angs)
const arc_y    = arc_r .* sin.(arc_angs)
lines!(ax, arc_x, arc_y; color = IMPRINT_PALETTE[4], linewidth = 2.2)

# Center point C
scatter!(ax, [center_c], [0.0]; color = INK, markersize = 9, strokewidth = 0)

# Point A: (σx, τxy) — x-face of the stress element
scatter!(ax, [sigma_x], [tau_xy];
    color = IMPRINT_PALETTE[2], markersize = 17,
    strokewidth = 1.5, strokecolor = PAGE_BG)

# Point B: (σy, −τxy) — y-face of the stress element
scatter!(ax, [sigma_y], [-tau_xy];
    color = IMPRINT_PALETTE[3], markersize = 17,
    strokewidth = 1.5, strokecolor = PAGE_BG)

# Principal stress points σ1, σ2 (circle intersects σ-axis)
scatter!(ax, [sigma1, sigma2], [0.0, 0.0];
    color = IMPRINT_PALETTE[5], markersize = 17, marker = :diamond,
    strokewidth = 1.5, strokecolor = PAGE_BG)

# τ_max points (top and bottom of circle)
scatter!(ax, [center_c, center_c], [tau_max, -tau_max];
    color = IMPRINT_PALETTE[4], markersize = 17,
    strokewidth = 1.5, strokecolor = PAGE_BG)

# Annotations
const nudge = 3.0
const voff  = radius * 0.07

text!(ax, sigma1 + nudge, -voff;
    text     = "σ₁ = $(round(Int, sigma1)) MPa",
    color    = INK,
    fontsize = 12,
    align    = (:left, :top))
text!(ax, sigma2 - nudge, -voff;
    text     = "σ₂ = $(round(Int, sigma2)) MPa",
    color    = INK,
    fontsize = 12,
    align    = (:right, :top))
text!(ax, center_c + nudge, tau_max + voff;
    text     = "τmax = $(round(Int, tau_max)) MPa",
    color    = INK,
    fontsize = 12,
    align    = (:left, :bottom))
text!(ax, center_c - nudge, -(tau_max + voff);
    text     = "−τmax",
    color    = INK,
    fontsize = 12,
    align    = (:right, :top))
text!(ax, sigma_x + nudge, tau_xy;
    text     = "A ($(round(Int, sigma_x)), $(round(Int, tau_xy))) MPa",
    color    = IMPRINT_PALETTE[2],
    fontsize = 11,
    align    = (:left, :center))
text!(ax, sigma_y - nudge, -tau_xy;
    text     = "B ($(round(Int, sigma_y)), $(round(Int, -tau_xy))) MPa",
    color    = IMPRINT_PALETTE[3],
    fontsize = 11,
    align    = (:right, :center))
text!(ax, center_c, voff;
    text     = "C",
    color    = INK,
    fontsize = 13,
    align    = (:center, :bottom))

# 2θp arc label
const mid_arc = two_theta_p / 2.0
text!(ax, center_c + arc_r * 1.45 * cos(mid_arc), arc_r * 1.45 * sin(mid_arc);
    text     = "2θₚ ≈ $(round(rad2deg(two_theta_p), digits=1))°",
    color    = IMPRINT_PALETTE[4],
    fontsize = 11,
    align    = (:left, :center))

save("plot-$(THEME).png", fig; px_per_unit = 2)
