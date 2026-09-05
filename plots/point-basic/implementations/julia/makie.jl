# anyplot.ai
# point-basic: Point Estimate Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND    = colorant"#009E73"  # Imprint palette position 1 — ALWAYS first series

# --- Data: standardized mean difference (SMD) per clinical trial subgroup ---
subgroups = [
    "Age < 40", "Age 40-59", "Age 60+", "Male", "Female",
    "Prior therapy", "No prior therapy",
]
n = length(subgroups)
estimate = [0.42, 0.31, 0.18, 0.28, 0.35, 0.12, 0.46]
half_width = [0.22, 0.16, 0.20, 0.15, 0.18, 0.24, 0.19]
lower_bound = estimate .- half_width
upper_bound = estimate .+ half_width

order = sortperm(estimate)
subgroups = subgroups[order]
estimate = estimate[order]
lower_bound = lower_bound[order]
upper_bound = upper_bound[order]
positions = 1:n

# --- Plot ---------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "point-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Standardized Mean Difference (95% CI)",
    ylabel             = "Subgroup",
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridvisible       = false,
    yticks             = (positions, subgroups),
)

vlines!(ax, [0.0]; color = INK_SOFT, linestyle = :dash, linewidth = 1.5)
rangebars!(ax, positions, lower_bound, upper_bound;
    direction = :x, color = BRAND, linewidth = 2.5, whiskerwidth = 14)
scatter!(ax, estimate, positions; color = BRAND, markersize = 20, strokewidth = 0)

xlims!(ax, -0.1, 0.85)
ylims!(ax, 0.3, n + 0.7)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
