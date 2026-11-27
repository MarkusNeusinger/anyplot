# anyplot.ai
# violin-basic: Basic Violin Plot
# Library: makie 0.24.16 | Julia 1.13.4
# Quality: 83/100 | Updated: 2026-11-27

using CairoMakie
using Colors
using DataFrames
using Random

# Theme tokens — Imprint palette
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette
const IMPRINT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
    colorant"#954477",
    colorant"#99B314",
]

# Columns: set these to your table's column names
const MODE     = "Transport mode"          # role: category
const DURATION = "Commute duration (min)"  # role: value

# Data: replace this block with your own table, for example df = CSV.read("commutes.csv", DataFrame)
Random.seed!(42)
n = 250
modes = ["Walk", "Bike", "Bus", "Car"]
durations = [
    clamp.(randn(n) .* 4.0 .+ 18.0, 4.0, Inf),                                  # walk: narrow
    clamp.(randn(n) .* 7.0 .+ 24.0, 4.0, Inf),                                  # bike: roughly normal
    clamp.(10.0 .+ 55.0 .* rand(n) .^ 2.5, 4.0, Inf),                           # bus: right-skewed
    clamp.(vcat(randn(n ÷ 2) .* 4.0 .+ 16.0, randn(n ÷ 2) .* 8.0 .+ 48.0), 4.0, Inf), # car: bimodal
]
df = DataFrame(
    MODE => repeat(modes; inner = n),
    DURATION => vcat(durations...),
)

# Plot: reads only df and the constants above
categories = unique(df[!, MODE])
x = [findfirst(==(m), categories) for m in df[!, MODE]]
values = df[!, DURATION]

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "violin-basic · julia · makie · anyplot.ai",
    titlesize          = 22,
    titlecolor         = INK,
    xlabel             = MODE,
    ylabel             = DURATION,
    xlabelsize         = 18,
    ylabelsize         = 18,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 16,
    yticklabelsize     = 16,
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
    xticks             = (eachindex(categories), categories),
)

# One violin per category, one Imprint color each; tails end at the data range
violin!(ax, x, values;
    color       = [RGBAf(c, 0.75) for c in IMPRINT_PALETTE[x]],
    datalimits  = extrema,
    strokewidth = 1.0,
    strokecolor = INK_SOFT,
)

# Quartile box and median line inside each violin
boxplot!(ax, x, values;
    color         = (:white, 0.0),
    strokecolor   = INK,
    strokewidth   = 1.5,
    mediancolor   = INK,
    whiskercolor  = INK,
    width         = 0.12,
    whiskerwidth  = 0.5,
    show_outliers = false,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
