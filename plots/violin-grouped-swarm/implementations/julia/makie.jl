# anyplot.ai
# violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-02

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

# --- Data ---------------------------------------------------------------
# Response times (ms) for 3 task types, split by 2 expertise levels.
task_types = ["Search", "Compute", "Render"]
expertise_levels = ["Junior", "Senior"]
n_per_group = 40

log_median = Dict("Search" => 4.2, "Compute" => 4.6, "Render" => 5.0)
log_spread = Dict("Search" => 0.28, "Compute" => 0.3, "Render" => 0.33)
expertise_shift = Dict("Junior" => 0.25, "Senior" => -0.15)

task_idx = Int[]
expertise_idx = Int[]
response_time = Float64[]

for (ti, task) in enumerate(task_types), (ei, level) in enumerate(expertise_levels)
    times = exp.(log_median[task] .+ expertise_shift[level] .+ log_spread[task] .* randn(n_per_group))
    append!(task_idx, fill(ti, n_per_group))
    append!(expertise_idx, fill(ei, n_per_group))
    append!(response_time, times)
end

point_color = [IMPRINT_PALETTE[i] for i in expertise_idx]

# --- Dodge geometry (mirrors Makie's internal violin dodge math, so swarm
# points line up with their violin's footprint) ------------------------------
const GAP = 0.2
const DODGE_GAP = 0.05
const N_DODGE = length(expertise_levels)

scale_width(dodge_gap, n_dodge) = (1 - (n_dodge - 1) * dodge_gap) / n_dodge
shift_dodge(i, dodge_width, dodge_gap) = (dodge_width - 1) / 2 + (i - 1) * (dodge_width + dodge_gap)

violin_slot_width = (1 - GAP) * scale_width(DODGE_GAP, N_DODGE)
slot_center(task, expertise) = task + (1 - GAP) * shift_dodge(expertise, scale_width(DODGE_GAP, N_DODGE), DODGE_GAP)

# --- Beeswarm layout: bin observations by value, spread symmetrically
# around the violin's dodge slot so overlapping points fan out sideways. ----
function beeswarm_offsets(values, nbins, step, max_offset)
    ymin, ymax = extrema(values)
    binwidth = (ymax - ymin) / nbins
    order = sortperm(values)
    bin_counts = zeros(Int, nbins)
    offsets = zeros(length(values))
    for i in order
        b = binwidth > 0 ? clamp(floor(Int, (values[i] - ymin) / binwidth) + 1, 1, nbins) : 1
        c = bin_counts[b]
        rank = (c + 1) ÷ 2
        side = iseven(c) ? 1 : -1
        offsets[i] = clamp(side * rank * step, -max_offset, max_offset)
        bin_counts[b] += 1
    end
    return offsets
end

swarm_x = zeros(length(response_time))
max_swarm_offset = violin_slot_width / 2 * 0.85
for ti in eachindex(task_types), ei in eachindex(expertise_levels)
    mask = (task_idx .== ti) .& (expertise_idx .== ei)
    offsets = beeswarm_offsets(response_time[mask], 16, 0.018, max_swarm_offset)
    swarm_x[mask] .= slot_center(ti, ei) .+ offsets
end

# --- Plot -----------------------------------------------------------------
title_str = "violin-grouped-swarm · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Task Type",
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
    xticks             = (1:length(task_types), task_types),
    limits             = (0.5, length(task_types) + 0.5, nothing, nothing),
)

violin!(
    ax, task_idx, response_time;
    dodge = expertise_idx, n_dodge = N_DODGE, gap = GAP, dodge_gap = DODGE_GAP,
    color = [RGBAf(c.r, c.g, c.b, 0.5) for c in point_color],
    strokecolor = INK_SOFT, strokewidth = 1, datalimits = (0, Inf),
)

scatter!(
    ax, swarm_x, response_time;
    color = point_color, markersize = 6, strokewidth = 0.5, strokecolor = PAGE_BG,
)

# --- Focal annotation: call out the group with the widest spread -----------
focal_task  = findfirst(==("Render"), task_types)
focal_level = findfirst(==("Junior"), expertise_levels)
focal_mask  = (task_idx .== focal_task) .& (expertise_idx .== focal_level)
focal_x     = slot_center(focal_task, focal_level)
focal_y     = maximum(response_time[focal_mask])
text!(
    ax, focal_x, focal_y;
    text = "Widest spread", align = (:left, :bottom), offset = (10, 2),
    color = INK_SOFT, fontsize = 11, font = :italic,
)

legend_elements = [MarkerElement(color = IMPRINT_PALETTE[i], marker = :circle, markersize = 14) for i in eachindex(expertise_levels)]
Legend(
    fig[1, 2], legend_elements, expertise_levels, "Expertise Level";
    labelcolor = INK_SOFT, titlecolor = INK, framevisible = false,
    labelsize = 12, titlesize = 14,
)
colsize!(fig.layout, 2, Fixed(160))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
