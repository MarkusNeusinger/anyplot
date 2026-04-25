""" anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: altair 6.1.0 | Python 3.14.4
Quality: 86/100 | Created: 2026-04-25
"""

import importlib
import math
import os
import sys
from collections import defaultdict


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
pd = importlib.import_module("pandas")


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette: brand green, vermillion, blue
COLOR_A = "#009E73"
COLOR_B = "#D55E00"
COLOR_C = "#0072B2"

# Symmetric three-circle Venn layout on a 1200x1200 square canvas
CANVAS = 1200
center_x, center_y = CANVAS / 2, CANVAS / 2
RADIUS = 240
OFFSET = RADIUS / math.sqrt(3)

cx_a = center_x - OFFSET * math.sin(math.radians(60))
cy_a = center_y + OFFSET * math.cos(math.radians(60))
cx_b = center_x + OFFSET * math.sin(math.radians(60))
cy_b = center_y + OFFSET * math.cos(math.radians(60))
cx_c = center_x
cy_c = center_y - OFFSET

df_circles = pd.DataFrame(
    [
        {"name": "Overhyped", "x": cx_a, "y": cy_a, "color": COLOR_A},
        {"name": "Actually Useful", "x": cx_b, "y": cy_b, "color": COLOR_B},
        {"name": "Secretly Loved", "x": cx_c, "y": cy_c, "color": COLOR_C},
    ]
)

# Category labels: outside each circle, on the side away from the diagram centroid
label_a_x = cx_a + math.cos(math.radians(150)) * (RADIUS + 30)
label_a_y = cy_a + math.sin(math.radians(150)) * (RADIUS + 30)
label_b_x = cx_b + math.cos(math.radians(30)) * (RADIUS + 30)
label_b_y = cy_b + math.sin(math.radians(30)) * (RADIUS + 30)
label_c_x = cx_c
label_c_y = cy_c - (RADIUS + 30)

# Items distributed across the seven Venn zones
items_raw = [
    ("NFTs", "A"),
    ("Metaverse", "A"),
    ("Spreadsheets", "B"),
    ("USB Hubs", "B"),
    ("Bubble Wrap", "C"),
    ("Karaoke", "C"),
    ("ChatGPT", "AB"),
    ("Smartphones", "AB"),
    ("Vinyl Records", "AC"),
    ("Avocado Toast", "AC"),
    ("Google Maps", "BC"),
    ("Dolly Parton", "BC"),
    ("Sourdough", "ABC"),
    ("Coffee", "ABC"),
]

# Geometric centroids of each Venn region (chosen for clear in-zone placement)
zone_centers = {
    "A": (390, 715),
    "B": (810, 715),
    "C": (600, 357),
    "AB": (600, 745),
    "AC": (480, 540),
    "BC": (720, 540),
    "ABC": (600, 600),
}

zone_to_items = defaultdict(list)
for label, zone in items_raw:
    zone_to_items[zone].append(label)

LINE_HEIGHT = 30
records = []
for zone, labels in zone_to_items.items():
    cx_zone, cy_zone = zone_centers[zone]
    n = len(labels)
    start_y = cy_zone + (n - 1) * LINE_HEIGHT / 2
    for idx, label in enumerate(labels):
        records.append({"label": label, "zone": zone, "x": cx_zone, "y": start_y - idx * LINE_HEIGHT})
df_items = pd.DataFrame(records)

# Plot
domain_x = [0, CANVAS]
domain_y = [0, CANVAS]
circle_size = math.pi * RADIUS * RADIUS

filled_circles = (
    alt.Chart(df_circles)
    .mark_point(shape="circle", filled=True, opacity=0.22, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=domain_x), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=domain_y), axis=None),
        color=alt.Color("color:N", scale=None, legend=None),
        size=alt.value(circle_size),
    )
)

outline_circles = (
    alt.Chart(df_circles)
    .mark_point(shape="circle", filled=False, strokeWidth=2.5, opacity=0.85)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=domain_x), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=domain_y), axis=None),
        stroke=alt.Color("color:N", scale=None, legend=None),
        size=alt.value(circle_size),
    )
)

label_a = (
    alt.Chart(pd.DataFrame([{"x": label_a_x, "y": label_a_y}]))
    .mark_text(
        text="Overhyped",
        fontSize=30,
        fontWeight="bold",
        fontStyle="italic",
        font="serif",
        color=COLOR_A,
        align="right",
        baseline="bottom",
    )
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=domain_x), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=domain_y), axis=None),
    )
)

label_b = (
    alt.Chart(pd.DataFrame([{"x": label_b_x, "y": label_b_y}]))
    .mark_text(
        text="Actually Useful",
        fontSize=30,
        fontWeight="bold",
        fontStyle="italic",
        font="serif",
        color=COLOR_B,
        align="left",
        baseline="bottom",
    )
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=domain_x), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=domain_y), axis=None),
    )
)

label_c = (
    alt.Chart(pd.DataFrame([{"x": label_c_x, "y": label_c_y}]))
    .mark_text(
        text="Secretly Loved",
        fontSize=30,
        fontWeight="bold",
        fontStyle="italic",
        font="serif",
        color=COLOR_C,
        align="center",
        baseline="top",
    )
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=domain_x), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=domain_y), axis=None),
    )
)

item_labels = (
    alt.Chart(df_items)
    .mark_text(fontSize=20, color=INK, fontWeight="normal")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=domain_x), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=domain_y), axis=None),
        text="label:N",
    )
)

chart = (
    alt.layer(filled_circles, outline_circles, label_a, label_b, label_c, item_labels)
    .properties(
        width=CANVAS,
        height=CANVAS,
        background=PAGE_BG,
        title=alt.Title(
            text="Pop Culture Vibes · venn-labeled-items · altair · anyplot.ai",
            subtitle="An opinionated three-circle taxonomy",
            fontSize=28,
            subtitleFontSize=18,
            color=INK,
            subtitleColor=INK_SOFT,
            anchor="middle",
            font="serif",
            subtitleFont="serif",
            subtitleFontStyle="italic",
            offset=24,
        ),
        padding={"left": 30, "right": 30, "top": 20, "bottom": 20},
    )
    .configure_view(fill=PAGE_BG, stroke=None)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
