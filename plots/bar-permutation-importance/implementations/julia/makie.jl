# anyplot.ai
# bar-permutation-importance: Permutation Feature Importance Plot
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-08-26

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential colormap — single-polarity continuous data
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# --- Data: permutation importance for a churn-prediction gradient-boosting model
features = [
    "monthly_charges", "tenure_months", "contract_type", "total_charges",
    "num_support_tickets", "internet_service", "payment_method",
    "avg_data_usage_gb", "customer_age", "paperless_billing",
    "has_multiple_lines", "senior_citizen", "partner_status", "dependents_count",
]
importance_mean = [
    0.182, 0.146, 0.098, 0.081, 0.063, 0.047, 0.038,
    0.029, 0.021, 0.014, 0.009, 0.005, 0.002, -0.004,
]
importance_std = 0.10 .* abs.(importance_mean) .+ 0.004 .* rand(length(features))

n = length(features)
y_positions = collect(n:-1:1)  # highest importance at the top

# --- Plot ---------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "bar-permutation-importance · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Decrease in Accuracy When Feature Is Shuffled",
    xlabelsize         = 14,
    xlabelcolor        = INK,
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
    ygridvisible       = false,
    yticks             = (1:n, reverse(features)),
)

vlines!(ax, 0; color = INK_SOFT, linewidth = 1.5, linestyle = :dash)

barplot!(
    ax, y_positions, importance_mean;
    direction = :x,
    color = importance_mean,
    colormap = ANYPLOT_SEQ,
    colorrange = (minimum(importance_mean), maximum(importance_mean)),
    strokewidth = 0,
)

errorbars!(
    ax, importance_mean, y_positions, importance_std;
    direction = :x,
    color = INK_SOFT,
    whiskerwidth = 8,
    linewidth = 1.5,
)

Colorbar(
    fig[1, 2];
    limits = (minimum(importance_mean), maximum(importance_mean)),
    colormap = ANYPLOT_SEQ,
    label = "Importance",
    labelcolor = INK,
    labelsize = 12,
    ticklabelsize = 11,
    ticklabelcolor = INK_SOFT,
    tickcolor = INK_SOFT,
)
colsize!(fig.layout, 2, Relative(0.03))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
