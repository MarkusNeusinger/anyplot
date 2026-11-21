"""anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TARGET_SIZE = (3200, 1800)
SCALE_FACTOR = 4.0

# Columns
PETAL_LENGTH = "Petal Length (cm)"  # role: x
PETAL_WIDTH = "Petal Width (cm)"  # role: y
SPECIES = "Species"  # role: category

# Data - Iris-like measurements by species
np.random.seed(42)
n_per_species = 50
species_names = ["Setosa", "Versicolor", "Virginica"]
base_length = [1.4, 4.2, 5.5]
base_width = [0.2, 1.3, 2.0]
spread = [0.2, 0.5, 0.6]

frames = []
for i, species in enumerate(species_names):
    frames.append(
        pd.DataFrame(
            {
                PETAL_LENGTH: np.random.normal(base_length[i], spread[i], n_per_species),
                PETAL_WIDTH: np.random.normal(base_width[i], spread[i] * 0.5, n_per_species),
                SPECIES: species,
            }
        )
    )
df = pd.concat(frames, ignore_index=True)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
categories = list(df[SPECIES].unique())

chart = (
    alt.Chart(df)
    .mark_point(size=90, opacity=0.75, filled=True, stroke=PAGE_BG, strokeWidth=0.8)
    .encode(
        x=alt.X(PETAL_LENGTH.translate(ESCAPE), type="quantitative", title=PETAL_LENGTH, scale=alt.Scale(zero=False)),
        y=alt.Y(PETAL_WIDTH.translate(ESCAPE), type="quantitative", title=PETAL_WIDTH, scale=alt.Scale(zero=False)),
        color=alt.Color(
            SPECIES.translate(ESCAPE),
            type="nominal",
            title=SPECIES,
            sort=None,
            scale=alt.Scale(domain=categories, range=IMPRINT_PALETTE),
        ),
        shape=alt.Shape(
            SPECIES.translate(ESCAPE),
            type="nominal",
            title=SPECIES,
            sort=None,
            scale=alt.Scale(domain=categories, range=["circle", "square", "triangle-up"]),
        ),
        tooltip=[
            alt.Tooltip(SPECIES.translate(ESCAPE), title=SPECIES),
            alt.Tooltip(PETAL_LENGTH.translate(ESCAPE), title=PETAL_LENGTH),
            alt.Tooltip(PETAL_WIDTH.translate(ESCAPE), title=PETAL_WIDTH),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("scatter-categorical · python · altair · anyplot.ai", fontSize=16),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=11,
        titleColor=INK,
        titleFontSize=13,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=13,
        symbolSize=90,
        padding=6,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=SCALE_FACTOR)
chart.save(f"plot-{THEME}.html")

# Fit to the exact canvas: shrink if the chart overshoots, then pad (never crop)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_SIZE[0] or img.height > TARGET_SIZE[1]:
    ratio = min(TARGET_SIZE[0] / img.width, TARGET_SIZE[1] / img.height)
    img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
if img.size != TARGET_SIZE:
    canvas = Image.new("RGB", TARGET_SIZE, PAGE_BG)
    canvas.paste(img, ((TARGET_SIZE[0] - img.width) // 2, (TARGET_SIZE[1] - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
