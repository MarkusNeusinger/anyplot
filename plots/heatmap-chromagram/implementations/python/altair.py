""" anyplot.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: altair 6.2.2 | Python 3.13.14
Quality: 85/100 | Updated: 2026-06-24
"""

import importlib
import os
import sys


# Remove script directory from sys.path so `altair` resolves to the package, not this file
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")
Image = importlib.import_module("PIL.Image")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential colormap for continuous single-polarity energy data
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Data - simulate a chromagram with chord progressions
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 120
time_seconds = np.linspace(0, 24, n_frames)
frame_width = time_seconds[1] - time_seconds[0]

# Chord templates (relative energy per pitch class)
c_major = np.array([1.0, 0.0, 0.1, 0.0, 0.8, 0.1, 0.0, 0.7, 0.0, 0.05, 0.0, 0.05])
g_major = np.array([0.1, 0.0, 0.15, 0.0, 0.05, 0.1, 0.0, 1.0, 0.0, 0.05, 0.0, 0.7])
a_minor = np.array([0.7, 0.0, 0.1, 0.0, 0.8, 0.1, 0.0, 0.05, 0.0, 1.0, 0.0, 0.05])
f_major = np.array([0.8, 0.0, 0.05, 0.0, 0.1, 1.0, 0.0, 0.05, 0.0, 0.7, 0.0, 0.05])

# Build chromagram: cycle through C -> G -> Am -> F progression
energy = np.zeros((12, n_frames))
chord_sequence = [c_major, g_major, a_minor, f_major]
frames_per_chord = n_frames // len(chord_sequence)

for i, chord in enumerate(chord_sequence):
    start = i * frames_per_chord
    end = start + frames_per_chord if i < len(chord_sequence) - 1 else n_frames
    for j in range(start, end):
        blend = np.random.uniform(0.7, 1.0)
        noise = np.random.uniform(0.0, 0.15, 12)
        energy[:, j] = chord * blend + noise

# Smooth transitions between chords
for i in range(1, n_frames):
    energy[:, i] = 0.7 * energy[:, i] + 0.3 * energy[:, i - 1]

# Normalize to 0-1
energy = energy / energy.max()

# Build long-form dataframe with bin edges for proper rect rendering
rows = []
for t_idx, t_val in enumerate(time_seconds):
    for p_idx, pitch in enumerate(pitch_classes):
        rows.append(
            {
                "t1": round(t_val, 3),
                "t2": round(t_val + frame_width, 3),
                "Pitch Class": pitch,
                "Energy": round(energy[p_idx, t_idx], 3),
            }
        )

df = pd.DataFrame(rows)

# Plot
title_text = "heatmap-chromagram · python · altair · anyplot.ai"

heatmap = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X(
            "t1:Q",
            title="Time (seconds)",
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, titlePadding=12, values=list(range(0, 25, 2))),
            scale=alt.Scale(domain=[0, 24.2]),
        ),
        x2="t2:Q",
        y=alt.Y(
            "Pitch Class:N",
            title="Pitch Class",
            sort=pitch_classes,
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, titlePadding=12),
        ),
        color=alt.Color(
            "Energy:Q",
            scale=alt.Scale(range=IMPRINT_SEQ),
            legend=alt.Legend(
                title="Energy",
                titleFontSize=16,
                labelFontSize=14,
                gradientLength=320,
                gradientThickness=16,
                titlePadding=8,
                offset=10,
                direction="vertical",
            ),
        ),
        tooltip=[
            alt.Tooltip("Pitch Class:N"),
            alt.Tooltip("t1:Q", title="Time (s)", format=".1f"),
            alt.Tooltip("Energy:Q", format=".3f"),
        ],
    )
)

chart = (
    heatmap.properties(
        width=420,
        height=440,
        background=PAGE_BG,
        title=alt.Title(
            title_text,
            subtitle="Pitch class energy · C → G → Am → F chord progression",
            fontSize=16,
            subtitleFontSize=12,
            color=INK,
            subtitleColor=INK_MUTED,
            anchor="start",
            offset=16,
        ),
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0, continuousWidth=420, continuousHeight=440)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, grid=False, labelColor=INK_SOFT, titleColor=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG then pad to exact canonical target (2400 × 2400 — square for heatmaps)
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 2400, 2400
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
