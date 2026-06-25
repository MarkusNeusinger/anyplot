# anyplot.ai
# scatter-basic: Basic Scatter Plot
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-25

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND    = colorant"#009E73"  # Imprint palette position 1 — first series

# Data — adult height (cm) vs weight (kg), simulated health study, n=150
n = 150
height_cm = 170.0 .+ 10.0 .* randn(n)
weight_kg = 0.5 .* height_cm .+ 5.0 .* randn(n) .- 15.0

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "scatter-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
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
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
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

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
