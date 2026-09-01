# anyplot.ai
# coefficient-confidence: Coefficient Plot with Confidence Intervals
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-09-01

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME     = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
BRAND     = colorant"#009E73"  # Imprint palette position 1 — significant coefficients

# Data — coefficients from a multiple linear regression predicting housing sale
# price (thousands of USD), controlling for all other predictors.
variables = [
    "Square Footage", "Distance to Downtown (mi)", "Bathrooms", "School Rating",
    "Garage Spaces", "Renovated (Y/N)", "Lot Size (acres)", "Bedrooms", "Age (years)",
]
coefficients = [45.2, -12.6, 18.7, 15.3, 9.8, 8.1, 6.4, -3.2, -2.1]
standard_errors = 0.28 .* abs.(coefficients) .+ 1.2 .+ 2.0 .* rand(length(coefficients))
ci_lower = coefficients .- 1.96 .* standard_errors
ci_upper = coefficients .+ 1.96 .* standard_errors
significant = .!((ci_lower .<= 0) .& (0 .<= ci_upper))

# Order by coefficient magnitude, largest effect first (drawn at the top)
order = sortperm(abs.(coefficients), rev = true)
variables = variables[order]
coefficients = coefficients[order]
ci_lower = ci_lower[order]
ci_upper = ci_upper[order]
significant = significant[order]

n = length(variables)
y_positions = collect(n:-1:1)
point_colors = [sig ? BRAND : INK_MUTED for sig in significant]

# Plot
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "coefficient-confidence · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Coefficient Estimate (Δ Sale Price, \$ thousands)",
    xlabelsize        = 16,
    xlabelcolor       = INK,
    xticklabelsize    = 14,
    xticklabelcolor   = INK_SOFT,
    yticks            = (1:n, reverse(variables)),
    yticklabelsize    = 14,
    yticklabelcolor   = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = true,
    ygridvisible       = false,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

vlines!(ax, [0.0]; color = INK_SOFT, linestyle = :dash, linewidth = 2)

errorbars!(
    ax, coefficients, y_positions,
    coefficients .- ci_lower, ci_upper .- coefficients;
    direction = :x, color = point_colors, whiskerwidth = 14, linewidth = 3,
)
scatter!(
    ax, coefficients, y_positions;
    color = point_colors, markersize = 22, strokewidth = 1.5, strokecolor = PAGE_BG,
)

# Legend — semantic mapping must be explicit per style guide
elem_sig = MarkerElement(color = BRAND, marker = :circle, markersize = 22, strokewidth = 1.5, strokecolor = PAGE_BG)
elem_ns  = MarkerElement(color = INK_MUTED, marker = :circle, markersize = 22, strokewidth = 1.5, strokecolor = PAGE_BG)
axislegend(
    ax, [elem_sig, elem_ns], ["Significant (95% CI excludes zero)", "Not significant"];
    position = :rb, labelcolor = INK_SOFT, labelsize = 13,
    backgroundcolor = (THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"),
    framevisible = false,
)

xlims!(ax, minimum(ci_lower) - 3, maximum(ci_upper) + 3)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
