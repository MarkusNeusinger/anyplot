""" anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-13
"""

import os
import sys


# Remove script directory from sys.path to avoid importing local altair.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (colorblind-safe)
IMPRINT = [
    "#009E73",  # brand green (position 1)
    "#C475FD",  # vermillion (position 2)
    "#4467A3",  # blue (position 3)
    "#BD8233",  # reddish purple (position 4)
    "#AE3030",  # orange (position 5)
    "#2ABCCD",  # sky blue (position 6)
    "#954477",  # yellow (position 7)
]

# Data - Customer journey through product categories
np.random.seed(42)

n_customers = 200
channels = np.random.choice(["Direct", "Search", "Social", "Email"], n_customers, p=[0.3, 0.35, 0.2, 0.15])
categories = np.random.choice(["Electronics", "Clothing", "Home", "Sports"], n_customers, p=[0.25, 0.35, 0.25, 0.15])
outcomes = np.random.choice(["Purchase", "Abandon", "Browse"], n_customers, p=[0.4, 0.35, 0.25])

df = pd.DataFrame({"Channel": channels, "Category": categories, "Outcome": outcomes})
agg_df = df.groupby(["Channel", "Category", "Outcome"]).size().reset_index(name="count")

# Dimension x-positions
x_pos = {"Channel": 0, "Category": 250, "Outcome": 500}

# Color maps using Okabe-Ito palette
channel_colors = {
    "Direct": IMPRINT[0],  # brand green
    "Search": IMPRINT[1],  # vermillion
    "Social": IMPRINT[2],  # blue
    "Email": IMPRINT[3],  # reddish purple
}
category_colors = {
    "Electronics": IMPRINT[0],  # green
    "Clothing": IMPRINT[1],  # vermillion
    "Home": IMPRINT[2],  # blue
    "Sports": IMPRINT[3],  # reddish purple
}
outcome_colors = {
    "Purchase": IMPRINT[0],  # green
    "Abandon": IMPRINT[1],  # vermillion
    "Browse": IMPRINT[2],  # blue
}

scale_factor = 3.5

# Calculate y-positions for each category in each dimension
channel_totals = agg_df.groupby("Channel")["count"].sum().sort_values(ascending=False)
category_totals = agg_df.groupby("Category")["count"].sum().sort_values(ascending=False)
outcome_totals = agg_df.groupby("Outcome")["count"].sum().sort_values(ascending=False)

channel_pos = {}
y = 0
for cat in channel_totals.index:
    h = channel_totals[cat] * scale_factor
    channel_pos[cat] = {"y0": y, "y1": y + h, "total": channel_totals[cat]}
    y += h + 12

category_pos = {}
y = 0
for cat in category_totals.index:
    h = category_totals[cat] * scale_factor
    category_pos[cat] = {"y0": y, "y1": y + h, "total": category_totals[cat]}
    y += h + 12

outcome_pos = {}
y = 0
for cat in outcome_totals.index:
    h = outcome_totals[cat] * scale_factor
    outcome_pos[cat] = {"y0": y, "y1": y + h, "total": outcome_totals[cat]}
    y += h + 12

# Build flow connections
ch_offsets = dict.fromkeys(channel_pos, 0)
cat_left_offsets = dict.fromkeys(category_pos, 0)
cat_right_offsets = dict.fromkeys(category_pos, 0)
out_offsets = dict.fromkeys(outcome_pos, 0)

ch_cat_flows = agg_df.groupby(["Channel", "Category"])["count"].sum().reset_index()
flow_lines = []

for _, row in ch_cat_flows.iterrows():
    ch, cat, cnt = row["Channel"], row["Category"], row["count"]
    height = cnt * scale_factor
    src_y = channel_pos[ch]["y0"] + ch_offsets[ch] + height / 2
    ch_offsets[ch] += height
    tgt_y = category_pos[cat]["y0"] + cat_left_offsets[cat] + height / 2
    cat_left_offsets[cat] += height
    flow_lines.append(
        {
            "x0": x_pos["Channel"] + 50,
            "y0": src_y,
            "x1": x_pos["Category"],
            "y1": tgt_y,
            "strokeWidth": max(5, cnt * 2.0),
            "color": channel_colors[ch],
        }
    )

cat_out_flows = agg_df.groupby(["Category", "Outcome"])["count"].sum().reset_index()
for _, row in cat_out_flows.iterrows():
    cat, out, cnt = row["Category"], row["Outcome"], row["count"]
    height = cnt * scale_factor
    dom_ch = agg_df[agg_df["Category"] == cat].groupby("Channel")["count"].sum().idxmax()
    src_y = category_pos[cat]["y0"] + cat_right_offsets[cat] + height / 2
    cat_right_offsets[cat] += height
    tgt_y = outcome_pos[out]["y0"] + out_offsets[out] + height / 2
    out_offsets[out] += height
    flow_lines.append(
        {
            "x0": x_pos["Category"] + 50,
            "y0": src_y,
            "x1": x_pos["Outcome"],
            "y1": tgt_y,
            "strokeWidth": max(5, cnt * 2.0),
            "color": channel_colors[dom_ch],
        }
    )

# Create bezier curve points for smooth ribbons
bezier_pts = []
for flow_id, fl in enumerate(flow_lines):
    for t in np.linspace(0, 1, 20):
        x = (
            fl["x0"] * (1 - t) ** 3
            + (fl["x0"] + 60) * 3 * (1 - t) ** 2 * t
            + (fl["x1"] - 60) * 3 * (1 - t) * t**2
            + fl["x1"] * t**3
        )
        y = fl["y0"] * (1 - t) + fl["y1"] * t
        bezier_pts.append(
            {"x": x, "y": y, "flow_id": flow_id, "color": fl["color"], "strokeWidth": fl["strokeWidth"], "order": t}
        )

bezier_df = pd.DataFrame(bezier_pts)

# Create category box data with distinct colors for each dimension
box_data = []
color_maps = {"Channel": channel_colors, "Category": category_colors, "Outcome": outcome_colors}
for dim, pos_dict in [("Channel", channel_pos), ("Category", category_pos), ("Outcome", outcome_pos)]:
    for cat, pos in pos_dict.items():
        box_data.append(
            {
                "category": cat,
                "x": x_pos[dim],
                "x2": x_pos[dim] + 50,
                "y0": pos["y0"],
                "y1": pos["y1"],
                "y_mid": (pos["y0"] + pos["y1"]) / 2,
                "total": pos["total"],
                "color": color_maps[dim].get(cat, INK_SOFT),
            }
        )

box_df = pd.DataFrame(box_data)
max_y = box_df["y1"].max() + 80

# Visualization layers
flows = (
    alt.Chart(bezier_df)
    .mark_line(opacity=0.65, strokeCap="round")
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-50, 680])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-70, max_y])),
        detail="flow_id:N",
        order="order:Q",
        color=alt.Color("color:N", scale=None),
        strokeWidth=alt.StrokeWidth("strokeWidth:Q", scale=None),
    )
)

boxes = (
    alt.Chart(box_df)
    .mark_rect(stroke=INK_SOFT, strokeWidth=2, cornerRadius=4)
    .encode(
        x=alt.X("x:Q", axis=None),
        x2="x2:Q",
        y=alt.Y("y0:Q", axis=None),
        y2="y1:Q",
        color=alt.Color("color:N", scale=None),
    )
)

labels = (
    alt.Chart(box_df)
    .mark_text(align="left", baseline="middle", fontSize=18, fontWeight="bold", dx=58)
    .encode(x="x:Q", y="y_mid:Q", text="category:N", color=alt.value(INK))
)

counts = (
    alt.Chart(box_df)
    .mark_text(align="left", baseline="middle", fontSize=15, dx=58, dy=24)
    .encode(x="x:Q", y="y_mid:Q", text=alt.Text("total:Q", format="d"), color=alt.value(INK_SOFT))
)

# Headers positioned above the boxes
headers_df = pd.DataFrame(
    {
        "x": [x_pos["Channel"] + 25, x_pos["Category"] + 25, x_pos["Outcome"] + 25],
        "y": [-45, -45, -45],
        "header": ["Channel", "Category", "Outcome"],
    }
)
headers = (
    alt.Chart(headers_df)
    .mark_text(fontSize=24, fontWeight="bold")
    .encode(x="x:Q", y="y:Q", text="header:N", color=alt.value(INK))
)

# Legend for Channel colors (flow color coding) using square marks
legend_items = []
for i, (ch, color) in enumerate(channel_colors.items()):
    legend_items.append({"label": ch, "color": color, "x": 600, "y": i * 32 + 10})
legend_df = pd.DataFrame(legend_items)

legend_marks = (
    alt.Chart(legend_df).mark_square(size=400).encode(x="x:Q", y="y:Q", color=alt.Color("color:N", scale=None))
)

legend_labels = (
    alt.Chart(legend_df)
    .mark_text(align="left", baseline="middle", fontSize=16, dx=18)
    .encode(x="x:Q", y="y:Q", text="label:N", color=alt.value(INK_SOFT))
)

legend_title_df = pd.DataFrame({"x": [600], "y": [-25], "text": ["Flow Colors"]})
legend_title = (
    alt.Chart(legend_title_df)
    .mark_text(fontSize=18, fontWeight="bold", align="left")
    .encode(x="x:Q", y="y:Q", text="text:N", color=alt.value(INK))
)

# Combine layers
chart = (
    alt.layer(flows, boxes, labels, counts, headers, legend_title, legend_marks, legend_labels)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "parallel-categories-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK, offset=30
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
