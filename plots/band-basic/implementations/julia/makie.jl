# anyplot.ai
# band-basic: Basic Band Plot
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: pending | Updated: 2026-11-27

using CairoMakie
using Colors
using DataFrames
using Random

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green, ALWAYS first series (Imprint palette)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Theme-adaptive band alpha: higher in dark mode for contrast
const BAND_ALPHA = THEME == "light" ? 0.25f0 : 0.45f0

# Columns: set these to your table's column names
const DAY = "Forecast day"            # role: x
const LOWER = "Lower 95% bound (°C)"  # role: lower
const UPPER = "Upper 95% bound (°C)"  # role: upper
const CENTER = "Forecast mean (°C)"   # role: center

# Data: 60-day temperature forecast with a widening 95% confidence interval
Random.seed!(42)
days = 1:60
center = 14.0 .+ 0.06 .* days .+ 3.0 .* sin.(2π .* days ./ 30)
halfwidth = 1.96 .* (0.5 .+ 0.05 .* days)
df = DataFrame(
    DAY => collect(days),
    LOWER => center .- halfwidth,
    UPPER => center .+ halfwidth,
    CENTER => center,
)

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "band-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    titlefont          = :bold,
    xlabel             = DAY,
    ylabel             = "Temperature (°C)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
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
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15f0),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

# 95% confidence interval band (semi-transparent Imprint brand green)
band!(ax, df[!, DAY], df[!, LOWER], df[!, UPPER];
    color = (IMPRINT_PALETTE[1], BAND_ALPHA))

# Central forecast line
lines!(ax, df[!, DAY], df[!, CENTER];
    color     = IMPRINT_PALETTE[1],
    linewidth = 2.5)

# Legend
axislegend(ax,
    [PolyElement(color = (IMPRINT_PALETTE[1], BAND_ALPHA), strokewidth = 0),
     LineElement(color = IMPRINT_PALETTE[1], linewidth = 2.5)],
    ["95% CI", "Forecast mean"],
    position         = :lt,
    backgroundcolor  = ELEVATED_BG,
    framecolor       = INK_SOFT,
    labelcolor       = INK_SOFT,
    labelsize        = 12,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
