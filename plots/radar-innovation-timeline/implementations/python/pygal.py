"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: pygal 3.1.0 | Python 3.14.3
Quality: pending | Created: 2026-05-29
"""

import os
import sys


# Prevent this file (pygal.py) from shadowing the pygal package on sys.path
_this_dir = os.path.abspath(os.path.dirname(__file__))
sys.path[:] = [p for p in sys.path if os.path.realpath(p or ".") != _this_dir]

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first 4 positions mapped to sectors
sectors = ["Data Engineering", "Cloud Platforms", "Security", "DevOps"]
sector_colors = {
    "Data Engineering": "#009E73",  # Imprint pos 1 — brand green
    "Cloud Platforms": "#C475FD",  # Imprint pos 2
    "Security": "#4467A3",  # Imprint pos 3
    "DevOps": "#BD8233",  # Imprint pos 4
}
ring_values = {"Adopt": 1, "Trial": 2, "Assess": 3, "Hold": 4}

# Data — 24 innovations across 4 sectors and 4 time-horizon rings
innovations = [
    ("dbt Core", "Data Engineering", "Adopt"),
    ("Apache Iceberg", "Data Engineering", "Adopt"),
    ("Kafka Streams", "Data Engineering", "Trial"),
    ("Delta Lake", "Data Engineering", "Trial"),
    ("Vector Databases", "Data Engineering", "Assess"),
    ("Arrow Flight RPC", "Data Engineering", "Hold"),
    ("Service Mesh", "Cloud Platforms", "Adopt"),
    ("eBPF Monitoring", "Cloud Platforms", "Trial"),
    ("Green Cloud APIs", "Cloud Platforms", "Trial"),
    ("Multi-Cloud Orch.", "Cloud Platforms", "Assess"),
    ("Serverless Edge", "Cloud Platforms", "Assess"),
    ("Quantum Cloud", "Cloud Platforms", "Hold"),
    ("Zero Trust Network", "Security", "Adopt"),
    ("AI-Native SOC", "Security", "Trial"),
    ("Supply Chain Sec.", "Security", "Trial"),
    ("Post-Quantum Crypto", "Security", "Assess"),
    ("Confidential Compute", "Security", "Assess"),
    ("Homomorphic Encrypt.", "Security", "Hold"),
    ("Platform Engineering", "DevOps", "Adopt"),
    ("AI Code Assistants", "DevOps", "Adopt"),
    ("FinOps Automation", "DevOps", "Trial"),
    ("Chaos Engineering", "DevOps", "Trial"),
    ("Internal Dev Portal", "DevOps", "Assess"),
    ("GitOps at Scale", "DevOps", "Hold"),
]

# Sort items within each sector by ring (near-term first for visual clarity)
sector_items = {s: [] for s in sectors}
for name, sector, ring in innovations:
    sector_items[sector].append((name, ring))
for s in sectors:
    sector_items[s].sort(key=lambda x: ring_values[x[1]])

# Angular layout: [header_slot, item_slots x6, gap_slot] per sector = 8 slots × 4 = 32
slots_per_sector = 8
total_slots = len(sectors) * slots_per_sector

x_labels = []
item_placements = []
for sector_idx, sector in enumerate(sectors):
    start_slot = sector_idx * slots_per_sector
    x_labels.append(sector)  # Sector header shown as major label
    for i, (name, ring) in enumerate(sector_items[sector]):
        x_labels.append(name)
        item_placements.append((name, sector, ring, start_slot + 1 + i))
    x_labels.append("")  # Gap slot between sectors

# Build series: one per sector, None for positions belonging to other sectors
series_data = {s: [None] * total_slots for s in sectors}
for name, sector, ring, slot in item_placements:
    series_data[sector][slot] = {"value": ring_values[ring], "label": name}

color_sequence = tuple(sector_colors[s] for s in sectors)

title_str = "radar-innovation-timeline · python · pygal · anyplot.ai"
n_chars = len(title_str)
title_font_size = round(66 * 67 / n_chars) if n_chars > 67 else 66
title_font_size = max(title_font_size, 44)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=color_sequence,
    title_font_size=title_font_size,
    label_font_size=34,  # Increased from 18 for better perimeter readability
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.9,
    opacity_hover=1.0,
    stroke_width=2.5,
)

chart = pygal.Radar(
    width=2400,
    height=2400,
    style=custom_style,
    title=title_str,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=30,
    fill=False,
    stroke=False,  # Disable polygon connecting lines — dots only for independent items
    show_dots=True,
    dots_size=18,
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
    margin_bottom=80,
    margin_left=80,
    margin_right=80,
    margin_top=60,
    truncate_label=100,
)

chart.x_labels = x_labels

for sector in sectors:
    chart.add(sector, series_data[sector])

chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
