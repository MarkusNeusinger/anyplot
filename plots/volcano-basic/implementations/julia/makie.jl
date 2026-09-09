# anyplot.ai
# volcano-basic: Volcano Plot for Statistical Significance
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 91/100 | Created: 2026-09-09

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const MUTED       = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Volcano plots follow a domain-standard convention (Imprint semantic
# exception): non-significant -> muted, up-regulated -> matte red,
# down-regulated -> blue.
const COLOR_NONSIG = MUTED
const COLOR_UP     = colorant"#AE3030"
const COLOR_DOWN   = colorant"#4467A3"

# --- Data: simulated differential gene expression (RNA-seq) -------------
n_genes = 2200
gene_names = "Gene" .* string.(1:n_genes)
log2_fold_change = randn(n_genes) .* 1.3
# Independent additive noise dominates over the fold-change-linked term so the
# cloud scatters realistically around the thresholds instead of forming a
# clean deterministic "V" (borderline points land on either side by chance,
# as in real differential-expression data).
neg_log10_pvalue = abs.(log2_fold_change .* (1.1 .+ 0.55 .* randn(n_genes))) .+
                    abs.(randn(n_genes) .* 1.3)

fc_threshold = 1.0
p_threshold = -log10(0.05)

is_up = (log2_fold_change .>= fc_threshold) .& (neg_log10_pvalue .>= p_threshold)
is_down = (log2_fold_change .<= -fc_threshold) .& (neg_log10_pvalue .>= p_threshold)
is_nonsig = .!(is_up .| is_down)

# --- Plot -----------------------------------------------------------------
fig = Figure(resolution = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title = "volcano-basic · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    xlabel = "log2(Fold Change)",
    ylabel = "-log10(p-value)",
    xlabelsize = 14,
    ylabelsize = 14,
    xlabelcolor = INK,
    ylabelcolor = INK,
    xticklabelsize = 12,
    yticklabelsize = 12,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinecolor = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    xgridcolor = RGBAf(INK.r, INK.g, INK.b, 0.12),
    ygridcolor = RGBAf(INK.r, INK.g, INK.b, 0.12),
    xminorgridvisible = false,
    yminorgridvisible = false,
)

scatter!(ax, log2_fold_change[is_nonsig], neg_log10_pvalue[is_nonsig];
    color = (COLOR_NONSIG, 0.45), markersize = 7, strokewidth = 0,
    label = "Non-significant")
scatter!(ax, log2_fold_change[is_down], neg_log10_pvalue[is_down];
    color = (COLOR_DOWN, 0.75), markersize = 8, strokewidth = 0,
    label = "Down-regulated")
scatter!(ax, log2_fold_change[is_up], neg_log10_pvalue[is_up];
    color = (COLOR_UP, 0.75), markersize = 8, strokewidth = 0,
    label = "Up-regulated")

hlines!(ax, [p_threshold]; color = INK_SOFT, linestyle = :dash, linewidth = 1.5)
vlines!(ax, [-fc_threshold, fc_threshold]; color = INK_SOFT, linestyle = :dash,
    linewidth = 1.5)

# Label the top few most-significant up/down genes by name, per the spec's
# optional annotation suggestion — a distinctive use of Makie's text! recipe.
n_label = 3
top_up = findall(is_up)[sortperm(neg_log10_pvalue[is_up]; rev = true)[1:min(n_label, count(is_up))]]
top_down = findall(is_down)[sortperm(neg_log10_pvalue[is_down]; rev = true)[1:min(n_label, count(is_down))]]

for i in top_up
    text!(ax, log2_fold_change[i] + 0.08, neg_log10_pvalue[i];
        text = gene_names[i], color = INK, fontsize = 11, align = (:left, :center))
end
for i in top_down
    text!(ax, log2_fold_change[i] - 0.08, neg_log10_pvalue[i];
        text = gene_names[i], color = INK, fontsize = 11, align = (:right, :center))
end

axislegend(ax; position = :rt, backgroundcolor = ELEVATED_BG,
    framecolor = INK_SOFT, labelcolor = INK)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
