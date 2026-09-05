# anyplot.ai
# line-confidence: Line Plot with Confidence Interval
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-05

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
const BRAND       = colorant"#009E73"  # Imprint palette position 1 — ALWAYS first series

# --- Data ---------------------------------------------------------------
# Daily-active-users forecast after a product launch: a saturating growth
# curve (point estimate) with a prediction interval that widens further out
# on the forecast horizon, as is typical for time-series forecasts.
days_since_launch = collect(1:60)
predicted_dau = @. 5000 + 4200 * (1 - exp(-days_since_launch / 18)) +
                   40 * sin(days_since_launch / 6)
interval_margin = @. 60 + 5.5 * days_since_launch
lower_bound = predicted_dau .- interval_margin
upper_bound = predicted_dau .+ interval_margin

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-confidence · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Days Since Launch",
    ylabel             = "Daily Active Users",
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
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

band!(
    ax, days_since_launch, lower_bound, upper_bound;
    color = RGBAf(BRAND.r, BRAND.g, BRAND.b, 0.25),
    label = "95% prediction interval",
)
lines!(
    ax, days_since_launch, predicted_dau;
    color     = BRAND,
    linewidth = 3,
    label     = "Predicted DAU",
)

axislegend(
    ax;
    position        = :lt,
    backgroundcolor = ELEVATED_BG,
    framecolor      = INK_SOFT,
    labelcolor      = INK,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
