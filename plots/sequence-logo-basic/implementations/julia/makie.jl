# anyplot.ai
# sequence-logo-basic: Sequence Logo for Motif Visualization
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 83/100 | Created: 2026-06-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens — Imprint palette, theme-adaptive chrome
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# DNA letter colors — Imprint palette semantic exception (bioinformatics convention)
# A=green, C=blue, G=ochre, T=red  (standard bioinformatics color scheme)
const DNA_COLORS = Dict(
    "A" => colorant"#009E73",  # Imprint position 1 — brand green
    "C" => colorant"#4467A3",  # Imprint position 3 — blue
    "G" => colorant"#BD8233",  # Imprint position 4 — ochre
    "T" => colorant"#AE3030",  # Imprint position 5 — matte red
)
const LETTERS = ["A", "C", "G", "T"]

# TATA-box transcription factor binding site: 10-position DNA motif
# Rows: [freq_A, freq_C, freq_G, freq_T] summing to 1.0 per position
const MOTIF_FREQS = [
    [0.10, 0.10, 0.10, 0.70],   # 1  — T-dominant
    [0.80, 0.05, 0.10, 0.05],   # 2  — A-dominant
    [0.05, 0.05, 0.10, 0.80],   # 3  — T-dominant
    [0.75, 0.10, 0.05, 0.10],   # 4  — A-dominant
    [0.60, 0.15, 0.15, 0.10],   # 5  — A-dominant
    [0.65, 0.10, 0.15, 0.10],   # 6  — A-dominant
    [0.15, 0.30, 0.30, 0.25],   # 7  — mixed (less conserved)
    [0.05, 0.05, 0.80, 0.10],   # 8  — G-dominant
    [0.10, 0.10, 0.05, 0.75],   # 9  — T-dominant
    [0.55, 0.15, 0.20, 0.10],   # 10 — A-dominant
]

n_pos = length(MOTIF_FREQS)

# Information content: IC = 2 + Σ f·log2(f)  (bits; max = 2 for DNA)
ic_vals = [begin
    ic = 2.0
    for f in freqs
        f > 0 && (ic += f * log2(f))
    end
    max(0.0, ic)
end for freqs in MOTIF_FREQS]

# Per-position stacks: sorted ascending by contribution (least → bottom, most → top)
stack_data = [begin
    ic = ic_vals[p]
    items = [(LETTERS[i], MOTIF_FREQS[p][i] * ic)
             for i in eachindex(LETTERS) if MOTIF_FREQS[p][i] > 0.005]
    sort!(items; by = x -> x[2])
    out = Tuple{String, Float64, Float64}[]
    y = 0.0
    for (ltr, contrib) in items
        push!(out, (ltr, contrib, y))
        y += contrib
    end
    out
end for p in 1:n_pos]

# Title with font-size scaled for length
title_str  = "TATA-box Motif · sequence-logo-basic · julia · makie · anyplot.ai"
n_chars    = length(title_str)
title_size = max(12, round(Int, 20 * min(1.0, 67.0 / n_chars)))

# Scaled-glyph font-size constants: axis height ≈ 70% of 900 pts canvas
# Y-range = 2 bits → ~315 pts/bit; fill 80% of each bar's height with the letter
const PTS_PER_BIT = 315.0
const FILL_FACTOR = 0.80

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = Float32(title_size),
    titlecolor         = INK,
    xlabel             = "Position",
    ylabel             = "Information content (bits)",
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    xticks             = 1:n_pos,
    yticks             = 0.0:0.5:2.0,
    limits             = (0.35, n_pos + 0.65, -0.05, 2.15),
)

# Subtle shaded band highlighting the TATA-box conserved core (positions 2–6)
poly!(ax, Rect2f(1.5, 0.0, 5.0, 2.0);
      color       = RGBAf(INK.r, INK.g, INK.b, 0.04),
      strokewidth = 0.8,
      strokecolor = RGBAf(INK.r, INK.g, INK.b, 0.10))

# Sequence logo: stacked colored rectangles + proportionally-scaled letter glyphs
bar_w = 0.88

for (pos, stacks) in enumerate(stack_data)
    for (letter, contrib, y_bot) in stacks
        contrib < 0.01 && continue
        poly!(ax, Rect2f(pos - bar_w / 2, y_bot, bar_w, contrib);
              color       = DNA_COLORS[letter],
              strokewidth = 0.4,
              strokecolor = PAGE_BG)
        # Scaled-glyph rendering: fontsize grows with bar height
        if contrib > 0.025
            glyph_size = max(6, round(Int, contrib * PTS_PER_BIT * FILL_FACTOR))
            text!(ax, Float64(pos), y_bot + contrib / 2;
                  text     = letter,
                  color    = (:white, 0.92),
                  fontsize = glyph_size,
                  align    = (:center, :center),
                  font     = :bold)
        end
    end
end

# Legend
leg_elems = [PolyElement(color = DNA_COLORS[l], strokecolor = :transparent) for l in LETTERS]
Legend(fig[1, 2], leg_elems, LETTERS, "Nucleotide";
       backgroundcolor = ELEVATED_BG,
       framevisible    = true,
       framecolor      = INK_SOFT,
       labelcolor      = INK,
       titlecolor      = INK,
       labelsize       = 12,
       titlesize       = 12,
       padding         = (8, 8, 8, 8),
       rowgap          = 4)

save("plot-$(THEME).png", fig; px_per_unit = 2)
