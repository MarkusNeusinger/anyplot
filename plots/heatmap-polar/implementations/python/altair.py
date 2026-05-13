""" anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-13
"""

import os
import sys


# Prevent the local altair.py from shadowing the installed library
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — monthly energy consumption (kWh) across five years
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
years = [2019, 2020, 2021, 2022, 2023]
n_months = len(months)
n_years = len(years)

rows = []
for yi, year in enumerate(years):
    for mi, month in enumerate(months):
        winter = 75 * np.exp(-min(mi**2, (12 - mi) ** 2) / 3.5)
        summer = 45 * np.exp(-((mi - 6.5) ** 2) / 5.0)
        trend = yi * 9
        noise = np.random.normal(0, 10)
        value = round(max(80, 155 + winter + summer + trend + noise), 1)

        rows.append(
            {
                "month": month,
                "year": str(year),
                "value": value,
                "theta": mi * 2 * np.pi / n_months,
                "theta2": (mi + 1) * 2 * np.pi / n_months,
                "r_inner": 100 + yi * 85,
                "r_outer": 100 + (yi + 1) * 85,
            }
        )

df = pd.DataFrame(rows)

# Month label positions (just outside outermost ring at r=525)
month_label_df = pd.DataFrame(
    [
        {"label": month, "theta_mid": (mi + 0.5) * 2 * np.pi / n_months, "r_label": 555}
        for mi, month in enumerate(months)
    ]
)

# Year label positions (near 11 o'clock, in the gap between rings)
year_label_df = pd.DataFrame(
    [
        {"label": str(year), "theta_mid": 2 * np.pi - np.pi / 6, "r_label": 100 + (yi + 0.5) * 85}
        for yi, year in enumerate(years)
    ]
)

# Arc heatmap cells
arc = (
    alt.Chart(df)
    .mark_arc(stroke=PAGE_BG, strokeWidth=0.8)
    .encode(
        theta=alt.Theta("theta:Q", scale=alt.Scale(type="identity")),
        theta2=alt.Theta2("theta2:Q"),
        radius=alt.Radius("r_outer:Q", scale=alt.Scale(type="identity")),
        radius2=alt.Radius2("r_inner:Q"),
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(
                title="kWh / month",
                titleFontSize=18,
                labelFontSize=16,
                fillColor=ELEVATED_BG,
                labelColor=INK_SOFT,
                titleColor=INK,
                strokeColor=INK_SOFT,
                orient="right",
                offset=20,
            ),
        ),
        tooltip=[
            alt.Tooltip("month:N", title="Month"),
            alt.Tooltip("year:N", title="Year"),
            alt.Tooltip("value:Q", title="kWh", format=".0f"),
        ],
    )
)

# Month labels around the perimeter
month_labels = (
    alt.Chart(month_label_df)
    .mark_text(fontSize=18, fontWeight="bold", align="center", baseline="middle", color=INK_SOFT)
    .encode(
        theta=alt.Theta("theta_mid:Q", scale=alt.Scale(type="identity")),
        radius=alt.Radius("r_label:Q", scale=alt.Scale(type="identity")),
        text="label:N",
    )
)

# Year labels near 11 o'clock, one per ring
year_labels = (
    alt.Chart(year_label_df)
    .mark_text(fontSize=16, align="center", baseline="middle", color=INK_SOFT)
    .encode(
        theta=alt.Theta("theta_mid:Q", scale=alt.Scale(type="identity")),
        radius=alt.Radius("r_label:Q", scale=alt.Scale(type="identity")),
        text="label:N",
    )
)

chart = (
    (arc + month_labels + year_labels)
    .properties(
        width=1200,
        height=1200,
        background=PAGE_BG,
        title=alt.Title("heatmap-polar · altair · anyplot.ai", fontSize=28, color=INK, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
