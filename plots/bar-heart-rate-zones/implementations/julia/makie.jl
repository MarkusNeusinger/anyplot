# anyplot.ai
# bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-14

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
const ZONE_LABELS = ["Z1\nRecovery", "Z2\nEndurance", "Z3\nAerobic", "Z4\nThreshold", "Z5\nMaximum"]

fmt_min(m) = "$(Int(m)) min"

const TITLE_STR = "90-Min Endurance Ride · bar-heart-rate-zones · julia · makie · anyplot.ai"
const TITLESIZE = round(Int, 20 * min(1.0, 67 / length(TITLE_STR)))

fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title              = TITLE_STR,
    titlesize          = TITLESIZE,
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

for (i, m) in enumerate(MINUTES)
    text!(ax, i, m + 1.0;
        text = fmt_min(m), align = (:center, :bottom), fontsize = 13, color = INK,
    )
end

ylims!(ax, 0, maximum(MINUTES) * 1.18)

save("plot-$(THEME).png", fig; px_per_unit = 2)
