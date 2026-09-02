# anyplot.ai
# bar-feature-importance: Feature Importance Bar Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential colormap (brand green -> blue) for continuous importance
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# --- Data -----------------------------------------------------------------
# Feature importances from a random forest customer-churn model
feature_names = [
    "Contract Type", "Tenure (Months)", "Monthly Charges", "Tech Support",
    "Total Charges", "Internet Service", "Online Security", "Payment Method",
    "Paperless Billing", "Device Protection", "Streaming TV", "Multiple Lines",
    "Senior Citizen", "Partner",
]
n_features = length(feature_names)

raw_importance = [0.184, 0.151, 0.132, 0.098, 0.087, 0.071, 0.062, 0.051,
                   0.042, 0.036, 0.029, 0.022, 0.019, 0.016]
importance = raw_importance ./ sum(raw_importance)
std_dev = importance .* (0.12 .+ 0.10 .* rand(n_features))

# Sort ascending so the highest importance lands at the top of the chart
order = sortperm(importance)
feature_names = feature_names[order]
importance = importance[order]
std_dev = std_dev[order]
positions = 1:n_features

# --- Plot -------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "bar-feature-importance · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Relative Importance",
    xlabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickformat       = xs -> [string(round(Int, x * 100), "%") for x in xs],
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridvisible      = false,
    yticks            = (positions, feature_names),
)

barplot!(
    ax, positions, importance;
    direction   = :x,
    color       = importance,
    colormap    = ANYPLOT_SEQ,
    colorrange  = (minimum(importance), maximum(importance)),
    strokewidth = 0,
)

errorbars!(
    ax, importance, positions, std_dev;
    direction    = :x,
    color        = INK_SOFT,
    whiskerwidth = 8,
    linewidth    = 1.5,
)

text!(
    ax, importance .+ std_dev .+ 0.010, positions;
    text     = [string(round(v * 100, digits = 1), "%") for v in importance],
    align    = (:left, :center),
    color    = INK,
    fontsize = 12,
)

xlims!(ax, 0, maximum(importance .+ std_dev) * 1.2)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
