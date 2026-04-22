""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: plotly 6.5.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-20
"""

import pandas as pd
import plotly.graph_objects as go


# Data - Sample investment portfolio with asset classes and holdings
portfolio_data = {
    "asset": [
        # Equities
        "Apple Inc.",
        "Microsoft Corp.",
        "Amazon.com",
        "NVIDIA Corp.",
        # Fixed Income
        "US Treasury 10Y",
        "Corporate Bonds AAA",
        "Municipal Bonds",
        # Alternatives
        "Gold ETF",
        "Real Estate REIT",
        # Cash
        "Money Market Fund",
    ],
    "weight": [15.0, 12.0, 8.0, 10.0, 18.0, 12.0, 8.0, 7.0, 6.0, 4.0],
    "category": [
        "Equities",
        "Equities",
        "Equities",
        "Equities",
        "Fixed Income",
        "Fixed Income",
        "Fixed Income",
        "Alternatives",
        "Alternatives",
        "Cash",
    ],
}

df = pd.DataFrame(portfolio_data)

# Color palette by asset class
category_colors = {
    "Equities": "#306998",  # Python Blue
    "Fixed Income": "#FFD43B",  # Python Yellow
    "Alternatives": "#4CAF50",  # Green
    "Cash": "#9E9E9E",  # Gray
}

# Assign colors based on category
colors = [category_colors[cat] for cat in df["category"]]

# Create main donut chart with all holdings
fig = go.Figure()

# Add pie trace with pull effect for visual separation
fig.add_trace(
    go.Pie(
        labels=df["asset"],
        values=df["weight"],
        hole=0.4,
        marker=dict(colors=colors, line=dict(color="white", width=3)),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=16),
        hovertemplate=("<b>%{label}</b><br>Weight: %{value:.1f}%<br>Category: %{customdata}<br><extra></extra>"),
        customdata=df["category"],
        pull=[0.02] * len(df),
        rotation=90,
    )
)

# Add center annotation showing portfolio type
fig.add_annotation(
    text="<b>Portfolio</b><br>Allocation", x=0.5, y=0.5, font=dict(size=24, color="#333333"), showarrow=False
)

# Create category summary for secondary view
category_summary = df.groupby("category")["weight"].sum().reset_index()
category_summary_colors = [category_colors[cat] for cat in category_summary["category"]]

# Add buttons for switching between views
fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=0.5,
            y=1.12,
            xanchor="center",
            buttons=[
                dict(
                    label="All Holdings",
                    method="update",
                    args=[
                        {
                            "labels": [df["asset"].tolist()],
                            "values": [df["weight"].tolist()],
                            "marker": [dict(colors=colors, line=dict(color="white", width=3))],
                            "customdata": [df["category"].tolist()],
                        },
                        {"annotations[0].text": "<b>Portfolio</b><br>Allocation"},
                    ],
                ),
                dict(
                    label="By Category",
                    method="update",
                    args=[
                        {
                            "labels": [category_summary["category"].tolist()],
                            "values": [category_summary["weight"].tolist()],
                            "marker": [dict(colors=category_summary_colors, line=dict(color="white", width=3))],
                            "customdata": [category_summary["category"].tolist()],
                        },
                        {"annotations[0].text": "<b>Asset Class</b><br>Overview"},
                    ],
                ),
            ],
            font=dict(size=16),
            bgcolor="#f0f0f0",
            bordercolor="#cccccc",
        )
    ]
)

# Layout configuration
fig.update_layout(
    title=dict(
        text="pie-portfolio-interactive · plotly · pyplots.ai",
        font=dict(size=28, color="#333333"),
        x=0.5,
        y=0.95,
        xanchor="center",
    ),
    showlegend=True,
    legend=dict(
        title=dict(text="Asset Class", font=dict(size=18)),
        font=dict(size=16),
        orientation="v",
        yanchor="middle",
        y=0.5,
        xanchor="left",
        x=1.02,
        itemsizing="constant",
    ),
    template="plotly_white",
    margin=dict(t=150, b=50, l=50, r=200),
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
)

# Create custom legend entries for asset classes (since pie doesn't group by category)
for category, color in category_colors.items():
    category_weight = df[df["category"] == category]["weight"].sum()
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=20, color=color),
            name=f"{category} ({category_weight:.1f}%)",
            showlegend=True,
            hoverinfo="skip",
        )
    )

# Hide the pie's individual legend entries and show only category legend
fig.update_traces(showlegend=False, selector=dict(type="pie"))

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
