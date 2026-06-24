# anyplot.ai
# heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-06-24

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

# Imprint sequential colormap for energy (single-polarity continuous data)
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# Data: chromagram of a I-V-vi-IV progression in C major
const PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
const N_PITCH     = 12
const N_FRAMES    = 120  # 12 seconds at 10 fps

time_seconds = collect(range(0.0, 12.0, length=N_FRAMES))

# Chord tones (1-based pitch indices)
# C major: C(1), E(5), G(8) | G major: D(3), G(8), B(12)
# A minor: C(1), E(5), A(10) | F major: C(1), F(6), A(10)
const CHORD_TONES = [
    [1, 5, 8],
    [3, 8, 12],
    [1, 5, 10],
    [1, 6, 10],
]

frames_per_chord = N_FRAMES ÷ 4

# Build chromagram matrix: chroma[frame, pitch_class]
chroma = zeros(N_FRAMES, N_PITCH)

for f in 1:N_FRAMES
    chord_idx = min(4, div(f - 1, frames_per_chord) + 1)
    tones = CHORD_TONES[chord_idx]
    for p in 1:N_PITCH
        if p in tones
            chroma[f, p] = 0.60 + 0.40 * rand()
        else
            circ_dist = minimum(min(abs(p - t), 12 - abs(p - t)) for t in tones)
            chroma[f, p] = 0.20 * exp(-0.9 * circ_dist) + 0.06 * rand()
        end
    end
end

# Plot
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "heatmap-chromagram · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Time (seconds)",
    ylabel             = "Pitch Class",
    xlabelsize         = 16,
    ylabelsize         = 16,
    xticklabelsize     = 14,
    yticklabelsize     = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = false,
)

hm = heatmap!(ax, time_seconds, collect(1:N_PITCH), chroma; colormap = ANYPLOT_SEQ)

ax.yticks = (collect(1:N_PITCH), PITCH_NAMES)

cb = Colorbar(
    fig[1, 2], hm;
    label          = "Energy",
    labelsize      = 16,
    ticklabelsize  = 13,
    labelcolor     = INK,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    width          = 25,
)

colgap!(fig.layout, 15)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
