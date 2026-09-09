# anyplot.ai
# timeline-basic: Event Timeline
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 83/100 | Created: 2026-09-09

using CairoMakie
using Dates
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
    colorant"#2ABCCD",
]

# --- Data ---------------------------------------------------------------
milestones = [
    (Date(2024, 1, 15), "Kickoff & Planning", "Planning"),
    (Date(2024, 2, 20), "Requirements Signed Off", "Planning"),
    (Date(2024, 3, 10), "Architecture Design", "Design"),
    (Date(2024, 4, 5), "UI Prototype Approved", "Design"),
    (Date(2024, 5, 18), "Core API Complete", "Build"),
    (Date(2024, 6, 22), "Database Migration", "Build"),
    (Date(2024, 7, 30), "Feature Freeze", "Build"),
    (Date(2024, 9, 2), "Beta Release", "Testing"),
    (Date(2024, 10, 14), "Security Audit Passed", "Testing"),
    (Date(2024, 11, 25), "General Availability", "Launch"),
]

categories = ["Planning", "Design", "Build", "Testing", "Launch"]
category_colors = Dict(
    "Planning" => IMPRINT_PALETTE[1],
    "Design"   => IMPRINT_PALETTE[2],
    "Build"    => IMPRINT_PALETTE[3],
    "Testing"  => IMPRINT_PALETTE[4],
    "Launch"   => IMPRINT_PALETTE[5],
)

dates       = [m[1] for m in milestones]
event_names = [m[2] for m in milestones]
event_cats  = [m[3] for m in milestones]
day_numbers = Float64.(Dates.value.(dates .- dates[1]))
event_colors = [category_colors[c] for c in event_cats]

# --- Plot -----------------------------------------------------------------
title_str = "timeline-basic · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 27,
    titlecolor         = INK,
    backgroundcolor    = PAGE_BG,
    xlabel             = "2024",
    xlabelsize         = 14,
    xlabelcolor        = INK,
    xticksvisible      = false,
    xticklabelsvisible = false,
    leftspinevisible   = false,
    rightspinevisible  = false,
    topspinevisible    = false,
    bottomspinecolor   = INK_SOFT,
    yticksvisible      = false,
    yticklabelsvisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
)

hidespines!(ax, :l, :r, :t)
ylims!(ax, -1.6, 1.6)

# Baseline axis
hlines!(ax, [0]; color = INK_SOFT, linewidth = 2)

# Stems + alternating labels above/below to prevent overlap
for (i, day) in enumerate(day_numbers)
    above = isodd(i)
    stem_top = above ? 0.9 : -0.9
    label_y = above ? 1.1 : -1.1

    lines!(ax, [day, day], [0.0, stem_top]; color = event_colors[i], linewidth = 2)

    label = event_names[i] * "\n" * Dates.format(dates[i], "u d")
    text!(
        ax, day, label_y;
        text  = label,
        color = INK,
        fontsize = 13,
        align = (:center, above ? :bottom : :top),
        lineheight = 1.3,
    )
end

scatter!(
    ax, day_numbers, zeros(length(day_numbers));
    color = event_colors, markersize = 20, strokewidth = 2, strokecolor = PAGE_BG,
)

# Legend for categories
legend_elements = [
    MarkerElement(color = category_colors[c], marker = :circle, markersize = 16)
    for c in categories
]
Legend(
    fig[2, 1], legend_elements, categories;
    orientation = :horizontal,
    framevisible = false,
    labelcolor = INK_SOFT,
    labelsize = 12,
    tellwidth = false,
    tellheight = true,
)
rowsize!(fig.layout, 2, Relative(0.08))

hideydecorations!(ax)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
