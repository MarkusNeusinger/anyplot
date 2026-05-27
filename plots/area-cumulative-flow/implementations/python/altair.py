""" anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-07
"""

import os
import sys


sys.path.pop(0)  # remove script dir so 'import altair' finds the installed package

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — 90-day software delivery Kanban board
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-02", periods=n_days, freq="D")

# Cumulative items that have reached each stage (monotonically non-decreasing)
# Workflow order: Backlog → Analysis → Development → Testing → Done
done = np.cumsum(np.random.poisson(0.75, n_days))

testing_cum = done + np.round(np.linspace(4, 8, n_days) + np.random.normal(0, 0.8, n_days))
testing_cum = np.maximum.accumulate(testing_cum.clip(0).astype(int))
testing_cum = np.maximum(testing_cum, done)

# Development is the bottleneck — band widens over time
dev_cum = testing_cum + np.round(np.linspace(8, 18, n_days) + np.random.normal(0, 1.2, n_days))
dev_cum = np.maximum.accumulate(dev_cum.clip(0).astype(int))
dev_cum = np.maximum(dev_cum, testing_cum)

analysis_cum = dev_cum + np.round(np.linspace(4, 7, n_days) + np.random.normal(0, 0.8, n_days))
analysis_cum = np.maximum.accumulate(analysis_cum.clip(0).astype(int))
analysis_cum = np.maximum(analysis_cum, dev_cum)

backlog_cum = analysis_cum + np.round(np.linspace(12, 16, n_days) + np.random.normal(0, 1.0, n_days))
backlog_cum = np.maximum.accumulate(backlog_cum.clip(0).astype(int))
backlog_cum = np.maximum(backlog_cum, analysis_cum)

# Decompose into WIP per stage (stacked from bottom: Done → Backlog)
stages = ["Done", "Testing", "Development", "Analysis", "Backlog"]
wip_arrays = [done, testing_cum - done, dev_cum - testing_cum, analysis_cum - dev_cum, backlog_cum - analysis_cum]

records = []
for stage, wip in zip(stages, wip_arrays, strict=True):
    for i, d in enumerate(dates):
        records.append({"date": d, "stage": stage, "wip": int(wip[i])})

df = pd.DataFrame(records)
df["stack_order"] = df["stage"].map({s: i for i, s in enumerate(stages)})

# Plot
base = (
    alt.Chart(df)
    .mark_area(interpolate="monotone")
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y", tickCount=6)),
        y=alt.Y("wip:Q", stack="zero", title="Cumulative Items"),
        color=alt.Color(
            "stage:N",
            scale=alt.Scale(domain=stages, range=IMPRINT),
            legend=alt.Legend(title="Workflow Stage", orient="top-left"),
        ),
        order=alt.Order("stack_order:Q"),
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title("area-cumulative-flow · altair · anyplot.ai", fontSize=28),
        background=PAGE_BG,
    )
)

chart = (
    base.configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_title(color=INK, fontSize=28)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=18,
        labelFontSize=16,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
