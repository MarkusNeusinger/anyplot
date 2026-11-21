"""anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-13
"""

import os

import plotly.graph_objects as go
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CLASS_ORDER = ["First", "Second", "Third"]
SEX_ORDER = ["Female", "Male"]
PORT_ORDER = ["Cherbourg", "Queenstown", "Southampton"]
OUTCOME_ORDER = ["Survived", "Did Not Survive"]

# Column constants
DIMENSIONS = ["Passenger Class", "Sex", "Embarked", "Outcome"]  # role: dimension_
PASSENGER_CLASS, SEX, EMBARKED, OUTCOME = DIMENSIONS

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
raw = sns.load_dataset("titanic")[["class", "sex", "embarked", "survived"]].dropna()
df = raw.rename(columns={"class": PASSENGER_CLASS, "sex": SEX, "embarked": EMBARKED, "survived": OUTCOME})[DIMENSIONS]
df[PASSENGER_CLASS] = df[PASSENGER_CLASS].astype(str)
df[SEX] = df[SEX].str.capitalize()
df[EMBARKED] = df[EMBARKED].map({"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"})
df[OUTCOME] = df[OUTCOME].map({0: "Did Not Survive", 1: "Survived"})

# Plot
category_order = {PASSENGER_CLASS: CLASS_ORDER, SEX: SEX_ORDER, EMBARKED: PORT_ORDER, OUTCOME: OUTCOME_ORDER}
dimensions = [
    {
        "label": name,
        "values": df[name],
        "categoryorder": "array",
        "categoryarray": [c for c in category_order.get(name, []) if c in set(df[name])] or sorted(df[name].unique()),
    }
    for name in DIMENSIONS
]

# Ribbons colored by the last dimension (outcome); first category takes the first palette color
last = DIMENSIONS[-1]
outcome_levels = dimensions[-1]["categoryarray"]
ribbon_color = (df[last] == outcome_levels[0]).astype(int)

fig = go.Figure(
    go.Parcats(
        dimensions=dimensions,
        line={
            "color": ribbon_color,
            "colorscale": [[0, IMPRINT_PALETTE[1]], [1, IMPRINT_PALETTE[0]]],
            "shape": "hspline",
        },
        labelfont={"size": 13, "color": INK},
        tickfont={"size": 11, "color": INK_SOFT},
        hoveron="color",
        hoverinfo="count+probability",
        arrangement="freeform",
    )
)

fig.update_layout(
    autosize=False,
    title={
        "text": "parallel-categories-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    font={"size": 11, "color": INK_SOFT},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 80, "r": 80, "t": 70, "b": 40},
)

# Save PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
