""" anyplot.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-17
"""

import os
import sys


# Ensure proper module loading by prioritizing venv packages
venv_path = [p for p in sys.path if ".venv" in p]
sys.path = venv_path + [p for p in sys.path if ".venv" not in p and p != ""]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from sklearn.datasets import load_iris  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Create custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=24,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=14,
    value_font_size=12,
    stroke_width=2,
)

# Data: Iris dataset
iris = load_iris()
X = iris.data
y = iris.target
target_names = iris.target_names
feature_names = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]

df = pd.DataFrame(X, columns=feature_names)
df["species"] = [target_names[i] for i in y]
df["index"] = range(len(df))

# Prepare data for linked views
species_colors = {target_names[0]: OKABE_ITO[0], target_names[1]: OKABE_ITO[1], target_names[2]: OKABE_ITO[2]}

# View 1: Scatter plot (Petal Width vs Petal Length, colored by species)
scatter = pygal.XY(
    width=1500,
    height=900,
    title="Petal Dimensions · linked-views-selection · pygal · anyplot.ai",
    x_title="Petal Length (cm)",
    y_title="Petal Width (cm)",
    style=custom_style,
    show_legend=True,
)

for sp in target_names:
    species_data = df[df["species"] == sp]
    data_points = [(row["Petal Length"], row["Petal Width"]) for _, row in species_data.iterrows()]
    scatter.add(sp, data_points, dots_size=5)

scatter_svg = scatter.render()

# View 2: Bar chart (species counts)
bar_chart = pygal.Bar(
    width=1500,
    height=900,
    title="Species Distribution · linked-views-selection · pygal · anyplot.ai",
    y_title="Count",
    style=custom_style,
    show_legend=False,
)

species_counts = df["species"].value_counts().sort_index()
for sp in target_names:
    if sp in species_counts.index:
        bar_chart.add(sp, [species_counts[sp]])

bar_chart.x_labels = ["Count"]
bar_svg = bar_chart.render()

# View 3: Histogram-like plot (Sepal Length distribution by species)
histogram = pygal.Line(
    width=1500,
    height=900,
    title="Sepal Length Distribution · linked-views-selection · pygal · anyplot.ai",
    x_title="Sepal Length (cm)",
    y_title="Frequency",
    style=custom_style,
    show_legend=True,
    dots_size=4,
)

# Create histogram data
bins = np.linspace(df["Sepal Length"].min(), df["Sepal Length"].max(), 12)

for sp in target_names:
    species_data = df[df["species"] == sp]["Sepal Length"]
    hist, bin_edges = np.histogram(species_data, bins=bins)
    histogram.add(sp, list(hist.astype(int)))

histogram.x_labels = [f"{b:.1f}" for b in bins[:-1]]
histogram_svg = histogram.render()

# Create combined HTML with linked selection JavaScript
html_content = (
    """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>linked-views-selection · pygal · anyplot.ai</title>
    <script src="https://kozea.github.io/pygal.js/2.0.x/pygal-tooltips.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: """
    + PAGE_BG
    + """;
            color: """
    + INK
    + """;
            padding: 40px;
        }

        .container {
            max-width: 100%;
            margin: 0 auto;
        }

        h1 {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 20px;
            color: """
    + INK
    + """;
        }

        .info-panel {
            background-color: """
    + ELEVATED_BG
    + """;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 40px;
            color: """
    + INK_SOFT
    + """;
            font-size: 16px;
        }

        .info-panel p {
            margin-bottom: 8px;
        }

        .selection-info {
            font-weight: 600;
            color: """
    + INK
    + """;
        }

        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin-bottom: 40px;
        }

        .chart-container {
            background-color: """
    + PAGE_BG
    + """;
            border: 1px solid """
    + INK_MUTED
    + """;
            border-radius: 4px;
            padding: 20px;
        }

        .chart-full {
            grid-column: 1 / -1;
        }

        svg {
            max-width: 100%;
            height: auto;
        }

        .reset-button {
            background-color: #009E73;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 30px;
            font-weight: 600;
        }

        .reset-button:hover {
            opacity: 0.9;
        }

        .selected {
            stroke-width: 3 !important;
            opacity: 1 !important;
        }

        .deselected {
            opacity: 0.2 !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Multiple Linked Views with Selection Sync</h1>

        <div class="info-panel">
            <p><strong>Explore linked data:</strong> Click on bars or lines to highlight corresponding species across all views.</p>
            <p class="selection-info">Selected: <span id="selection">All species</span></p>
            <button class="reset-button" onclick="resetSelection()">Reset Selection</button>
        </div>

        <div class="charts-grid">
            <div class="chart-container">
                <div id="scatter"></div>
            </div>
            <div class="chart-container">
                <div id="histogram"></div>
            </div>
            <div class="chart-container chart-full">
                <div id="bar"></div>
            </div>
        </div>
    </div>

    <script>
        // SVG data embedded directly
        const scatterSvg = `"""
    + scatter_svg.decode("utf-8")
    + """`;
        const barSvg = `"""
    + bar_svg.decode("utf-8")
    + """`;
        const histogramSvg = `"""
    + histogram_svg.decode("utf-8")
    + """`;

        // Insert SVGs
        document.getElementById('scatter').innerHTML = scatterSvg;
        document.getElementById('bar').innerHTML = barSvg;
        document.getElementById('histogram').innerHTML = histogramSvg;

        // Available species
        const species = ['setosa', 'versicolor', 'virginica'];
        let selectedSpecies = new Set(species);

        // Update selection UI
        function updateSelectionUI() {
            if (selectedSpecies.size === 0) {
                selectedSpecies = new Set(species);
            }

            const selected = Array.from(selectedSpecies).join(', ');
            document.getElementById('selection').textContent =
                selectedSpecies.size === 3 ? 'All species' : selected;

            applySelection();
        }

        // Apply selection to all charts
        function applySelection() {
            const circles = document.querySelectorAll('circle[class*="reactive"]');
            const rects = document.querySelectorAll('rect[class*="reactive"]');

            circles.forEach(circle => {
                const parent = circle.closest('[class*="series"]');
                if (parent) {
                    const seriesClass = parent.getAttribute('class');
                    let isSelected = false;

                    for (const sp of selectedSpecies) {
                        if (seriesClass.includes(sp)) {
                            isSelected = true;
                            break;
                        }
                    }

                    if (isSelected) {
                        circle.classList.remove('deselected');
                        circle.classList.add('selected');
                    } else {
                        circle.classList.add('deselected');
                        circle.classList.remove('selected');
                    }
                }
            });

            rects.forEach(rect => {
                const parent = rect.closest('[class*="series"]');
                if (parent) {
                    const seriesClass = parent.getAttribute('class');
                    let isSelected = false;

                    for (const sp of selectedSpecies) {
                        if (seriesClass.includes(sp)) {
                            isSelected = true;
                            break;
                        }
                    }

                    if (isSelected) {
                        rect.classList.remove('deselected');
                        rect.classList.add('selected');
                    } else {
                        rect.classList.add('deselected');
                        rect.classList.remove('selected');
                    }
                }
            });
        }

        // Reset selection
        function resetSelection() {
            selectedSpecies = new Set(species);
            updateSelectionUI();
        }

        // Add click handlers to chart elements
        document.addEventListener('click', function(e) {
            const rect = e.target.closest('rect[class*="reactive"]');
            const circle = e.target.closest('circle[class*="reactive"]');

            if (rect || circle) {
                const parent = (rect || circle).closest('[class*="series"]');
                if (parent) {
                    const seriesClass = parent.getAttribute('class');

                    let clickedSpecies = null;
                    for (const sp of species) {
                        if (seriesClass.includes(sp)) {
                            clickedSpecies = sp;
                            break;
                        }
                    }

                    if (clickedSpecies) {
                        if (selectedSpecies.has(clickedSpecies)) {
                            selectedSpecies.delete(clickedSpecies);
                        } else {
                            selectedSpecies.add(clickedSpecies);
                        }
                        updateSelectionUI();
                    }
                }
            }
        });

        // Initialize
        updateSelectionUI();
    </script>
</body>
</html>"""
)

# Save HTML file
with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)

# For PNG output, create a composite image with all three views
# First, render each chart as PNG
scatter.render_to_png(f"scatter-{THEME}.png")
bar_chart.render_to_png(f"bar-{THEME}.png")
histogram.render_to_png(f"histogram-{THEME}.png")

# Load the PNG images and combine them using PIL
try:
    from PIL import Image

    # Open images
    img_scatter = Image.open(f"scatter-{THEME}.png")
    img_bar = Image.open(f"bar-{THEME}.png")
    img_histogram = Image.open(f"histogram-{THEME}.png")

    # Create a new image for the composite (2x2 grid)
    width = img_scatter.width + img_bar.width + 60
    height = img_scatter.height + img_histogram.height + 60

    composite = Image.new("RGB", (width, height), PAGE_BG.replace("#", "0x"))

    # Paste images
    composite.paste(img_scatter, (10, 10))
    composite.paste(img_bar, (img_scatter.width + 20, 10))
    composite.paste(img_histogram, (10, img_scatter.height + 20))

    # Save composite
    composite.save(f"plot-{THEME}.png")

except Exception:
    # If PIL is not available, just use the scatter plot as fallback
    import shutil

    shutil.copy(f"scatter-{THEME}.png", f"plot-{THEME}.png")
