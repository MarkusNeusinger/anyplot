# anyplot.ai
# count-basic: Basic Count Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-08-11

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND    = colorant"#009E73"  # Imprint palette position 1 — ALWAYS first series

# --- Data ---------------------------------------------------------------
# Raw survey responses (one row per respondent) — a count plot tallies these
# directly, unlike a bar chart which needs pre-aggregated values.
device_pool = vcat(
    fill("Smartphone", 342),
    fill("Laptop", 268),
    fill("Tablet", 145),
    fill("Desktop", 98),
    fill("Smartwatch", 61),
    fill("E-reader", 24),
)
responses = shuffle(device_pool)

counts_by_category = Dict{String,Int}()
for r in responses
    counts_by_category[r] = get(counts_by_category, r, 0) + 1
end

categories = collect(keys(counts_by_category))
tallies = [counts_by_category[c] for c in categories]
order = sortperm(tallies; rev = true)
categories = categories[order]
tallies = tallies[order]

n = length(categories)
title_str = "count-basic · julia · makie · anyplot.ai"

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Primary Device Used for Survey",
    ylabel             = "Number of Respondents",
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticks             = (1:n, categories),
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
)

barplot!(ax, 1:n, tallies; color = BRAND, width = 0.65)

for (i, count) in enumerate(tallies)
    text!(ax, i, count; text = string(count), align = (:center, :bottom),
          offset = (0, 6), color = INK_SOFT, fontsize = 13)
end

ylims!(ax, 0, maximum(tallies) * 1.12)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
