"""anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-07-26
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme-adaptive chrome tokens (Imprint)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Company budget breakdown by department, team, and project
# Hierarchical structure: Department > Team > Project
data = [
    # Engineering Department
    {"level_1": "Engineering", "level_2": "Backend", "level_3": "API", "value": 180},
    {"level_1": "Engineering", "level_2": "Backend", "level_3": "Database", "value": 120},
    {"level_1": "Engineering", "level_2": "Frontend", "level_3": "Web App", "value": 150},
    {"level_1": "Engineering", "level_2": "Frontend", "level_3": "Mobile", "value": 100},
    {"level_1": "Engineering", "level_2": "DevOps", "level_3": "Cloud", "value": 90},
    {"level_1": "Engineering", "level_2": "DevOps", "level_3": "CI/CD", "value": 60},
    # Marketing Department
    {"level_1": "Marketing", "level_2": "Digital", "level_3": "SEO", "value": 80},
    {"level_1": "Marketing", "level_2": "Digital", "level_3": "Social", "value": 70},
    {"level_1": "Marketing", "level_2": "Content", "level_3": "Blog", "value": 50},
    {"level_1": "Marketing", "level_2": "Content", "level_3": "Video", "value": 60},
    # Operations Department
    {"level_1": "Operations", "level_2": "Support", "level_3": "Tier 1", "value": 70},
    {"level_1": "Operations", "level_2": "Support", "level_3": "Tier 2", "value": 50},
    {"level_1": "Operations", "level_2": "HR", "level_3": "Recruiting", "value": 60},
    {"level_1": "Operations", "level_2": "HR", "level_3": "Training", "value": 40},
    # Sales Department
    {"level_1": "Sales", "level_2": "Enterprise", "level_3": "APAC", "value": 100},
    {"level_1": "Sales", "level_2": "Enterprise", "level_3": "EMEA", "value": 85},
    {"level_1": "Sales", "level_2": "SMB", "level_3": "Direct", "value": 65},
    {"level_1": "Sales", "level_2": "SMB", "level_3": "Partners", "value": 45},
]

df = pd.DataFrame(data)

# Imprint palette - first series is always #009E73 (brand green)
level1_colors = {
    "Engineering": "#009E73",  # brand green
    "Marketing": "#C475FD",  # lavender
    "Operations": "#4467A3",  # blue
    "Sales": "#BD8233",  # ochre
}

# Helper to lighten colors for child levels
hex_to_lighter = {}
for name, hex_color in level1_colors.items():
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    # Level 2: 25% lighter
    r2, g2, b2 = int(r + (255 - r) * 0.25), int(g + (255 - g) * 0.25), int(b + (255 - b) * 0.25)
    # Level 3: 50% lighter
    r3, g3, b3 = int(r + (255 - r) * 0.5), int(g + (255 - g) * 0.5), int(b + (255 - b) * 0.5)
    hex_to_lighter[name] = {"l1": hex_color, "l2": f"#{r2:02x}{g2:02x}{b2:02x}", "l3": f"#{r3:02x}{g3:02x}{b3:02x}"}

# Level 1: Department totals
level1_df = df.groupby("level_1")["value"].sum().reset_index()
level1_df.columns = ["name", "value"]
level1_df = level1_df.sort_values("value", ascending=False).reset_index(drop=True)
total_value = level1_df["value"].sum()

# Calculate level 1 angles (full circle distribution)
level1_df["theta"] = 0.0
level1_df["theta2"] = 0.0
current_angle = 0
for idx in level1_df.index:
    fraction = level1_df.loc[idx, "value"] / total_value
    level1_df.loc[idx, "theta"] = current_angle
    level1_df.loc[idx, "theta2"] = current_angle + fraction * 2 * np.pi
    current_angle = level1_df.loc[idx, "theta2"]

level1_df["color"] = level1_df["name"].map(level1_colors)

# Level 2: Team totals
level2_df = df.groupby(["level_1", "level_2"])["value"].sum().reset_index()
level2_df.columns = ["parent", "name", "value"]
level2_df = level2_df.sort_values(["parent", "value"], ascending=[True, False]).reset_index(drop=True)

# Calculate level 2 angles (within parent's arc)
level2_df["theta"] = 0.0
level2_df["theta2"] = 0.0
parent_cumulative = {row["name"]: row["theta"] for _, row in level1_df.iterrows()}

for idx in level2_df.index:
    parent = level2_df.loc[idx, "parent"]
    parent_row = level1_df[level1_df["name"] == parent].iloc[0]
    parent_start, parent_end = parent_row["theta"], parent_row["theta2"]
    parent_total = parent_row["value"]

    fraction = level2_df.loc[idx, "value"] / parent_total
    segment_angle = (parent_end - parent_start) * fraction

    level2_df.loc[idx, "theta"] = parent_cumulative[parent]
    level2_df.loc[idx, "theta2"] = parent_cumulative[parent] + segment_angle
    parent_cumulative[parent] = level2_df.loc[idx, "theta2"]

# Assign lighter colors for level 2
level2_df["color"] = level2_df["parent"].apply(lambda p: hex_to_lighter[p]["l2"])

# Level 3: Project values
level3_df = df.copy()
level3_df["parent_l1"] = level3_df["level_1"]
level3_df["parent_l2"] = level3_df["level_2"]
level3_df["name"] = level3_df["level_3"]
level3_df = level3_df.sort_values(["level_1", "level_2", "value"], ascending=[True, True, False]).reset_index(drop=True)

# Calculate level 3 angles (within parent's arc in level 2)
level3_df["theta"] = 0.0
level3_df["theta2"] = 0.0
l2_cumulative = {}
for _, row in level2_df.iterrows():
    key = f"{row['parent']}|{row['name']}"
    l2_cumulative[key] = {"start": row["theta"], "current": row["theta"], "end": row["theta2"], "total": row["value"]}

for idx in level3_df.index:
    key = f"{level3_df.loc[idx, 'level_1']}|{level3_df.loc[idx, 'level_2']}"
    l2_data = l2_cumulative[key]
    fraction = level3_df.loc[idx, "value"] / l2_data["total"]
    segment_angle = (l2_data["end"] - l2_data["start"]) * fraction

    level3_df.loc[idx, "theta"] = l2_data["current"]
    level3_df.loc[idx, "theta2"] = l2_data["current"] + segment_angle
    l2_data["current"] = level3_df.loc[idx, "theta2"]

# Assign lightest colors for level 3
level3_df["color"] = level3_df["level_1"].apply(lambda p: hex_to_lighter[p]["l3"])

# Ring radii (absolute pixels, centered in the 500x460 view)
inner_r1, outer_r1 = 60, 98  # Level 1 (innermost)
inner_r2, outer_r2 = 104, 142  # Level 2 (middle)
inner_r3, outer_r3 = 148, 186  # Level 3 (outermost)

# Overlay coordinate system (label/legend layer only, 1:1 with view pixels so
# radii computed above line up exactly with the arc marks' own pixel radii).
# range is explicit (not the Vega-Lite default flipped-Y range) so that
# label_y = -radius*cos(angle) (standard y-down screen convention) lines up
# with the arc marks' own top-origin, clockwise angle convention.
X_DOMAIN = [-250, 250]  # matches half of properties(width=500)
Y_DOMAIN = [-230, 230]  # matches half of properties(height=460)
X_SCALE = alt.Scale(domain=X_DOMAIN, range=[0, 500])
Y_SCALE = alt.Scale(domain=Y_DOMAIN, range=[0, 460])

# Level 1 - innermost ring (Departments)
chart_l1 = (
    alt.Chart(level1_df)
    .mark_arc(innerRadius=inner_r1, outerRadius=outer_r1, stroke=PAGE_BG, strokeWidth=2)
    .encode(
        theta=alt.Theta("theta:Q", scale=alt.Scale(domain=[0, 2 * np.pi])),
        theta2="theta2:Q",
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("name:N", title="Department"), alt.Tooltip("value:Q", title="Budget ($K)")],
    )
)

# Level 2 - middle ring (Teams)
chart_l2 = (
    alt.Chart(level2_df)
    .mark_arc(innerRadius=inner_r2, outerRadius=outer_r2, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        theta=alt.Theta("theta:Q", scale=alt.Scale(domain=[0, 2 * np.pi])),
        theta2="theta2:Q",
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip("parent:N", title="Department"),
            alt.Tooltip("name:N", title="Team"),
            alt.Tooltip("value:Q", title="Budget ($K)"),
        ],
    )
)

# Level 3 - outer ring (Projects)
chart_l3 = (
    alt.Chart(level3_df)
    .mark_arc(innerRadius=inner_r3, outerRadius=outer_r3, stroke=PAGE_BG, strokeWidth=1)
    .encode(
        theta=alt.Theta("theta:Q", scale=alt.Scale(domain=[0, 2 * np.pi])),
        theta2="theta2:Q",
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip("level_1:N", title="Department"),
            alt.Tooltip("level_2:N", title="Team"),
            alt.Tooltip("name:N", title="Project"),
            alt.Tooltip("value:Q", title="Budget ($K)"),
        ],
    )
)

# Add labels for level 1 segments (department names at arc center)
level1_df["label_angle"] = (level1_df["theta"] + level1_df["theta2"]) / 2
level1_df["label_radius"] = (inner_r1 + outer_r1) / 2
level1_df["label_x"] = level1_df["label_radius"] * np.sin(level1_df["label_angle"])
level1_df["label_y"] = -level1_df["label_radius"] * np.cos(level1_df["label_angle"])

text_l1 = (
    alt.Chart(level1_df)
    .mark_text(fontSize=12, fontWeight="bold", color="#ffffff")
    .encode(
        x=alt.X("label_x:Q", scale=X_SCALE, axis=None), y=alt.Y("label_y:Q", scale=Y_SCALE, axis=None), text="name:N"
    )
)

# Add legend as a horizontal row below the rings (kept left/right-balanced
# around x=0 so the donut itself stays centered on the padded canvas)
LEGEND_SLOT_W = 120
legend_items = []
for i, (_, row) in enumerate(level1_df.iterrows()):
    slot_x = -LEGEND_SLOT_W * len(level1_df) / 2 + i * LEGEND_SLOT_W
    legend_items.append({"dept": row["name"], "color": level1_colors[row["name"]], "x": slot_x, "y": 205})
legend_df = pd.DataFrame(legend_items)

legend_rects = (
    alt.Chart(legend_df)
    .mark_rect(width=14, height=14)
    .encode(
        x=alt.X("x:Q", scale=X_SCALE, axis=None),
        y=alt.Y("y:Q", scale=Y_SCALE, axis=None),
        color=alt.Color("color:N", scale=None),
    )
)

legend_text = (
    alt.Chart(legend_df)
    .mark_text(fontSize=10, align="left", dx=8, color=INK_SOFT)
    .encode(x=alt.X("x:Q", scale=X_SCALE, axis=None), y=alt.Y("y:Q", scale=Y_SCALE, axis=None), text="dept:N")
)

# Combine all layers
chart = (
    alt.layer(chart_l1, chart_l2, chart_l3, text_l1, legend_rects, legend_text)
    .properties(
        width=500,
        height=460,
        background=PAGE_BG,
        title=alt.Title(text="sunburst-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
)

# Save outputs — canonical square target 2400x2400 (see prompts/library/altair.md "Canvas")
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 2400, 2400
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

chart.save(f"plot-{THEME}.html")
