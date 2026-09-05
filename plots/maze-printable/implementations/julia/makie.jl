# anyplot.ai
# maze-printable: Printable Maze Puzzle
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

# --- Theme tokens ------------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data: perfect maze via randomized depth-first carving --------------------
# A spanning-tree maze (every cell reachable, no loops) guarantees exactly one
# simple path between any two cells, which is what makes the puzzle solvable
# with a single unambiguous route.
Random.seed!(42)

width = 25
height = 25

wall_n = trues(height, width)
wall_s = trues(height, width)
wall_e = trues(height, width)
wall_w = trues(height, width)

visited = falses(height, width)
stack = [(1, 1)]
visited[1, 1] = true

while !isempty(stack)
    r, c = stack[end]
    neighbors = Tuple{Int,Int,Symbol}[]
    r > 1 && !visited[r-1, c] && push!(neighbors, (r - 1, c, :N))
    r < height && !visited[r+1, c] && push!(neighbors, (r + 1, c, :S))
    c < width && !visited[r, c+1] && push!(neighbors, (r, c + 1, :E))
    c > 1 && !visited[r, c-1] && push!(neighbors, (r, c - 1, :W))

    if isempty(neighbors)
        pop!(stack)
        continue
    end

    nr, nc, direction = rand(neighbors)
    if direction == :N
        wall_n[r, c] = false
        wall_s[nr, nc] = false
    elseif direction == :S
        wall_s[r, c] = false
        wall_n[nr, nc] = false
    elseif direction == :E
        wall_e[r, c] = false
        wall_w[nr, nc] = false
    else
        wall_w[r, c] = false
        wall_e[nr, nc] = false
    end
    visited[nr, nc] = true
    push!(stack, (nr, nc))
end

wall_segments = Point2f[]
for r in 1:height, c in 1:width
    x0, x1 = Float32(c - 1), Float32(c)
    y0, y1 = Float32(height - r), Float32(height - r + 1)
    if wall_n[r, c]
        push!(wall_segments, Point2f(x0, y1), Point2f(x1, y1))
    end
    if wall_s[r, c]
        push!(wall_segments, Point2f(x0, y0), Point2f(x1, y0))
    end
    if wall_w[r, c]
        push!(wall_segments, Point2f(x0, y0), Point2f(x0, y1))
    end
    if wall_e[r, c]
        push!(wall_segments, Point2f(x1, y0), Point2f(x1, y1))
    end
end

start_point = Point2f(0.5, height - 0.5)
goal_point = Point2f(width - 0.5, 0.5)

# --- Plot ----------------------------------------------------------------------
fig = Figure(
    size=(1200, 1200),
    fontsize=14,
    backgroundcolor=PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title="maze-printable · julia · makie · anyplot.ai",
    titlesize=20,
    titlecolor=INK,
    backgroundcolor=PAGE_BG,
    aspect=DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)
limits!(ax, -0.8, width + 0.8, -0.8, height + 0.8)

linesegments!(ax, wall_segments; color=INK, linewidth=5)

# Start (brand green, "go") and goal (matte red, "stop") — the traffic-light
# green/red convention is a strong, widely shared color cue (semantic
# exception in the Imprint palette), so both markers borrow from that
# association instead of the plain 1→N categorical order.
scatter!(ax, [start_point]; color=IMPRINT_PALETTE[1], markersize=36, strokewidth=0)
text!(ax, start_point; text="S", color=PAGE_BG, fontsize=20, align=(:center, :center))

scatter!(ax, [goal_point]; color=IMPRINT_PALETTE[5], markersize=36, strokewidth=0)
text!(ax, goal_point; text="G", color=PAGE_BG, fontsize=20, align=(:center, :center))

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit=2)
