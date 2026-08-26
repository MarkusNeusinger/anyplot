# anyplot.ai
# area-stacked-confidence: Stacked Area Chart with Confidence Bands
# Library: Makie.jl 0.12 | Julia 1.11
# Quality: pending | Created: 2026-08-26

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome") ---
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — first series is ALWAYS #009E73
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
]

# --- Data: quarterly revenue forecast by product line, 90% prediction interval ---
n_quarters = 24
quarters = collect(1:n_quarters)
product_lines = ["Core Platform", "Cloud Services", "Emerging Markets"]

base_revenue = [18.0, 9.0, 5.0]     # starting quarterly revenue ($M)
trend        = [0.55, 0.65, 0.35]   # quarterly growth ($M)
noise_scale  = [0.9, 0.8, 0.6]
pi_base      = [0.6, 0.7, 0.9]      # starting half-width of the 90% interval ($M)
pi_growth    = [0.22, 0.30, 0.42]   # interval widening rate with forecast horizon

revenue = Matrix{Float64}(undef, n_quarters, 3)
half_width = Matrix{Float64}(undef, n_quarters, 3)
for i in 1:3
    revenue[:, i] = base_revenue[i] .+ trend[i] .* (quarters .- 1) .+
                    noise_scale[i] .* randn(n_quarters)
    half_width[:, i] = pi_base[i] .+ pi_growth[i] .* sqrt.(quarters .- 1)
end

cum_top = cumsum(revenue, dims = 2)
cum_baseline = hcat(zeros(n_quarters), cum_top[:, 1:2])
band_lower = cum_top .- half_width
band_upper = cum_top .+ half_width

quarter_labels = ["Q$(mod1(q, 4))'$(24 + div(q - 1, 4))" for q in quarters]
tick_idx = 1:4:n_quarters

# --- Plot ---------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "area-stacked-confidence · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Fiscal Quarter",
    ylabel            = "Revenue (\$M, cumulative)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    xticks             = (quarters[tick_idx], quarter_labels[tick_idx]),
    xticklabelrotation = 0.35,
)

# Stacked areas drawn first (opaque), then confidence bands overlaid
# (semi-transparent so overlap with the next layer stays legible), then
# boundary lines on top.
for i in 1:3
    band!(ax, quarters, cum_baseline[:, i], cum_top[:, i];
          color = (IMPRINT_PALETTE[i], 0.85))
end
for i in 1:3
    band!(ax, quarters, band_lower[:, i], band_upper[:, i];
          color = (IMPRINT_PALETTE[i], 0.28))
end
for i in 1:3
    lines!(ax, quarters, cum_top[:, i]; color = IMPRINT_PALETTE[i], linewidth = 2.5)
end

legend_elements = vcat(
    [PolyElement(color = (IMPRINT_PALETTE[i], 0.85)) for i in 1:3],
    [PolyElement(color = (INK_SOFT, 0.28))],
)
legend_labels = vcat(product_lines, ["90% prediction interval"])
Legend(
    fig[1, 2], legend_elements, legend_labels;
    framevisible    = false,
    labelcolor      = INK,
    backgroundcolor = PAGE_BG,
)
colsize!(fig.layout, 1, Relative(0.8))

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
