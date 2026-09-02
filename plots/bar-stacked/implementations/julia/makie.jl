# anyplot.ai
# bar-stacked: Stacked Bar Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-09-02

using CairoMakie
using Colors

# --- Theme tokens ------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — 8 hues, theme-independent, hybrid-v3 sort
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (ALWAYS first series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
]

# --- Data ---------------------------------------------------------------------
# Monthly grid-generation mix (GWh): fossil sources receding, renewables rising.
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
n_months = length(months)

solar       = [6.0, 8.0, 10.0, 12.0, 15.0, 17.0, 19.0, 20.0]
wind        = [10.0, 11.0, 13.0, 15.0, 17.0, 19.0, 21.0, 22.0]
natural_gas = [30.0, 29.0, 28.0, 28.0, 27.0, 27.0, 26.0, 26.0]
coal        = [42.0, 38.0, 34.0, 30.0, 28.0, 26.0, 25.0, 24.0]
totals = coal .+ natural_gas .+ wind .+ solar

# Legend/color order (canonical Imprint 1→4): solar, wind, natural gas, coal.
solar_color, wind_color, gas_color, coal_color = IMPRINT_PALETTE

# Visual stack order (bottom → top): coal, natural gas, wind, solar — legacy
# baseload at the bottom, emerging renewables on top.
x_idx  = repeat(1:n_months, outer = 4)
stack  = vcat(fill(1, n_months), fill(2, n_months), fill(3, n_months), fill(4, n_months))
values = vcat(coal, natural_gas, wind, solar)
colors = vcat(
    fill(coal_color, n_months),
    fill(gas_color, n_months),
    fill(wind_color, n_months),
    fill(solar_color, n_months),
)

# --- Plot ----------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "bar-stacked · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Month",
    ylabel             = "Electricity Generation (GWh)",
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
)
ax.xticks = (1:n_months, months)

barplot!(
    ax, x_idx, values;
    stack = stack, color = colors, width = 0.72,
    strokewidth = 1.25, strokecolor = PAGE_BG,
)

text!(
    ax, 1:n_months, totals;
    text  = [string(round(Int, t)) for t in totals],
    align = (:center, :bottom),
    offset = (0, 6),
    color = INK,
    fontsize = 14,
    font = :bold,
    strokewidth = 0.75,
    strokecolor = PAGE_BG,
)

ylims!(ax, 0, maximum(totals) * 1.18)

elements = [PolyElement(color = c) for c in IMPRINT_PALETTE]
Legend(
    fig[1, 2], elements, ["Solar", "Wind", "Natural Gas", "Coal"], "Energy Source";
    framevisible = false,
    labelcolor   = INK,
    labelsize    = 13,
    titlecolor   = INK,
    titlesize    = 14,
    titlefont    = :bold,
    titlehalign  = :left,
)

# --- Save -----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
