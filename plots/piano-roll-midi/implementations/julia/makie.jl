# anyplot.ai
# piano-roll-midi: MIDI Piano Roll Visualization
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-06-03

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

# Imprint sequential colormap for velocity (blue=soft → green=loud, both Imprint positions)
const VEL_CMAP = cgrad([colorant"#4467A3", colorant"#009E73"])

# Piano keyboard row backgrounds
const WHITE_KEY_BG = THEME == "light" ? RGBAf(0.980, 0.973, 0.945, 1.0) : RGBAf(0.130, 0.130, 0.112, 1.0)
const BLACK_KEY_BG = THEME == "light" ? RGBAf(0.900, 0.891, 0.858, 1.0) : RGBAf(0.082, 0.082, 0.070, 1.0)

is_black_key(pitch) = mod(pitch, 12) in (1, 3, 6, 8, 10)

function midi_to_name(pitch)
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = div(pitch, 12) - 1
    return string(names[mod(pitch, 12) + 1], octave)
end

# Data: C major generative phrase over 4 measures (4/4, 16 beats total)
# Each tuple: (pitch, start, duration, velocity)
notes_raw = [
    # Measure 1 — ascending melody
    (60, 0.0,  0.5,  68),  # C4
    (62, 0.5,  0.5,  74),  # D4
    (64, 1.0,  0.5,  80),  # E4
    (67, 1.5,  0.5,  86),  # G4
    (69, 2.0,  1.0,  92),  # A4
    (67, 3.0,  0.5,  80),  # G4
    (65, 3.5,  0.5,  74),  # F4
    # Measure 1 — chord accompaniment
    (48, 0.0,  2.0,  52),  # C3
    (52, 0.0,  2.0,  48),  # E3
    (55, 0.0,  2.0,  48),  # G3
    (53, 2.0,  2.0,  52),  # F3
    (57, 2.0,  2.0,  48),  # A3
    (60, 2.0,  2.0,  48),  # C4 chord
    # Measure 2 — rising to climax
    (64, 4.0,  0.5,  84),  # E4
    (65, 4.5,  0.5,  80),  # F4
    (67, 5.0,  1.0,  96),  # G4
    (69, 6.0,  0.5,  88),  # A4
    (71, 6.5,  0.5,  92),  # B4
    (72, 7.0,  1.0, 102),  # C5 peak
    # Measure 2 — chord accompaniment
    (55, 4.0,  2.0,  54),  # G3
    (59, 4.0,  2.0,  48),  # B3
    (62, 4.0,  2.0,  48),  # D4
    (50, 6.0,  2.0,  54),  # D3
    (53, 6.0,  2.0,  48),  # F3
    (57, 6.0,  2.0,  48),  # A3
    # Measure 3 — descending return
    (71, 8.0,  0.5,  90),  # B4
    (69, 8.5,  0.5,  84),  # A4
    (67, 9.0,  0.5,  78),  # G4
    (65, 9.5,  0.5,  74),  # F4
    (64, 10.0, 1.0,  82),  # E4
    (62, 11.0, 0.5,  72),  # D4
    (60, 11.5, 0.5,  68),  # C4
    # Measure 3 — chord accompaniment
    (48, 8.0,  2.0,  52),  # C3
    (52, 8.0,  2.0,  48),  # E3
    (55, 8.0,  2.0,  48),  # G3
    (50, 10.0, 2.0,  52),  # D3
    (53, 10.0, 2.0,  48),  # F3
    (57, 10.0, 2.0,  48),  # A3
    # Measure 4 — resolution
    (67, 12.0, 0.5,  78),  # G4
    (65, 12.5, 0.5,  74),  # F4
    (64, 13.0, 1.0,  84),  # E4
    (62, 14.0, 0.5,  70),  # D4
    (60, 14.5, 1.5,  92),  # C4 final
    # Measure 4 — final tonic chord
    (48, 12.0, 4.0,  58),  # C3
    (52, 12.0, 4.0,  54),  # E3
    (55, 12.0, 4.0,  54),  # G3
    (60, 12.0, 4.0,  50),  # C4
]

pitches    = [n[1] for n in notes_raw]
starts     = Float32[n[2] for n in notes_raw]
durations  = Float32[n[3] for n in notes_raw]
velocities = [n[4] for n in notes_raw]

pitch_min    = minimum(pitches) - 1   # 47
pitch_max    = maximum(pitches) + 1   # 73
total_beats  = 16.0f0

# Plot
fig = Figure(
    size            = (1600, 900),
    fontsize        = 13,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "piano-roll-midi · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Time (beats)",
    ylabel            = "Pitch",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 11,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridvisible      = false,
)

# Background rows: alternate white/black key shading
for pitch in pitch_min:pitch_max
    bg = is_black_key(pitch) ? BLACK_KEY_BG : WHITE_KEY_BG
    poly!(ax, Rect2f(0.0f0, pitch - 0.5f0, total_beats, 1.0f0); color = bg)
end

# Vertical beat grid lines
for beat in 0:Int(total_beats)
    is_measure = mod(beat, 4) == 0
    lw    = is_measure ? 1.8f0 : 0.7f0
    alpha = is_measure ? 0.40f0 : 0.18f0
    vlines!(ax, Float32(beat);
        color     = RGBAf(INK.r, INK.g, INK.b, alpha),
        linewidth = lw,
    )
end

# Note rectangles, colored by velocity
note_rects  = [Rect2f(starts[i], pitches[i] - 0.42f0, durations[i] - 0.04f0, 0.84f0)
               for i in eachindex(notes_raw)]
note_colors = [get(VEL_CMAP, velocities[i] / 127.0) for i in eachindex(notes_raw)]

poly!(ax, note_rects;
    color       = note_colors,
    strokecolor = RGBAf(INK.r, INK.g, INK.b, 0.55f0),
    strokewidth = 0.7f0,
)

# Y-axis ticks: show names for white-key pitches only (avoid crowding)
white_pitches = [p for p in pitch_min:pitch_max if !is_black_key(p)]
ax.yticks = (white_pitches, [midi_to_name(p) for p in white_pitches])

# X-axis ticks: beats 0, 4, 8, 12, 16
ax.xticks = (0:4:16, string.(0:4:16))

# Measure number labels at the top of each measure
for m in 1:4
    x_pos = (m - 1) * 4.0f0 + 0.12f0
    text!(ax, x_pos, Float32(pitch_max) + 0.3f0;
        text     = "Meas. $m",
        fontsize = 11,
        color    = INK_SOFT,
        align    = (:left, :center),
    )
end

xlims!(ax, -0.3f0, total_beats + 0.3f0)
ylims!(ax, pitch_min - 0.5f0, pitch_max + 0.8f0)

# Velocity colorbar
Colorbar(fig[1, 2];
    colormap        = VEL_CMAP,
    limits          = (0.0, 127.0),
    label           = "Velocity",
    labelsize       = 13,
    labelcolor      = INK,
    ticksize        = 5,
    tickcolor       = INK_SOFT,
    ticklabelsize   = 11,
    ticklabelcolor  = INK_SOFT,
    ticks           = [0, 32, 64, 96, 127],
    width           = 18,
    topspinecolor   = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    leftspinecolor  = INK_SOFT,
    rightspinecolor = INK_SOFT,
)

colsize!(fig.layout, 1, Relative(0.93))

save(joinpath(@__DIR__, "plot-$(THEME).png"), fig; px_per_unit = 2)
