# anyplot.ai
# maze-circular: Circular Maze Puzzle
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 92/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND    = colorant"#009E73"  # Imprint palette position 1 — entry/goal accent

# --- Maze parameters -----------------------------------------------------------
# 8 rings keeps the puzzle within the spec's recommended 5-10 range. Sector count
# doubles every 3 rings from the hub outward (3 -> 6 -> 12) so cell width stays
# roughly consistent from the cramped center to the roomier rim, instead of a
# fixed sector count leaving the innermost rings a dense cluster of narrow wedges.
rings        = 8
ring_sectors = [3, 3, 3, 6, 6, 6, 12, 12]   # ring 1 = innermost (hub side)
difficulty   = "medium"
entry_sector = 1                    # sector (on the outer ring) hosting the opening
hub_radius   = 1.0
ring_width   = 1.0
n_arc        = 12                   # points per drawn arc segment

radii = [hub_radius + i * ring_width for i in 0:rings]  # radii[1] = hub boundary
dθ    = [2π / ring_sectors[i] for i in 1:rings]          # sector angle, per ring

# Node ids: 1 = center hub, then each ring's sectors packed consecutively.
ring_offset = vcat(0, cumsum(ring_sectors))              # ring_offset[i] = cells before ring i
node_id(ring, sector) = 1 + ring_offset[ring] + sector

polar(r, θ) = Point2f(r * cos(θ), r * sin(θ))

# --- Union-Find (disjoint set), used by the randomized-Kruskal maze carver ----
function find_root(parent, x)
    while parent[x] != x
        parent[x] = parent[parent[x]]
        x = parent[x]
    end
    return x
end

function union_cells!(parent, a, b)
    ra, rb = find_root(parent, a), find_root(parent, b)
    ra == rb && return false
    parent[ra] = rb
    return true
end

# --- Candidate connections between adjacent cells -----------------------------
# Each entry is a wall between two cells; shape encodes how to draw it if the
# connection stays closed: an :arc (fixed radius, spans an angle range) for
# ring-to-ring boundaries, or a :line (fixed angle, spans a radius range) for
# sector-to-sector boundaries.
edges = NamedTuple{(:a, :b, :shape, :p1, :p2, :p3),Tuple{Int,Int,Symbol,Float64,Float64,Float64}}[]

# Hub <-> innermost ring.
for s in 1:ring_sectors[1]
    θ1, θ2 = (s - 1) * dθ[1], s * dθ[1]
    push!(edges, (a = 1, b = node_id(1, s), shape = :arc, p1 = radii[1], p2 = θ1, p3 = θ2))
end

# Ring i <-> ring i+1. `ratio` is 1 when sector count stays flat, or 2 where it
# doubles outward — each inner cell then borders exactly `ratio` outer cells.
for i in 1:(rings - 1)
    ratio = ring_sectors[i + 1] ÷ ring_sectors[i]
    for s in 1:ring_sectors[i], k in 1:ratio
        s_out = (s - 1) * ratio + k
        θ1, θ2 = (s_out - 1) * dθ[i + 1], s_out * dθ[i + 1]
        push!(edges, (a = node_id(i, s), b = node_id(i + 1, s_out), shape = :arc, p1 = radii[i + 1], p2 = θ1, p3 = θ2))
    end
end

# Sector <-> next sector within the same ring.
for i in 1:rings, s in 1:ring_sectors[i]
    s2 = s % ring_sectors[i] + 1
    θ = s * dθ[i]
    push!(edges, (a = node_id(i, s), b = node_id(i, s2), shape = :line, p1 = θ, p2 = radii[i], p3 = radii[i + 1]))
end

# --- Carve the maze: randomized Kruskal spanning tree over the cell graph ----
# A spanning tree connects every cell with exactly one path between any two —
# guaranteeing exactly one solvable path from the entry to the center goal.
n_nodes = 1 + sum(ring_sectors)
parent  = collect(1:n_nodes)
walls   = similar(edges, 0)
for e in shuffle(edges)
    union_cells!(parent, e.a, e.b) || push!(walls, e)
end

# --- Wall geometry: one polyline per closed connection, NaN-separated -------
wall_pts = Point2f[]
for e in walls
    if e.shape == :arc
        for θ in range(e.p2, e.p3; length = n_arc)
            push!(wall_pts, polar(e.p1, θ))
        end
    else
        push!(wall_pts, polar(e.p2, e.p1))
        push!(wall_pts, polar(e.p3, e.p1))
    end
    push!(wall_pts, Point2f(NaN, NaN))
end

outer_r       = radii[end]
outer_sectors = ring_sectors[rings]
for s in 1:outer_sectors
    if s != entry_sector
        for θ in range((s - 1) * dθ[rings], s * dθ[rings]; length = n_arc)
            push!(wall_pts, polar(outer_r, θ))
        end
        push!(wall_pts, Point2f(NaN, NaN))
    end
end

# --- Figure --------------------------------------------------------------------
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

title_str = "maze-circular · julia · makie · anyplot.ai"

ax = Axis(
    fig[1, 1];
    title           = title_str,
    titlesize       = 24,
    titlecolor      = INK,
    subtitle        = "$(rings) rings · $(difficulty) difficulty · single solution",
    subtitlesize    = 15,
    subtitlecolor   = INK_SOFT,
    aspect          = DataAspect(),
    backgroundcolor = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)

lines!(ax, wall_pts; color = INK, linewidth = 4.5)

# --- Goal marker at the center --------------------------------------------------
poly!(ax, Circle(Point2f(0, 0), hub_radius * 0.82); color = (BRAND, 0.12), strokewidth = 0)
scatter!(ax, [Point2f(0, 0)]; marker = :star5, markersize = 30, color = BRAND, strokewidth = 0)
text!(ax, 0.0, -hub_radius * 0.55; text = "GOAL", align = (:center, :center), color = INK, fontsize = 14)

# --- Entry marker on the outer boundary ----------------------------------------
entry_angle = (entry_sector - 0.5) * dθ[rings]
r_tail, r_tip = outer_r + 1.0, outer_r + 0.15
x0, y0 = r_tail * cos(entry_angle), r_tail * sin(entry_angle)
x1, y1 = r_tip * cos(entry_angle), r_tip * sin(entry_angle)
arrows!(ax, [x0], [y0], [x1 - x0], [y1 - y0]; color = BRAND, linewidth = 4.5, arrowsize = 22)
label_x, label_y = (outer_r + 1.55) * cos(entry_angle), (outer_r + 1.55) * sin(entry_angle)
text!(ax, label_x, label_y; text = "START", align = (:center, :center), color = INK, fontsize = 14)

# --- Content-hugging canvas limits ---------------------------------------------
# Fit the view snugly around everything actually drawn (walls + entry marker +
# labels) instead of padding every side uniformly — a uniform pad leaves extra
# empty space opposite the one-sided START arrow, since that side needs less.
content_x = Float64[x0, x1, label_x]
content_y = Float64[y0, y1, label_y]
for p in wall_pts
    isfinite(p[1]) || continue
    push!(content_x, p[1])
    push!(content_y, p[2])
end
label_margin = 0.55  # room for the START / GOAL glyphs beyond their anchor point
xmin, xmax = minimum(content_x) - label_margin, maximum(content_x) + label_margin
ymin, ymax = minimum(content_y) - label_margin, maximum(content_y) + label_margin
half = max(xmax - xmin, ymax - ymin) / 2
cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
xlims!(ax, cx - half, cx + half)
ylims!(ax, cy - half, cy + half)

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
