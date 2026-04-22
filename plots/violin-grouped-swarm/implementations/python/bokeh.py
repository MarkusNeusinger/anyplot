""" pyplots.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy import stats


# Data - Response times (ms) across 3 task types and 2 expertise levels
np.random.seed(42)

categories = ["Simple", "Moderate", "Complex"]
groups = ["Novice", "Expert"]

# Generate realistic response time data for each combination
data = []
for cat_idx, category in enumerate(categories):
    for _grp_idx, group in enumerate(groups):
        # Experts faster, complex tasks take longer
        base = 200 + cat_idx * 150
        expert_adjust = -80 if group == "Expert" else 0
        mean = base + expert_adjust
        std = 30 + cat_idx * 15
        values = np.random.normal(mean, std, 40)
        values = np.clip(values, 50, 900)
        for val in values:
            data.append({"category": category, "group": group, "value": val})

# Colors
colors = {"Novice": "#306998", "Expert": "#FFD43B"}

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="violin-grouped-swarm · bokeh · pyplots.ai",
    x_axis_label="Task Type",
    y_axis_label="Response Time (ms)",
    x_range=[-0.5, 2.5],
    y_range=[0, 750],
    tools="",
    toolbar_location=None,
)

# Styling
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Positioning
cat_positions = {cat: i for i, cat in enumerate(categories)}
group_offsets = {"Novice": -0.2, "Expert": 0.2}

# Store legend items
legend_items = []

# Draw violin shapes and swarm points for each category-group combination
for _grp_idx, group in enumerate(groups):
    first_violin = None

    for _cat_idx, category in enumerate(categories):
        # Get values for this category-group
        values = np.array([d["value"] for d in data if d["category"] == category and d["group"] == group])

        base_x = cat_positions[category] + group_offsets[group]

        # Compute kernel density estimate for violin
        kde = stats.gaussian_kde(values)
        y_range = np.linspace(values.min() - 15, values.max() + 15, 100)
        density = kde(y_range)

        # Scale density to reasonable width
        max_width = 0.17
        density_scaled = density / density.max() * max_width

        # Create violin polygon
        violin_x = np.concatenate([base_x - density_scaled, (base_x + density_scaled)[::-1]])
        violin_y = np.concatenate([y_range, y_range[::-1]])

        # Draw violin
        v_glyph = p.patch(
            violin_x, violin_y, fill_color=colors[group], fill_alpha=0.5, line_color=colors[group], line_width=3
        )

        if first_violin is None:
            first_violin = v_glyph

        # Create swarm points - bin values and assign jittered x positions
        swarm_x = []
        bin_width = 20
        value_bins = {}

        for val in values:
            bin_key = int(val // bin_width)
            if bin_key not in value_bins:
                value_bins[bin_key] = 0
            count = value_bins[bin_key]
            # Alternate sides with increasing offset
            offset = (count // 2 + 1) * 0.025 * (1 if count % 2 == 0 else -1)
            if count == 0:
                offset = 0
            # Clamp offset within violin width
            max_offset = density_scaled[min(int((val - y_range[0]) / (y_range[-1] - y_range[0]) * 99), 99)] * 0.7
            offset = np.clip(offset, -max_offset, max_offset)
            swarm_x.append(base_x + offset)
            value_bins[bin_key] += 1

        swarm_source = ColumnDataSource(data={"x": swarm_x, "y": values})

        p.scatter(
            "x",
            "y",
            source=swarm_source,
            size=14,
            fill_color=colors[group],
            fill_alpha=0.75,
            line_color="white",
            line_width=2,
        )

    # Add legend item for this group
    legend_items.append(LegendItem(label=group, renderers=[first_violin]))

# Custom x-axis with category labels
p.xaxis.ticker = list(range(len(categories)))
p.xaxis.major_label_overrides = dict(enumerate(categories))

# Add legend
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="22pt",
    glyph_width=40,
    glyph_height=40,
    spacing=15,
    padding=20,
    background_fill_alpha=0.8,
    border_line_color="#cccccc",
    border_line_width=2,
)
p.add_layout(legend, "right")

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactive version
save(p, filename="plot.html", resources=CDN, title="violin-grouped-swarm · bokeh · pyplots.ai")
