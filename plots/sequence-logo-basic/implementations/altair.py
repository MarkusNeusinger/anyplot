""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: altair 6.0.0 | Python 3.14.3
Quality: 71/100 | Created: 2026-03-06
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - ETS-family transcription factor binding motif (CCGGAAGT core)
np.random.seed(42)

frequencies = [
    {"A": 0.30, "C": 0.25, "G": 0.20, "T": 0.25},
    {"A": 0.05, "C": 0.80, "G": 0.05, "T": 0.10},
    {"A": 0.02, "C": 0.02, "G": 0.94, "T": 0.02},
    {"A": 0.02, "C": 0.02, "G": 0.94, "T": 0.02},
    {"A": 0.90, "C": 0.03, "G": 0.04, "T": 0.03},
    {"A": 0.85, "C": 0.05, "G": 0.05, "T": 0.05},
    {"A": 0.10, "C": 0.10, "G": 0.15, "T": 0.65},
    {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},
    {"A": 0.10, "C": 0.10, "G": 0.10, "T": 0.70},
    {"A": 0.20, "C": 0.30, "G": 0.20, "T": 0.30},
]

rows = []
for pos_idx, freqs in enumerate(frequencies):
    position = pos_idx + 1
    entropy = -sum(f * np.log2(f) for f in freqs.values() if f > 0)
    ic = 2.0 - entropy

    sorted_letters = sorted(freqs.items(), key=lambda x: x[1])
    y_start = 0.0
    for letter, freq in sorted_letters:
        height = ic * freq
        if height > 0.005:
            rows.append(
                {
                    "position": position,
                    "letter": letter,
                    "height": height,
                    "y_start": round(y_start, 6),
                    "y_end": round(y_start + height, 6),
                    "y_mid": round(y_start + height / 2, 6),
                    "label": letter if height > 0.25 else "",
                }
            )
            y_start += height

df = pd.DataFrame(rows)

# Color mapping (standard DNA: A=green, C=blue, G=orange, T=red)
color_scale = alt.Scale(domain=["A", "C", "G", "T"], range=["#109648", "#255C99", "#F7B32B", "#D62839"])

# Bars
bars = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X("position:O", title="Position"),
        y=alt.Y("y_start:Q", title="Information Content (bits)", scale=alt.Scale(domain=[0, 2])),
        y2="y_end:Q",
        color=alt.Color("letter:N", scale=color_scale, legend=None),
    )
)

# Labels on dominant bars only (empty string for small bars)
labels = (
    alt.Chart(df)
    .mark_text(fontSize=70, fontWeight="bold", color="white")
    .encode(x="position:O", y="y_mid:Q", text="label:N")
)

# Combine
chart = (
    (bars + labels)
    .properties(width=1600, height=900, title=alt.Title("sequence-logo-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, labelAngle=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
