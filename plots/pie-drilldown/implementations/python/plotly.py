""" anyplot.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: plotly 6.7.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-15
"""

import json
import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series must be #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Hierarchical data for sales regions
hierarchy = {
    "All": {"children": ["North America", "Europe", "Asia Pacific", "Latin America"], "parent": None},
    "North America": {"children": ["USA", "Canada", "Mexico"], "parent": "All"},
    "Europe": {"children": ["UK", "Germany", "France"], "parent": "All"},
    "Asia Pacific": {"children": ["Japan", "Australia", "India"], "parent": "All"},
    "Latin America": {"children": ["Brazil", "Argentina", "Chile"], "parent": "All"},
    # Leaf nodes with values (in millions)
    "USA": {"value": 2400, "parent": "North America"},
    "Canada": {"value": 680, "parent": "North America"},
    "Mexico": {"value": 420, "parent": "North America"},
    "UK": {"value": 1200, "parent": "Europe"},
    "Germany": {"value": 980, "parent": "Europe"},
    "France": {"value": 750, "parent": "Europe"},
    "Japan": {"value": 1600, "parent": "Asia Pacific"},
    "Australia": {"value": 890, "parent": "Asia Pacific"},
    "India": {"value": 560, "parent": "Asia Pacific"},
    "Brazil": {"value": 640, "parent": "Latin America"},
    "Argentina": {"value": 380, "parent": "Latin America"},
    "Chile": {"value": 320, "parent": "Latin America"},
}

# Compute parent values (sum of children)
hierarchy["North America"]["value"] = sum(hierarchy[c]["value"] for c in hierarchy["North America"]["children"])
hierarchy["Europe"]["value"] = sum(hierarchy[c]["value"] for c in hierarchy["Europe"]["children"])
hierarchy["Asia Pacific"]["value"] = sum(hierarchy[c]["value"] for c in hierarchy["Asia Pacific"]["children"])
hierarchy["Latin America"]["value"] = sum(hierarchy[c]["value"] for c in hierarchy["Latin America"]["children"])

# Color mapping using Okabe-Ito (first series is always #009E73 for brand)
colors = {
    "North America": OKABE_ITO[0],  # #009E73 - brand green
    "Europe": OKABE_ITO[1],  # #D55E00 - vermillion
    "Asia Pacific": OKABE_ITO[2],  # #0072B2 - blue
    "Latin America": OKABE_ITO[3],  # #CC79A7 - reddish purple
}

# Lighter shades for subcategories (derived from main colors with opacity in hover)
sub_colors = {
    # North America shades
    "USA": OKABE_ITO[0],
    "Canada": OKABE_ITO[0],
    "Mexico": OKABE_ITO[0],
    # Europe shades
    "UK": OKABE_ITO[1],
    "Germany": OKABE_ITO[1],
    "France": OKABE_ITO[1],
    # Asia Pacific shades
    "Japan": OKABE_ITO[2],
    "Australia": OKABE_ITO[2],
    "India": OKABE_ITO[2],
    # Latin America shades
    "Brazil": OKABE_ITO[3],
    "Argentina": OKABE_ITO[3],
    "Chile": OKABE_ITO[3],
}

# Get data for top level
current_level = "All"
children = hierarchy[current_level]["children"]
values = [hierarchy[child]["value"] for child in children]
slice_colors = [colors[child] for child in children]

# Create pie chart
fig = go.Figure()

fig.add_trace(
    go.Pie(
        labels=children,
        values=values,
        hole=0.3,
        textinfo="label+percent",
        textposition="outside",
        textfont={"size": 20, "color": INK},
        hovertemplate="<b>%{label}</b><br>Sales: $%{value:.0f}M<br>Percentage: %{percent}<br><extra>Click to drill</extra>",
        marker={"colors": slice_colors, "line": {"color": PAGE_BG, "width": 3}},
        pull=[0.02] * len(children),
        sort=False,
    )
)

# Center annotation
fig.add_annotation(
    text="<b>Global Sales</b><br>by Region",
    x=0.5,
    y=0.5,
    font={"size": 24, "color": INK},
    showarrow=False,
    xref="paper",
    yref="paper",
)

# Breadcrumb navigation (repositioned lower to avoid overlap)
fig.add_annotation(
    text="📍 All Regions",
    x=0.02,
    y=0.15,
    xanchor="left",
    yanchor="bottom",
    font={"size": 20, "color": INK},
    showarrow=False,
    xref="paper",
    yref="paper",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=10,
)

# Click instruction
fig.add_annotation(
    text="Click any slice to explore by country",
    x=0.5,
    y=0.02,
    xanchor="center",
    yanchor="bottom",
    font={"size": 18, "color": INK_SOFT},
    showarrow=False,
    xref="paper",
    yref="paper",
)

fig.update_layout(
    title={
        "text": "pie-drilldown · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    showlegend=True,
    legend={
        "orientation": "v",
        "yanchor": "middle",
        "y": 0.5,
        "xanchor": "left",
        "x": 1.02,
        "font": {"size": 18, "color": INK_SOFT},
        "title": {"text": "Regions", "font": {"size": 20, "color": INK}},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 60, "r": 200, "t": 100, "b": 100},
)

# JavaScript for drilldown (only in HTML)
hierarchy_json = json.dumps(hierarchy)
colors_json = json.dumps(colors)
sub_colors_json = json.dumps(sub_colors)

drilldown_js = f"""
<script>
var hierarchyData = {hierarchy_json};
var colors = {colors_json};
var subColors = {sub_colors_json};
var currentPath = ['All'];

function getValue(nodeName) {{
    return hierarchyData[nodeName].value;
}}

function updateBreadcrumb() {{
    var breadcrumb = '📍 ' + currentPath.join(' > ');
    var annotations = document.querySelectorAll('[data-breadcrumb]');
    annotations.forEach(function(el) {{
        if (el.textContent && el.textContent.includes('📍')) {{
            el.textContent = breadcrumb;
        }}
    }});
}}

function updateChart(level) {{
    var node = hierarchyData[level];
    if (!node.children) return;

    var children = node.children;
    var values = children.map(c => getValue(c));
    var sliceColors = children.map(c => subColors[c] || colors[c] || '#009E73');

    Plotly.animate('plotly-chart', {{
        data: [{{
            labels: children,
            values: values,
            marker: {{colors: sliceColors}}
        }}],
        layout: {{}}
    }}, {{
        transition: {{duration: 500, easing: 'cubic-in-out'}},
        frame: {{duration: 500}}
    }});
    updateBreadcrumb();
}}

document.getElementById('plotly-chart').on('plotly_click', function(data) {{
    var clickedLabel = data.points[0].label;
    if (hierarchyData[clickedLabel] && hierarchyData[clickedLabel].children) {{
        currentPath.push(clickedLabel);
        updateChart(clickedLabel);
    }}
}});

// Double-click to go back up hierarchy
document.getElementById('plotly-chart').on('plotly_doubleclick', function() {{
    if (currentPath.length > 1) {{
        currentPath.pop();
        updateChart(currentPath[currentPath.length - 1]);
    }}
}});
</script>
"""

# Save PNG
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save HTML with drilldown interactivity
html_content = fig.to_html(
    full_html=True,
    include_plotlyjs="cdn",
    div_id="plotly-chart",
    config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "toImageButtonOptions": {"format": "png", "width": 4800, "height": 2700},
    },
)

html_content = html_content.replace("</body>", drilldown_js + "</body>")

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
