# anyplot.ai
# count-basic: Basic Count Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-08-11

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND    = colorant"#009E73"  # Imprint palette position 1 — ALWAYS first series

# --- Data ---------------------------------------------------------------
# Raw per-session device type from a web analytics log — count-basic tallies
# occurrences from unaggregated observations rather than pre-computed values.
device_types  = ["Desktop", "Mobile", "Tablet", "Smart TV", "Wearable"]
session_share = [820, 1150, 340, 95, 45]  # underlying popularity per device
raw_sessions = reduce(vcat, [fill(device, n) for (device, n) in zip(device_types, session_share)])
shuffle!(raw_sessions)

session_counts = Dict{String,Int}()
for device in raw_sessions
    session_counts[device] = get(session_counts, device, 0) + 1
end

# Sorted by frequency, descending
sorted_devices = sort(collect(keys(session_counts)); by = d -> session_counts[d], rev = true)
sorted_counts  = [session_counts[d] for d in sorted_devices]

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "count-basic · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Device Type",
    ylabel            = "Sessions",
    xlabelsize        = 16,
    ylabelsize        = 16,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 13,
    yticklabelsize    = 13,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.12),
    xticks            = (1:length(sorted_devices), sorted_devices),
)

barplot!(ax, 1:length(sorted_devices), sorted_counts; color = BRAND, width = 0.62)

for (i, count) in enumerate(sorted_counts)
    text!(
        ax, i, count;
        text = string(count),
        align = (:center, :bottom),
        offset = (0, 6),
        fontsize = 14,
        color = INK_SOFT,
    )
end

ylims!(ax, 0, maximum(sorted_counts) * 1.12)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
