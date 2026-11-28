# anyplot.ai
# energy-level-atomic: Atomic Energy Level Diagram
# Library: makie 0.24 | Julia 1.11
# Quality: pending | Created: 2026-05-30

using CairoMakie
using Colors
using DataFrames
using Printf

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

# Constants — hydrogen: E_n = -13.6 / n² eV, λ = hc / ΔE with hc = 1240 eV·nm
const RYDBERG_EV = 13.6
const HC_EV_NM   = 1240.0

# Columns: set these to your table's column names
const UPPER_LEVEL = "Upper level n"     # role: from
const LOWER_LEVEL = "Lower level n"     # role: to
const SERIES      = "Spectral series"   # role: group

# Data: replace this block with your own table, for example df = CSV.read("transitions.csv", DataFrame)
n_levels = 6
df = DataFrame(
    UPPER_LEVEL => [2, 3, 4, 3, 4, 5, 4, 5],
    LOWER_LEVEL => [1, 1, 1, 2, 2, 2, 3, 3],
    SERIES => ["Lyman (UV)", "Lyman (UV)", "Lyman (UV)",
               "Balmer (visible)", "Balmer (visible)", "Balmer (visible)",
               "Paschen (IR)", "Paschen (IR)"],
)

# Plot: reads only df and the constants above
levels      = 1:n_levels
energies    = [-RYDBERG_EV / n^2 for n in levels]
# Display position grows with n, so the converging upper levels stay readable
level_y     = Float64.(levels)
ionization_y = n_levels + 0.9
series      = unique(df[!, SERIES])
ytick_pos   = [level_y; ionization_y]
ytick_labels = [@sprintf("%.2f", e) for e in energies]
push!(ytick_labels, "0")

# Schematic horizontal layout: arrows of one series sit together
x_line_start = 0.06
x_line_end   = 0.90
x_label      = 0.92
arrow_dx     = 0.085
arrow_x      = [x_line_start + 0.05 + arrow_dx * (i - 1) + 0.04 * (findfirst(==(s), series) - 1)
                for (i, s) in enumerate(df[!, SERIES])]

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title               = "energy-level-atomic · julia · makie · anyplot.ai",
    titlesize           = 22,
    titlecolor          = INK,
    ylabel              = "Energy (eV)",
    ylabelcolor         = INK,
    ylabelsize          = 18,
    yticklabelcolor     = INK_SOFT,
    yticklabelsize      = 16,
    yticks              = (ytick_pos, ytick_labels),
    backgroundcolor     = PAGE_BG,
    topspinevisible     = false,
    rightspinevisible   = false,
    bottomspinevisible  = false,
    leftspinecolor      = INK_SOFT,
    ytickcolor          = INK_SOFT,
    xticksvisible       = false,
    xticklabelsvisible  = false,
    xgridvisible        = false,
    ygridvisible        = false,
)

# Energy level lines with quantum-number labels
for n in levels
    lines!(ax, [x_line_start, x_line_end], [level_y[n], level_y[n]];
           color = INK_SOFT, linewidth = 2.6)
    text!(ax, x_label, level_y[n]; text = "n = $n", color = INK,
          fontsize = 16, align = (:left, :center))
end

# Ionization limit (n = ∞, 0 eV), dashed to tell it apart from the levels
lines!(ax, [x_line_start, x_line_end], [ionization_y, ionization_y];
       color = INK_MUTED, linewidth = 2.0, linestyle = :dash)
text!(ax, x_label, ionization_y; text = "n = ∞ (ionized)", color = INK_MUTED,
      fontsize = 16, align = (:left, :center))

# Emission arrows, colored by spectral series, with wavelength labels
for i in 1:nrow(df)
    hi, lo = df[i, UPPER_LEVEL], df[i, LOWER_LEVEL]
    color = IMPRINT_PALETTE[findfirst(==(df[i, SERIES]), series)]
    y_from, y_to = level_y[hi], level_y[lo]
    arrows2d!(ax, [arrow_x[i]], [y_from], [0.0], [y_to - y_from];
              color = color, shaftwidth = 3.2, tipwidth = 15, tiplength = 16)
    wavelength = HC_EV_NM / (RYDBERG_EV * (1 / lo^2 - 1 / hi^2))
    text!(ax, arrow_x[i] + 0.02, (y_from + y_to) / 2 + 0.2;
          text = @sprintf("%d nm", round(Int, wavelength)),
          color = color, fontsize = 15, align = (:left, :center))
end

# Series legend
Legend(fig[1, 1],
       [LineElement(color = IMPRINT_PALETTE[i], linewidth = 4) for i in eachindex(series)],
       series;
       tellwidth = false, tellheight = false,
       halign = :center, valign = :bottom, orientation = :horizontal,
       framevisible = false, labelcolor = INK, labelsize = 16, padding = (0, 0, 8, 8))

xlims!(ax, 0.0, 1.08)
ylims!(ax, 0.3, ionization_y + 0.5)

save("plot-$(THEME).png", fig; px_per_unit = 2)
