# anyplot.ai
# ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-05-29

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

# Data — credit scoring: Good vs Bad customer score distributions
n_good = 400
n_bad  = 400
good_scores = randn(n_good) .* 60.0 .+ 620.0
bad_scores  = randn(n_bad)  .* 70.0 .+ 490.0

# Build step function coordinates for ECDF
function ecdf_step(sample)
    sorted_vals = sort(sample)
    n = length(sorted_vals)
    xs_out = Vector{Float64}(undef, 2 * n + 2)
    ys_out = Vector{Float64}(undef, 2 * n + 2)

    xs_out[1] = sorted_vals[1] - 5.0
    ys_out[1] = 0.0
    for i in 1:n
        xs_out[2i]     = sorted_vals[i]
        ys_out[2i]     = (i - 1) / n
        xs_out[2i + 1] = sorted_vals[i]
        ys_out[2i + 1] = i / n
    end
    xs_out[end] = sorted_vals[end] + 5.0
    ys_out[end] = 1.0

    return xs_out, ys_out
end

# Two-sample KS statistic
function ks_stat(x1, x2)
    n1, n2 = length(x1), length(x2)
    sx1 = sort(x1)
    sx2 = sort(x2)
    all_pts = sort(unique(vcat(sx1, sx2)))

    max_d  = 0.0
    max_pt = all_pts[1]
    for pt in all_pts
        c1 = searchsortedlast(sx1, pt)
        c2 = searchsortedlast(sx2, pt)
        d  = abs(c1 / n1 - c2 / n2)
        if d > max_d
            max_d  = d
            max_pt = pt
        end
    end
    return max_d, max_pt
end

# KS p-value (asymptotic Kolmogorov distribution)
function ks_pvalue(d, n1, n2)
    n = (n1 * n2) / (n1 + n2)
    z = d * (sqrt(n) + 0.12 + 0.11 / sqrt(n))
    s = 0.0
    for k in 1:100
        s += (-1)^(k - 1) * exp(-2.0 * k^2 * z^2)
    end
    return max(0.0, min(1.0, 2.0 * s))
end

ks_d, ks_x = ks_stat(good_scores, bad_scores)
ks_p = ks_pvalue(ks_d, n_good, n_bad)

# CDF values at the KS point for the gap segment
sx_good = sort(good_scores)
sx_bad  = sort(bad_scores)
cdf_good_at_ks = searchsortedlast(sx_good, ks_x) / n_good
cdf_bad_at_ks  = searchsortedlast(sx_bad,  ks_x) / n_bad
y_lo = min(cdf_good_at_ks, cdf_bad_at_ks)
y_hi = max(cdf_good_at_ks, cdf_bad_at_ks)

# ECDF step function data
sx_good_plot, sy_good_plot = ecdf_step(good_scores)
sx_bad_plot,  sy_bad_plot  = ecdf_step(bad_scores)

# Title (47 chars < 67 baseline, no scaling needed)
title_str  = "ks-test-comparison · julia · makie · anyplot.ai"
title_size = max(14, round(Int, 20 * min(1.0, 67.0 / length(title_str))))

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = title_size,
    titlecolor        = INK,
    xlabel            = "Credit Score",
    ylabel            = "Cumulative Proportion",
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
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.12),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.12),
    xminorgridvisible = false,
    yminorgridvisible = false,
    limits            = (nothing, nothing, -0.02, 1.05),
)

# ECDFs
lines!(ax, sx_good_plot, sy_good_plot;
    color = IMPRINT_PALETTE[1], linewidth = 2.5, label = "Good Customers")
lines!(ax, sx_bad_plot, sy_bad_plot;
    color = IMPRINT_PALETTE[2], linewidth = 2.5, label = "Bad Customers")

# KS statistic: dashed vertical marker + filled gap segment
vlines!(ax, [ks_x]; color = IMPRINT_PALETTE[5], linewidth = 1.2, linestyle = :dash)
lines!(ax, [ks_x, ks_x], [y_lo, y_hi];
    color = IMPRINT_PALETTE[5], linewidth = 4.0)

# Annotation: D value and p-value
ks_p_str = ks_p < 0.001 ? "p < 0.001" : "p = $(round(ks_p; digits = 3))"
text!(ax,
    "D = $(round(ks_d; digits = 3))\n$(ks_p_str)";
    position  = Point2f(ks_x + 8.0, (y_lo + y_hi) / 2.0),
    align     = (:left, :center),
    color     = INK,
    fontsize  = 13,
)

axislegend(ax;
    position        = :rb,
    labelsize       = 12,
    framevisible    = true,
    framecolor      = INK_SOFT,
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
