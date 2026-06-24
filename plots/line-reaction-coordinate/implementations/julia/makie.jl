# anyplot.ai
# line-reaction-coordinate: Reaction Coordinate Energy Diagram
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
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]

# Data — single-step exothermic reaction
E_r  = 50.0   # reactant energy level (kJ/mol)
E_ts = 120.0  # transition state energy (kJ/mol)
E_p  = 20.0   # product energy level (kJ/mol)

x_peak = 0.38  # transition state position on [0, 1]
sigma  = 0.14  # Gaussian half-width controls barrier sharpness

n_pts = 300
x_vals = collect(LinRange(0.0, 1.0, n_pts))
linear_baseline = E_r .+ (E_p - E_r) .* x_vals
barrier_height = E_ts - (E_r + (E_p - E_r) * x_peak)
energy = linear_baseline .+ barrier_height .* exp.(-(x_vals .- x_peak).^2 ./ (2 * sigma^2))

E_a     = Int(E_ts - E_r)  # activation energy = 70 kJ/mol
delta_H = Int(E_p - E_r)   # enthalpy change = -30 kJ/mol

# Figure
title_str = "line-reaction-coordinate · julia · makie · anyplot.ai"

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Reaction Coordinate",
    ylabel             = "Potential Energy (kJ/mol)",
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
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    xticklabelsvisible = false,
    xticksvisible      = false,
)

# Reaction energy curve
lines!(ax, x_vals, energy; color = BRAND, linewidth = 3.5)

# Horizontal dashed reference lines at reactant and product energy levels
hlines!(ax, E_r; color = INK_MUTED, linewidth = 1.2, linestyle = :dash)
hlines!(ax, E_p; color = INK_MUTED, linewidth = 1.2, linestyle = :dash)

# Axis limits — extra right margin for annotation labels
xlims!(ax, -0.05, 1.20)
ylims!(ax, E_p - 15.0, E_ts + 30.0)

# Labels: reactants, transition state, products
text!(ax, 0.04, E_r + 6.0;
      text  = "Reactants\n50 kJ/mol",
      color = INK, fontsize = 13, align = (:left, :bottom))
text!(ax, x_peak, E_ts + 8.0;
      text  = "Transition State ‡\n120 kJ/mol",
      color = INK, fontsize = 13, align = (:center, :bottom))
text!(ax, 0.94, E_p + 6.0;
      text  = "Products\n20 kJ/mol",
      color = INK, fontsize = 13, align = (:right, :bottom))

# Activation energy (Eₐ) double-headed arrow: from reactant level to transition state
x_ea = 0.62
arrows!(ax, [x_ea], [E_r], [0.0], [E_ts - E_r]; color = INK, linewidth = 1.5)
arrows!(ax, [x_ea], [E_ts], [0.0], [-(E_ts - E_r)]; color = INK, linewidth = 1.5)
text!(ax, x_ea + 0.03, (E_r + E_ts) / 2.0;
      text  = "Eₐ = $(E_a) kJ/mol",
      color = INK, fontsize = 12, align = (:left, :center))

# Enthalpy change (ΔH) double-headed arrow: between reactant and product levels
x_dh = 0.85
arrows!(ax, [x_dh], [E_p], [0.0], [E_r - E_p]; color = INK, linewidth = 1.5)
arrows!(ax, [x_dh], [E_r], [0.0], [-(E_r - E_p)]; color = INK, linewidth = 1.5)
text!(ax, x_dh + 0.03, (E_r + E_p) / 2.0;
      text  = "ΔH = $(delta_H) kJ/mol",
      color = INK, fontsize = 12, align = (:left, :center))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
