# anyplot.ai
# pyramid-basic: Basic Pyramid Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 90/100 | Created: 2026-09-05

using CairoMakie
using Colors

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const GRID     = RGBAf(INK.r, INK.g, INK.b, 0.15)

# Imprint palette — Agree is positive sentiment (brand green, position 1),
# Disagree is negative sentiment (matte red, semantic anchor)
const AGREE_COLOR    = colorant"#009E73"
const DISAGREE_COLOR = colorant"#AE3030"

# Data — employee survey on workplace policies, sorted most- to least-agreed
policies = [
    "Flexible Hours",
    "Remote Work Days",
    "Four-Day Workweek",
    "Unlimited PTO Policy",
    "Open Floor Plan",
    "Annual Performance Reviews",
    "Mandatory Team Retreats",
    "Return-to-Office Mandate",
    "Mandatory Overtime",
]
agree_pct    = [82, 74, 68, 61, 39, 33, 28, 22, 12]
disagree_pct = [8, 15, 20, 24, 47, 52, 58, 68, 79]
positions = 1:length(policies)

# Plot
title_str = "Employee Policy Survey · pyramid-basic · julia · makie · anyplot.ai"
title_fontsize = round(Int, 20 * min(1.0, 67 / length(title_str)))

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = title_fontsize,
    titlecolor        = INK,
    xlabel            = "Respondents",
    xlabelcolor       = INK,
    xlabelsize        = 14,
    xticklabelcolor   = INK_SOFT,
    xticklabelsize    = 12,
    xticks            = (-80:20:80, [string(abs(v)) * "%" for v in -80:20:80]),
    yticks            = (positions, policies),
    yticklabelcolor   = INK_SOFT,
    yticklabelsize    = 12,
    yreversed         = true,
    backgroundcolor   = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = GRID,
    ygridvisible       = false,
)
xlims!(ax, -95, 95)

barplot!(ax, positions, -disagree_pct; direction = :x, color = DISAGREE_COLOR, label = "Disagree")
barplot!(ax, positions, agree_pct; direction = :x, color = AGREE_COLOR, label = "Agree")
vlines!(ax, 0; color = INK_SOFT, linewidth = 1)

Legend(fig[1, 2], ax; framevisible = false, labelcolor = INK)
colsize!(fig.layout, 2, Auto(0.18))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
