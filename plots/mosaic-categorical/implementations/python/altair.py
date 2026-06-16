""" anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
"""

import os
import sys


# Work around filename shadowing the altair library
sys.path.pop(0)

import altair as alt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito positions 1 and 2
COLOR_SURVIVED = "#009E73"
COLOR_NOT_SURVIVED = "#C475FD"

# Data: Titanic survival by passenger class (contingency table)
data = pd.DataFrame(
    {
        "Class": ["1st", "1st", "2nd", "2nd", "3rd", "3rd", "Crew", "Crew"],
        "Survival": [
            "Survived",
            "Did Not Survive",
            "Survived",
            "Did Not Survive",
            "Survived",
            "Did Not Survive",
            "Survived",
            "Did Not Survive",
        ],
        "Count": [203, 122, 118, 167, 178, 528, 212, 673],
    }
)

# Calculate mosaic layout: widths from marginal proportions, heights from conditional proportions
class_totals = data.groupby("Class")["Count"].sum().reset_index()
class_totals.columns = ["Class", "ClassTotal"]
total = class_totals["ClassTotal"].sum()
class_totals["Width"] = class_totals["ClassTotal"] / total

class_order = ["1st", "2nd", "3rd", "Crew"]
class_totals["ClassOrder"] = class_totals["Class"].map({c: i for i, c in enumerate(class_order)})
class_totals = class_totals.sort_values("ClassOrder")
class_totals["x_start"] = class_totals["Width"].cumsum() - class_totals["Width"]
class_totals["x_end"] = class_totals["Width"].cumsum()
class_totals["x_mid"] = (class_totals["x_start"] + class_totals["x_end"]) / 2

data = data.merge(class_totals[["Class", "Width", "x_start", "x_end", "x_mid", "ClassTotal"]], on="Class")
data["Height"] = data["Count"] / data["ClassTotal"]

survival_order = {"Survived": 0, "Did Not Survive": 1}
data["SurvivalOrder"] = data["Survival"].map(survival_order)
data = data.sort_values(["Class", "SurvivalOrder"])

y_positions = []
for cls in class_order:
    cls_data = data[data["Class"] == cls].sort_values("SurvivalOrder")
    cumsum = 0.0
    for idx in cls_data.index:
        y_positions.append({"index": idx, "y_start": cumsum, "y_end": cumsum + data.loc[idx, "Height"]})
        cumsum += data.loc[idx, "Height"]

y_df = pd.DataFrame(y_positions).set_index("index")
data["y_start"] = data.index.map(y_df["y_start"])
data["y_end"] = data.index.map(y_df["y_end"])
data["y_mid"] = (data["y_start"] + data["y_end"]) / 2
data["Percentage"] = (data["Count"] / total * 100).round(1)

# Plot: mosaic rectangles with axis titles for both categorical dimensions
mosaic = (
    alt.Chart(data)
    .mark_rect(stroke=PAGE_BG, strokeWidth=3)
    .encode(
        x=alt.X("x_start:Q", axis=alt.Axis(title="Passenger Class", labels=False, ticks=False, domain=False)),
        x2=alt.X2("x_end:Q"),
        y=alt.Y("y_start:Q", axis=alt.Axis(title="Proportion", labels=False, ticks=False, domain=False)),
        y2=alt.Y2("y_end:Q"),
        color=alt.Color(
            "Survival:N",
            scale=alt.Scale(domain=["Survived", "Did Not Survive"], range=[COLOR_SURVIVED, COLOR_NOT_SURVIVED]),
            legend=alt.Legend(
                title="Survival Status", titleFontSize=20, labelFontSize=18, orient="right", symbolSize=400
            ),
        ),
        tooltip=["Class:N", "Survival:N", "Count:Q", "Percentage:Q"],
    )
)

# Count labels — white on green (survived), theme ink on vermillion (did not survive)
labels = (
    alt.Chart(data)
    .mark_text(fontSize=22, fontWeight="bold", align="center", baseline="middle")
    .encode(
        x=alt.X("x_mid:Q"),
        y=alt.Y("y_mid:Q"),
        text=alt.Text("Count:Q"),
        color=alt.condition(alt.datum.Survival == "Survived", alt.value("white"), alt.value(INK)),
    )
)

# Class name labels at top of each column
class_labels_df = class_totals[["Class", "x_mid"]].copy()
class_labels = (
    alt.Chart(class_labels_df)
    .mark_text(fontSize=20, fontWeight="bold", baseline="top", dy=15, color=INK)
    .encode(x=alt.X("x_mid:Q"), y=alt.value(1.0), text="Class:N")
)

# Combine layers with theme-adaptive chrome
chart = (
    alt.layer(mosaic, labels, class_labels)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("mosaic-categorical · python · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
