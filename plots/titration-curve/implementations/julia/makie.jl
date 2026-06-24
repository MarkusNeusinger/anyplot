# anyplot.ai
# titration-curve: Acid-Base Titration Curve
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-24

using CairoMakie
using Colors
using Random

Random.seed!(42)

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const IMPRINT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
    colorant"#954477",
    colorant"#99B314",
]

# Data: 25 mL of 0.1 M HCl titrated with 0.1 M NaOH
n_points = 200
volumes  = collect(range(0.0, 50.0; length = n_points))

function calc_ph(v)
    v_eq_local  = 25.0
    c           = 0.1
    v_hcl_local = 25.0
    if v < v_eq_local - 1e-4
        n_excess_h = (v_eq_local - v) * c * 1e-3
        v_total    = (v_hcl_local + v) * 1e-3
        return -log10(n_excess_h / v_total)
    elseif v > v_eq_local + 1e-4
        n_excess_oh = (v - v_eq_local) * c * 1e-3
        v_total     = (v_hcl_local + v) * 1e-3
        return 14.0 + log10(n_excess_oh / v_total)
    else
        return 7.0
    end
end

ph     = clamp.([calc_ph(v) for v in volumes], 0.0, 14.0)
dph_dv = zeros(n_points)
for i in 2:(n_points - 1)
    dph_dv[i] = (ph[i + 1] - ph[i - 1]) / (volumes[i + 1] - volumes[i - 1])
end
dph_dv[1]   = dph_dv[2]
dph_dv[end] = dph_dv[end - 1]

v_eq  = 25.0
ph_eq = 7.0

# Title with length-aware fontsize
title_str = "HCl/NaOH Titration · titration-curve · julia · makie · anyplot.ai"
titlesize = max(16, round(Int, 20.0 * min(1.0, 67.0 / length(title_str))))

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

# Primary axis (pH)
ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = titlesize,
    titlecolor         = INK,
    xlabel             = "Volume of NaOH added (mL)",
    ylabel             = "pH",
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
    xgridvisible       = false,
    ygridvisible       = true,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12f0),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

# Secondary axis (dpH/dV derivative, right side)
ax2 = Axis(
    fig[1, 1];
    yaxisposition      = :right,
    ylabel             = "dpH/dV (pH·mL⁻¹)",
    ylabelsize         = 14,
    ylabelcolor        = IMPRINT_PALETTE[2],
    yticklabelsize     = 12,
    yticklabelcolor    = IMPRINT_PALETTE[2],
    ytickcolor         = IMPRINT_PALETTE[2],
    rightspinecolor    = IMPRINT_PALETTE[2],
    backgroundcolor    = :transparent,
    topspinevisible    = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xticklabelsvisible = false,
    xticksvisible      = false,
    xgridvisible       = false,
    ygridvisible       = false,
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

linkxaxes!(ax, ax2)
xlims!(ax, 0, 50)
ylims!(ax, 0, 14)
ylims!(ax2, 0, 20)

# Rapid transition zone highlight (±2 mL around equivalence point)
poly!(
    ax,
    [Point2f(23, 0), Point2f(27, 0), Point2f(27, 14), Point2f(23, 14)];
    color       = (IMPRINT_PALETTE[6], 0.1),
    strokewidth = 0,
)

# pH titration curve
ph_line = lines!(ax, volumes, ph;
    color     = IMPRINT_PALETTE[1],
    linewidth = 3.0,
)

# Equivalence point vertical dashed line
vlines!(ax, [v_eq];
    color     = (INK_MUTED, 0.75),
    linewidth = 1.5,
    linestyle = :dash,
)

# Equivalence point annotation (placed in the blank space below the post-equivalence curve)
text!(ax, "Equivalence point\n(V = 25 mL, pH = 7)";
    position = Point2f(v_eq + 1.5, 4.5),
    fontsize  = 11,
    color     = INK_SOFT,
    align     = (:left, :center),
)

# Derivative curve on secondary axis
deriv_line = lines!(ax2, volumes, dph_dv;
    color     = IMPRINT_PALETTE[2],
    linewidth = 2.0,
    linestyle = :dash,
)

# Legend
poly_elem = PolyElement(color = (IMPRINT_PALETTE[6], 0.3), strokewidth = 0)

Legend(
    fig[1, 1],
    [ph_line, deriv_line, poly_elem],
    ["pH curve", "dpH/dV (derivative)", "Transition zone"];
    tellheight      = false,
    tellwidth       = false,
    halign          = :left,
    valign          = :top,
    framecolor      = (INK_SOFT, 0.3),
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK_SOFT,
    labelsize       = 11,
    padding         = (10, 10, 10, 10),
    rowgap          = 4,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
