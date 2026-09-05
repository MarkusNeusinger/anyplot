# anyplot.ai
# residual-plot: Residual Plot
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-09-05

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
const MUTED    = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------
# Advertising spend ($1000s) predicting weekly revenue ($1000s). The true
# relationship is linear but noise variance grows with spend, so a simple
# OLS fit leaves heteroscedastic residuals — exactly what this plot is
# meant to expose.
n = 300
ad_spend = sort(rand(n) .* 190 .+ 10)
noise_scale = 1.0 .+ 0.06 .* ad_spend
revenue = 50 .+ 4.5 .* ad_spend .+ randn(n) .* noise_scale .* 3.5

spend_mean = mean(ad_spend)
revenue_mean = mean(revenue)
slope = sum((ad_spend .- spend_mean) .* (revenue .- revenue_mean)) / sum((ad_spend .- spend_mean) .^ 2)
intercept = revenue_mean - slope * spend_mean
fitted_revenue = intercept .+ slope .* ad_spend
residuals = revenue .- fitted_revenue

resid_std = std(residuals)
is_outlier = abs.(residuals) .> 2 * resid_std

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "residual-plot · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Fitted Revenue (\$1000s)",
    ylabel             = "Residual (\$1000s)",
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
)

hspan!(ax, -2 * resid_std, 2 * resid_std; color = RGBAf(MUTED.r, MUTED.g, MUTED.b, 0.10))
hlines!(ax, [-2resid_std, 2resid_std]; color = MUTED, linewidth = 1.5, linestyle = :dot)
hlines!(ax, [0]; color = INK_SOFT, linewidth = 2.5, linestyle = :dash)

scatter!(
    ax, fitted_revenue[.!is_outlier], residuals[.!is_outlier];
    color = IMPRINT_PALETTE[1], markersize = 11, alpha = 0.65, strokewidth = 0,
    label = "Residual",
)
scatter!(
    ax, fitted_revenue[is_outlier], residuals[is_outlier];
    color = IMPRINT_PALETTE[5], markersize = 14, strokewidth = 1, strokecolor = PAGE_BG,
    label = "Outlier (|residual| > 2σ)",
)

axislegend(
    ax;
    position = :lb,
    labelcolor = INK_SOFT,
    labelsize = 12,
    framevisible = false,
    backgroundcolor = :transparent,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
