# anyplot.ai
# histogram-basic: Basic Histogram
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-05-28

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME   = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK     = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND   = colorant"#009E73"

# Data — customer age distribution (bimodal: young adults + mid-career segment)
ages_young  = randn(200) .* 5 .+ 28
ages_mid    = randn(150) .* 8 .+ 55
ages        = vcat(ages_young, ages_mid)
ages        = clamp.(ages, 18, 75)

# Plot
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "histogram-basic · julia · makie · anyplot.ai",
    titlesize         = 22,
    titlecolor        = INK,
    xlabel            = "Customer Age",
    ylabel            = "Count",
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
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15f0),
    yminorgridvisible = false,
    xminorgridvisible = false,
)

hist!(ax, ages;
    bins        = 28,
    color       = BRAND,
    strokecolor = PAGE_BG,
    strokewidth = 1.5,
)

# Bimodal valley reference line separating the two customer segments
vlines!(ax, [42.0]; color = INK_SOFT, linestyle = :dash, linewidth = 1.5)

# Segment annotations above each distribution peak
text!(ax, 27.0, 37.0; text = "Young Adult\nSegment", color = INK,
    fontsize = 12, align = (:center, :bottom))
text!(ax, 55.0, 19.0; text = "Mid-Career\nSegment", color = INK,
    fontsize = 12, align = (:center, :bottom))

ylims!(ax, 0, 52)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
