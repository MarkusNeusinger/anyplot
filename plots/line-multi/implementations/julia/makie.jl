# anyplot.ai
# line-multi: Multi-Line Comparison Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-08-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
]

# --- Data ---------------------------------------------------------------
# Indexed revenue (base = 100) for 4 product lines over 36 months, each
# following a random walk with its own drift so the lines diverge visibly.
n_months = 36
months = 1:n_months
product_lines = ["Core Platform", "Mobile App", "Analytics Suite", "API Services"]
drifts = [0.35, 1.15, -0.25, 0.75]
vols = [1.6, 2.4, 2.0, 2.8]

revenue_index = Array{Float64}(undef, n_months, length(product_lines))
for (i, (drift, vol)) in enumerate(zip(drifts, vols))
    steps = drift .+ vol .* randn(n_months)
    revenue_index[:, i] = 100.0 .+ cumsum(steps) .- steps[1]
end

# --- Plot -----------------------------------------------------------------
title_str = "line-multi · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Month",
    ylabel             = "Revenue Index (base = 100)",
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
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

for (i, name) in enumerate(product_lines)
    lines!(ax, months, revenue_index[:, i];
        color = IMPRINT_PALETTE[i], linewidth = 3.0, label = name)
end

axislegend(ax; position = :lt, framevisible = true, backgroundcolor = ELEVATED_BG,
    framecolor = INK_SOFT, labelcolor = INK_SOFT, labelsize = 12, patchsize = (20, 12))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
