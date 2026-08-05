# anyplot.ai
# bar-grouped: Grouped Bar Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 70/100 | Created: 2026-08-05

using CairoMakie
using Colors

# --- Theme tokens -------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -----------------------------------------------------------------
# Quarterly hardware/software/services revenue ($M) across five regions.
categories = ["N. America", "Europe", "Asia-Pacific", "Latin America", "MEA"]
groups     = ["Hardware", "Software", "Services"]

# rows = categories, cols = groups
revenue = [
    42.0 28.0 15.0
    35.0 31.0 18.0
    27.0 22.0 12.0
    18.0 14.0  9.0
    12.0  9.0  6.0
]

n_cat = length(categories)
n_grp = length(groups)

x      = repeat(1:n_cat, inner = n_grp)
dodge  = repeat(1:n_grp, outer = n_cat)
height = vec(permutedims(revenue))
colors = IMPRINT_PALETTE[repeat(1:n_grp, outer = n_cat)]

# --- Plot -------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "bar-grouped · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Region",
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
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    yminorgridvisible = false,
)

barplot!(
    ax, x, height;
    dodge     = dodge,
    color     = colors,
    width     = 0.85,
    dodge_gap = 0.03,
    gap       = 0.25,
)

ax.xticks = (1:n_cat, categories)

# --- Data storytelling: per-region totals, leading region called out -------
totals      = vec(sum(revenue, dims = 2))
max_per_cat = vec(maximum(revenue, dims = 2))
top_idx     = argmax(totals)

ylims!(ax, 0, maximum(revenue) + 10)

for i in 1:n_cat
    text!(
        ax, i, max_per_cat[i] + 1.5;
        text     = "\$$(round(Int, totals[i]))M",
        align    = (:center, :bottom),
        fontsize = 12,
        color    = INK_SOFT,
    )
end

text!(
    ax, top_idx, max_per_cat[top_idx] + 5.5;
    text     = "▲ leading region",
    align    = (:center, :bottom),
    fontsize = 12,
    color    = INK,
    font     = :bold,
)

legend_elements = [PolyElement(color = IMPRINT_PALETTE[i]) for i in 1:n_grp]
Legend(
    fig[1, 2], legend_elements, groups, "Product Line";
    labelcolor      = INK_SOFT,
    titlecolor      = INK,
    framevisible    = false,
    backgroundcolor = PAGE_BG,
)

colgap!(fig.layout, 1, 24)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
