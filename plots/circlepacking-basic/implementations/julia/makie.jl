# anyplot.ai
# circlepacking-basic: Circle Packing Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
]

# --- Data: disk storage broken down into folders and files --------------------
struct LeafSpec
    label::String
    size_mb::Float64
end

struct SubcatSpec
    label::String
    leaves::Vector{LeafSpec}
end

struct CategorySpec
    label::String
    subcats::Vector{SubcatSpec}
end

function random_leaves(names, lo, hi)
    return [LeafSpec(n, lo + rand() * (hi - lo)) for n in names]
end

categories = [
    CategorySpec("Documents", [
        SubcatSpec("Reports", random_leaves(["Q1", "Q2", "Q3", "Q4"], 4.0, 60.0)),
        SubcatSpec("Spreadsheets", random_leaves(["Budget", "Forecast", "Payroll"], 2.0, 40.0)),
        SubcatSpec("Presentations", random_leaves(["Kickoff", "Roadmap"], 8.0, 90.0)),
    ]),
    CategorySpec("Media", [
        SubcatSpec("Photos", random_leaves(["Trip", "Family", "Events", "Pets"], 20.0, 320.0)),
        SubcatSpec("Videos", random_leaves(["Vacation", "Tutorial"], 200.0, 1400.0)),
        SubcatSpec("Audio", random_leaves(["Podcasts", "Music", "Voice Memos"], 15.0, 260.0)),
        SubcatSpec("Design Files", random_leaves(["Logos", "Mockups"], 10.0, 150.0)),
    ]),
    CategorySpec("Code", [
        SubcatSpec("Frontend", random_leaves(["Components", "Styles", "Assets"], 3.0, 55.0)),
        SubcatSpec("Backend", random_leaves(["API", "Services", "Migrations"], 3.0, 50.0)),
        SubcatSpec("Scripts", random_leaves(["Automation", "CI"], 1.0, 20.0)),
        SubcatSpec("Tests", random_leaves(["Unit", "Integration", "Fixtures"], 1.0, 30.0)),
    ]),
    CategorySpec("System", [
        SubcatSpec("Cache", random_leaves(["Browser", "Build", "Package"], 10.0, 200.0)),
        SubcatSpec("Logs", random_leaves(["App", "Access", "Crash"], 2.0, 45.0)),
        SubcatSpec("Config", random_leaves(["User", "Network"], 0.5, 6.0)),
        SubcatSpec("Temp", random_leaves(["Downloads", "Swap", "Recovery"], 5.0, 90.0)),
    ]),
]

# --- Hierarchy node + recursive circle packing ---------------------------------
mutable struct PackNode
    label::String
    depth::Int
    value::Float64
    category_idx::Int
    children::Vector{PackNode}
    rel_x::Float64
    rel_y::Float64
    abs_x::Float64
    abs_y::Float64
    r::Float64
end

PackNode(label, depth, category_idx) =
    PackNode(label, depth, 0.0, category_idx, PackNode[], 0.0, 0.0, 0.0, 0.0, 0.0)

# Position of a circle with radius r3, externally tangent to two placed circles.
function tangent_points(x1, y1, r1, x2, y2, r2, r3)
    d = hypot(x2 - x1, y2 - y1)
    R1, R2 = r1 + r3, r2 + r3
    if d < 1e-9 || d > R1 + R2 || d < abs(R1 - R2)
        return Tuple{Float64,Float64}[]
    end
    a = (R1^2 - R2^2 + d^2) / (2d)
    h2 = R1^2 - a^2
    h2 < 0 && return Tuple{Float64,Float64}[]
    h = sqrt(h2)
    xm = x1 + a * (x2 - x1) / d
    ym = y1 + a * (y2 - y1) / d
    ux, uy = -(y2 - y1) / d, (x2 - x1) / d
    return [(xm + h * ux, ym + h * uy), (xm - h * ux, ym - h * uy)]
end

# Greedy sibling packer: places circles (by descending radius) tangent to two
# already-placed neighbors, minimizing distance from the current centroid.
function pack_siblings(radii::Vector{Float64})
    n = length(radii)
    n == 0 && return Float64[], Float64[]
    xs, ys = zeros(n), zeros(n)
    order = sortperm(radii, rev = true)
    placed = Int[order[1]]
    if n >= 2
        i2 = order[2]
        xs[i2] = radii[order[1]] + radii[i2]
        push!(placed, i2)
    end
    for k in 3:n
        i = order[k]
        r = radii[i]
        best, best_dist = nothing, Inf
        for ai in 1:length(placed), bi in (ai + 1):length(placed)
            a, b = placed[ai], placed[bi]
            for p in tangent_points(xs[a], ys[a], radii[a], xs[b], ys[b], radii[b], r)
                ok = true
                for c in placed
                    if hypot(p[1] - xs[c], p[2] - ys[c]) < radii[c] + r - 1e-6
                        ok = false
                        break
                    end
                end
                if ok
                    dist = hypot(p[1], p[2]) + r
                    if dist < best_dist
                        best_dist, best = dist, p
                    end
                end
            end
        end
        if best === nothing
            angle = 2pi * k / n
            reach = sum(radii) + r
            best = (reach * cos(angle), reach * sin(angle))
        end
        xs[i], ys[i] = best
        push!(placed, i)
    end
    return xs, ys
end

# Bottom-up: pack each node's children, then set node.r to their enclosing
# circle (plus padding) and store each child's offset relative to this node.
function pack!(node::PackNode; padding_ratio = 0.10)
    if isempty(node.children)
        node.r = sqrt(node.value)
        return
    end
    for c in node.children
        pack!(c; padding_ratio = padding_ratio)
    end
    radii = [c.r for c in node.children]
    xs, ys = pack_siblings(radii)
    lefts = xs .- radii
    rights = xs .+ radii
    tops = ys .- radii
    bottoms = ys .+ radii
    cx = (minimum(lefts) + maximum(rights)) / 2
    cy = (minimum(tops) + maximum(bottoms)) / 2
    xs .-= cx
    ys .-= cy
    enclosing_r = maximum(hypot.(xs, ys) .+ radii)
    node.r = enclosing_r * (1 + padding_ratio)
    for (c, x, y) in zip(node.children, xs, ys)
        c.rel_x, c.rel_y = x, y
    end
end

function locate!(node::PackNode, parent_x, parent_y)
    node.abs_x = parent_x + node.rel_x
    node.abs_y = parent_y + node.rel_y
    for c in node.children
        locate!(c, node.abs_x, node.abs_y)
    end
end

function collect_nodes!(node::PackNode, acc::Vector{PackNode})
    push!(acc, node)
    for c in node.children
        collect_nodes!(c, acc)
    end
end

# --- Build the tree -------------------------------------------------------------
root = PackNode("Storage", 0, 0)
for (ci, cat) in enumerate(categories)
    cat_node = PackNode(cat.label, 1, ci)
    for sub in cat.subcats
        sub_node = PackNode(sub.label, 2, ci)
        for leaf in sub.leaves
            leaf_node = PackNode(leaf.label, 3, ci)
            leaf_node.value = leaf.size_mb
            push!(sub_node.children, leaf_node)
        end
        push!(cat_node.children, sub_node)
    end
    push!(root.children, cat_node)
end

pack!(root)
root.rel_x, root.rel_y = 0.0, 0.0
locate!(root, 0.0, 0.0)

# Rescale so the root circle lands on a fixed size in figure data units.
const TARGET_ROOT_R = 540.0
scale = TARGET_ROOT_R / root.r
all_nodes = PackNode[]
collect_nodes!(root, all_nodes)
for node in all_nodes
    node.abs_x *= scale
    node.abs_y *= scale
    node.r *= scale
end

# --- Plot ------------------------------------------------------------------------
fig = Figure(
    resolution = (1200, 1200),
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title = "circlepacking-basic · julia · makie · anyplot.ai",
    titlesize = 30,
    titlecolor = INK,
    aspect = DataAspect(),
    backgroundcolor = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)

# Root: faint container circle showing the encompassing boundary.
poly!(ax, Circle(Point2f(root.abs_x, root.abs_y), root.r);
    color = (PAGE_BG, 0.0), strokecolor = INK_SOFT, strokewidth = 1.5)

fill_alpha = Dict(1 => 0.16, 2 => 0.38, 3 => 0.88)
for depth in 1:3
    for node in all_nodes
        node.depth == depth || continue
        base = IMPRINT_PALETTE[node.category_idx]
        poly!(ax, Circle(Point2f(node.abs_x, node.abs_y), node.r);
            color = (base, fill_alpha[depth]), strokecolor = PAGE_BG, strokewidth = 2.0)
    end
end

# Labels: categories placed just below the actual bottom of their own child
# cluster (not a fixed fraction of the category radius, which can collide
# with a child that happens to sit near the category's edge); subcategories
# at their own center, only when large relative to their own category (not
# the global root) so every category gets comparable coverage.
category_r = Dict(node.category_idx => node.r for node in all_nodes if node.depth == 1)
label_margin = 0.05 * root.r
for node in all_nodes
    if node.depth == 1
        child_bottom = minimum(c.abs_y - c.r for c in node.children)
        text!(ax, node.abs_x, child_bottom - label_margin; text = node.label,
            align = (:center, :center), fontsize = 20, color = INK, font = :bold)
    elseif node.depth == 2 && node.r >= 0.18 * category_r[node.category_idx]
        text!(ax, node.abs_x, node.abs_y; text = node.label, align = (:center, :center),
            fontsize = 13, color = INK)
    end
end

# --- Save --------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
