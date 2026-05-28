# anyplot.ai
# heatmap-basic: Basic Heatmap
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-05-28

using CairoMakie
using Colors
using Random
using Statistics
using Printf

Random.seed!(42)

# Theme tokens
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint diverging colormap — for correlation data with a meaningful midpoint at 0
const _midpoint   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ANYPLOT_DIV = cgrad([colorant"#AE3030", _midpoint, colorant"#4467A3"])

# Data — correlation matrix for climate variables (200 daily observations)
var_labels = ["Temp", "Humidity", "Wind", "Pressure", "Precip", "Dewpoint", "UV Index", "Clouds"]
n = length(var_labels)

obs = zeros(200, n)
obs[:, 1] = randn(200)                                           # Temperature
obs[:, 6] = 0.85 .* obs[:, 1] .+ 0.53 .* randn(200)            # Dewpoint ~ Temp
obs[:, 2] = 0.45 .* obs[:, 1] .+ 0.45 .* obs[:, 6] .+ 0.45 .* randn(200)  # Humidity
obs[:, 5] = 0.55 .* obs[:, 2] .+ 0.84 .* randn(200)            # Precip ~ Humidity
obs[:, 8] = 0.40 .* obs[:, 5] .+ 0.92 .* randn(200)            # Clouds ~ Precip
obs[:, 7] = -0.55 .* obs[:, 8] .+ 0.84 .* randn(200)           # UV Index ~ -Clouds
obs[:, 3] = 0.15 .* obs[:, 1] .+ 0.99 .* randn(200)            # Wind (mostly noise)
obs[:, 4] = -0.25 .* obs[:, 1] .+ 0.97 .* randn(200)           # Pressure ~ -Temp

corr_mat = cor(obs)

# Plot — square canvas for symmetric heatmap
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "heatmap-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "",
    ylabel             = "",
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticksize          = 0,
    yticksize          = 0,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
    xticks             = (1:n, var_labels),
    yticks             = (1:n, var_labels),
    xticklabelrotation = π / 4,
    xticklabelsize     = 13,
    yticklabelsize     = 13,
    yreversed          = true,
)

hm = heatmap!(ax, 1:n, 1:n, corr_mat;
    colormap   = ANYPLOT_DIV,
    colorrange = (-1.0, 1.0),
)

# Cell value annotations — collect all positions and labels for a single text! call
positions = Point2f[]
cell_labels = String[]
for i in 1:n
    for j in 1:n
        push!(positions, Point2f(i, j))
        push!(cell_labels, @sprintf("%.2f", corr_mat[i, j]))
    end
end
text!(ax, positions; text = cell_labels, align = (:center, :center), color = INK, fontsize = 11)

# Colorbar
Colorbar(fig[1, 2], hm;
    label          = "Pearson r",
    labelcolor     = INK,
    tickcolor      = INK_SOFT,
    ticklabelcolor = INK_SOFT,
    ticklabelsize  = 12,
    labelsize      = 13,
    width          = 22,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
