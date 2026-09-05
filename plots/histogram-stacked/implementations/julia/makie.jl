# anyplot.ai
# histogram-stacked: Stacked Histogram
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -----------------------------------------------------------------------
locations = ["Downtown", "Uptown", "Airport"]
wait_downtown = max.(randn(600) .* 2.2 .+ 6.5, 0.2)
wait_uptown   = max.(randn(450) .* 2.6 .+ 8.5, 0.2)
wait_airport  = max.(randn(350) .* 3.4 .+ 11.0, 0.2)
wait_times = vcat(wait_downtown, wait_uptown, wait_airport)
group_labels = vcat(
    fill(locations[1], length(wait_downtown)),
    fill(locations[2], length(wait_uptown)),
    fill(locations[3], length(wait_airport)),
)

n_bins = 22
bin_edges = range(minimum(wait_times), maximum(wait_times); length = n_bins + 1)
bin_width = step(bin_edges)
bin_centers = (bin_edges[1:end-1] .+ bin_edges[2:end]) ./ 2

counts = zeros(Int, n_bins, length(locations))
for (val, grp) in zip(wait_times, group_labels)
    bin_idx = clamp(searchsortedlast(bin_edges, val), 1, n_bins)
    grp_idx = findfirst(==(grp), locations)
    counts[bin_idx, grp_idx] += 1
end

x_flat = repeat(bin_centers; outer = length(locations))
height_flat = vec(counts)
stack_flat = repeat(1:length(locations); inner = n_bins)
color_flat = IMPRINT_PALETTE[stack_flat]

# Focal-point insight: which bin sees the most total traffic, and which
# location dominates it — turns the raw stack into a story instead of
# just displaying the composition.
totals = vec(sum(counts, dims = 2))
peak_idx = argmax(totals)
peak_x = bin_centers[peak_idx]
peak_total = totals[peak_idx]
peak_group = locations[argmax(counts[peak_idx, :])]

# --- Plot -----------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "histogram-stacked · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    subtitle          = "Peak volume at $(round(peak_x, digits = 1)) min ($(peak_total) customers) — $(peak_group) leads this bin",
    subtitlesize      = 14,
    subtitlecolor     = INK_SOFT,
    xlabel            = "Wait Time (minutes)",
    ylabel            = "Number of Customers",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

barplot!(ax, x_flat, height_flat;
         stack = stack_flat, color = color_flat,
         width = bin_width * 0.95, strokewidth = 1.5, strokecolor = PAGE_BG)

# Callout on the busiest bin — a layered `text!` annotation gives the eye a
# focal point instead of leaving the composition shift to be inferred.
text!(ax, peak_x, peak_total;
      text = "▲ $(peak_group) leads",
      color = INK, fontsize = 13, font = :bold,
      align = (:center, :bottom), offset = (0, 6))
ylims!(ax, 0, maximum(totals) * 1.18)

legend_elements = [PolyElement(color = c) for c in IMPRINT_PALETTE[1:length(locations)]]
Legend(fig[1, 2], legend_elements, locations, "Location";
       labelcolor = INK_SOFT, titlecolor = INK,
       backgroundcolor = PAGE_BG, framevisible = false,
       patchsize = (18, 18), rowgap = 6)

# --- Save -----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
