# anyplot.ai
# scatter-basic: Basic Scatter Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-06-25

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND    = colorant"#009E73"

# Data — adult height (cm) vs weight (kg), simulated health study, n=150
n = 150
height_cm = 170.0 .+ 10.0 .* randn(n)
weight_kg = 0.5 .* height_cm .+ 5.0 .* randn(n) .- 15.0

# Regression line
x_bar     = mean(height_cm)
y_bar     = mean(weight_kg)
slope     = sum((height_cm .- x_bar) .* (weight_kg .- y_bar)) / sum((height_cm .- x_bar) .^ 2)
intercept = y_bar - slope * x_bar
x_fit     = LinRange(minimum(height_cm) - 1, maximum(height_cm) + 1, 200)
y_fit     = slope .* x_fit .+ intercept
r_val     = cor(height_cm, weight_kg)

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

# Subtitle using Makie compositional layout slot above the main axis
Label(
    fig[0, 1],
    "Pearson r = $(round(r_val; digits=2)) — positive correlation (height predicts weight, n=$n)",
    fontsize  = 13,
    color     = INK_SOFT,
    halign    = :left,
    tellwidth = false,
)

ax = Axis(
    fig[1, 1];
    title              = "scatter-basic · julia · makie · anyplot.ai",
    titlesize          = 23,
    titlecolor         = INK,
    xlabel             = "Height (cm)",
    ylabel             = "Weight (kg)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticksvisible      = false,
    yticksvisible      = false,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

scatter!(
    ax, height_cm, weight_kg;
    color       = (BRAND, 0.7),
    markersize  = 12,
    strokewidth = 1,
    strokecolor = PAGE_BG,
)

lines!(ax, collect(x_fit), collect(y_fit); color = INK_SOFT, linewidth = 2.0, linestyle = :dash)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
