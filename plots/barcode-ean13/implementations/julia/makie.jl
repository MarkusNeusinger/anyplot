# anyplot.ai
# barcode-ean13: EAN-13 Barcode
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 90/100 | Created: 2026-09-01

using CairoMakie
using Colors

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# A real EAN-13 needs a light quiet zone to stay scannable, so the label
# stock and bar ink are fixed rather than theme-adaptive — like a printed
# barcode photographed on a page, this "data" doesn't flip with the theme.
const LABEL_BG   = colorant"#FBF9F2"
const BAR_INK    = colorant"#15130F"
const PAPER_TEXT = colorant"#4A4A44"  # fixed muted ink for text on the paper card

# --- Data: encode a 13-digit EAN-13 -----------------------------------------
# GS1 prefix "400" identifies Germany; the remaining digits are a
# manufacturer reference, product reference, and check digit.
code   = "4006381333931"
digits = [parse(Int, c) for c in code]

# Recompute the check digit from the first 12 digits (odd positions x1,
# even positions x3, mod 10) to confirm the example is a valid EAN-13.
odd_sum    = sum(digits[i] for i in 1:2:11)
even_sum   = sum(digits[i] for i in 2:2:12)
digits[13] = (10 - (odd_sum + 3 * even_sum) % 10) % 10

# 7-module digit patterns: L (left, odd parity), G (left, even parity), R (right)
L_CODE = ["0001101", "0011001", "0010011", "0111101", "0100011",
          "0110001", "0101111", "0111011", "0110111", "0001011"]
G_CODE = ["0100111", "0110011", "0011011", "0100001", "0011101",
          "0111001", "0000101", "0010001", "0001001", "0010111"]
R_CODE = ["1110010", "1100110", "1101100", "1000010", "1011100",
          "1001110", "1010000", "1000100", "1001000", "1110100"]

# Which of the 6 left digits use L vs. G code, keyed by the leading digit
PARITY = Dict(
    0 => "LLLLLL", 1 => "LLGLGG", 2 => "LLGGLG", 3 => "LLGGGL", 4 => "LGLLGG",
    5 => "LGGLLG", 6 => "LGGGLL", 7 => "LGLGLG", 8 => "LGLGGL", 9 => "LGGLGL",
)

first_digit    = digits[1]
left_digits    = digits[2:7]
right_digits   = digits[8:13]
parity         = PARITY[first_digit]
left_patterns  = [parity[i] == 'L' ? L_CODE[left_digits[i] + 1] : G_CODE[left_digits[i] + 1]
                  for i in 1:6]
right_patterns = [R_CODE[right_digits[i] + 1] for i in 1:6]

START_GUARD, CENTER_GUARD, END_GUARD = "101", "01010", "101"

# --- Geometry: lay out modules left to right --------------------------------
quiet   = 9      # quiet-zone module widths (spec minimum on each side)
bar_h   = 70.0   # data-bar height, in module-width units
guard_h = 75.0   # guard bars run 5 modules deeper than data bars (GS1 spec)

bars = Tuple{Float64,Float64}[]  # (x, height) of every printed (black) module
x = Float64(quiet)
for bit in START_GUARD
    bit == '1' && push!(bars, (x, guard_h))
    global x += 1
end
for pattern in left_patterns
    for bit in pattern
        bit == '1' && push!(bars, (x, bar_h))
        global x += 1
    end
end
for bit in CENTER_GUARD
    bit == '1' && push!(bars, (x, guard_h))
    global x += 1
end
for pattern in right_patterns
    for bit in pattern
        bit == '1' && push!(bars, (x, bar_h))
        global x += 1
    end
end
for bit in END_GUARD
    bit == '1' && push!(bars, (x, guard_h))
    global x += 1
end
total_width = x + quiet

left_start  = quiet + 3
right_start = quiet + 3 + 42 + 5

# --- Plot ---------------------------------------------------------------
title_str  = "barcode-ean13 · julia · makie · anyplot.ai"
title_size = length(title_str) > 67 ? round(Int, 20 * 67 / length(title_str)) : 20

fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title               = title_str,
    titlesize           = title_size,
    titlecolor          = INK,
    subtitle            = "EAN-13 · $(join(digits)) · Germany · retail product identification",
    subtitlesize        = 13,
    subtitlecolor       = INK_SOFT,
    backgroundcolor     = PAGE_BG,
    xticksvisible       = false,
    yticksvisible       = false,
    xticklabelsvisible  = false,
    yticklabelsvisible  = false,
    topspinevisible     = false,
    rightspinevisible   = false,
    leftspinevisible    = false,
    bottomspinevisible  = false,
    xgridvisible        = false,
    ygridvisible        = false,
    xminorgridvisible   = false,
    yminorgridvisible   = false,
)

# Vertical layout, top to bottom: bars -> human-readable digits ->
# colored structure underlines -> segment names -> paper backdrop.
text_top      = -(guard_h + 8.0)
underline_y   = text_top - 34.0
underline_h   = 6.0
seg_label_top = underline_y - underline_h - 10.0
paper_top     = 18.0
paper_bottom  = seg_label_top - 26.0

poly!(ax, Rect2f(0.0, paper_bottom, total_width, paper_top - paper_bottom);
      color = LABEL_BG, strokewidth = 0)

# Bars: guard patterns (start, center, end) run deeper than data bars
for (bx, bh) in bars
    poly!(ax, Rect2f(bx, -bh, 1.0, bh); color = BAR_INK, strokewidth = 0)
end

# Human-readable digits — the leading digit sits left of the start guard
text!(ax, quiet - 1.0, text_top; text = string(first_digit),
      color = BAR_INK, fontsize = 24, align = (:right, :top))
for (i, d) in enumerate(left_digits)
    text!(ax, left_start + (i - 1) * 7 + 3.5, text_top; text = string(d),
          color = BAR_INK, fontsize = 24, align = (:center, :top))
end
for (i, d) in enumerate(right_digits)
    text!(ax, right_start + (i - 1) * 7 + 3.5, text_top; text = string(d),
          color = BAR_INK, fontsize = 24, align = (:center, :top))
end

# Structure legend: country / manufacturer / product / check digit.
# Imprint positions 1-3 in canonical order for the abstract groups; the
# check digit gets the semantic-red anchor (position 5) instead of the
# next ordinal slot, since its role is error detection, not an abstract
# category (see "Semantic exception" in the default style guide).
segments = [
    (2.0,                left_start + 7.0,   IMPRINT_PALETTE[1], "Country"),
    (left_start + 7.0,   left_start + 42.0,  IMPRINT_PALETTE[2], "Manufacturer"),
    (right_start,        right_start + 35.0, IMPRINT_PALETTE[3], "Product"),
    (right_start + 35.0, right_start + 42.0, IMPRINT_PALETTE[5], "Check"),
]

for (x1, x2, color, label) in segments
    poly!(ax, Rect2f(x1, underline_y, x2 - x1, underline_h); color = color, strokewidth = 0)
    text!(ax, (x1 + x2) / 2, seg_label_top; text = label,
          color = PAPER_TEXT, fontsize = 15, align = (:center, :top))
end

xlims!(ax, -4.0, total_width + 4.0)
ylims!(ax, paper_bottom - 8.0, paper_top + 8.0)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
