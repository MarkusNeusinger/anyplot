# anyplot.ai
# scatter-hr-diagram: Hertzsprung-Russell Diagram
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-06-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette — 8 hues, hybrid-v3 sort, theme-independent
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (first series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data — synthetic stellar populations for Hertzsprung-Russell diagram
n_ms = 200
ms_temp = exp.(range(log(3200.0), log(38000.0), length=n_ms) .+ randn(n_ms) .* 0.06)
ms_lum  = (ms_temp ./ 5778.0) .^ 3.5 .* exp.(randn(n_ms) .* 0.22)

n_rg = 45
rg_temp = exp.(log(3900.0) .+ randn(n_rg) .* 0.16)
rg_lum  = exp.(range(log(10.0), log(600.0), length=n_rg) .+ randn(n_rg) .* 0.35)

n_sg = 18
sg_temp = exp.(range(log(3500.0), log(22000.0), length=n_sg) .+ randn(n_sg) .* 0.18)
sg_lum  = exp.(range(log(4000.0), log(180000.0), length=n_sg) .+ randn(n_sg) .* 0.30)

n_wd = 28
wd_temp = exp.(range(log(9000.0), log(55000.0), length=n_wd) .+ randn(n_wd) .* 0.12)
wd_lum  = exp.(range(log(0.0001), log(0.008), length=n_wd) .+ randn(n_wd) .* 0.30)

# Semantic color assignments (Imprint palette, stellar spectral convention):
# main sequence → brand green (#009E73, first series)
# red giants    → matte red  (#AE3030, semantic anchor: dominant red chromatic identity)
# supergiants   → lavender   (#C475FD, luminous, often hot/blue supergiants)
# white dwarfs  → blue       (#4467A3, hot blue-white stellar remnants)
# Sun           → amber      (#DDCC77, yellow G-type reference — semantic anchor)
col_ms  = IMPRINT_PALETTE[1]
col_rg  = IMPRINT_PALETTE[5]
col_sg  = IMPRINT_PALETTE[2]
col_wd  = IMPRINT_PALETTE[3]
col_sun = colorant"#DDCC77"

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "scatter-hr-diagram · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Surface Temperature (K)",
    ylabel             = "Luminosity (L☉)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(Float32(INK.r), Float32(INK.g), Float32(INK.b), 0.12f0),
    ygridcolor         = RGBAf(Float32(INK.r), Float32(INK.g), Float32(INK.b), 0.12f0),
    xscale             = log10,
    yscale             = log10,
    xreversed          = true,
    xticks             = ([3000, 5000, 10000, 20000, 40000],
                          ["3k", "5k", "10k", "20k", "40k"]),
)

# Stellar populations — x-axis reversed (hot on left, following astrophysical convention)
scatter!(ax, ms_temp, ms_lum;
    color = (col_ms, 0.65), markersize = 7, strokewidth = 0,
    label = "Main Sequence")
scatter!(ax, rg_temp, rg_lum;
    color = (col_rg, 0.85), markersize = 13, strokewidth = 0,
    label = "Red Giants")
scatter!(ax, sg_temp, sg_lum;
    color = (col_sg, 0.85), markersize = 16, strokewidth = 0,
    label = "Supergiants")
scatter!(ax, wd_temp, wd_lum;
    color = (col_wd, 0.80), markersize = 6, strokewidth = 0,
    label = "White Dwarfs")
scatter!(ax, [5778.0], [1.0];
    color = col_sun, markersize = 20, marker = :star5,
    strokewidth = 1.5, strokecolor = INK,
    label = "Sun")

# Region labels in data coordinates
text!(ax, 9000.0, 6.0;
    text = "Main Sequence", fontsize = 12, color = INK_SOFT,
    align = (:center, :center))
text!(ax, 3750.0, 200.0;
    text = "Red Giants", fontsize = 12, color = INK_SOFT,
    align = (:center, :center))
text!(ax, 10000.0, 80000.0;
    text = "Supergiants", fontsize = 12, color = INK_SOFT,
    align = (:center, :center))
text!(ax, 25000.0, 0.002;
    text = "White Dwarfs", fontsize = 12, color = INK_SOFT,
    align = (:center, :center))

# Legend
axislegend(ax;
    position        = :rb,
    backgroundcolor = ELEVATED_BG,
    framecolor      = INK_SOFT,
    fontsize        = 11,
)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
