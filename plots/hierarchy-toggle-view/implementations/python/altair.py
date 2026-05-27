""" anyplot.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

DEPT_DOMAIN = ["Engineering", "Sales", "Marketing", "Operations"]
DEPT_COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data
np.random.seed(42)

hierarchy_data = [
    {"id": "Company", "parent": "", "label": "TechCorp", "value": 0},
    {"id": "Engineering", "parent": "Company", "label": "Engineering", "value": 0},
    {"id": "Sales", "parent": "Company", "label": "Sales", "value": 0},
    {"id": "Marketing", "parent": "Company", "label": "Marketing", "value": 0},
    {"id": "Operations", "parent": "Company", "label": "Operations", "value": 0},
    {"id": "Frontend", "parent": "Engineering", "label": "Frontend", "value": 55},
    {"id": "Backend", "parent": "Engineering", "label": "Backend", "value": 62},
    {"id": "DevOps", "parent": "Engineering", "label": "DevOps", "value": 38},
    {"id": "QA", "parent": "Engineering", "label": "QA", "value": 32},
    {"id": "DataSci", "parent": "Engineering", "label": "Data Sci", "value": 45},
    {"id": "Enterprise", "parent": "Sales", "label": "Enterprise", "value": 48},
    {"id": "SMB", "parent": "Sales", "label": "SMB", "value": 35},
    {"id": "Partners", "parent": "Sales", "label": "Partners", "value": 28},
    {"id": "Digital", "parent": "Marketing", "label": "Digital", "value": 30},
    {"id": "Content", "parent": "Marketing", "label": "Content", "value": 25},
    {"id": "Events", "parent": "Marketing", "label": "Events", "value": 22},
    {"id": "HR", "parent": "Operations", "label": "HR", "value": 28},
    {"id": "Finance", "parent": "Operations", "label": "Finance", "value": 32},
    {"id": "Legal", "parent": "Operations", "label": "Legal", "value": 20},
]

df = pd.DataFrame(hierarchy_data)

# Calculate parent values (sum of leaf children)
parent_ids = df[df["parent"] != ""]["parent"].unique()
for _ in range(5):
    for parent_id in parent_ids:
        children = df[df["parent"] == parent_id]
        if len(children) > 0 and all(children["value"] > 0):
            df.loc[df["id"] == parent_id, "value"] = children["value"].sum()

# Assign department grouping
for dept in DEPT_DOMAIN:
    df.loc[df["parent"] == dept, "department"] = dept
df.loc[df["id"].isin(DEPT_DOMAIN), "department"] = df.loc[df["id"].isin(DEPT_DOMAIN), "id"]
df["department"] = df["department"].fillna("Company")

# Treemap layout (leaf nodes only) - fills [0,100] x [0,100] coordinate space
all_parent_ids = set(df["parent"].unique())
leaf_mask = ~df["id"].isin(all_parent_ids - {""})
leaf_df = df[leaf_mask & (df["value"] > 0)].copy()

sorted_leaf = leaf_df.sort_values("value", ascending=False).reset_index(drop=True)
items = [(row["value"], row["id"], row["label"], row["department"]) for _, row in sorted_leaf.iterrows()]

layout_stack = [(items, 0, 0, 100, 100)]
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
    if w >= h:
        layout_stack.append((right_items, x + w * ratio, y, w * (1 - ratio), h))
        layout_stack.append((left_items, x, y, w * ratio, h))
    else:
        layout_stack.append((right_items, x, y + h * ratio, w, h * (1 - ratio)))
        layout_stack.append((left_items, x, y, w, h * ratio))

treemap_df = pd.DataFrame(treemap_records)

# Sunburst data (polar arc segments, no x/y to avoid scale conflict with treemap)
sunburst_records = []
dept_values = {d: df[df["id"] == d]["value"].values[0] for d in DEPT_DOMAIN}
total_company = sum(dept_values.values())

start_angle = 0
for dept in DEPT_DOMAIN:
    dept_angle = 360 * (dept_values[dept] / total_company)
    end_angle = start_angle + dept_angle
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
            "view": "Sunburst",
        }
    )
    teams = df[df["parent"] == dept]
    dept_start = start_angle
    for _, team in teams.iterrows():
        team_angle = dept_angle * (team["value"] / dept_values[dept]) if dept_values[dept] > 0 else 0
        team_end = dept_start + team_angle
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
                "view": "Sunburst",
            }
        )
        dept_start = team_end
    start_angle = end_angle

sunburst_df = pd.DataFrame(sunburst_records)
sunburst_df["startAngle_rad"] = np.radians(sunburst_df["startAngle"] - 90)
sunburst_df["endAngle_rad"] = np.radians(sunburst_df["endAngle"] - 90)

# Interactive toggle
view_dropdown = alt.binding_select(options=["Treemap", "Sunburst"], name="Select View: ")
view_selection = alt.selection_point(fields=["view"], bind=view_dropdown, value="Treemap")

color_scale = alt.Scale(domain=DEPT_DOMAIN, range=DEPT_COLORS)
color_legend = alt.Legend(title="Department", titleFontSize=20, labelFontSize=18, orient="right")

# Treemap - x/y domain [0,100] fills full canvas (1600x900)
treemap_rects = (
    alt.Chart(treemap_df)
    .mark_rect(stroke=PAGE_BG, strokeWidth=3)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color("department:N", scale=color_scale, legend=color_legend),
        opacity=alt.condition(view_selection, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("label:N", title="Team"),
            alt.Tooltip("value:Q", title="Headcount"),
            alt.Tooltip("department:N", title="Department"),
        ],
    )
    .add_params(view_selection)
)

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

# Sunburst - uses only polar channels (theta, radius), no x/y, so no scale conflict
sunburst_arcs = (
    alt.Chart(sunburst_df)
    .mark_arc(stroke=PAGE_BG, strokeWidth=2)
    .encode(
        theta=alt.Theta("endAngle_rad:Q", scale=alt.Scale(domain=[-np.pi, np.pi])),
        theta2="startAngle_rad:Q",
        radius=alt.Radius("outerRadius:Q", scale=alt.Scale(domain=[0, 120], range=[0, 420])),
        radius2="innerRadius:Q",
        color=alt.Color("department:N", scale=color_scale, legend=color_legend),
        opacity=alt.condition(view_selection, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("label:N", title="Name"),
            alt.Tooltip("value:Q", title="Headcount"),
            alt.Tooltip("department:N", title="Department"),
        ],
    )
)

# Combine - treemap x/y domain [0,100] governs the shared axes;
# sunburst polar channels don't conflict, so treemap fills the full canvas
combined_chart = (
    alt.layer(treemap_chart, sunburst_arcs)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "hierarchy-toggle-view · python · altair · anyplot.ai",
            fontSize=28,
            anchor="middle",
            offset=20,
            subtitle="Use dropdown to toggle between Treemap and Sunburst views",
            subtitleFontSize=18,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK, subtitleColor=INK_SOFT)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=20,
        labelFontSize=18,
        symbolSize=200,
    )
)

combined_chart.save(f"plot-{THEME}.png", scale_factor=3.0)
combined_chart.save(f"plot-{THEME}.html")
