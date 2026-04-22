""" pyplots.ai
map-marker-clustered: Clustered Marker Map
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, LabelSet, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Store locations across a region (coffee shop chain example)
np.random.seed(42)

# Generate clustered store locations around major neighborhoods
neighborhoods = [
    {"name": "Downtown", "lat": 40.758, "lon": -73.985, "stores": 45},
    {"name": "Midtown", "lat": 40.755, "lon": -73.975, "stores": 35},
    {"name": "Upper East", "lat": 40.773, "lon": -73.965, "stores": 28},
    {"name": "Upper West", "lat": 40.785, "lon": -73.976, "stores": 22},
    {"name": "Chelsea", "lat": 40.742, "lon": -74.000, "stores": 18},
    {"name": "SoHo", "lat": 40.723, "lon": -73.998, "stores": 25},
    {"name": "Financial", "lat": 40.707, "lon": -74.011, "stores": 32},
    {"name": "Brooklyn Heights", "lat": 40.696, "lon": -73.993, "stores": 20},
    {"name": "Williamsburg", "lat": 40.714, "lon": -73.961, "stores": 30},
    {"name": "DUMBO", "lat": 40.703, "lon": -73.988, "stores": 15},
]

# Generate individual store locations around each neighborhood center
all_lats = []
all_lons = []
all_labels = []
all_categories = []
all_neighborhoods = []

categories = ["Coffee", "Express", "Roastery", "Reserve"]
category_weights = [0.5, 0.3, 0.15, 0.05]

for hood in neighborhoods:
    n_stores = hood["stores"]
    # Add some random scatter around the center
    store_lats = hood["lat"] + np.random.normal(0, 0.008, n_stores)
    store_lons = hood["lon"] + np.random.normal(0, 0.008, n_stores)
    store_labels = [f"{hood['name']} Store {i + 1}" for i in range(n_stores)]
    store_categories = np.random.choice(categories, n_stores, p=category_weights)

    all_lats.extend(store_lats)
    all_lons.extend(store_lons)
    all_labels.extend(store_labels)
    all_categories.extend(store_categories)
    all_neighborhoods.extend([hood["name"]] * n_stores)

lats = np.array(all_lats)
lons = np.array(all_lons)
labels = np.array(all_labels)
store_categories = np.array(all_categories)
store_neighborhoods = np.array(all_neighborhoods)


# Convert lat/lon to Web Mercator projection (inline calculation)
k = 6378137  # Earth radius in meters
mercator_x = lons * (k * np.pi / 180.0)
mercator_y = np.log(np.tan((90 + lats) * np.pi / 360.0)) * k

# Grid-based clustering for marker aggregation
# This simulates zoom-level clustering behavior
grid_size = 2500  # meters in Web Mercator

# Calculate grid cell for each point
grid_x = np.floor(mercator_x / grid_size).astype(int)
grid_y = np.floor(mercator_y / grid_size).astype(int)

# Create unique cluster IDs from grid coordinates
cluster_ids = grid_x * 10000 + grid_y
unique_clusters = np.unique(cluster_ids)

# Calculate cluster centers and counts
cluster_centers_x = []
cluster_centers_y = []
cluster_counts = []
cluster_dominant_category = []

category_colors = {
    "Coffee": "#306998",  # Python Blue
    "Express": "#FFD43B",  # Python Yellow
    "Roastery": "#4B8BBE",  # Light Blue
    "Reserve": "#2ECC71",  # Green
}

for cluster_id in unique_clusters:
    mask = cluster_ids == cluster_id
    cluster_centers_x.append(mercator_x[mask].mean())
    cluster_centers_y.append(mercator_y[mask].mean())
    cluster_counts.append(mask.sum())

    # Find dominant category in cluster
    cluster_cats = store_categories[mask]
    unique, counts = np.unique(cluster_cats, return_counts=True)
    dominant = unique[counts.argmax()]
    cluster_dominant_category.append(dominant)

cluster_centers_x = np.array(cluster_centers_x)
cluster_centers_y = np.array(cluster_centers_y)
cluster_counts = np.array(cluster_counts)

# Calculate cluster marker sizes based on count
min_size = 45
max_size = 110
count_normalized = (cluster_counts - cluster_counts.min() + 1) / (cluster_counts.max() - cluster_counts.min() + 1)
cluster_sizes = min_size + np.sqrt(count_normalized) * (max_size - min_size)

# Color clusters by dominant category
cluster_colors = [category_colors[cat] for cat in cluster_dominant_category]

# Create figure with tile map
p = figure(
    width=4800,
    height=2700,
    x_axis_type="mercator",
    y_axis_type="mercator",
    title="map-marker-clustered · bokeh · pyplots.ai",
    tools="pan,wheel_zoom,box_zoom,reset,hover,save",
    tooltips=[("Stores", "@count"), ("Dominant Type", "@category")],
)

# Add map tiles (CartoDB Positron for clean basemap)
p.add_tile("CartoDB Positron")

# Create cluster data source
cluster_source = ColumnDataSource(
    data={
        "x": cluster_centers_x,
        "y": cluster_centers_y,
        "count": cluster_counts,
        "size": cluster_sizes,
        "color": cluster_colors,
        "category": cluster_dominant_category,
        "count_label": [str(c) for c in cluster_counts],
    }
)

# Create separate renderers for each category to build legend
legend_items = []
for category, color in category_colors.items():
    cat_mask = np.array([cat == category for cat in cluster_dominant_category])
    if any(cat_mask):
        cat_source = ColumnDataSource(
            data={
                "x": cluster_centers_x[cat_mask],
                "y": cluster_centers_y[cat_mask],
                "size": cluster_sizes[cat_mask],
                "count": cluster_counts[cat_mask],
                "count_label": [str(c) for c in cluster_counts[cat_mask]],
                "category": [category] * cat_mask.sum(),
            }
        )
        renderer = p.scatter(
            x="x",
            y="y",
            source=cat_source,
            size="size",
            fill_color=color,
            fill_alpha=0.8,
            line_color="#333333",
            line_width=3,
        )
        legend_items.append(LegendItem(label=f"{category} (dominant)", renderers=[renderer]))

# Add count labels on cluster markers
cluster_labels_set = LabelSet(
    x="x",
    y="y",
    text="count_label",
    source=cluster_source,
    text_font_size="24pt",
    text_font_style="bold",
    text_color="white",
    text_align="center",
    text_baseline="middle",
)
p.add_layout(cluster_labels_set)

# Show individual markers faintly to indicate member positions
individual_source = ColumnDataSource(
    data={"x": mercator_x, "y": mercator_y, "label": labels, "category": store_categories}
)

p.scatter(x="x", y="y", source=individual_source, size=10, fill_color="#306998", fill_alpha=0.2, line_color=None)

# Add legend for store types
legend = Legend(
    items=legend_items,
    location="top_left",
    title="Store Type",
    title_text_font_size="24pt",
    label_text_font_size="18pt",
    glyph_height=35,
    glyph_width=35,
    spacing=12,
    padding=20,
    background_fill_alpha=0.9,
    background_fill_color="white",
    border_line_color="#306998",
    border_line_width=2,
)
p.add_layout(legend, "right")

# Add text annotation explaining clustering
p.text(
    x=[-8250000],
    y=[4965000],
    text=["Clustered markers show aggregated store counts"],
    text_font_size="20pt",
    text_color="#555555",
    text_font_style="italic",
)

# Styling
p.title.text_font_size = "32pt"
p.title.text_color = "#306998"
p.xaxis.axis_label = "Easting (m)"
p.yaxis.axis_label = "Northing (m)"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Set view to focus on NYC area
p.x_range.start = -8265000
p.x_range.end = -8215000
p.y_range.start = 4955000
p.y_range.end = 5015000

# Background and border
p.background_fill_color = None
p.border_fill_color = "#ffffff"
p.outline_line_color = "#306998"
p.outline_line_width = 2

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="map-marker-clustered · bokeh · pyplots.ai", resources=CDN)
