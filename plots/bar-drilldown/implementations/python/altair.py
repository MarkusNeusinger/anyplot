"""anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: altair 6.0.0 | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import json
import os

import altair as alt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Hierarchical data: Sales by Region -> Country -> City
# Children always sum exactly to their parent value
data = [
    # Root level
    {"id": "asia", "name": "Asia Pacific", "value": 520, "parent": None},
    {"id": "americas", "name": "Americas", "value": 450, "parent": None},
    {"id": "europe", "name": "Europe", "value": 380, "parent": None},
    {"id": "africa", "name": "Africa", "value": 180, "parent": None},
    # Americas: 280 + 95 + 75 = 450
    {"id": "usa", "name": "USA", "value": 280, "parent": "americas"},
    {"id": "canada", "name": "Canada", "value": 95, "parent": "americas"},
    {"id": "brazil", "name": "Brazil", "value": 75, "parent": "americas"},
    # Europe: 145 + 120 + 115 = 380
    {"id": "germany", "name": "Germany", "value": 145, "parent": "europe"},
    {"id": "uk", "name": "UK", "value": 120, "parent": "europe"},
    {"id": "france", "name": "France", "value": 115, "parent": "europe"},
    # Asia Pacific: 220 + 165 + 135 = 520
    {"id": "china", "name": "China", "value": 220, "parent": "asia"},
    {"id": "japan", "name": "Japan", "value": 165, "parent": "asia"},
    {"id": "india", "name": "India", "value": 135, "parent": "asia"},
    # Africa: 65 + 60 + 55 = 180
    {"id": "nigeria", "name": "Nigeria", "value": 65, "parent": "africa"},
    {"id": "egypt", "name": "Egypt", "value": 60, "parent": "africa"},
    {"id": "south_africa", "name": "South Africa", "value": 55, "parent": "africa"},
    # USA: 120 + 90 + 70 = 280
    {"id": "nyc", "name": "New York", "value": 120, "parent": "usa"},
    {"id": "la", "name": "Los Angeles", "value": 90, "parent": "usa"},
    {"id": "chicago", "name": "Chicago", "value": 70, "parent": "usa"},
    # UK: 75 + 25 + 20 = 120
    {"id": "london", "name": "London", "value": 75, "parent": "uk"},
    {"id": "manchester", "name": "Manchester", "value": 25, "parent": "uk"},
    {"id": "birmingham", "name": "Birmingham", "value": 20, "parent": "uk"},
    # China: 95 + 80 + 45 = 220
    {"id": "shanghai", "name": "Shanghai", "value": 95, "parent": "china"},
    {"id": "beijing", "name": "Beijing", "value": 80, "parent": "china"},
    {"id": "shenzhen", "name": "Shenzhen", "value": 45, "parent": "china"},
]

df = pd.DataFrame(data)

# Root-level data sorted by value descending for consistent color mapping
root_df = df[df["parent"].isna()].copy()
root_order = root_df.sort_values("value", ascending=False)["name"].tolist()
region_colors = OKABE_ITO[: len(root_order)]

TITLE = "bar-drilldown · python · altair · anyplot.ai"

# Bars layer
bars = (
    alt.Chart(root_df)
    .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, cursor="pointer")
    .encode(
        x=alt.X("name:N", title="Region", sort=root_order),
        y=alt.Y("value:Q", title="Sales (millions USD)"),
        color=alt.Color("name:N", scale=alt.Scale(domain=root_order, range=region_colors), legend=None),
        tooltip=[alt.Tooltip("name:N", title="Region"), alt.Tooltip("value:Q", title="Sales ($M)", format=",.0f")],
    )
)

# Value labels above bars — no in-bar text noise
text_labels = (
    alt.Chart(root_df)
    .mark_text(dy=-10, fontSize=12, fontWeight="bold")
    .encode(
        x=alt.X("name:N", sort=root_order),
        y=alt.Y("value:Q"),
        text=alt.Text("value:Q", format="$,.0f"),
        color=alt.value(INK),
    )
)

chart = (
    (bars + text_labels)
    .properties(
        width=800,
        height=450,
        background=PAGE_BG,
        title=alt.Title(
            text=TITLE,
            subtitle="Sales by Region — open the HTML version to drill down interactively",
            fontSize=16,
            subtitleFontSize=10,
            subtitleColor=INK_SOFT,
            anchor="middle",
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
        labelAngle=0,
    )
    .configure_title(color=INK)
)

# Save static PNG (3200×1800 px)
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Interactive HTML with full drilldown functionality
data_json = df.to_json(orient="records")
id_to_name_json = json.dumps(df.set_index("id")["name"].to_dict())
okabe_ito_json = json.dumps(OKABE_ITO)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>bar-drilldown — altair — anyplot.ai</title>
    <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 24px;
            background: {PAGE_BG};
            color: {INK};
            margin: 0;
        }}
        #breadcrumb {{
            font-size: 15px;
            margin-bottom: 16px;
            padding: 10px 20px;
            background: {ELEVATED_BG};
            border-radius: 8px;
            border: 1px solid {INK_SOFT}44;
        }}
        #breadcrumb .link {{
            color: #009E73;
            cursor: pointer;
        }}
        #breadcrumb .link:hover {{ text-decoration: underline; }}
        #breadcrumb .sep {{ color: {INK_SOFT}; margin: 0 8px; }}
        #breadcrumb .current {{ color: {INK}; font-weight: 600; }}
        #vis {{ border-radius: 12px; overflow: hidden; }}
    </style>
</head>
<body>
    <div id="breadcrumb"><span class="current">All Regions</span></div>
    <div id="vis"></div>
    <script>
        const fullData = {data_json};
        const idToName = {id_to_name_json};
        const OKABE_ITO = {okabe_ito_json};
        const PAGE_BG = "{PAGE_BG}";
        const ELEVATED_BG = "{ELEVATED_BG}";
        const INK = "{INK}";
        const INK_SOFT = "{INK_SOFT}";

        let currentParent = null;
        let breadcrumbPath = [];

        function getChildren(parentId) {{
            return fullData.filter(d => parentId === null ? d.parent === null : d.parent === parentId);
        }}

        function updateBreadcrumb() {{
            const bc = document.getElementById('breadcrumb');
            let html = '<span class="link" onclick="drillTo(null, -1)">All Regions</span>';
            for (let i = 0; i < breadcrumbPath.length; i++) {{
                const id = breadcrumbPath[i];
                html += '<span class="sep">›</span>';
                if (i === breadcrumbPath.length - 1) {{
                    html += `<span class="current">${{idToName[id]}}</span>`;
                }} else {{
                    html += `<span class="link" onclick="drillTo('${{id}}', ${{i}})">${{idToName[id]}}</span>`;
                }}
            }}
            bc.innerHTML = html;
        }}

        function drillTo(id, pathIndex) {{
            if (pathIndex === -1) {{
                breadcrumbPath = [];
                currentParent = null;
            }} else {{
                breadcrumbPath = breadcrumbPath.slice(0, pathIndex + 1);
                currentParent = id;
            }}
            updateBreadcrumb();
            renderChart();
        }}

        function renderChart() {{
            const items = getChildren(currentParent);
            const sorted = [...items].sort((a, b) => b.value - a.value);
            const names = sorted.map(d => d.name);
            const colors = names.map((_, i) => OKABE_ITO[i % OKABE_ITO.length]);
            const hasChildren = items.some(d => getChildren(d.id).length > 0);

            const spec = {{
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "width": 720,
                "height": 420,
                "background": PAGE_BG,
                "title": {{
                    "text": "bar-drilldown · python · altair · anyplot.ai",
                    "subtitle": hasChildren ? "Click a bar to drill down" : "No further levels",
                    "fontSize": 18,
                    "subtitleFontSize": 12,
                    "color": INK,
                    "subtitleColor": INK_SOFT,
                    "anchor": "middle"
                }},
                "data": {{ "values": items }},
                "layer": [
                    {{
                        "mark": {{
                            "type": "bar",
                            "cornerRadiusTopLeft": 8,
                            "cornerRadiusTopRight": 8,
                            "cursor": hasChildren ? "pointer" : "default"
                        }},
                        "encoding": {{
                            "x": {{
                                "field": "name", "type": "nominal",
                                "title": "Category",
                                "sort": names,
                                "axis": {{
                                    "labelFontSize": 13, "titleFontSize": 14,
                                    "labelAngle": 0,
                                    "labelColor": INK_SOFT, "titleColor": INK,
                                    "domainColor": INK_SOFT, "tickColor": INK_SOFT
                                }}
                            }},
                            "y": {{
                                "field": "value", "type": "quantitative",
                                "title": "Sales (millions USD)",
                                "axis": {{
                                    "labelFontSize": 13, "titleFontSize": 14,
                                    "gridOpacity": 0.10,
                                    "gridColor": INK,
                                    "labelColor": INK_SOFT, "titleColor": INK,
                                    "domainColor": INK_SOFT, "tickColor": INK_SOFT
                                }}
                            }},
                            "color": {{
                                "field": "name", "type": "nominal",
                                "scale": {{ "domain": names, "range": colors }},
                                "legend": null
                            }},
                            "tooltip": [
                                {{ "field": "name", "title": "Category" }},
                                {{ "field": "value", "title": "Sales ($M)", "format": ",.0f" }}
                            ]
                        }}
                    }},
                    {{
                        "mark": {{
                            "type": "text",
                            "dy": -12, "fontSize": 13,
                            "fontWeight": "bold",
                            "color": INK
                        }},
                        "encoding": {{
                            "x": {{ "field": "name", "type": "nominal", "sort": names }},
                            "y": {{ "field": "value", "type": "quantitative" }},
                            "text": {{ "field": "value", "type": "quantitative", "format": "$,.0f" }}
                        }}
                    }}
                ],
                "config": {{
                    "view": {{ "strokeWidth": 0, "fill": PAGE_BG }}
                }}
            }};

            vegaEmbed('#vis', spec, {{ actions: false }}).then(result => {{
                if (hasChildren) {{
                    result.view.addEventListener('click', (event, item) => {{
                        if (item && item.datum && item.datum.id) {{
                            breadcrumbPath.push(item.datum.id);
                            currentParent = item.datum.id;
                            updateBreadcrumb();
                            renderChart();
                        }}
                    }});
                }}
            }});
        }}

        renderChart();
    </script>
</body>
</html>
"""

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
