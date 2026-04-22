""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import altair as alt
import pandas as pd


# Data: Titanic survival by class and survival status
# Classic contingency table example
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

# Calculate proportions for mosaic layout
# Width: proportion of each class in total
class_totals = data.groupby("Class")["Count"].sum().reset_index()
class_totals.columns = ["Class", "ClassTotal"]
total = class_totals["ClassTotal"].sum()
class_totals["Width"] = class_totals["ClassTotal"] / total

# Calculate cumulative x positions for each class
class_order = ["1st", "2nd", "3rd", "Crew"]
class_totals["ClassOrder"] = class_totals["Class"].map({c: i for i, c in enumerate(class_order)})
class_totals = class_totals.sort_values("ClassOrder")
class_totals["x_start"] = class_totals["Width"].cumsum() - class_totals["Width"]
class_totals["x_end"] = class_totals["Width"].cumsum()
class_totals["x_mid"] = (class_totals["x_start"] + class_totals["x_end"]) / 2

# Merge back to main data
data = data.merge(class_totals[["Class", "Width", "x_start", "x_end", "x_mid", "ClassTotal"]], on="Class")

# Calculate height proportions within each class
data["Height"] = data["Count"] / data["ClassTotal"]

# Calculate y positions within each class
survival_order = {"Survived": 0, "Did Not Survive": 1}
data["SurvivalOrder"] = data["Survival"].map(survival_order)
data = data.sort_values(["Class", "SurvivalOrder"])

# Calculate cumulative y positions
y_positions = []
for cls in class_order:
    cls_data = data[data["Class"] == cls].sort_values("SurvivalOrder")
    cumsum = 0
    for idx in cls_data.index:
        y_positions.append({"index": idx, "y_start": cumsum, "y_end": cumsum + data.loc[idx, "Height"]})
        cumsum += data.loc[idx, "Height"]

y_df = pd.DataFrame(y_positions).set_index("index")
data["y_start"] = data.index.map(y_df["y_start"])
data["y_end"] = data.index.map(y_df["y_end"])
data["y_mid"] = (data["y_start"] + data["y_end"]) / 2

# Calculate percentage for labels
data["Percentage"] = (data["Count"] / total * 100).round(1)

# Create mosaic chart
mosaic = (
    alt.Chart(data)
    .mark_rect(stroke="white", strokeWidth=3)
    .encode(
        x=alt.X("x_start:Q", axis=None),
        x2=alt.X2("x_end:Q"),
        y=alt.Y("y_start:Q", axis=None),
        y2=alt.Y2("y_end:Q"),
        color=alt.Color(
            "Survival:N",
            scale=alt.Scale(domain=["Survived", "Did Not Survive"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(
                title="Survival Status", titleFontSize=20, labelFontSize=18, orient="right", symbolSize=400
            ),
        ),
        tooltip=["Class:N", "Survival:N", "Count:Q", "Percentage:Q"],
    )
)

# Add count labels inside rectangles
labels = (
    alt.Chart(data)
    .mark_text(fontSize=22, fontWeight="bold", align="center", baseline="middle")
    .encode(
        x=alt.X("x_mid:Q"),
        y=alt.Y("y_mid:Q"),
        text=alt.Text("Count:Q"),
        color=alt.condition(alt.datum.Survival == "Survived", alt.value("white"), alt.value("#333333")),
    )
)


# Add class labels at bottom
class_labels_df = class_totals[["Class", "x_mid"]].copy()
class_labels = (
    alt.Chart(class_labels_df)
    .mark_text(fontSize=20, fontWeight="bold", baseline="top", dy=15)
    .encode(x=alt.X("x_mid:Q"), y=alt.value(1.0), text="Class:N")
)

# Combine layers
chart = (
    alt.layer(mosaic, labels, class_labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("mosaic-categorical · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
