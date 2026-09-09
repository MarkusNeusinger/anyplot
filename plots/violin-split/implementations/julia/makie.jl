# anyplot.ai
# violin-split: Split Violin Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-09

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — theme-independent, first series always brand green
IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data ---------------------------------------------------------------
# Crop yields under two irrigation regimes, compared across four crop types.
crops = ["Wheat", "Corn", "Soybean", "Rice"]
n_per_group = 220

irrigated_mean = [4.3, 6.1, 3.2, 6.6]
irrigated_std = [0.55, 0.75, 0.45, 0.85]
rainfed_mean = [2.7, 4.0, 2.2, 3.9]
rainfed_std = [0.70, 0.90, 0.55, 1.00]

x_irrigated = Int[]
y_irrigated = Float64[]
x_rainfed = Int[]
y_rainfed = Float64[]

for i in 1:length(crops)
    append!(x_irrigated, fill(i, n_per_group))
    append!(y_irrigated, irrigated_mean[i] .+ irrigated_std[i] .* randn(n_per_group))
    append!(x_rainfed, fill(i, n_per_group))
    append!(y_rainfed, rainfed_mean[i] .+ rainfed_std[i] .* randn(n_per_group))
end

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "violin-split · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Crop",
    ylabel            = "Yield (tons per hectare)",
    xlabelsize        = 16,
    ylabelsize        = 16,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 14,
    yticklabelsize    = 14,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xticks             = (1:length(crops), crops),
)

violin!(
    ax, x_irrigated, y_irrigated;
    side = :left,
    color = (IMPRINT_PALETTE[1], 0.85),
    strokewidth = 1.5,
    strokecolor = IMPRINT_PALETTE[1],
    width = 0.85,
    show_median = true,
    mediancolor = INK,
)

violin!(
    ax, x_rainfed, y_rainfed;
    side = :right,
    color = (IMPRINT_PALETTE[2], 0.85),
    strokewidth = 1.5,
    strokecolor = IMPRINT_PALETTE[2],
    width = 0.85,
    show_median = true,
    mediancolor = INK,
)

legend_elements = [
    PolyElement(color = (IMPRINT_PALETTE[1], 0.85), strokecolor = IMPRINT_PALETTE[1], strokewidth = 1.5),
    PolyElement(color = (IMPRINT_PALETTE[2], 0.85), strokecolor = IMPRINT_PALETTE[2], strokewidth = 1.5),
]
Legend(
    fig[1, 1], legend_elements, ["Irrigated", "Rain-fed"];
    tellwidth = false, tellheight = false,
    halign = :left, valign = :top,
    framevisible = false, labelcolor = INK, labelsize = 14,
    margin = (20, 20, 20, 20),
)

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
