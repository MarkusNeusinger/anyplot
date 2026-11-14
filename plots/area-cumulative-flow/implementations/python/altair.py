"""anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-14
"""

import os
import sys


sys.path.pop(0)  # remove script dir so 'import altair' finds the installed package

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

# Imprint palette: all eight positions, one per stage in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
STAGE = "Workflow stage"  # role: stage
COUNT = "Cumulative items"  # role: count

# Data: replace this block with your own table, for example df = pd.read_csv("flow.csv")
# One row per date and stage: the cumulative number of items that have entered or passed that stage.
# Rows come in workflow order, earliest stage first.
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-02", periods=n_days, freq="D")

# Development is the bottleneck: its band widens over time
done = np.cumsum(np.random.poisson(0.75, n_days))
testing = np.maximum(done + np.round(np.linspace(4, 8, n_days) + np.random.normal(0, 0.8, n_days)), done)
development = np.maximum(testing + np.round(np.linspace(8, 18, n_days) + np.random.normal(0, 1.2, n_days)), testing)
analysis = np.maximum(development + np.round(np.linspace(4, 7, n_days) + np.random.normal(0, 0.8, n_days)), development)
backlog = np.maximum(analysis + np.round(np.linspace(12, 16, n_days) + np.random.normal(0, 1.0, n_days)), analysis)

df = pd.concat(
    [
        pd.DataFrame({DATE: dates, STAGE: stage, COUNT: np.maximum.accumulate(values).astype(int)})
        for stage, values in [
            ("Backlog", backlog),
            ("Analysis", analysis),
            ("Development", development),
            ("Testing", testing),
            ("Done", done),
        ]
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
WIP = "Items in stage"

# Cumulative counts become items in each stage: the gap to the next stage in the workflow
stages = list(df[STAGE].unique())
cumulative = df.pivot_table(index=DATE, columns=STAGE, values=COUNT, sort=False)[stages]
in_stage = cumulative - cumulative.shift(-1, axis=1).fillna(0)
flow = in_stage.reset_index().melt(id_vars=DATE, var_name=STAGE, value_name=WIP)

# Done (the last stage) is drawn at the bottom and takes the first palette color
stage_color = {stage: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, stage in enumerate(reversed(stages))}
stack_position = {stage: i for i, stage in enumerate(reversed(stages))}
flow["stack_order"] = flow[STAGE].map(stack_position)

chart = (
    alt.Chart(flow)
    .mark_area(interpolate="monotone")
    .encode(
        x=alt.X(
            DATE.translate(ESCAPE), type="temporal", title=DATE, axis=alt.Axis(format="%b %Y", tickCount=6, grid=False)
        ),
        y=alt.Y(WIP.translate(ESCAPE), type="quantitative", title=COUNT, stack="zero"),
        color=alt.Color(
            STAGE.translate(ESCAPE),
            type="nominal",
            title=STAGE,
            sort=stages,
            scale=alt.Scale(domain=stages, range=[stage_color[s] for s in stages]),
            legend=alt.Legend(orient="right"),
        ),
        order=alt.Order("stack_order", type="quantitative"),
    )
    .properties(
        width=620,
        height=320,
        title=alt.Title("area-cumulative-flow · python · altair · anyplot.ai", fontSize=16),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_title(color=INK, fontSize=16)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=11,
        labelFontSize=10,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Fit (never crop) the PNG into the 3200 x 1800 canvas, padding what is left
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    img.thumbnail((TARGET_W, TARGET_H), Image.LANCZOS)  # a table with many stages widens the legend
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
