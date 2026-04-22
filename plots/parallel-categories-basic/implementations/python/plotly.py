""" pyplots.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import plotly.graph_objects as go
import seaborn as sns


# Data - Titanic survival data with multiple categorical dimensions
df = sns.load_dataset("titanic")

# Prepare data: select key categorical variables
df = df[["class", "sex", "embarked", "survived"]].dropna()

# Map survived to readable labels
df["outcome"] = df["survived"].map({0: "Did Not Survive", 1: "Survived"})

# Create dimension specifications for parallel categories
dimensions = [
    {
        "label": "Passenger Class",
        "values": df["class"].astype(str),
        "categoryorder": "array",
        "categoryarray": ["First", "Second", "Third"],
    },
    {
        "label": "Sex",
        "values": df["sex"].str.capitalize(),
        "categoryorder": "array",
        "categoryarray": ["Female", "Male"],
    },
    {
        "label": "Embarked",
        "values": df["embarked"].map({"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"}),
        "categoryorder": "array",
        "categoryarray": ["Cherbourg", "Queenstown", "Southampton"],
    },
    {
        "label": "Outcome",
        "values": df["outcome"],
        "categoryorder": "array",
        "categoryarray": ["Survived", "Did Not Survive"],
    },
]

# Create color scale based on survival outcome (last dimension)
color_values = df["survived"].values

# Create parallel categories plot
fig = go.Figure(
    go.Parcats(
        dimensions=dimensions,
        line={
            "color": color_values,
            "colorscale": [[0, "#306998"], [1, "#FFD43B"]],  # Python Blue for not survived, Yellow for survived
            "shape": "hspline",
        },
        hoveron="color",
        hoverinfo="count+probability",
        arrangement="freeform",
    )
)

# Update layout for 4800x2700 canvas
fig.update_layout(
    title={
        "text": "Titanic Passengers · parallel-categories-basic · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    font={"size": 20},
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin={"l": 80, "r": 80, "t": 120, "b": 80},
    annotations=[
        {
            "text": "Color: Yellow = Survived, Blue = Did Not Survive",
            "x": 0.5,
            "y": -0.08,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 18, "color": "#666666"},
            "xanchor": "center",
        }
    ],
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
