"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os

import pandas as pd
from plotly import graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_HIGHLIGHT = 3  # the largest points by x that get the accent color

# Columns: set these to your table's column names
MARKET_CAP = "Market Cap (Billion USD)"  # role: x
REVENUE = "Annual Revenue (Billion USD)"  # role: y
COMPANY = "Company"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("companies.csv")
df = pd.DataFrame(
    {
        COMPANY: [
            "Apple",
            "Microsoft",
            "Alphabet",
            "Amazon",
            "Meta",
            "Tesla",
            "Nvidia",
            "Samsung",
            "TSMC",
            "Oracle",
            "Salesforce",
            "Netflix",
        ],
        MARKET_CAP: [2800, 2700, 1700, 1500, 900, 700, 1200, 350, 500, 300, 250, 250],
        REVENUE: [380, 210, 280, 520, 130, 95, 60, 230, 70, 50, 32, 33],
    }
)

# Plot: reads only df and the constants above
# Label offsets in pixels from the point (right/left, above/below, then straight above/below)
LABEL_OFFSETS = [(50, -15), (50, 15), (60, 20), (-50, 15), (0, 30), (-50, -15)]
top_names = set(df.nlargest(N_HIGHLIGHT, MARKET_CAP)[COMPANY])
is_top = df[COMPANY].isin(top_names)
point_colors = [IMPRINT_PALETTE[1] if top else IMPRINT_PALETTE[0] for top in is_top]

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[MARKET_CAP],
        y=df[REVENUE],
        mode="markers",
        marker=dict(
            size=[13 if top else 10 for top in is_top],
            color=point_colors,
            opacity=0.8,
            line=dict(width=1.2, color=PAGE_BG),
        ),
        text=df[COMPANY],
        customdata=df[REVENUE] / df[MARKET_CAP],
        hovertemplate=(
            "<b>%{text}</b><br>"
            + MARKET_CAP
            + ": $%{x:.0f}B<br>"
            + REVENUE
            + ": $%{y:.0f}B<br>"
            + "Revenue / market cap: %{customdata:.2f}x<extra></extra>"
        ),
    )
)

annotations = []
for i, (company, cap, rev) in enumerate(zip(df[COMPANY], df[MARKET_CAP], df[REVENUE])):
    ax, ay = LABEL_OFFSETS[i % len(LABEL_OFFSETS)]
    accent = company in top_names
    annotations.append(
        dict(
            x=cap,
            y=rev,
            text=f"<b>{company}</b>",
            showarrow=True,
            arrowhead=0,
            arrowwidth=1,
            arrowcolor=INK_SOFT,
            standoff=6,
            ax=ax,
            ay=ay,
            font=dict(size=10, color=INK),
            bgcolor=ELEVATED_BG,
            bordercolor=IMPRINT_PALETTE[1] if accent else INK_SOFT,
            borderwidth=1.2 if accent else 0.8,
            borderpad=3,
        )
    )

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title=dict(
        text="scatter-annotated · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
        y=0.97,
        yanchor="top",
    ),
    xaxis=dict(
        title=dict(text=MARKET_CAP, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linewidth=1,
        linecolor=INK_SOFT,
        range=[-0.03 * df[MARKET_CAP].max(), df[MARKET_CAP].max() * 1.1],
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text=REVENUE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linewidth=1,
        linecolor=INK_SOFT,
        range=[-0.12 * df[REVENUE].max(), df[REVENUE].max() * 1.12],
        zeroline=False,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    annotations=annotations,
    margin=dict(l=70, r=40, t=60, b=60),
    showlegend=False,
    hovermode="closest",
    font=dict(family="Arial, sans-serif", color=INK),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
