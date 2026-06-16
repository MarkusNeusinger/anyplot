""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: altair 6.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-13
"""

import os

import altair as alt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Wind direction frequency data
np.random.seed(42)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
angles = [0, 45, 90, 135, 180, 225, 270, 315]

# Simulate realistic wind frequency with prevailing westerlies
base_freq = [12, 8, 10, 6, 9, 18, 22, 16]
frequencies = [f + np.random.randint(-2, 3) for f in base_freq]

# Create DataFrame with angle in radians for Altair
df = pd.DataFrame({"direction": directions, "angle": angles, "frequency": frequencies})

# Calculate start and end angles for each bar (in radians)
# Altair uses radians, and we need to center each bar on its direction
bar_width = 40  # degrees
df["theta_start"] = np.radians(df["angle"] - bar_width / 2)
df["theta_end"] = np.radians(df["angle"] + bar_width / 2)

# Create the polar bar chart using mark_arc
base = alt.Chart(df)

# Bars radiating from center using arc marks
bars = base.mark_arc(stroke=INK_SOFT, strokeWidth=1.5).encode(
    theta=alt.Theta("theta_start:Q", scale=alt.Scale(domain=[0, 2 * np.pi])),
    theta2="theta_end:Q",
    radius=alt.Radius("frequency:Q", scale=alt.Scale(type="linear", zero=True, rangeMin=0)),
    color=alt.Color(
        "direction:N",
        scale=alt.Scale(range=IMPRINT),
        legend=alt.Legend(
            title="Direction",
            titleFontSize=18,
            labelFontSize=16,
            orient="right",
            fillColor=ELEVATED_BG,
            strokeColor=INK_SOFT,
        ),
    ),
    tooltip=[alt.Tooltip("direction:N", title="Direction"), alt.Tooltip("frequency:Q", title="Frequency (days)")],
)

# Add direction labels around the perimeter
max_freq = max(frequencies) * 1.25
label_df = pd.DataFrame({"direction": directions, "angle_rad": np.radians(angles), "radius": [max_freq] * 8})

# Calculate x, y positions for labels
label_df["x"] = label_df["radius"] * np.sin(label_df["angle_rad"])
label_df["y"] = label_df["radius"] * np.cos(label_df["angle_rad"])

labels = (
    alt.Chart(label_df)
    .mark_text(fontSize=20, fontWeight="bold", color=INK_SOFT)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), text="direction:N")
)

# Combine bars and labels
chart = (
    alt.layer(bars, labels)
    .properties(
        width=900,
        height=900,
        background=PAGE_BG,
        title=alt.Title(text="polar-bar · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .interactive()
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
