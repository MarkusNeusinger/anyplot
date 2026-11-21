"""anyplot.ai
gantt-basic: Basic Gantt Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
"""

import os

import pandas as pd
import plotly.express as px


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TODAY_SHARE = 0.44  # the current-date line sits at this share of the schedule's span

# Columns: set these to your table's column names
TASK = "Task"  # role: task
START = "Start"  # role: start
END = "End"  # role: end
CATEGORY = "Category"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("schedule.csv", parse_dates=[START, END])
df = pd.DataFrame(
    {
        TASK: [
            "Requirements Analysis",
            "System Design",
            "Database Design",
            "UI/UX Design",
            "Backend Development",
            "Frontend Development",
            "API Integration",
            "Unit Testing",
            "Integration Testing",
            "User Acceptance Testing",
            "Documentation",
            "Deployment & Launch",
        ],
        START: pd.to_datetime(
            [
                "2025-01-06",
                "2025-01-13",
                "2025-01-27",
                "2025-01-27",
                "2025-02-03",
                "2025-02-10",
                "2025-03-03",
                "2025-03-10",
                "2025-03-24",
                "2025-04-01",
                "2025-03-17",
                "2025-04-07",
            ]
        ),
        END: pd.to_datetime(
            [
                "2025-01-17",
                "2025-01-31",
                "2025-02-07",
                "2025-02-14",
                "2025-03-14",
                "2025-03-21",
                "2025-03-21",
                "2025-03-28",
                "2025-04-04",
                "2025-04-11",
                "2025-04-11",
                "2025-04-18",
            ]
        ),
        CATEGORY: ["Planning"] * 2 + ["Design"] * 2 + ["Development"] * 3 + ["Testing"] * 3 + ["Deployment"] * 2,
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(START, kind="stable").reset_index(drop=True)
today = df[START].min() + (df[END].max() - df[START].min()) * TODAY_SHARE

title = "Software Development Project · gantt-basic · python · plotly · anyplot.ai"
title_size = round(16 * 67 / len(title)) if len(title) > 67 else 16

fig = px.timeline(df, x_start=START, x_end=END, y=TASK, color=CATEGORY, color_discrete_sequence=IMPRINT_PALETTE)
fig.update_yaxes(autorange="reversed")

# Current-date line, spanning the full plot height
fig.add_shape(
    type="line",
    xref="x",
    yref="paper",
    x0=today,
    x1=today,
    y0=0,
    y1=1,
    line={"color": INK_SOFT, "width": 1.5, "dash": "dash"},
    layer="above",
)
fig.add_annotation(
    x=today,
    xref="x",
    yref="paper",
    y=0,
    text="Today",
    showarrow=False,
    font={"size": 10, "color": INK_SOFT},
    yanchor="bottom",
    xanchor="left",
    xshift=4,
    yshift=4,
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "%b %d",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": TASK, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "title": {"text": CATEGORY, "font": {"size": 10, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 130, "r": 40, "t": 90, "b": 55},
    bargap=0.3,
)
fig.update_traces(marker={"line": {"color": PAGE_BG, "width": 0.5}}, opacity=0.9)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
