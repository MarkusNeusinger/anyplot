# anyplot.ai
# line-styled: Styled Line Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 83/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome") ---
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette (position 1-4) — theme-independent
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
]

# --- Data: hourly latency percentiles over a week of web traffic ------------
hours = 0:167  # 7 days x 24h
daily_cycle = sin.(2π .* mod.(hours, 24) ./ 24 .- π / 2)  # peaks around midday

p50 = 80.0 .+ 15.0 .* daily_cycle .+ randn(length(hours)) .* 4.0
p90 = 180.0 .+ 35.0 .* daily_cycle .+ randn(length(hours)) .* 8.0
p99 = 320.0 .+ 60.0 .* daily_cycle .+ randn(length(hours)) .* 15.0
p999 = 480.0 .+ 90.0 .* daily_cycle .+ randn(length(hours)) .* 25.0

# --- Plot ---------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-styled · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Time (hours)",
    ylabel             = "Response Time (ms)",
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

lines!(ax, hours, p50; color = IMPRINT_PALETTE[1], linestyle = :solid, linewidth = 2.75, label = "p50")
lines!(ax, hours, p90; color = IMPRINT_PALETTE[2], linestyle = :dash, linewidth = 2.75, label = "p90")
lines!(ax, hours, p99; color = IMPRINT_PALETTE[3], linestyle = :dot, linewidth = 2.75, label = "p99")
lines!(ax, hours, p999; color = IMPRINT_PALETTE[4], linestyle = :dashdot, linewidth = 2.75, label = "p99.9")

axislegend(ax; position = :lt, labelcolor = INK_SOFT, framevisible = false)

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
