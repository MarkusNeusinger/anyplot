# anyplot.ai
# scatter-categorical: Categorical Scatter Plot
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens ------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------------
# Soil nutrient survey across three land-use types: fertilized cropland runs
# nitrogen-rich, grassland sits in between, and undisturbed forest soil is
# nutrient-poor but more variable plot to plot.
land_uses   = ["Cropland", "Grassland", "Forest"]
n_means     = [45.0, 26.0, 12.0]
n_sds       = [6.0, 5.0, 4.5]
p_means     = [31.0, 19.0, 8.0]
p_sds       = [4.5, 4.0, 3.5]
n_samples   = 60
markers     = [:circle, :utriangle, :diamond]

nitrogen   = Float64[]
phosphorus = Float64[]
group_idx  = Int[]

for i in eachindex(land_uses)
    append!(nitrogen, n_means[i] .+ n_sds[i] .* randn(n_samples))
    append!(phosphorus, p_means[i] .+ p_sds[i] .* randn(n_samples) .+ 0.3 .* (nitrogen[end-n_samples+1:end] .- n_means[i]))
    append!(group_idx, fill(i, n_samples))
end

title_str = "scatter-categorical · julia · makie · anyplot.ai"

# --- Plot ----------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Soil Nitrogen (mg/kg)",
    ylabel            = "Soil Phosphorus (mg/kg)",
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
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible = false,
    yminorgridvisible = false,
)

for i in eachindex(land_uses)
    mask = group_idx .== i
    scatter!(ax, nitrogen[mask], phosphorus[mask];
             color = IMPRINT_PALETTE[i], marker = markers[i],
             markersize = 16, strokewidth = 1, strokecolor = PAGE_BG,
             label = land_uses[i])
end

axislegend(ax, position = :rb, labelcolor = INK, framevisible = false, labelsize = 13)

# --- Save -----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
