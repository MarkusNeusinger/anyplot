""" pyplots.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: plotly 6.5.1 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Iris-like multivariate dataset with clear clusters
np.random.seed(42)

# Create 3 distinct groups with different characteristics
n_per_group = 50
categories = ["Setosa", "Versicolor", "Virginica"]
colors = ["#306998", "#FFD43B", "#E53935"]
deselected_colors = ["rgba(48,105,152,0.2)", "rgba(255,212,59,0.2)", "rgba(229,57,53,0.2)"]

# Generate clustered data
sepal_length = np.concatenate(
    [
        np.random.normal(5.0, 0.35, n_per_group),
        np.random.normal(5.9, 0.50, n_per_group),
        np.random.normal(6.6, 0.60, n_per_group),
    ]
)
sepal_width = np.concatenate(
    [
        np.random.normal(3.4, 0.38, n_per_group),
        np.random.normal(2.8, 0.30, n_per_group),
        np.random.normal(3.0, 0.32, n_per_group),
    ]
)
petal_length = np.concatenate(
    [
        np.random.normal(1.5, 0.17, n_per_group),
        np.random.normal(4.3, 0.45, n_per_group),
        np.random.normal(5.5, 0.55, n_per_group),
    ]
)
category = np.repeat(categories, n_per_group)
point_indices = np.arange(len(sepal_length))

# Create subplots: scatter plot, histogram, and bar chart
fig = make_subplots(
    rows=2,
    cols=2,
    specs=[[{"colspan": 2}, None], [{}, {}]],
    subplot_titles=("Sepal Dimensions by Species", "Petal Length Distribution", "Species Count"),
    vertical_spacing=0.15,
    horizontal_spacing=0.12,
)

# Add scatter plot for each category (top row, spans both columns)
for i, cat in enumerate(categories):
    mask = category == cat
    fig.add_trace(
        go.Scatter(
            x=sepal_length[mask],
            y=sepal_width[mask],
            mode="markers",
            marker={"size": 14, "color": colors[i], "opacity": 0.8, "line": {"width": 1, "color": "white"}},
            name=cat,
            legendgroup=cat,
            customdata=np.column_stack([point_indices[mask], np.full(mask.sum(), i)]),
            hovertemplate=f"<b>{cat}</b><br>Sepal Length: %{{x:.2f}} cm<br>Sepal Width: %{{y:.2f}} cm<extra></extra>",
            selected={"marker": {"opacity": 1.0, "size": 16}},
            unselected={"marker": {"opacity": 0.2, "size": 10}},
        ),
        row=1,
        col=1,
    )

# Add histogram for petal length (bottom left) - use bar for better selection control
for i, cat in enumerate(categories):
    mask = category == cat
    petal_data = petal_length[mask]
    hist, bin_edges = np.histogram(petal_data, bins=15, range=(0, 7))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    fig.add_trace(
        go.Bar(
            x=bin_centers,
            y=hist,
            width=bin_edges[1] - bin_edges[0],
            name=cat,
            marker={"color": colors[i], "opacity": 0.7, "line": {"width": 1, "color": "white"}},
            legendgroup=cat,
            showlegend=False,
            hovertemplate=f"<b>{cat}</b><br>Petal Length: %{{x:.2f}} cm<br>Count: %{{y}}<extra></extra>",
            customdata=np.full(len(hist), i),
        ),
        row=2,
        col=1,
    )

# Add bar chart for species count (bottom right)
counts = [n_per_group] * 3
fig.add_trace(
    go.Bar(
        x=categories,
        y=counts,
        marker={"color": colors, "opacity": 0.85, "line": {"width": 2, "color": "white"}},
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        customdata=list(range(3)),
    ),
    row=2,
    col=2,
)

# Update layout for linked selection
fig.update_layout(
    title={
        "text": "linked-views-selection · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    template="plotly_white",
    font={"size": 18},
    legend={
        "title": {"text": "Species", "font": {"size": 20}},
        "font": {"size": 18},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "itemsizing": "constant",
    },
    barmode="overlay",
    hovermode="closest",
    dragmode="select",
    margin={"l": 80, "r": 80, "t": 140, "b": 100},
    annotations=[
        {
            "text": "Use box/lasso select on scatter plot to highlight species across all views | Double-click to reset",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.10,
            "showarrow": False,
            "font": {"size": 16, "color": "#666666"},
            "xanchor": "center",
        }
    ],
)

# Update subplot titles font size
for annotation in fig.layout.annotations:
    if annotation.text in ["Sepal Dimensions by Species", "Petal Length Distribution", "Species Count"]:
        annotation.font = {"size": 22}

# Update axes
fig.update_xaxes(
    title={"text": "Sepal Length (cm)", "font": {"size": 20}},
    tickfont={"size": 16},
    gridcolor="rgba(0,0,0,0.1)",
    row=1,
    col=1,
)
fig.update_yaxes(
    title={"text": "Sepal Width (cm)", "font": {"size": 20}},
    tickfont={"size": 16},
    gridcolor="rgba(0,0,0,0.1)",
    row=1,
    col=1,
)
fig.update_xaxes(
    title={"text": "Petal Length (cm)", "font": {"size": 20}},
    tickfont={"size": 16},
    gridcolor="rgba(0,0,0,0.1)",
    row=2,
    col=1,
)
fig.update_yaxes(
    title={"text": "Count", "font": {"size": 20}}, tickfont={"size": 16}, gridcolor="rgba(0,0,0,0.1)", row=2, col=1
)
fig.update_xaxes(title={"text": "Species", "font": {"size": 20}}, tickfont={"size": 16}, row=2, col=2)
fig.update_yaxes(
    title={"text": "Count", "font": {"size": 20}}, tickfont={"size": 16}, gridcolor="rgba(0,0,0,0.1)", row=2, col=2
)

# Configure select/lasso behavior
fig.update_layout(selectdirection="any", newselection={"line": {"color": "#306998", "width": 2}})

# Save PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# JavaScript for true cross-view linked selection
linked_selection_js = """
<script>
(function() {
    var gd = document.getElementById('plotly-graph');
    var originalColors = ['#306998', '#FFD43B', '#E53935'];
    var fadedColors = ['rgba(48,105,152,0.2)', 'rgba(255,212,59,0.2)', 'rgba(229,57,53,0.2)'];
    var histTraces = [3, 4, 5];  // Histogram bar traces
    var countBarTrace = 6;  // Species count bar trace

    // Handle selection on scatter traces (0, 1, 2)
    gd.on('plotly_selected', function(eventData) {
        if (!eventData || !eventData.points || eventData.points.length === 0) return;

        // Determine which species are selected
        var selectedSpecies = new Set();
        eventData.points.forEach(function(pt) {
            if (pt.curveNumber < 3) {  // Scatter traces
                selectedSpecies.add(pt.curveNumber);
            }
        });

        // Update histogram bars
        var histColors = [];
        var histOpacities = [];
        for (var i = 0; i < 3; i++) {
            if (selectedSpecies.has(i)) {
                histColors.push(originalColors[i]);
                histOpacities.push(0.85);
            } else {
                histColors.push(fadedColors[i]);
                histOpacities.push(0.3);
            }
        }

        // Update count bar colors
        var countColors = [];
        var countOpacities = [];
        for (var j = 0; j < 3; j++) {
            if (selectedSpecies.has(j)) {
                countColors.push(originalColors[j]);
                countOpacities.push(0.85);
            } else {
                countColors.push(fadedColors[j]);
                countOpacities.push(0.3);
            }
        }

        // Apply updates
        var updates = [];
        var indices = [];

        histTraces.forEach(function(traceIdx, i) {
            updates.push({'marker.color': selectedSpecies.has(i) ? originalColors[i] : fadedColors[i],
                         'marker.opacity': selectedSpecies.has(i) ? 0.85 : 0.3});
            indices.push(traceIdx);
        });

        Plotly.restyle(gd, {'marker.color': [countColors]}, [countBarTrace]);

        for (var k = 0; k < histTraces.length; k++) {
            Plotly.restyle(gd, {
                'marker.color': selectedSpecies.has(k) ? originalColors[k] : fadedColors[k],
                'marker.opacity': selectedSpecies.has(k) ? 0.85 : 0.3
            }, [histTraces[k]]);
        }
    });

    // Reset on double-click or deselect
    gd.on('plotly_deselect', function() {
        // Reset histogram colors
        for (var i = 0; i < histTraces.length; i++) {
            Plotly.restyle(gd, {
                'marker.color': originalColors[i],
                'marker.opacity': 0.7
            }, [histTraces[i]]);
        }
        // Reset count bar
        Plotly.restyle(gd, {'marker.color': [originalColors]}, [countBarTrace]);
    });
})();
</script>
"""

# Save HTML with linked selection JavaScript
html_content = fig.to_html(include_plotlyjs=True, full_html=True, div_id="plotly-graph")
html_content = html_content.replace("</body>", linked_selection_js + "</body>")

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
