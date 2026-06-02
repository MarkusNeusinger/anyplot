# anyplot.ai
# scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-06-02

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
    colorant"#009E73",  # 1 — brand green (first series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data — 5th roots of unity: e^(2πik/5) for k = 0,...,4
n_roots = 5
theta_roots = [2π * k / n_roots for k in 0:(n_roots - 1)]
re_roots = cos.(theta_roots)
im_roots = sin.(theta_roots)
root_labels = ["z₀", "z₁", "z₂", "z₃", "z₄"]

# Arbitrary complex numbers outside the unit circle
re_arb = [1.5, -1.3, 0.6]
im_arb = [1.1, 0.8, -1.7]
arb_labels = ["w₁", "w₂", "w₃"]

# Unit circle reference (parametric)
theta_circle = LinRange(0, 2π, 300)

# Figure — square canvas: size=(1200,1200) × px_per_unit=2 → 2400×2400 px
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "scatter-complex-plane · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Re(z)",
    ylabel             = "Im(z)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = (INK_SOFT, 0.12),
    ygridcolor         = (INK_SOFT, 0.12),
    aspect             = DataAspect(),
)

# Unit circle — dashed reference
lines!(ax, cos.(theta_circle), sin.(theta_circle);
    linestyle = :dash,
    color     = (INK_SOFT, 0.8),
    linewidth = 1.5,
)

# Real and imaginary axis lines through origin
hlines!(ax, [0.0]; color = (INK_SOFT, 0.5), linewidth = 0.8)
vlines!(ax, [0.0]; color = (INK_SOFT, 0.5), linewidth = 0.8)

# Arrows from origin to 5th roots of unity
roots_origins = fill(Point2f(0, 0), n_roots)
roots_dirs    = Point2f.(re_roots, im_roots)
arrows!(ax, roots_origins, roots_dirs;
    color     = IMPRINT_PALETTE[1],
    linewidth = 2.0,
    arrowsize = 16,
)

# Arrows from origin to arbitrary complex numbers
arb_origins = fill(Point2f(0, 0), length(re_arb))
arb_dirs    = Point2f.(re_arb, im_arb)
arrows!(ax, arb_origins, arb_dirs;
    color     = IMPRINT_PALETTE[2],
    linewidth = 2.0,
    arrowsize = 16,
)

# Scatter points — 5th roots of unity (circle markers)
scatter!(ax, re_roots, im_roots;
    color       = IMPRINT_PALETTE[1],
    markersize  = 14,
    marker      = :circle,
    strokewidth = 1.5,
    strokecolor = PAGE_BG,
    label       = "5th roots of unity",
)

# Scatter points — arbitrary complex numbers (diamond markers for shape encoding)
scatter!(ax, re_arb, im_arb;
    color       = IMPRINT_PALETTE[2],
    markersize  = 14,
    marker      = :diamond,
    strokewidth = 1.5,
    strokecolor = PAGE_BG,
    label       = "Arbitrary complex",
)

# Labels for roots of unity — symbolic name + rectangular form annotation
label_offset = 0.18
for (r_val, i_val, lbl) in zip(re_roots, im_roots, root_labels)
    mag = sqrt(r_val^2 + i_val^2)
    ox  = r_val / mag * label_offset
    oy  = i_val / mag * label_offset
    h   = r_val > 0.1 ? :left : (r_val < -0.1 ? :right : :center)
    v   = i_val > 0.1 ? :bottom : (i_val < -0.1 ? :top : :center)
    # Symbolic label
    text!(ax, [Point2f(r_val + ox, i_val + oy)];
        text     = [lbl],
        fontsize = 14,
        color    = INK,
        align    = [(h, v)],
    )
    # Rectangular form — placed further out along the same radial direction
    rect_str = i_val >= 0 ?
        "$(round(r_val, digits=2))+$(round(i_val, digits=2))i" :
        "$(round(r_val, digits=2))$(round(i_val, digits=2))i"
    rox = r_val / mag * (label_offset + 0.24)
    roy = i_val / mag * (label_offset + 0.24)
    text!(ax, [Point2f(r_val + rox, i_val + roy)];
        text     = [rect_str],
        fontsize = 10,
        color    = INK_SOFT,
        align    = [(h, v)],
    )
end

# Labels for arbitrary complex numbers — symbolic name + rectangular form annotation
for (r_val, i_val, lbl) in zip(re_arb, im_arb, arb_labels)
    mag = sqrt(r_val^2 + i_val^2)
    ox  = r_val / mag * 0.2
    oy  = i_val / mag * 0.2
    h   = r_val > 0 ? :left : :right
    v   = i_val > 0 ? :bottom : :top
    # Symbolic label
    text!(ax, [Point2f(r_val + ox, i_val + oy)];
        text     = [lbl],
        fontsize = 14,
        color    = INK,
        align    = [(h, v)],
    )
    # Rectangular form — placed further out along the same radial direction
    rect_str = i_val >= 0 ?
        "$(round(r_val, digits=2))+$(round(i_val, digits=2))i" :
        "$(round(r_val, digits=2))$(round(i_val, digits=2))i"
    rox = r_val / mag * (0.2 + 0.24)
    roy = i_val / mag * (0.2 + 0.24)
    text!(ax, [Point2f(r_val + rox, i_val + roy)];
        text     = [rect_str],
        fontsize = 10,
        color    = INK_SOFT,
        align    = [(h, v)],
    )
end

# Legend (lower-left inside axis)
axislegend(ax;
    position        = :lb,
    backgroundcolor = ELEVATED_BG,
    framecolor      = INK_SOFT,
    labelcolor      = INK,
    labelsize       = 12,
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
