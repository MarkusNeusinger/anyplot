# anyplot.ai
# hive-basic: Basic Hive Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome") ----
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — Core (brand green, always first series)
    colorant"#C475FD",  # 2 — Utility (lavender)
    colorant"#4467A3",  # 3 — Interface (blue)
]

# --- Data: a software module dependency network -----------------------------
# 3 radial axes grouped by module type; node position along its axis encodes
# in-network degree so structurally similar modules always land at the same
# radius, making the plot directly comparable across versions/runs.
axis_names = ["Core", "Utility", "Interface"]
n_per_axis = 12
n_nodes = n_per_axis * length(axis_names)
node_axis = repeat(1:length(axis_names), inner = n_per_axis)  # 1=Core 2=Utility 3=Interface

# Dependency edges only connect modules on *different* axes — the classic
# hive-plot convention where axis membership, not adjacency, tells the story.
edges = Tuple{Int, Int}[]
for i in 1:n_nodes, j in (i + 1):n_nodes
    if node_axis[i] != node_axis[j]
        pair = sort([node_axis[i], node_axis[j]])
        edge_probability = pair == [1, 2] ? 0.22 : pair == [2, 3] ? 0.18 : 0.08
        if rand() < edge_probability
            push!(edges, (i, j))
        end
    end
end

degree = zeros(Int, n_nodes)
for (source, target) in edges
    degree[source] += 1
    degree[target] += 1
end

# --- Radial layout (shared scale across all 3 axes) --------------------------
const MIN_R = 0.15
const MAX_R = 0.95
axis_angles = deg2rad.([90.0, 210.0, 330.0])  # up, lower-left, lower-right

node_x = zeros(n_nodes)
node_y = zeros(n_nodes)
for axis_idx in 1:length(axis_names)
    members = findall(==(axis_idx), node_axis)
    ranked = sort(members, by = n -> (degree[n], n))  # low → high degree, stable tie-break
    radii = range(MIN_R, MAX_R, length = length(ranked))
    angle = axis_angles[axis_idx]
    for (rank, n) in enumerate(ranked)
        node_x[n] = radii[rank] * cos(angle)
        node_y[n] = radii[rank] * sin(angle)
    end
end

# --- Plot ---------------------------------------------------------------------
title_text = "hive-basic · julia · makie · anyplot.ai"

fig = Figure(
    size = (1200, 1200),
    fontsize = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title = title_text,
    titlesize = 20,
    titlecolor = INK,
    backgroundcolor = PAGE_BG,
    aspect = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)
limits!(ax, -1.2, 1.2, -1.2, 1.2)

# Axis reference lines (subtle, structural — not data)
for angle in axis_angles
    lines!(
        ax, [0.0, MAX_R * cos(angle)], [0.0, MAX_R * sin(angle)];
        color = (INK_SOFT, 0.5), linewidth = 1.5,
    )
end

# Axis tip labels
label_r = MAX_R + 0.14
for (i, angle) in enumerate(axis_angles)
    text!(
        ax, label_r * cos(angle), label_r * sin(angle);
        text = axis_names[i], color = INK, fontsize = 16,
        align = (:center, :center),
    )
end

# Edges — quadratic Bezier curves bowed toward the origin (never through
# nodes on the third axis), muted so the categorical node colors lead
for (source, target) in edges
    angle_a = axis_angles[node_axis[source]]
    angle_b = axis_angles[node_axis[target]]
    control_angle = atan(sin(angle_a) + sin(angle_b), cos(angle_a) + cos(angle_b))
    control_r = 0.32 * MAX_R
    p0x, p0y = node_x[source], node_y[source]
    p1x, p1y = control_r * cos(control_angle), control_r * sin(control_angle)
    p2x, p2y = node_x[target], node_y[target]
    t = range(0.0, 1.0, length = 30)
    curve_x = @. (1 - t)^2 * p0x + 2 * (1 - t) * t * p1x + t^2 * p2x
    curve_y = @. (1 - t)^2 * p0y + 2 * (1 - t) * t * p1y + t^2 * p2y
    lines!(ax, curve_x, curve_y; color = (INK_SOFT, 0.3), linewidth = 1.3)
end

# Nodes — colored by axis category (Imprint palette, first series always brand green)
for (i, name) in enumerate(axis_names)
    members = findall(==(i), node_axis)
    scatter!(
        ax, node_x[members], node_y[members];
        color = IMPRINT_PALETTE[i], markersize = 16,
        strokewidth = 1, strokecolor = PAGE_BG, label = name,
    )
end

axislegend(ax; position = :lt, framevisible = false, labelcolor = INK, patchsize = (18, 18))

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
