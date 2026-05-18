""" anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-18
"""

import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# noqa: E402 - imports after sys.path manipulation to fix shadowing
_cwd = os.getcwd()
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(__file__)]
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem  # noqa: E402
from bokeh.plotting import figure  # noqa: E402


sys.path.insert(0, os.path.dirname(__file__))

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

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

# Color mapping
colors = {group: OKABE_ITO[i] for i, group in enumerate(groups)}

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="violin-grouped-swarm · Python · bokeh · anyplot.ai",
    x_axis_label="Task Type",
    y_axis_label="Response Time (ms)",
    x_range=[-0.5, 2.5],
    y_range=[0, 750],
    tools="",
    toolbar_location=None,
)

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

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

        swarm_source = ColumnDataSource(
            data={"x": swarm_x, "y": values, "group": [group] * len(values), "category": [category] * len(values)}
        )

        # Add hover tool for swarm points
        hover = HoverTool(
            tooltips=[("Task Type", "@category"), ("Expertise", "@group"), ("Response Time", "@y{0.0f} ms")]
        )
        p.add_tools(hover)

        p.scatter(
            "x",
            "y",
            source=swarm_source,
            size=15,
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

# Add legend with larger sizing
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="20pt",
    label_text_color=INK_SOFT,
    glyph_width=50,
    glyph_height=50,
    spacing=20,
    padding=25,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.95,
    border_line_color=INK_SOFT,
    border_line_width=2,
)
p.add_layout(legend, "right")

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium
W, H = 4800, 2700
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
