# anyplot.ai
# pp-basic: Probability-Probability (P-P) Plot
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-09

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — first categorical series (Imprint palette)
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
    colorant"#954477",
    colorant"#99B314",
]

# Data — process measurements (coating thickness, micrometers) with a right-skewed tail
# 85% from a normal base distribution, 15% with a positive boost → slightly right-skewed
n = 200
base_measurements = 50.0 .+ 8.0 .* randn(n)
boost_flags       = Float64.(rand(n) .< 0.15)
boost_amounts     = 20.0 .+ 5.0 .* abs.(randn(n))
coating_thickness = base_measurements .+ boost_flags .* boost_amounts

# Standardise to zero mean, unit variance for P-P comparison against N(0,1)
μ_fit    = mean(coating_thickness)
σ_fit    = std(coating_thickness)
z_scores = (coating_thickness .- μ_fit) ./ σ_fit

# Sort and compute empirical CDF (Hazen plotting positions: (i − 0.5) / n)
sorted_z      = sort(z_scores)
empirical_cdf = [(i - 0.5) / n for i in 1:n]

# Theoretical normal CDF — Abramowitz & Stegun (1964) rational approximation 26.2.17
# Maximum absolute error ≤ 7.5e-8; no external packages required.
abs_z     = abs.(sorted_z)
t_coeff   = 1.0 ./ (1.0 .+ 0.2316419 .* abs_z)
poly_val  = t_coeff .* (0.319381530 .+ t_coeff .* (
            -0.356563782 .+ t_coeff .* (
             1.781477937 .+ t_coeff .* (
            -1.821255978 .+ t_coeff .* 1.330274429))))
p_upper   = 1.0 .- (1.0 / sqrt(2π)) .* exp.(-abs_z .^ 2 ./ 2.0) .* poly_val
theoretical_cdf = ifelse.(sorted_z .>= 0.0, p_upper, 1.0 .- p_upper)

# Title
title_str  = "pp-basic · julia · makie · anyplot.ai"
n_title    = length(title_str)
title_size = n_title > 67 ? max(14, round(Int, 20 * 67 / n_title)) : 20

# Figure — square canvas (P-P plots use equal 0–1 probability axes)
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = title_size,
    titlecolor        = INK,
    xlabel            = "Theoretical Cumulative Probability",
    ylabel            = "Empirical Cumulative Probability",
    xlabelsize        = 15,
    ylabelsize        = 15,
    xticklabelsize    = 13,
    yticklabelsize    = 13,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.12),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.12),
    xminorgridvisible = false,
    yminorgridvisible = false,
    aspect            = AxisAspect(1),
    limits            = (0.0, 1.0, 0.0, 1.0),
)

# Reference diagonal — perfect distributional fit
lines!(ax, [0.0, 1.0], [0.0, 1.0];
    color     = INK_SOFT,
    linewidth = 1.5,
    linestyle = :dash,
)

# P-P scatter points
scatter!(ax, theoretical_cdf, empirical_cdf;
    color       = IMPRINT_PALETTE[1],
    markersize  = 9,
    strokewidth = 0.5,
    strokecolor = PAGE_BG,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
