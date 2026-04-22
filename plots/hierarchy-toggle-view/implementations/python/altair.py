""" pyplots.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: altair 6.0.0 | Python 3.13.11
Quality: 72/100 | Created: 2026-01-11
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Company structure with departments and teams (18 nodes, 3 levels)
np.random.seed(42)

hierarchy_data = [
    # Root
    {"id": "Company", "parent": "", "label": "TechCorp", "value": 0},
    # Level 1 - Departments
    {"id": "Engineering", "parent": "Company", "label": "Engineering", "value": 0},
    {"id": "Sales", "parent": "Company", "label": "Sales", "value": 0},
    {"id": "Marketing", "parent": "Company", "label": "Marketing", "value": 0},
    {"id": "Operations", "parent": "Company", "label": "Operations", "value": 0},
    # Level 2 - Engineering Teams
    {"id": "Frontend", "parent": "Engineering", "label": "Frontend", "value": 55},
    {"id": "Backend", "parent": "Engineering", "label": "Backend", "value": 62},
    {"id": "DevOps", "parent": "Engineering", "label": "DevOps", "value": 38},
    {"id": "QA", "parent": "Engineering", "label": "QA", "value": 32},
    {"id": "DataSci", "parent": "Engineering", "label": "Data Sci", "value": 45},
    # Level 2 - Sales Teams
    {"id": "Enterprise", "parent": "Sales", "label": "Enterprise", "value": 48},
    {"id": "SMB", "parent": "Sales", "label": "SMB", "value": 35},
    {"id": "Partners", "parent": "Sales", "label": "Partners", "value": 28},
    # Level 2 - Marketing Teams
    {"id": "Digital", "parent": "Marketing", "label": "Digital", "value": 30},
    {"id": "Content", "parent": "Marketing", "label": "Content", "value": 25},
    {"id": "Events", "parent": "Marketing", "label": "Events", "value": 22},
    # Level 2 - Operations Teams
    {"id": "HR", "parent": "Operations", "label": "HR", "value": 28},
    {"id": "Finance", "parent": "Operations", "label": "Finance", "value": 32},
    {"id": "Legal", "parent": "Operations", "label": "Legal", "value": 20},
]

df = pd.DataFrame(hierarchy_data)

# Calculate parent values (sum of children)
parent_ids = df[df["parent"] != ""]["parent"].unique()
for _ in range(5):
    for parent_id in parent_ids:
        children = df[df["parent"] == parent_id]
        if len(children) > 0 and all(children["value"] > 0):
            df.loc[df["id"] == parent_id, "value"] = children["value"].sum()

# Assign department colors based on parent chain
dept_mapping = {"Engineering": "Engineering", "Sales": "Sales", "Marketing": "Marketing", "Operations": "Operations"}
for dept in dept_mapping:
    df.loc[df["parent"] == dept, "department"] = dept
df.loc[df["id"].isin(dept_mapping.keys()), "department"] = df.loc[df["id"].isin(dept_mapping.keys()), "id"]
df["department"] = df["department"].fillna("Company")

# Get leaf nodes (nodes that are not parents)
all_parent_ids = set(df["parent"].unique())
leaf_mask = ~df["id"].isin(all_parent_ids - {""})
leaf_df = df[leaf_mask & (df["value"] > 0)].copy()

# Build treemap rectangles using iterative binary split algorithm (no functions)
# Sort items by value descending for better layout
sorted_leaf = leaf_df.sort_values("value", ascending=False).reset_index(drop=True)
items = [(row["value"], row["id"], row["label"], row["department"]) for _, row in sorted_leaf.iterrows()]

# Iterative squarified layout using a stack - fills canvas from (0,0) to (100,100)
layout_stack = [(items, 0, 0, 100, 100)]  # (items, x, y, width, height)
treemap_records = []

while layout_stack:
    current_items, x, y, w, h = layout_stack.pop()
    if not current_items:
        continue
    if len(current_items) == 1:
        val, nid, lbl, dept = current_items[0]
        treemap_records.append(
            {
                "id": nid,
                "label": lbl,
                "value": val,
                "department": dept,
                "x": x,
                "y": y,
                "x2": x + w,
                "y2": y + h,
                "cx": x + w / 2,
                "cy": y + h / 2,
                "view": "Treemap",
            }
        )
        continue
    # Split items at approximate half of total value for best aspect ratio
    total = sum(v for v, _, _, _ in current_items)
    half_val = total / 2
    cumsum = 0
    split_idx = 1
    for i, (val, _, _, _) in enumerate(current_items):
        cumsum += val
        if cumsum >= half_val:
            split_idx = i + 1
            break
    left_items = current_items[:split_idx]
    right_items = current_items[split_idx:]
    left_total = sum(v for v, _, _, _ in left_items)
    ratio = left_total / total if total > 0 else 0.5
    # Choose horizontal or vertical split for better aspect ratios
    if w >= h:
        layout_stack.append((right_items, x + w * ratio, y, w * (1 - ratio), h))
        layout_stack.append((left_items, x, y, w * ratio, h))
    else:
        layout_stack.append((right_items, x, y + h * ratio, w, h * (1 - ratio)))
        layout_stack.append((left_items, x, y, w, h * ratio))

treemap_df = pd.DataFrame(treemap_records)

# Build sunburst data from hierarchy - centered at origin
sunburst_records = []
departments = ["Engineering", "Sales", "Marketing", "Operations"]
dept_values = {d: df[df["id"] == d]["value"].values[0] for d in departments}
total_company = sum(dept_values.values())

# Create arc segments for sunburst
start_angle = 0
for dept in departments:
    dept_angle = 360 * (dept_values[dept] / total_company)
    end_angle = start_angle + dept_angle
    mid_angle = (start_angle + end_angle) / 2
    mid_angle_rad = np.radians(mid_angle - 90)
    sunburst_records.append(
        {
            "id": dept,
            "label": dept,
            "value": dept_values[dept],
            "department": dept,
            "startAngle": start_angle,
            "endAngle": end_angle,
            "innerRadius": 35,
            "outerRadius": 65,
            "depth": 1,
            "labelX": np.cos(mid_angle_rad) * 50,
            "labelY": np.sin(mid_angle_rad) * 50,
            "view": "Sunburst",
        }
    )
    # Team arcs within department
    teams = df[df["parent"] == dept]
    dept_start = start_angle
    for _, team in teams.iterrows():
        team_angle = dept_angle * (team["value"] / dept_values[dept]) if dept_values[dept] > 0 else 0
        team_end = dept_start + team_angle
        team_mid_angle = (dept_start + team_end) / 2
        team_mid_rad = np.radians(team_mid_angle - 90)
        sunburst_records.append(
            {
                "id": team["id"],
                "label": team["label"],
                "value": team["value"],
                "department": dept,
                "startAngle": dept_start,
                "endAngle": team_end,
                "innerRadius": 65,
                "outerRadius": 100,
                "depth": 2,
                "labelX": np.cos(team_mid_rad) * 82,
                "labelY": np.sin(team_mid_rad) * 82,
                "view": "Sunburst",
            }
        )
        dept_start = team_end
    start_angle = end_angle

sunburst_df = pd.DataFrame(sunburst_records)
sunburst_df["startAngle_rad"] = np.radians(sunburst_df["startAngle"] - 90)
sunburst_df["endAngle_rad"] = np.radians(sunburst_df["endAngle"] - 90)

# Color scale - colorblind-friendly
dept_domain = ["Engineering", "Sales", "Marketing", "Operations"]
dept_range = ["#306998", "#FFD43B", "#E74C3C", "#27AE60"]

# Interactive toggle selection
view_dropdown = alt.binding_select(options=["Treemap", "Sunburst"], name="Select View: ")
view_selection = alt.selection_point(fields=["view"], bind=view_dropdown, value="Treemap")

# Treemap chart - rectangles fill the full canvas (0-100 scale for both axes)
treemap_rects = (
    alt.Chart(treemap_df)
    .mark_rect(stroke="white", strokeWidth=3)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(
            "department:N",
            scale=alt.Scale(domain=dept_domain, range=dept_range),
            legend=alt.Legend(title="Department", titleFontSize=20, labelFontSize=18, orient="right"),
        ),
        opacity=alt.condition(view_selection, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("label:N", title="Team"),
            alt.Tooltip("value:Q", title="Headcount"),
            alt.Tooltip("department:N", title="Department"),
        ],
    )
    .add_params(view_selection)
)

# Treemap chart - labels sized by cell value
treemap_labels = (
    alt.Chart(treemap_df)
    .mark_text(fontWeight="bold", color="white", baseline="middle", align="center")
    .encode(
        x=alt.X("cx:Q", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("cy:Q", scale=alt.Scale(domain=[0, 100])),
        text="label:N",
        opacity=alt.condition(view_selection, alt.value(1), alt.value(0)),
        size=alt.Size("value:Q", scale=alt.Scale(domain=[20, 65], range=[14, 24]), legend=None),
    )
)

treemap_chart = treemap_rects + treemap_labels

# Sunburst chart - arcs centered and scaled to fill canvas
sunburst_arcs = (
    alt.Chart(sunburst_df)
    .mark_arc(stroke="white", strokeWidth=2)
    .encode(
        theta=alt.Theta("endAngle_rad:Q", scale=alt.Scale(domain=[-np.pi, np.pi])),
        theta2="startAngle_rad:Q",
        radius=alt.Radius("outerRadius:Q", scale=alt.Scale(domain=[0, 120], range=[0, 420])),
        radius2="innerRadius:Q",
        color=alt.Color("department:N", scale=alt.Scale(domain=dept_domain, range=dept_range), legend=None),
        opacity=alt.condition(view_selection, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("label:N", title="Name"),
            alt.Tooltip("value:Q", title="Headcount"),
            alt.Tooltip("department:N", title="Department"),
        ],
    )
)

# Sunburst department labels (inner ring)
dept_labels_df = sunburst_df[sunburst_df["depth"] == 1].copy()
sunburst_dept_labels = (
    alt.Chart(dept_labels_df)
    .mark_text(fontSize=16, fontWeight="bold", color="white", baseline="middle", align="center")
    .encode(
        x=alt.X("labelX:Q", scale=alt.Scale(domain=[-130, 130])),
        y=alt.Y("labelY:Q", scale=alt.Scale(domain=[-130, 130])),
        text="label:N",
        opacity=alt.condition(view_selection, alt.value(1), alt.value(0)),
    )
)

# Sunburst team labels (outer ring, larger teams only)
team_labels_df = sunburst_df[(sunburst_df["depth"] == 2) & (sunburst_df["value"] >= 28)].copy()
sunburst_team_labels = (
    alt.Chart(team_labels_df)
    .mark_text(fontSize=14, fontWeight="normal", color="white", baseline="middle", align="center")
    .encode(
        x=alt.X("labelX:Q", scale=alt.Scale(domain=[-130, 130])),
        y=alt.Y("labelY:Q", scale=alt.Scale(domain=[-130, 130])),
        text="label:N",
        opacity=alt.condition(view_selection, alt.value(1), alt.value(0)),
    )
)

sunburst_chart = sunburst_arcs + sunburst_dept_labels + sunburst_team_labels

# Layer both views together with toggle control
combined_chart = (
    alt.layer(treemap_chart, sunburst_chart)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "hierarchy-toggle-view · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            offset=20,
            subtitle="Use dropdown to toggle between Treemap and Sunburst views",
            subtitleFontSize=18,
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=20, labelFontSize=18, symbolSize=200)
)

# Save outputs - 4800x2700 per style guide (1600 × 3 = 4800, 900 × 3 = 2700)
combined_chart.save("plot.png", scale_factor=3.0)
combined_chart.save("plot.html")
