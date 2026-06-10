# anyplot.ai
# funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-06-10

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (first series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data: 20 RCTs on antihypertensive drug vs placebo (log odds ratio of major CV events)
const summary_effect = -0.38
std_errors = [0.07, 0.09, 0.11, 0.12, 0.14, 0.16, 0.18, 0.20, 0.23, 0.25,
              0.28, 0.31, 0.33, 0.36, 0.38, 0.41, 0.44, 0.47, 0.50, 0.54]
n_studies = length(std_errors)
# Slight small-study asymmetry: smaller trials claim larger benefit (publication bias)
small_study_bias = -0.25 .* (std_errors ./ maximum(std_errors))
effect_sizes = summary_effect .+ small_study_bias .+ randn(n_studies) .* std_errors

# Funnel 95% confidence limit boundary
max_se_plot = maximum(std_errors) * 1.12
n_pts = 200
se_grid  = collect(range(0.0, max_se_plot; length=n_pts))
funnel_lo = summary_effect .- 1.96 .* se_grid
funnel_hi = summary_effect .+ 1.96 .* se_grid

# Funnel fill polygon (trace lo top→bottom, then hi bottom→top)
funnel_polygon = [
    [Point2f(funnel_lo[i], se_grid[i]) for i in 1:n_pts];
    [Point2f(funnel_hi[i], se_grid[i]) for i in n_pts:-1:1]
]

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(fig[1, 1];
    title             = "funnel-meta-analysis · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Log Odds Ratio",
    ylabel            = "Standard Error",
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
    ygridvisible      = false,
    yreversed         = true,
)

# Funnel shaded region
poly!(ax, funnel_polygon;
    color       = RGBAf(INK_MUTED.r, INK_MUTED.g, INK_MUTED.b, 0.12),
    strokewidth = 0)

# 95% CI boundary lines
lines!(ax, funnel_lo, se_grid; color = INK_SOFT, linewidth = 1.5, linestyle = :dash)
lines!(ax, funnel_hi, se_grid; color = INK_SOFT, linewidth = 1.5, linestyle = :dash)

# Null effect reference line (log OR = 0 ↔ OR = 1)
vlines!(ax, [0.0]; color = INK_MUTED, linewidth = 1.5, linestyle = :dot)

# Pooled effect line
vlines!(ax, [summary_effect]; color = IMPRINT_PALETTE[3], linewidth = 2.0)

# Individual study points
scatter!(ax, effect_sizes, std_errors;
    color       = IMPRINT_PALETTE[1],
    markersize  = 14,
    strokewidth = 1.0,
    strokecolor = PAGE_BG)

# Axis limits
ylims!(ax, (0.0, max_se_plot))
xlims!(ax, (funnel_lo[end] - 0.08, funnel_hi[end] + 0.08))

# Legend
elem_studies = MarkerElement(marker = :circle, color = IMPRINT_PALETTE[1],
    strokecolor = PAGE_BG, strokewidth = 1.0, markersize = 14)
elem_pooled  = LineElement(color = IMPRINT_PALETTE[3], linewidth = 2.0)
elem_null    = LineElement(color = INK_MUTED, linewidth = 1.5, linestyle = :dot)
elem_ci      = LineElement(color = INK_SOFT,  linewidth = 1.5, linestyle = :dash)

Legend(fig[1, 2],
    [elem_studies, elem_pooled, elem_null, elem_ci],
    ["Individual study (n=20)",
     "Pooled effect (OR = $(round(exp(summary_effect), digits=2)))",
     "Null effect (OR = 1.0)",
     "95% confidence limits"],
    framevisible    = true,
    framecolor      = INK_SOFT,
    backgroundcolor = ELEVATED_BG,
    labelsize       = 11,
    padding         = (12, 12, 10, 10),
    rowgap          = 6,
)

colsize!(fig.layout, 1, Relative(0.80))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
