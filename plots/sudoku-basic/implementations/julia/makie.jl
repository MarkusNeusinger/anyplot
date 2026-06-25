# anyplot.ai
# sudoku-basic: Basic Sudoku Grid
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 90/100 | Created: 2026-06-25

using CairoMakie
using Colors

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Data — a classic partially-filled Sudoku puzzle
const puzzle = [
    5 3 0 0 7 0 0 0 0;
    6 0 0 1 9 5 0 0 0;
    0 9 8 0 0 0 0 6 0;
    8 0 0 0 6 0 0 0 3;
    4 0 0 8 0 3 0 0 1;
    7 0 0 0 2 0 0 0 6;
    0 6 0 0 0 0 2 8 0;
    0 0 0 4 1 9 0 0 5;
    0 0 0 0 8 0 0 7 9
]

# Figure — square canvas (2400×2400 after px_per_unit=2)
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "sudoku-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    backgroundcolor    = PAGE_BG,
    aspect             = DataAspect(),
    xgridvisible       = false,
    ygridvisible       = false,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xticksvisible      = false,
    yticksvisible      = false,
    xticklabelsvisible = false,
    yticklabelsvisible = false,
)

# Elevated background for given (clue) cells — poly! highlights filled cells
for row in 1:9, col in 1:9
    if puzzle[row, col] != 0
        poly!(ax, Rect2f(col - 1, 9 - row, 1.0, 1.0); color = ELEVATED_BG, strokewidth = 0)
    end
end

# Thin cell dividers (positions 1,2,4,5,7,8 — skip box boundaries at 0,3,6,9)
thin_segs = vcat(
    [Point2f(x, j) for x in [1, 2, 4, 5, 7, 8] for j in [0, 9]],
    [Point2f(j, y) for y in [1, 2, 4, 5, 7, 8] for j in [0, 9]],
)
linesegments!(ax, thin_segs; color = INK_SOFT, linewidth = 1.0)

# Thick box boundaries including outer border (positions 0,3,6,9)
thick_segs = vcat(
    [Point2f(x, j) for x in [0, 3, 6, 9] for j in [0, 9]],
    [Point2f(j, y) for y in [0, 3, 6, 9] for j in [0, 9]],
)
linesegments!(ax, thick_segs; color = INK, linewidth = 3.5)

# Numbers — row 1 at top (y center = 8.5), row 9 at bottom (y center = 0.5)
for row in 1:9, col in 1:9
    val = puzzle[row, col]
    if val != 0
        text!(ax, string(val);
              position = Point2f(col - 0.5, 9.5 - row),
              fontsize = 33,
              color    = INK,
              align    = (:center, :center),
        )
    end
end

limits!(ax, -0.15, 9.15, -0.15, 9.15)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
