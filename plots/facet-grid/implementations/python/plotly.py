"""anyplot.ai
facet-grid: Faceted Grid Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
import plotly.express as px


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: first position is the single series colour
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PAYLOAD = "Payload size (KB)"  # role: x
LATENCY = "Response time (ms)"  # role: y
SERVER = "Server"  # role: row_facet
TIME_OF_DAY = "Time of day"  # role: col_facet

# Data: replace this block with your own table, for example df = pd.read_csv("latency.csv")
rng = np.random.default_rng(42)
servers = {"Frankfurt": 40, "Virginia": 70, "Singapore": 110}  # base network delay (ms)
periods = {"Night": 0, "Morning": 25, "Afternoon": 45, "Evening": 70}  # load penalty (ms)
frames = []
for server, base in servers.items():
    for period, load in periods.items():
        payload = rng.uniform(50, 900, 35)
        latency = base + load + payload * rng.uniform(0.08, 0.16, 35) + rng.normal(0, 12, 35)
        frames.append(pd.DataFrame({PAYLOAD: payload, LATENCY: latency, SERVER: server, TIME_OF_DAY: period}))
df = pd.concat(frames, ignore_index=True)

# Plot
fig = px.scatter(
    df,
    x=PAYLOAD,
    y=LATENCY,
    facet_row=SERVER,
    facet_col=TIME_OF_DAY,
    color_discrete_sequence=IMPRINT_PALETTE,
    category_orders={SERVER: list(df[SERVER].unique()), TIME_OF_DAY: list(df[TIME_OF_DAY].unique())},
)

# Style
fig.update_layout(
    autosize=False,
    margin={"l": 70, "r": 40, "t": 70, "b": 60},
    title={
        "text": "facet-grid · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
)

axis_style = {
    "title_font": {"size": 12, "color": INK},
    "tickfont": {"size": 10, "color": INK_SOFT},
    "gridcolor": GRID,
    "linecolor": INK_SOFT,
    "zerolinecolor": GRID,
}
fig.update_xaxes(**axis_style)
fig.update_yaxes(**axis_style)

# One shared y title for the whole figure instead of one per row (they collide on three rows)
fig.update_yaxes(title_text=None)
fig.add_annotation(
    text=LATENCY,
    textangle=-90,
    x=-0.075,
    y=0.5,
    xref="paper",
    yref="paper",
    showarrow=False,
    font={"size": 12, "color": INK},
)

# Strip labels show the category only ("Frankfurt", not "Server=Frankfurt")
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font={"size": 11, "color": INK}))

fig.update_traces(
    marker={"size": 6, "opacity": 0.75, "color": IMPRINT_PALETTE[0], "line": {"width": 0.5, "color": PAGE_BG}}
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
