# anyplot.ai
# dendrogram-radial: Radial Dendrogram
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 79/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green, Immune module
    colorant"#C475FD",  # 2 — lavender, Metabolic module
    colorant"#4467A3",  # 3 — blue, Neural module
    colorant"#BD8233",  # 4 — ochre, Cardiac module
]

# Data — synthetic gene-expression profiles for four functional modules,
# clustered hierarchically from scratch (no Clustering.jl in the CI runtime).
Random.seed!(42)

group_names = ["Immune", "Metabolic", "Neural", "Cardiac"]
group_prefixes = ["IMM", "MET", "NEU", "CAR"]
group_means = [
    [3.0, 0.5, 0.2, 2.8, 0.4, 3.2],
    [0.3, 3.1, 2.9, 0.5, 3.0, 0.2],
    [2.9, 2.8, 0.3, 0.4, 0.3, 0.5],
    [0.4, 0.3, 3.0, 3.1, 2.9, 2.8],
]
n_per_group = 10
n = n_per_group * length(group_names)

features = Matrix{Float64}(undef, n, 6)
leaf_group = Vector{Int}(undef, n)
labels = Vector{String}(undef, n)

for g in 1:length(group_names), k in 1:n_per_group
    idx = (g - 1) * n_per_group + k
    features[idx, :] = group_means[g] .+ 0.7 .* randn(6)
    leaf_group[idx] = g
    labels[idx] = group_prefixes[g] * "-" * lpad(k, 2, "0")
end

# Agglomerative clustering (UPGMA / average linkage) via the Lance-Williams
# update — produces a scipy-style merge sequence (id1, id2, distance, new_id)
# without needing an external clustering package.
dist = Dict{Tuple{Int,Int},Float64}()
for i in 1:n, j in (i + 1):n
    dist[(i, j)] = sqrt(sum((features[i, :] .- features[j, :]) .^ 2))
end

sizes = Dict{Int,Int}(i => 1 for i in 1:n)
active = collect(1:n)
next_id = n + 1
merges = Tuple{Int,Int,Float64,Int}[]

while length(active) > 1
    best_d = Inf
    best_i = 0
    best_j = 0
    for a in 1:(length(active) - 1), b in (a + 1):length(active)
        p, q = active[a], active[b]
        key = p < q ? (p, q) : (q, p)
        d = dist[key]
        if d < best_d
            best_d = d
            best_i = p
            best_j = q
        end
    end
    ni, nj = sizes[best_i], sizes[best_j]
    nid = next_id
    for k in active
        if k == best_i || k == best_j
            continue
        end
        key_ik = best_i < k ? (best_i, k) : (k, best_i)
        key_jk = best_j < k ? (best_j, k) : (k, best_j)
        key_nk = nid < k ? (nid, k) : (k, nid)
        dist[key_nk] = (ni * dist[key_ik] + nj * dist[key_jk]) / (ni + nj)
    end
    sizes[nid] = ni + nj
    push!(merges, (best_i, best_j, best_d, nid))
    filter!(x -> x != best_i && x != best_j, active)
    push!(active, nid)
    global next_id += 1
end

root_id = merges[end][4]
max_height = merges[end][3]

children = Dict{Int,Tuple{Int,Int}}()
for (i, j, d, nid) in merges
    children[nid] = (i, j)
end

# Leaf order (iterative DFS, left child first) keeps sibling subtrees
# angularly contiguous so branches never cross.
order = Int[]
stack = [root_id]
while !isempty(stack)
    node = pop!(stack)
    if node <= n
        push!(order, node)
    else
        i, j = children[node]
        push!(stack, j)
        push!(stack, i)
    end
end

# Angle (leaves equally spaced, small gap at the top) and radius
# (proportional to merge distance, root at the center) per node.
R_max = 1.0
gap = deg2rad(6)
angle_span = 2 * pi - gap
start_angle = pi / 2 + gap / 2
angle_step = angle_span / (n - 1)

node_angle = Dict{Int,Float64}()
node_radius = Dict{Int,Float64}()
for (p, leaf) in enumerate(order)
    node_angle[leaf] = start_angle + angle_step * (p - 1)
    node_radius[leaf] = R_max
end
for (i, j, d, nid) in merges
    node_angle[nid] = (node_angle[i] + node_angle[j]) / 2
    node_radius[nid] = R_max * (1 - d / max_height)
end

# Pure-cluster color propagation: a node keeps its module color while every
# leaf beneath it shares the same module, else it falls back to neutral ink
# (mirrors the standard dendrogram color_threshold convention).
node_group = Dict{Int,Int}()
for leaf in 1:n
    node_group[leaf] = leaf_group[leaf]
end
for (i, j, d, nid) in merges
    gi, gj = node_group[i], node_group[j]
    node_group[nid] = gi == gj ? gi : 0
end

# Plot — see default-style-guide.md "Visual Sizing Defaults" for the canvas + sizing values
title_text = "dendrogram-radial · julia · makie · anyplot.ai"

fig = Figure(
    resolution = (1200, 1200),
    fontsize = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title = title_text,
    titlesize = 26,
    titlecolor = INK,
    aspect = DataAspect(),
    backgroundcolor = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)

L = 1.32
limits!(ax, -L, L, -L, L)

for (i, j, d, nid) in merges
    rp = node_radius[nid]
    ai, aj = node_angle[i], node_angle[j]

    color_i = node_group[i] == 0 ? INK_SOFT : IMPRINT_PALETTE[node_group[i]]
    xi1, yi1 = node_radius[i] * cos(ai), node_radius[i] * sin(ai)
    xi2, yi2 = rp * cos(ai), rp * sin(ai)
    lines!(ax, [xi1, xi2], [yi1, yi2]; color = color_i, linewidth = 2.5)

    color_j = node_group[j] == 0 ? INK_SOFT : IMPRINT_PALETTE[node_group[j]]
    xj1, yj1 = node_radius[j] * cos(aj), node_radius[j] * sin(aj)
    xj2, yj2 = rp * cos(aj), rp * sin(aj)
    lines!(ax, [xj1, xj2], [yj1, yj2]; color = color_j, linewidth = 2.5)

    color_nid = node_group[nid] == 0 ? INK_SOFT : IMPRINT_PALETTE[node_group[nid]]
    a_lo, a_hi = ai < aj ? (ai, aj) : (aj, ai)
    arc!(ax, Point2f(0, 0), rp, a_lo, a_hi; color = color_nid, linewidth = 2.5)
end

# Color-coded outer ring: contiguous leaf runs sharing a module, one arc per run.
ring_r = R_max * 1.05
half_step = angle_step / 2
seg_start = 1
for p in 2:(n + 1)
    if p == n + 1 || leaf_group[order[p]] != leaf_group[order[seg_start]]
        g = leaf_group[order[seg_start]]
        a0 = node_angle[order[seg_start]] - half_step
        a1 = node_angle[order[p - 1]] + half_step
        arc!(ax, Point2f(0, 0), ring_r, a0, a1; color = IMPRINT_PALETTE[g], linewidth = 6)
        global seg_start = p
    end
end

leaf_x = [R_max * cos(node_angle[l]) for l in 1:n]
leaf_y = [R_max * sin(node_angle[l]) for l in 1:n]
leaf_colors = [IMPRINT_PALETTE[leaf_group[l]] for l in 1:n]
scatter!(ax, leaf_x, leaf_y; color = leaf_colors, markersize = 11, strokewidth = 0)

label_r = R_max * 1.16
for l in 1:n
    a = node_angle[l]
    flip = cos(a) < 0
    rot = flip ? a + pi : a
    halign = flip ? :right : :left
    text!(
        ax, label_r * cos(a), label_r * sin(a);
        text = labels[l], rotation = rot, align = (halign, :center),
        fontsize = 12, color = INK_SOFT,
    )
end

legend_elements = [LineElement(color = IMPRINT_PALETTE[g], linewidth = 4) for g in 1:4]
Legend(
    fig[1, 2], legend_elements, group_names, "Module";
    framevisible = false, labelcolor = INK, titlecolor = INK,
    labelsize = 14, titlesize = 16,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
