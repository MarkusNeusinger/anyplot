""" anyplot.ai
swarm-basic: Basic Swarm Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-05
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Employee performance scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
n_per_dept = [45, 38, 52, 35]

data = []
for dept, n in zip(departments, n_per_dept, strict=True):
    if dept == "Engineering":
        scores = np.random.normal(78, 8, n)
    elif dept == "Marketing":
        scores = np.random.normal(72, 12, n)
    elif dept == "Sales":
        scores = np.concatenate([np.random.normal(65, 6, n // 2), np.random.normal(82, 5, n - n // 2)])
    else:  # HR
        scores = np.concatenate([np.random.normal(68, 9, n - 3), np.array([45, 92, 95])])
    scores = np.clip(scores, 30, 100)
    for score in scores:
        data.append({"Department": dept, "Performance Score": score})

df = pd.DataFrame(data)

# Numeric x position per department
dept_positions = {dept: i for i, dept in enumerate(departments)}
df["x_pos"] = df["Department"].map(dept_positions)

# Calculate means
means = df.groupby("Department")["Performance Score"].mean().reset_index()
means["x_pos"] = means["Department"].map(dept_positions)

# Swarm points — use Altair's transform_calculate with random() for native jitter
swarm = (
    alt.Chart(df)
    .mark_circle(size=180, opacity=0.75)
    .encode(
        x=alt.X(
            "x_jitter:Q",
            scale=alt.Scale(domain=[-0.7, 3.7]),
            axis=alt.Axis(
                values=list(range(4)),
                labelExpr="['Engineering', 'Marketing', 'Sales', 'HR'][datum.value]",
                title="Department",
                labelFontSize=18,
                titleFontSize=22,
                labelAngle=0,
            ),
        ),
        y=alt.Y(
            "Performance Score:Q", scale=alt.Scale(domain=[25, 105]), axis=alt.Axis(labelFontSize=18, titleFontSize=22)
        ),
        color=alt.Color(
            "Department:N",
            scale=alt.Scale(domain=departments, range=OKABE_ITO),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, orient="right"),
        ),
        tooltip=["Department", "Performance Score"],
    )
    .transform_calculate(x_jitter="datum.x_pos + (random() - 0.5) * 0.55")
)

# Mean diamond markers (theme-adaptive color)
mean_markers = (
    alt.Chart(means)
    .mark_point(shape="diamond", size=400, filled=True, color=INK, strokeWidth=2)
    .encode(
        x="x_pos:Q",
        y="Performance Score:Q",
        tooltip=[alt.Tooltip("Department"), alt.Tooltip("Performance Score:Q", title="Mean", format=".1f")],
    )
)

# Mean reference lines (theme-adaptive color)
mean_lines = (
    alt.Chart(means)
    .mark_rule(color=INK, strokeWidth=2, strokeDash=[4, 4])
    .encode(x=alt.X("x_start:Q"), x2="x_end:Q", y="Performance Score:Q")
    .transform_calculate(x_start="datum.x_pos - 0.35", x_end="datum.x_pos + 0.35")
)

# Compose and apply theme-adaptive chrome
chart = (
    (swarm + mean_lines + mean_markers)
    .properties(
        width=1400,
        height=800,
        background=PAGE_BG,
        title=alt.Title("swarm-basic · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
