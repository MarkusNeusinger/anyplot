# anyplot.ai
# line-yield-curve: Yield Curve (Interest Rate Term Structure)
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 91/100 | Created: 2026-06-10

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
    colorant"#954477",
    colorant"#99B314",
]
const ANYPLOT_AMBER = colorant"#DDCC77"

# Data: U.S. Treasury yield curves on three dates
maturity_years  = [0.083, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0]
maturity_labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

yields_jan2021 = [0.09, 0.08, 0.09, 0.10, 0.13, 0.21, 0.45, 0.74, 1.07, 1.62, 1.84]
yields_oct2022 = [3.30, 3.82, 4.20, 4.48, 4.47, 4.35, 4.20, 4.05, 4.00, 4.15, 4.05]
yields_jul2023 = [5.34, 5.49, 5.49, 5.45, 4.87, 4.55, 4.36, 4.22, 3.97, 4.18, 3.95]

# Inversion band: from 2Y onward, shade between 2Y reference yield and actual curve
inv_start = 5
inv_x     = maturity_years[inv_start:end]
inv_upper = fill(yields_jul2023[inv_start], length(inv_x))
inv_lower = yields_jul2023[inv_start:end]

# Title
title_str  = "U.S. Treasury Yields · line-yield-curve · julia · makie · anyplot.ai"
title_n    = length(title_str)
title_size = max(14, round(Int, 20 * 67 / title_n))

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = title_size,
    titlecolor         = INK,
    xlabel             = "Maturity",
    ylabel             = "Yield (%)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    xscale             = log10,
    xticks             = (maturity_years, maturity_labels),
)

# Inversion shading (amber warning zone where short-term yields exceed long-term)
band!(ax, inv_x, inv_lower, inv_upper; color = (ANYPLOT_AMBER, 0.30))

# Inversion zone label (inside the amber band, between inv_lower and inv_upper at 7Y)
text!(ax, [7.0], [4.55];
    text      = ["Inverted zone"],
    color     = ANYPLOT_AMBER,
    fontsize  = 11,
    align     = (:center, :center))

# Jan 2021 near-zero annotation in the empty band between the two clusters
text!(ax, [2.5], [2.2];
    text      = ["COVID-era near-zero rates"],
    color     = INK_SOFT,
    fontsize  = 10,
    align     = (:left, :center))

# Yield curves
scatterlines!(ax, maturity_years, yields_jan2021;
    color       = IMPRINT_PALETTE[1],
    linewidth   = 2.5,
    markersize  = 10,
    strokewidth = 0,
    label       = "Jan 2021 (normal)")

scatterlines!(ax, maturity_years, yields_oct2022;
    color       = IMPRINT_PALETTE[2],
    linewidth   = 2.5,
    markersize  = 10,
    strokewidth = 0,
    label       = "Oct 2022 (flat)")

scatterlines!(ax, maturity_years, yields_jul2023;
    color       = IMPRINT_PALETTE[3],
    linewidth   = 2.5,
    markersize  = 10,
    strokewidth = 0,
    label       = "Jul 2023 (inverted)")

axislegend(ax;
    position        = :rt,
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK_SOFT,
    framecolor      = INK_SOFT,
    framewidth      = 0.5,
    patchsize       = (20f0, 10f0))

ylims!(ax, -0.3, 6.4)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
