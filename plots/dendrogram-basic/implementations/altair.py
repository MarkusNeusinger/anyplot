""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: altair 6.0.0 | Python 3.14.3
Quality: 88/100 | Updated: 2026-04-05
"""

import altair as alt
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from sklearn.datasets import load_iris


# Data - Iris flower measurements (15 samples, 3 species)
iris = load_iris()
indices = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140]
features = iris.data[indices]
species_names = ["Setosa", "Versicolor", "Virginica"]
labels = [f"{species_names[iris.target[i]]}-{i}" for i in indices]

# Compute hierarchical clustering using Ward's method
Z = linkage(features, method="ward")
dendro = dendrogram(Z, labels=labels, no_plot=True)

# Assign cluster colors based on distance threshold
distance_threshold = 5.0
cluster_ids = fcluster(Z, t=distance_threshold, criterion="distance")
cluster_colors = {1: "#306998", 2: "#D4A017", 3: "#7B68AE"}

# Build a mapping from leaf index to cluster color, then propagate to merges
n_leaves = len(labels)
node_colors = {}
for idx in dendro["leaves"]:
    node_colors[idx] = cluster_colors.get(cluster_ids[idx], "#888888")

# Track merged node colors through linkage
for i, row in enumerate(Z):
    left, right = int(row[0]), int(row[1])
    left_c = node_colors.get(left, "#888888")
    right_c = node_colors.get(right, "#888888")
    node_colors[n_leaves + i] = left_c if left_c == right_c else "#888888"

# Extract line segments with cluster-based coloring
segments = []
for merge_idx, (xpts, ypts) in enumerate(zip(dendro["icoord"], dendro["dcoord"], strict=True)):
    merge_height = max(ypts)
    left_node = int(Z[merge_idx, 0])
    right_node = int(Z[merge_idx, 1])
    left_c = node_colors.get(left_node, "#888888")
    right_c = node_colors.get(right_node, "#888888")
    merge_c = left_c if left_c == right_c else "#888888"

    # Left vertical
    segments.append(
        {"x": xpts[0], "y": ypts[0], "x2": xpts[1], "y2": ypts[1], "color": left_c, "distance": round(merge_height, 2)}
    )
    # Horizontal bar
    segments.append(
        {"x": xpts[1], "y": ypts[1], "x2": xpts[2], "y2": ypts[2], "color": merge_c, "distance": round(merge_height, 2)}
    )
    # Right vertical
    segments.append(
        {"x": xpts[2], "y": ypts[2], "x2": xpts[3], "y2": ypts[3], "color": right_c, "distance": round(merge_height, 2)}
    )

segments_df = pd.DataFrame(segments)

# Leaf label positions from scipy (positioned at 5, 15, 25, ...)
leaf_labels = dendro["ivl"]
leaf_df = pd.DataFrame(
    {
        "x": [5 + 10 * i for i in range(len(leaf_labels))],
        "y_base": [0.0] * len(leaf_labels),
        "label": leaf_labels,
        "species": [lbl.rsplit("-", 1)[0] for lbl in leaf_labels],
    }
)

# Species color palette starting with Python Blue
species_palette = {"Setosa": "#306998", "Versicolor": "#D4A017", "Virginica": "#7B68AE"}

# Axis domain
x_min = min(s["x"] for s in segments) - 8
x_max = max(s["x2"] for s in segments) + 8
y_max = Z[:, 2].max() * 1.15

# Annotation for the final merge (top of tree) — key storytelling element
top_merge_y = Z[-1, 2]
top_merge_x = (dendro["icoord"][-1][1] + dendro["icoord"][-1][2]) / 2
annotation_df = pd.DataFrame(
    {"x": [top_merge_x], "y": [top_merge_y], "text": ["Setosa diverges\nfrom Versicolor + Virginica"]}
)

# Interactive selection: click legend to highlight a species
species_selection = alt.selection_point(fields=["species"], bind="legend")

# Dendrogram branches with cluster-based coloring and tooltips
branches = (
    alt.Chart(segments_df)
    .mark_rule(strokeWidth=3)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[x_min, x_max]), axis=None),
        x2="x2:Q",
        y=alt.Y("y:Q", title="Distance (Ward's method)", scale=alt.Scale(domain=[0, y_max])),
        y2="y2:Q",
        color=alt.Color("color:N", scale=None),
        tooltip=[alt.Tooltip("distance:Q", title="Merge Distance", format=".2f")],
    )
)

# Leaf markers at base of dendrogram colored by species
leaf_dots = (
    alt.Chart(leaf_df)
    .mark_point(size=180, filled=True, strokeWidth=1.5, stroke="white")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[x_min, x_max]), axis=None),
        y=alt.Y("y_base:Q", scale=alt.Scale(domain=[0, y_max])),
        color=alt.Color(
            "species:N",
            scale=alt.Scale(domain=list(species_palette.keys()), range=list(species_palette.values())),
            legend=alt.Legend(
                title="Species",
                titleFontSize=18,
                titleFontWeight="bold",
                labelFontSize=16,
                symbolSize=220,
                orient="right",
                offset=10,
                titleColor="#333333",
                labelColor="#444444",
            ),
        ),
        tooltip=[alt.Tooltip("label:N", title="Sample"), alt.Tooltip("species:N", title="Species")],
        opacity=alt.condition(species_selection, alt.value(1.0), alt.value(0.15)),
    )
    .add_params(species_selection)
)

# Leaf labels colored by species
leaf_text = (
    alt.Chart(leaf_df)
    .mark_text(angle=315, align="right", baseline="top", fontSize=16, fontWeight="bold", dx=-4, dy=4)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[x_min, x_max]), axis=None),
        y=alt.value(870),
        text="label:N",
        color=alt.Color(
            "species:N",
            scale=alt.Scale(domain=list(species_palette.keys()), range=list(species_palette.values())),
            legend=None,
        ),
        opacity=alt.condition(species_selection, alt.value(1.0), alt.value(0.15)),
    )
)

# Distance threshold reference line
threshold_df = pd.DataFrame({"y": [distance_threshold]})
threshold_line = (
    alt.Chart(threshold_df).mark_rule(strokeDash=[8, 6], strokeWidth=1.8, color="#CC4444", opacity=0.7).encode(y="y:Q")
)

threshold_label = (
    alt.Chart(threshold_df)
    .mark_text(align="left", baseline="bottom", fontSize=14, color="#CC4444", fontStyle="italic", dx=5, dy=-5)
    .encode(x=alt.value(10), y="y:Q", text=alt.value("cluster threshold (d = 5.0)"))
)

# Annotation at top merge point
top_annotation = (
    alt.Chart(annotation_df)
    .mark_text(align="left", baseline="middle", fontSize=14, fontWeight="bold", color="#555555", lineBreak="\n", dx=12)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

top_arrow = (
    alt.Chart(annotation_df)
    .mark_point(shape="triangle-left", size=80, filled=True, color="#888888")
    .encode(x="x:Q", y="y:Q")
)

# Combine layers
chart = (
    alt.layer(branches, threshold_line, threshold_label, leaf_dots, leaf_text, top_arrow, top_annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "dendrogram-basic · altair · pyplots.ai",
            subtitle="Ward's linkage on Iris measurements — Setosa separates clearly from Versicolor / Virginica",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
            anchor="start",
            offset=20,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#333333",
        labelColor="#555555",
        gridOpacity=0.12,
        gridDash=[3, 5],
        gridColor="#cccccc",
        domainColor="#aaaaaa",
        domainWidth=1.5,
        tickColor="#bbbbbb",
        tickSize=6,
    )
    .configure_view(strokeWidth=0, fill="#FAFBFC")
    .configure_legend(padding=20, cornerRadius=6, strokeColor="#dddddd", fillColor="#FAFBFC")
    .configure_title(subtitlePadding=8)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
