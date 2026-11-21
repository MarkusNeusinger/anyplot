"""anyplot.ai
timeline-basic: Event Timeline
Library: plotly | Python 3
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
EVENT = "Event"  # role: event
CATEGORY = "Category"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv")
df = pd.DataFrame(
    {
        DATE: pd.to_datetime(
            [
                "2018-12-26",
                "2019-07-17",
                "2020-03-16",
                "2020-11-09",
                "2021-03-11",
                "2021-11-09",
                "2022-03-16",
                "2023-03-10",
                "2024-01-10",
            ]
        ),
        EVENT: [
            "Market Bottom",
            "Bull Run Begins",
            "COVID Crash",
            "Post-Election Rally",
            "Recovery Accelerates",
            "Peak Market Euphoria",
            "Rate Hikes Begin",
            "Bank Crisis Resolved",
            "AI Boom Peaks",
        ],
        CATEGORY: ["Market", "Market", "Crisis", "Recovery", "Recovery", "Expansion", "Correction", "Crisis", "Growth"],
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(DATE).reset_index(drop=True)
side = [1 if i % 2 == 0 else -1 for i in range(len(df))]  # alternate above / below the axis
reach = [side[i] * (0.55 if (i // 2) % 2 == 0 else 0.85) for i in range(len(df))]  # stem length, layout only
categories = list(dict.fromkeys(df[CATEGORY]))
span = df[DATE].max() - df[DATE].min()
pad = span * 0.06

fig = go.Figure()

# Stems from axis to label
for date, y in zip(df[DATE], reach):
    fig.add_trace(
        go.Scatter(
            x=[date, date],
            y=[0, y],
            mode="lines",
            line=dict(color=INK_SOFT, width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Event markers, one trace and one Imprint color per category
for i, cat in enumerate(categories):
    rows = df[df[CATEGORY] == cat]
    fig.add_trace(
        go.Scatter(
            x=rows[DATE],
            y=[0] * len(rows),
            mode="markers",
            marker=dict(size=12, color=IMPRINT_PALETTE[i], line=dict(color=PAGE_BG, width=1.5)),
            name=cat,
            customdata=rows[[EVENT]].assign(when=rows[DATE].dt.strftime("%b %d, %Y")),
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
        )
    )

# Event name and date, tied to the marker by its stem
for date, event, y in zip(df[DATE], df[EVENT], reach):
    fig.add_annotation(
        x=date,
        y=y,
        text=f"<b>{event}</b><br><span style='font-size:8px;color:{INK_SOFT}'>{date:%b %Y}</span>",
        showarrow=False,
        font=dict(size=10, color=INK),
        xanchor="center",
        yanchor="bottom" if y > 0 else "top",
    )

title = "timeline-basic · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title=dict(text=title, font=dict(size=16, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text=DATE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        tickformat="%Y",
        dtick="M12",
        range=[df[DATE].min() - pad, df[DATE].max() + pad],
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=INK_SOFT,
        linewidth=2,
    ),
    yaxis=dict(visible=False, range=[-1.25, 1.25], fixedrange=True),
    template="plotly_white",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.0,
        xanchor="center",
        x=0.5,
        font=dict(size=10, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=40, r=40, t=90, b=60),
)

# Output
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
