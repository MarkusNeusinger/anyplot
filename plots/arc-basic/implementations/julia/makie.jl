# anyplot.ai
# arc-basic: Basic Arc Diagram
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-05-30

using CairoMakie
using Colors

# Theme tokens — Imprint palette
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const BRAND  = colorant"#009E73"  # Imprint position 1 — within-group edges
const ACCENT = colorant"#C475FD"  # Imprint position 2 — cross-group edges

# Data — research collaboration network (12 researchers, 17 co-authorship links)
const node_names = [
    "Alice", "Bob", "Carol", "Dave",
    "Eve", "Frank", "Grace", "Hank",
    "Iris", "Jack", "Kim", "Leo",
]
const n_nodes = length(node_names)

# Groups: A = 1–4, B = 5–8, C = 9–12
# (src, tgt, weight, cross_group)
const edges = [
    (1, 2, 5, false), (1, 3, 4, false), (2, 4, 3, false), (3, 4, 4, false),
    (5, 6, 4, false), (5, 7, 5, false), (6, 8, 3, false), (7, 8, 4, false),
    (9, 10, 5, false), (9, 11, 3, false), (10, 12, 4, false), (11, 12, 3, false),
    (2, 5, 2, true), (4, 7, 2, true), (8, 9, 1, true), (3, 11, 1, true), (1, 12, 1, true),
]

const node_x     = Float64.(0:(n_nodes - 1))
const max_weight = maximum(w for (_, _, w, _) in edges)

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

# Arcs — color-coded by edge type; weight encodes opacity and linewidth
for (src, tgt, weight, is_cross) in edges
    xi, xj = node_x[src], node_x[tgt]
    cx = (xi + xj) / 2.0
    r  = abs(xj - xi) / 2.0
    h  = r * 0.55

    t     = range(0.0, π; length = 300)
    arc_x = cx .+ r .* cos.(t)
    arc_y = h .* sin.(t)

    alpha = 0.3 + 0.5 * (weight / max_weight)
    lw    = 1.0 + 2.5 * (weight / max_weight)
    col   = is_cross ? ACCENT : BRAND

    lines!(ax, arc_x, arc_y; color = (col, alpha), linewidth = lw)
end

# Horizontal baseline
lines!(ax, [node_x[1] - 0.5, node_x[end] + 0.5], [0.0, 0.0];
       color = INK_SOFT, linewidth = 1.5)

# Node dots
scatter!(ax, node_x, zeros(n_nodes);
         color       = BRAND,
         markersize  = 16,
         strokewidth = 1.5,
         strokecolor = PAGE_BG)

# Node labels
for (i, name) in enumerate(node_names)
    text!(ax, node_x[i], -0.12;
          text     = name,
          fontsize = Float32(13),
          color    = INK_SOFT,
          align    = (:center, :top))
end

ylims!(ax, -0.65, 3.8)
xlims!(ax, -0.8, 12.0)

# Makie Legend with LineElement + MarkerElement — Makie-idiomatic typed legend entries
leg_elements = [
    [LineElement(color = (BRAND, 0.8), linewidth = 3.5)],
    [LineElement(color = (ACCENT, 0.8), linewidth = 2.0)],
    [MarkerElement(color = BRAND, marker = :circle, markersize = 14,
                   strokewidth = 1.5, strokecolor = PAGE_BG)],
]
leg_labels = ["Within-group (weight 3–5)", "Cross-group (weight 1–2)", "Researcher"]

Legend(
    fig[1, 2],
    leg_elements,
    leg_labels;
    title           = "Connection type",
    titlesize       = 13,
    labelsize       = 12,
    titlecolor      = INK,
    labelcolor      = INK_SOFT,
    framevisible    = false,
    backgroundcolor = PAGE_BG,
    tellheight      = false,
    patchsize       = (24, 10),
    padding         = (8, 8, 8, 8),
    rowgap          = 6,
)

colsize!(fig.layout, 1, Relative(0.80))

save("plot-$(THEME).png", fig; px_per_unit = 2)
