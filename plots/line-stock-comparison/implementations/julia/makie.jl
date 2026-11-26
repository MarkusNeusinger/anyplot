# anyplot.ai
# line-stock-comparison: Stock Price Comparison Chart
# Library: makie 0.24.16 | Julia 1.13.4
# Quality: 81/100 | Updated: 2026-11-26

using CairoMakie
using Colors
using DataFrames
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# Columns: set these to your table's column names
const DAY    = "Trading day"                   # role: x
const SYMBOL = "Symbol"                        # role: group
const PRICE  = "Rebased performance (start = 100)"  # role: value

# Data: 252 trading days (~1 year) for 4 assets, geometric Brownian motion rebased to 100
# Replace this block with your own table, for example df = CSV.read("prices.csv", DataFrame)
Random.seed!(42)
n_days = 252
gbm_params = [   # (symbol, daily drift, daily volatility)
    ("NVDA", 0.0018, 0.038),
    ("AAPL", 0.0007, 0.019),
    ("AMZN", 0.0005, 0.023),
    ("SPY",  0.0003, 0.012),
]
frames = map(gbm_params) do (sym, μ, σ)
    p = fill(100.0, n_days)
    for i in 2:n_days
        p[i] = p[i-1] * (1.0 + μ + σ * randn())
    end
    DataFrame(DAY => 1:n_days, SYMBOL => sym, PRICE => p)
end
df = reduce(vcat, frames)

# Plot
symbols = unique(df[!, SYMBOL])
n_days_plot = maximum(df[!, DAY])

# Month tick positions (~21 trading days per month)
month_ticks  = collect(1:21:n_days_plot)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][1:length(month_ticks)]

# Semi-transparent colors for grid and reference line
grid_col = RGBAf(red(INK), green(INK), blue(INK), 0.15f0)
ref_col  = RGBAf(red(INK), green(INK), blue(INK), 0.40f0)

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-stock-comparison · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Month (one trading year, daily close)",
    ylabel             = PRICE,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = grid_col,
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    xticks             = (month_ticks, month_labels),
)

# Horizontal reference line at 100 (common starting point)
hlines!(ax, [100.0]; color = ref_col, linewidth = 1.2, linestyle = :dash)

# Stock series lines
xlims!(ax, 1, n_days_plot + 25)
for (j, sym) in enumerate(symbols)
    sub = df[df[!, SYMBOL] .== sym, :]
    lines!(ax, sub[!, DAY], sub[!, PRICE];
        color     = IMPRINT_PALETTE[j],
        linewidth = 2.5,
        label     = sym,
    )
    # End-of-series value label (final rebased performance)
    final_val = sub[end, PRICE]
    text!(ax, n_days_plot + 3, final_val;
        text     = string(round(Int, final_val)),
        color    = IMPRINT_PALETTE[j],
        fontsize = 13,
        align    = (:left, :center),
    )
end

# Legend (right column, external to plot)
Legend(fig[1, 2], ax;
    labelcolor      = INK,
    framevisible    = false,
    backgroundcolor = ELEVATED_BG,
    labelsize       = 12,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
