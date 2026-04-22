"""pyplots.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: altair 6.0.0 | Python 3.13.11
Quality: 84/100 | Created: 2025-12-31
"""

import altair as alt
import pandas as pd


# Hierarchical data: Company budget breakdown
# Structure: id, name, value, parent (following spec's data format)
hierarchy_data = [
    # Root level (shown by default)
    {"id": "root", "name": "All Departments", "value": 3200000, "parent": None, "level": 0},
    # Level 1: Departments (children of root)
    {"id": "engineering", "name": "Engineering", "value": 1755000, "parent": "root", "level": 1},
    {"id": "marketing", "name": "Marketing", "value": 740000, "parent": "root", "level": 1},
    {"id": "operations", "name": "Operations", "value": 485000, "parent": "root", "level": 1},
    {"id": "hr", "name": "HR", "value": 220000, "parent": "root", "level": 1},
    # Level 2: Engineering Teams
    {"id": "eng_frontend", "name": "Frontend", "value": 510000, "parent": "engineering", "level": 2},
    {"id": "eng_backend", "name": "Backend", "value": 745000, "parent": "engineering", "level": 2},
    {"id": "eng_devops", "name": "DevOps", "value": 500000, "parent": "engineering", "level": 2},
    # Level 2: Marketing Teams
    {"id": "mkt_digital", "name": "Digital", "value": 295000, "parent": "marketing", "level": 2},
    {"id": "mkt_content", "name": "Content", "value": 245000, "parent": "marketing", "level": 2},
    {"id": "mkt_events", "name": "Events", "value": 200000, "parent": "marketing", "level": 2},
    # Level 2: Operations Teams
    {"id": "ops_facilities", "name": "Facilities", "value": 325000, "parent": "operations", "level": 2},
    {"id": "ops_it", "name": "IT Support", "value": 160000, "parent": "operations", "level": 2},
    # Level 2: HR Teams
    {"id": "hr_recruit", "name": "Recruiting", "value": 120000, "parent": "hr", "level": 2},
    {"id": "hr_training", "name": "Training", "value": 100000, "parent": "hr", "level": 2},
]

df = pd.DataFrame(hierarchy_data)

# Calculate percentages within each parent group
df["parent_total"] = df.groupby("parent")["value"].transform("sum")
df["percentage"] = (df["value"] / df["parent_total"] * 100).fillna(0)

# Format labels
df["display_label"] = df.apply(
    lambda r: f"{r['name']}\n${r['value'] / 1e6:.2f}M ({r['percentage']:.1f}%)"
    if r["value"] >= 1e6
    else f"{r['name']}\n${r['value'] / 1e3:.0f}K ({r['percentage']:.1f}%)",
    axis=1,
)

# Color scheme - consistent colors for departments and their children
color_map = {
    # Root level
    "All Departments": "#4a4a4a",
    # Departments
    "Engineering": "#1f77b4",
    "Marketing": "#ff7f0e",
    "Operations": "#2ca02c",
    "HR": "#9467bd",
    # Engineering teams - blue shades
    "Frontend": "#6baed6",
    "Backend": "#2171b5",
    "DevOps": "#08519c",
    # Marketing teams - orange shades
    "Digital": "#fdae6b",
    "Content": "#fd8d3c",
    "Events": "#d94701",
    # Operations teams - green shades
    "Facilities": "#74c476",
    "IT Support": "#238b45",
    # HR teams - purple shades
    "Recruiting": "#bcbddc",
    "Training": "#807dba",
}

df["color"] = df["name"].map(color_map)

# Create separate dataframes for each view level
root_view = df[df["parent"] == "root"].copy()
eng_view = df[df["parent"] == "engineering"].copy()
mkt_view = df[df["parent"] == "marketing"].copy()
ops_view = df[df["parent"] == "operations"].copy()
hr_view = df[df["parent"] == "hr"].copy()

# Selection parameter for drilldown navigation (single-select click)
selection = alt.selection_point(fields=["id"], empty=True, name="drill")

# Main pie (Level 1 - Departments) - visible by default
main_pie = (
    alt.Chart(root_view)
    .mark_arc(innerRadius=180, outerRadius=380, stroke="#ffffff", strokeWidth=6, cursor="pointer")
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color(
            "name:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None
        ),
        order=alt.Order("value:Q", sort="descending"),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.85)),
        tooltip=[
            alt.Tooltip("name:N", title="Department"),
            alt.Tooltip("value:Q", title="Budget ($)", format=",.0f"),
            alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
        ],
    )
    .add_params(selection)
)

# Main pie labels
main_labels = (
    alt.Chart(root_view)
    .mark_text(radius=460, fontSize=22, fontWeight="bold", align="center", baseline="middle", lineBreak="\n")
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        order=alt.Order("value:Q", sort="descending"),
        text=alt.Text("display_label:N"),
        color=alt.value("#333333"),
    )
)

# Center text for main view
main_center_df = pd.DataFrame([{"line1": "Total Budget", "line2": "$3.20M", "line3": "Click slice to drill down"}])
main_center = alt.layer(
    alt.Chart(main_center_df).mark_text(fontSize=24, fontWeight="bold", color="#333333", dy=-30).encode(text="line1:N"),
    alt.Chart(main_center_df).mark_text(fontSize=36, fontWeight="bold", color="#1f77b4", dy=10).encode(text="line2:N"),
    alt.Chart(main_center_df).mark_text(fontSize=16, color="#888888", dy=50).encode(text="line3:N"),
)

# Engineering drilldown
eng_pie = (
    alt.Chart(eng_view)
    .mark_arc(innerRadius=180, outerRadius=380, stroke="#ffffff", strokeWidth=6)
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color(
            "name:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None
        ),
        order=alt.Order("value:Q", sort="descending"),
        tooltip=[
            alt.Tooltip("name:N", title="Team"),
            alt.Tooltip("value:Q", title="Budget ($)", format=",.0f"),
            alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
        ],
    )
    .transform_filter(alt.datum.parent == "engineering")
    .transform_filter(selection)
)

eng_labels = (
    alt.Chart(eng_view)
    .mark_text(radius=460, fontSize=20, fontWeight="bold", align="center", baseline="middle", lineBreak="\n")
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        order=alt.Order("value:Q", sort="descending"),
        text=alt.Text("display_label:N"),
        color=alt.value("#333333"),
    )
    .transform_filter(alt.datum.parent == "engineering")
    .transform_filter(selection)
)

eng_center_df = pd.DataFrame([{"line1": "⬅ Engineering", "line2": "$1.76M", "line3": "Click outside to go back"}])
eng_center = (
    alt.layer(
        alt.Chart(eng_center_df)
        .mark_text(fontSize=24, fontWeight="bold", color="#1f77b4", dy=-30)
        .encode(text="line1:N"),
        alt.Chart(eng_center_df)
        .mark_text(fontSize=36, fontWeight="bold", color="#1f77b4", dy=10)
        .encode(text="line2:N"),
        alt.Chart(eng_center_df).mark_text(fontSize=16, color="#888888", dy=50).encode(text="line3:N"),
    )
    .transform_filter(selection)
    .transform_calculate(parent="'engineering'")
    .transform_filter("datum.id == 'engineering'")
)

# Marketing drilldown
mkt_pie = (
    alt.Chart(mkt_view)
    .mark_arc(innerRadius=180, outerRadius=380, stroke="#ffffff", strokeWidth=6)
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color(
            "name:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None
        ),
        order=alt.Order("value:Q", sort="descending"),
        tooltip=[
            alt.Tooltip("name:N", title="Team"),
            alt.Tooltip("value:Q", title="Budget ($)", format=",.0f"),
            alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
        ],
    )
    .transform_filter(alt.datum.parent == "marketing")
    .transform_filter(selection)
)

mkt_labels = (
    alt.Chart(mkt_view)
    .mark_text(radius=460, fontSize=20, fontWeight="bold", align="center", baseline="middle", lineBreak="\n")
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        order=alt.Order("value:Q", sort="descending"),
        text=alt.Text("display_label:N"),
        color=alt.value("#333333"),
    )
    .transform_filter(alt.datum.parent == "marketing")
    .transform_filter(selection)
)

mkt_center_df = pd.DataFrame([{"line1": "⬅ Marketing", "line2": "$740K", "line3": "Click outside to go back"}])
mkt_center = (
    alt.layer(
        alt.Chart(mkt_center_df)
        .mark_text(fontSize=24, fontWeight="bold", color="#ff7f0e", dy=-30)
        .encode(text="line1:N"),
        alt.Chart(mkt_center_df)
        .mark_text(fontSize=36, fontWeight="bold", color="#ff7f0e", dy=10)
        .encode(text="line2:N"),
        alt.Chart(mkt_center_df).mark_text(fontSize=16, color="#888888", dy=50).encode(text="line3:N"),
    )
    .transform_filter(selection)
    .transform_calculate(parent="'marketing'")
    .transform_filter("datum.id == 'marketing'")
)

# Operations drilldown
ops_pie = (
    alt.Chart(ops_view)
    .mark_arc(innerRadius=180, outerRadius=380, stroke="#ffffff", strokeWidth=6)
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color(
            "name:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None
        ),
        order=alt.Order("value:Q", sort="descending"),
        tooltip=[
            alt.Tooltip("name:N", title="Team"),
            alt.Tooltip("value:Q", title="Budget ($)", format=",.0f"),
            alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
        ],
    )
    .transform_filter(alt.datum.parent == "operations")
    .transform_filter(selection)
)

ops_labels = (
    alt.Chart(ops_view)
    .mark_text(radius=460, fontSize=20, fontWeight="bold", align="center", baseline="middle", lineBreak="\n")
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        order=alt.Order("value:Q", sort="descending"),
        text=alt.Text("display_label:N"),
        color=alt.value("#333333"),
    )
    .transform_filter(alt.datum.parent == "operations")
    .transform_filter(selection)
)

ops_center_df = pd.DataFrame([{"line1": "⬅ Operations", "line2": "$485K", "line3": "Click outside to go back"}])
ops_center = (
    alt.layer(
        alt.Chart(ops_center_df)
        .mark_text(fontSize=24, fontWeight="bold", color="#2ca02c", dy=-30)
        .encode(text="line1:N"),
        alt.Chart(ops_center_df)
        .mark_text(fontSize=36, fontWeight="bold", color="#2ca02c", dy=10)
        .encode(text="line2:N"),
        alt.Chart(ops_center_df).mark_text(fontSize=16, color="#888888", dy=50).encode(text="line3:N"),
    )
    .transform_filter(selection)
    .transform_calculate(parent="'operations'")
    .transform_filter("datum.id == 'operations'")
)

# HR drilldown
hr_pie = (
    alt.Chart(hr_view)
    .mark_arc(innerRadius=180, outerRadius=380, stroke="#ffffff", strokeWidth=6)
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color(
            "name:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None
        ),
        order=alt.Order("value:Q", sort="descending"),
        tooltip=[
            alt.Tooltip("name:N", title="Team"),
            alt.Tooltip("value:Q", title="Budget ($)", format=",.0f"),
            alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
        ],
    )
    .transform_filter(alt.datum.parent == "hr")
    .transform_filter(selection)
)

hr_labels = (
    alt.Chart(hr_view)
    .mark_text(radius=460, fontSize=20, fontWeight="bold", align="center", baseline="middle", lineBreak="\n")
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        order=alt.Order("value:Q", sort="descending"),
        text=alt.Text("display_label:N"),
        color=alt.value("#333333"),
    )
    .transform_filter(alt.datum.parent == "hr")
    .transform_filter(selection)
)

hr_center_df = pd.DataFrame([{"line1": "⬅ HR", "line2": "$220K", "line3": "Click outside to go back"}])
hr_center = (
    alt.layer(
        alt.Chart(hr_center_df)
        .mark_text(fontSize=24, fontWeight="bold", color="#9467bd", dy=-30)
        .encode(text="line1:N"),
        alt.Chart(hr_center_df)
        .mark_text(fontSize=36, fontWeight="bold", color="#9467bd", dy=10)
        .encode(text="line2:N"),
        alt.Chart(hr_center_df).mark_text(fontSize=16, color="#888888", dy=50).encode(text="line3:N"),
    )
    .transform_filter(selection)
    .transform_calculate(parent="'hr'")
    .transform_filter("datum.id == 'hr'")
)

# Breadcrumb - dynamically updates based on selection
breadcrumb_data = pd.DataFrame(
    [
        {"id": "engineering", "text": "📊 All Departments  ›  Engineering  ›  Teams"},
        {"id": "marketing", "text": "📊 All Departments  ›  Marketing  ›  Teams"},
        {"id": "operations", "text": "📊 All Departments  ›  Operations  ›  Teams"},
        {"id": "hr", "text": "📊 All Departments  ›  HR  ›  Teams"},
    ]
)

breadcrumb_default = pd.DataFrame([{"text": "📊 All Departments  ›  Click any slice to explore"}])
breadcrumb_base = (
    alt.Chart(breadcrumb_default)
    .mark_text(fontSize=22, align="center", fontWeight="bold", color="#555555")
    .encode(text="text:N")
    .properties(width=1400, height=50)
)

breadcrumb_selected = (
    alt.Chart(breadcrumb_data)
    .mark_text(fontSize=22, align="center", fontWeight="bold", color="#555555")
    .encode(text="text:N")
    .properties(width=1400, height=50)
    .transform_filter(selection)
)

breadcrumb = alt.layer(breadcrumb_base, breadcrumb_selected)

# Layer all pie charts (only one visible at a time based on selection)
pie_chart = alt.layer(
    main_pie,
    main_labels,
    main_center,
    eng_pie,
    eng_labels,
    eng_center,
    mkt_pie,
    mkt_labels,
    mkt_center,
    ops_pie,
    ops_labels,
    ops_center,
    hr_pie,
    hr_labels,
    hr_center,
).properties(width=1000, height=1000)

# Title
title_text = alt.TitleParams(
    text="Company Budget Breakdown with Click-to-Drill Navigation",
    subtitle="pie-drilldown · altair · pyplots.ai",
    fontSize=36,
    subtitleFontSize=22,
    subtitleColor="#666666",
    anchor="middle",
    offset=20,
)

# Instruction text
instruction_df = pd.DataFrame(
    [
        {
            "text": "Interactive: Click department slices to drill down | Click outside pie to navigate back | Hover for details"
        }
    ]
)
instruction = (
    alt.Chart(instruction_df)
    .mark_text(fontSize=18, color="#888888")
    .encode(text="text:N")
    .properties(width=1400, height=40)
)

# Final composition
final_chart = (
    alt.vconcat(breadcrumb, pie_chart, instruction, spacing=15)
    .properties(title=title_text)
    .configure_view(strokeWidth=0)
    .configure_title(fontSize=36, subtitleFontSize=22)
)

# Save outputs (target: 4800 x 2700 at scale 3 = 1600 x 900 base)
final_chart.save("plot.png", scale_factor=3.0)
final_chart.save("plot.html")
