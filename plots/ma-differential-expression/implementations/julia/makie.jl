# anyplot.ai
# ma-differential-expression: MA Plot for Differential Expression
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-06-21

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint palette positions used in this plot
const BRAND_GREEN = colorant"#009E73"  # position 1 — up-regulated (gain)
const MATTE_RED   = colorant"#AE3030"  # semantic anchor — down-regulated (loss)
const OCHRE       = colorant"#BD8233"  # position 4 — LOESS trend line

# Data — simulated RNA-seq differential expression (~15 000 genes)
n_genes = 15_000

# A-values: mean log2 expression (funnel-shaped distribution typical of RNA-seq)
mean_expr = abs.(randn(n_genes)) .* 3.5 .+ abs.(randn(n_genes)) .* 1.0
mean_expr = clamp.(mean_expr, 0.05, 14.5)

# M-values: LFC variance shrinks at higher expression
lfc_noise = (2.0 ./ (mean_expr .+ 0.8)) .+ 0.18
lfc = randn(n_genes) .* lfc_noise

# Slight upward bias at low expression — common normalization artifact
lfc .+= 0.25 .* exp.(-mean_expr ./ 3.5)

# Inject ~10 % truly differentially expressed genes
n_de    = 1_500
de_idx  = randperm(n_genes)[1:n_de]
half_de = div(n_de, 2)
for i in 1:half_de
    lfc[de_idx[i]] += 1.9 + abs(randn()) * 0.6
end
for i in (half_de + 1):n_de
    lfc[de_idx[i]] -= 1.9 + abs(randn()) * 0.6
end
lfc = clamp.(lfc, -7.5, 7.5)

significant = falses(n_genes)
significant[de_idx] .= true

not_sig  = .!significant
sig_up   = significant .& (lfc .>  0.0)
sig_down = significant .& (lfc .<= 0.0)

# Gaussian kernel smoothing — LOESS approximation (inline, no function)
n_eval   = 120
bw       = 1.5
x_eval   = collect(range(minimum(mean_expr), maximum(mean_expr), length=n_eval))
y_smooth = zeros(n_eval)
for i in eachindex(x_eval)
    w       = exp.(-((mean_expr .- x_eval[i]) ./ bw) .^ 2)
    wsum    = sum(w)
    y_smooth[i] = wsum > 1e-10 ? sum(w .* lfc) / wsum : 0.0
end

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "ma-differential-expression · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Mean log₂ Expression",
    ylabel             = "log₂ Fold Change",
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
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.10),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.10),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

# Layer 1: non-significant genes (large cloud, semi-transparent)
scatter!(ax, mean_expr[not_sig], lfc[not_sig];
    color       = (INK_MUTED, 0.18),
    markersize  = 4,
    strokewidth = 0,
)

# Layer 2: significantly up-regulated genes (brand green — gain)
scatter!(ax, mean_expr[sig_up], lfc[sig_up];
    color       = (BRAND_GREEN, 0.65),
    markersize  = 7,
    strokewidth = 0,
)

# Layer 3: significantly down-regulated genes (matte red — loss)
scatter!(ax, mean_expr[sig_down], lfc[sig_down];
    color       = (MATTE_RED, 0.65),
    markersize  = 7,
    strokewidth = 0,
)

# Reference lines: zero line and ±1 log2 FC thresholds
hlines!(ax, [0.0]; color = INK_SOFT, linewidth = 1.5)
hlines!(ax, [1.0, -1.0]; color = INK_SOFT, linewidth = 0.9, linestyle = :dash)

# LOESS-like smoothing curve
lines!(ax, x_eval, y_smooth; color = OCHRE, linewidth = 3.0)

# Legend
Legend(
    fig[1, 2],
    [
        MarkerElement(
            color = RGBAf(INK_MUTED.r, INK_MUTED.g, INK_MUTED.b, 0.55),
            marker = :circle, markersize = 14,
        ),
        MarkerElement(color = BRAND_GREEN, marker = :circle, markersize = 14),
        MarkerElement(color = MATTE_RED,   marker = :circle, markersize = 14),
        LineElement(color = OCHRE, linewidth = 2.5),
    ],
    [
        "Not significant",
        "Up-regulated (adj. p < 0.05)",
        "Down-regulated (adj. p < 0.05)",
        "LOESS trend",
    ],
    framevisible    = true,
    framecolor      = INK_SOFT,
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK,
    labelsize       = 12,
)

colsize!(fig.layout, 1, Relative(0.78))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
