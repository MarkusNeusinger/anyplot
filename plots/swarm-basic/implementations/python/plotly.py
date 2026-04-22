""" pyplots.ai
swarm-basic: Basic Swarm Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - student test scores across 4 classrooms with varied distributions
np.random.seed(42)
classrooms = ["Room A", "Room B", "Room C", "Room D"]
colors = ["#306998", "#FFD43B", "#5A9BD4", "#E07B39"]

scores_a = np.concatenate([np.random.normal(75, 8, 35), np.random.normal(90, 5, 10)])
scores_b = np.random.normal(68, 12, 50)  # Wide spread
scores_c = np.concatenate([np.random.normal(60, 6, 20), np.random.normal(82, 6, 25)])  # Bimodal
scores_d = np.random.normal(78, 6, 40)  # Tight cluster

all_data = [scores_a, scores_b, scores_c, scores_d]

# Calculate beeswarm positions for each category
x_all = []
y_all = []
color_all = []
classroom_all = []

for cat_idx, scores in enumerate(all_data):
    # Sort values to place nearby values together
    sorted_indices = np.argsort(scores)
    y_sorted = scores[sorted_indices]
    x_positions = np.zeros(len(scores))

    value_range = scores.max() - scores.min()
    point_threshold = 0.015 * value_range  # Vertical proximity threshold

    for i, orig_idx in enumerate(sorted_indices):
        y_val = y_sorted[i]

        # Find points already placed that are nearby vertically
        placed_y = y_sorted[:i]
        placed_x = x_positions[sorted_indices[:i]]
        nearby_mask = np.abs(placed_y - y_val) < point_threshold

        if not np.any(nearby_mask):
            x_positions[orig_idx] = cat_idx
        else:
            nearby_x = placed_x[nearby_mask]
            # Find available horizontal slot by alternating left/right
            offset = 0.02
            found = False
            for sign in [1, -1, 1, -1, 1, -1, 1, -1]:
                test_x = cat_idx + sign * offset
                if not np.any(np.abs(nearby_x - test_x) < 0.015):
                    x_positions[orig_idx] = test_x
                    found = True
                    break
                offset += 0.015
            if not found:
                x_positions[orig_idx] = cat_idx + np.random.uniform(-0.2, 0.2)

    x_all.extend(x_positions)
    y_all.extend(scores)
    color_all.extend([colors[cat_idx]] * len(scores))
    classroom_all.extend([classrooms[cat_idx]] * len(scores))

# Create figure
fig = go.Figure()

# Add swarm points for each category
for cat_idx, (classroom, scores) in enumerate(zip(classrooms, all_data, strict=True)):
    mask = [c == classroom for c in classroom_all]
    x_cat = [x_all[i] for i in range(len(x_all)) if mask[i]]
    y_cat = [y_all[i] for i in range(len(y_all)) if mask[i]]

    fig.add_trace(
        go.Scatter(
            x=x_cat,
            y=y_cat,
            mode="markers",
            name=classroom,
            marker={"size": 14, "color": colors[cat_idx], "opacity": 0.8, "line": {"width": 1.5, "color": "#333333"}},
            hovertemplate=f"{classroom}<br>Score: %{{y:.1f}}<extra></extra>",
        )
    )

    # Add mean marker
    mean_val = np.mean(scores)
    fig.add_trace(
        go.Scatter(
            x=[cat_idx],
            y=[mean_val],
            mode="markers",
            marker={"symbol": "diamond", "size": 20, "color": "white", "line": {"width": 3, "color": colors[cat_idx]}},
            showlegend=False,
            hovertemplate=f"{classroom} Mean: {mean_val:.1f}<extra></extra>",
        )
    )

# Layout
fig.update_layout(
    title={"text": "swarm-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Classroom", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "tickmode": "array",
        "tickvals": list(range(len(classrooms))),
        "ticktext": classrooms,
        "gridcolor": "rgba(0,0,0,0.05)",
    },
    yaxis={
        "title": {"text": "Test Score", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "range": [35, 105],
    },
    template="plotly_white",
    showlegend=True,
    legend={"font": {"size": 18}, "x": 1.02, "y": 0.98, "xanchor": "left"},
    margin={"l": 100, "r": 150, "t": 100, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
