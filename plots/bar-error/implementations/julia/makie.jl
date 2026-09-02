# anyplot.ai
# bar-error: Bar Chart with Error Bars
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
BRAND    = colorant"#009E73"  # Imprint palette position 1 — ALWAYS first series

# Data — catalytic reaction yield across catalysts, mean ± 1 SD over 30 runs each
catalysts = ["Pd/C", "Pt/C", "Ru/C", "Ni", "Cu", "Fe"]
mean_yield = [87.4, 82.1, 74.9, 71.6, 63.8, 54.2]
std_yield = [3.1, 4.6, 5.2, 5.8, 6.9, 8.1]
x = 1:length(catalysts)

# Plot — see default-style-guide.md "Visual Sizing Defaults" and prompts/library/makie.md
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "bar-error · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    subtitle          = "Error bars: ±1 SD (n = 30 runs per catalyst)",
    subtitlesize      = 14,
    subtitlecolor     = INK_SOFT,
    xlabel            = "Catalyst",
    ylabel            = "Reaction Yield (%)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xticks            = (x, catalysts),
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible = false,
    yminorgridvisible = false,
)

barplot!(ax, x, mean_yield;
    color       = BRAND,
    strokecolor = PAGE_BG,
    strokewidth = 1.5,
    width       = 0.6,
)
errorbars!(ax, x, mean_yield, std_yield;
    color        = INK,
    linewidth    = 2,
    whiskerwidth = 18,
)

ylims!(ax, 0, nothing)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
