""" pyplots.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import altair as alt
import pandas as pd


# Hierarchical data: Sales by Region -> Country -> City
data = [
    # Root level (regions)
    {"id": "americas", "name": "Americas", "value": 450, "parent": None},
    {"id": "europe", "name": "Europe", "value": 380, "parent": None},
    {"id": "asia", "name": "Asia Pacific", "value": 520, "parent": None},
    {"id": "africa", "name": "Africa", "value": 180, "parent": None},
    # Americas -> Countries
    {"id": "usa", "name": "USA", "value": 280, "parent": "americas"},
    {"id": "canada", "name": "Canada", "value": 95, "parent": "americas"},
    {"id": "brazil", "name": "Brazil", "value": 75, "parent": "americas"},
    # Europe -> Countries
    {"id": "uk", "name": "UK", "value": 120, "parent": "europe"},
    {"id": "germany", "name": "Germany", "value": 145, "parent": "europe"},
    {"id": "france", "name": "France", "value": 115, "parent": "europe"},
    # Asia Pacific -> Countries
    {"id": "china", "name": "China", "value": 220, "parent": "asia"},
    {"id": "japan", "name": "Japan", "value": 165, "parent": "asia"},
    {"id": "india", "name": "India", "value": 135, "parent": "asia"},
    # Africa -> Countries
    {"id": "nigeria", "name": "Nigeria", "value": 65, "parent": "africa"},
    {"id": "south_africa", "name": "South Africa", "value": 55, "parent": "africa"},
    {"id": "egypt", "name": "Egypt", "value": 60, "parent": "africa"},
    # USA -> Cities
    {"id": "nyc", "name": "New York", "value": 120, "parent": "usa"},
    {"id": "la", "name": "Los Angeles", "value": 90, "parent": "usa"},
    {"id": "chicago", "name": "Chicago", "value": 70, "parent": "usa"},
    # UK -> Cities
    {"id": "london", "name": "London", "value": 75, "parent": "uk"},
    {"id": "manchester", "name": "Manchester", "value": 25, "parent": "uk"},
    {"id": "birmingham", "name": "Birmingham", "value": 20, "parent": "uk"},
    # China -> Cities
    {"id": "shanghai", "name": "Shanghai", "value": 95, "parent": "china"},
    {"id": "beijing", "name": "Beijing", "value": 80, "parent": "china"},
    {"id": "shenzhen", "name": "Shenzhen", "value": 45, "parent": "china"},
]

df = pd.DataFrame(data)

# Create lookup for parent names (for breadcrumb)
id_to_name = dict(zip(df["id"], df["name"], strict=True))

# Add level information
df["level"] = df["parent"].apply(lambda x: 0 if pd.isna(x) else (1 if x in df[df["parent"].isna()]["id"].values else 2))

# Create selection parameter for drilldown
selection = alt.selection_point(fields=["id"], empty=False, name="drill")

# Filter to show root level initially (will change on selection in HTML)
root_df = df[df["parent"].isna()].copy()

# Python color palette
colors = ["#306998", "#FFD43B", "#4B8BBE", "#FFE873", "#646464"]

# Create the bar chart
bars = (
    alt.Chart(root_df)
    .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, cursor="pointer")
    .encode(
        x=alt.X(
            "name:N",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0),
            title="Category",
            sort=alt.EncodingSortField(field="value", order="descending"),
        ),
        y=alt.Y(
            "value:Q",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.3),
            title="Sales (millions USD)",
        ),
        color=alt.Color("name:N", scale=alt.Scale(range=colors), legend=None),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.7)),
        tooltip=[alt.Tooltip("name:N", title="Category"), alt.Tooltip("value:Q", title="Sales ($M)", format=",.0f")],
    )
    .add_params(selection)
)

# Add value labels on top of bars
text = (
    alt.Chart(root_df)
    .mark_text(dy=-15, fontSize=20, fontWeight="bold", color="#306998")
    .encode(
        x=alt.X("name:N", sort=alt.EncodingSortField(field="value", order="descending")),
        y=alt.Y("value:Q"),
        text=alt.Text("value:Q", format="$,.0f"),
    )
)

# Add clickable indicator text
click_hint = (
    alt.Chart(root_df)
    .mark_text(dy=25, fontSize=14, color="#666666", fontStyle="italic")
    .encode(
        x=alt.X("name:N", sort=alt.EncodingSortField(field="value", order="descending")),
        y=alt.Y("value:Q"),
        text=alt.value("Click to drill down"),
    )
)

# Breadcrumb as subtitle showing navigation path
breadcrumb_text = "Sales by Region (Click a bar to drill down)"

# Combine layers
chart = (
    (bars + text + click_hint)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            text="bar-drilldown \u00b7 altair \u00b7 pyplots.ai",
            subtitle=breadcrumb_text,
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
            anchor="middle",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_view(strokeWidth=0)
)

# Save as PNG (static view shows root level)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML with drilldown functionality
# The HTML version includes JavaScript for full interactivity
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>bar-drilldown - altair - pyplots.ai</title>
    <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            background: #fafafa;
        }}
        #breadcrumb {{
            font-size: 18px;
            margin-bottom: 20px;
            padding: 12px 24px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        #breadcrumb span {{
            color: #306998;
            cursor: pointer;
        }}
        #breadcrumb span:hover {{
            text-decoration: underline;
        }}
        #breadcrumb .separator {{
            color: #999;
            margin: 0 8px;
        }}
        #breadcrumb .current {{
            color: #333;
            font-weight: bold;
            cursor: default;
        }}
        #vis {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div id="breadcrumb"><span class="current">All Regions</span></div>
    <div id="vis"></div>
    <script>
        const fullData = {df.to_json(orient="records")};
        const idToName = {dict(zip(df["id"], df["name"], strict=True))};

        let currentParent = null;
        let breadcrumbPath = [];

        function getChildren(parentId) {{
            if (parentId === null) {{
                return fullData.filter(d => d.parent === null);
            }}
            return fullData.filter(d => d.parent === parentId);
        }}

        function updateBreadcrumb() {{
            const bc = document.getElementById('breadcrumb');
            let html = '<span onclick="drillTo(null)">All Regions</span>';

            for (let i = 0; i < breadcrumbPath.length; i++) {{
                const id = breadcrumbPath[i];
                const name = idToName[id];
                html += '<span class="separator">&gt;</span>';
                if (i === breadcrumbPath.length - 1) {{
                    html += `<span class="current">${{name}}</span>`;
                }} else {{
                    html += `<span onclick="drillTo('${{id}}', ${{i}})">${{name}}</span>`;
                }}
            }}
            bc.innerHTML = html;
        }}

        function drillTo(id, pathIndex) {{
            if (pathIndex !== undefined) {{
                breadcrumbPath = breadcrumbPath.slice(0, pathIndex + 1);
            }} else if (id === null) {{
                breadcrumbPath = [];
            }}
            currentParent = id;
            updateBreadcrumb();
            renderChart();
        }}

        function drillDown(id) {{
            const children = getChildren(id);
            if (children.length > 0) {{
                breadcrumbPath.push(id);
                currentParent = id;
                updateBreadcrumb();
                renderChart();
            }}
        }}

        function renderChart() {{
            const data = getChildren(currentParent);
            const hasChildren = data.some(d => getChildren(d.id).length > 0);

            const spec = {{
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "width": 1200,
                "height": 600,
                "title": {{
                    "text": "bar-drilldown \\u00b7 altair \\u00b7 pyplots.ai",
                    "fontSize": 24,
                    "subtitle": hasChildren ? "Click a bar to drill down" : "Lowest level reached",
                    "subtitleFontSize": 14,
                    "subtitleColor": "#666"
                }},
                "data": {{ "values": data }},
                "mark": {{
                    "type": "bar",
                    "cornerRadiusTopLeft": 8,
                    "cornerRadiusTopRight": 8,
                    "cursor": hasChildren ? "pointer" : "default"
                }},
                "encoding": {{
                    "x": {{
                        "field": "name",
                        "type": "nominal",
                        "axis": {{ "labelFontSize": 14, "titleFontSize": 16, "labelAngle": 0 }},
                        "title": "Category",
                        "sort": {{ "field": "value", "order": "descending" }}
                    }},
                    "y": {{
                        "field": "value",
                        "type": "quantitative",
                        "axis": {{ "labelFontSize": 14, "titleFontSize": 16, "grid": true, "gridOpacity": 0.3 }},
                        "title": "Sales (millions USD)"
                    }},
                    "color": {{
                        "field": "name",
                        "type": "nominal",
                        "scale": {{ "range": ["#306998", "#FFD43B", "#4B8BBE", "#FFE873", "#646464"] }},
                        "legend": null
                    }},
                    "tooltip": [
                        {{ "field": "name", "title": "Category" }},
                        {{ "field": "value", "title": "Sales ($M)", "format": ",.0f" }}
                    ]
                }},
                "config": {{
                    "view": {{ "strokeWidth": 0 }}
                }}
            }};

            vegaEmbed('#vis', spec, {{ actions: false }}).then(result => {{
                if (hasChildren) {{
                    result.view.addEventListener('click', (event, item) => {{
                        if (item && item.datum && item.datum.id) {{
                            drillDown(item.datum.id);
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

with open("plot.html", "w") as f:
    f.write(html_content)
