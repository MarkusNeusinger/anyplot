""" anyplot.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: plotly 6.7.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-15
"""

import json
import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
ELEVATED_DARK = "#F5F3ED" if THEME == "light" else "#3A3935"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ACCENT = "#009E73"

# Okabe-Ito palette (first series must be #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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
total_value = sum(hierarchy[c]["value"] for c in hierarchy["All"]["children"])

# Find top region for visual emphasis
top_region = max(hierarchy["All"]["children"], key=lambda x: hierarchy[x]["value"])
top_value = hierarchy[top_region]["value"]
top_percent = 100 * top_value / total_value

# Color mapping using Okabe-Ito (first series is always #009E73 for brand)
colors = {
    "North America": IMPRINT[0],  # #009E73 - brand green
    "Europe": IMPRINT[1],  # #C475FD - vermillion
    "Asia Pacific": IMPRINT[2],  # #4467A3 - blue
    "Latin America": IMPRINT[3],  # #BD8233 - reddish purple
}

# Lighter shades for subcategories (derived from main colors with opacity in hover)
sub_colors = {
    # North America shades
    "USA": IMPRINT[0],
    "Canada": IMPRINT[0],
    "Mexico": IMPRINT[0],
    # Europe shades
    "UK": IMPRINT[1],
    "Germany": IMPRINT[1],
    "France": IMPRINT[1],
    # Asia Pacific shades
    "Japan": IMPRINT[2],
    "Australia": IMPRINT[2],
    "India": IMPRINT[2],
    # Latin America shades
    "Brazil": IMPRINT[3],
    "Argentina": IMPRINT[3],
    "Chile": IMPRINT[3],
}

# Get data for top level
current_level = "All"
children = hierarchy[current_level]["children"]
values = [hierarchy[child]["value"] for child in children]
slice_colors = [colors[child] for child in children]

# Create pie chart with enhanced styling
fig = go.Figure()

fig.add_trace(
    go.Pie(
        labels=children,
        values=values,
        hole=0.35,
        textinfo="label+percent",
        textposition="outside",
        textfont={"size": 22, "color": INK, "family": "Arial, sans-serif"},
        hovertemplate="<b style='font-size:16px'>%{label}</b><br>"
        + "Sales: <b>$%{value:.0f}M</b><br>"
        + "Share: <b>%{percent}</b><br>"
        + "<i style='color:#999'>↻ Click to explore</i><extra></extra>",
        marker={"colors": slice_colors, "line": {"color": PAGE_BG, "width": 4}},
        pull=[0.08] * len(children),
        sort=False,
    )
)

# Enhanced center annotation with key insight
fig.add_annotation(
    text="<b>Global Sales</b><br><span style='font-size:20px'>by Region</span>",
    x=0.5,
    y=0.52,
    font={"size": 26, "color": INK, "family": "Arial, sans-serif"},
    showarrow=False,
    xref="paper",
    yref="paper",
)

# Top region insight annotation (visual storytelling)
fig.add_annotation(
    text=f"<b>🏆 Leading Region</b><br>{top_region}<br><span style='font-size:18px; color:{ACCENT}'>${top_value:.0f}M ({top_percent:.1f}%)</span>",
    x=0.5,
    y=0.35,
    font={"size": 16, "color": INK},
    showarrow=False,
    xref="paper",
    yref="paper",
    bgcolor=ELEVATED_DARK,
    bordercolor=ACCENT,
    borderwidth=2,
    borderpad=12,
    opacity=0.95,
)

# Enhanced breadcrumb navigation with styling
fig.add_annotation(
    text="<b>📍 Navigate</b><br>All Regions",
    x=0.02,
    y=0.18,
    xanchor="left",
    yanchor="middle",
    font={"size": 18, "color": INK, "family": "Arial, sans-serif"},
    showarrow=False,
    xref="paper",
    yref="paper",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=2,
    borderpad=12,
    align="left",
)

# Improved click instruction with visual emphasis
fig.add_annotation(
    text="<i style='font-size:16px; color:"
    + INK_SOFT
    + "'>💡 Click any slice to drill down and explore by country</i>",
    x=0.5,
    y=0.01,
    xanchor="center",
    yanchor="bottom",
    font={"size": 16, "color": INK_SOFT},
    showarrow=False,
    xref="paper",
    yref="paper",
)

fig.update_layout(
    title={
        "text": "<b>Global Sales Distribution by Region</b><br><span style='font-size:20px; font-weight: normal'>plotly · anyplot.ai</span>",
        "font": {"size": 32, "color": INK, "family": "Arial, sans-serif"},
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
        "font": {"size": 18, "color": INK_SOFT, "family": "Arial, sans-serif"},
        "title": {"text": "<b>Sales Regions</b>", "font": {"size": 20, "color": INK}},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 2,
        "tracegroupgap": 10,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": "Arial, sans-serif"},
    margin={"l": 80, "r": 240, "t": 120, "b": 100},
    height=900,
    width=1600,
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
