""" anyplot.ai
box-grouped: Grouped Box Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-08
"""

import os

import altair
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (positions 1, 2, 3 for Junior, Mid, Senior)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Employee performance scores across departments and experience levels
np.random.seed(42)

departments = ["Engineering", "Sales", "Marketing", "Support"]
experience_levels = ["Junior", "Mid", "Senior"]

data = []
# Create varied distributions for each combination
distributions = {
    ("Engineering", "Junior"): (65, 12),
    ("Engineering", "Mid"): (75, 10),
    ("Engineering", "Senior"): (85, 8),
    ("Sales", "Junior"): (55, 15),
    ("Sales", "Mid"): (70, 12),
    ("Sales", "Senior"): (80, 10),
    ("Marketing", "Junior"): (60, 14),
    ("Marketing", "Mid"): (72, 11),
    ("Marketing", "Senior"): (82, 9),
    ("Support", "Junior"): (58, 13),
    ("Support", "Mid"): (68, 12),
    ("Support", "Senior"): (78, 10),
}

for dept in departments:
    for exp in experience_levels:
        mean, std = distributions[(dept, exp)]
        n_samples = 50
        values = np.random.normal(mean, std, n_samples)
        # Add some outliers
        if np.random.random() > 0.5:
            values = np.append(values, [mean + 3.5 * std, mean - 3 * std])
        # Clip to realistic range
        values = np.clip(values, 0, 100)
        for v in values:
            data.append({"Department": dept, "Experience": exp, "Performance Score": v})

df = pd.DataFrame(data)

# Create grouped box plot with theme-adaptive styling
chart = (
    altair.Chart(df)
    .mark_boxplot(size=60, median={"stroke": INK, "strokeWidth": 2}, outliers={"size": 80, "strokeOpacity": 0.7})
    .encode(
        x=altair.X("Department:N", title="Department", axis=altair.Axis(labelFontSize=18, titleFontSize=22)),
        y=altair.Y(
            "Performance Score:Q",
            title="Performance Score (%)",
            scale=altair.Scale(domain=[0, 105]),
            axis=altair.Axis(labelFontSize=18, titleFontSize=22),
        ),
        color=altair.Color(
            "Experience:N",
            title="Experience Level",
            scale=altair.Scale(domain=["Junior", "Mid", "Senior"], range=IMPRINT),
            legend=altair.Legend(titleFontSize=20, labelFontSize=18, symbolSize=300, orient="top-left"),
        ),
        xOffset="Experience:N",
        tooltip=["Department:N", "Experience:N", "Performance Score:Q"],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=altair.Title(text="box-grouped · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save as PNG and HTML with theme-suffixed filenames
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
