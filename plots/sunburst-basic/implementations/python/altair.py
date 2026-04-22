""" pyplots.ai
sunburst-basic: Basic Sunburst Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


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

# Color palette - Python Blue as primary, with colorblind-safe colors
level1_colors = {
    "Engineering": "#306998",  # Python Blue
    "Marketing": "#FFD43B",  # Python Yellow
    "Operations": "#4ECDC4",  # Teal
    "Sales": "#FF6B6B",  # Coral
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

# Ring radii (scaled for 1200x1200 canvas)
inner_r1, outer_r1 = 100, 200  # Level 1 (innermost)
inner_r2, outer_r2 = 210, 310  # Level 2 (middle)
inner_r3, outer_r3 = 320, 420  # Level 3 (outermost)

# Level 1 - innermost ring (Departments)
chart_l1 = (
    alt.Chart(level1_df)
    .mark_arc(innerRadius=inner_r1, outerRadius=outer_r1, stroke="#ffffff", strokeWidth=2)
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
    .mark_arc(innerRadius=inner_r2, outerRadius=outer_r2, stroke="#ffffff", strokeWidth=1.5)
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
    .mark_arc(innerRadius=inner_r3, outerRadius=outer_r3, stroke="#ffffff", strokeWidth=1)
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
    .mark_text(fontSize=18, fontWeight="bold", color="#ffffff")
    .encode(
        x=alt.X("label_x:Q", scale=alt.Scale(domain=[-500, 500]), axis=None),
        y=alt.Y("label_y:Q", scale=alt.Scale(domain=[-500, 500]), axis=None),
        text="name:N",
    )
)

# Add legend with department colors (sorted by value, matching level1_df order)
legend_items = []
for i, (_, row) in enumerate(level1_df.iterrows()):
    legend_items.append({"dept": row["name"], "color": level1_colors[row["name"]], "x": 480, "y": -350 + i * 45})
legend_df = pd.DataFrame(legend_items)

legend_rects = (
    alt.Chart(legend_df)
    .mark_rect(width=20, height=20)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-500, 500]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-500, 500]), axis=None),
        color=alt.Color("color:N", scale=None),
    )
)

legend_text = (
    alt.Chart(legend_df)
    .mark_text(fontSize=16, align="left", dx=15)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-500, 500]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-500, 500]), axis=None),
        text="dept:N",
    )
)

# Combine all layers
chart = (
    alt.layer(chart_l1, chart_l2, chart_l3, text_l1, legend_rects, legend_text)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(text="sunburst-basic · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save outputs (3600x3600 px with scale_factor=3.0)
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
