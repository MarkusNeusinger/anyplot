# anyplot.ai
# network-force-directed: Force-Directed Graph
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-07-01

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

# Data: academic research collaboration network (4 departments, 32 researchers)
n_nodes    = 32
dept_names = ["Machine Learning", "Networks", "Databases", "Systems"]
node_dept  = vcat([fill(d, 8) for d in 1:4]...)

edges = Tuple{Int,Int}[]

# Dense within-department edges
for d in 1:4
    members = findall(==(d), node_dept)
    for i in members, j in members
        if i < j && rand() < 0.65
            push!(edges, (i, j))
        end
    end
end

# Sparse cross-department bridges
for (d1, d2) in [(1, 2), (2, 3), (3, 4), (1, 3), (1, 4), (2, 4)]
    m1 = findall(==(d1), node_dept)
    m2 = findall(==(d2), node_dept)
    for _ in 1:2
        push!(edges, (rand(m1), rand(m2)))
    end
end

unique!(edges)

degree = zeros(Int, n_nodes)
for (u, v) in edges
    degree[u] += 1
    degree[v] += 1
end

# Force-directed layout — Fruchterman-Reingold algorithm
pos_x = randn(n_nodes) .* 3.0
pos_y = randn(n_nodes) .* 3.0

k = sqrt(100.0 / n_nodes)  # ideal spring length

for iter in 0:299
    t_step = max(1.0 * 0.97^iter, 0.005)  # cooling schedule

    dx = zeros(n_nodes)
    dy = zeros(n_nodes)

    # Repulsive forces between all node pairs
    for i in 1:n_nodes, j in 1:n_nodes
        if i != j
            δx = pos_x[i] - pos_x[j]
            δy = pos_y[i] - pos_y[j]
            d  = max(sqrt(δx^2 + δy^2), 1e-4)
            f  = k^2 / d
            dx[i] += δx / d * f
            dy[i] += δy / d * f
        end
    end

    # Attractive forces along edges
    for (u, v) in edges
        δx = pos_x[u] - pos_x[v]
        δy = pos_y[u] - pos_y[v]
        d  = max(sqrt(δx^2 + δy^2), 1e-4)
        f  = d^2 / k
        dx[u] -= δx / d * f
        dy[u] -= δy / d * f
        dx[v] += δx / d * f
        dy[v] += δy / d * f
    end

    # Update positions clipped to temperature
    for i in 1:n_nodes
        disp = sqrt(dx[i]^2 + dy[i]^2)
        if disp > 0
            pos_x[i] += dx[i] / disp * min(disp, t_step)
            pos_y[i] += dy[i] / disp * min(disp, t_step)
        end
    end
end

# Normalise to [0.05, 0.95]
pos_x = 0.05 .+ 0.90 .* (pos_x .- minimum(pos_x)) ./ (maximum(pos_x) - minimum(pos_x))
pos_y = 0.05 .+ 0.90 .* (pos_y .- minimum(pos_y)) ./ (maximum(pos_y) - minimum(pos_y))

node_colors = [IMPRINT_PALETTE[d] for d in node_dept]
node_sizes  = 12.0 .+ degree .* 2.5

# Title — 51 chars, below the 67-char baseline so no scaling needed
const TITLE        = "network-force-directed · julia · makie · anyplot.ai"
const TITLE_SIZE   = 22

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = TITLE,
    titlesize          = TITLE_SIZE,
    titlecolor         = INK,
    backgroundcolor    = PAGE_BG,
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

limits!(ax, 0, 1, 0, 1)

# Draw edges
for (u, v) in edges
    lines!(ax, [pos_x[u], pos_x[v]], [pos_y[u], pos_y[v]];
           color = (INK_SOFT, 0.25), linewidth = 1.0)
end

# Draw nodes (size scales with degree)
scatter!(ax, pos_x, pos_y;
         color       = node_colors,
         markersize  = node_sizes,
         strokewidth = 1.5,
         strokecolor = PAGE_BG)

# Legend
legend_elems = [
    MarkerElement(
        color       = IMPRINT_PALETTE[i],
        marker      = :circle,
        markersize  = 16,
        strokewidth = 0,
    )
    for i in 1:4
]

Legend(
    fig[1, 2], legend_elems, dept_names;
    title        = "Department",
    titlesize    = 13,
    titlecolor   = INK,
    labelsize    = 12,
    labelcolor   = INK,
    framevisible    = true,
    framecolor      = (INK_SOFT, 0.3),
    backgroundcolor = ELEVATED_BG,
)

colsize!(fig.layout, 1, Relative(0.82))

# Annotation: explain the node-size encoding
text!(ax, 0.01, 0.01; text = "Node size ∝ degree (connections)",
      fontsize = 10, color = INK_SOFT, align = (:left, :bottom))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
