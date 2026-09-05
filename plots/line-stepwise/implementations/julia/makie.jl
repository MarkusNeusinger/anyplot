# anyplot.ai
# line-stepwise: Step Line Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — first series is always brand green
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]

# --- Data ---------------------------------------------------------------
# Warehouse pallet inventory over a 24h operating day: each delivery or
# outgoing shipment nudges the stock level, which then holds constant until
# the next event — a natural fit for a post-aligned step plot. Gaps between
# events are floored so clusters of near-simultaneous jumps don't muddy the
# step shape.
n_events = 46
min_gap = 0.18
gaps = min_gap .+ rand(n_events) .* (24 / n_events - min_gap) * 1.8
event_hours = cumsum(gaps)
event_hours = event_hours[event_hours .< 24]
hour = vcat(0.0, event_hours, 24.0)

stock = zeros(Int, length(hour))
stock[1] = 950
for i in 2:length(stock)-1
    jump = rand() < 0.55 ? rand(20:80) : -rand(20:80)
    stock[i] = clamp(stock[i-1] + jump, 400, 1600)
end
stock[end] = stock[end-1]

peak_idx = argmax(stock)
peak_hour, peak_stock = hour[peak_idx], stock[peak_idx]

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-stepwise · julia · makie · anyplot.ai",
    titlesize          = 25,
    titlecolor         = INK,
    xlabel             = "Hour of Day",
    ylabel             = "Pallets in Stock",
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
    xticks             = 0:6:24,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    yminorgridvisible  = false,
)

stairs!(ax, hour, stock; step = :post, color = BRAND, linewidth = 3.0)

# Focal point: call out the peak stock level reached during the day
scatter!(ax, [peak_hour], [peak_stock]; color = BRAND, markersize = 12, strokewidth = 2, strokecolor = PAGE_BG)
text!(
    ax, peak_hour, peak_stock;
    text = "Peak: $(peak_stock) pallets",
    color = INK,
    fontsize = 13,
    align = (peak_hour > 20 ? :right : :left, :bottom),
    offset = (peak_hour > 20 ? -10 : 10, 8),
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
