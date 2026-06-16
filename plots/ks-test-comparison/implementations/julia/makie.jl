# anyplot.ai
# ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-05-29

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

sorted_good = sort(good_scores)
sorted_bad  = sort(bad_scores)

# KS statistic (inline — two-sample D and its x-location)
all_pts = sort(unique(vcat(sorted_good, sorted_bad)))
diffs   = abs.(searchsortedlast.(Ref(sorted_good), all_pts) ./ n_good .-
               searchsortedlast.(Ref(sorted_bad),  all_pts) ./ n_bad)
ks_idx  = argmax(diffs)
ks_d    = diffs[ks_idx]
ks_x    = all_pts[ks_idx]

# KS p-value (asymptotic Kolmogorov distribution, inline)
n_eff = sqrt((n_good * n_bad) / (n_good + n_bad))
z     = ks_d * (n_eff + 0.12 + 0.11 / n_eff)
ks_p  = max(0.0, min(1.0, 2.0 * sum((-1)^(k - 1) * exp(-2.0 * k^2 * z^2) for k in 1:100)))

# CDF values at the KS point for the gap segment
cdf_good_at_ks = searchsortedlast(sorted_good, ks_x) / n_good
cdf_bad_at_ks  = searchsortedlast(sorted_bad,  ks_x) / n_bad
y_lo = min(cdf_good_at_ks, cdf_bad_at_ks)
y_hi = max(cdf_good_at_ks, cdf_bad_at_ks)

# ECDF step function coordinates
function ecdf_step(sv)
    n  = length(sv)
    xs = vcat(sv[1] - 5.0,
              vec(permutedims(hcat(sv, sv))),
              sv[end] + 5.0)
    ys = vcat(0.0,
              vec(permutedims(hcat((0:n-1) ./ n, (1:n) ./ n))),
              1.0)
    return xs, ys
end

xs_good, ys_good = ecdf_step(sorted_good)
xs_bad,  ys_bad  = ecdf_step(sorted_bad)

# Dense x grid for band fill (evaluates both ECDFs at every data point)
x_fill      = sort(unique(vcat(sorted_good, sorted_bad)))
y_good_fill = [searchsortedlast(sorted_good, x) / n_good for x in x_fill]
y_bad_fill  = [searchsortedlast(sorted_bad,  x) / n_bad  for x in x_fill]

# Title
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

# Shaded fill between ECDF curves (narrates the divergence region)
ks_red = IMPRINT_PALETTE[5]
band!(ax, x_fill, min.(y_good_fill, y_bad_fill), max.(y_good_fill, y_bad_fill);
    color = RGBAf(ks_red.r, ks_red.g, ks_red.b, 0.12))

# ECDFs
lines!(ax, xs_good, ys_good;
    color = IMPRINT_PALETTE[1], linewidth = 2.5, label = "Good Customers")
lines!(ax, xs_bad, ys_bad;
    color = IMPRINT_PALETTE[2], linewidth = 2.5, label = "Bad Customers")

# KS statistic: dashed vertical marker + filled gap segment
vlines!(ax, [ks_x]; color = IMPRINT_PALETTE[5], linewidth = 1.2, linestyle = :dash)
lines!(ax, [ks_x, ks_x], [y_lo, y_hi];
    color = IMPRINT_PALETTE[5], linewidth = 4.0)

# Annotation: D value and p-value
ks_p_str = ks_p < 0.001 ? "p < 0.001" : "p = $(round(ks_p; digits = 3))"
text!(ax,
    "D = $(round(ks_d; digits = 3))\n$(ks_p_str)";
    position = Point2f(ks_x + 8.0, (y_lo + y_hi) / 2.0),
    align    = (:left, :center),
    color    = INK,
    fontsize = 16,
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
