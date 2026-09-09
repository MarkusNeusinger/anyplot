# anyplot.ai
# shap-waterfall: SHAP Waterfall Plot for Feature Attribution
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-09

using CairoMakie
using Colors
using Printf

# --- Theme tokens -----------------------------------------------------------
THEME      = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG    = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK        = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT   = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette semantic anchors: matte red for positive push, blue for negative
POSITIVE_COLOR = colorant"#AE3030"
NEGATIVE_COLOR = colorant"#4467A3"

# --- Data ---------------------------------------------------------------
# Credit scoring model explaining a single loan applicant's predicted default
# probability. Features ranked by descending absolute SHAP magnitude.
features = [
    "Debt-to-Income Ratio",
    "Credit Utilization",
    "Recent Missed Payments",
    "Income Stability",
    "Credit History Length",
    "Age",
    "Number of Open Accounts",
    "Employment Length",
    "Loan-to-Value Ratio",
    "Number of Credit Inquiries",
]
shap_values = [7.2, 5.1, 4.3, -3.8, -3.1, -2.4, 1.8, -1.5, 1.2, 0.9]

base_value = 18.4
n = length(features)

ends = base_value .+ cumsum(shap_values)
starts = ends .- shap_values
final_value = ends[end]

# Position n (top) holds the largest-magnitude feature; position 1 (bottom)
# holds the smallest, matching the descending-magnitude ranking above.
positions = collect(n:-1:1)
bar_colors = [v >= 0 ? POSITIVE_COLOR : NEGATIVE_COLOR for v in shap_values]

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

lo = minimum(vcat(starts, ends, [base_value])) - 5.0
hi = maximum(vcat(starts, ends, [final_value])) + 5.0

ax = Axis(
    fig[1, 1];
    title              = "shap-waterfall · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Predicted Default Probability (%)",
    xlabelsize         = 14,
    xlabelcolor        = INK,
    xticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticks             = (1:n, reverse(features)),
    yticklabelsize     = 13,
    yticklabelcolor    = INK_SOFT,
    ylabel             = "Feature",
    ylabelsize         = 14,
    ylabelcolor        = INK,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = true,
    ygridvisible       = false,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

xlims!(ax, lo, hi)
ylims!(ax, 0.2, n + 1.3)

# Dotted connector lines between consecutive cumulative segments
for i in 1:(n - 1)
    lines!(
        ax,
        [ends[i], ends[i]],
        [positions[i], positions[i + 1]];
        color = INK_SOFT,
        linestyle = :dot,
        linewidth = 1.5,
    )
end

# Base value and final prediction reference lines, stopped below the label
# row (as plain lines! with an explicit y-extent) so the dashed lines never
# cross through their own annotation text above.
line_top = n + 0.4
lines!(ax, [base_value, base_value], [0.2, line_top]; color = INK_SOFT, linestyle = :dash, linewidth = 1.5)
lines!(ax, [final_value, final_value], [0.2, line_top]; color = INK, linestyle = :dash, linewidth = 1.5)
scatter!(ax, [base_value], [line_top]; marker = :utriangle, markersize = 10, color = INK_SOFT)
scatter!(ax, [final_value], [line_top]; marker = :utriangle, markersize = 10, color = INK)

text!(
    ax, base_value, n + 0.9;
    text = @sprintf("Base value: %.1f%%", base_value),
    color = INK_SOFT, fontsize = 13, align = (:center, :bottom),
)
text!(
    ax, final_value, n + 0.5;
    text = @sprintf("Prediction: %.1f%%", final_value),
    color = INK, fontsize = 13, align = (:center, :bottom), font = :bold,
)

# Waterfall bars (horizontal, floating from cumulative start to cumulative end)
barplot!(
    ax,
    positions,
    ends;
    fillto = starts,
    direction = :x,
    color = bar_colors,
    width = 0.62,
    strokewidth = 0,
)

# Numeric SHAP value labels beside each bar
for i in 1:n
    label = @sprintf("%+.1f", shap_values[i])
    x_offset = shap_values[i] >= 0 ? ends[i] + 0.5 : ends[i] - 0.5
    text_align = shap_values[i] >= 0 ? (:left, :center) : (:right, :center)
    text!(
        ax, x_offset, positions[i];
        text = label, color = INK, fontsize = 13, align = text_align,
    )
end

# Legend explaining bar color semantics
legend_elems = [PolyElement(color = POSITIVE_COLOR), PolyElement(color = NEGATIVE_COLOR)]
legend_labels = ["Increases prediction", "Decreases prediction"]
Legend(
    fig[2, 1], legend_elems, legend_labels;
    orientation = :horizontal, framevisible = false,
    labelcolor = INK, labelsize = 13, backgroundcolor = PAGE_BG,
)

rowsize!(fig.layout, 1, Relative(0.92))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
