# anyplot.ai
# heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-05-30

using CairoMakie
using Colors

# Theme tokens (Imprint palette — theme-adaptive chrome)
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential colormap: brand green → blue (single-polarity continuous data)
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# Interior of the Mandelbrot set: near-black (canonical convention, never escapes)
const INTERIOR_COLOR = colorant"#0A0A0A"

# Mandelbrot parameters
const X_MIN    = -2.5
const X_MAX    =  1.0
const Y_MIN    = -1.25
const Y_MAX    =  1.25
const MAX_ITER = 256
const WIDTH    = 1600
const HEIGHT   =  900

# Compute smooth escape count for each pixel
xs = range(X_MIN, X_MAX; length = WIDTH)
ys = range(Y_MIN, Y_MAX; length = HEIGHT)
escape = Matrix{Float64}(undef, WIDTH, HEIGHT)

for i in 1:WIDTH, j in 1:HEIGHT
    cx = xs[i]
    cy = ys[j]
    zx = 0.0
    zy = 0.0
    iter = 0
    escaped = false
    while iter < MAX_ITER
        zx2 = zx * zx
        zy2 = zy * zy
        if zx2 + zy2 > 4.0
            escaped = true
            break
        end
        zy = 2.0 * zx * zy + cy
        zx = zx2 - zy2 + cx
        iter += 1
    end
    if escaped
        zmod = sqrt(zx * zx + zy * zy)
        smooth = iter + 1.0 - log2(log2(zmod))
        escape[i, j] = mod(smooth, 8.0) / 8.0
    else
        escape[i, j] = NaN
    end
end

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "heatmap-mandelbrot · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Re(c)",
    ylabel             = "Im(c)",
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
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    topspinevisible    = false,
    rightspinevisible  = false,
    xgridvisible       = false,
    ygridvisible       = false,
    backgroundcolor    = PAGE_BG,
    aspect             = DataAspect(),
)

hm = heatmap!(ax, xs, ys, escape;
    colormap   = ANYPLOT_SEQ,
    nan_color  = INTERIOR_COLOR,
    colorrange = (0.0, 1.0),
)

Colorbar(fig[1, 2], hm;
    label          = "Escape speed",
    labelsize      = 12,
    labelcolor     = INK,
    ticklabelsize  = 10,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    width          = 16,
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
