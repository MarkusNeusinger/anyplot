# anyplot.ai
# biplot-pca: PCA Biplot with Scores and Loading Vectors
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-01

using CairoMakie
using Colors
using RDatasets
using Statistics
using LinearAlgebra

# --- Theme tokens ------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------------
iris = RDatasets.dataset("datasets", "iris")
feature_names = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
features = Matrix(iris[:, [:SepalLength, :SepalWidth, :PetalLength, :PetalWidth]])
species = String.(iris.Species)
groups = unique(species)

# Standardize so PCA decomposes the correlation matrix, not the covariance matrix
feature_means = mean(features; dims = 1)
feature_stds = std(features; dims = 1)
standardized = (features .- feature_means) ./ feature_stds

# Eigen-decompose the correlation matrix, sorted by descending eigenvalue
correlation = Symmetric(cor(standardized))
eigen_result = eigen(correlation)
order = sortperm(eigen_result.values; rev = true)
eigenvalues = eigen_result.values[order]
eigenvectors = eigen_result.vectors[:, order]

variance_explained = eigenvalues ./ sum(eigenvalues) .* 100
scores = standardized * eigenvectors[:, 1:2]
loadings = eigenvectors[:, 1:2] .* sqrt.(eigenvalues[1:2])'

# Scale correlation loadings so the arrows sit alongside the score cloud
score_radius = maximum(sqrt.(scores[:, 1] .^ 2 .+ scores[:, 2] .^ 2))
loading_radius = maximum(sqrt.(loadings[:, 1] .^ 2 .+ loadings[:, 2] .^ 2))
arrow_scale = 0.85 * score_radius / loading_radius
arrow_xy = loadings .* arrow_scale

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

pc1_label = "PC1 ($(round(variance_explained[1]; digits = 1))%)"
pc2_label = "PC2 ($(round(variance_explained[2]; digits = 1))%)"

ax = Axis(
    fig[1, 1];
    title              = "biplot-pca · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = pc1_label,
    ylabel             = pc2_label,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xlabelsize         = 14,
    ylabelsize         = 14,
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
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    aspect             = DataAspect(),
)

# Unit circle reference for the correlation-scaled loadings
circle_theta = range(0, 2π; length = 200)
lines!(ax, cos.(circle_theta) .* arrow_scale, sin.(circle_theta) .* arrow_scale;
    color = INK_SOFT, linestyle = :dash, linewidth = 1.5)

hlines!(ax, [0]; color = RGBAf(INK.r, INK.g, INK.b, 0.3), linewidth = 1)
vlines!(ax, [0]; color = RGBAf(INK.r, INK.g, INK.b, 0.3), linewidth = 1)

for (i, group) in enumerate(groups)
    mask = species .== group
    scatter!(ax, scores[mask, 1], scores[mask, 2];
        color = IMPRINT_PALETTE[i], markersize = 12, strokewidth = 0, label = group)
end

arrows!(ax, zeros(length(feature_names)), zeros(length(feature_names)),
    arrow_xy[:, 1], arrow_xy[:, 2];
    color = INK, linewidth = 2.5, arrowsize = 18)

# Nudge labels apart vertically when their arrow tips sit too close to read
label_dy = zeros(length(feature_names))
for i in 1:length(feature_names), j in (i + 1):length(feature_names)
    tip_distance = hypot(arrow_xy[i, 1] - arrow_xy[j, 1], arrow_xy[i, 2] - arrow_xy[j, 2])
    if tip_distance < 0.4
        label_dy[i] += 0.35
        label_dy[j] -= 0.35
    end
end

for (i, name) in enumerate(feature_names)
    text!(ax, arrow_xy[i, 1], arrow_xy[i, 2] + label_dy[i]; text = name,
        color = INK, fontsize = 13, align = (:left, :bottom))
end

Legend(fig[1, 2], ax, "Species";
    backgroundcolor = ELEVATED_BG, framecolor = INK_SOFT,
    labelcolor = INK, titlecolor = INK)
colsize!(fig.layout, 2, Relative(0.18))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
