# anyplot.ai
# lift-curve: Model Lift Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 70/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]

# --- Data --------------------------------------------------------------------
# Fraud detection: a small fraction of transactions are fraudulent, and a
# model score concentrates most fraud cases near the top of the ranking.
n_transactions = 5000
fraud_rate = 0.08

is_fraud = rand(n_transactions) .< fraud_rate
model_score = ifelse.(is_fraud, randn(n_transactions) .+ 2.8, randn(n_transactions))

ranking = sortperm(model_score; rev=true)
sorted_fraud = is_fraud[ranking]
cumulative_fraud = cumsum(sorted_fraud)

population_pct = (1:n_transactions) ./ n_transactions .* 100
baseline_rate = sum(is_fraud) / n_transactions
cumulative_rate = cumulative_fraud ./ (1:n_transactions)
lift = cumulative_rate ./ baseline_rate

decile_idx = round.(Int, (0.1:0.1:1.0) .* n_transactions)
decile_pct = population_pct[decile_idx]
decile_lift = lift[decile_idx]

# --- Plot ---------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "lift-curve · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Population Targeted (%)",
    ylabel             = "Cumulative Lift",
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
    limits             = (0, 100, 0, nothing),
)

band!(ax, population_pct, fill(1.0, n_transactions), lift; color=(BRAND, 0.18))
reference_line = hlines!(ax, [1.0]; color=INK_SOFT, linestyle=:dash, linewidth=2)
model_line = lines!(ax, population_pct, lift; color=BRAND, linewidth=3)
scatter!(ax, decile_pct, decile_lift; color=BRAND, markersize=16, strokewidth=1.5, strokecolor=PAGE_BG)

axislegend(
    ax,
    [model_line, reference_line],
    ["Fraud model", "Random selection (no lift)"];
    position = :rt,
    labelcolor = INK,
    backgroundcolor = PAGE_BG,
    framevisible = false,
)

# --- Callout annotation ------------------------------------------------------
# Large leader line + bold text deliberately placed in the open area to the
# right of the curve, turning otherwise-empty canvas into a focal point.
callout_lift = round(decile_lift[1], digits=1)
callout_pos = (42.0, 9.5)
arrows!(
    ax,
    [callout_pos[1] - 1], [callout_pos[2] - 0.6],
    [decile_pct[1] - callout_pos[1] + 1], [decile_lift[1] - callout_pos[2] + 0.6];
    color = INK_SOFT, linewidth = 2.5, arrowsize = 22,
)
text!(
    ax, callout_pos[1], callout_pos[2];
    text = "Top 10% → $(callout_lift)x lift",
    color = INK,
    fontsize = 22,
    font = :bold,
    align = (:left, :bottom),
)

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit=2)
