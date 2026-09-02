# anyplot.ai
# cat-box-strip: Box Plot with Strip Overlay
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-02

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
# Reaction time (ms) across four caffeine-dose groups in a lab experiment
groups = ["Placebo", "50mg", "100mg", "200mg"]
group_means = [420.0, 390.0, 355.0, 345.0]
group_sds = [55.0, 48.0, 42.0, 50.0]
group_sizes = [90, 90, 90, 90]

category = String[]
value = Float64[]
group_index = Int[]
for (i, (g, mu, sigma, n)) in enumerate(zip(groups, group_means, group_sds, group_sizes))
    append!(category, fill(g, n))
    append!(value, mu .+ sigma .* randn(n))
    append!(group_index, fill(i, n))
end

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "cat-box-strip · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Caffeine Dose",
    ylabel             = "Reaction Time (ms)",
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
    xticks             = (1:length(groups), groups),
    backgroundcolor    = PAGE_BG,
    topspinevisible     = false,
    rightspinevisible   = false,
    leftspinecolor      = INK_SOFT,
    bottomspinecolor    = INK_SOFT,
    xgridvisible        = false,
    ygridcolor          = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

box_colors = [RGBAf(c.r, c.g, c.b, 0.35) for c in IMPRINT_PALETTE[1:length(groups)]]

boxplot!(
    ax, group_index, value;
    color = box_colors[group_index],
    strokecolor = IMPRINT_PALETTE[1:length(groups)],
    strokewidth = 1.5,
    width = 0.55,
    show_outliers = false,
    whiskerwidth = 0.4,
    gap = 0.0,
)

jitter = (rand(length(value)) .- 0.5) .* 0.28
scatter!(
    ax, group_index .+ jitter, value;
    color = IMPRINT_PALETTE[1:length(groups)][group_index],
    markersize = 7,
    strokewidth = 0,
    alpha = 0.45,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
