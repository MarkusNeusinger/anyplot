# anyplot.ai
# barcode-code128: Code 128 Barcode
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-09-01

using CairoMakie
using Colors

# --- Theme tokens ------------------------------------------------------------
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# A printed barcode label is black ink on white stock under any lighting —
# it does not follow the page theme the way surrounding chrome does, so
# these two stay fixed instead of branching on THEME.
const LABEL_BG = colorant"#FFFFFF"
const BAR_INK  = colorant"#0A0A0A"
const LABEL_INK = colorant"#1A1A17"

# --- Data: Code 128 Subset B encoding -----------------------------------------
# Laboratory specimen tracking label.
content = "SPEC-88451-QC"

# Subset B covers ASCII 32 (space) through 127 (DEL) as symbol values 0-95,
# i.e. symbol value = character code point - 32. This spans every printable
# character, so subset B alone can encode the full label without switching.
values = [Int(c) - 32 for c in content]

start_value = 104  # Start Code B
checksum = mod(start_value + sum(v * i for (i, v) in enumerate(values)), 103)
codewords = vcat([start_value], values, [checksum], [106])  # 106 = Stop

# Bar/space module-width patterns (ISO/IEC 15417) for symbol values 0-105 —
# 6 widths each, alternating bar/space starting with a bar. Index 106 is the
# unique 13-module Stop pattern (7 widths, also starting with a bar).
const CODE128_WIDTHS = [
    [2,1,2,2,2,2], [2,2,2,1,2,2], [2,2,2,2,2,1], [1,2,1,2,2,3], [1,2,1,3,2,2],
    [1,3,1,2,2,2], [1,2,2,2,1,3], [1,2,2,3,1,2], [1,3,2,2,1,2], [2,2,1,2,1,3],
    [2,2,1,3,1,2], [2,3,1,2,1,2], [1,1,2,2,3,2], [1,2,2,1,3,2], [1,2,2,2,3,1],
    [1,1,3,2,2,2], [1,2,3,1,2,2], [1,2,3,2,2,1], [2,2,3,2,1,1], [2,2,1,1,3,2],
    [2,2,1,2,3,1], [2,1,3,2,1,2], [2,2,3,1,1,2], [3,1,2,1,3,1], [3,1,1,2,2,2],
    [3,2,1,1,2,2], [3,2,1,2,2,1], [3,1,2,2,1,2], [3,2,2,1,1,2], [3,2,2,2,1,1],
    [2,1,2,1,2,3], [2,1,2,3,2,1], [2,3,2,1,2,1], [1,1,1,3,2,3], [1,3,1,1,2,3],
    [1,3,1,3,2,1], [1,1,2,3,1,3], [1,3,2,1,1,3], [1,3,2,3,1,1], [2,1,1,3,1,3],
    [2,3,1,1,1,3], [2,3,1,3,1,1], [1,1,2,1,3,3], [1,1,2,3,3,1], [1,3,2,1,3,1],
    [1,1,3,1,2,3], [1,1,3,3,2,1], [1,3,3,1,2,1], [3,1,3,1,2,1], [2,1,1,3,3,1],
    [2,3,1,1,3,1], [2,1,3,1,1,3], [2,1,3,3,1,1], [2,1,3,1,3,1], [3,1,1,1,2,3],
    [3,1,1,3,2,1], [3,3,1,1,2,1], [3,1,2,1,1,3], [3,1,2,3,1,1], [3,3,2,1,1,1],
    [3,1,4,1,1,1], [2,2,1,4,1,1], [4,3,1,1,1,1], [1,1,1,2,2,4], [1,1,1,4,2,2],
    [1,2,1,1,2,4], [1,2,1,4,2,1], [1,4,1,1,2,2], [1,4,1,2,2,1], [1,1,2,2,1,4],
    [1,1,2,4,1,2], [1,2,2,1,1,4], [1,2,2,4,1,1], [1,4,2,1,1,2], [1,4,2,2,1,1],
    [2,4,1,2,1,1], [2,2,1,1,1,4], [4,1,3,1,1,1], [2,4,1,1,1,2], [1,3,4,1,1,1],
    [1,1,1,2,4,2], [1,2,1,1,4,2], [1,2,1,2,4,1], [1,1,4,2,1,2], [1,2,4,1,1,2],
    [1,2,4,2,1,1], [4,1,1,2,1,2], [4,2,1,1,1,2], [4,2,1,2,1,1], [2,1,2,1,4,1],
    [2,1,4,1,2,1], [4,1,2,1,2,1], [1,1,1,1,4,3], [1,1,1,3,4,1], [1,3,1,1,4,1],
    [1,1,4,1,1,3], [1,1,4,3,1,1], [4,1,1,1,1,3], [4,1,1,3,1,1], [1,1,3,1,4,1],
    [1,1,4,1,3,1], [3,1,1,1,4,1], [4,1,1,1,3,1], [2,1,1,4,1,2], [2,1,1,2,1,4],
    [2,1,1,2,3,2],
    [2,3,3,1,1,1,2],
]

# --- Geometry ------------------------------------------------------------------
module_width  = 6    # design px per module
quiet_modules = 10   # ISO/IEC 15417 minimum quiet zone, each side

bar_widths  = [CODE128_WIDTHS[c + 1] for c in codewords]  # +1: Julia is 1-indexed
flat_widths = vcat(bar_widths...) .* module_width
is_bar      = vcat([isodd.(1:length(w)) for w in bar_widths]...)

barcode_width = sum(flat_widths)
quiet_width   = quiet_modules * module_width
half_block    = barcode_width / 2 + quiet_width
canvas_center = 800.0

block_left = canvas_center - half_block
bar_x0     = block_left + quiet_width

edges       = cumsum(vcat([0.0], flat_widths))
bar_starts  = edges[1:end-1][is_bar] .+ bar_x0
bar_lengths = flat_widths[is_bar]

bar_y_bottom = 390.0
bar_height   = 260.0
bar_rects    = Rect2f.(bar_starts, bar_y_bottom, bar_lengths, bar_height)

card_pad_x  = 60.0
card_x      = block_left - card_pad_x
card_width  = 2 * half_block + 2 * card_pad_x
card_y      = 300.0
card_height = 400.0

# --- Plot ------------------------------------------------------------------
fig = Figure(size = (1600, 900), backgroundcolor = PAGE_BG)

ax = Axis(fig[1, 1]; backgroundcolor = PAGE_BG, aspect = DataAspect())
hidedecorations!(ax)
hidespines!(ax)
xlims!(ax, 0, 1600)
ylims!(ax, 0, 900)

poly!(ax, Rect2f(card_x, card_y, card_width, card_height); color = LABEL_BG)
poly!(ax, bar_rects; color = BAR_INK)

text!(ax, canvas_center, 815;
      text = "barcode-code128 · julia · makie · anyplot.ai",
      color = INK, fontsize = 26, align = (:center, :center))
text!(ax, canvas_center, 758;
      text = "Laboratory specimen label",
      color = INK_SOFT, fontsize = 18, align = (:center, :center))
text!(ax, canvas_center, 340; text = content,
      color = LABEL_INK, fontsize = 26, font = :bold, align = (:center, :center))
text!(ax, canvas_center, 150;
      text = "Code 128, Subset B  ·  Quiet zone $(quiet_modules) modules each side  ·  Check digit $(checksum)",
      color = INK_MUTED, fontsize = 15, align = (:center, :center))

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
