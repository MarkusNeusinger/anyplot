"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: /100 | Updated: 2026-02-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Department budget allocation with group clusters
np.random.seed(42)
departments = {
    "label": [
        "Engineering",
        "R&D",
        "Data Science",
        "QA",
        "Marketing",
        "Sales",
        "Support",
        "Finance",
        "HR",
        "Legal",
        "Operations",
        "IT",
        "Security",
        "Design",
        "Product",
    ],
    "value": [850, 750, 460, 195, 420, 680, 210, 290, 180, 150, 320, 380, 170, 240, 550],
    "group": [
        "Technology",
        "Technology",
        "Technology",
        "Technology",
        "Revenue",
        "Revenue",
        "Revenue",
        "Corporate",
        "Corporate",
        "Corporate",
        "Operations",
        "Operations",
        "Operations",
        "Product",
        "Product",
    ],
}

labels = departments["label"]
values = departments["value"]
groups = departments["group"]
n = len(labels)

# Scale values to radius (sqrt for area-proportional sizing)
min_radius = 30
max_radius = 120
values_array = np.array(values)
radii = min_radius + (max_radius - min_radius) * np.sqrt(
    (values_array - values_array.min()) / (values_array.max() - values_array.min())
)

# Sort by size (largest first) for better packing
order = np.argsort(-radii)
radii = radii[order]
labels = [labels[i] for i in order]
values = [values[i] for i in order]
groups = [groups[i] for i in order]

# Circle packing - place circles one by one, finding best position
x_pos = np.zeros(n)
y_pos = np.zeros(n)

for i in range(1, n):
    best_x, best_y = 0.0, 0.0
    best_dist = float("inf")

    for j in range(i):
        for angle in np.linspace(0, 2 * np.pi, 36, endpoint=False):
            test_x = x_pos[j] + (radii[j] + radii[i] + 2) * np.cos(angle)
            test_y = y_pos[j] + (radii[j] + radii[i] + 2) * np.sin(angle)

            valid = True
            for k in range(i):
                dx = test_x - x_pos[k]
                dy = test_y - y_pos[k]
                if np.sqrt(dx**2 + dy**2) < radii[i] + radii[k] + 1:
                    valid = False
                    break

            if valid:
                center_dist = np.sqrt(test_x**2 + test_y**2)
                if center_dist < best_dist:
                    best_dist = center_dist
                    best_x, best_y = test_x, test_y

    x_pos[i] = best_x
    y_pos[i] = best_y

# Physics simulation for tighter packing
for _ in range(200):
    for i in range(n):
        fx, fy = -x_pos[i] * 0.01, -y_pos[i] * 0.01
        for j in range(n):
            if i != j:
                dx = x_pos[i] - x_pos[j]
                dy = y_pos[i] - y_pos[j]
                dist = np.sqrt(dx**2 + dy**2) + 0.1
                min_dist = radii[i] + radii[j] + 2
                if dist < min_dist:
                    force = (min_dist - dist) * 0.5
                    fx += (dx / dist) * force
                    fy += (dy / dist) * force
        x_pos[i] += fx
        y_pos[i] += fy

# Center the layout
x_center = (x_pos.min() + x_pos.max()) / 2
y_center = (y_pos.min() + y_pos.max()) / 2
x_pos -= x_center
y_pos -= y_center

# Group color palette - colorblind-safe
group_colors = {
    "Technology": "#306998",
    "Revenue": "#E07A5F",
    "Corporate": "#7B9E89",
    "Operations": "#4A90A4",
    "Product": "#FFD43B",
}

df = pd.DataFrame(
    {
        "label": labels,
        "value": values,
        "group": groups,
        "x": x_pos,
        "y": y_pos,
        "radius": radii,
        "budget": [f"${v}K" for v in values],
    }
)

# Group ordering for consistent legend
group_order = ["Technology", "Revenue", "Operations", "Corporate", "Product"]

# Circles layer
circles = (
    alt.Chart(df)
    .mark_circle(opacity=0.85, stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(padding=max_radius * 1.4)),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(padding=max_radius * 1.4)),
        size=alt.Size("radius:Q", scale=alt.Scale(range=[min_radius**2 * 3, max_radius**2 * 3]), legend=None),
        color=alt.Color(
            "group:N",
            scale=alt.Scale(domain=group_order, range=[group_colors[g] for g in group_order]),
            legend=alt.Legend(
                title="Division",
                titleFontSize=18,
                titleFontWeight="bold",
                labelFontSize=15,
                symbolSize=300,
                orient="none",
                legendX=1400,
                legendY=680,
                direction="vertical",
            ),
        ),
        tooltip=[
            alt.Tooltip("label:N", title="Department"),
            alt.Tooltip("budget:N", title="Budget"),
            alt.Tooltip("group:N", title="Division"),
        ],
    )
)

# Labels inside larger bubbles
df_large = df[df["radius"] > 50].copy()
df_large["display_text"] = df_large["label"] + "\n" + df_large["budget"]

labels_layer = (
    alt.Chart(df_large)
    .mark_text(fontWeight="bold", fontSize=13, lineBreak="\n")
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q"),
        text="display_text:N",
        color=alt.condition(alt.datum.group == "Product", alt.value("#333333"), alt.value("white")),
    )
)

# Combine layers
chart = (
    alt.layer(circles, labels_layer)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Department Budget Allocation · bubble-packed · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="middle",
        ),
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
