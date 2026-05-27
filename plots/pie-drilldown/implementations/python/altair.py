""" anyplot.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: altair 6.1.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-15
"""

import os
import sys

import pandas as pd


# Set up path to load altair without shadowing
sys.path.insert(0, "/home/runner/work/anyplot/anyplot/.venv/lib/python3.13/site-packages")
try:
    import altair as alt
finally:
    sys.path.pop(0)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

hierarchy_data = [
    {"id": "root", "name": "All Departments", "value": 3200000, "parent": None},
    {"id": "engineering", "name": "Engineering", "value": 1755000, "parent": "root"},
    {"id": "marketing", "name": "Marketing", "value": 740000, "parent": "root"},
    {"id": "operations", "name": "Operations", "value": 485000, "parent": "root"},
    {"id": "hr", "name": "HR", "value": 220000, "parent": "root"},
    {"id": "eng_frontend", "name": "Frontend", "value": 510000, "parent": "engineering"},
    {"id": "eng_backend", "name": "Backend", "value": 745000, "parent": "engineering"},
    {"id": "eng_devops", "name": "DevOps", "value": 500000, "parent": "engineering"},
    {"id": "mkt_digital", "name": "Digital", "value": 295000, "parent": "marketing"},
    {"id": "mkt_content", "name": "Content", "value": 245000, "parent": "marketing"},
    {"id": "mkt_events", "name": "Events", "value": 200000, "parent": "marketing"},
    {"id": "ops_facilities", "name": "Facilities", "value": 325000, "parent": "operations"},
    {"id": "ops_it", "name": "IT Support", "value": 160000, "parent": "operations"},
    {"id": "hr_recruit", "name": "Recruiting", "value": 120000, "parent": "hr"},
    {"id": "hr_training", "name": "Training", "value": 100000, "parent": "hr"},
]

df = pd.DataFrame(hierarchy_data)

color_map = {
    "All Departments": INK,
    "Engineering": IMPRINT[0],
    "Marketing": IMPRINT[1],
    "Operations": IMPRINT[2],
    "HR": IMPRINT[3],
    "Frontend": "#2ABCCD",
    "Backend": IMPRINT[0],
    "DevOps": "#4467A3",
    "Digital": "#FFC863",
    "Content": IMPRINT[1],
    "Events": "#C475FD",
    "Facilities": "#72C472",
    "IT Support": IMPRINT[2],
    "Recruiting": "#BC8FBC",
    "Training": "#BD8233",
}

df["color"] = df["name"].map(color_map)
df["parent_total"] = df.groupby("parent")["value"].transform("sum")
df["percentage"] = (df["value"] / df["parent_total"] * 100).fillna(0)
df["pct_label"] = df["percentage"].apply(lambda x: f"{x:.0f}%")
df["display_label"] = df["name"] + "\n" + df["pct_label"]

selection = alt.selection_point(fields=["id"], empty=True, name="drill")

breadcrumb_df = pd.DataFrame([{"breadcrumb": "All Departments"}])
breadcrumb = (
    alt.Chart(breadcrumb_df)
    .mark_text(fontSize=16, align="center", color=INK_SOFT)
    .encode(text="breadcrumb:N")
    .properties(width=600, height=30)
)

root_view = df[df["parent"] == "root"]
main_pie = (
    alt.Chart(root_view)
    .mark_arc(innerRadius=160, outerRadius=280, stroke=PAGE_BG, strokeWidth=4, cursor="pointer")
    .encode(
        theta=alt.Theta("value:Q", stack=True),
        color=alt.Color(
            "name:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None
        ),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.85)),
        tooltip=[
            alt.Tooltip("name:N", title="Department"),
            alt.Tooltip("value:Q", title="Budget ($)", format=",.0f"),
            alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
        ],
    )
    .add_params(selection)
)

main_labels = (
    alt.Chart(root_view)
    .mark_text(radius=180, fontSize=13, align="center", baseline="middle")
    .encode(theta=alt.Theta("value:Q", stack=True), text=alt.Text("display_label:N"), color=alt.value(INK))
)

main_center_df = pd.DataFrame([{"line1": "All Departments", "line2": "$3.20B"}])
main_center = alt.layer(
    alt.Chart(main_center_df).mark_text(fontSize=22, fontWeight="bold", dy=-20, color=INK).encode(text="line1:N"),
    alt.Chart(main_center_df)
    .mark_text(fontSize=32, fontWeight="bold", dy=15, color=IMPRINT[0])
    .encode(text="line2:N"),
)

main_pie_chart = alt.layer(main_pie, main_labels, main_center).properties(width=600, height=600)

drilldown_views = []
dept_configs = [("engineering", "Engineering"), ("marketing", "Marketing"), ("operations", "Operations"), ("hr", "HR")]
for parent_id, parent_name in dept_configs:
    dept_view = df[df["parent"] == parent_id]
    if len(dept_view) == 0:
        continue

    dept_total = df[df["id"] == parent_id]["value"].values[0]

    dept_pie = (
        alt.Chart(dept_view)
        .mark_arc(innerRadius=160, outerRadius=280, stroke=PAGE_BG, strokeWidth=4)
        .encode(
            theta=alt.Theta("value:Q", stack=True),
            color=alt.Color(
                "name:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None
            ),
            tooltip=[
                alt.Tooltip("name:N", title="Team"),
                alt.Tooltip("value:Q", title="Budget ($)", format=",.0f"),
                alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
            ],
        )
        .transform_filter(alt.datum.parent == parent_id)
    )

    dept_labels = (
        alt.Chart(dept_view)
        .mark_text(radius=180, fontSize=12, align="center", baseline="middle", color=INK)
        .encode(theta=alt.Theta("value:Q", stack=True), text=alt.Text("display_label:N"))
        .transform_filter(alt.datum.parent == parent_id)
    )

    dept_center_df = pd.DataFrame([{"line1": f"← {parent_name}", "line2": f"${dept_total / 1e6:.2f}B"}])
    dept_center = alt.layer(
        alt.Chart(dept_center_df)
        .mark_text(fontSize=20, fontWeight="bold", dy=-15, color=INK_SOFT)
        .encode(text="line1:N"),
        alt.Chart(dept_center_df)
        .mark_text(fontSize=28, fontWeight="bold", dy=15, color=color_map[parent_name])
        .encode(text="line2:N"),
    )

    dept_combined = (
        alt.layer(dept_pie, dept_labels, dept_center)
        .transform_filter(selection)
        .transform_filter(f"datum.id == '{parent_id}'")
        .properties(width=600, height=600)
    )
    drilldown_views.append(dept_combined)

final_layer = alt.layer(main_pie_chart, *drilldown_views)

final_chart = (
    alt.vconcat(breadcrumb, final_layer, spacing=20)
    .properties(
        title=alt.TitleParams(text="pie-drilldown · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

final_chart.save(f"plot-{THEME}.png", scale_factor=3.0)
final_chart.save(f"plot-{THEME}.html")
