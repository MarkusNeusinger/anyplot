# anyplot.ai
# arc-basic: Basic Arc Diagram
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-05-30

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens — Imprint palette
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const BRAND = colorant"#009E73"  # Imprint palette position 1 — always first series

# Data — research collaboration network (12 researchers, 17 co-authorship links)
const node_names = [
    "Alice", "Bob", "Carol", "Dave",
    "Eve", "Frank", "Grace", "Hank",
    "Iris", "Jack", "Kim", "Leo",
]
const n_nodes = length(node_names)

# (src, tgt, weight) — 1-indexed; weight = number of co-authored papers
const edges = [
    (1, 2, 5), (1, 3, 4), (2, 4, 3), (3, 4, 4),             # Group A internal
    (5, 6, 4), (5, 7, 5), (6, 8, 3), (7, 8, 4),             # Group B internal
    (9, 10, 5), (9, 11, 3), (10, 12, 4), (11, 12, 3),       # Group C internal
    (2, 5, 2), (4, 7, 2), (8, 9, 1), (3, 11, 1), (1, 12, 1), # cross-group
]

const node_x     = Float64.(0:(n_nodes - 1))
const max_weight = maximum(w for (_, _, w) in edges)

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    backgroundcolor    = PAGE_BG,
    title              = "arc-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
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

# Draw arcs — parametric semicircles, opacity and linewidth scaled by weight
for (src, tgt, weight) in edges
    xi, xj = node_x[src], node_x[tgt]
    cx = (xi + xj) / 2.0
    r  = abs(xj - xi) / 2.0
    h  = r * 0.55

    t     = range(0.0, π; length = 300)
    arc_x = cx .+ r .* cos.(t)
    arc_y = h .* sin.(t)

    alpha = 0.3 + 0.5 * (weight / max_weight)
    lw    = 1.0 + 2.5 * (weight / max_weight)

    lines!(ax, arc_x, arc_y; color = (BRAND, alpha), linewidth = lw)
end

# Horizontal baseline
lines!(ax, [node_x[1] - 0.5, node_x[end] + 0.5], [0.0, 0.0];
       color = INK_SOFT, linewidth = 1.5)

# Nodes
scatter!(ax, node_x, zeros(n_nodes);
         color       = BRAND,
         markersize  = 16,
         strokewidth = 1.5,
         strokecolor = PAGE_BG)

# Node labels
for (i, name) in enumerate(node_names)
    text!(ax, node_x[i], -0.12;
          text     = name,
          fontsize = Float32(11),
          color    = INK_SOFT,
          align    = (:center, :top))
end

ylims!(ax, -0.9, 3.8)
xlims!(ax, -0.8, 12.0)

save("plot-$(THEME).png", fig; px_per_unit = 2)
