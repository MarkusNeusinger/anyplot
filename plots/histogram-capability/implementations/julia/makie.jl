# anyplot.ai
# histogram-capability: Process Capability Plot with Specification Limits
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-20

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
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

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

# Data — shaft diameter measurements (mm), slightly off-center process
const N      = 200
const LSL    = 9.95
const USL    = 10.05
const TARGET = 10.00

measurements = randn(N) .* 0.015 .+ 10.012

mu    = mean(measurements)
sigma = std(measurements)
cp    = (USL - LSL) / (6 * sigma)
cpk   = min((USL - mu) / (3 * sigma), (mu - LSL) / (3 * sigma))

# Normal distribution curve scaled to histogram counts
n_bins           = 20
approx_bin_width = (maximum(measurements) - minimum(measurements)) / n_bins
x_curve          = range(LSL - 0.012, USL + 0.012, length = 400)
pdf_vals         = @. exp(-0.5 * ((x_curve - mu) / sigma)^2) / (sigma * sqrt(2π))
pdf_scaled       = pdf_vals .* N .* approx_bin_width

y_ceil = maximum(pdf_scaled) * 1.8

# Plot
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "histogram-capability · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Shaft Diameter (mm)",
    ylabel            = "Count",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
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
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.12f0),
    yminorgridvisible = false,
    xminorgridvisible = false,
)

# Histogram bars — first Imprint series (brand green)
hist!(ax, measurements;
    bins        = n_bins,
    color       = IMPRINT_PALETTE[1],
    strokecolor = PAGE_BG,
    strokewidth = 1.0,
)

# Normal distribution curve — Imprint blue
lines!(ax, collect(x_curve), pdf_scaled;
    color     = IMPRINT_PALETTE[3],
    linewidth = 2.5,
)

# Specification limit lines — matte red dashed (semantic: spec boundary / error)
vlines!(ax, [LSL, USL];
    color     = IMPRINT_PALETTE[5],
    linewidth = 2.0,
    linestyle = :dash,
)

# Target (nominal) line — ochre dashed
vlines!(ax, [TARGET];
    color     = IMPRINT_PALETTE[4],
    linewidth = 2.0,
    linestyle = :dash,
)

ylims!(ax, 0, y_ceil)
xlims!(ax, LSL - 0.015, USL + 0.015)

# Limit and target labels
label_y = y_ceil * 0.94
text!(ax, LSL + 0.001, label_y;
    text     = "LSL",
    align    = (:left, :top),
    fontsize = 12,
    color    = IMPRINT_PALETTE[5],
)
text!(ax, TARGET + 0.001, label_y;
    text     = "Target",
    align    = (:left, :top),
    fontsize = 12,
    color    = IMPRINT_PALETTE[4],
)
text!(ax, USL - 0.001, label_y;
    text     = "USL",
    align    = (:right, :top),
    fontsize = 12,
    color    = IMPRINT_PALETTE[5],
)

# Capability annotation — upper right, below limit labels
cp_rounded  = round(cp,  digits = 2)
cpk_rounded = round(cpk, digits = 2)
text!(ax, USL - 0.003, y_ceil * 0.72;
    text     = "Cp  = $(cp_rounded)\nCpk = $(cpk_rounded)",
    align    = (:right, :top),
    fontsize = 13,
    color    = INK,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
