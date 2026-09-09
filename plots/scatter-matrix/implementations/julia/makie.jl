# anyplot.ai
# scatter-matrix: Scatter Plot Matrix
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-09

using CairoMakie
using Colors
using RDatasets
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
THEME       = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
GRID_COLOR  = RGBAf(INK.r, INK.g, INK.b, 0.15)

IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -----------------------------------------------------------------
iris = dataset("datasets", "iris")

variables = [:SepalLength, :SepalWidth, :PetalLength, :PetalWidth]
var_labels = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
n_vars = length(variables)

species_names = unique(iris.Species)
species_colors = Dict(sp => IMPRINT_PALETTE[i] for (i, sp) in enumerate(species_names))
point_colors = [species_colors[sp] for sp in iris.Species]

# --- Plot -------------------------------------------------------------------
title_str = "scatter-matrix · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

Label(fig[1, 1:(n_vars + 1)], title_str; fontsize = 20, color = INK, font = :bold)

for row in 1:n_vars, col in 1:n_vars
    is_diag = row == col
    show_y  = col == 1 && !is_diag
    show_x  = row == n_vars

    ax = Axis(
        fig[row + 1, col];
        backgroundcolor  = PAGE_BG,
        xlabel           = var_labels[col],
        ylabel           = var_labels[row],
        xlabelsize       = 13,
        ylabelsize       = 13,
        xlabelcolor      = INK,
        ylabelcolor      = INK,
        xlabelvisible    = show_x,
        ylabelvisible    = show_y,
        xticklabelsize   = 9,
        yticklabelsize   = 9,
        xticklabelcolor  = INK_SOFT,
        yticklabelcolor  = INK_SOFT,
        xticklabelsvisible = show_x,
        yticklabelsvisible  = show_y,
        xticksvisible    = show_x,
        yticksvisible    = show_y,
        xtickcolor       = INK_SOFT,
        ytickcolor       = INK_SOFT,
        leftspinecolor   = INK_SOFT,
        bottomspinecolor = INK_SOFT,
        topspinevisible    = false,
        rightspinevisible  = false,
        xgridcolor         = GRID_COLOR,
        ygridcolor         = GRID_COLOR,
        xminorgridvisible  = false,
        yminorgridvisible  = false,
    )

    if is_diag
        ax.yticklabelsvisible = false
        ax.ylabelvisible      = false
        ax.yticksvisible      = false
        for sp in species_names
            vals = iris[iris.Species .== sp, variables[row]]
            density!(
                ax, vals;
                color       = (species_colors[sp], 0.35),
                strokecolor = species_colors[sp],
                strokewidth = 2,
            )
        end
    else
        scatter!(
            ax, iris[!, variables[col]], iris[!, variables[row]];
            color       = point_colors,
            alpha       = 0.6,
            markersize  = 7,
            strokewidth = 0,
        )
    end
end

legend_elements = [MarkerElement(color = species_colors[sp], marker = :circle, markersize = 14) for sp in species_names]
Legend(
    fig[2:(n_vars + 1), n_vars + 1],
    legend_elements, string.(species_names), "Species";
    labelcolor      = INK,
    titlecolor      = INK,
    backgroundcolor = ELEVATED_BG,
    framevisible    = false,
)

colgap!(fig.layout, 8)
rowgap!(fig.layout, 8)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
