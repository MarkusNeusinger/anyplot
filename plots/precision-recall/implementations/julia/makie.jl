# anyplot.ai
# precision-recall: Precision-Recall Curve
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-09-05

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

# --- Data ---------------------------------------------------------------
# Fraud-detection scenario: rare positive class (fraudulent transactions)
# scored by a classifier's predicted probability.
n_transactions = 2000
positive_rate = 0.06
is_fraud = Int.(rand(n_transactions) .< positive_rate)

# Simulated classifier scores: fraud cases carry a stronger latent signal,
# on top of noise that creates realistic overlap with legitimate cases.
latent_signal = 2.6 .* is_fraud .+ 1.2 .* randn(n_transactions)
risk_score = 1 ./ (1 .+ exp.(-latent_signal))

# --- Precision / recall at every threshold (descending score order) --------
order = sortperm(risk_score; rev = true)
sorted_labels = is_fraud[order]

n_positives = sum(is_fraud)
true_positives = cumsum(sorted_labels)
predicted_positives = collect(1:n_transactions)

precision = true_positives ./ predicted_positives
recall = true_positives ./ n_positives

# Prepend the (recall=0, precision=1) anchor point (standard PR-curve convention)
recall_curve = vcat(0.0, recall)
precision_curve = vcat(1.0, precision)

average_precision = sum(
    (recall_curve[i] - recall_curve[i - 1]) * precision_curve[i]
    for i in 2:length(recall_curve)
)
baseline = n_positives / n_transactions

# --- Plot ---------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "precision-recall · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Recall",
    ylabel             = "Precision",
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
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)
xlims!(ax, -0.02, 1.02)
ylims!(ax, 0.0, 1.05)

stairs!(
    ax, recall_curve, precision_curve;
    step = :post,
    color = IMPRINT_PALETTE[1],
    linewidth = 3.0,
    label = "Precision-recall (AP = $(round(average_precision, digits = 2)))",
)
hlines!(
    ax, [baseline];
    color = INK_SOFT,
    linestyle = :dash,
    linewidth = 2.0,
    label = "Baseline (fraud rate = $(round(100 * baseline, digits = 1))%)",
)

Legend(
    fig[1, 2], ax;
    backgroundcolor = PAGE_BG,
    labelcolor = INK,
    framevisible = false,
)

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
