# anyplot.ai
# line-impurity-comparison: Gini Impurity vs Entropy Comparison
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-05-29

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

# Data — probability range, Gini impurity, and normalized binary entropy
p = range(0.0, 1.0; length = 100)

gini_raw = 2 .* p .* (1 .- p)
gini     = gini_raw ./ maximum(gini_raw)

entropy_raw = [q <= 0.0 || q >= 1.0 ? 0.0 : -q * log2(q) - (1 - q) * log2(1 - q) for q in p]
entropy     = entropy_raw ./ maximum(entropy_raw)

# Plot
title_str = "Gini vs Entropy · line-impurity-comparison · julia · makie · anyplot.ai"
title_n   = length(title_str)
title_sz  = title_n > 67 ? round(Int, 20 * 67 / title_n) : 20

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = title_sz,
    titlecolor         = INK,
    xlabel             = "Probability p",
    ylabel             = "Impurity (normalized to [0, 1])",
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
    ygridvisible       = true,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

band!(ax, collect(p), gini, entropy;
    color = (IMPRINT_PALETTE[3], 0.12))

lines!(ax, collect(p), gini;
    color     = IMPRINT_PALETTE[1],
    linewidth = 3.0,
    label     = "Gini:  2p(1−p)  [normalized]")

lines!(ax, collect(p), entropy;
    color     = IMPRINT_PALETTE[2],
    linewidth = 3.0,
    linestyle = :dash,
    label     = "Entropy:  −p log₂p − (1−p) log₂(1−p)")

# Annotate maximum impurity point at p = 0.5 (spec requirement)
vlines!(ax, [0.5];
    color     = INK_MUTED,
    linewidth = 1.5,
    linestyle = :dot)

text!(ax, 0.52, 0.97;
    text     = "max at p = 0.5",
    color    = INK_MUTED,
    fontsize = 13,
    align    = (:left, :top))

Legend(fig[1, 2], ax;
    framecolor      = RGBAf(INK_SOFT.r, INK_SOFT.g, INK_SOFT.b, 0.4f0),
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
