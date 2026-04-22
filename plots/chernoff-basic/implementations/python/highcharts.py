""" pyplots.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import base64
import tempfile
import time
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_iris


# Data - Using Iris dataset (4 variables per flower)
np.random.seed(42)
iris = load_iris()
X = iris.data
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

# Take 3 samples from each species for 9 total faces
sample_indices = []
for species_id in [0, 1, 2]:
    species_indices = np.where(y == species_id)[0]
    sample_indices.extend(species_indices[:3])

X_sample = X[sample_indices]
y_sample = y[sample_indices]

# Normalize data to 0-1 range for each feature
X_min = X_sample.min(axis=0)
X_max = X_sample.max(axis=0)
X_norm = (X_sample - X_min) / (X_max - X_min + 1e-8)

# Colors for species - colorblind-safe
species_colors = ["#306998", "#FFD43B", "#9467BD"]

# SVG dimensions
svg_width = 4800
svg_height = 2700

# Build custom Chernoff faces HTML/SVG
# Feature mappings:
# - Variable 0 (sepal length): face width
# - Variable 1 (sepal width): eye size
# - Variable 2 (petal length): mouth curvature
# - Variable 3 (petal width): eyebrow slant


def create_face_svg(values, color, label, x_pos, y_pos, size=450):
    """Create SVG for a single Chernoff face."""
    # Extract normalized values (0-1)
    face_width = 0.7 + values[0] * 0.3  # 0.7 to 1.0 multiplier
    eye_size = 0.7 + values[1] * 0.5  # 0.7 to 1.2 multiplier
    mouth_curve = values[2] * 2 - 1  # -1 to 1 (sad to happy)
    eyebrow_slant = (values[3] - 0.5) * 30  # -15 to +15 degrees

    cx = x_pos + size // 2
    cy = y_pos + size // 2
    face_rx = int(size * 0.4 * face_width)
    face_ry = int(size * 0.45)

    # Eye positions and sizes
    eye_cx_left = cx - int(size * 0.15)
    eye_cx_right = cx + int(size * 0.15)
    eye_cy = cy - int(size * 0.08)
    eye_r = int(18 * eye_size)
    pupil_r = int(9 * eye_size)

    # Mouth (cubic bezier curve)
    mouth_y = cy + int(size * 0.2)
    mouth_width = int(size * 0.25)
    mouth_curve_offset = int(mouth_curve * size * 0.12)

    # Eyebrows
    brow_y = eye_cy - int(size * 0.12)
    brow_len = int(size * 0.12)

    svg = f"""
    <!-- Face {label} -->
    <ellipse cx="{cx}" cy="{cy}" rx="{face_rx}" ry="{face_ry}"
             fill="{color}" stroke="#333333" stroke-width="4"/>

    <!-- Left eye -->
    <circle cx="{eye_cx_left}" cy="{eye_cy}" r="{eye_r}" fill="white" stroke="#333333" stroke-width="3"/>
    <circle cx="{eye_cx_left}" cy="{eye_cy}" r="{pupil_r}" fill="#333333"/>

    <!-- Right eye -->
    <circle cx="{eye_cx_right}" cy="{eye_cy}" r="{eye_r}" fill="white" stroke="#333333" stroke-width="3"/>
    <circle cx="{eye_cx_right}" cy="{eye_cy}" r="{pupil_r}" fill="#333333"/>

    <!-- Left eyebrow -->
    <line x1="{eye_cx_left - brow_len}" y1="{brow_y + int(eyebrow_slant)}"
          x2="{eye_cx_left + brow_len}" y2="{brow_y - int(eyebrow_slant)}"
          stroke="#333333" stroke-width="5" stroke-linecap="round"/>

    <!-- Right eyebrow -->
    <line x1="{eye_cx_right - brow_len}" y1="{brow_y - int(eyebrow_slant)}"
          x2="{eye_cx_right + brow_len}" y2="{brow_y + int(eyebrow_slant)}"
          stroke="#333333" stroke-width="5" stroke-linecap="round"/>

    <!-- Nose -->
    <line x1="{cx}" y1="{cy - int(size * 0.02)}" x2="{cx}" y2="{cy + int(size * 0.1)}"
          stroke="#333333" stroke-width="4" stroke-linecap="round"/>

    <!-- Mouth -->
    <path d="M {cx - mouth_width} {mouth_y} Q {cx} {mouth_y + mouth_curve_offset} {cx + mouth_width} {mouth_y}"
          fill="none" stroke="#333333" stroke-width="5" stroke-linecap="round"/>

    <!-- Label -->
    <text x="{cx}" y="{y_pos + size + 50}" text-anchor="middle"
          font-size="36" font-family="Arial, sans-serif" font-weight="bold">{label}</text>
    """
    return svg


# Create the complete HTML with embedded SVG
faces_svg = ""
face_size = 580
cols = 3
rows = 3

# Calculate grid to center faces properly across the canvas
# Leave space for legends on right (about 600px) and title at top (about 220px)
grid_left = 100
grid_right = 3350
grid_top = 250
grid_bottom = svg_height - 100

grid_width = grid_right - grid_left
grid_height = grid_bottom - grid_top

# Calculate cell size for even distribution
cell_width = grid_width // cols
cell_height = grid_height // rows

for idx in range(9):
    row = idx // cols
    col = idx % cols

    # Center face within its cell
    cell_x = grid_left + col * cell_width
    cell_y = grid_top + row * cell_height
    x_pos = cell_x + (cell_width - face_size) // 2
    y_pos = cell_y + (cell_height - face_size - 60) // 2  # -60 for label space

    species_idx = y_sample[idx]
    color = species_colors[species_idx]
    label = f"{species_names[species_idx]} #{(idx % 3) + 1}"

    faces_svg += create_face_svg(X_norm[idx], color, label, x_pos, y_pos, face_size)

# Create legend - positioned in right column, vertically centered
legend_x = 3550
legend_y = 450
legend_svg = f"""
<rect x="{legend_x}" y="{legend_y}" width="550" height="380" fill="#f8f8f8" stroke="#333333" stroke-width="3" rx="15"/>
<text x="{legend_x + 35}" y="{legend_y + 60}" font-size="44" font-family="Arial, sans-serif" font-weight="bold">Species Legend</text>
"""

for i, (species, color) in enumerate(zip(species_names, species_colors, strict=True)):
    ly_item = legend_y + 130 + i * 80
    legend_svg += f"""
    <circle cx="{legend_x + 60}" cy="{ly_item}" r="30" fill="{color}" stroke="#333333" stroke-width="3"/>
    <text x="{legend_x + 110}" y="{ly_item + 14}" font-size="38" font-family="Arial, sans-serif">{species}</text>
    """

# Feature mapping legend
feature_legend_y = legend_y + 450
feature_legend_svg = f"""
<rect x="{legend_x}" y="{feature_legend_y}" width="550" height="480" fill="#f8f8f8" stroke="#333333" stroke-width="3" rx="15"/>
<text x="{legend_x + 35}" y="{feature_legend_y + 60}" font-size="40" font-family="Arial, sans-serif" font-weight="bold">Feature Mapping</text>
<text x="{legend_x + 35}" y="{feature_legend_y + 130}" font-size="30" font-family="Arial, sans-serif">Face Width → Sepal Length</text>
<text x="{legend_x + 35}" y="{feature_legend_y + 190}" font-size="30" font-family="Arial, sans-serif">Eye Size → Sepal Width</text>
<text x="{legend_x + 35}" y="{feature_legend_y + 250}" font-size="30" font-family="Arial, sans-serif">Mouth Curve → Petal Length</text>
<text x="{legend_x + 35}" y="{feature_legend_y + 310}" font-size="30" font-family="Arial, sans-serif">Eyebrow Slant → Petal Width</text>
<line x1="{legend_x + 35}" y1="{feature_legend_y + 355}" x2="{legend_x + 515}" y2="{feature_legend_y + 355}" stroke="#cccccc" stroke-width="2"/>
<text x="{legend_x + 35}" y="{feature_legend_y + 410}" font-size="26" font-family="Arial, sans-serif" fill="#666666">All values normalized to 0-1 range</text>
"""

# Complete HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ margin: 0; padding: 0; background: #ffffff; }}
    </style>
</head>
<body>
    <svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
        <!-- Background -->
        <rect width="100%" height="100%" fill="#ffffff"/>

        <!-- Title -->
        <text x="{svg_width // 2}" y="100" text-anchor="middle"
              font-size="64" font-family="Arial, sans-serif" font-weight="bold">
            chernoff-basic · highcharts · pyplots.ai
        </text>

        <!-- Subtitle -->
        <text x="{svg_width // 2}" y="175" text-anchor="middle"
              font-size="40" font-family="Arial, sans-serif" fill="#666666">
            Iris Dataset: 4 Variables Mapped to Facial Features (9 Samples, 3 Per Species)
        </text>

        <!-- Faces Grid -->
        {faces_svg}

        <!-- Species Legend -->
        {legend_svg}

        <!-- Feature Mapping Legend -->
        {feature_legend_svg}
    </svg>
</body>
</html>"""

# Save HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Export to PNG via Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(3)

# Use CDP to capture full page at exact dimensions
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 4800, "height": 2700, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(1)

# Take screenshot with clip to exact dimensions
result = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {
        "format": "png",
        "captureBeyondViewport": True,
        "clip": {"x": 0, "y": 0, "width": 4800, "height": 2700, "scale": 1},
    },
)

with open("plot.png", "wb") as f:
    f.write(base64.b64decode(result["data"]))

driver.quit()

Path(temp_path).unlink()
