# anyplot.ai
# violin-box: Violin Plot with Embedded Box Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-09

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG      = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG  = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK          = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT     = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED    = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const GRID_COLOR   = RGBAf(INK.r, INK.g, INK.b, 0.15)

# Imprint categorical palette — first series is ALWAYS brand green
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — Control
    colorant"#C475FD",  # 2 — Mild Stress
    colorant"#4467A3",  # 3 — High Stress
]

# --- Data ---------------------------------------------------------------
# Salivary cortisol response (ng/mL) under three lab-controlled stress conditions
groups = ["Control", "Mild Stress", "High Stress"]
n_per_group = 150
group_means = [8.5, 12.0, 17.5]
group_sds = [1.8, 2.6, 3.4]

group_index = Int[]
cortisol_level = Float64[]
for (i, (mean_level, sd_level)) in enumerate(zip(group_means, group_sds))
    append!(group_index, fill(i, n_per_group))
    append!(cortisol_level, mean_level .+ sd_level .* randn(n_per_group))
end
violin_colors = [IMPRINT_PALETTE[i] for i in group_index]

# --- Plot -----------------------------------------------------------------
title_text = "Cortisol Response by Stress Condition · violin-box · julia · makie · anyplot.ai"

fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title             = title_text,
    titlesize         = 17,
    titlecolor        = INK,
    xlabel            = "Stress Test Condition",
    ylabel            = "Cortisol Level (ng/mL)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticks            = (1:3, groups),
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridcolor        = GRID_COLOR,
    yminorgridvisible = false,
)

violin!(
    ax, group_index, cortisol_level;
    color = violin_colors, strokecolor = INK, strokewidth = 1.5,
    width = 0.75, show_median = false,
)
boxplot!(
    ax, group_index, cortisol_level;
    width = 0.12, color = ELEVATED_BG, strokecolor = INK, strokewidth = 1.2,
    mediancolor = INK, medianlinewidth = 2.5,
    whiskercolor = INK, whiskerwidth = 0.5, whiskerlinewidth = 1.5,
    outliercolor = INK_MUTED, markersize = 6, show_outliers = true,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
