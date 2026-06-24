# anyplot.ai
# line-stress-strain: Engineering Stress-Strain Curve
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-06-21

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
const GRID_COLOR  = THEME == "light" ? RGBAf(0.102, 0.102, 0.090, 0.12) : RGBAf(0.941, 0.937, 0.910, 0.12)
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (ALWAYS first series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red (semantic: peak / critical)
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Mild steel (AISI 1020) — stress values are realistic; strain axis is schematic
# (elastic region widened for visual clarity, a standard textbook convention)
const σ_y1   = 280.0    # upper yield strength (MPa)
const σ_y2   = 250.0    # lower yield strength / Lüders plateau (MPa)
const σ_uts  = 420.0    # ultimate tensile strength (MPa)
const σ_frac = 318.0    # fracture stress (MPa)
const ε_y1   = 0.015    # upper yield strain (schematic)
const ε_y2   = 0.025    # lower yield strain (schematic)
const ε_pe   = 0.065    # end of Lüders plateau
const ε_uts  = 0.220    # strain at UTS
const ε_frac = 0.385    # fracture strain
const E_schm = σ_y1 / ε_y1    # apparent elastic slope for the schematic axis

# Stress-strain curve — five piecewise segments
eps_el   = collect(range(0.0, ε_y1; length=60))
sig_el   = E_schm .* eps_el

eps_dip  = collect(range(ε_y1, ε_y2; length=20))
t_dip    = (eps_dip .- ε_y1) ./ (ε_y2 - ε_y1)
sig_dip  = σ_y1 .+ (σ_y2 - σ_y1) .* t_dip .^ 0.5

eps_plat = collect(range(ε_y2, ε_pe; length=50))
t_wvl    = collect(range(0.0, 1.0; length=50))
sig_plat = σ_y2 .+ 3.5 .* sin.(t_wvl .* 8π) .+ 0.8 .* randn(50)

eps_hard = collect(range(ε_pe, ε_uts; length=150))
sig_hard = σ_y2 .+ (σ_uts - σ_y2) .* ((eps_hard .- ε_pe) ./ (ε_uts - ε_pe)) .^ 0.27

eps_neck = collect(range(ε_uts, ε_frac; length=70))
t_neck   = (eps_neck .- ε_uts) ./ (ε_frac - ε_uts)
sig_neck = σ_uts .- (σ_uts - σ_frac) .* t_neck .^ 0.55

strain = vcat(eps_el, eps_dip[2:end], eps_plat[2:end], eps_hard[2:end], eps_neck[2:end])
stress = vcat(sig_el, sig_dip[2:end], sig_plat[2:end], sig_hard[2:end], sig_neck[2:end])

# 0.2 % offset line (parallel to elastic region, offset by 0.002 in strain)
const ε_off0 = 0.002
eps_off      = collect(range(ε_off0, ε_off0 + σ_uts / E_schm; length=60))
sig_off      = E_schm .* (eps_off .- ε_off0)
mask_off     = sig_off .<= σ_uts * 1.01
eps_off      = eps_off[mask_off]
sig_off      = sig_off[mask_off]

# Yield point (0.2 % offset intersection with curve)
const ε_yield = ε_off0 + σ_y2 / E_schm
const σ_yield = σ_y2

# Young's modulus indicator — dotted line along the elastic slope
const ε_E_end  = ε_y1 * 0.60
const ε_E_line = [0.0, ε_E_end]
const σ_E_line = E_schm .* ε_E_line

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-stress-strain · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Engineering Strain  (ε,  schematic scale — elastic region widened for clarity)",
    ylabel             = "Engineering Stress  (σ, MPa)",
    xlabelsize         = 13,
    ylabelsize         = 13,
    xticklabelsize     = 11,
    yticklabelsize     = 11,
    xlabelcolor        = INK_SOFT,
    ylabelcolor        = INK_SOFT,
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
    ygridvisible       = true,
    ygridcolor         = GRID_COLOR,
)

xlims!(ax, -0.008, 0.425)
ylims!(ax, -20.0,  510.0)

# Region background shading
poly!(ax, [Point2f(0.0, -20), Point2f(ε_y1, -20), Point2f(ε_y1, 472), Point2f(0.0, 472)];
    color = RGBAf(0.0, 0.620, 0.451, 0.07), strokewidth = 0)

poly!(ax, [Point2f(ε_y1, -20), Point2f(ε_uts, -20), Point2f(ε_uts, 472), Point2f(ε_y1, 472)];
    color = RGBAf(0.267, 0.404, 0.639, 0.05), strokewidth = 0)

poly!(ax, [Point2f(ε_uts, -20), Point2f(0.425, -20), Point2f(0.425, 472), Point2f(ε_uts, 472)];
    color = RGBAf(0.741, 0.510, 0.200, 0.06), strokewidth = 0)

# Region boundaries
vlines!(ax, [ε_y1, ε_uts];
    color     = INK_MUTED,
    linewidth = 1.0,
    linestyle = :dash,
)

# 0.2 % offset line
lines!(ax, eps_off, sig_off;
    color     = IMPRINT_PALETTE[3],
    linewidth = 2.0,
    linestyle = :dash,
)

# Main stress-strain curve (on top)
lines!(ax, strain, stress;
    color     = IMPRINT_PALETTE[1],
    linewidth = 3.5,
)

# Young's modulus slope indicator
lines!(ax, ε_E_line, σ_E_line;
    color     = INK_MUTED,
    linewidth = 2.0,
    linestyle = :dot,
)

# Horizontal reference at UTS
hlines!(ax, [σ_uts];
    color     = IMPRINT_PALETTE[5],
    linewidth = 0.8,
    linestyle = :dot,
)

# Critical point markers
scatter!(ax, [ε_yield], [σ_yield];
    color       = IMPRINT_PALETTE[1],
    markersize  = 16,
    strokewidth = 2.0,
    strokecolor = INK,
)
scatter!(ax, [ε_uts], [σ_uts];
    color       = IMPRINT_PALETTE[5],
    markersize  = 16,
    strokewidth = 2.0,
    strokecolor = INK,
)
scatter!(ax, [ε_frac], [σ_frac];
    color       = INK_SOFT,
    markersize  = 16,
    strokewidth = 2.0,
    strokecolor = INK,
)

# Region labels (top of shaded areas)
text!(ax, ε_y1 / 2, 485;
    text     = "Elastic",
    fontsize = 13,
    color    = INK_SOFT,
    align    = (:center, :center),
)
text!(ax, (ε_y1 + ε_uts) / 2, 485;
    text     = "Plastic  (Strain Hardening)",
    fontsize = 13,
    color    = INK_SOFT,
    align    = (:center, :center),
)
text!(ax, (ε_uts + 0.425) / 2, 485;
    text     = "Necking",
    fontsize = 13,
    color    = INK_SOFT,
    align    = (:center, :center),
)

# Critical point annotations
text!(ax, ε_yield + 0.009, σ_yield + 22;
    text     = "Yield Point (0.2 % offset)\n$(Int(round(σ_yield))) MPa",
    fontsize = 11,
    color    = INK_SOFT,
    align    = (:left, :bottom),
)
text!(ax, ε_uts + 0.010, σ_uts + 8;
    text     = "UTS = $(Int(round(σ_uts))) MPa",
    fontsize = 11,
    color    = IMPRINT_PALETTE[5],
    align    = (:left, :bottom),
)
text!(ax, ε_frac + 0.007, σ_frac;
    text     = "Fracture\n$(Int(round(σ_frac))) MPa",
    fontsize = 11,
    color    = INK_SOFT,
    align    = (:left, :center),
)
text!(ax, ε_off0 + 0.010, 48;
    text     = "0.2 % offset line",
    fontsize = 11,
    color    = IMPRINT_PALETTE[3],
    align    = (:left, :center),
)
text!(ax, ε_E_end + 0.003, σ_E_line[end] - 20;
    text     = "slope = E ≈ 200 GPa",
    fontsize = 11,
    color    = INK_MUTED,
    align    = (:left, :top),
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
