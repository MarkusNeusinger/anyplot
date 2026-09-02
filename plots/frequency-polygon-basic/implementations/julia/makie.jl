# anyplot.ai
# frequency-polygon-basic: Frequency Polygon for Distribution Comparison
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 83/100 | Created: 2026-09-02

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
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3",
]

# --- Data ---------------------------------------------------------------
# Reaction times (ms) across three experimental conditions in a psychology study
n_per_group = 300
conditions = ["Control", "Caffeine", "Sleep-deprived"]
reaction_times = [
    280 .+ 45 .* randn(n_per_group),
    250 .+ 38 .* randn(n_per_group),
    340 .+ 60 .* randn(n_per_group),
]

# Shared bin edges across all groups for accurate comparison
all_values = vcat(reaction_times...)
n_bins = 24
lo, hi = minimum(all_values), maximum(all_values)
edges = range(lo, hi; length = n_bins + 1)
bin_width = step(edges)
midpoints = [(edges[i] + edges[i + 1]) / 2 for i in 1:n_bins]

# Bin each group onto the shared edges, closing the polygon to zero at both ends
polygon_xs = Vector{Vector{Float64}}()
polygon_ys = Vector{Vector{Int}}()
for values in reaction_times
    counts = zeros(Int, n_bins)
    for v in values
        idx = clamp(searchsortedlast(edges, v), 1, n_bins)
        counts[idx] += 1
    end
    push!(polygon_xs, vcat(midpoints[1] - bin_width, midpoints, midpoints[end] + bin_width))
    push!(polygon_ys, vcat(0, counts, 0))
end

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "frequency-polygon-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Reaction Time (ms)",
    ylabel             = "Frequency",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

# Sleep-deprived carries the widest, longest-tailed distribution — the story
# of this chart — so it gets a heavier line to draw the eye toward it.
linestyles = [:solid, :dash, :solid]
linewidths = [3, 3, 4]

for (i, label) in enumerate(conditions)
    xs, ys = polygon_xs[i], polygon_ys[i]
    color = IMPRINT_PALETTE[i]
    band!(ax, xs, zeros(length(ys)), ys; color = RGBAf(color.r, color.g, color.b, 0.15))
    lines!(ax, xs, ys; color = color, linewidth = linewidths[i], linestyle = linestyles[i], label = label)
end

axislegend(ax; position = :rt, framevisible = false, labelcolor = INK_SOFT)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
