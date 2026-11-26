# anyplot.ai
# histogram-basic: Basic Histogram
# Library: makie 0.24.16 | Julia 1.13.4
# Quality: 84/100 | Updated: 2026-11-26

using CairoMakie
using Colors
using DataFrames
using Random

# Theme tokens
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# Columns: set these to your table's column names
const CUSTOMER_AGE = "Customer age (years)"  # role: value

# Data: replace this block with your own table, for example df = CSV.read("customers.csv", DataFrame)
Random.seed!(42)
ages_young = randn(200) .* 5 .+ 28
ages_mid = randn(150) .* 8 .+ 55
df = DataFrame(CUSTOMER_AGE => clamp.(vcat(ages_young, ages_mid), 18, 75))

# Plot: reads only df and the constants above
fig = Figure(
    size = (1600, 900),
    fontsize = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title = "histogram-basic · julia · makie · anyplot.ai",
    titlesize = 24,
    titlecolor = INK,
    xlabel = CUSTOMER_AGE,
    ylabel = "Count",
    xlabelsize = 20,
    ylabelsize = 20,
    xlabelcolor = INK,
    ylabelcolor = INK,
    xticklabelsize = 17,
    yticklabelsize = 17,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xtickcolor = INK_SOFT,
    ytickcolor = INK_SOFT,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinecolor = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    xgridvisible = false,
    ygridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15f0),
    xminorgridvisible = false,
    yminorgridvisible = false,
    limits = (nothing, nothing, 0, nothing),
)

hist!(ax, df[!, CUSTOMER_AGE];
    bins = 28,
    color = IMPRINT_PALETTE[1],
    strokecolor = PAGE_BG,
    strokewidth = 1.5,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
