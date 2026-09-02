# anyplot.ai
# bar-error: Bar Chart with Error Bars
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
BRAND    = colorant"#009E73"  # Imprint palette position 1 — ALWAYS first series

# Data — 30 simulated runs per catalyst, drawn from each catalyst's known
# reaction-yield distribution; mean/SD are derived from the runs themselves
# (not hardcoded) so the seeded RNG actually drives the summary statistics.
catalysts = ["Pd/C", "Pt/C", "Ru/C", "Ni", "Cu", "Fe"]
true_mean = [87.4, 82.1, 74.9, 71.6, 63.8, 54.2]
true_std  = [3.1, 4.6, 5.2, 5.8, 6.9, 8.1]
n_runs = 30

runs = [tm .+ ts .* randn(n_runs) for (tm, ts) in zip(true_mean, true_std)]
mean_yield = mean.(runs)
std_yield = std.(runs)
x = 1:length(catalysts)
best = argmax(mean_yield)

# Plot — see default-style-guide.md "Visual Sizing Defaults" and prompts/library/makie.md
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "bar-error · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    subtitle          = "Error bars: ±1 SD (n = 30 runs per catalyst)",
    subtitlesize      = 14,
    subtitlecolor     = INK_SOFT,
    xlabel            = "Catalyst",
    ylabel            = "Reaction Yield (%)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xticks            = (x, catalysts),
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible = false,
    yminorgridvisible = false,
)

barplot!(ax, x, mean_yield;
    color       = BRAND,
    strokecolor = PAGE_BG,
    strokewidth = 1.5,
    width       = 0.6,
)

# Raincloud-style overlay: jittered individual runs, hinting at the
# per-catalyst distribution the bar+error-bar summary is drawn from.
jitter_x = vcat([fill(xi, n_runs) .+ (rand(n_runs) .- 0.5) .* 0.32 for xi in x]...)
jitter_y = vcat(runs...)
scatter!(ax, jitter_x, jitter_y;
    color       = (INK, 0.22),
    markersize  = 5,
    strokewidth = 0,
)

errorbars!(ax, x, mean_yield, std_yield;
    color        = INK,
    linewidth    = 2,
    whiskerwidth = 18,
)

# Callout on the top-performing catalyst — gives the sorted bars an
# explicit focal point instead of relying on descending order alone.
text!(ax, x[best], mean_yield[best] + std_yield[best];
    text      = "★ Top performer",
    color     = INK,
    fontsize  = 13,
    font      = :bold,
    align     = (:center, :bottom),
    offset    = (0, 6),
)

ylims!(ax, 0, maximum(mean_yield .+ std_yield) * 1.18)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
