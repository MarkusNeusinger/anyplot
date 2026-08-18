"""anyplot.ai
box-grouped: Grouped Box Plot
Library: altair 6.1.0 | Python 3.13.13
"""

import os

import altair
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (positions 1, 2, 3 for Junior, Mid, Senior)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Employee performance scores across departments and experience levels
np.random.seed(42)

departments = ["Engineering", "Sales", "Marketing", "Support"]
experience_levels = ["Junior", "Mid", "Senior"]

data = []
# Create varied distributions for each combination
distributions = {
    ("Engineering", "Junior"): (65, 12),
    ("Engineering", "Mid"): (75, 10),
    ("Engineering", "Senior"): (85, 8),
    ("Sales", "Junior"): (55, 15),
    ("Sales", "Mid"): (70, 12),
    ("Sales", "Senior"): (80, 10),
    ("Marketing", "Junior"): (60, 14),
    ("Marketing", "Mid"): (72, 11),
    ("Marketing", "Senior"): (82, 9),
    ("Support", "Junior"): (58, 13),
    ("Support", "Mid"): (68, 12),
    ("Support", "Senior"): (78, 10),
}

for dept in departments:
    for exp in experience_levels:
        mean, std = distributions[(dept, exp)]
        n_samples = 50
        values = np.random.normal(mean, std, n_samples)
        # Add some outliers
        if np.random.random() > 0.5:
            values = np.append(values, [mean + 3.5 * std, mean - 3 * std])
        # Clip to realistic range
        values = np.clip(values, 0, 100)
        for v in values:
            data.append({"Department": dept, "Experience": exp, "Performance Score": v})

df = pd.DataFrame(data)

# Create grouped box plot with theme-adaptive styling
chart = (
    altair.Chart(df)
    .mark_boxplot(size=22, median={"stroke": INK, "strokeWidth": 1.5}, outliers={"size": 28, "strokeOpacity": 0.7})
    .encode(
        x=altair.X("Department:N", title="Department", axis=altair.Axis(labelFontSize=10, titleFontSize=12)),
        y=altair.Y(
            "Performance Score:Q",
            title="Performance Score (%)",
            scale=altair.Scale(domain=[0, 105]),
            axis=altair.Axis(labelFontSize=10, titleFontSize=12),
        ),
        color=altair.Color(
            "Experience:N",
            title="Experience Level",
            scale=altair.Scale(domain=["Junior", "Mid", "Senior"], range=IMPRINT),
            legend=altair.Legend(titleFontSize=10, labelFontSize=10, symbolSize=100, orient="top-left"),
        ),
        xOffset="Experience:N",
        tooltip=["Department:N", "Experience:N", "Performance Score:Q"],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=altair.Title(text="box-grouped · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save as PNG and HTML with theme-suffixed filenames
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Canvas contract: pad (never crop) the exported PNG up to the exact target.
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}x{_h}, exceeds target {TW}x{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")
