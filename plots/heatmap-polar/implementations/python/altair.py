"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-11-22
"""

import os

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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CELL_TEXT = "#FAF8F1"  # year labels sit on the data colors, which are identical in both themes

# Columns: set these to your table's column names
MONTH = "Month"  # role: angular
YEAR = "Year"  # role: radial
ENERGY = "Energy (kWh/month)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
years = ["2019", "2020", "2021", "2022", "2023"]
values = []
for yi in range(len(years)):
    for mi in range(len(months)):
        winter = 75 * np.exp(-min(mi**2, (12 - mi) ** 2) / 3.5)
        summer = 45 * np.exp(-((mi - 6.5) ** 2) / 5.0)
        values.append(round(max(80, 155 + winter + summer + yi * 9 + np.random.normal(0, 10)), 1))
df = pd.DataFrame({MONTH: months * len(years), YEAR: np.repeat(years, len(months)), ENERGY: values})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
VIEW = 480  # inner view size in px; polar geometry below scales with it
R_HOLE = VIEW * 0.09  # empty centre so the innermost ring keeps a usable width
R_EDGE = VIEW * 0.43  # outer edge of the last ring
R_LABEL = VIEW * 0.465  # month labels just outside the rings

month_codes, month_names = pd.factorize(df[MONTH])
year_codes, year_names = pd.factorize(df[YEAR])
n_months, n_years = len(month_names), len(year_names)
ring = (R_EDGE - R_HOLE) / n_years

cells = df.assign(
    theta=month_codes * 2 * np.pi / n_months,
    theta2=(month_codes + 1) * 2 * np.pi / n_months,
    r_inner=R_HOLE + year_codes * ring,
    r_outer=R_HOLE + (year_codes + 1) * ring,
)
month_labels_df = pd.DataFrame(
    {"label": month_names, "theta": (np.arange(n_months) + 0.5) * 2 * np.pi / n_months, "r": R_LABEL}
)
# One year label per ring, stacked along the ray at 11 o'clock (centre of the last month)
year_labels_df = pd.DataFrame(
    {
        "label": year_names,
        "theta": (n_months - 0.5) * 2 * np.pi / n_months,
        "r": R_HOLE + (np.arange(n_years) + 0.5) * ring,
    }
)

identity = alt.Scale(type="identity")
arc = (
    alt.Chart(cells)
    .mark_arc(stroke=PAGE_BG, strokeWidth=0.6)
    .encode(
        theta=alt.Theta("theta", type="quantitative", scale=identity),
        theta2=alt.Theta2("theta2"),
        radius=alt.Radius("r_outer", type="quantitative", scale=identity),
        radius2=alt.Radius2("r_inner"),
        color=alt.Color(
            ENERGY.translate(ESCAPE),
            type="quantitative",
            title=ENERGY,
            scale=alt.Scale(range=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]),
            legend=alt.Legend(
                titleFontSize=14,
                labelFontSize=12,
                fillColor=ELEVATED_BG,
                labelColor=INK_SOFT,
                titleColor=INK,
                strokeColor=INK_SOFT,
                padding=8,
                orient="bottom",
                direction="horizontal",
                gradientLength=300,
                offset=14,
            ),
        ),
        tooltip=[
            alt.Tooltip(MONTH.translate(ESCAPE), type="nominal", title=MONTH),
            alt.Tooltip(YEAR.translate(ESCAPE), type="nominal", title=YEAR),
            alt.Tooltip(ENERGY.translate(ESCAPE), type="quantitative", title=ENERGY, format=".0f"),
        ],
    )
)

month_text = (
    alt.Chart(month_labels_df)
    .mark_text(fontSize=15, fontWeight="bold", align="center", baseline="middle", color=INK_SOFT)
    .encode(
        theta=alt.Theta("theta", type="quantitative", scale=identity),
        radius=alt.Radius("r", type="quantitative", scale=identity),
        text="label:N",
    )
)

year_text = (
    alt.Chart(year_labels_df)
    .mark_text(fontSize=11, fontWeight="bold", align="center", baseline="middle", color=CELL_TEXT)
    .encode(
        theta=alt.Theta("theta", type="quantitative", scale=identity),
        radius=alt.Radius("r", type="quantitative", scale=identity),
        text="label:N",
    )
)

chart = (
    (arc + month_text + year_text)
    .properties(
        width=VIEW,
        height=VIEW,
        background=PAGE_BG,
        title=alt.Title("heatmap-polar · python · altair · anyplot.ai", fontSize=20, color=INK, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the 2400 x 2400 square target
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET}x{TARGET}; shrink VIEW")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
