# anyplot.ai
# facet-grid: Faceted Grid Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens ------------------------------------------------------------
const THEME      = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG    = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK        = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT   = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND      = colorant"#009E73"

# --- Data ----------------------------------------------------------------
# Synthetic penguin bill measurements, faceted by species (columns) and sex
# (rows) — mirrors real Palmer Penguins sexual-dimorphism patterns.
const SPECIES = ["Adelie", "Chinstrap", "Gentoo"]
const SEXES = ["Female", "Male"]
const N_PER_FACET = 150

const LENGTH_MEAN = Dict("Adelie" => 38.8, "Chinstrap" => 48.8, "Gentoo" => 47.5)
const LENGTH_SD = Dict("Adelie" => 2.7, "Chinstrap" => 3.3, "Gentoo" => 3.1)
const DEPTH_MEAN = Dict("Adelie" => 18.3, "Chinstrap" => 18.4, "Gentoo" => 15.0)
const DEPTH_SD = Dict("Adelie" => 1.2, "Chinstrap" => 1.1, "Gentoo" => 1.0)
const LENGTH_SEX_OFFSET = 4.0  # males have longer bills on average
const DEPTH_SEX_OFFSET = 1.0   # males have deeper bills on average

bill_length = Dict{Tuple{String,String},Vector{Float64}}()
bill_depth = Dict{Tuple{String,String},Vector{Float64}}()

for species in SPECIES, sex in SEXES
    sign = sex == "Male" ? 1 : -1
    bill_length[(species, sex)] =
        LENGTH_MEAN[species] .+ sign * LENGTH_SEX_OFFSET / 2 .+
        randn(N_PER_FACET) .* LENGTH_SD[species]
    bill_depth[(species, sex)] =
        DEPTH_MEAN[species] .+ sign * DEPTH_SEX_OFFSET / 2 .+
        randn(N_PER_FACET) .* DEPTH_SD[species]
end

# --- Plot ------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

n_cols = length(SPECIES)
n_rows = length(SEXES)
title_row = 1
strip_row = 2
first_ax_row = 3
xlabel_row = first_ax_row + n_rows
strip_col = n_cols + 1
ylabel_col = 0

Label(
    fig[title_row, 1:n_cols],
    "facet-grid · julia · makie · anyplot.ai";
    fontsize = 20, color = INK, tellwidth = false,
)

# Column strips — species
for (j, species) in enumerate(SPECIES)
    Box(fig[strip_row, j]; color = ELEVATED_BG, strokewidth = 0)
    Label(fig[strip_row, j], species; fontsize = 15, color = INK, tellwidth = false)
end

axes = Matrix{Axis}(undef, n_rows, n_cols)

for (i, sex) in enumerate(SEXES)
    row = first_ax_row + i - 1

    # Row strip — sex
    Box(fig[row, strip_col]; color = ELEVATED_BG, strokewidth = 0)
    Label(
        fig[row, strip_col], sex;
        fontsize = 15, color = INK, rotation = -pi / 2, tellheight = false,
    )

    for (j, species) in enumerate(SPECIES)
        ax = Axis(
            fig[row, j];
            backgroundcolor  = PAGE_BG,
            xticklabelsize   = 12,
            yticklabelsize   = 12,
            xticklabelcolor  = INK_SOFT,
            yticklabelcolor  = INK_SOFT,
            xtickcolor       = INK_SOFT,
            ytickcolor       = INK_SOFT,
            leftspinecolor   = INK_SOFT,
            bottomspinecolor = INK_SOFT,
            topspinecolor    = INK_SOFT,
            rightspinecolor  = INK_SOFT,
            xgridcolor       = RGBAf(INK.r, INK.g, INK.b, 0.12),
            ygridcolor       = RGBAf(INK.r, INK.g, INK.b, 0.12),
            xminorgridvisible = false,
            yminorgridvisible = false,
        )
        scatter!(
            ax, bill_length[(species, sex)], bill_depth[(species, sex)];
            color = BRAND, markersize = 8, alpha = 0.6, strokewidth = 0,
        )

        j != 1 && hideydecorations!(ax; grid = false)
        i != n_rows && hidexdecorations!(ax; grid = false)

        axes[i, j] = ax
    end
end

linkxaxes!(axes...)
linkyaxes!(axes...)

Label(
    fig[xlabel_row, 1:n_cols], "Bill Length (mm)";
    fontsize = 14, color = INK, tellwidth = false,
)
Label(
    fig[first_ax_row:(first_ax_row + n_rows - 1), ylabel_col], "Bill Depth (mm)";
    fontsize = 14, color = INK, rotation = pi / 2, tellheight = false,
)

rowsize!(fig.layout, title_row, Relative(0.09))
rowsize!(fig.layout, strip_row, Relative(0.06))
rowsize!(fig.layout, xlabel_row, Relative(0.06))
colsize!(fig.layout, strip_col, Relative(0.05))
colsize!(fig.layout, ylabel_col, Relative(0.05))
colgap!(fig.layout, 8)
rowgap!(fig.layout, 8)

# --- Save --------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
