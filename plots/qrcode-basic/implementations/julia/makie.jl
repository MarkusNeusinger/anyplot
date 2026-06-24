# anyplot.ai
# qrcode-basic: Basic QR Code Generator
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-06-24

using CairoMakie
using Colors
using QRCoders

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# QR code is always dark-on-light for scanner reliability
const QR_MODULE = colorant"#1A1A17"
const QR_BG     = colorant"#FFFDF6"

# Data: encode the anyplot.ai URL with Medium error correction (M = 15%)
url       = "https://anyplot.ai"
qr_raw    = qrcode(url; eclevel = Medium())
n         = size(qr_raw, 1)

# Add ISO/IEC 18004 quiet zone: 4 modules on each side
quiet  = 4
m      = n + 2 * quiet
padded = falses(m, m)
padded[quiet+1:quiet+n, quiet+1:quiet+n] .= qr_raw

# Convert to Float64 for the heatmap colormap (0 = light, 1 = dark)
z = Float64.(padded')

# Plot
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    aspect             = DataAspect(),
    backgroundcolor    = QR_BG,
    title              = "qrcode-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Encodes: $url  ·  Error correction: M (15%)",
    xlabelsize         = 13,
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
    yreversed          = true,
)

heatmap!(ax, z;
    colormap   = [QR_BG, QR_MODULE],
    colorrange = (0.0, 1.0),
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
