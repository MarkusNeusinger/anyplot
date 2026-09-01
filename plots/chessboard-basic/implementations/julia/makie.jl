# anyplot.ai
# chessboard-basic: Chess Board Grid Visualization
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-01

using CairoMakie
using Colors

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Board squares pair the Imprint brand green (dark square) with the fixed
# Imprint amber anchor (light square) — both data colors stay identical
# across themes; only the surrounding chrome (background/text/grid) flips.
const DARK_SQUARE  = colorant"#009E73"
const LIGHT_SQUARE = colorant"#DDCC77"

# --- Data ---------------------------------------------------------------
# Standard chess board: a1 is dark, light squares at h1 and a8.
# (file index + rank index) even -> dark square; odd -> light square.
files = 'a':'h'
ranks = 1:8
squares      = [Rect2f(f + 0.5, r + 0.5, 1, 1) for f in 0:7 for r in 0:7]
square_color = [(f + r) % 2 == 0 ? DARK_SQUARE : LIGHT_SQUARE for f in 0:7 for r in 0:7]

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

# Each square is its own poly! Rect2f — a Makie-idiomatic geometry
# primitive rather than a generic two-color heatmap — with a thin ink
# hairline stroke between squares for definition.
hairline = RGBAf(INK.r, INK.g, INK.b, 0.15)
poly!(ax, squares; color = square_color, strokecolor = hairline, strokewidth = 1)

# Outer board frame: a crisp ink-soft border around the full 8x8 grid gives
# the eye a clean boundary and extra polish beyond the flat square fills.
lines!(ax, [0.5, 8.5, 8.5, 0.5, 0.5], [0.5, 0.5, 8.5, 8.5, 0.5]; color = INK_SOFT, linewidth = 2.5)

limits!(ax, 0.5, 8.5, 0.5, 8.5)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
