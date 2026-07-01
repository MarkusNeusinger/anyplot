# anyplot.ai
# lollipop-basic: Basic Lollipop Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-07-01

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (always first categorical series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data — renewable energy share (%) by country
countries = ["Norway", "Iceland", "Austria", "Sweden", "New Zealand",
             "Germany", "UK", "Canada", "Australia", "USA"]
pct_renew = [98.0, 85.0, 71.0, 65.0, 58.0, 46.0, 39.0, 32.0, 24.0, 18.0]

# Sort ascending so values rise left-to-right
order            = sortperm(pct_renew)
sorted_countries = countries[order]
sorted_pct       = pct_renew[order]
n                = length(sorted_pct)

# Build stem point pairs for linesegments!
stem_pts = Point2f[]
for (i, val) in enumerate(sorted_pct)
    push!(stem_pts, Point2f(i, 0.0))
    push!(stem_pts, Point2f(i, val))
end

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "lollipop-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Country",
    ylabel             = "Renewable Energy Share (%)",
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    yminorgridvisible  = false,
    xminorgridvisible  = false,
)

ax.xticks = (1:n, sorted_countries)
ax.xticklabelrotation = π / 6

# Stems
linesegments!(ax, stem_pts; color = IMPRINT_PALETTE[1], linewidth = 2.5)

# Dots
scatter!(ax, collect(1:n), sorted_pct;
    color       = IMPRINT_PALETTE[1],
    markersize  = 18,
    strokewidth = 2.0,
    strokecolor = PAGE_BG,
)

ylims!(ax, 0, 105)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
