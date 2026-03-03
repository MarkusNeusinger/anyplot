"""pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: plotly 6.6.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-03
"""

import plotly.graph_objects as go


# Data: Survey tracking 1000 respondents' opinions on public transit expansion
# across 4 quarterly waves, showing gradual polarization from center
waves = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
n_cats = len(categories)
n_waves = len(waves)

# Category colors (diverging: blue for agreement, gray for neutral, warm for disagreement)
cat_colors = {
    "Strongly Agree": "#306998",
    "Agree": "#72B7D4",
    "Neutral": "#888888",
    "Disagree": "#E8853D",
    "Strongly Disagree": "#C44E52",
}

# Transition flows between consecutive waves
# (source_cat_idx, target_cat_idx, count)
# Designed to show gradual polarization: Neutral shrinks as extremes grow
# Wave 1 sizes: SA=150, A=250, N=300, D=200, SD=100
transitions_w1_w2 = [
    (0, 0, 130),
    (0, 1, 20),
    (1, 0, 25),
    (1, 1, 200),
    (1, 2, 25),
    (2, 1, 20),
    (2, 2, 230),
    (2, 3, 35),
    (2, 4, 15),
    (3, 2, 10),
    (3, 3, 165),
    (3, 4, 25),
    (4, 3, 5),
    (4, 4, 95),
]
# Wave 2 sizes: SA=155, A=240, N=265, D=205, SD=135
transitions_w2_w3 = [
    (0, 0, 135),
    (0, 1, 20),
    (1, 0, 30),
    (1, 1, 185),
    (1, 2, 25),
    (2, 1, 15),
    (2, 2, 195),
    (2, 3, 40),
    (2, 4, 15),
    (3, 2, 10),
    (3, 3, 170),
    (3, 4, 25),
    (4, 3, 5),
    (4, 4, 130),
]
# Wave 3 sizes: SA=165, A=220, N=230, D=215, SD=170
transitions_w3_w4 = [
    (0, 0, 150),
    (0, 1, 15),
    (1, 0, 35),
    (1, 1, 160),
    (1, 2, 25),
    (2, 1, 10),
    (2, 2, 160),
    (2, 3, 45),
    (2, 4, 15),
    (3, 2, 10),
    (3, 3, 175),
    (3, 4, 30),
    (4, 3, 5),
    (4, 4, 165),
]
# Wave 4 sizes: SA=185, A=185, N=195, D=225, SD=210

all_transitions = [transitions_w1_w2, transitions_w2_w3, transitions_w3_w4]

# Per-wave totals for node labels
wave_totals = [
    [150, 250, 300, 200, 100],
    [155, 240, 265, 205, 135],
    [165, 220, 230, 215, 170],
    [185, 185, 195, 225, 210],
]

# Build node arrays
node_labels = []
node_colors = []
x_positions = []
y_positions = []

for w in range(n_waves):
    for c in range(n_cats):
        cat_name = categories[c]
        count = wave_totals[w][c]
        node_labels.append(f"{cat_name}<br>{count}")
        node_colors.append(cat_colors[cat_name])
        x_positions.append(0.05 + (w / (n_waves - 1)) * 0.80)
        y_positions.append(0.10 + (c / (n_cats - 1)) * 0.82)

# Build link arrays
sources = []
targets = []
values = []
link_colors = []
link_customdata = []

for wave_idx, trans in enumerate(all_transitions):
    for src_cat, tgt_cat, count in trans:
        src_node = wave_idx * n_cats + src_cat
        tgt_node = (wave_idx + 1) * n_cats + tgt_cat
        sources.append(src_node)
        targets.append(tgt_node)
        values.append(count)

        # Stable flows (same category) get higher opacity to visually distinguish
        is_stable = src_cat == tgt_cat
        base_color = cat_colors[categories[src_cat]]
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        opacity = 0.55 if is_stable else 0.30
        link_colors.append(f"rgba({r},{g},{b},{opacity})")

        link_customdata.append(
            [
                categories[src_cat],
                waves[wave_idx],
                categories[tgt_cat],
                waves[wave_idx + 1],
                "Stable" if is_stable else "Changed",
            ]
        )

# Plot
fig = go.Figure(
    data=[
        go.Sankey(
            arrangement="snap",
            node={
                "pad": 25,
                "thickness": 35,
                "line": {"color": "white", "width": 2},
                "label": node_labels,
                "color": node_colors,
                "x": x_positions,
                "y": y_positions,
                "hovertemplate": "<b>%{label}</b><br>Respondents: %{value:,}<extra></extra>",
            },
            link={
                "source": sources,
                "target": targets,
                "value": values,
                "color": link_colors,
                "customdata": link_customdata,
                "hovertemplate": (
                    "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                    "→ <b>%{customdata[2]}</b> (%{customdata[3]})<br>"
                    "Respondents: <b>%{value:,}</b><br>"
                    "Status: %{customdata[4]}<extra></extra>"
                ),
            },
        )
    ]
)

# Wave column headers (paper coordinates, positioned above nodes)
wave_x_paper = [0.07, 0.335, 0.60, 0.865]
for i, wave in enumerate(waves):
    fig.add_annotation(
        x=wave_x_paper[i],
        y=1.03,
        xref="paper",
        yref="paper",
        text=f"<b>{wave}</b>",
        showarrow=False,
        font={"size": 24, "color": "#333333"},
        xanchor="center",
    )

# Net flow annotations on the right side to highlight polarization trends
net_changes = []
for c in range(n_cats):
    delta = wave_totals[-1][c] - wave_totals[0][c]
    net_changes.append((categories[c], delta, cat_colors[categories[c]]))

# Legend using invisible scatter traces
for cat, color in cat_colors.items():
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 18, "color": color, "symbol": "square"},
            name=cat,
            showlegend=True,
        )
    )

# Net change annotations on right side of diagram
# Sankey in Plotly uses y where 0=top, 1=bottom in node positioning
# Paper coordinates use y where 0=bottom, 1=top
# We need to invert: paper_y = 1 - node_y (approximately)
for c in range(n_cats):
    cat_name, delta, color = net_changes[c]
    sign = "+" if delta > 0 else ""
    node_y = 0.10 + (c / (n_cats - 1)) * 0.82
    paper_y = 1.0 - node_y
    fig.add_annotation(
        x=0.99,
        y=paper_y,
        xref="paper",
        yref="paper",
        text=f"<b>{sign}{delta}</b>",
        showarrow=False,
        font={"size": 20, "color": color},
        xanchor="left",
    )

# Style
fig.update_layout(
    title={
        "text": "Opinion Polarization on Public Transit · alluvial-opinion-flow · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
    },
    font={"size": 18, "color": "#333333"},
    template="plotly_white",
    margin={"l": 40, "r": 60, "t": 160, "b": 90},
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": -0.08,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 18},
        "itemsizing": "constant",
    },
    xaxis={"visible": False},
    yaxis={"visible": False},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
