# anyplot.ai
# heatmap-calendar: Basic Calendar Heatmap
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-07-24

using CairoMakie
using Colors
using Dates
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential colormap (single-polarity) — brand green → blue.
# Daily commit counts are single-polarity magnitude, so imprint_seq applies.
const IMPRINT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])
# Faint neutral for calendar cells outside the data range (missing days).
const EMPTY_CELL  = RGBAf(INK.r, INK.g, INK.b, 0.06)

# --- Data -------------------------------------------------------------------
# GitHub-style contribution graph: one year of daily commit counts.
start_date = Date(2025, 1, 1)
end_date   = Date(2025, 12, 31)
all_dates  = start_date:Day(1):end_date

commits_by_date = Dict{Date,Int}()
for d in all_dates
    weekday_base = dayofweek(d) <= 5 ? 5.0 : 1.5              # busier on weekdays
    yearly_trend = 8.0 * (dayofyear(d) / 365)                # activity grows over the year
    seasonal     = 3.0 * sin(2π * (dayofyear(d) - 80) / 365) # spring/autumn peaks
    count        = round(Int, max(0.0, weekday_base + yearly_trend + seasonal + randn() * 2.0))
    rand() < 0.08 && (count = 0)                              # occasional rest day
    commits_by_date[d] = count
end
vmax = maximum(values(commits_by_date))

# Calendar grid geometry: columns = weeks, rows = weekdays (Mon..Sun).
first_monday = start_date - Day(dayofweek(start_date) - 1)
n_weeks      = div((end_date - first_monday).value, 7) + 1

cell_rects  = Rect2f[]
cell_colors = RGBAf[]
pad = 0.09
for week in 0:(n_weeks - 1), row in 1:7
    day = first_monday + Day(week * 7 + (row - 1))
    push!(cell_rects, Rect2f(week - 0.5 + pad, row - 0.5 + pad, 1 - 2pad, 1 - 2pad))
    if start_date <= day <= end_date
        push!(cell_colors, RGBAf(get(IMPRINT_SEQ, commits_by_date[day] / vmax)))
    else
        push!(cell_colors, EMPTY_CELL)
    end
end

# Month labels centered over each month's mid-point week (shown along the top).
month_positions = Float64[]
month_labels    = String[]
for m in 1:12
    mid = Date(2025, m, 15)
    push!(month_positions, div((mid - first_monday).value, 7))
    push!(month_labels, monthabbr(mid))
end

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
    figure_padding  = (40, 40, 24, 24),
)

ax = Axis(
    fig[1, 1];
    title              = "heatmap-calendar · julia · makie · anyplot.ai",
    titlesize          = 24,
    titlecolor         = INK,
    titlegap           = 18,
    backgroundcolor    = PAGE_BG,
    aspect             = n_weeks / (7 * 1.8),   # slightly tall cells fill the band
    yreversed          = true,                  # Monday at the top row
    xaxisposition      = :top,
    xticks             = (month_positions, month_labels),
    yticks             = (1:7, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
    xticklabelsize     = 15,
    yticklabelsize     = 15,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticksvisible      = false,
    yticksvisible      = false,
    xgridvisible       = false,
    ygridvisible       = false,
)
hidespines!(ax)

poly!(ax, cell_rects; color = cell_colors, strokewidth = 0)

xlims!(ax, -0.7, n_weeks - 0.3)
ylims!(ax, 7.7, 0.3)

# Sequential legend for value interpretation.
Colorbar(
    fig[2, 1];
    colormap       = IMPRINT_SEQ,
    limits         = (0, vmax),
    vertical       = false,
    flipaxis       = false,
    label          = "Daily commits",
    labelcolor     = INK,
    labelsize      = 15,
    ticklabelcolor = INK_SOFT,
    ticklabelsize  = 13,
    tickcolor      = INK_SOFT,
    width          = Relative(0.36),
    height         = 16,
)

rowgap!(fig.layout, 12)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
