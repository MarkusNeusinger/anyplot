# anyplot.ai
# line-navigator: Line Chart with Mini Navigator
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-05-27

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

const ANYPLOT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
    colorant"#954477",
    colorant"#99B314",
]

# Data: daily temperature sensor readings over 3 years (1095 days)
const N_DAYS = 1095
t = collect(0:N_DAYS-1)
seasonal = 10.0 .* sin.(2π .* t ./ 365.0 .- 1.4) .+ 3.5 .* sin.(4π .* t ./ 365.0)
temperature = 17.0 .+ seasonal .+ 1.5 .* randn(N_DAYS)

# Selection window: 90-day summer peak in year 2
const WIN_START = 450
const WIN_END   = 540
detail_t    = t[WIN_START+1:WIN_END+1]
detail_vals = temperature[WIN_START+1:WIN_END+1]

# Title — at 59 chars, no scaling needed (under 67 baseline)
const TITLE_STR  = "Sensor Data · line-navigator · julia · makie · anyplot.ai"
const TITLE_SIZE = length(TITLE_STR) > 67 ? max(round(Int, 20 * 67 / length(TITLE_STR)), 13) : 20

# Grid colour helper (15% alpha)
const GRID_COLOR = RGBAf(red(INK), green(INK), blue(INK), 0.15f0)

# Figure: size=(1600,900) × px_per_unit=2 → 3200×1800 px
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

# Main detail axis — zoomed into selected window
ax_main = Axis(
    fig[1, 1];
    title              = TITLE_STR,
    titlesize          = TITLE_SIZE,
    titlecolor         = INK,
    xlabel             = "Day",
    xlabelsize         = 11,
    xlabelcolor        = INK,
    ylabel             = "Temperature (°C)",
    ylabelsize         = 14,
    ylabelcolor        = INK,
    xticklabelsize     = 11,
    yticklabelsize     = 11,
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
    ygridcolor         = GRID_COLOR,
    yminorgridvisible  = false,
    xminorgridvisible  = false,
)

# Navigator axis — full time series overview with elevated background for visual hierarchy
ax_nav = Axis(
    fig[2, 1];
    xlabel             = "Day",
    xlabelsize         = 11,
    xlabelcolor        = INK,
    xticklabelsize     = 9,
    yticklabelsize     = 9,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = ELEVATED_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = false,
    yticklabelsvisible = false,
)

# Row proportions: detail 78%, navigator 22% (set after axes are created)
rowsize!(fig.layout, 1, Relative(0.78))
rowsize!(fig.layout, 2, Relative(0.22))
rowgap!(fig.layout, 1, 8)

# Detail view: selected window
brand = ANYPLOT_PALETTE[1]
lines!(ax_main, detail_t, detail_vals; color = brand, linewidth = 2.0f0)

# Annotation: selected range with insight context
detail_ymin, detail_ymax = extrema(detail_vals)
label_x = Float32(detail_t[1] + 3)
label_y = Float32(detail_ymin + 0.87 * (detail_ymax - detail_ymin))
text!(ax_main,
      "Days $(WIN_START)–$(WIN_END) of $(N_DAYS) · Summer temperature peak";
      position = Point2f(label_x, label_y),
      align    = (:left, :center),
      color    = INK_MUTED,
      fontsize = 12)

# Navigator: full series at reduced opacity with matching linewidth for visual consistency
lines!(ax_nav, t, temperature;
       color     = RGBAf(red(brand), green(brand), blue(brand), 0.65f0),
       linewidth = 2.0f0)

# Selection highlight — filled polygon over the selected range
nav_ylo, nav_yhi = extrema(temperature)
nav_pad = (nav_yhi - nav_ylo) * 0.08
sel_verts = Point2f[
    (WIN_START, nav_ylo - nav_pad), (WIN_END, nav_ylo - nav_pad),
    (WIN_END,   nav_yhi + nav_pad), (WIN_START, nav_yhi + nav_pad),
]
poly!(ax_nav, sel_verts;
      color       = RGBAf(red(brand), green(brand), blue(brand), 0.30f0),
      strokewidth = 0)

# Selection edge lines
vlines!(ax_nav, [WIN_START, WIN_END]; color = brand, linewidth = 2.0f0)

save("plot-$(THEME).png", fig; px_per_unit = 2)
