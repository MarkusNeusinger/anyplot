# anyplot.ai
# scatter-annotated: Annotated Scatter Plot with Text Labels
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random
using Statistics

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND    = colorant"#009E73"  # Imprint palette position 1 — always first series

# --- Data -----------------------------------------------------------------
company_names = [
    "NovaSys", "ByteForge", "QuantumLeap", "DataWeave", "CloudPeak", "SwiftAI",
    "NeuralArc", "EdgeStack", "VectorFlow", "PixelCraft", "StreamLine", "CoreLogic",
    "BrightPath", "ZenithTech", "ApexData", "TrueNorth", "SilverBit", "GreenSpark",
    "BluePeak", "RedShift", "OrbitLabs", "FusionWorks", "PrimeCode", "NextWave",
]
n = length(company_names)

rd_spend = round.(exp.(randn(n) .* 0.5 .+ 2.5); digits=1)                 # R&D spend ($M)
revenue_growth = round.(0.9 .* rd_spend .+ randn(n) .* 6 .+ 5; digits=1)  # Revenue growth (%)

# Highlight a handful of notable points instead of labeling all 24: the
# biggest / leanest spenders, the top / bottom growers, and the two
# companies whose growth deviates most from the spend-growth trend.
trend_residual = revenue_growth .- 0.9 .* rd_spend
labeled_idx = unique([
    argmax(revenue_growth), argmin(revenue_growth),
    argmax(rd_spend), argmin(rd_spend),
    argmax(trend_residual), argmin(trend_residual),
])

cx, cy = mean(rd_spend), mean(revenue_growth)
x_range = maximum(rd_spend) - minimum(rd_spend)
y_range = maximum(revenue_growth) - minimum(revenue_growth)

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "scatter-annotated · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "R&D Spend (\$M)",
    ylabel            = "Revenue Growth (%)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

scatter!(ax, rd_spend, revenue_growth;
    color = BRAND, alpha = 0.7, markersize = 16, strokewidth = 1, strokecolor = PAGE_BG)

# Push each label away from the data centroid so it lands in open space,
# with a thin connector line back to its point.
for i in labeled_idx
    dx = (rd_spend[i] >= cx ? 1 : -1) * 0.08 * x_range
    dy = (revenue_growth[i] >= cy ? 1 : -1) * 0.11 * y_range
    lx, ly = rd_spend[i] + dx, revenue_growth[i] + dy
    halign = dx >= 0 ? :left : :right
    valign = dy >= 0 ? :bottom : :top

    lines!(ax, [rd_spend[i], lx], [revenue_growth[i], ly];
        color = INK_SOFT, linewidth = 1, alpha = 0.6)
    text!(ax, lx, ly; text = company_names[i], align = (halign, valign),
        fontsize = 13, color = INK_SOFT)
end

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
