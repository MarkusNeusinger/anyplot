""" anyplot.ai
bar-spine: Spine Plot for Two-Variable Proportions
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-08
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data: subscription outcomes by acquisition channel
channels = ["Direct", "Organic Search", "Social Media", "Email", "Referral"]
channel_sizes = [400, 620, 830, 310, 240]

outcome_counts = {
    "Active": [220, 380, 350, 170, 185],
    "On Trial": [110, 155, 215, 80, 40],
    "Cancelled": [70, 85, 265, 60, 15],
}

# Bar widths proportional to marginal counts
total = sum(channel_sizes)
widths = [c / total for c in channel_sizes]

# Bar centers along the x-axis (cumulative)
centers = []
pos = 0.0
for w in widths:
    centers.append(pos + w / 2)
    pos += w

# Conditional proportions within each bar (heights sum to 1)
outcome_props = {k: [cnt / m for cnt, m in zip(v, channel_sizes)] for k, v in outcome_counts.items()}

# Okabe-Ito palette: Active=green(1), On Trial=orange(5), Cancelled=vermillion(2)
COLORS = {"Active": "#009E73", "On Trial": "#AE3030", "Cancelled": "#C475FD"}

# Plot
fig = go.Figure()

for outcome in ["Active", "On Trial", "Cancelled"]:
    props = outcome_props[outcome]
    labels = [f"{p:.0%}" if p >= 0.09 else "" for p in props]
    fig.add_trace(
        go.Bar(
            name=outcome,
            x=centers,
            y=props,
            width=widths,
            marker_color=COLORS[outcome],
            marker_line_width=0,
            text=labels,
            textposition="inside",
            textfont=dict(size=16, color="white"),
            hovertemplate=[
                f"<b>{ch}</b><br>{outcome}: {p:.1%}<br>n={m:,}<extra></extra>"
                for ch, p, m in zip(channels, props, channel_sizes)
            ],
        )
    )

ticktext = [f"<b>{ch}</b><br>n={m:,}" for ch, m in zip(channels, channel_sizes)]

fig.update_layout(
    barmode="stack",
    bargap=0,
    title=dict(
        text="Subscription Outcomes by Channel · bar-spine · plotly · anyplot.ai",
        font=dict(size=28, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Acquisition Channel", font=dict(size=22, color=INK)),
        tickmode="array",
        tickvals=centers,
        ticktext=ticktext,
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, 1],
        showgrid=False,
        zeroline=False,
        linecolor=INK_SOFT,
        showline=True,
        ticks="",
    ),
    yaxis=dict(
        title=dict(text="Proportion of Customers", font=dict(size=22, color=INK)),
        tickformat=".0%",
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, 1.01],
        gridcolor=GRID,
        showgrid=True,
        linecolor=INK_SOFT,
        showline=True,
        zeroline=False,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        title=dict(text="Status", font=dict(color=INK, size=18)),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        font=dict(color=INK_SOFT, size=16),
        traceorder="normal",
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
    ),
    margin=dict(l=90, r=40, t=100, b=100),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
