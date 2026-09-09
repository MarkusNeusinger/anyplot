# anyplot.ai
# silhouette-basic: Silhouette Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-09

using CairoMakie
using Colors
using Random
using Statistics

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

# --- Data: synthetic clustering result, one pair of clusters overlapping ---
# to produce a realistic mix of strong and borderline silhouette scores.
n_per_cluster = 50
n_clusters = 3
centers = [(0.0, 0.0), (4.2, 0.0), (2.0, 3.2)]
spreads = [1.0, 1.0, 1.3]

feature_x = Float64[]
feature_y = Float64[]
cluster_labels = Int[]
for c in 1:n_clusters
    cx, cy = centers[c]
    append!(feature_x, cx .+ spreads[c] .* randn(n_per_cluster))
    append!(feature_y, cy .+ spreads[c] .* randn(n_per_cluster))
    append!(cluster_labels, fill(c - 1, n_per_cluster))
end
n_samples = length(feature_x)

# --- Silhouette coefficient per sample (computed directly: a(i), b(i)) -----
euclidean(i, j) = sqrt((feature_x[i] - feature_x[j])^2 + (feature_y[i] - feature_y[j])^2)

silhouette_values = zeros(n_samples)
for i in 1:n_samples
    own_cluster = cluster_labels[i]
    same_idx = [j for j in 1:n_samples if cluster_labels[j] == own_cluster && j != i]
    a_i = isempty(same_idx) ? 0.0 : mean(euclidean(i, j) for j in same_idx)

    b_i = Inf
    for c in 0:(n_clusters - 1)
        c == own_cluster && continue
        other_idx = [j for j in 1:n_samples if cluster_labels[j] == c]
        b_i = min(b_i, mean(euclidean(i, j) for j in other_idx))
    end

    silhouette_values[i] = isempty(same_idx) ? 0.0 : (b_i - a_i) / max(a_i, b_i)
end
avg_silhouette = mean(silhouette_values)

# --- Arrange bars: grouped by cluster, ascending within cluster, gapped ----
cluster_gap = 8
y_positions = Float64[]
bar_values = Float64[]
bar_colors = RGB[]
cluster_center_y = Float64[]
cluster_avg_silhouette = Float64[]
cluster_max_silhouette = Float64[]

y_cursor = cluster_gap
for c in 0:(n_clusters - 1)
    global y_cursor
    idx = findall(==(c), cluster_labels)
    sorted_vals = sort(silhouette_values[idx])
    size_c = length(sorted_vals)

    append!(y_positions, y_cursor:(y_cursor + size_c - 1))
    append!(bar_values, sorted_vals)
    append!(bar_colors, fill(IMPRINT_PALETTE[c + 1], size_c))

    push!(cluster_center_y, y_cursor + size_c / 2 - 0.5)
    push!(cluster_avg_silhouette, mean(sorted_vals))
    push!(cluster_max_silhouette, maximum(sorted_vals))

    y_cursor += size_c + cluster_gap
end

x_upper = maximum(cluster_max_silhouette) + 0.18

# --- Plot ---------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "silhouette-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Silhouette Coefficient",
    ylabel             = "Cluster",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    yticksvisible      = false,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridvisible       = false,
    yticks             = (cluster_center_y, ["Cluster $(c)" for c in 0:(n_clusters - 1)]),
)

barplot!(ax, y_positions, bar_values;
    direction = :x, color = bar_colors, gap = 0.0, strokewidth = 0)

vlines!(ax, [avg_silhouette]; color = INK_SOFT, linestyle = :dash, linewidth = 2)

for c in 0:(n_clusters - 1)
    text!(ax, cluster_max_silhouette[c + 1] + 0.03, cluster_center_y[c + 1];
        text = "avg = $(round(cluster_avg_silhouette[c + 1], digits = 2))",
        align = (:left, :center),
        color = INK,
        fontsize = 13,
    )
end

xlims!(ax, min(-0.15, minimum(bar_values) - 0.05), x_upper)
ylims!(ax, 0, y_cursor)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
