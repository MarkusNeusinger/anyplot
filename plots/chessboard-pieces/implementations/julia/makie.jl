# anyplot.ai
# chessboard-pieces: Chess Board with Pieces for Position Diagrams
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 90/100 | Created: 2026-09-01

using CairoMakie
using Colors

# --- Theme tokens ------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND       = colorant"#009E73"  # Imprint palette position 1 — brand green

# Board squares blended from approved tokens (page background + brand green)
# so the checkerboard reads as a felt/wood board without an invented hue.
const LIGHT_SQUARE = weighted_color_mean(0.6, PAGE_BG, colorant"#FFFDF6")
const DARK_SQUARE  = weighted_color_mean(0.65, PAGE_BG, BRAND)

# Piece identity (white vs. black) is the data here, so — like the Imprint
# categorical colors — it stays fixed across themes; only the board and
# chrome adapt. Each fill gets an opposite-polarity stroke so a piece reads
# against either square shade.
const PIECE_LIGHT = colorant"#FFFDF6"
const PIECE_DARK  = colorant"#1A1A17"

const PIECE_GLYPHS = Dict(
    'K' => "♔", 'Q' => "♕", 'R' => "♖", 'B' => "♗", 'N' => "♘", 'P' => "♙",
    'k' => "♚", 'q' => "♛", 'r' => "♜", 'b' => "♝", 'n' => "♞", 'p' => "♟",
)

# --- Data ---------------------------------------------------------------------
# Scholar's Mate, final position: 1. e4 e5  2. Bc4 Nc6  3. Qh5 Nf6??  4. Qxf7#
const pieces = Dict(
    "a1" => 'R', "b1" => 'N', "c1" => 'B', "e1" => 'K', "c4" => 'B',
    "g1" => 'N', "h1" => 'R', "f7" => 'Q',
    "a2" => 'P', "b2" => 'P', "c2" => 'P', "d2" => 'P', "e4" => 'P',
    "f2" => 'P', "g2" => 'P', "h2" => 'P',
    "a8" => 'r', "c6" => 'n', "c8" => 'b', "d8" => 'q', "e8" => 'k',
    "f8" => 'b', "f6" => 'n', "h8" => 'r',
    "a7" => 'p', "b7" => 'p', "c7" => 'p', "d7" => 'p', "e5" => 'p',
    "g7" => 'p', "h7" => 'p',
)

# 8x8 checkerboard matrix: a1 is dark, h1 is light (standard orientation)
square_shade = [isodd(col + row) ? 1.0 : 0.0 for row in 1:8, col in 1:8]

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    backgroundcolor = PAGE_BG,
    figure_padding  = (24, 24, 12, 24),
)

title = "chessboard-pieces · julia · makie · anyplot.ai"
n = length(title)
ratio = n > 67 ? 67 / n : 1.0

ax = Axis(
    fig[1, 1];
    title           = title,
    titlesize       = round(Int, 24 * ratio),
    titlecolor      = INK,
    aspect          = DataAspect(),
    backgroundcolor = PAGE_BG,
    xticks          = (0.5:1:7.5, ["a", "b", "c", "d", "e", "f", "g", "h"]),
    yticks          = (0.5:1:7.5, string.(1:8)),
    xticklabelsize  = 20,
    yticklabelsize  = 20,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xticksvisible     = false,
    yticksvisible     = false,
    xgridvisible      = false,
    ygridvisible      = false,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinevisible  = false,
    bottomspinevisible = false,
)
xlims!(ax, 0, 8)
ylims!(ax, 0, 8)

heatmap!(ax, 0.5:1:7.5, 0.5:1:7.5, square_shade';
    colormap = [DARK_SQUARE, LIGHT_SQUARE])
lines!(ax, [0, 8, 8, 0, 0], [0, 0, 8, 8, 0]; color = INK_SOFT, linewidth = 2)

for square in sort(collect(keys(pieces)))
    piece = pieces[square]
    col = Int(square[1]) - Int('a') + 1
    row = parse(Int, square[2])
    is_white = isuppercase(piece)
    text!(ax, col - 0.5, row - 0.5;
        text        = PIECE_GLYPHS[piece],
        fontsize    = 76,
        font        = "DejaVu Sans",
        color       = is_white ? PIECE_LIGHT : PIECE_DARK,
        strokecolor = is_white ? PIECE_DARK : PIECE_LIGHT,
        strokewidth = 2.5,
        align       = (:center, :center))
end

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
