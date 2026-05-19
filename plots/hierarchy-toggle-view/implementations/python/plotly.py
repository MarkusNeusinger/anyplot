"""anyplot.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: plotly | Python 3.13
Quality: 92/100 | Updated: 2026-05-19
"""

import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Hierarchical data: Company budget allocation (in thousands)
# Deterministic data — no random seed needed
labels = ["Company"]
parents = [""]
values = [9600]

departments = [("Engineering", 4500), ("Marketing", 2100), ("Sales", 1800), ("Operations", 1200)]

for dept_name, dept_budget in departments:
    labels.append(dept_name)
    parents.append("Company")
    values.append(dept_budget)

teams_data = [
    ("Backend", "Engineering", 1800),
    ("Frontend", "Engineering", 1200),
    ("Data Science", "Engineering", 900),
    ("DevOps", "Engineering", 600),
    ("Digital", "Marketing", 900),
    ("Brand", "Marketing", 600),
    ("Content", "Marketing", 600),
    ("Enterprise", "Sales", 1000),
    ("SMB", "Sales", 500),
    ("Partners", "Sales", 300),
    ("IT", "Operations", 500),
    ("HR", "Operations", 400),
    ("Finance", "Operations", 300),
]

for team_name, parent_dept, team_budget in teams_data:
    labels.append(team_name)
    parents.append(parent_dept)
    values.append(team_budget)

# Okabe-Ito palette for departments (positions 1–4)
dept_colors = {"Engineering": "#009E73", "Marketing": "#D55E00", "Sales": "#0072B2", "Operations": "#CC79A7"}

colors = []
for i, label in enumerate(labels):
    if label == "Company":
        colors.append(ELEVATED_BG)
    elif label in dept_colors:
        colors.append(dept_colors[label])
    else:
        colors.append(dept_colors.get(parents[i], "#009E73"))

# Side-by-side PNG: both views visible simultaneously
fig = make_subplots(rows=1, cols=2, specs=[[{"type": "treemap"}, {"type": "sunburst"}]], horizontal_spacing=0.03)

fig.add_trace(
    go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"width": 2, "color": PAGE_BG}},
        textfont={"size": 20},
        textinfo="label+value",
        texttemplate="%{label}<br>$%{value}K",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}K<br>Percent: %{percentParent:.1%}<extra></extra>",
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"width": 2, "color": PAGE_BG}},
        textfont={"size": 16},
        textinfo="label",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}K<br>Percent: %{percentParent:.1%}<extra></extra>",
        insidetextorientation="radial",
    ),
    row=1,
    col=2,
)

fig.update_layout(
    title={
        "text": "hierarchy-toggle-view · python · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"t": 130, "l": 20, "r": 20, "b": 90},
    annotations=[
        {
            "text": "Treemap View",
            "x": 0.22,
            "y": 1.05,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 22, "color": INK_SOFT},
        },
        {
            "text": "Sunburst View",
            "x": 0.78,
            "y": 1.05,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 22, "color": INK_SOFT},
        },
        {
            "text": "Two perspectives: rectangles for size comparison, radial for hierarchy depth",
            "x": 0.5,
            "y": -0.05,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 18, "color": INK_SOFT},
        },
    ],
)

fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Interactive HTML with toggle buttons
fig_html = go.Figure()

fig_html.add_trace(
    go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"width": 2, "color": PAGE_BG}},
        textfont={"size": 22},
        textinfo="label+value",
        texttemplate="%{label}<br>$%{value}K",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}K<br>Percent: %{percentParent:.1%}<extra></extra>",
        visible=True,
    )
)

fig_html.add_trace(
    go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"width": 2, "color": PAGE_BG}},
        textfont={"size": 18},
        textinfo="label",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}K<br>Percent: %{percentParent:.1%}<extra></extra>",
        visible=False,
        insidetextorientation="radial",
    )
)

fig_html.update_layout(
    title={
        "text": "hierarchy-toggle-view · python · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"t": 150, "l": 30, "r": 30, "b": 50},
    updatemenus=[
        {
            "type": "buttons",
            "direction": "right",
            "x": 0.5,
            "xanchor": "center",
            "y": 1.12,
            "buttons": [
                {"label": "  Treemap  ", "method": "update", "args": [{"visible": [True, False]}]},
                {"label": "  Sunburst  ", "method": "update", "args": [{"visible": [False, True]}]},
            ],
            "font": {"size": 18, "color": INK},
            "bgcolor": ELEVATED_BG,
            "bordercolor": "#009E73",
            "borderwidth": 2,
        }
    ],
)

fig_html.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
