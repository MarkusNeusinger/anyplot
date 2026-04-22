""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: altair 6.0.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-06
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
                "height": round(height, 6),
                "y_start": round(y_start, 6),
                "y_end": round(y_start + height, 6),
                "y_mid": round(y_start + height / 2, 6),
                "ic": round(ic, 4),
                "freq": round(freq, 4),
                "is_core": 2 <= position <= 9,
            }
        )
        y_start += height

df = pd.DataFrame(rows)

# Standard DNA colors per spec (A=green, C=blue, G=orange/yellow, T=red)
nuc_colors = {"A": "#2ca02c", "C": "#1f77b4", "G": "#F5A623", "T": "#d62728"}
color_scale = alt.Scale(domain=["A", "C", "G", "T"], range=list(nuc_colors.values()))

# Highlight selection: hovering a position highlights entire column
position_hover = alt.selection_point(fields=["position"], on="pointerover", empty=False)

y_scale = alt.Scale(domain=[0, 2.1])

# Stacked colored bars as letter background
bars = (
    alt.Chart(df)
    .mark_rect(cornerRadius=2)
    .encode(
        x=alt.X(
            "position:O",
            title="Position",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0, tickSize=0, domainWidth=0, titlePadding=16),
        ),
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
        opacity=alt.condition(alt.datum.is_core, alt.value(0.95), alt.value(0.45)),
        stroke=alt.condition(position_hover, alt.value("#333333"), alt.value("#ffffff")),
        strokeWidth=alt.condition(position_hover, alt.value(2.0), alt.value(0.5)),
        tooltip=[
            alt.Tooltip("position:O", title="Position"),
            alt.Tooltip("letter:N", title="Nucleotide"),
            alt.Tooltip("freq:Q", title="Frequency", format=".0%"),
            alt.Tooltip("height:Q", title="Height (bits)", format=".3f"),
            alt.Tooltip("ic:Q", title="Total IC (bits)", format=".3f"),
        ],
    )
    .add_params(position_hover)
)

# Large letter glyphs as the primary visual element
# Use transform_calculate to scale font size proportional to height, making
# letters the dominant visual rather than just labels on bars
letters = (
    alt.Chart(df)
    .transform_filter(alt.datum.height > 0.06)
    .transform_calculate(
        font_size="max(14, min(72, datum.height * 65))",
        letter_color="datum.letter == 'G' ? '#6B4400' : datum.letter == 'A' ? '#0B5B0B' : datum.letter == 'C' ? '#0A3D6B' : '#8B0000'",
    )
    .mark_text(fontWeight="bold", font="Arial Black, Impact, sans-serif", baseline="middle")
    .encode(
        x="position:O",
        y=alt.Y("y_mid:Q", scale=y_scale),
        text="letter:N",
        size=alt.Size("font_size:Q", scale=None, legend=None),
        color=alt.Color("letter_color:N", scale=None, legend=None),
        opacity=alt.condition(alt.datum.is_core, alt.value(1.0), alt.value(0.6)),
    )
)

# Core region bracket annotation at top
core_annotation_df = pd.DataFrame(
    [{"position": 5, "y_val": 2.0, "label": "\u25c0 CCGGAAGT core (pos 2\u20139) \u25b6"}]
)

core_annotation = (
    alt.Chart(core_annotation_df)
    .mark_text(fontSize=16, fontWeight="bold", color="#556677", fontStyle="italic")
    .encode(x="position:O", y=alt.Y("y_val:Q", scale=y_scale), text="label:N")
)

# Background shading for core region to strengthen storytelling
core_bg_df = pd.DataFrame([{"pos": p} for p in range(2, 10)])
core_bg = (
    alt.Chart(core_bg_df).mark_rect(color="#e8edf2", opacity=0.3).encode(x="pos:O", y=alt.value(0), y2=alt.value(900))
)

# IC summary bar at bottom: thin marks showing total information content per position
ic_summary_df = df.drop_duplicates(subset=["position"])[["position", "ic", "is_core"]].copy()

ic_ticks = (
    alt.Chart(ic_summary_df)
    .mark_tick(thickness=3, color="#556677")
    .encode(
        x="position:O",
        y=alt.Y("ic:Q", scale=y_scale),
        opacity=alt.condition(alt.datum.is_core, alt.value(0.7), alt.value(0.3)),
    )
)

# Combine layers: background shading first, then bars, letters, annotations
chart = (
    alt.layer(core_bg, bars, letters, ic_ticks, core_annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "sequence-logo-basic \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="middle",
            subtitle=[
                "ETS-family transcription factor binding motif (CCGGAAGT core)",
                "Letter height \u221d information content \u2014 taller letters = higher conservation",
            ],
            subtitleFontSize=16,
            subtitleColor="#667788",
            offset=16,
        ),
    )
    .configure_view(strokeWidth=0, fill="#fafbfd")
    .configure_axis(domainColor="#bbbbbb", tickColor="#bbbbbb", labelColor="#444444", titleColor="#333333")
    .configure(padding={"left": 24, "right": 24, "top": 20, "bottom": 20})
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
