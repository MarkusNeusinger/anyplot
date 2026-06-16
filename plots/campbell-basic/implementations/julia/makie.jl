# anyplot.ai
# campbell-basic: Campbell Diagram
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 90/100 | Created: 2026-05-28

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
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const IMPRINT_PALETTE = [
    colorant"#009E73",   # 1 — brand green  (1st Bending)
    colorant"#C475FD",   # 2 — lavender     (2nd Bending)
    colorant"#4467A3",   # 3 — blue         (1st Torsional)
    colorant"#BD8233",   # 4 — ochre        (Axial)
]
const CRITICAL_COLOR = colorant"#AE3030"   # semantic: danger / resonance

# Data — turbine rotor, 0–6000 RPM operating range
speeds   = collect(range(0.0, 6000.0; length = 100))
speed_eo = [0.0, 6000.0]

# Natural frequency curves (Hz) — gyroscopic variation with speed
freq_1b = @.  50.0 + 25.0 * (speeds / 6000.0)   # 1st Bending:   50 → 75 Hz
freq_2b = @. 120.0 + 25.0 * (speeds / 6000.0)   # 2nd Bending:  120 → 145 Hz
freq_1t = @. 200.0 - 15.0 * (speeds / 6000.0)   # 1st Torsional: 200 → 185 Hz
freq_ax = @. 310.0 +  8.0 * (speeds / 6000.0)   # Axial:         310 → 318 Hz

# Engine order excitation lines (Hz = n × RPM / 60)
eo_freq_1x = speed_eo ./ 60.0
eo_freq_2x = 2.0 .* speed_eo ./ 60.0
eo_freq_3x = 3.0 .* speed_eo ./ 60.0

# Critical speed intersections (mode curve ∩ engine order line, analytically solved)
# Mode 1 + 1×: 4000 RPM,  66.7 Hz  |  Mode 2 + 2×: 4114 RPM, 137.1 Hz
# Mode 1 + 2×: 1714 RPM,  57.1 Hz  |  Mode 2 + 3×: 2618 RPM, 130.9 Hz
# Mode 1 + 3×: 1091 RPM,  54.5 Hz  |  Mode 3 + 3×: 3810 RPM, 190.5 Hz
crit_spd = [4000.0, 1714.3, 1090.9, 4114.3, 2618.2, 3809.5]
crit_frq  = [66.67,  57.14,  54.55, 137.14, 130.91, 190.48]

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "campbell-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Rotational Speed (RPM)",
    ylabel             = "Frequency (Hz)",
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    yminorgridvisible  = false,
    xminorgridvisible  = false,
)

# Engine order excitation lines (dashed reference lines from origin)
l_eo = lines!(ax, speed_eo, eo_freq_1x; color = INK_MUTED, linestyle = :dash, linewidth = 1.5)
lines!(ax, speed_eo, eo_freq_2x; color = INK_MUTED, linestyle = :dash, linewidth = 1.5)
lines!(ax, speed_eo, eo_freq_3x; color = INK_MUTED, linestyle = :dash, linewidth = 1.5)

# Natural frequency curves
l_1b = lines!(ax, speeds, freq_1b; color = IMPRINT_PALETTE[1], linewidth = 2.5)
l_2b = lines!(ax, speeds, freq_2b; color = IMPRINT_PALETTE[2], linewidth = 2.5)
l_1t = lines!(ax, speeds, freq_1t; color = IMPRINT_PALETTE[3], linewidth = 2.5)
l_ax = lines!(ax, speeds, freq_ax; color = IMPRINT_PALETTE[4], linewidth = 2.5)

# Critical speed intersection markers
sc_crit = scatter!(ax, crit_spd, crit_frq;
    color       = CRITICAL_COLOR,
    marker      = :diamond,
    markersize  = 14,
    strokewidth = 0,
)

xlims!(ax, 0.0, 6100.0)
ylims!(ax, 0.0, 360.0)

# Engine order labels (placed mid-plot to avoid overlap with mode curves)
text!(ax, 2100.0, 1.0 * 2100.0 / 60.0 + 3.0; text = "1×", color = INK_MUTED, fontsize = 11, align = (:left, :bottom))
text!(ax, 2100.0, 2.0 * 2100.0 / 60.0 + 3.0; text = "2×", color = INK_MUTED, fontsize = 11, align = (:left, :bottom))
text!(ax, 2100.0, 3.0 * 2100.0 / 60.0 + 3.0; text = "3×", color = INK_MUTED, fontsize = 11, align = (:left, :bottom))

# Legend
Legend(
    fig[1, 2],
    [l_1b, l_2b, l_1t, l_ax, l_eo, sc_crit],
    ["1st Bending", "2nd Bending", "1st Torsional", "Axial", "Engine Orders", "Critical Speed"],
    backgroundcolor = ELEVATED_BG,
    framecolor      = INK_SOFT,
    framewidth      = 0.5,
    labelcolor      = INK,
)

colsize!(fig.layout, 1, Relative(0.82))

save("plot-$(THEME).png", fig; px_per_unit = 2)
