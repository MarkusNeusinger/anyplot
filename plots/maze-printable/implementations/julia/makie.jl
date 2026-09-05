# anyplot.ai
# maze-printable: Printable Maze Puzzle
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 90/100 | Created: 2026-09-05

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

# Softly rounded print-frame border around the maze — a Makie `poly!`-built
# rounded rectangle (traced corner-arc by corner-arc) rather than a plain
# `lines!` rectangle, giving the puzzle sheet a finished, card-like edge.
frame_x0, frame_x1 = -0.6, width + 0.6
frame_y0, frame_y1 = -0.6, height + 0.6
frame_r = 0.6
frame_corners = [
    (frame_x1 - frame_r, frame_y0 + frame_r, -90.0, 0.0),
    (frame_x1 - frame_r, frame_y1 - frame_r, 0.0, 90.0),
    (frame_x0 + frame_r, frame_y1 - frame_r, 90.0, 180.0),
    (frame_x0 + frame_r, frame_y0 + frame_r, 180.0, 270.0),
]
frame_pts = Point2f[]
for (cx, cy, a0, a1) in frame_corners
    for t in range(a0, a1; length=12)
        θ = deg2rad(t)
        push!(frame_pts, Point2f(cx + frame_r * cos(θ), cy + frame_r * sin(θ)))
    end
end

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
limits!(ax, -1.0, width + 1.0, -1.0, height + 1.0)

# Subtle accent tint on the start/goal cells — a light hint of visual
# hierarchy beyond the markers themselves, reinforcing the start-to-goal
# narrative before the walls are drawn on top.
poly!(ax, Rect2f(0, height - 1, 1, 1); color=(IMPRINT_PALETTE[1], 0.12), strokewidth=0)
poly!(ax, Rect2f(width - 1, 0, 1, 1); color=(IMPRINT_PALETTE[5], 0.12), strokewidth=0)

linesegments!(ax, wall_segments; color=INK, linewidth=6)

poly!(ax, frame_pts; color=(PAGE_BG, 0.0), strokecolor=INK_SOFT, strokewidth=3)

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
