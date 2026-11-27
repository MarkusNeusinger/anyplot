# anyplot.ai
# hexbin-basic: Basic Hexbin Plot
# Library: makie 0.24.16 | Julia 1.13.4
# Quality: 84/100 | Updated: 2026-11-27

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

# Imprint sequential ramp (fields: colored cells fill the plot)
const ANYPLOT_SEQ_FIELDS = THEME == "light" ?
    cgrad([colorant"#66E2B2", colorant"#009E73", colorant"#024582", colorant"#351E45"], [0.0, 0.369, 0.803, 1.0]) :
    cgrad([colorant"#404C02", colorant"#009E73", colorant"#CDD9FF"], [0.0, 0.487, 1.0])

# Columns: set these to your table's column names
const LONGITUDE = "Longitude (relative km)"  # role: x
const LATITUDE = "Latitude (relative km)"    # role: y

# Data: simulated urban GPS coordinates with clustered hotspots (12000 points)
Random.seed!(42)
centers = [(0.0, 0.0, 0.4, 0.4), (-2.0, 2.2, 0.5, 0.4), (2.4, 0.6, 0.5, 0.4), (0.4, -2.5, 0.45, 0.4)]
sizes = [5000, 2500, 2500, 2000]
df = DataFrame(
    LONGITUDE => reduce(vcat, [randn(n) .* c[3] .+ c[1] for (c, n) in zip(centers, sizes)]),
    LATITUDE => reduce(vcat, [randn(n) .* c[4] .+ c[2] for (c, n) in zip(centers, sizes)]),
)

# Plot
# Figure
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 16,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "hexbin-basic · julia · makie · anyplot.ai",
    titlesize          = 24,
    titlecolor         = INK,
    xlabel             = LONGITUDE,
    ylabel             = LATITUDE,
    xlabelsize         = 18,
    ylabelsize         = 18,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 15,
    yticklabelsize     = 15,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12f0),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12f0),
    aspect             = DataAspect(),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

# Log colorscale surfaces peripheral mid-density clusters that would otherwise wash out
hb = hexbin!(ax, df[!, LONGITUDE], df[!, LATITUDE];
    cellsize    = 0.22,
    colormap    = ANYPLOT_SEQ_FIELDS,
    colorscale  = log10,
    strokewidth = 0,
)

# Colorbar with log-scale ticks
Colorbar(fig[1, 2], hb;
    label          = "Point count (log scale)",
    labelsize      = 18,
    labelcolor     = INK,
    ticklabelsize  = 15,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    ticks          = LogTicks(0:3),
    width          = 24,
)

colgap!(fig.layout, 14)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
