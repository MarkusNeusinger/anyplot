""" pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-17
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

# Risk score matrix (likelihood x impact)
risk_scores = np.array([[1, 2, 3, 4, 5], [2, 4, 6, 8, 10], [3, 6, 9, 12, 15], [4, 8, 12, 16, 20], [5, 10, 15, 20, 25]])

# Zone thresholds and colorblind-safe palette (blue → amber → burnt orange → crimson)
zone_thresholds = [(4, "Low"), (9, "Medium"), (16, "High"), (25, "Critical")]
zone_colors = {"Low": "#5C9BD5", "Medium": "#F4B942", "High": "#E8713A", "Critical": "#C0392B"}
zone_bg = {
    "Low": "rgba(92,155,213,0.22)",
    "Medium": "rgba(244,185,66,0.25)",
    "High": "rgba(232,113,58,0.22)",
    "Critical": "rgba(192,57,43,0.20)",
}

# Risk items with categories
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

# Category styling — distinct shapes per category for additional encoding
category_colors = {"Technical": "#1565C0", "Financial": "#7B1FA2", "Operational": "#E65100"}
category_symbols = {"Technical": "circle", "Financial": "diamond", "Operational": "square"}

# Pre-compute cell occupancy for jitter
cell_items = {}
for risk in risks:
    key = (risk["likelihood"], risk["impact"])
    cell_items.setdefault(key, []).append(risk)

jitter_offsets = {
    1: [(0, 0)],
    2: [(-0.18, 0.12), (0.18, -0.12)],
    3: [(-0.22, 0.14), (0.22, 0.14), (0, -0.16)],
    4: [(-0.22, 0.14), (0.22, 0.14), (-0.22, -0.14), (0.22, -0.14)],
}

# Plot
fig = go.Figure()

# Colored cell backgrounds with refined borders
for i in range(5):
    for j in range(5):
        score = risk_scores[i][j]
        zone = next(name for threshold, name in zone_thresholds if score <= threshold)
        fig.add_shape(
            type="rect",
            x0=j + 0.5,
            x1=j + 1.5,
            y0=i + 0.5,
            y1=i + 1.5,
            fillcolor=zone_bg[zone],
            line={"color": "white", "width": 3},
            layer="below",
        )
        # Score label at bottom-right of each cell
        fig.add_annotation(
            x=j + 1.38,
            y=i + 0.58,
            text=f"<b>{score}</b>",
            showarrow=False,
            font={"size": 14, "color": "rgba(100,100,100,0.45)", "family": "Arial"},
            xanchor="right",
            yanchor="bottom",
        )

# Risk markers with visual hierarchy by zone severity
seen_categories = set()
for risk in risks:
    key = (risk["likelihood"], risk["impact"])
    items = cell_items[key]
    idx = items.index(risk)
    n = len(items)

    jx, jy = jitter_offsets[min(n, 4)][idx % min(n, 4)]
    cat = risk["category"]
    score = risk["likelihood"] * risk["impact"]
    zone = next(name for threshold, name in zone_thresholds if score <= threshold)

    # Visual hierarchy: critical risks are larger and bolder
    sizes = {
        "Critical": (30, 4, 800, 15),
        "High": (25, 3, 600, 14),
        "Medium": (20, 2.5, 400, 13),
        "Low": (18, 2, 400, 13),
    }
    marker_size, outline_width, font_weight, font_size = sizes[zone]

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
                "symbol": category_symbols[cat],
                "opacity": 0.92,
            },
            text=f"<b>{risk['name']}</b>",
            textposition="top center",
            textfont={"size": font_size, "color": category_colors[cat], "weight": font_weight, "family": "Arial"},
            name=cat,
            legendgroup=cat,
            showlegend=show_legend,
            hovertemplate=(
                f"<b>{risk['name']}</b><br>"
                f"Likelihood: {likelihood_labels[risk['likelihood'] - 1]}<br>"
                f"Impact: {impact_labels[risk['impact'] - 1]}<br>"
                f"Risk Score: {score} ({zone})<br>"
                f"Category: {cat}<extra></extra>"
            ),
        )
    )

# Zone legend entries with group title
for zone_name, color in zone_colors.items():
    ranges = {"Low": "1–4", "Medium": "5–9", "High": "10–16", "Critical": "20–25"}
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 20, "color": color, "symbol": "square", "opacity": 0.5},
            name=f"  {zone_name} ({ranges[zone_name]})",
            legendgroup="zones",
            legendgrouptitle={"text": "Risk Zones", "font": {"size": 14, "color": "#555"}},
        )
    )

# Layout with refined typography and subtitle
fig.update_layout(
    title={
        "text": (
            "heatmap-risk-matrix · plotly · pyplots.ai"
            "<br><sup style='color:#777;font-weight:normal'>"
            "Enterprise Risk Assessment — Likelihood vs Impact Matrix</sup>"
        ),
        "font": {"size": 28, "color": "#2C3E50", "family": "Arial Black, Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "title": {"text": "Impact Severity →", "font": {"size": 22, "color": "#444"}, "standoff": 15},
        "tickvals": [1, 2, 3, 4, 5],
        "ticktext": impact_labels,
        "tickfont": {"size": 18, "color": "#444"},
        "range": [0.35, 5.65],
        "showgrid": False,
        "zeroline": False,
        "fixedrange": True,
    },
    yaxis={
        "title": {"text": "← Likelihood", "font": {"size": 22, "color": "#444"}, "standoff": 15},
        "tickvals": [1, 2, 3, 4, 5],
        "ticktext": likelihood_labels,
        "tickfont": {"size": 18, "color": "#444"},
        "range": [0.35, 5.65],
        "showgrid": False,
        "zeroline": False,
        "fixedrange": True,
    },
    template="plotly_white",
    legend={
        "font": {"size": 15, "color": "#444"},
        "x": 1.01,
        "y": 1,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": "rgba(255,255,255,0.95)",
        "bordercolor": "#ddd",
        "borderwidth": 1,
        "tracegroupgap": 12,
        "itemsizing": "constant",
    },
    margin={"l": 120, "r": 230, "t": 120, "b": 90},
    plot_bgcolor="white",
    paper_bgcolor="white",
    hoverlabel={"bgcolor": "white", "bordercolor": "#ccc", "font": {"size": 14, "family": "Arial"}},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
