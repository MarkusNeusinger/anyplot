""" pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-07
"""

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Setup - leverage seaborn's context and style system
sns.set_context("talk", rc={"axes.titlesize": 24, "axes.labelsize": 20, "xtick.labelsize": 16, "ytick.labelsize": 14})
sns.set_style("white", rc={"axes.edgecolor": "#cccccc", "axes.linewidth": 0.5})

# MIDI helpers
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BLACK_KEY_INDICES = {1, 3, 6, 8, 10}
WHITE_KEY_NAMES = {"C", "D", "E", "F", "G", "A", "B"}

# Data - A chord progression (C - Am - F - G) with melody over 8 measures
np.random.seed(42)

notes_data = []

# Chord progression pattern with inversions for voice leading
chords = {
    "C": [48, 52, 55, 60, 64, 67],  # C3, E3, G3, C4, E4, G4
    "Am": [48, 52, 57, 60, 64],  # C3, E3, A3, C4, E4
    "F": [48, 53, 57, 60, 65],  # C3, F3, A3, C4, F4
    "G": [47, 50, 55, 59, 62],  # B2, D3, G3, B3, D4
}
progression = ["C", "Am", "F", "G"]

# Add chord tones across 8 measures (32 beats in 4/4 time)
# Vary voicing and dynamics per measure for storytelling
chord_velocity_contour = [55, 50, 48, 52, 60, 45, 65, 42]  # dynamic arc: builds M5/M7

for measure in range(8):
    chord_name = progression[measure % 4]
    pitches = chords[chord_name]
    beat_offset = measure * 4
    base_vel = chord_velocity_contour[measure]

    for pitch in pitches:
        velocity = base_vel + np.random.randint(-5, 8)
        velocity = np.clip(velocity, 35, 70)
        # Whole notes for sustained chords
        notes_data.append({"start": beat_offset, "duration": 4.0, "pitch": pitch, "velocity": int(velocity)})

# Melody line with expressive dynamics and articulation variety
melody = [
    # M1: ascending phrase, accented downbeat
    (0, 0.5, 72, 110),
    (0.5, 0.5, 74, 90),
    (1.0, 1.0, 76, 115),
    (2.0, 0.5, 77, 85),
    (2.5, 0.5, 76, 80),
    (3.0, 1.0, 74, 90),
    # M2: descending with syncopation + staccato
    (4, 0.5, 72, 105),
    (4.5, 0.25, 71, 85),  # staccato
    (5.0, 1.0, 69, 120),  # accented syncopation
    (6.0, 0.5, 67, 80),
    (6.75, 0.25, 69, 75),  # grace note
    (7.0, 1.0, 71, 95),
    # M3: building intensity with legato
    (8, 1.5, 72, 110),
    (9.5, 0.5, 74, 95),
    (10.0, 1.5, 76, 120),  # sustained, loud
    (11.5, 0.5, 77, 100),
    # M4: gentle descent, diminuendo
    (12, 0.5, 74, 95),
    (12.5, 0.5, 72, 85),
    (13.0, 1.0, 69, 80),
    (14.0, 0.5, 67, 70),
    (14.5, 0.5, 69, 75),
    (15.0, 1.0, 71, 85),
    # M5: dramatic leap and fortissimo
    (16, 0.5, 72, 100),
    (16.5, 0.5, 74, 105),
    (17.0, 2.0, 79, 127),  # fortissimo peak - longer sustain
    (19.0, 1.0, 76, 90),
    # M6: softer, reflective - wider intervals
    (20, 1.5, 74, 70),
    (21.5, 0.5, 69, 60),
    (22.0, 1.5, 72, 65),
    (23.5, 0.5, 71, 55),
    # M7: crescendo to second climax
    (24, 0.5, 72, 90),
    (24.5, 0.5, 74, 100),
    (25.0, 1.0, 76, 115),
    (26.0, 0.75, 79, 125),  # climax
    (26.75, 0.25, 80, 110),  # ornament at top
    (27.0, 1.0, 76, 100),
    # M8: resolving, ritardando + diminuendo
    (28, 2.0, 72, 95),  # longer notes = slowing down
    (30.0, 1.0, 69, 60),
    (31.0, 1.0, 60, 45),  # final note drops to C4, very soft
]

for start, dur, pitch, vel in melody:
    notes_data.append({"start": start, "duration": dur, "pitch": pitch, "velocity": vel})

df = pd.DataFrame(notes_data)

# Pitch range with margin
pitch_min = df["pitch"].min() - 1
pitch_max = df["pitch"].max() + 1
pitches = list(range(pitch_min, pitch_max + 1))
n_pitches = len(pitches)

# Create a time-pitch matrix for heatmap (resolution: 0.25 beats = sixteenth notes)
resolution = 0.25
total_beats = 32
n_steps = int(total_beats / resolution)
matrix = np.full((n_pitches, n_steps), np.nan)

for _, row in df.iterrows():
    pitch_idx = int(row["pitch"]) - pitch_min
    start_step = int(row["start"] / resolution)
    end_step = int((row["start"] + row["duration"]) / resolution)
    end_step = min(end_step, n_steps)
    for t in range(start_step, end_step):
        existing = matrix[pitch_idx, t]
        if np.isnan(existing) or row["velocity"] > existing:
            matrix[pitch_idx, t] = row["velocity"]

# Flip so highest pitch is at the top
matrix_flipped = matrix[::-1]
pitches_flipped = pitches[::-1]

# Build pitch labels - show only white keys to reduce y-axis density
pitch_labels = []
for p in pitches_flipped:
    name = NOTE_NAMES[p % 12]
    octave = p // 12 - 1
    if name in WHITE_KEY_NAMES:
        pitch_labels.append(f"{name}{octave}")
    else:
        pitch_labels.append("")

# Build time positions for x-axis
# Custom colormap: deep navy through violet to warm coral/crimson
cmap = mcolors.LinearSegmentedColormap.from_list(
    "piano_velocity", ["#1a2a6c", "#6a4c93", "#b5446e", "#e85d4a", "#fdcb6e"], N=256
)

# Black key row mask for background shading
black_key_mask = np.array([p % 12 in BLACK_KEY_INDICES for p in pitches_flipped])

# Create DataFrame for seaborn with proper index
heatmap_df = pd.DataFrame(matrix_flipped, index=pitch_labels)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw background shading for black keys
for i, is_black in enumerate(black_key_mask):
    if is_black:
        ax.axhspan(i, i + 1, color="#f0ede8", zorder=0)

# Use seaborn heatmap with sns.color_palette for distinctive feature usage
sns.heatmap(
    heatmap_df,
    ax=ax,
    cmap=cmap,
    vmin=35,
    vmax=127,
    cbar_kws={"label": "Velocity (MIDI 0–127)", "shrink": 0.75, "aspect": 25, "pad": 0.03},
    xticklabels=False,
    yticklabels=1,
    linewidths=0,
    mask=np.isnan(matrix_flipped),
    square=False,
)

# Beat grid lines with hierarchical styling
for beat in range(total_beats + 1):
    x_pos = beat / resolution
    if beat % 4 == 0:
        ax.axvline(x_pos, color="#555555", linewidth=1.4, alpha=0.5, zorder=3)
    elif beat % 2 == 0:
        ax.axvline(x_pos, color="#aaaaaa", linewidth=0.6, alpha=0.25, zorder=3)
    else:
        ax.axvline(x_pos, color="#cccccc", linewidth=0.3, alpha=0.15, zorder=3)

# Horizontal grid lines for pitch grouping (one per octave at C notes)
for i, p in enumerate(pitches_flipped):
    if p % 12 == 0:  # C notes = octave boundaries
        ax.axhline(i, color="#888888", linewidth=0.8, alpha=0.3, zorder=3)

# X-axis: measure labels centered in each measure
measure_positions = [int(b / resolution) for b in range(0, total_beats, 4)]
ax.set_xticks([pos + 2 / resolution for pos in measure_positions])
ax.set_xticklabels([f"M{i + 1}" for i in range(len(measure_positions))], fontsize=16)

# Y-axis: show labels at every position but only non-empty ones are visible
ax.tick_params(axis="y", labelsize=14, length=0, pad=4)
ax.tick_params(axis="x", length=0, pad=8)

# Colorbar styling - explicit 16pt tick size
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=16)
cbar.set_label("Velocity (MIDI 0–127)", fontsize=18, labelpad=10)
cbar.outline.set_visible(False)

# Add dynamic region annotations for storytelling
# Place ff above the fortissimo peak in M5, pp above the soft passage in M6
ff_y = pitches_flipped.index(max(p for p in pitches_flipped if p <= 79)) - 1.2
pp_y = pitches_flipped.index(max(p for p in pitches_flipped if p <= 74)) - 1.2
ax.annotate(
    "ff",
    xy=(17.5 / resolution, ff_y),
    fontsize=15,
    fontweight="bold",
    color="#c0392b",
    ha="center",
    va="bottom",
    alpha=0.9,
)
ax.annotate(
    "pp",
    xy=(22 / resolution, pp_y),
    fontsize=15,
    fontstyle="italic",
    color="#1a2a6c",
    ha="center",
    va="bottom",
    alpha=0.8,
)

# Labels and title
ax.set_xlabel("Measure (4/4 time)", fontsize=20, labelpad=10)
ax.set_ylabel("Pitch", fontsize=20, labelpad=10)
ax.set_title("piano-roll-midi · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=18, color="#2c2c2c")

# Remove spines for clean look
sns.despine(ax=ax, left=True, bottom=True)

# Add a subtle legend for dynamic markings
ff_patch = mpatches.Patch(color="#e85d4a", alpha=0.7, label="Loud (ff)")
pp_patch = mpatches.Patch(color="#1a2a6c", alpha=0.7, label="Soft (pp)")
ax.legend(
    handles=[pp_patch, ff_patch],
    loc="upper right",
    fontsize=14,
    frameon=True,
    facecolor="white",
    edgecolor="#cccccc",
    framealpha=0.9,
    borderpad=0.6,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
