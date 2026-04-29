""" anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-04-29
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
pd = importlib.import_module("pandas")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data — population pyramid with pronounced gender gap in older age groups
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male = [4.8, 5.2, 6.1, 7.3, 8.5, 7.8, 5.9, 3.2, 1.2]
female = [4.5, 5.0, 6.3, 7.5, 8.7, 8.2, 6.8, 4.8, 2.5]  # more females in older groups

df = pd.DataFrame(
    {
        "Age Group": age_groups * 2,
        "Population": [-v for v in male] + female,
        "Gender": ["Male"] * len(age_groups) + ["Female"] * len(age_groups),
        "Absolute": male + female,
    }
)

age_order = list(reversed(age_groups))

# Interactive highlight — click legend to isolate a gender
selection = alt.selection_point(fields=["Gender"], bind="legend")

# Plot
chart = (
    alt.Chart(df)
    .mark_bar(cornerRadiusEnd=3)
    .encode(
        y=alt.Y("Age Group:N", sort=age_order, axis=alt.Axis(title="Age Group", titleFontSize=22, labelFontSize=18)),
        x=alt.X(
            "Population:Q",
            axis=alt.Axis(
                title="Population (millions)",
                titleFontSize=22,
                labelFontSize=18,
                values=[-8, -6, -4, -2, 0, 2, 4, 6, 8],
                labelExpr="abs(datum.value)",
            ),
            scale=alt.Scale(domain=[-10, 10]),
        ),
        color=alt.Color(
            "Gender:N",
            scale=alt.Scale(domain=["Male", "Female"], range=[OKABE_ITO[0], OKABE_ITO[1]]),
            legend=alt.Legend(title="Gender", titleFontSize=20, labelFontSize=18, orient="bottom"),
        ),
        opacity=alt.condition(selection, alt.value(0.9), alt.value(0.25)),
        tooltip=[
            alt.Tooltip("Gender:N"),
            alt.Tooltip("Age Group:N"),
            alt.Tooltip("Absolute:Q", title="Population (M)", format=".1f"),
        ],
    )
    .add_params(selection)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(text="pyramid-basic · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=20,
        labelFontSize=18,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
