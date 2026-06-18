# anyplot.ai
# scatter-constellation-diagram: Digital Modulation Constellation Diagram
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-06-18

using CairoMakie
using Colors
using Printf
using Random
using Statistics

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (first series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red (semantic: reference target)
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# 16-QAM ideal constellation: ±1, ±3 grid (4×4 = 16 symbols)
levels = [-3.0, -1.0, 1.0, 3.0]
ideal_i = [ii for qi in levels for ii in levels]
ideal_q = [qi for qi in levels for ii in levels]

# Received symbols with additive Gaussian noise (~20 dB SNR)
n_symbols = 1200
noise_std = 0.18
symbol_idx = rand(1:16, n_symbols)
recv_i = ideal_i[symbol_idx] .+ noise_std .* randn(n_symbols)
recv_q = ideal_q[symbol_idx] .+ noise_std .* randn(n_symbols)

# EVM: sqrt(mean squared error) / RMS ideal amplitude × 100%
err_sq = (recv_i .- ideal_i[symbol_idx]).^2 .+ (recv_q .- ideal_q[symbol_idx]).^2
rms_signal = sqrt(mean(ideal_i.^2 .+ ideal_q.^2))
evm_pct = sqrt(mean(err_sq)) / rms_signal * 100.0

# Figure — square canvas (equal aspect ratio required for constellation geometry)
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

title_str = "scatter-constellation-diagram · julia · makie · anyplot.ai"
ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "In-Phase (I)",
    ylabel             = "Quadrature (Q)",
    xlabelsize         = 16,
    ylabelsize         = 16,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 13,
    yticklabelsize     = 13,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = false,
    xminorgridvisible  = false,
    yminorgridvisible  = false,
    aspect             = DataAspect(),
    limits             = (-4.5, 4.5, -4.5, 4.5),
)

# Dashed decision boundary lines separating the 16 symbol regions
boundary_color = RGBAf(INK.r, INK.g, INK.b, 0.2f0)
for boundary in [-2.0, 0.0, 2.0]
    hlines!(ax, boundary; color = boundary_color, linewidth = 1.2, linestyle = :dash)
    vlines!(ax, boundary; color = boundary_color, linewidth = 1.2, linestyle = :dash)
end

# Received symbols — Imprint brand green (first series), semi-transparent
recv_plt = scatter!(ax, recv_i, recv_q;
    color       = RGBAf(IMPRINT_PALETTE[1].r, IMPRINT_PALETTE[1].g, IMPRINT_PALETTE[1].b, 0.4f0),
    markersize  = 8,
    strokewidth = 0,
)

# Ideal 16-QAM reference points — matte red cross markers
ideal_plt = scatter!(ax, ideal_i, ideal_q;
    color       = IMPRINT_PALETTE[5],
    marker      = :xcross,
    markersize  = 20,
    strokewidth = 2.5,
)

# EVM annotation (top-left, clear of constellation data)
text!(ax, -4.2, 4.1;
    text     = @sprintf("EVM = %.1f%%", evm_pct),
    fontsize = 15,
    color    = INK,
)

# Legend
Legend(
    fig[2, 1],
    [recv_plt, ideal_plt],
    ["Received symbols (n = $n_symbols)", "Ideal 16-QAM points"],
    orientation     = :horizontal,
    framecolor      = INK_SOFT,
    framewidth      = 0.5,
    labelcolor      = INK_SOFT,
    fontsize        = 14,
    backgroundcolor = ELEVATED_BG,
    tellheight      = true,
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
