# anyplot.ai
# bar-stacked-labeled: Stacked Bar Chart with Total Labels
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-08-26

using CairoMakie
using Colors

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -------------------------------------------------------------------
# Quarterly SaaS revenue split by product line ($M, illustrative).
quarters      = ["Q1", "Q2", "Q3", "Q4"]
product_lines = ["Subscriptions", "Services", "Hardware"]

revenue = [
    5.2 2.1 1.4
    5.8 2.3 1.3
    6.5 2.6 1.5
    7.3 3.0 1.6
]

n_quarter = length(quarters)
n_product = length(product_lines)

x      = repeat(1:n_quarter, inner = n_product)
stack  = repeat(1:n_product, outer = n_quarter)
height = vec(permutedims(revenue))
colors = IMPRINT_PALETTE[repeat(1:n_product, outer = n_quarter)]

totals = vec(sum(revenue, dims = 2))

# --- Plot ---------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "bar-stacked-labeled · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Quarter",
    ylabel            = "Revenue (\$M)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 13,
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
    ygridvisible      = true,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.12),
    yminorgridvisible = false,
)

barplot!(
    ax, x, height;
    stack       = stack,
    color       = colors,
    width       = 0.6,
    strokewidth = 0,
)

ax.xticks = (1:n_quarter, quarters)

# --- Total labels: bold and larger than any other text, directly above the
# tallest segment of each stack -----------------------------------------
for (i, total) in enumerate(totals)
    text!(
        ax, Point2f(i, total);
        text     = "\$$(round(total, digits = 1))M",
        offset   = (0, 8),
        align    = (:center, :bottom),
        fontsize = 19,
        color    = INK,
    )
end

Legend(
    fig[1, 2], [PolyElement(color = c) for c in IMPRINT_PALETTE[1:n_product]], product_lines;
    labelcolor      = INK_SOFT,
    labelsize       = 13,
    framevisible    = false,
    backgroundcolor = PAGE_BG,
)

# Fix the y-range last so the label headroom above the tallest bar survives
# any autolimits reset triggered by the legend/text calls above.
ylims!(ax, 0, maximum(totals) * 1.16)

# --- Save ---------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
