# anyplot.ai
# line-load-duration: Load Duration Curve for Energy Systems
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-06-10

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data — synthetic annual hourly load profile for a mid-sized utility
n_hours = 8760

# Build a realistic load duration curve:
# base component + daily/seasonal variation
base_load = 420.0
daily_variation = 150.0 * (0.5 .+ 0.5 .* sin.(range(0, 2π * 365, length=n_hours)))
intraday_variation = 80.0 .* (0.5 .+ 0.5 .* sin.(range(0, 2π * n_hours, length=n_hours)))
noise = 40.0 .* randn(n_hours)

raw_loads = base_load .+ daily_variation .+ intraday_variation .+ noise

# Clamp and sort descending (load duration curve definition)
raw_loads = clamp.(raw_loads, 380.0, 1250.0)
load_mw = sort(raw_loads, rev=true)
hours = 0:(n_hours - 1)

# Capacity tier boundaries (hours)
peak_end      = 876    # top 10% of hours
intermediate_end = 4380  # top 50% of hours

# Corresponding load levels at tier boundaries
peak_capacity_mw        = load_mw[peak_end + 1]
intermediate_capacity_mw = load_mw[intermediate_end + 1]
base_capacity_mw        = minimum(load_mw) + 20.0

# Total energy (area under curve) in GWh
total_energy_gwh = sum(load_mw) / 1000.0

# Plot
const TITLE = "line-load-duration · julia · makie · anyplot.ai"
n_title = length(TITLE)
title_fontsize = n_title > 67 ? round(Int, 20 * 67 / n_title) : 20

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = TITLE,
    titlesize          = title_fontsize,
    titlecolor         = INK,
    xlabel             = "Duration (hours per year)",
    ylabel             = "Load (MW)",
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
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    yminorgridvisible  = false,
    xminorgridvisible  = false,
    limits             = (0, n_hours, 0, maximum(load_mw) * 1.08),
)

# Fill the three load regions under the curve
peak_hours   = 0:peak_end
inter_hours  = peak_end:(intermediate_end)
base_hours   = intermediate_end:(n_hours - 1)

# Peak region (leftmost, brief spikes) — matte red with low alpha
band!(ax,
    collect(peak_hours),
    zeros(length(peak_hours)),
    load_mw[peak_hours .+ 1];
    color = RGBAf(IMPRINT_PALETTE[5].r, IMPRINT_PALETTE[5].g, IMPRINT_PALETTE[5].b, 0.18),
)

# Intermediate region — ochre
band!(ax,
    collect(inter_hours),
    zeros(length(inter_hours)),
    load_mw[inter_hours .+ 1];
    color = RGBAf(IMPRINT_PALETTE[4].r, IMPRINT_PALETTE[4].g, IMPRINT_PALETTE[4].b, 0.28),
)

# Base load region (rightmost, always-on) — brand green
band!(ax,
    collect(base_hours),
    zeros(length(base_hours)),
    load_mw[base_hours .+ 1];
    color = RGBAf(IMPRINT_PALETTE[1].r, IMPRINT_PALETTE[1].g, IMPRINT_PALETTE[1].b, 0.22),
)

# Main load duration curve
lines!(ax, collect(hours), load_mw;
    color     = IMPRINT_PALETTE[1],
    linewidth = 2.5,
)

# Horizontal dashed capacity tier lines
hlines!(ax, [peak_capacity_mw, intermediate_capacity_mw, base_capacity_mw];
    color     = [IMPRINT_PALETTE[5], IMPRINT_PALETTE[4], IMPRINT_PALETTE[1]],
    linestyle = :dash,
    linewidth = 1.5,
)

# Vertical boundary lines between regions
vlines!(ax, [peak_end, intermediate_end];
    color     = RGBAf(INK_MUTED.r, INK_MUTED.g, INK_MUTED.b, 0.5),
    linestyle = :dot,
    linewidth = 1.2,
)

# Region labels
text!(ax, peak_end / 2, maximum(load_mw) * 0.92;
    text      = "Peak\nLoad",
    align     = (:center, :top),
    fontsize  = 13,
    color     = IMPRINT_PALETTE[5],
    font      = :bold,
)

text!(ax, (peak_end + intermediate_end) / 2, maximum(load_mw) * 0.92;
    text      = "Intermediate\nLoad",
    align     = (:center, :top),
    fontsize  = 13,
    color     = IMPRINT_PALETTE[4],
    font      = :bold,
)

text!(ax, (intermediate_end + n_hours) / 2, maximum(load_mw) * 0.92;
    text      = "Base\nLoad",
    align     = (:center, :top),
    fontsize  = 13,
    color     = IMPRINT_PALETTE[1],
    font      = :bold,
)

# Capacity tier labels on right margin
label_x = n_hours * 0.94
text!(ax, label_x, peak_capacity_mw + 12;
    text     = "Peak cap. $(round(Int, peak_capacity_mw)) MW",
    align    = (:right, :bottom),
    fontsize = 11,
    color    = IMPRINT_PALETTE[5],
)

text!(ax, label_x, intermediate_capacity_mw + 12;
    text     = "Interm. cap. $(round(Int, intermediate_capacity_mw)) MW",
    align    = (:right, :bottom),
    fontsize = 11,
    color    = IMPRINT_PALETTE[4],
)

text!(ax, label_x, base_capacity_mw + 12;
    text     = "Base cap. $(round(Int, base_capacity_mw)) MW",
    align    = (:right, :bottom),
    fontsize = 11,
    color    = IMPRINT_PALETTE[1],
)

# Total energy annotation (area under curve)
energy_label = "Total annual energy: $(round(Int, total_energy_gwh)) GWh"
text!(ax, n_hours * 0.50, maximum(load_mw) * 0.44;
    text     = energy_label,
    align    = (:center, :center),
    fontsize = 13,
    color    = INK_SOFT,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
