# anyplot.ai
# area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-08-19

using CairoMakie
using Colors
using Random
using Dates

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEV_BG  = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — position 1 (#009E73) is always the first series
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
]

# Data — 90-day Kanban board with a Backlog -> Analysis -> Development ->
# Testing -> Done pipeline. Each stage's cumulative curve is the arrival
# curve re-sampled at a dwell-time offset, so the vertical gap between two
# adjacent curves is exactly the WIP for the stage in between. Development
# carries a time-varying dwell that bulges mid-range (a hiring crunch) and
# drains by the end — the widening/narrowing bottleneck signal a CFD is
# meant to surface.
n_days = 90
start_date = Date(2024, 3, 3)
dates = start_date .+ Day.(0:(n_days - 1))
day_index = 1:n_days
t = collect(1:n_days)

daily_arrivals = rand(2:6, n_days)
backlog_cum = cumsum(daily_arrivals)

dwell_backlog = 4
analysis_cum = backlog_cum[clamp.(t .- dwell_backlog, 1, n_days)]

crunch = clamp.(1 .- abs.(t .- 50) ./ 25, 0.0, 1.0)
dwell_development = round.(Int, 5 .+ 10 .* crunch)
development_cum = analysis_cum[clamp.(t .- dwell_development, 1, n_days)]

dwell_testing = 4
testing_cum = development_cum[clamp.(t .- dwell_testing, 1, n_days)]

dwell_done = 3
done_cum = testing_cum[clamp.(t .- dwell_done, 1, n_days)]

zero_cum = zeros(Int, n_days)

# Plot
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "area-cumulative-flow · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Date",
    ylabel             = "Cumulative Items",
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

# Bands stacked with the earliest stage on top (per spec: Backlog above,
# Done below), drawn from the raw cumulative curves rather than summed
# deltas — the vertical thickness of each band is already the WIP for
# that stage since counts are monotonically non-decreasing downstream.
stage_lowers = (analysis_cum, development_cum, testing_cum, done_cum, zero_cum)
stage_uppers = (backlog_cum, analysis_cum, development_cum, testing_cum, done_cum)
stage_labels = ("Backlog", "Analysis", "Development", "Testing", "Done")

for i in 1:5
    band!(ax, day_index, stage_lowers[i], stage_uppers[i];
          color = IMPRINT_PALETTE[i], label = stage_labels[i])
end

# Thin page-background strokes crisp up the boundaries between bands
for curve in (backlog_cum, analysis_cum, development_cum, testing_cum, done_cum)
    lines!(ax, day_index, curve; color = PAGE_BG, linewidth = 1.5)
end

xlims!(ax, 1, n_days)
ylims!(ax, 0, maximum(backlog_cum) * 1.05)

tick_idx = 1:15:n_days
ax.xticks = (Float64.(collect(tick_idx)), Dates.format.(dates[tick_idx], "u dd"))

Legend(
    fig[1, 2], ax, "Stage";
    framevisible  = false,
    backgroundcolor = ELEV_BG,
    labelcolor    = INK_SOFT,
    titlecolor    = INK,
)
colsize!(fig.layout, 1, Relative(0.84))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
