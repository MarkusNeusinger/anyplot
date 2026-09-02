# anyplot.ai
# density-rug: Density Plot with Rug Marks
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
BRAND    = colorant"#009E73"  # Imprint palette position 1 — always first series

# --- Data ---------------------------------------------------------------
# Reaction times (ms) from a cognitive test battery: right-skewed, occasional
# slow-response outliers — a classic case for pairing a smoothed KDE with a
# rug of the raw observations.
n_trials = 220
reaction_times_ms = exp.(0.22 .* randn(n_trials) .+ log(340))

# --- Plot ---------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "density-rug · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Reaction Time (ms)",
    ylabel             = "Density",
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
    yminorgridvisible  = false,
)

# Smoothed KDE — semi-transparent fill preserves visibility of the rug beneath it.
density!(
    ax, reaction_times_ms;
    color       = (BRAND, 0.35),
    strokecolor = BRAND,
    strokewidth = 2.5,
)

# Rug marks — one tick per raw observation, drawn along the axis baseline in
# axis-relative units so they sit clear of the density fill. Slight
# transparency keeps overlapping ticks in the busiest region legible.
vlines!(
    ax, reaction_times_ms;
    ymin      = 0.0,
    ymax      = 0.045,
    color     = (BRAND, 0.45),
    linewidth = 1.5,
)

ylims!(ax, low = 0)

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
