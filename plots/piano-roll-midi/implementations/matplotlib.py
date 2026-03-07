""" pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-07
"""

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - A musical phrase: ascending melody with chords and varying dynamics
np.random.seed(42)

black_keys_semitone = {1, 3, 6, 8, 10}  # C#, D#, F#, G#, A#

# Compose a short piece: melody + bass + chords over 8 measures (32 beats)
notes = [
    # Measure 1 - Opening melody
    (0.0, 1.0, 72, 100),
    (1.0, 0.5, 74, 90),
    (1.5, 0.5, 76, 85),
    (2.0, 1.5, 79, 110),
    (3.5, 0.5, 76, 70),
    # Bass notes measure 1
    (0.0, 2.0, 60, 80),
    (2.0, 2.0, 64, 75),
    # Measure 2 - Continuation
    (4.0, 1.0, 74, 95),
    (5.0, 1.0, 72, 88),
    (6.0, 2.0, 76, 105),
    # Bass measure 2
    (4.0, 2.0, 65, 78),
    (6.0, 2.0, 67, 82),
    # Measure 3 - Chords + melody
    (8.0, 2.0, 79, 115),
    (8.0, 2.0, 76, 90),
    (8.0, 2.0, 72, 85),
    (10.0, 1.0, 81, 120),
    (11.0, 1.0, 79, 100),
    # Bass measure 3
    (8.0, 4.0, 60, 85),
    # Measure 4 - Descending
    (12.0, 1.0, 79, 95),
    (13.0, 1.0, 76, 88),
    (14.0, 1.0, 74, 80),
    (15.0, 1.0, 72, 75),
    # Bass measure 4
    (12.0, 2.0, 64, 78),
    (14.0, 2.0, 62, 72),
    # Measure 5 - New phrase, louder
    (16.0, 0.5, 72, 105),
    (16.5, 0.5, 74, 100),
    (17.0, 0.5, 76, 110),
    (17.5, 0.5, 79, 115),
    (18.0, 2.0, 81, 125),
    # Bass measure 5
    (16.0, 2.0, 60, 90),
    (18.0, 2.0, 67, 88),
    # Measure 6 - Sustained
    (20.0, 3.0, 79, 108),
    (23.0, 1.0, 76, 85),
    # Chord measure 6
    (20.0, 2.0, 72, 80),
    (20.0, 2.0, 67, 75),
    # Bass measure 6
    (20.0, 4.0, 60, 82),
    # Measure 7 - Climax
    (24.0, 1.0, 76, 100),
    (25.0, 1.0, 79, 110),
    (26.0, 2.0, 81, 127),
    (26.0, 2.0, 76, 100),
    (26.0, 2.0, 72, 95),
    # Bass measure 7
    (24.0, 2.0, 65, 90),
    (26.0, 2.0, 64, 85),
    # Measure 8 - Resolution
    (28.0, 2.0, 79, 90),
    (30.0, 2.0, 72, 70),
    (28.0, 2.0, 76, 80),
    (30.0, 2.0, 67, 65),
    # Bass measure 8
    (28.0, 4.0, 60, 75),
]

pitches = np.array([n[2] for n in notes])

# Pitch range with margin
pitch_min = int(pitches.min()) - 1
pitch_max = int(pitches.max()) + 1

# Velocity colormap: perceptually-uniform, colorblind-safe
cmap = plt.cm.plasma
norm = mcolors.Normalize(vmin=40, vmax=127)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#FAFAFA")
ax.set_facecolor("#FAFAFA")

# Background: alternate shading for black vs white keys
for pitch in range(pitch_min, pitch_max + 1):
    semitone = pitch % 12
    if semitone in black_keys_semitone:
        ax.axhspan(pitch - 0.5, pitch + 0.5, color="#E0E0E0", zorder=0)
    else:
        ax.axhspan(pitch - 0.5, pitch + 0.5, color="#F0F0F0", zorder=0)

# Beat grid lines
total_beats = 32
for beat in range(total_beats + 1):
    if beat % 4 == 0:
        ax.axvline(beat, color="#999999", linewidth=1.2, zorder=1)
    else:
        ax.axvline(beat, color="#CCCCCC", linewidth=0.6, zorder=1)

# Draw note rectangles with shadow effect for depth
for start, dur, pitch, vel in notes:
    color = cmap(norm(vel))
    rect = mpatches.FancyBboxPatch(
        (start, pitch - 0.4),
        dur,
        0.8,
        boxstyle="round,pad=0.05",
        facecolor=color,
        edgecolor="white",
        linewidth=1.0,
        zorder=2,
        path_effects=[pe.withStroke(linewidth=2.5, foreground="#00000020"), pe.Normal()],
    )
    ax.add_patch(rect)

# Y-axis: note names
visible_pitches = list(range(pitch_min, pitch_max + 1))
pitch_labels = []
for p in visible_pitches:
    octave = p // 12 - 1
    semitone = p % 12
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][semitone]
    pitch_labels.append(f"{name}{octave}")

ax.set_yticks(visible_pitches)
ax.set_yticklabels(pitch_labels, fontsize=16, fontfamily="monospace")

# X-axis: beats
beat_ticks = np.arange(0, total_beats + 1, 4)
ax.set_xticks(beat_ticks)
ax.set_xticklabels([str(int(b // 4) + 1) for b in beat_ticks], fontsize=16)

# Style
ax.set_xlim(-0.2, total_beats + 0.2)
ax.set_ylim(pitch_min - 0.5, pitch_max + 0.5)
ax.set_xlabel("Measure", fontsize=20, labelpad=10)
ax.set_ylabel("Pitch", fontsize=20, labelpad=10)
ax.set_title("piano-roll-midi · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.tick_params(axis="both", length=0)

# Colorbar for velocity
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02, aspect=30, shrink=0.8)
cbar.set_label("Velocity (MIDI)", fontsize=18)
cbar.ax.tick_params(labelsize=16)
cbar.outline.set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
