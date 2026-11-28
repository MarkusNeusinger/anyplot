# anyplot.ai
# pie-basic: Basic Pie Chart
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: pending | Created: 2026-05-28

using CairoMakie
using Colors
using Printf

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const LABEL_FG    = colorant"#FFFFFF"

const IMPRINT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
]

const categories  = ["Python", "JavaScript", "Java", "C / C++", "TypeScript"]
const values      = [36.0, 29.5, 17.0, 11.5, 6.0]
const total       = sum(values)
const fracs       = values ./ total
const pct         = fracs .* 100

const explode_idx = argmax(values)
const explode_r   = 0.08

# Cumulative fractions for angle calculations (matches pie! counterclockwise convention)
const cum        = cumsum(vcat(0.0, fracs))
const PIE_OFFSET = Float64(π / 2)

const title_str = "Primary Programming Language · pie-basic · julia · makie · anyplot.ai"
const title_fs  = round(Int, 26 * min(1.0, 66.0 / length(title_str)))

fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
    figure_padding  = 40,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = title_fs,
    titlefont          = :bold,
    titlegap           = 24,
    titlecolor         = INK,
    aspect             = DataAspect(),
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

# Wedges drawn as polygons so the dominant slice can be pulled out of the circle
function slice_points(a0, a1, dx, dy; n = 120)
    ang = range(a0, a1; length = n)
    pts = vcat([Point2f(dx, dy)], [Point2f(dx + cos(t), dy + sin(t)) for t in ang])
    return pts
end

for i in 1:length(values)
    θ  = PIE_OFFSET + (cum[i] + fracs[i] / 2) * 2π
    ex = i == explode_idx ? explode_r * cos(θ) : 0.0
    ey = i == explode_idx ? explode_r * sin(θ) : 0.0
    a0 = PIE_OFFSET + cum[i] * 2π
    a1 = PIE_OFFSET + cum[i + 1] * 2π
    poly!(ax, slice_points(a0, a1, ex, ey);
          color = IMPRINT_PALETTE[i], strokecolor = PAGE_BG, strokewidth = 3)
    # Thin slices carry their label outside the circle, the others sit inside
    outside = fracs[i] < 0.08
    r = outside ? 1.14 : 0.62
    text!(ax, ex + r * cos(θ), ey + r * sin(θ);
          text     = @sprintf("%.1f%%", pct[i]),
          align    = (:center, :center),
          fontsize = i == explode_idx ? 26 : 22,
          font     = i == explode_idx ? :bold : :regular,
          color    = outside ? INK : LABEL_FG,
    )
end

# Explicit limits so the translated slice stays fully in view
limits!(ax, -1.25, 1.25, -1.25, 1.3)

legend_entries = [PolyElement(color = IMPRINT_PALETTE[i], strokecolor = :transparent) for i in 1:length(categories)]
legend_labels  = [@sprintf("%s  %.1f%%", categories[i], pct[i]) for i in 1:length(categories)]

Legend(
    fig[1, 2],
    legend_entries,
    legend_labels;
    framevisible    = false,
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK,
    labelsize       = 20,
    rowgap          = 18,
    patchsize       = (34, 34),
    halign          = :left,
    valign          = :center,
    padding         = (16, 16, 16, 16),
)

colsize!(fig.layout, 1, Relative(0.70))
colgap!(fig.layout, 1, 20)

save("plot-$(THEME).png", fig; px_per_unit = 2)
