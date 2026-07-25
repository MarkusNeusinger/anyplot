# anyplot.ai
# span-basic: Basic Span Plot (Highlighted Region)
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-07-25

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const ANYPLOT_AMBER = colorant"#DDCC77"  # warning / caution — outside the categorical pool
const ANYPLOT_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const ANYPLOT_ALERT = colorant"#AE3030"  # bad / breach — semantic-red anchor

# --- Data ---------------------------------------------------------------
# Daily API response latency (ms) over a 90-day monitoring window, with two
# operational events overlaid: an incident-driven spike and a planned
# maintenance bump.
days = 1:90
latency = fill(120.0, 90) .+ randn(90) .* 8.0

incident_days = 35:41
latency[incident_days] .+= 55.0 .+ randn(length(incident_days)) .* 5.0

maintenance_days = 65:70
latency[maintenance_days] .+= 18.0 .+ randn(length(maintenance_days)) .* 3.0

sla_threshold = 160.0  # ms — response times above this breach the SLA

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "span-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Day of Monitoring Window",
    ylabel             = "API Response Latency (ms)",
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

vspan!(ax, 34.5, 41.5; color = (ANYPLOT_AMBER, 0.25), label = "Incident: Database Failover")
vspan!(ax, 64.5, 70.5; color = (ANYPLOT_MUTED, 0.2), label = "Scheduled Maintenance")
hspan!(ax, sla_threshold, 200; color = (ANYPLOT_ALERT, 0.09), label = "SLA Threshold (>160ms)")

# Thin edge strokes give each span a crisper boundary against the grid,
# without adding duplicate legend entries.
vlines!(ax, [34.5, 41.5]; color = ANYPLOT_AMBER, linewidth = 1.5, linestyle = :dash)
vlines!(ax, [64.5, 70.5]; color = ANYPLOT_MUTED, linewidth = 1.5, linestyle = :dash)
hlines!(ax, [sla_threshold]; color = ANYPLOT_ALERT, linewidth = 1.5, linestyle = :dash)

lines!(ax, days, latency; color = IMPRINT_PALETTE[1], linewidth = 3, label = "Response Latency")

# Fix y-limits to the data's natural range; the SLA hspan's upper bound (200)
# is intentionally past the visible area so the "breach zone" reads as
# extending to the top of the chart, without dragging the autolimits along.
ylims!(ax, 95, 195)

axislegend(
    ax;
    position        = :lt,
    framevisible    = false,
    backgroundcolor = :transparent,
    labelcolor      = INK_SOFT,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
