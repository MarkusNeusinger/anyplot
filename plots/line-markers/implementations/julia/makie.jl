# anyplot.ai
# line-markers: Line Plot with Markers
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 83/100 | Created: 2026-09-05

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
    colorant"#009E73", colorant"#4467A3",
]

# --- Data ---------------------------------------------------------------
# Quality-control readings: two production lines sampled at hourly checkpoints.
hours = 0:11
line_a = 98.2 .+ cumsum(randn(length(hours)) .* 0.6)
line_b = 96.8 .+ cumsum(randn(length(hours)) .* 0.6)

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-markers · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Inspection Hour",
    ylabel             = "Yield (%)",
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
    xticks             = collect(hours),
)

lines!(ax, hours, line_a; color = IMPRINT_PALETTE[1], linewidth = 3)
scatter!(ax, hours, line_a; color = IMPRINT_PALETTE[1], marker = :circle,
         markersize = 16, strokewidth = 1.5, strokecolor = PAGE_BG,
         label = "Line A")

lines!(ax, hours, line_b; color = IMPRINT_PALETTE[2], linewidth = 3)
scatter!(ax, hours, line_b; color = IMPRINT_PALETTE[2], marker = :utriangle,
         markersize = 18, strokewidth = 1.5, strokecolor = PAGE_BG,
         label = "Line B")

axislegend(ax; position = :rb, labelcolor = INK_SOFT, framevisible = false)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
