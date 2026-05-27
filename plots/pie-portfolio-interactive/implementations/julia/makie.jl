# anyplot.ai
# pie-portfolio-interactive: Interactive Portfolio Allocation Chart
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 83/100 | Created: 2026-05-27

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

const ANYPLOT_PALETTE = [
    colorant"#009E73",  # 1 — brand green  (Equities)
    colorant"#C475FD",  # 2 — lavender     (Fixed Income)
    colorant"#4467A3",  # 3 — blue         (Alternatives)
    colorant"#BD8233",  # 4 — ochre        (Cash)
]

# Data — sample $100M multi-asset portfolio
categories = ["Equities", "Fixed Income", "Alternatives", "Cash"]
weights    = [40.0, 30.0, 20.0, 10.0]   # percentages, sum = 100

# Cumulative angles: clockwise from 12 o'clock (π/2)
cum_angles = [π / 2]
for w in weights
    push!(cum_angles, last(cum_angles) - w / 100.0 * 2π)
end

# Donut geometry
r_inner = 0.38
r_outer = 1.00
r_label = 1.22
n_arc   = 80

# Title (54 chars < 67 — no scaling needed, titlesize = 20 is fine)
title_str = "pie-portfolio-interactive · julia · makie · anyplot.ai"

# Figure — square canvas (2400 × 2400 at px_per_unit=2)
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title           = title_str,
    titlesize       = 20,
    titlecolor      = INK,
    aspect          = DataAspect(),
    backgroundcolor = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)
xlims!(ax, -1.42, 1.42)
ylims!(ax, -1.42, 1.42)

# Donut slices and percentage labels
for i in 1:length(categories)
    θ         = range(cum_angles[i], cum_angles[i + 1]; length = n_arc)
    outer_pts = [Point2f(cos(t) * r_outer, sin(t) * r_outer) for t in θ]
    inner_pts = [Point2f(cos(t) * r_inner, sin(t) * r_inner) for t in reverse(θ)]
    poly!(ax, vcat(outer_pts, inner_pts);
          color       = ANYPLOT_PALETTE[i],
          strokewidth = 4,
          strokecolor = PAGE_BG)

    mid_θ = (cum_angles[i] + cum_angles[i + 1]) / 2
    abs_val = Int(round(weights[i]))   # $1M per percentage point of $100M total
    label_text = string(abs_val) * "%\n\$" * string(abs_val) * "M"
    # Slightly larger label for the dominant slice to create focal-point emphasis
    label_size = i == 1 ? 17 : 15
    text!(ax, cos(mid_θ) * r_label, sin(mid_θ) * r_label;
          text     = label_text,
          fontsize  = label_size,
          color    = INK,
          align    = (:center, :center))
end

# Center labels in the donut hole
text!(ax, 0.0, 0.09;
      text     = "Portfolio",
      fontsize = 18,
      color    = INK,
      align    = (:center, :center))
text!(ax, 0.0, -0.10;
      text     = "\$100M AUM",
      fontsize = 14,
      color    = INK_SOFT,
      align    = (:center, :center))

# Horizontal legend below the chart
legend_entries = [PolyElement(color = ANYPLOT_PALETTE[i], strokewidth = 0) for i in 1:length(categories)]
legend_labels  = [categories[i] * "  " * string(Int(round(weights[i]))) * "%  \$" * string(Int(round(weights[i]))) * "M" for i in 1:length(categories)]

Legend(
    fig[2, 1], legend_entries, legend_labels;
    orientation     = :horizontal,
    framevisible    = false,
    labelcolor      = INK,
    labelsize       = 14,
    backgroundcolor = PAGE_BG,
    tellwidth       = false,
    padding         = (0, 0, 6, 6),
)

rowgap!(fig.layout, 1, 4)

save("plot-$(THEME).png", fig; px_per_unit = 2)
