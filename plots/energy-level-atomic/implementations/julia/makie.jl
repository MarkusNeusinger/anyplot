# anyplot.ai
# energy-level-atomic: Atomic Energy Level Diagram
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-05-30

using CairoMakie
using Colors

# Theme tokens — Imprint palette, theme-adaptive chrome
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 brand green
    colorant"#C475FD",  # 2 lavender
    colorant"#4467A3",  # 3 blue
    colorant"#BD8233",  # 4 ochre
    colorant"#AE3030",  # 5 matte red
    colorant"#2ABCCD",  # 6 cyan
    colorant"#954477",  # 7 rose
    colorant"#99B314",  # 8 lime
]

# Hydrogen atom energy levels: E_n = -13.6 / n² eV (n = 1 to 4 + ionization)
energies = [-13.6 / n^2 for n in 1:4]

# Emission transitions (from_n, to_n) — downward arrows
lyman_transitions   = [(2, 1), (3, 1), (4, 1)]   # UV photons  → n = 1
balmer_transitions  = [(3, 2), (4, 2)]            # Visible     → n = 2
paschen_transitions = [(4, 3)]                    # Infrared    → n = 3

# Pseudo-x layout: energy lines span [x_line_start, x_line_end]; labels at x_label
x_line_start    = 0.10
x_line_end      = 0.82
x_label         = 0.84
lyman_xs        = [0.20, 0.30, 0.40]
balmer_xs       = [0.54, 0.64]
paschen_xs      = [0.74]

lyman_color   = IMPRINT_PALETTE[1]   # brand green — Lyman UV series
balmer_color  = IMPRINT_PALETTE[2]   # lavender — Balmer visible series
paschen_color = IMPRINT_PALETTE[3]   # blue — Paschen infrared series

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title               = "energy-level-atomic · julia · makie · anyplot.ai",
    titlesize           = 20,
    titlecolor          = INK,
    ylabel              = "Energy (eV)",
    ylabelcolor         = INK,
    ylabelsize          = 14,
    yticklabelcolor     = INK_SOFT,
    yticklabelsize      = 12,
    backgroundcolor     = PAGE_BG,
    topspinevisible     = false,
    rightspinevisible   = false,
    bottomspinevisible  = false,
    leftspinecolor      = INK_SOFT,
    ytickcolor          = INK_SOFT,
    xticksvisible       = false,
    xticklabelsvisible  = false,
    xgridvisible        = false,
    ygridcolor          = RGBAf(Float32(red(INK)), Float32(green(INK)), Float32(blue(INK)), 0.12f0),
)

# Energy level horizontal lines with quantum-number labels
for n in 1:4
    e = energies[n]
    lines!(ax, [x_line_start, x_line_end], [e, e];
           color = INK_SOFT, linewidth = 2.2)
    text!(ax, x_label, e;
          text     = "n = $n",
          color    = INK,
          fontsize = 12,
          align    = (:left, :center))
end

# Ionization continuum reference line
lines!(ax, [x_line_start, x_line_end], [0.0, 0.0];
       color     = INK_MUTED,
       linewidth = 1.5,
       linestyle = :dash)
text!(ax, x_label, 0.0;
      text     = "n = ∞\n(ionized)",
      color    = INK_MUTED,
      fontsize = 11,
      align    = (:left, :center))

# Lyman series emission arrows (to n = 1, UV photons)
for (i, (fn, tn)) in enumerate(lyman_transitions)
    xp = lyman_xs[i]
    arrows!(ax, [xp], [energies[fn]], [0.0], [energies[tn] - energies[fn]];
            color     = lyman_color,
            arrowsize = 14,
            linewidth = 2.4)
end

# Balmer series emission arrows (to n = 2, visible photons)
for (i, (fn, tn)) in enumerate(balmer_transitions)
    xp = balmer_xs[i]
    arrows!(ax, [xp], [energies[fn]], [0.0], [energies[tn] - energies[fn]];
            color     = balmer_color,
            arrowsize = 14,
            linewidth = 2.4)
end

# Paschen series emission arrow (to n = 3, infrared photons)
for (i, (fn, tn)) in enumerate(paschen_transitions)
    xp = paschen_xs[i]
    arrows!(ax, [xp], [energies[fn]], [0.0], [energies[tn] - energies[fn]];
            color     = paschen_color,
            arrowsize = 14,
            linewidth = 2.4)
end

# Series labels in the open space below n = 1
text!(ax, 0.30, -14.8;
      text     = "Lyman (UV)",
      color    = lyman_color,
      fontsize = 12,
      align    = (:center, :center))
text!(ax, 0.59, -14.8;
      text     = "Balmer (visible)",
      color    = balmer_color,
      fontsize = 12,
      align    = (:center, :center))
text!(ax, 0.74, -14.8;
      text     = "Paschen (IR)",
      color    = paschen_color,
      fontsize = 12,
      align    = (:center, :center))

xlims!(ax, 0.0, 1.06)
ylims!(ax, -15.5, 1.0)

save("plot-$(THEME).png", fig; px_per_unit = 2)
