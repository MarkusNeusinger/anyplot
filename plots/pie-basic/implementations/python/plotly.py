"""anyplot.ai
pie-basic: Basic Pie Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per slice in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PROCESSOR = "Payment processor"  # role: category
MARKET_SHARE = "Market share (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("shares.csv")
df = pd.DataFrame(
    {PROCESSOR: ["Visa", "Mastercard", "PayPal", "Amex", "Apple Pay", "Others"], MARKET_SHARE: [38, 26, 18, 7, 5, 6]}
)

# Plot: reads only df and the constants above
largest = df[MARKET_SHARE].idxmax()
pull = [0.08 if i == largest else 0 for i in range(len(df))]

fig = go.Figure(
    data=[
        go.Pie(
            labels=df[PROCESSOR],
            values=df[MARKET_SHARE],
            texttemplate="%{label}<br>%{percent:.0%}",
            textposition="auto",
            insidetextorientation="horizontal",
            insidetextfont={"size": 13, "color": "#FFFFFF"},
            outsidetextfont={"size": 13, "color": INK},
            hovertemplate="<b>%{label}</b><br>%{value}% market share<extra></extra>",
            marker={"colors": IMPRINT_PALETTE, "line": {"color": PAGE_BG, "width": 3}},
            pull=pull,
            sort=False,
            direction="clockwise",
            rotation=90,
            domain={"x": [0.06, 0.66], "y": [0.1, 0.86]},
        )
    ]
)

# Source note
fig.add_annotation(
    text="Source: Industry estimates, 2024",
    x=0.36,
    y=0.02,
    xref="paper",
    yref="paper",
    showarrow=False,
    font={"size": 10, "color": INK_MUTED, "family": "Arial, sans-serif"},
    xanchor="center",
    yanchor="bottom",
)

# Layout
fig.update_layout(
    autosize=False,
    title={
        "text": (
            "pie-basic · python · plotly · anyplot.ai"
            f"<br><span style='font-size:11px;color:{INK_SOFT}'>"
            "Global digital payment market share, 2024</span>"
        ),
        "font": {"size": 16, "color": INK, "family": "Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
        "y": 0.97,
    },
    legend={
        "font": {"size": 12, "color": INK_SOFT},
        "orientation": "v",
        "yanchor": "middle",
        "y": 0.5,
        "xanchor": "left",
        "x": 0.8,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"t": 60, "b": 35, "l": 20, "r": 20},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
