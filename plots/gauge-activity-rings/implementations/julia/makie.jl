# anyplot.ai
# gauge-activity-rings: Activity Rings Progress Chart
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-06-14

using CairoMakie
using Colors
using Statistics

# Theme tokens
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (first series, always)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data — daily fitness tracker: Move, Exercise, Stand
const metrics     = ["Move",  "Exercise", "Stand"]
const val_current = [420,      25,          9]
const val_goal    = [600,      30,         12]
const val_unit    = ["kcal",  "min",       "hr"]
const ring_radii  = [0.68,    0.50,        0.32]
const ring_colors = IMPRINT_PALETTE[1:3]

const fractions = val_current ./ val_goal     # [0.70, 0.833, 0.75]
const avg_pct   = round(Int, mean(fractions) * 100)   # 76

# Figure — square canvas → 2400 × 2400 output
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "gauge-activity-rings · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    backgroundcolor    = PAGE_BG,
    aspect             = DataAspect(),
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
    xticksvisible      = false,
    yticksvisible      = false,
    xticklabelsvisible = false,
    yticklabelsvisible = false,
)

limits!(ax, -1.10, 1.10, -1.10, 1.10)

# Ring drawing parameters
const N_PTS = 360
const LW    = 46   # device px → ×2 = 92 output px on 2400-px canvas

# Draw rings outer → inner
for (r, frac, col) in zip(ring_radii, fractions, ring_colors)
    # Faint background track — full circle; higher opacity in dark for contrast
    bg_alpha = THEME == "dark" ? 0.22f0 : 0.12f0
    θ_bg = range(0.0, 2π, length = N_PTS + 1)
    lines!(ax, r .* cos.(θ_bg), r .* sin.(θ_bg);
           linewidth = LW, color = (col, bg_alpha))

    # Progress arc — starts at 12 o'clock (π/2), sweeps clockwise
    sweep = min(frac, 1.0) * 2π
    n_arc = max(4, round(Int, frac * N_PTS))
    θ_arc = range(π / 2, π / 2 - sweep; length = n_arc)
    x_arc = r .* cos.(θ_arc)
    y_arc = r .* sin.(θ_arc)
    lines!(ax, x_arc, y_arc; linewidth = LW, color = col)

    # Circular end caps that match the line width for a rounded look
    scatter!(ax, [x_arc[1]],   [y_arc[1]];   color = col, markersize = LW, strokewidth = 0)
    scatter!(ax, [x_arc[end]], [y_arc[end]]; color = col, markersize = LW, strokewidth = 0)
end

# Center summary text
text!(ax, 0.0, 0.10;
      text     = "$(avg_pct)%",
      fontsize = 60,
      color    = INK,
      align    = (:center, :center))
text!(ax, 0.0, -0.12;
      text     = "COMPLETE",
      fontsize = 18,
      color    = INK_MUTED,
      align    = (:center, :center))

# Bottom legend strip — color dot + metric name + value/goal
const x_pos = [-0.52, 0.0, 0.52]
const y_lbl = -0.84
const y_val = -0.97

for (i, (name, cur, goal, unit, col)) in
        enumerate(zip(metrics, val_current, val_goal, val_unit, ring_colors))
    xc = x_pos[i]
    scatter!(ax, [xc - 0.14], [(y_lbl + y_val) / 2];
             color = col, markersize = 22, strokewidth = 0)
    text!(ax, xc - 0.04, y_lbl;
          text = name, fontsize = 16, color = INK, align = (:left, :baseline))
    text!(ax, xc - 0.04, y_val;
          text = "$(cur) / $(goal) $(unit)", fontsize = 13, color = INK_SOFT,
          align = (:left, :baseline))
end

# Save — px_per_unit = 2 doubles the resolution to 2400 × 2400
save("plot-$(THEME).png", fig; px_per_unit = 2)
