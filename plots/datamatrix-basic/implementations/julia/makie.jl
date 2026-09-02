# anyplot.ai
# datamatrix-basic: Basic Data Matrix 2D Barcode
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# A printed Data Matrix code is black-on-white for scanner contrast under any
# lighting, so it does not follow the page theme the way surrounding chrome
# does — these two stay fixed instead of branching on THEME.
const DM_BG  = colorant"#FFFDF6"
const DM_INK = colorant"#1A1A17"

# --- Data ---------------------------------------------------------------
# Pharmaceutical serialization code, one of the spec's listed applications.
content = "RX-88451-2024-A7"
n       = 20  # modules per side, including the finder + clock-track border
quiet   = 3   # ISO/IEC 16022 quiet zone, in modules (spec asks for >= 1)
m       = n + 2 * quiet

Random.seed!(42)
z = zeros(Bool, m, m)
for x in 1:n, y in 1:n
    gx, gy = quiet + x, quiet + y
    z[gx, gy] =
        if x == 1
            true         # left column: solid L-shaped finder pattern
        elseif y == 1
            true         # bottom row: solid L-shaped finder pattern
        elseif y == n
            isodd(x)     # top row: alternating clock (timing) track
        elseif x == n
            isodd(y)     # right column: alternating clock (timing) track
        else
            rand(Bool)   # data region: representative module fill — full
                          # ECC200 Reed-Solomon codeword placement is out of
                          # scope for this static illustration
        end
end

# --- Plot -----------------------------------------------------------------
title_str      = "Pharmaceutical Serialization · datamatrix-basic · julia · makie · anyplot.ai"
title_fontsize = max(13, round(Int, 20 * min(1.0, 67 / length(title_str))))

fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    aspect             = DataAspect(),
    backgroundcolor    = DM_BG,
    title              = title_str,
    titlesize          = title_fontsize,
    titlecolor         = INK,
    xlabel             = "Encodes \"$content\" · $(n)×$(n) modules + quiet zone · ISO/IEC 16022 finder + clock track",
    xlabelsize         = 15,
    xlabelcolor        = INK_SOFT,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xticksvisible      = false,
    yticksvisible      = false,
    xticklabelsvisible = false,
    yticklabelsvisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
)

heatmap!(ax, Float64.(z);
    colormap   = [DM_BG, DM_INK],
    colorrange = (0.0, 1.0),
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
