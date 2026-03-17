"""pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-17
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

# Risk score matrix (likelihood x impact)
risk_scores = np.array([[1, 2, 3, 4, 5], [2, 4, 6, 8, 10], [3, 6, 9, 12, 15], [4, 8, 12, 16, 20], [5, 10, 15, 20, 25]])

# Colorblind-safe zone colors (blue-yellow-orange-purple instead of green-red)
zone_colors = {"Low": "#2196F3", "Medium": "#FFB300", "High": "#E65100", "Critical": "#880E4F"}


def get_zone(score):
    if score <= 4:
        return "Low"
    elif score <= 9:
        return "Medium"
    elif score <= 16:
        return "High"
    return "Critical"


# Risk items with categories (single-line names to avoid overlap)
risks = [
    {"name": "Supply Chain", "likelihood": 3, "impact": 4, "category": "Operational"},
    {"name": "Data Breach", "likelihood": 2, "impact": 5, "category": "Technical"},
    {"name": "Budget Overrun", "likelihood": 4, "impact": 3, "category": "Financial"},
    {"name": "Staff Turnover", "likelihood": 3, "impact": 3, "category": "Operational"},
    {"name": "Regulatory", "likelihood": 2, "impact": 4, "category": "Financial"},
    {"name": "System Outage", "likelihood": 3, "impact": 5, "category": "Technical"},
    {"name": "Scope Creep", "likelihood": 5, "impact": 2, "category": "Operational"},
    {"name": "Vendor Failure", "likelihood": 2, "impact": 3, "category": "Financial"},
    {"name": "Cyber Attack", "likelihood": 4, "impact": 5, "category": "Technical"},
    {"name": "Market Shift", "likelihood": 3, "impact": 2, "category": "Financial"},
    {"name": "Tech Debt", "likelihood": 5, "impact": 3, "category": "Technical"},
    {"name": "Compliance Gap", "likelihood": 2, "impact": 4, "category": "Operational"},
]

# Category colors
category_colors = {"Technical": "#1565C0", "Financial": "#6A1B9A", "Operational": "#E65100"}

# Compute jitter offsets per cell
cell_items = {}
for risk in risks:
    key = (risk["likelihood"], risk["impact"])
    cell_items.setdefault(key, []).append(risk)

jitter_patterns = [(-0.2, 0.15), (0.2, 0.15), (-0.2, -0.15), (0.2, -0.15)]

# Plot
fig = go.Figure()

# Add colored cells as shapes and score annotations (placed at bottom of cell to avoid label overlap)
for i in range(5):
    for j in range(5):
        score = risk_scores[i][j]
        zone = get_zone(score)
        fig.add_shape(
            type="rect",
            x0=j + 0.5,
            x1=j + 1.5,
            y0=i + 0.5,
            y1=i + 1.5,
            fillcolor=zone_colors[zone],
            opacity=0.3,
            line={"color": "white", "width": 3},
            layer="below",
        )
        # Place score annotation at bottom-right of cell to avoid marker/label overlap
        fig.add_annotation(
            x=j + 1.35,
            y=i + 0.6,
            text=f"<sub>{score}</sub>",
            showarrow=False,
            font={"size": 13, "color": "#888888"},
            opacity=0.5,
            xanchor="right",
            yanchor="bottom",
        )

# Add risk markers with visual hierarchy based on risk score
seen_categories = set()
for risk in risks:
    key = (risk["likelihood"], risk["impact"])
    items = cell_items[key]
    idx = items.index(risk)

    if len(items) == 1:
        jx, jy = 0, 0
    else:
        jx, jy = jitter_patterns[idx % 4]

    cat = risk["category"]
    score = risk["likelihood"] * risk["impact"]
    zone = get_zone(score)

    # Visual hierarchy: critical risks are larger and bolder
    if zone == "Critical":
        marker_size, outline_width, font_weight = 28, 3.5, 700
    elif zone == "High":
        marker_size, outline_width, font_weight = 24, 3, 600
    else:
        marker_size, outline_width, font_weight = 18, 2, 400

    show_legend = cat not in seen_categories
    seen_categories.add(cat)

    fig.add_trace(
        go.Scatter(
            x=[risk["impact"] + jx],
            y=[risk["likelihood"] + jy],
            mode="markers+text",
            marker={
                "size": marker_size,
                "color": category_colors[cat],
                "line": {"color": "white", "width": outline_width},
                "symbol": "circle",
            },
            text=risk["name"],
            textposition="top center",
            textfont={"size": 11, "color": category_colors[cat], "weight": font_weight},
            name=cat,
            legendgroup=cat,
            showlegend=show_legend,
            hovertemplate=(
                f"<b>{risk['name']}</b><br>"
                f"Likelihood: {likelihood_labels[risk['likelihood'] - 1]}<br>"
                f"Impact: {impact_labels[risk['impact'] - 1]}<br>"
                f"Risk Score: {score}<br>"
                f"Category: {cat}<extra></extra>"
            ),
        )
    )

# Add legend entries for risk zones
for zone_name, color in zone_colors.items():
    thresholds = {"Low": "1-4", "Medium": "5-9", "High": "10-16", "Critical": "20-25"}
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 18, "color": color, "symbol": "square", "opacity": 0.5},
            name=f"{zone_name} ({thresholds[zone_name]})",
            legendgroup="zones",
        )
    )

# Style
fig.update_layout(
    title={
        "text": "heatmap-risk-matrix · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Impact", "font": {"size": 24}},
        "tickvals": [1, 2, 3, 4, 5],
        "ticktext": impact_labels,
        "tickfont": {"size": 17},
        "range": [0.4, 5.6],
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Likelihood", "font": {"size": 24}},
        "tickvals": [1, 2, 3, 4, 5],
        "ticktext": likelihood_labels,
        "tickfont": {"size": 17},
        "range": [0.4, 5.6],
        "showgrid": False,
        "zeroline": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 16},
        "x": 1.02,
        "y": 1,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "#cccccc",
        "borderwidth": 1,
    },
    margin={"l": 130, "r": 200, "t": 100, "b": 100},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
