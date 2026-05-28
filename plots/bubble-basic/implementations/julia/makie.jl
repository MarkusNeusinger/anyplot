# anyplot.ai
# bubble-basic: Basic Bubble Chart
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-05-28

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
const BRAND       = colorant"#009E73"

# Data — product portfolio with a visible narrative:
#   higher price correlates with better ratings (premium positioning),
#   but mid-range products (~$150–$280) capture the highest sales volume
n          = 65
price_norm = rand(n)                          # uniform [0, 1]
price      = 20.0 .+ 480.0 .* price_norm     # $20–$500

# Rating rises with price (r ≈ 0.65): premium commands better quality perception
quality = clamp.(1.5 .+ 2.5 .* price_norm .+ 0.45 .* randn(n), 1.5, 4.5)

# Sales peak at mid-range ~$200 and fall off at both extremes (sweet-spot effect)
sweet_spot = (price .- 200.0) ./ 160.0
sales = clamp.(15.0 .+ 80.0 .* exp.(-0.5 .* sweet_spot .^ 2) .+ 8.0 .* randn(n), 10.0, 100.0)

# Scale marker sizes proportional to area (visual area ∝ data value)
s_min, s_max = extrema(sales)
s_norm       = (sales .- s_min) ./ (s_max - s_min)
marker_sizes = 10.0 .+ 55.0 .* sqrt.(s_norm)

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

scatter!(ax, price, quality;
    color       = RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.6f0),
    markersize  = marker_sizes,
    strokewidth = 1.0,
    strokecolor = RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.9f0),
)

# Size legend — reference bubbles showing annual sales scale
ref_vals = [10, 40, 70, 100]
ref_norm = clamp.((Float64.(ref_vals) .- s_min) ./ (s_max - s_min), 0.0, 1.0)
ref_ms   = 10.0 .+ 55.0 .* sqrt.(ref_norm)

legend_elems = [
    MarkerElement(
        color       = RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.6f0),
        marker      = :circle,
        markersize  = ms,
        strokewidth = 1.0,
        strokecolor = RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.9f0),
    )
    for ms in ref_ms
]

Legend(fig[1, 2], legend_elems, string.(ref_vals) .* " units", "Annual Sales";
    backgroundcolor = ELEVATED_BG,
    framecolor      = INK_SOFT,
    labelcolor      = INK_SOFT,
    titlecolor      = INK,
    patchsize       = (80, 55),
    labelsize       = 13,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
