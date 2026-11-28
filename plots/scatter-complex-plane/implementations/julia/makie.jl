# anyplot.ai
# scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-06-02

using CairoMakie
using Colors
using DataFrames

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
# Imprint palette
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

# Columns
const NAME     = "Name"                # role: label
const RE_PART  = "Real part Re(z)"     # role: x
const IM_PART  = "Imaginary part Im(z)" # role: y
const KIND     = "Kind of number"      # role: group

# Data: sixth roots of unity, two operands a and b, and their sum and product
roots = [cis(2π * k / 6) for k in 0:5]
a = 1.2 + 0.8im
b = -1.0 + 0.6im
z = vcat(roots, [a, b, a + b, a * b])
df = DataFrame(
    NAME => vcat(["z" * Char(0x2080 + k) for k in 0:5], ["a", "b", "a + b", "a · b"]),
    RE_PART => real.(z),
    IM_PART => imag.(z),
    KIND => vcat(fill("6th roots of unity", 6), fill("Operands", 2), fill("Sum and product", 2)),
)

# Plot
kinds   = unique(df[!, KIND])
group   = [findfirst(==(k), kinds) for k in df[!, KIND]]
markers = [:circle, :diamond, :rect][group]
re_vals = df[!, RE_PART]
im_vals = df[!, IM_PART]
span    = maximum(abs.(vcat(re_vals, im_vals))) * 1.4
theta   = range(0, 2π; length = 300)

fig = Figure(size = (1200, 1200), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title              = "scatter-complex-plane · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = RE_PART,
    ylabel             = IM_PART,
    xlabelsize         = 16,
    ylabelsize         = 16,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 14,
    yticklabelsize     = 14,
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
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    aspect             = DataAspect(),
)
limits!(ax, -span, span, -span, span)

# Unit circle, dashed reference
lines!(ax, cos.(theta), sin.(theta); linestyle = :dash, color = (INK_SOFT, 0.8), linewidth = 2)

# Real and imaginary axes through the origin
hlines!(ax, [0.0]; color = (INK_SOFT, 0.5), linewidth = 1)
vlines!(ax, [0.0]; color = (INK_SOFT, 0.5), linewidth = 1)

# One arrow per point, from the origin to its head
arrows2d!(ax, zeros(nrow(df)), zeros(nrow(df)), re_vals, im_vals;
    color     = IMPRINT_PALETTE[group],
    shaftwidth = 2.5,
    tipwidth  = 14,
    tiplength = 16,
)

# Points, one scatter per kind so the legend names them
for (i, kind) in enumerate(kinds)
    idx = findall(==(i), group)
    scatter!(ax, re_vals[idx], im_vals[idx];
        color       = IMPRINT_PALETTE[i],
        marker      = markers[idx[1]],
        markersize  = 16,
        strokewidth = 1.5,
        strokecolor = PAGE_BG,
        label       = kind,
    )
end

# Name and rectangular form a+bi, placed outward along each point's direction
for (name, x, y) in zip(df[!, NAME], re_vals, im_vals)
    r    = hypot(x, y)
    sign = y >= 0 ? "+" : "−"
    form = string(replace(string(round(x; digits = 2)), "-" => "−"), sign, round(abs(y); digits = 2), "i")
    h    = x > 0.1 ? :left : (x < -0.1 ? :right : :center)
    v    = y > -0.05 ? :bottom : :top
    text!(ax, x + 0.1 * x / r, y + 0.1 * y / r;
        text     = name * "\n" * form,
        fontsize = 15,
        color    = INK,
        align    = (h, v),
    )
end

axislegend(ax;
    position        = :lb,
    backgroundcolor = ELEVATED_BG,
    framecolor      = INK_SOFT,
    labelcolor      = INK,
    labelsize       = 15,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
