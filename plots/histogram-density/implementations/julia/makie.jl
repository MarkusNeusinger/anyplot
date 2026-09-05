# anyplot.ai
# histogram-density: Density Histogram
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------
# Net weight (grams) of cereal boxes off a filling line, nominal fill 500 g.
box_weights = 500 .+ 15 .* randn(450)

mu = mean(box_weights)
sigma = std(box_weights)
x_fit = range(minimum(box_weights), maximum(box_weights); length = 200)
pdf_fit = @. 1 / (sigma * sqrt(2π)) * exp(-0.5 * ((x_fit - mu) / sigma)^2)

# --- Plot -----------------------------------------------------------------
title_text = "Cereal Box Net Weight · histogram-density · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_text,
    titlesize         = 19,
    titlecolor        = INK,
    xlabel            = "Net Weight (g)",
    ylabel            = "Density",
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
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

hist!(
    ax, box_weights;
    normalization = :pdf,
    bins          = 25,
    color         = IMPRINT_PALETTE[1],
    strokewidth   = 1,
    strokecolor   = PAGE_BG,
    label         = "Observed boxes",
)

lines!(ax, x_fit, pdf_fit; color = IMPRINT_PALETTE[2], linewidth = 3, label = "Normal fit")

axislegend(
    ax;
    position      = :rt,
    framevisible  = false,
    labelcolor    = INK_SOFT,
    labelsize     = 12,
    backgroundcolor = :transparent,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
