# anyplot.ai
# elbow-curve: Elbow Curve for K-Means Clustering
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------
# Simulated K-means inertia for customer segmentation on behavioral features.
# Inertia falls sharply until the natural cluster count, then flattens.
k_values = collect(1:10)
true_k = 4
base_inertia = 5200.0
decay = [1.0, 0.42, 0.24, 0.15, 0.115, 0.095, 0.081, 0.070, 0.062, 0.056]
noise = randn(length(k_values)) .* 25.0
inertia = base_inertia .* decay .+ noise
inertia = round.(inertia, digits = 1)
elbow_idx = true_k

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "elbow-curve · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Number of Clusters (k)",
    ylabel             = "Inertia (Within-Cluster Sum of Squares)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    xticks             = k_values,
)

lines!(ax, k_values, inertia; color = IMPRINT_PALETTE[1], linewidth = 3.0)
scatter!(ax, k_values, inertia; color = IMPRINT_PALETTE[1], markersize = 16, strokewidth = 1.5, strokecolor = PAGE_BG)

# Highlight the elbow point with an outlined marker in the same brand color.
scatter!(
    ax, [k_values[elbow_idx]], [inertia[elbow_idx]];
    color = PAGE_BG, markersize = 22, strokewidth = 3, strokecolor = IMPRINT_PALETTE[1],
)
accent = IMPRINT_PALETTE[3]  # secondary Imprint accent (blue) for the guide line
vlines!(ax, [k_values[elbow_idx]]; color = RGBAf(accent.r, accent.g, accent.b, 0.55), linewidth = 1.5, linestyle = :dash)

# Label the elbow directly on the chart with a Makie text! annotation.
text!(
    ax, k_values[elbow_idx], inertia[elbow_idx];
    text      = "k=4 (optimal)",
    align     = (:left, :bottom),
    offset    = (12, 12),
    fontsize  = 14,
    color     = accent,
    font      = :bold,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
