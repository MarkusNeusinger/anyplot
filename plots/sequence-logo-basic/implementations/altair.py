"""pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: altair 6.0.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-06
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
                "is_core": 2 <= position <= 9,
            }
        )
        y_start += height

df = pd.DataFrame(rows)

# Standard DNA colors per spec (A=green, C=blue, G=orange/yellow, T=red)
nuc_colors = ["#228B22", "#1f77b4", "#F5A623", "#CC3311"]
color_scale = alt.Scale(domain=["A", "C", "G", "T"], range=nuc_colors)

# Shared axis configs
x_axis = alt.X(
    "position:O",
    title="Position",
    axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0, tickSize=0, domainWidth=0, titlePadding=16),
)
y_scale = alt.Scale(domain=[0, 2.0])

# Stacked bars with conditional opacity: core positions more vivid
bars = (
    alt.Chart(df)
    .mark_rect(stroke="#ffffff", strokeWidth=0.8, cornerRadius=1)
    .encode(
        x=x_axis,
        y=alt.Y(
            "y_start:Q",
            title="Information Content (bits)",
            scale=y_scale,
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                grid=True,
                gridColor="#e0e4e8",
                gridWidth=0.5,
                gridDash=[4, 4],
                tickSize=0,
                domainWidth=0,
                titlePadding=16,
                values=[0, 0.5, 1.0, 1.5, 2.0],
            ),
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
                titlePadding=8,
                padding=16,
            ),
        ),
        opacity=alt.condition(alt.datum.is_core, alt.value(1.0), alt.value(0.5)),
        tooltip=[
            alt.Tooltip("position:O", title="Position"),
            alt.Tooltip("letter:N", title="Nucleotide"),
            alt.Tooltip("height:Q", title="Height (bits)", format=".3f"),
            alt.Tooltip("ic:Q", title="Total IC (bits)", format=".3f"),
        ],
    )
)

# Letter labels scaled by bar height via calculated transform
labels = (
    alt.Chart(df)
    .transform_filter(alt.datum.height > 0.12)
    .transform_calculate(
        font_size="max(18, min(64, datum.height * 55))", text_color="datum.letter == 'G' ? '#222222' : 'white'"
    )
    .mark_text(fontWeight="bold", baseline="middle")
    .encode(
        x="position:O",
        y=alt.Y("y_mid:Q", scale=y_scale),
        text="letter:N",
        size=alt.Size("font_size:Q", scale=None, legend=None),
        color=alt.Color("text_color:N", scale=None, legend=None),
    )
)

# Core annotation: bracket label at top of chart
core_annotation_df = pd.DataFrame(
    [{"position": 5, "y_val": 1.92, "label": "\u2190 CCGGAAGT core (pos 2\u20139) \u2192"}]
)

core_annotation = (
    alt.Chart(core_annotation_df)
    .mark_text(fontSize=16, color="#667788", fontStyle="italic")
    .encode(x="position:O", y=alt.Y("y_val:Q", scale=y_scale), text="label:N")
)

# Combine layers
chart = (
    alt.layer(bars, labels, core_annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "sequence-logo-basic \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="middle",
            subtitle="ETS-family transcription factor binding motif (CCGGAAGT core)",
            subtitleFontSize=18,
            subtitleColor="#667788",
            offset=16,
        ),
    )
    .configure_view(strokeWidth=0, fill="#fafbfc")
    .configure_axis(domainColor="#cccccc", tickColor="#cccccc", labelColor="#444444", titleColor="#333333")
    .configure(padding={"left": 24, "right": 24, "top": 20, "bottom": 20})
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
