# anyplot.ai
# alluvial-opinion-flow: Opinion Flow Diagram
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-05-30

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
THEME       = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Opinion category colors — semantic mapping: positive→green, negative→red, neutral→muted
CAT_COLORS = [
    colorant"#009E73",  # Strongly Support — Imprint brand green (positive)
    colorant"#2ABCCD",  # Support           — Imprint cyan
    INK_MUTED,          # Neutral           — theme-adaptive muted
    colorant"#BD8233",  # Oppose            — Imprint ochre
    colorant"#AE3030",  # Strongly Oppose   — Imprint matte red (negative)
]
categories = ["Strongly Support", "Support", "Neutral", "Oppose", "Strongly Oppose"]
N_CATS     = 5

# Data: public health policy opinion survey, 1000 respondents, 3 quarterly waves
waves   = ["Wave 1\n(January)", "Wave 2\n(April)", "Wave 3\n(July)"]
N_WAVES = 3

w1 = [200, 305, 200, 190, 105]

# Transition matrix Wave 1 → Wave 2; rows = source category, cols = target
# Row sums must equal w1
f12 = [
    155  28   9   5   3;
     25 205  50  18   7;
     10  40 115  30   5;
      5  15  32 120  18;
      2   5  11  18  69;
]

w2 = vec(sum(f12; dims = 1))   # [197, 293, 217, 191, 102]

# Transition matrix Wave 2 → Wave 3; row sums must equal w2
f23 = [
    148  30  12   5   2;
     25 210  40  13   5;
     12  38 132  28   7;
      4  15  28 130  14;
      2   4  10  18  68;
]

w3 = vec(sum(f23; dims = 1))   # [191, 297, 222, 194, 96]

wave_counts   = [w1, w2, w3]
flow_matrices = [f12, f23]

# Layout
WAVE_XS  = [1.0, 3.5, 6.0]   # x centre of each wave column
NODE_W   = 0.20               # node rectangle half-width × 2
NODE_GAP = 20                 # gap between vertically stacked nodes (respondent units)
N_BEZ    = 80                 # bezier interpolation segments

# Node y-positions: stack bottom→top, Strongly Oppose (index 5) at base
all_y_lo = [zeros(Float64, N_CATS) for _ in 1:N_WAVES]
all_y_hi = [zeros(Float64, N_CATS) for _ in 1:N_WAVES]
for w in 1:N_WAVES
    y = 0.0
    for i in N_CATS:-1:1
        all_y_lo[w][i] = y
        all_y_hi[w][i] = y + Float64(wave_counts[w][i])
        y += wave_counts[w][i] + NODE_GAP
    end
end

# Bezier strip: smooth S-curve flow band connecting two node edges
function bezier_strip(x0, y0_lo, y0_hi, x1, y1_lo, y1_hi)
    cx = (x0 + x1) / 2.0
    ts = range(0.0, 1.0; length = N_BEZ)
    bx(t, xa, xb) = (1 - t)^3 * xa + 3 * (1 - t)^2 * t * cx + 3 * (1 - t) * t^2 * cx + t^3 * xb
    top = [Point2f(bx(t, x0, x1), (1 - t) * y0_hi + t * y1_hi) for t in ts]
    bot = [Point2f(bx(t, x1, x0), (1 - t) * y1_lo + t * y0_lo) for t in ts]
    return vcat(top, bot)
end

# Pre-compute all flow polygons; track fill offsets per node
src_used = [zeros(Float64, N_CATS) for _ in 1:(N_WAVES - 1)]
dst_used = [zeros(Float64, N_CATS) for _ in 1:(N_WAVES - 1)]

flow_polys  = Vector{Vector{Point2f}}()
flow_colors = Vector{Tuple{RGBf, Float32}}()

for pair in 1:(N_WAVES - 1)
    x0r  = WAVE_XS[pair]     + NODE_W / 2
    x1l  = WAVE_XS[pair + 1] - NODE_W / 2
    fmat = flow_matrices[pair]
    for src in 1:N_CATS
        for dst in 1:N_CATS
            v = Float64(fmat[src, dst])
            v < 1 && continue
            s_lo = all_y_lo[pair][src]     + src_used[pair][src]
            s_hi = s_lo + v
            src_used[pair][src] += v
            d_lo = all_y_lo[pair + 1][dst] + dst_used[pair][dst]
            d_hi = d_lo + v
            dst_used[pair][dst] += v
            push!(flow_polys,  bezier_strip(x0r, s_lo, s_hi, x1l, d_lo, d_hi))
            c = CAT_COLORS[src]
            push!(flow_colors, (RGBf(Float32(red(c)), Float32(green(c)), Float32(blue(c))), 0.32f0))
        end
    end
end

y_max = maximum(all_y_hi[w][1] for w in 1:N_WAVES)

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "alluvial-opinion-flow · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    backgroundcolor    = PAGE_BG,
    leftspinevisible   = false,
    rightspinevisible  = false,
    topspinevisible    = false,
    bottomspinevisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
    xticksvisible      = false,
    yticksvisible      = false,
    xticklabelsvisible = false,
    yticklabelsvisible = false,
)

# Draw flows (rendered behind nodes)
for (pts, (rgb, alpha)) in zip(flow_polys, flow_colors)
    poly!(ax, pts; color = RGBAf(rgb.r, rgb.g, rgb.b, alpha), strokewidth = 0)
end

# Draw nodes and inline count labels
for w in 1:N_WAVES
    for cat in 1:N_CATS
        xl = WAVE_XS[w] - NODE_W / 2
        xr = WAVE_XS[w] + NODE_W / 2
        yl = all_y_lo[w][cat]
        yh = all_y_hi[w][cat]
        node_pts = [Point2f(xl, yl), Point2f(xr, yl), Point2f(xr, yh), Point2f(xl, yh)]
        poly!(ax, node_pts; color = CAT_COLORS[cat], strokewidth = 0)
        text!(ax, WAVE_XS[w], (yl + yh) / 2;
              text     = string(wave_counts[w][cat]),
              align    = (:center, :center),
              fontsize = 12,
              color    = colorant"#FFFDF6",
              font     = :bold,
        )
    end
end

# Wave column headers
for w in 1:N_WAVES
    text!(ax, WAVE_XS[w], y_max + 60;
          text     = waves[w],
          align    = (:center, :bottom),
          fontsize = 13,
          color    = INK,
          font     = :bold,
    )
end

# Legend
legend_x = WAVE_XS[end] + 0.55
for (i, cat) in enumerate(categories)
    y_mid      = y_max - (i - 1) * 215
    swatch_pts = [
        Point2f(legend_x,        y_mid - 22),
        Point2f(legend_x + 0.17, y_mid - 22),
        Point2f(legend_x + 0.17, y_mid + 22),
        Point2f(legend_x,        y_mid + 22),
    ]
    poly!(ax, swatch_pts; color = CAT_COLORS[i], strokewidth = 0)
    text!(ax, legend_x + 0.23, y_mid;
          text     = cat,
          align    = (:left, :center),
          fontsize = 12,
          color    = INK_SOFT,
    )
end

xlims!(ax, 0.3, 7.7)
ylims!(ax, -60, y_max + 150)

save(joinpath(@__DIR__, "plot-$(THEME).png"), fig; px_per_unit = 2)
