# anyplot.ai
# box-grouped: Grouped Box Plot
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-08-18

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — 8 hues, theme-independent, hybrid-v3 sort
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
]

# Data — quarterly performance review scores by department and experience level
const DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Support"]
const EXPERIENCE_LEVELS = ["Junior", "Mid-Level", "Senior"]
const DEPT_BASELINE = [72.0, 68.0, 70.0, 65.0]
const EXPERIENCE_BONUS = [0.0, 7.0, 15.0]
const N_PER_GROUP = 45

category_idx = Int[]
subgroup_idx = Int[]
performance_scores = Float64[]

for (ci, baseline) in enumerate(DEPT_BASELINE)
    for (si, bonus) in enumerate(EXPERIENCE_BONUS)
        scores = clamp.(baseline .+ bonus .+ randn(N_PER_GROUP) .* 7.0, 20.0, 100.0)
        append!(performance_scores, scores)
        append!(category_idx, fill(ci, N_PER_GROUP))
        append!(subgroup_idx, fill(si, N_PER_GROUP))
    end
end

point_colors = IMPRINT_PALETTE[subgroup_idx]

# Plot — see default-style-guide.md "Visual Sizing Defaults" for canvas + sizing values
title_str = "box-grouped · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = 20,
    titlecolor        = INK,
    ylabel            = "Performance Score",
    ylabelsize        = 14,
    ylabelcolor       = INK,
    xticks            = (1:length(DEPARTMENTS), DEPARTMENTS),
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

boxplot!(
    ax, category_idx, performance_scores;
    dodge         = subgroup_idx,
    color         = point_colors,
    width         = 0.7,
    dodge_gap     = 0.05,
    gap           = 0.3,
    strokecolor   = INK,
    strokewidth   = 1,
    mediancolor   = INK,
    whiskercolor  = INK_SOFT,
    markersize    = 6,
)

legend_elements = [PolyElement(color = c, strokecolor = :transparent) for c in IMPRINT_PALETTE]
Legend(
    fig[1, 2], legend_elements, EXPERIENCE_LEVELS, "Experience Level";
    framevisible = false,
    labelcolor   = INK,
    titlecolor   = INK,
    labelsize    = 12,
    titlesize    = 12,
)
colsize!(fig.layout, 2, Relative(0.14))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
