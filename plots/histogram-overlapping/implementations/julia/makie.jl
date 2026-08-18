# anyplot.ai
# histogram-overlapping: Overlapping Histograms
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-08-18

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
    colorant"#009E73",  # 1 — brand green, ALWAYS first series
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
]

# --- Data ---------------------------------------------------------------
# Reaction times (ms) across three UI response conditions
n_per_group = 220
condition_a = 240 .+ 35 .* randn(n_per_group)          # baseline
condition_b = 265 .+ 42 .* randn(n_per_group)           # added latency
condition_c = 225 .+ 30 .* randn(n_per_group)           # optimized

bin_edges = range(minimum(vcat(condition_a, condition_b, condition_c)) - 5,
                   maximum(vcat(condition_a, condition_b, condition_c)) + 5;
                   length = 31)

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "histogram-overlapping · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Response Time (ms)",
    ylabel             = "Number of Trials",
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

hist!(ax, condition_a; bins = bin_edges, color = (IMPRINT_PALETTE[1], 0.55),
      strokewidth = 1, strokecolor = IMPRINT_PALETTE[1], label = "Baseline")
hist!(ax, condition_b; bins = bin_edges, color = (IMPRINT_PALETTE[2], 0.55),
      strokewidth = 1, strokecolor = IMPRINT_PALETTE[2], label = "Added Latency")
hist!(ax, condition_c; bins = bin_edges, color = (IMPRINT_PALETTE[3], 0.55),
      strokewidth = 1, strokecolor = IMPRINT_PALETTE[3], label = "Optimized")

axislegend(ax; position = :rt, labelsize = 12, labelcolor = INK_SOFT,
           framevisible = false, backgroundcolor = :transparent)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
