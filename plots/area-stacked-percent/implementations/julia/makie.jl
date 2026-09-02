# anyplot.ai
# area-stacked-percent: 100% Stacked Area Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 93/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -----------------------------------------------------------------
# Quarterly revenue mix for a software vendor, shifting from perpetual
# licenses/hardware toward subscription + support over three years.
n_quarters   = 16
quarter_of   = i -> ((i - 1) % 4) + 1
year_of      = i -> 2021 + div(i - 1, 4)
quarter_lbls = ["Q$(quarter_of(i)) $(year_of(i))" for i in 1:n_quarters]
categories   = ["Subscription", "Support", "Services", "Hardware", "License"]
n_categories = length(categories)

progress = range(0.0, 1.0, length = n_quarters)

subscription = 18.0 .+ 34.0 .* progress .^ 1.3 .+ randn(n_quarters) .* 1.5
support      = 16.0 .+ 3.0  .* progress          .+ randn(n_quarters) .* 1.2
services     = 14.0 .+ 4.0  .* progress          .+ randn(n_quarters) .* 1.3
hardware     = 20.0 .- 6.0  .* progress          .+ randn(n_quarters) .* 1.4
license      = 34.0 .- 24.0 .* progress .^ 1.2   .+ randn(n_quarters) .* 1.5

revenue     = clamp.(hcat(subscription, support, services, hardware, license), 1.0, Inf)
percentages = revenue ./ sum(revenue, dims = 2) .* 100.0
cum_share   = cumsum(percentages, dims = 2)

x = 1:n_quarters

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title               = "area-stacked-percent · julia · makie · anyplot.ai",
    titlesize           = 22,
    titlecolor          = INK,
    xlabel              = "Quarter",
    ylabel              = "Share of Revenue",
    xlabelsize          = 16,
    ylabelsize          = 16,
    xlabelcolor         = INK,
    ylabelcolor         = INK,
    xticklabelsize      = 13,
    yticklabelsize      = 13,
    xticklabelcolor     = INK_SOFT,
    yticklabelcolor     = INK_SOFT,
    xtickcolor          = INK_SOFT,
    ytickcolor          = INK_SOFT,
    leftspinecolor      = INK_SOFT,
    bottomspinecolor    = INK_SOFT,
    topspinevisible     = false,
    rightspinevisible   = false,
    backgroundcolor     = PAGE_BG,
    xticks              = (1:2:n_quarters, quarter_lbls[1:2:end]),
    xticklabelrotation  = pi / 6,
    yticks              = 0:20:100,
    ytickformat         = ys -> ["$(round(Int, y))%" for y in ys],
    xgridvisible        = false,
    ygridcolor          = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

xlims!(ax, 1, n_quarters)
ylims!(ax, 0, 100)

for k in 1:n_categories
    lower_k = k == 1 ? zeros(n_quarters) : cum_share[:, k - 1]
    upper_k = cum_share[:, k]
    band!(ax, x, lower_k, upper_k; color = IMPRINT_PALETTE[k], label = categories[k])
    lines!(ax, x, upper_k; color = PAGE_BG, linewidth = 1.5)
end

Legend(
    fig[1, 2], ax, "Product Line";
    labelsize       = 13,
    labelcolor      = INK_SOFT,
    titlesize       = 14,
    titlecolor      = INK,
    framevisible    = false,
    backgroundcolor = PAGE_BG,
)

colsize!(fig.layout, 1, Relative(0.85))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
