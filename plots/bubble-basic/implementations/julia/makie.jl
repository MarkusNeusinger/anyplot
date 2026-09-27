# anyplot.ai
# bubble-basic: Basic Bubble Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 90/100 | Updated: 2026-09-27

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
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const IMPRINT_PALETTE = [colorant"#009E73", colorant"#C475FD", colorant"#4467A3"]

# Data — product portfolio with a visible narrative:
#   higher price correlates with better ratings (premium positioning),
#   but mid-range products (~$150-280) capture the highest sales volume
n          = 65
price_norm = rand(n)                          # uniform [0, 1]
price      = 20.0 .+ 480.0 .* price_norm     # $20-$500

# Rating rises with price (r ≈ 0.65): premium commands better quality perception
quality = clamp.(1.5 .+ 2.5 .* price_norm .+ 0.45 .* randn(n), 1.5, 4.5)

# Sales peak at mid-range ~$200 and fall off at both extremes (sweet-spot effect)
sweet_spot = (price .- 200.0) ./ 160.0
sales = clamp.(15.0 .+ 80.0 .* exp.(-0.5 .* sweet_spot .^ 2) .+ 8.0 .* randn(n), 10.0, 100.0)

# Scale marker sizes proportional to area (visual area ∝ data value)
s_min, s_max = extrema(sales)
s_norm       = (sales .- s_min) ./ (s_max - s_min)
marker_sizes = 10.0 .+ 55.0 .* sqrt.(s_norm)

# Product tier — a distinct categorical variable (not derived from sales) so
# color and size each carry their own signal instead of duplicating one.
tier_idx    = ifelse.(price .< 150.0, 1, ifelse.(price .< 280.0, 2, 3))
tier_names  = ["Budget (<\$150)", "Mid-range (\$150–280)", "Premium (>\$280)"]
point_color = IMPRINT_PALETTE[tier_idx]

# Plot
title_str = "bubble-basic · julia · makie · anyplot.ai"

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Price (USD)",
    ylabel            = "Customer Rating",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

# Highlight the mid-range sweet spot where sales peak — makes the DE-03
# narrative explicit instead of leaving it implicit in the data alone.
vspan!(ax, 150.0, 280.0; color = RGBAf(INK.r, INK.g, INK.b, 0.06))
text!(ax, 215.0, 4.55;
    text     = "peak sales zone",
    align    = (:center, :bottom),
    fontsize = 14,
    color    = INK_SOFT,
)

# Bubble area (sqrt-scaled) encodes annual sales; fill color encodes product
# tier — two independent variables, each with its own legend group below.
scatter!(ax, price, quality;
    color       = point_color,
    markersize  = marker_sizes,
    alpha       = 0.65,
    strokewidth = 1.0,
    strokecolor = RGBAf(INK.r, INK.g, INK.b, 0.35),
)

# Tier legend — fixed-size swatches, one per product tier
tier_elems = [
    MarkerElement(
        color       = IMPRINT_PALETTE[i],
        marker      = :circle,
        markersize  = 18,
        strokewidth = 1.0,
        strokecolor = RGBAf(INK.r, INK.g, INK.b, 0.35),
    )
    for i in eachindex(IMPRINT_PALETTE)
]

# Size legend — neutral-colored reference bubbles show the area scale only
ref_vals = [10, 40, 70, 100]
ref_norm = clamp.((Float64.(ref_vals) .- s_min) ./ (s_max - s_min), 0.0, 1.0)
ref_ms   = 10.0 .+ 55.0 .* sqrt.(ref_norm)

size_elems = [
    MarkerElement(
        color       = RGBAf(INK_MUTED.r, INK_MUTED.g, INK_MUTED.b, 0.65),
        marker      = :circle,
        markersize  = ref_ms[i],
        strokewidth = 1.0,
        strokecolor = RGBAf(INK.r, INK.g, INK.b, 0.35),
    )
    for i in eachindex(ref_ms)
]

Legend(fig[1, 2],
    [tier_elems, size_elems],
    [tier_names, string.(ref_vals) .* " units"],
    ["Product Tier", "Annual Sales"];
    backgroundcolor = ELEVATED_BG,
    framecolor      = INK_SOFT,
    labelcolor      = INK_SOFT,
    titlecolor      = INK,
    patchsize       = (60, 40),
    labelsize       = 13,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
