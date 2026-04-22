""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: pygal 3.1.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-02-18
"""

import pygal
from pygal.style import Style


# Data - Technology innovations mapped to time-horizon rings and thematic sectors
sectors = ["AI & ML", "Cloud & Infra", "Sustainability", "Biotech & Health"]
ring_values = {"Adopt": 1, "Trial": 2, "Assess": 3, "Hold": 4}

# Colorblind-safe sector palette (blue, amber, teal, purple — no red-green conflict)
sector_colors = {
    "AI & ML": "#2563eb",
    "Cloud & Infra": "#d97706",
    "Sustainability": "#0d9488",
    "Biotech & Health": "#7c3aed",
}

innovations = [
    ("LLM Agents", "AI & ML", "Adopt"),
    ("RAG Pipelines", "AI & ML", "Adopt"),
    ("Edge AI Inference", "AI & ML", "Trial"),
    ("Federated Learning", "AI & ML", "Assess"),
    ("Neuromorphic Chips", "AI & ML", "Hold"),
    ("Causal AI", "AI & ML", "Assess"),
    ("Kubernetes", "Cloud & Infra", "Adopt"),
    ("GitOps Workflows", "Cloud & Infra", "Adopt"),
    ("WASM Runtimes", "Cloud & Infra", "Trial"),
    ("Confidential Compute", "Cloud & Infra", "Trial"),
    ("Serverless GPUs", "Cloud & Infra", "Assess"),
    ("Quantum Networking", "Cloud & Infra", "Hold"),
    ("Carbon Accounting", "Sustainability", "Trial"),
    ("Green Software", "Sustainability", "Adopt"),
    ("Digital Passports", "Sustainability", "Assess"),
    ("Energy-Harvest IoT", "Sustainability", "Hold"),
    ("Circular Supply", "Sustainability", "Assess"),
    ("AI-Optimized Grids", "Sustainability", "Trial"),
    ("mRNA Therapeutics", "Biotech & Health", "Adopt"),
    ("Digital Organ Twins", "Biotech & Health", "Assess"),
    ("CRISPR Diagnostics", "Biotech & Health", "Trial"),
    ("Synthetic Biology", "Biotech & Health", "Hold"),
    ("Wearable Biomarkers", "Biotech & Health", "Trial"),
    ("Longevity Genomics", "Biotech & Health", "Hold"),
]

# Group and sort by ring within each sector (near-term first for visual progression)
sector_items = {s: [] for s in sectors}
for name, sector, ring in innovations:
    sector_items[sector].append((name, ring))
for s in sectors:
    sector_items[s].sort(key=lambda x: ring_values[x[1]])

# Angular layout: [HEADER, item1..item6, gap] per sector = 8 slots × 4 sectors = 32
slots_per_sector = 8
total_slots = len(sectors) * slots_per_sector

x_labels = []
item_placements = []
for sector_idx, sector in enumerate(sectors):
    start_slot = sector_idx * slots_per_sector
    x_labels.append(sector)
    for i, (name, ring) in enumerate(sector_items[sector]):
        x_labels.append(name)  # Show innovation names on perimeter
        item_placements.append((name, sector, ring, start_slot + 1 + i))
    x_labels.append("")

# One series per sector → 4 legend entries colored by category
series_data = {s: [None] * total_slots for s in sectors}
for name, sector, ring, slot in item_placements:
    series_data[sector][slot] = {"value": ring_values[ring], "label": name}

color_sequence = tuple(sector_colors[s] for s in sectors)

custom_style = Style(
    background="white",
    plot_background="#f4f5fa",
    foreground="#3a3a4a",
    foreground_strong="#16162a",
    foreground_subtle="#a0a0b0",  # Visible ring guides for time-horizon hierarchy
    colors=color_sequence,
    title_font_size=48,
    label_font_size=18,
    major_label_font_size=34,
    legend_font_size=26,
    value_font_size=20,
    opacity=0.65,
    opacity_hover=0.9,
    stroke_width=2.5,
)

chart = pygal.Radar(
    width=3600,
    height=3600,
    style=custom_style,
    title="radar-innovation-timeline · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=22,
    fill=False,
    stroke=True,
    show_dots=True,
    dots_size=16,
    show_y_guides=True,
    show_x_guides=False,
    range=(0, 5),
    inner_radius=0.12,
    y_labels=[
        {"value": 1, "label": "Adopt"},
        {"value": 2, "label": "Trial"},
        {"value": 3, "label": "Assess"},
        {"value": 4, "label": "Hold"},
    ],
    show_minor_x_labels=True,
    x_labels_major=sectors,
    x_label_rotation=0,
    margin_bottom=60,
    margin_left=60,
    margin_right=60,
    margin_top=60,
    truncate_label=100,
)

chart.x_labels = x_labels

for sector in sectors:
    chart.add(sector, series_data[sector])

chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
