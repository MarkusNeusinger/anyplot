# anyplot.ai
# curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-05-28

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
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const ANYPLOT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (Bias²)
    colorant"#C475FD",  # 2 — lavender (Variance)
    colorant"#4467A3",  # 3 — blue (Total Error)
    colorant"#BD8233",  # 4 — ochre (Irreducible Error)
]

# Data — theoretical bias-variance tradeoff curves
complexity = range(0.1, 10.0, length=80)

bias_sq         = 1.0 ./ (1.0 .+ complexity) .+ 0.02
variance        = (complexity .^ 1.4) ./ 22.0
irreducible_err = fill(0.15, length(complexity))
total_err       = bias_sq .+ variance .+ irreducible_err

# Find optimal complexity (minimum total error)
opt_idx       = argmin(total_err)
opt_complexity = complexity[opt_idx]
opt_total      = total_err[opt_idx]

# Title
title_str = "curve-bias-variance-tradeoff · julia · makie · anyplot.ai"
n = length(title_str)
default_titlesize = 20.0
titlesize = n > 67 ? max(14.0, round(default_titlesize * 67 / n)) : default_titlesize

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = titlesize,
    titlecolor         = INK,
    xlabel             = "Model Complexity",
    ylabel             = "Prediction Error",
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
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    yminorgridvisible  = false,
    xminorgridvisible  = false,
)

# Shaded zones (underfitting / overfitting)
vspan!(ax, complexity[1], opt_complexity;
    color = RGBAf(ANYPLOT_PALETTE[1].r, ANYPLOT_PALETTE[1].g, ANYPLOT_PALETTE[1].b, 0.07))
vspan!(ax, opt_complexity, complexity[end];
    color = RGBAf(ANYPLOT_PALETTE[2].r, ANYPLOT_PALETTE[2].g, ANYPLOT_PALETTE[2].b, 0.07))

# Curves
lines!(ax, complexity, bias_sq;
    color = ANYPLOT_PALETTE[1], linewidth = 2.5, linestyle = :solid, label = "Bias²")
lines!(ax, complexity, variance;
    color = ANYPLOT_PALETTE[2], linewidth = 2.5, linestyle = :dash, label = "Variance")
lines!(ax, complexity, total_err;
    color = ANYPLOT_PALETTE[3], linewidth = 3.0, linestyle = :dashdot, label = "Total Error")
lines!(ax, complexity, irreducible_err;
    color = ANYPLOT_PALETTE[4], linewidth = 2.0, linestyle = :dot, label = "Irreducible Error")

# Optimal point vertical line
vlines!(ax, [opt_complexity]; color = INK_SOFT, linewidth = 1.5, linestyle = :dash)

# Optimal point marker on total error curve
scatter!(ax, [opt_complexity], [opt_total];
    color = ANYPLOT_PALETTE[3], markersize = 14, strokewidth = 1.5,
    strokecolor = PAGE_BG)

# Zone labels
text!(ax, complexity[4], maximum(total_err) * 0.78;
    text = "Underfitting\n(High Bias)",
    color = INK_MUTED, fontsize = 13, align = (:left, :center))
text!(ax, opt_complexity + 0.3, maximum(total_err) * 0.78;
    text = "Overfitting\n(High Variance)",
    color = INK_MUTED, fontsize = 13, align = (:left, :center))

# Optimal label
text!(ax, opt_complexity, opt_total + 0.03;
    text = "Optimal",
    color = INK, fontsize = 11, align = (:center, :bottom), font = :bold)

# Direct curve labels (spec requirement: annotate each curve directly on the plot)
lbl_bias_x   = 2.0
lbl_bias_y   = 1.0 / (1.0 + lbl_bias_x) + 0.02
lbl_var_x    = 8.5
lbl_var_y    = (lbl_var_x ^ 1.4) / 22.0
lbl_tot_x    = 7.5
lbl_tot_y    = (1.0 / (1.0 + lbl_tot_x) + 0.02) + ((lbl_tot_x ^ 1.4) / 22.0) + 0.15
lbl_irr_x    = 5.0

text!(ax, lbl_bias_x, lbl_bias_y + 0.03;
    text = "Bias²",
    color = ANYPLOT_PALETTE[1], fontsize = 12, align = (:center, :bottom), font = :bold)
text!(ax, lbl_var_x, lbl_var_y + 0.03;
    text = "Variance",
    color = ANYPLOT_PALETTE[2], fontsize = 12, align = (:center, :bottom), font = :bold)
text!(ax, lbl_tot_x, lbl_tot_y + 0.03;
    text = "Total Error",
    color = ANYPLOT_PALETTE[3], fontsize = 12, align = (:center, :bottom), font = :bold)
text!(ax, lbl_irr_x, 0.15 + 0.03;
    text = "Irreducible Error",
    color = ANYPLOT_PALETTE[4], fontsize = 12, align = (:center, :bottom), font = :bold)

# Formula annotation
text!(ax, complexity[end], irreducible_err[1] + 0.01;
    text = "Total Error = Bias² + Variance + Irreducible Error",
    color = INK_MUTED, fontsize = 12, align = (:right, :bottom))

# Legend
axislegend(ax;
    position       = :rc,
    backgroundcolor = ELEVATED_BG,
    framecolor     = INK_SOFT,
    labelcolor     = INK,
    titlecolor     = INK,
    framewidth     = 0.8,
    labelsize      = 12,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
