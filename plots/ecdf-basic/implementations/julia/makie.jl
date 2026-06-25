# anyplot.ai
# ecdf-basic: Basic ECDF Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-06-25

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
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

# Data: page load times (seconds) for three server configurations (n=200 each)
n = 200
times_cached = randn(n) .* 0.20 .+ 0.80
times_cdn    = randn(n) .* 0.30 .+ 1.40
times_legacy = randn(n) .* 0.60 .+ 2.80

# P50 (median) for each group — used for reference lines
p50_c   = median(times_cached)
p50_cdn = median(times_cdn)
p50_l   = median(times_legacy)

# Compute ECDFs: sort data, build cumulative proportions, extend tails for clean drawing
sorted_c   = sort(times_cached)
ext_c      = 0.08 * (sorted_c[end] - sorted_c[1])
xs_c       = vcat([sorted_c[1] - ext_c], sorted_c, [sorted_c[end] + ext_c])
ys_c       = vcat([0.0], collect(1:n) ./ n, [1.0])

sorted_cdn = sort(times_cdn)
ext_cdn    = 0.08 * (sorted_cdn[end] - sorted_cdn[1])
xs_cdn     = vcat([sorted_cdn[1] - ext_cdn], sorted_cdn, [sorted_cdn[end] + ext_cdn])
ys_cdn     = vcat([0.0], collect(1:n) ./ n, [1.0])

sorted_l   = sort(times_legacy)
ext_l      = 0.08 * (sorted_l[end] - sorted_l[1])
xs_l       = vcat([sorted_l[1] - ext_l], sorted_l, [sorted_l[end] + ext_l])
ys_l       = vcat([0.0], collect(1:n) ./ n, [1.0])

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "ecdf-basic · julia · makie · anyplot.ai",
    titlesize          = 22,
    titlecolor         = INK,
    xlabel             = "Page Load Time (seconds)",
    ylabel             = "Cumulative Proportion",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    yticks             = 0.0:0.1:1.0,
)

# Horizontal reference at P50 (y=0.5) — reads off median directly
hlines!(ax, [0.5];
    color     = RGBAf(INK_SOFT.r, INK_SOFT.g, INK_SOFT.b, 0.30),
    linestyle = :dash,
    linewidth = 1.0,
)

# Vertical drop lines at each group's P50
vlines!(ax, [p50_c];
    color     = RGBAf(IMPRINT_PALETTE[1].r, IMPRINT_PALETTE[1].g, IMPRINT_PALETTE[1].b, 0.45),
    linestyle = :dash,
    linewidth = 1.2,
)
vlines!(ax, [p50_cdn];
    color     = RGBAf(IMPRINT_PALETTE[2].r, IMPRINT_PALETTE[2].g, IMPRINT_PALETTE[2].b, 0.45),
    linestyle = :dash,
    linewidth = 1.2,
)
vlines!(ax, [p50_l];
    color     = RGBAf(IMPRINT_PALETTE[3].r, IMPRINT_PALETTE[3].g, IMPRINT_PALETTE[3].b, 0.45),
    linestyle = :dash,
    linewidth = 1.2,
)

# ECDF step curves
stairs!(ax, xs_c, ys_c;
    step      = :post,
    color     = IMPRINT_PALETTE[1],
    linewidth = 2.5,
    label     = "Cached Server",
)
stairs!(ax, xs_cdn, ys_cdn;
    step      = :post,
    color     = IMPRINT_PALETTE[2],
    linewidth = 2.5,
    label     = "CDN Server",
)
stairs!(ax, xs_l, ys_l;
    step      = :post,
    color     = IMPRINT_PALETTE[3],
    linewidth = 2.5,
    label     = "Legacy Server",
)

# P50 callout annotations — label each median crossing
text!(ax, p50_c,   0.53;
    text      = "P50: $(round(p50_c,   digits=2))s",
    color     = IMPRINT_PALETTE[1],
    fontsize  = 10,
    align     = (:left, :bottom),
)
text!(ax, p50_cdn, 0.53;
    text      = "P50: $(round(p50_cdn, digits=2))s",
    color     = IMPRINT_PALETTE[2],
    fontsize  = 10,
    align     = (:left, :bottom),
)
text!(ax, p50_l,   0.53;
    text      = "P50: $(round(p50_l,   digits=2))s",
    color     = IMPRINT_PALETTE[3],
    fontsize  = 10,
    align     = (:left, :bottom),
)

ylims!(ax, -0.02, 1.05)

axislegend(ax;
    position        = :lt,
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK_SOFT,
    framevisible    = false,
    labelsize       = 12,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
