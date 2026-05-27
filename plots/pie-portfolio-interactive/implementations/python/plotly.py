"""anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: plotly | Python 3.13
Quality: 93/100 | Updated: 2026-05-27
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# anyplot palette — semantic color mapping for ESG portfolio categories
# Sustainable Equities → brand green (environmental)
# Technology → blue (tech/stability)
# Green Fixed Income → lavender (debt markets, calm)
# Real Assets → ochre (earth, tangible)
CATEGORY_COLORS = {
    "Sustainable Equities": "#009E73",
    "Technology": "#4467A3",
    "Green Fixed Income": "#C475FD",
    "Real Assets": "#BD8233",
}

# Data — ESG-focused portfolio (technology-forward, climate-aligned)
portfolio_data = {
    "asset": [
        # Sustainable Equities
        "Ørsted A/S",
        "NextEra Energy",
        "Vestas Wind",
        "Brookfield Renewable",
        # Technology
        "Microsoft Corp.",
        "Alphabet Inc.",
        "Schneider Electric",
        # Green Fixed Income
        "Green Bonds AAA",
        "Climate Bonds",
        # Real Assets
        "Clean Water ETF",
        "Timber REIT",
    ],
    "weight": [9.0, 11.0, 7.0, 8.0, 10.0, 8.0, 7.0, 15.0, 12.0, 8.0, 5.0],
    "category": [
        "Sustainable Equities",
        "Sustainable Equities",
        "Sustainable Equities",
        "Sustainable Equities",
        "Technology",
        "Technology",
        "Technology",
        "Green Fixed Income",
        "Green Fixed Income",
        "Real Assets",
        "Real Assets",
    ],
}

df = pd.DataFrame(portfolio_data)
colors = [CATEGORY_COLORS[cat] for cat in df["category"]]

# Category summary for "By Category" toggle view
category_summary = df.groupby("category")["weight"].sum().reset_index()
category_summary = category_summary.sort_values("weight", ascending=False).reset_index(drop=True)
category_summary_colors = [CATEGORY_COLORS[cat] for cat in category_summary["category"]]

# Title — length 56 chars, under 67-char baseline → no scaling needed
title_text = "pie-portfolio-interactive · python · plotly · anyplot.ai"
title_fontsize = 16

# Figure
fig = go.Figure()

# Main donut trace — all individual holdings
fig.add_trace(
    go.Pie(
        labels=df["asset"],
        values=df["weight"],
        hole=0.42,
        marker=dict(colors=colors, line=dict(color=PAGE_BG, width=3)),
        textinfo="percent",
        textposition="inside",
        textfont=dict(size=13, color=PAGE_BG),
        insidetextorientation="horizontal",
        hovertemplate=("<b>%{label}</b><br>Weight: %{value:.1f}%<br>Category: %{customdata}<br><extra></extra>"),
        customdata=df["category"],
        pull=[0.02] * len(df),
        rotation=90,
    )
)

# Center annotation
fig.add_annotation(text="<b>ESG</b><br>Portfolio", x=0.5, y=0.5, font=dict(size=22, color=INK), showarrow=False)

# Toggle buttons — All Holdings vs By Category
fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=0.5,
            y=1.10,
            xanchor="center",
            buttons=[
                dict(
                    label="All Holdings",
                    method="update",
                    args=[
                        {
                            "labels": [df["asset"].tolist()],
                            "values": [df["weight"].tolist()],
                            "marker": [dict(colors=colors, line=dict(color=PAGE_BG, width=3))],
                            "customdata": [df["category"].tolist()],
                        },
                        {"annotations[0].text": "<b>ESG</b><br>Portfolio"},
                    ],
                ),
                dict(
                    label="By Category",
                    method="update",
                    args=[
                        {
                            "labels": [category_summary["category"].tolist()],
                            "values": [category_summary["weight"].tolist()],
                            "marker": [dict(colors=category_summary_colors, line=dict(color=PAGE_BG, width=3))],
                            "customdata": [category_summary["category"].tolist()],
                        },
                        {"annotations[0].text": "<b>Asset Class</b><br>Overview"},
                    ],
                ),
            ],
            font=dict(size=13, color=INK),
            bgcolor=ELEVATED_BG,
            bordercolor=INK_SOFT,
        )
    ]
)

# Layout
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    title=dict(text=title_text, font=dict(size=title_fontsize, color=INK), x=0.5, y=0.97, xanchor="center"),
    showlegend=True,
    legend=dict(
        title=dict(text="Asset Class", font=dict(size=13, color=INK)),
        font=dict(size=12, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        orientation="h",
        yanchor="top",
        y=-0.04,
        xanchor="center",
        x=0.5,
        itemsizing="constant",
    ),
    margin=dict(t=140, b=160, l=60, r=60),
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
)

# Custom legend entries — asset classes with total weights
for category, color in CATEGORY_COLORS.items():
    category_weight = df[df["category"] == category]["weight"].sum()
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=18, color=color),
            name=f"{category} ({category_weight:.1f}%)",
            showlegend=True,
            hoverinfo="skip",
        )
    )

# Hide individual pie legend entries — only category legend shows
fig.update_traces(showlegend=False, selector=dict(type="pie"))

# Save — square canvas for symmetric pie chart
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
