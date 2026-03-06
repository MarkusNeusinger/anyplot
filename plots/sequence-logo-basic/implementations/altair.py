"""pyplots.ai
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
    {"A": 0.30, "C": 0.25, "G": 0.20, "T": 0.25},  # pos 1: low conservation
    {"A": 0.05, "C": 0.80, "G": 0.05, "T": 0.10},  # pos 2: C dominant
    {"A": 0.02, "C": 0.02, "G": 0.94, "T": 0.02},  # pos 3: G highly conserved
    {"A": 0.02, "C": 0.02, "G": 0.94, "T": 0.02},  # pos 4: G highly conserved
    {"A": 0.90, "C": 0.03, "G": 0.04, "T": 0.03},  # pos 5: A dominant
    {"A": 0.85, "C": 0.05, "G": 0.05, "T": 0.05},  # pos 6: A dominant
    {"A": 0.10, "C": 0.10, "G": 0.15, "T": 0.65},  # pos 7: T dominant
    {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},  # pos 8: no conservation
    {"A": 0.10, "C": 0.10, "G": 0.10, "T": 0.70},  # pos 9: T dominant
    {"A": 0.20, "C": 0.30, "G": 0.20, "T": 0.30},  # pos 10: slight C/T bias
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
        rows.append(
            {
                "position": position,
                "letter": letter,
                "height": height,
                "y_start": round(y_start, 6),
                "y_end": round(y_start + height, 6),
                "y_mid": round(y_start + height / 2, 6),
                "ic": round(ic, 4),
            }
        )
        y_start += height

df = pd.DataFrame(rows)

# Standard DNA colors per spec (A=green, C=blue, G=orange/yellow, T=red)
# Using colorblind-friendly shades: teal-green and brick-red are more distinguishable
nuc_colors = ["#228B22", "#1f77b4", "#F5A623", "#CC3311"]
color_scale = alt.Scale(domain=["A", "C", "G", "T"], range=nuc_colors)

# Label threshold: only show letters when bar is tall enough to read
label_threshold = 0.15

# Stacked bars representing nucleotide heights
bars = (
    alt.Chart(df)
    .mark_rect(stroke="#ffffff", strokeWidth=0.5)
    .encode(
        x=alt.X("position:O", title="Position", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0)),
        y=alt.Y(
            "y_start:Q",
            title="Information Content (bits)",
            scale=alt.Scale(domain=[0, 2]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=True, gridColor="#e8e8e8", gridWidth=0.5),
        ),
        y2="y_end:Q",
        color=alt.Color(
            "letter:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Nucleotide",
                titleFontSize=18,
                labelFontSize=16,
                orient="right",
                symbolSize=300,
                symbolStrokeWidth=0,
            ),
        ),
        tooltip=[
            alt.Tooltip("position:O", title="Position"),
            alt.Tooltip("letter:N", title="Nucleotide"),
            alt.Tooltip("height:Q", title="Height (bits)", format=".3f"),
            alt.Tooltip("ic:Q", title="Total IC (bits)", format=".3f"),
        ],
    )
)

# Letter labels on dominant bars
df_labels = df[df["height"] > label_threshold].copy()

# White text on dark bars (A=green, C=blue, T=red), dark text on light bars (G=amber)
df_labels["text_color"] = df_labels["letter"].map({"A": "white", "C": "white", "G": "#222222", "T": "white"})

labels = (
    alt.Chart(df_labels)
    .mark_text(fontSize=56, fontWeight="bold", baseline="middle")
    .encode(
        x="position:O",
        y=alt.Y("y_mid:Q", scale=alt.Scale(domain=[0, 2])),
        text="letter:N",
        color=alt.Color("text_color:N", scale=None, legend=None),
    )
)

# Combine layers
chart = (
    (bars + labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "sequence-logo-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="middle",
            subtitle="ETS-family transcription factor binding motif (CCGGAAGT core)",
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(domainColor="#999999", tickColor="#999999", labelColor="#333333", titleColor="#333333")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
