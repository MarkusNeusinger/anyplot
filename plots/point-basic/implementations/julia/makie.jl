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
baseline_estimate   = [0.42, 0.31, 0.18, 0.28, 0.35, 0.12, 0.46]
baseline_half_width = [0.22, 0.16, 0.22, 0.15, 0.18, 0.24, 0.19]
estimate    = baseline_estimate .+ (rand(n) .- 0.5) .* 0.02
half_width  = baseline_half_width .+ (rand(n) .- 0.5) .* 0.02
lower_bound = estimate .- half_width
upper_bound = estimate .+ half_width

order = sortperm(estimate)
subgroups   = subgroups[order]
estimate    = estimate[order]
lower_bound = lower_bound[order]
upper_bound = upper_bound[order]
positions   = 1:n
crosses_null = (lower_bound .< 0) .& (upper_bound .> 0)

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
    xlabelsize         = 15,
    ylabelsize         = 15,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 14,
    yticklabelsize     = 14,
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

# Filled markers = CI excludes the null; open (hollow) markers = CI spans it —
# a classic forest-plot convention that reads at a glance without adding a
# second hue (palette stays single-accent).
sig, nonsig = .!crosses_null, crosses_null
scatter!(ax, estimate[sig], positions[sig];
    color = BRAND, markersize = 20, strokewidth = 0)
scatter!(ax, estimate[nonsig], positions[nonsig];
    color = PAGE_BG, markersize = 20, strokewidth = 2.5, strokecolor = BRAND)

xlims!(ax, -0.1, 0.85)
ylims!(ax, 0.3, n + 0.7)

Label(fig[2, 1], "○ open marker — 95% CI spans the null (SMD = 0)";
    color = INK_SOFT, fontsize = 13, halign = :left, padding = (6, 0, 0, 4))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
