# anyplot.ai
# heatmap-correlation: Correlation Matrix Heatmap
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-08-20

using CairoMakie
using Colors
using ColorSchemes
using Printf
using Random
using Statistics

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
DIV_MID  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
IMPRINT_DIV = cgrad([colorant"#AE3030", DIV_MID, colorant"#4467A3"])

# --- Data -----------------------------------------------------------------
# Monthly returns for 8 asset classes driven by two latent macro factors
# (equity beta, rate sensitivity) plus idiosyncratic noise, then reduced
# to a Pearson correlation matrix — a portfolio-diversification scenario.
asset_names = ["US Equities", "Int'l Equities", "Corp Bonds", "Treasuries",
               "Real Estate", "Commodities", "Gold", "Cash"]
n_assets = length(asset_names)
n_periods = 300

market_factor = randn(n_periods)
rate_factor = randn(n_periods)
market_loadings = [0.95, 0.85, 0.10, -0.15, 0.55, 0.35, -0.05, 0.0]
rate_loadings = [-0.10, -0.05, 0.80, 0.90, 0.05, -0.10, 0.15, 0.0]

returns = zeros(n_periods, n_assets)
for i in 1:n_assets
    returns[:, i] = market_loadings[i] .* market_factor .+
                    rate_loadings[i] .* rate_factor .+
                    0.4 .* randn(n_periods)
end

corr_matrix = cor(returns)

# Mask the upper triangle to drop the mirrored, redundant half
display_matrix = [(i >= j ? corr_matrix[i, j] : NaN) for i in 1:n_assets, j in 1:n_assets]

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 16,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "heatmap-correlation · julia · makie · anyplot.ai",
    titlesize          = 26,
    titlecolor         = INK,
    xticks             = (1:n_assets, asset_names),
    yticks             = (1:n_assets, asset_names),
    xticklabelrotation = π / 4,
    xticklabelsize     = 15,
    yticklabelsize     = 15,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    aspect             = 1,
    yreversed          = true,
    leftspinecolor     = INK_SOFT,
    rightspinecolor    = INK_SOFT,
    topspinecolor      = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = false,
)

hm = heatmap!(
    ax, 1:n_assets, 1:n_assets, display_matrix;
    colormap   = IMPRINT_DIV,
    colorrange = (-1, 1),
    nan_color  = :transparent,
)

# Pick ink vs. paper text per cell so labels stay legible against both the
# saturated red/blue extremes and the near-neutral middle of the colormap.
for i in 1:n_assets, j in 1:n_assets
    if i >= j
        value = corr_matrix[i, j]
        cell_color = get(IMPRINT_DIV, (value + 1) / 2)
        luminance = 0.299 * cell_color.r + 0.587 * cell_color.g + 0.114 * cell_color.b
        label_color = luminance > 0.5 ? colorant"#1A1A17" : colorant"#F0EFE8"
        text!(ax, i, j; text = @sprintf("%.2f", value),
              align = (:center, :center), fontsize = 15, color = label_color)
    end
end

Colorbar(
    fig[1, 2], hm;
    label          = "Pearson correlation",
    labelcolor     = INK,
    labelsize      = 16,
    ticklabelcolor = INK_SOFT,
    ticklabelsize  = 14,
    ticks          = -1:0.5:1,
)

colgap!(fig.layout, 20)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
