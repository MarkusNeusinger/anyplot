"""pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

# Risk score matrix (likelihood x impact)
risk_scores = np.array([[1, 2, 3, 4, 5], [2, 4, 6, 8, 10], [3, 6, 9, 12, 15], [4, 8, 12, 16, 20], [5, 10, 15, 20, 25]])

# Color mapping: Low=green, Medium=yellow, High=orange, Critical=red
zone_colors = {0: "#4CAF50", 1: "#FFC107", 2: "#FF9800", 3: "#F44336"}
zone_thresholds = [4, 9, 16, 25]
colors = np.array(
    [[zone_colors[next(i for i, t in enumerate(zone_thresholds) if s <= t)] for s in row] for row in risk_scores]
)

# Risk items with categories
risks = [
    {"name": "Supply Chain\nDisruption", "likelihood": 3, "impact": 4, "category": "Operational"},
    {"name": "Data Breach", "likelihood": 2, "impact": 5, "category": "Technical"},
    {"name": "Budget\nOverrun", "likelihood": 4, "impact": 3, "category": "Financial"},
    {"name": "Key Staff\nTurnover", "likelihood": 3, "impact": 3, "category": "Operational"},
    {"name": "Regulatory\nChange", "likelihood": 2, "impact": 4, "category": "Financial"},
    {"name": "System\nOutage", "likelihood": 3, "impact": 5, "category": "Technical"},
    {"name": "Scope\nCreep", "likelihood": 5, "impact": 2, "category": "Operational"},
    {"name": "Vendor\nFailure", "likelihood": 2, "impact": 3, "category": "Financial"},
    {"name": "Cyber\nAttack", "likelihood": 4, "impact": 5, "category": "Technical"},
    {"name": "Market\nShift", "likelihood": 3, "impact": 2, "category": "Financial"},
    {"name": "Tech Debt\nAccumulation", "likelihood": 5, "impact": 3, "category": "Technical"},
    {"name": "Compliance\nGap", "likelihood": 2, "impact": 4, "category": "Operational"},
]

# Plot - Build heatmap background with individual colored rectangles
fig = go.Figure()

# Add colored cells as shapes and score annotations
for i in range(5):
    for j in range(5):
        fig.add_shape(
            type="rect",
            x0=j + 0.5,
            x1=j + 1.5,
            y0=i + 0.5,
            y1=i + 1.5,
            fillcolor=colors[i][j],
            opacity=0.35,
            line=dict(color="white", width=3),
            layer="below",
        )
        # Zone label in each cell
        score = risk_scores[i][j]
        if score <= 4:
            zone = "Low"
        elif score <= 9:
            zone = "Medium"
        elif score <= 16:
            zone = "High"
        else:
            zone = "Critical"
        fig.add_annotation(
            x=j + 1,
            y=i + 1,
            text=f"<b>{score}</b><br><sub>{zone}</sub>",
            showarrow=False,
            font=dict(size=16, color="#555555"),
            opacity=0.6,
        )

# Category colors for risk markers
category_colors = {"Technical": "#1565C0", "Financial": "#6A1B9A", "Operational": "#E65100"}

# Add jitter for risks sharing cells
jitter_offsets = {}
for risk in risks:
    cell_key = (risk["likelihood"], risk["impact"])
    if cell_key not in jitter_offsets:
        jitter_offsets[cell_key] = 0
    jitter_offsets[cell_key] += 1

cell_counts = {}
for risk in risks:
    cell_key = (risk["likelihood"], risk["impact"])
    if cell_key not in cell_counts:
        cell_counts[cell_key] = 0

    count = jitter_offsets[cell_key]
    idx = cell_counts[cell_key]

    # Jitter pattern for multiple items in same cell
    jitter_x = [-0.2, 0.2, -0.2, 0.2][idx % 4]
    jitter_y = [0.15, 0.15, -0.15, -0.15][idx % 4]
    if count == 1:
        jitter_x, jitter_y = 0, 0

    cell_counts[cell_key] += 1

    cat = risk["category"]
    fig.add_trace(
        go.Scatter(
            x=[risk["impact"] + jitter_x],
            y=[risk["likelihood"] + jitter_y],
            mode="markers+text",
            marker=dict(size=22, color=category_colors[cat], line=dict(color="white", width=2.5), symbol="circle"),
            text=risk["name"],
            textposition="top center",
            textfont=dict(size=13, color=category_colors[cat], family="Arial Black"),
            name=cat,
            legendgroup=cat,
            showlegend=cat not in [r["category"] for r in risks[: risks.index(risk)]],
            hovertemplate=(
                f"<b>{risk['name'].replace(chr(10), ' ')}</b><br>"
                f"Likelihood: {likelihood_labels[risk['likelihood'] - 1]}<br>"
                f"Impact: {impact_labels[risk['impact'] - 1]}<br>"
                f"Risk Score: {risk['likelihood'] * risk['impact']}<br>"
                f"Category: {cat}<extra></extra>"
            ),
        )
    )

# Add legend entries for risk zones
for zone, color in [
    ("Low (1-4)", "#4CAF50"),
    ("Medium (5-9)", "#FFC107"),
    ("High (10-16)", "#FF9800"),
    ("Critical (20-25)", "#F44336"),
]:
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=18, color=color, symbol="square", opacity=0.5),
            name=zone,
            legendgroup="zones",
        )
    )

# Style
fig.update_layout(
    title=dict(text="heatmap-risk-matrix · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Impact", font=dict(size=24)),
        tickvals=[1, 2, 3, 4, 5],
        ticktext=impact_labels,
        tickfont=dict(size=17),
        range=[0.4, 5.6],
        showgrid=False,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Likelihood", font=dict(size=24)),
        tickvals=[1, 2, 3, 4, 5],
        ticktext=likelihood_labels,
        tickfont=dict(size=17),
        range=[0.4, 5.6],
        showgrid=False,
        zeroline=False,
    ),
    template="plotly_white",
    legend=dict(font=dict(size=16), x=1.02, y=1, bgcolor="rgba(255,255,255,0.9)", bordercolor="#cccccc", borderwidth=1),
    margin=dict(l=130, r=200, t=100, b=100),
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
