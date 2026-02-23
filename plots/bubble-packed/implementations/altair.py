"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: altair 6.0.0 | Python 3.14.3
"""

import altair as alt
import numpy as np
import pandas as pd


np.random.seed(42)

# Data - Department budget allocation by division
labels = [
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
]
values = [850, 750, 460, 195, 420, 680, 210, 290, 180, 150, 320, 380, 170, 240, 550]
groups = ["Technology"] * 4 + ["Revenue"] * 3 + ["Corporate"] * 3 + ["Operations"] * 3 + ["Product"] * 2
n = len(labels)

# Area-proportional radius scaling (sqrt for perceptual accuracy)
min_r, max_r = 30, 120
vals = np.array(values, dtype=float)
radii = min_r + (max_r - min_r) * np.sqrt((vals - vals.min()) / (vals.max() - vals.min()))

# Sort largest-first for greedy packing
order = np.argsort(-radii)
radii = radii[order]
labels = [labels[i] for i in order]
values = [values[i] for i in order]
groups = [groups[i] for i in order]

# Circle packing: radial scan places each circle at closest-to-center valid position
x, y = np.zeros(n), np.zeros(n)
gap = 0.5  # minimum gap between circle edges

for i in range(1, n):
    placed = False
    for r in np.arange(0, 600, 0.4):
        n_a = max(72, int(2 * np.pi * r / 1.5))
        theta = np.linspace(0, 2 * np.pi, n_a, endpoint=False)
        px, py = r * np.cos(theta), r * np.sin(theta)
        dx_all = px[:, None] - x[None, :i]
        dy_all = py[:, None] - y[None, :i]
        dists = np.sqrt(dx_all**2 + dy_all**2)
        valid = np.all(dists >= radii[i] + radii[:i] + gap, axis=1)
        if np.any(valid):
            # Pick the most tucked-in position (smallest gap to nearest neighbor)
            valid_idx = np.where(valid)[0]
            surface_gaps = np.min(dists[valid] - radii[i] - radii[:i], axis=1)
            best = valid_idx[np.argmin(surface_gaps)]
            x[i], y[i] = float(px[best]), float(py[best])
            placed = True
            break
    if not placed:
        x[i], y[i] = 0.0, 0.0

# Physics compaction — gravity pulls cluster tighter, overlap resolution prevents merging
for _ in range(300):
    for i in range(n):
        dx, dy = x[i] - x, y[i] - y
        dist = np.sqrt(dx**2 + dy**2) + 0.01
        min_d = radii[i] + radii + 1.5
        overlap = dist < min_d
        overlap[i] = False
        push = np.where(overlap, (min_d - dist) * 0.5, 0)
        x[i] += -x[i] * 0.02 + (dx / dist * push).sum()
        y[i] += -y[i] * 0.02 + (dy / dist * push).sum()

# Center the cluster
x -= (x.min() + x.max()) / 2
y -= (y.min() + y.max()) / 2

# Colorblind-safe palette (teal replaces sage green for deuteranopia safety)
group_order = ["Technology", "Revenue", "Operations", "Corporate", "Product"]
palette = ["#306998", "#E07A5F", "#8B6DA8", "#2A9D8F", "#FFD43B"]

df = pd.DataFrame(
    {
        "label": labels,
        "value": values,
        "group": groups,
        "x": x,
        "y": y,
        "radius": radii,
        "budget": [f"${v}K" for v in values],
    }
)

# Interactive legend selection — click to highlight a division (Altair-distinctive)
selection = alt.selection_point(fields=["group"], bind="legend")

circles = (
    alt.Chart(df)
    .mark_circle(stroke="white", strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(padding=max_r * 0.85)),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(padding=max_r * 0.85)),
        size=alt.Size("radius:Q", scale=alt.Scale(range=[min_r**2 * 3, max_r**2 * 3]), legend=None),
        color=alt.Color(
            "group:N",
            scale=alt.Scale(domain=group_order, range=palette),
            legend=alt.Legend(
                title="Division",
                titleFontSize=20,
                titleFontWeight="bold",
                labelFontSize=18,
                symbolSize=350,
                orient="right",
            ),
        ),
        opacity=alt.condition(selection, alt.value(0.9), alt.value(0.15)),
        tooltip=[
            alt.Tooltip("label:N", title="Department"),
            alt.Tooltip("budget:N", title="Budget"),
            alt.Tooltip("group:N", title="Division"),
        ],
    )
    .add_params(selection)
)

# Labels inside larger bubbles (fontSize=20 for clear legibility)
df_large = df[df["radius"] > 50].copy()
df_large["display_text"] = df_large["label"] + "\n" + df_large["budget"]

labels_layer = (
    alt.Chart(df_large)
    .mark_text(fontWeight="bold", fontSize=20, lineBreak="\n")
    .encode(
        x="x:Q",
        y="y:Q",
        text="display_text:N",
        color=alt.condition(alt.datum.group == "Product", alt.value("#333333"), alt.value("white")),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.1)),
    )
)

chart = (
    alt.layer(circles, labels_layer)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Department Budget Allocation · bubble-packed · altair · pyplots.ai",
            subtitle="Technology division leads at 39% of total budget — Engineering alone accounts for $850K",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#555555",
            fontWeight="bold",
            anchor="middle",
        ),
    )
    .configure_view(strokeWidth=0)
)

chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
