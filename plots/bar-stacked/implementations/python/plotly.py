"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-09
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

# Imprint palette: all eight positions, one per component in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
EXPENSE = "Expense type"  # role: component
BUDGET = "Budget (thousand USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("budget.csv")
departments = ["Engineering", "Marketing", "Sales", "Operations", "HR"]
expense_types = ["Salaries", "Equipment", "Travel", "Training"]
amounts = {
    "Salaries": [820, 410, 560, 480, 290],
    "Equipment": [240, 60, 90, 310, 35],
    "Travel": [55, 120, 210, 85, 25],
    "Training": [70, 30, 45, 40, 60],
}
df = pd.DataFrame(
    {
        DEPARTMENT: [d for _ in expense_types for d in departments],
        EXPENSE: [e for e in expense_types for _ in departments],
        BUDGET: [v for e in expense_types for v in amounts[e]],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=DEPARTMENT, columns=EXPENSE, values=BUDGET, sort=False)
totals = table.sum(axis=1)

fig = go.Figure()
for i, expense in enumerate(table.columns):
    share = (table[expense] / totals * 100).map("{:.0f}%".format)
    fig.add_trace(
        go.Bar(
            name=str(expense),
            x=table.index,
            y=table[expense],
            marker={"color": IMPRINT_PALETTE[i], "line": {"color": PAGE_BG, "width": 1}},
            text=table[expense],
            textposition="inside",
            textfont={"size": 11, "color": "white"},
            customdata=share,
            hovertemplate=f"<b>{expense}</b><br>%{{x}}<br>{BUDGET}: %{{y}}<br>Share of department: %{{customdata}}<extra></extra>",
        )
    )

# Total labels above each complete stack
fig.add_trace(
    go.Scatter(
        x=table.index,
        y=totals,
        mode="text",
        text=[f"<b>{t:,.0f}</b>" for t in totals],
        textposition="top center",
        textfont={"size": 13, "color": INK},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Style
fig.update_layout(
    autosize=False,
    title={"text": "bar-stacked · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    xaxis={
        "title": {"text": DEPARTMENT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": BUDGET, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 0.5,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "range": [0, totals.max() * 1.12],
    },
    barmode="stack",
    bargap=0.3,
    uniformtext={"minsize": 11, "mode": "hide"},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "title": {"text": EXPENSE, "font": {"size": 11, "color": INK}},
        "font": {"size": 11, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.99,
        "xanchor": "right",
        "y": 0.99,
        "yanchor": "top",
    },
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
