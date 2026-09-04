# anyplot.ai
# confusion-matrix: Confusion Matrix Heatmap
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-04

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# --- Data: bird species classifier confusion matrix -------------------------
# Rows = true species, columns = predicted species. Small songbirds
# (Sparrow, Finch, Robin) are visually similar and get confused with each
# other more often; raptors (Owl, Hawk) are visually distinct and are rarely
# confused with songbirds or with each other.
class_names = ["Sparrow", "Finch", "Robin", "Owl", "Hawk"]
n_classes = length(class_names)
sample_sizes = [180, 150, 165, 90, 95]
confusion_rates = [
    0.90 0.05 0.04 0.00 0.01
    0.06 0.87 0.06 0.00 0.01
    0.05 0.07 0.86 0.01 0.01
    0.00 0.01 0.01 0.93 0.05
    0.01 0.00 0.01 0.06 0.92
]

counts = zeros(Int, n_classes, n_classes)
for i in 1:n_classes
    counts[i, :] = round.(Int, sample_sizes[i] .* confusion_rates[i, :])
end
max_count = maximum(counts)

# --- Colormap: Imprint sequential (single-polarity count data) --------------
const IMPRINT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# --- Plot ---------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "confusion-matrix · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Predicted Label",
    ylabel             = "True Label",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticks             = (1:n_classes, class_names),
    yticks             = (1:n_classes, class_names),
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    aspect             = DataAspect(),
    yreversed          = true,
    leftspinecolor     = INK_SOFT,
    rightspinecolor    = INK_SOFT,
    topspinecolor      = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = false,
)

zmatrix = permutedims(counts)
hm = heatmap!(
    ax, 1:n_classes, 1:n_classes, zmatrix;
    colormap = IMPRINT_SEQ, colorrange = (0, max_count),
)

# Cell annotations (counts) — text color adapts to cell luminance so it
# stays legible across the full green-to-blue sequential range.
for i in 1:n_classes, j in 1:n_classes
    value = counts[i, j]
    t = max_count == 0 ? 0.0 : value / max_count
    cell_color = IMPRINT_SEQ[t]
    luminance = 0.2126 * red(cell_color) + 0.7152 * green(cell_color) + 0.0722 * blue(cell_color)
    text_color = luminance > 0.55 ? INK : colorant"#FFFFFF"
    text!(
        ax, j, i, text = string(value),
        align = (:center, :center), color = text_color, fontsize = 16,
    )
end

# Highlight the diagonal (correct predictions)
for i in 1:n_classes
    xs = [i - 0.5, i + 0.5, i + 0.5, i - 0.5, i - 0.5]
    ys = [i - 0.5, i - 0.5, i + 0.5, i + 0.5, i - 0.5]
    lines!(ax, xs, ys; color = INK, linewidth = 3)
end

Colorbar(
    fig[1, 2], hm;
    label = "Sample Count", labelsize = 14, labelcolor = INK,
    ticklabelsize = 12, ticklabelcolor = INK_SOFT, width = 25,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
