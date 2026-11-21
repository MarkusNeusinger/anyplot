"""anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: altair 6.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-11-21
"""

import os
import sys


_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _here]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
AGE_GROUP = "Age group"  # role: x_category
EDUCATION = "Education level"  # role: y_category
SCORE = "Satisfaction score (0–100)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
rng = np.random.default_rng(42)
age_groups = ["18–24", "25–34", "35–44", "45–54", "55–64"]
base_scores = {
    "High School": [62, 68, 71, 74, 70],
    "Bachelor's": [70, 75, 78, 76, 73],
    "Master's": [74, 79, 82, 80, 77],
    "Doctorate": [76, 81, 85, 83, 79],
}
df = pd.DataFrame(
    {
        AGE_GROUP: age_groups * len(base_scores),
        EDUCATION: [edu for edu in base_scores for _ in age_groups],
        SCORE: np.round(np.concatenate(list(base_scores.values())) + rng.uniform(-1.5, 1.5, 20), 1),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
chart = (
    alt.Chart(df)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X(
            AGE_GROUP.translate(ESCAPE),
            type="nominal",
            title=AGE_GROUP,
            sort=None,
            axis=alt.Axis(labelAngle=0, labelFontSize=10, titleFontSize=12),
        ),
        xOffset=alt.XOffset(EDUCATION.translate(ESCAPE), type="nominal", sort=None),
        y=alt.Y(
            SCORE.translate(ESCAPE),
            type="quantitative",
            title=SCORE,
            scale=alt.Scale(domain=[0, df[SCORE].max() * 1.15], nice=True),
            axis=alt.Axis(labelFontSize=10, titleFontSize=12, grid=True),
        ),
        color=alt.Color(
            EDUCATION.translate(ESCAPE),
            type="nominal",
            title=EDUCATION,
            sort=None,
            scale=alt.Scale(range=IMPRINT_PALETTE),
            legend=alt.Legend(titleFontSize=11, labelFontSize=10, orient="right"),
        ),
        tooltip=[
            alt.Tooltip(AGE_GROUP.translate(ESCAPE), type="nominal", title=AGE_GROUP),
            alt.Tooltip(EDUCATION.translate(ESCAPE), type="nominal", title=EDUCATION),
            alt.Tooltip(SCORE.translate(ESCAPE), type="quantitative", title=SCORE, format=".1f"),
        ],
    )
    .properties(
        width=560,
        height=320,
        title=alt.Title("bar-3d-categorical · python · altair · anyplot.ai", fontSize=16, color=INK, anchor="start"),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
canvas = Image.new("RGB", (max(TARGET_W, img.width), max(TARGET_H, img.height)), PAGE_BG)
canvas.paste(img, ((canvas.width - img.width) // 2, (canvas.height - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
