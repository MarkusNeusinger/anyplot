# anyplot.ai
# density-basic: Basic Density Plot
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-05-30

using CairoMakie
using Colors
using DataFrames
using Random

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (always first)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Columns: set these to your table's column names
const CLICK_DELAY = "Ad click delay (seconds)"  # role: values

# Data: replace this block with your own table, for example df = CSV.read("clicks.csv", DataFrame)
# Delays between seeing an ad and clicking it: right-skewed, most clicks come quickly
Random.seed!(42)
df = DataFrame(CLICK_DELAY => exp.(1.1 .+ 0.6 .* randn(400)))

# Plot: reads only df and the constants above
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "density-basic · julia · makie · anyplot.ai",
    titlesize         = 22,
    titlecolor        = INK,
    xlabel            = CLICK_DELAY,
    ylabel            = "Density",
    xlabelsize        = 16,
    ylabelsize        = 16,
    xticklabelsize    = 14,
    yticklabelsize    = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.12),
    xminorgridvisible = false,
    yminorgridvisible = false,
)

values = df[!, CLICK_DELAY]

density!(ax, values;
    color       = (IMPRINT_PALETTE[1], THEME == "dark" ? 0.40 : 0.30),
    strokecolor = IMPRINT_PALETTE[1],
    strokewidth = 3,
)

# Rug plot: each observation as a tick along the baseline
scatter!(ax, values, zeros(length(values));
    marker      = :vline,
    markersize  = 12,
    color       = (IMPRINT_PALETTE[1], 0.6),
    strokewidth = 0,
)

ylims!(ax, 0, nothing)
xlims!(ax, minimum(values) - 0.05 * (maximum(values) - minimum(values)), nothing)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
