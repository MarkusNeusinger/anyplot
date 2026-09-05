# anyplot.ai
# errorbar-asymmetric: Asymmetric Error Bars Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const BRAND    = colorant"#009E73"  # Imprint palette position 1

# --- Data ---------------------------------------------------------------
# Airborne particulate matter (PM2.5, μg/m3) reported as station medians. The
# underlying measurement noise is log-normal, so back-transforming the
# uncertainty to the linear concentration scale yields a larger upper bound
# than lower bound at every station.
stations = ["Riverside", "Lakeview", "Hillcrest", "Downtown",
            "Parkside", "Eastgate", "Westbrook", "Northfield"]
n = length(stations)
positions = 1:n

median_conc = [34.2, 28.7, 24.1, 21.5, 17.8, 14.4, 11.2, 8.6]
log_sigma = 0.14 .+ 0.22 .* rand(n)

error_lower = median_conc .* (1 .- exp.(-log_sigma))
error_upper = median_conc .* (exp.(log_sigma) .- 1)

# --- Plot ---------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "errorbar-asymmetric · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    subtitle           = "Bars mark the 10th–90th percentile range (log-normal back-transform)",
    subtitlesize       = 13,
    subtitlecolor      = INK_MUTED,
    xlabel             = "Monitoring Station",
    ylabel             = "PM2.5 Concentration (μg/m³)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticks             = (positions, stations),
    xticklabelrotation = π / 8,
    backgroundcolor    = PAGE_BG,
    topspinevisible     = false,
    rightspinevisible   = false,
    leftspinecolor      = INK_SOFT,
    bottomspinecolor    = INK_SOFT,
    xgridvisible        = false,
    ygridcolor          = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

errorbars!(ax, positions, median_conc, error_lower, error_upper;
           color = BRAND, whiskerwidth = 18, linewidth = 2.5)
scatter!(ax, positions, median_conc; color = BRAND, markersize = 20, strokewidth = 0)

ylims!(ax, 0, nothing)

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
