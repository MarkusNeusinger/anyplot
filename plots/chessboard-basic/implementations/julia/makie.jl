# anyplot.ai
# chessboard-basic: Chess Board Grid Visualization
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-01

using CairoMakie
using Colors

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Board squares pair the Imprint brand green (dark square) with a
# theme-adaptive off-white (light square) — a classic tournament-set
# green/cream contrast built from Imprint tokens.
const LIGHT_SQUARE = THEME == "light" ? colorant"#FAF8F1" : colorant"#F0EFE8"
const DARK_SQUARE  = colorant"#009E73"

# --- Data ---------------------------------------------------------------
# Standard chess board: a1 is dark, light squares at h1 and a8.
# (file index + rank index) even -> dark square; odd -> light square.
files = 'a':'h'
ranks = 1:8
board = [(f + r) % 2 == 0 ? 0 : 1 for f in 0:7, r in 0:7]

# --- Plot -------------------------------------------------------------------
title_str = "chessboard-basic · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = title_str,
    titlesize         = 20,
    titlecolor        = INK,
    aspect            = DataAspect(),
    backgroundcolor   = PAGE_BG,
    xticks            = (1:8, string.(collect(files))),
    yticks            = (1:8, string.(collect(ranks))),
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xticklabelsize    = 16,
    yticklabelsize    = 16,
    xticksvisible     = false,
    yticksvisible     = false,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridvisible      = false,
)

heatmap!(ax, 1:8, 1:8, board; colormap = [DARK_SQUARE, LIGHT_SQUARE])

# Thin ink-colored grid lines between squares for definition.
for i in 0.5:1:8.5
    hlines!(ax, [i]; xmin = 0, xmax = 1, color = RGBAf(INK.r, INK.g, INK.b, 0.15), linewidth = 1)
    vlines!(ax, [i]; ymin = 0, ymax = 1, color = RGBAf(INK.r, INK.g, INK.b, 0.15), linewidth = 1)
end

limits!(ax, 0.5, 8.5, 0.5, 8.5)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
