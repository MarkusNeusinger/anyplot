# anyplot.ai
# bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-06-14

using CairoMakie
using Colors

const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Semantic zone colors: conventional fitness zone color scheme (semantic exception)
# Z1→grey/muted, Z2→Imprint blue, Z3→Imprint green, Z4→Imprint ochre, Z5→Imprint red
const ZONE_COLORS = [
    INK_MUTED,           # Z1 Recovery  — grey (theme-adaptive muted)
    colorant"#4467A3",   # Z2 Endurance — Imprint blue
    colorant"#009E73",   # Z3 Aerobic   — Imprint brand green
    colorant"#BD8233",   # Z4 Threshold — Imprint ochre
    colorant"#AE3030",   # Z5 Maximum   — Imprint matte red
]

# Data — 90-minute endurance ride
const ZONE_POS    = [1, 2, 3, 4, 5]
const MINUTES     = [10.0, 48.0, 20.0, 10.0, 2.0]
const TOTAL_MIN   = sum(MINUTES)
const ZONE_LABELS = ["Z1\nRecovery", "Z2\nEndurance", "Z3\nAerobic", "Z4\nThreshold", "Z5\nMaximum"]

const TITLE_STR = "90-Min Endurance Ride · bar-heart-rate-zones · julia · makie · anyplot.ai"
const TITLESIZE = round(Int, 20 * min(1.0, 67 / length(TITLE_STR)))

fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title              = TITLE_STR,
    titlesize          = TITLESIZE,
    titlefont          = :bold,
    titlecolor         = INK,
    xlabel             = "Heart Rate Zone",
    ylabel             = "Time (minutes)",
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
    yminorgridvisible  = false,
    xminorgridvisible  = false,
    xticks             = (ZONE_POS, ZONE_LABELS),
)

barplot!(ax, ZONE_POS, MINUTES; color = ZONE_COLORS, width = 0.65, strokewidth = 0)

# Duration + percentage breakdown labels above each bar
# Dominant zone (Z2) rendered in zone color and bold for storytelling emphasis
for (i, m) in enumerate(MINUTES)
    pct = round(Int, 100 * m / TOTAL_MIN)
    if i == 2  # Z2 Endurance — dominant zone
        text!(ax, i, m + 1.2;
            text     = "$(Int(m)) min\n$(pct)%",
            align    = (:center, :bottom),
            fontsize = 13,
            color    = ZONE_COLORS[2],
            font     = :bold,
        )
    else
        text!(ax, i, m + 1.2;
            text     = "$(Int(m)) min\n$(pct)%",
            align    = (:center, :bottom),
            fontsize = 12,
            color    = INK,
        )
    end
end

# Dominant zone callout — session context in the upper-right open space
text!(ax, 5.38, maximum(MINUTES) * 1.25;
    text  = "Base endurance ride\nZ2-heavy · 53% of session",
    align = (:right, :top),
    fontsize = 11,
    color    = INK_MUTED,
    font     = :italic,
)

ylims!(ax, 0, maximum(MINUTES) * 1.40)

# HR zone boundary legend — Makie composable layout with PolyElement patches
legend_patches = [PolyElement(color = ZONE_COLORS[i], strokewidth = 0) for i in 1:5]
legend_labels = [
    "Z1 Recovery  < 60% HRmax",
    "Z2 Endurance  60–70% HRmax",
    "Z3 Aerobic  70–80% HRmax",
    "Z4 Threshold  80–90% HRmax",
    "Z5 Maximum  > 90% HRmax",
]

Legend(fig[2, 1], legend_patches, legend_labels, "HR Zone Boundaries";
    orientation  = :horizontal,
    framevisible = false,
    labelcolor   = INK_SOFT,
    titlecolor   = INK_SOFT,
    labelsize    = 10,
    titlesize    = 11,
    patchsize    = (20, 12),
)

rowsize!(fig.layout, 2, Relative(0.08))
rowgap!(fig.layout, 6)

save("plot-$(THEME).png", fig; px_per_unit = 2)
