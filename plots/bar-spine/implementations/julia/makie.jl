# anyplot.ai
# bar-spine: Spine Plot for Two-Variable Proportions
# Library: Makie.jl 0.12 | Julia 1.11
# Quality: pending | Created: 2026-09-02

using CairoMakie
using Colors

# --- Theme tokens -------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette — semantic exception applies: retained/churned is a
# good/bad pair the legend labels explicitly, so green/red replace the
# ordinal 1st/2nd slots (see default-style-guide.md "Semantic exception").
const RETAINED_COLOR = colorant"#009E73"  # good outcome — brand green
const CHURNED_COLOR  = colorant"#AE3030"  # bad outcome — matte red anchor

# --- Data -----------------------------------------------------------------
# Customer churn by subscription tier: bar width = tier size (marginal
# count), segment heights = conditional retained/churned proportions.
tiers            = ["Basic", "Standard", "Premium", "Enterprise"]
retained_counts  = [420, 650, 540, 310]
churned_counts   = [380, 250, 110, 40]
tier_totals      = retained_counts .+ churned_counts
retained_frac    = retained_counts ./ tier_totals

edges   = vcat(0, cumsum(tier_totals))
lefts   = edges[1:end-1]
rights  = edges[2:end]
centers = (lefts .+ rights) ./ 2

# --- Plot -------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "bar-spine · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Subscription Tier  (bar width ∝ customer count)",
    ylabel             = "Share of Customers",
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
    xticks             = (centers, tiers),
    yticks             = (0:0.25:1, ["0%", "25%", "50%", "75%", "100%"]),
)
xlims!(ax, 0, edges[end])
ylims!(ax, 0, 1)

for i in eachindex(tiers)
    left, right, split = lefts[i], rights[i], retained_frac[i]

    poly!(ax, Rect2f(left, 0, right - left, split);
          color = RETAINED_COLOR, strokecolor = PAGE_BG, strokewidth = 3)
    poly!(ax, Rect2f(left, split, right - left, 1 - split);
          color = CHURNED_COLOR, strokecolor = PAGE_BG, strokewidth = 3)

    text!(ax, (left + right) / 2, split / 2;
          text = "$(round(Int, split * 100))%", align = (:center, :center),
          color = :white, fontsize = 15)
    text!(ax, (left + right) / 2, split + (1 - split) / 2;
          text = "$(round(Int, (1 - split) * 100))%", align = (:center, :center),
          color = :white, fontsize = 15)
end

Legend(
    fig[1, 2],
    [PolyElement(color = RETAINED_COLOR), PolyElement(color = CHURNED_COLOR)],
    ["Retained", "Churned"];
    labelcolor = INK_SOFT,
    framevisible = false,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
