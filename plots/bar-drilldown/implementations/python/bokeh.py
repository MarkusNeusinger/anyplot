""" pyplots.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-16
"""

from bokeh.io import export_png, save
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, CustomJS, Div, LabelSet, Legend, TapTool
from bokeh.plotting import figure


# Hierarchical data structure: Sales by Region > Country > City
hierarchy_data = {
    "root": {"children": ["north_america", "europe", "asia_pacific"]},
    "north_america": {"name": "North America", "value": 450, "parent": "root", "children": ["usa", "canada", "mexico"]},
    "europe": {"name": "Europe", "value": 380, "parent": "root", "children": ["uk", "germany", "france"]},
    "asia_pacific": {
        "name": "Asia Pacific",
        "value": 320,
        "parent": "root",
        "children": ["japan", "australia", "singapore"],
    },
    # North America children
    "usa": {"name": "USA", "value": 280, "parent": "north_america", "children": ["new_york", "los_angeles", "chicago"]},
    "canada": {
        "name": "Canada",
        "value": 95,
        "parent": "north_america",
        "children": ["toronto", "vancouver", "montreal"],
    },
    "mexico": {
        "name": "Mexico",
        "value": 75,
        "parent": "north_america",
        "children": ["mexico_city", "guadalajara", "monterrey"],
    },
    # Europe children
    "uk": {"name": "UK", "value": 140, "parent": "europe", "children": ["london", "manchester", "birmingham"]},
    "germany": {"name": "Germany", "value": 130, "parent": "europe", "children": ["berlin", "munich", "hamburg"]},
    "france": {"name": "France", "value": 110, "parent": "europe", "children": ["paris", "lyon", "marseille"]},
    # Asia Pacific children
    "japan": {"name": "Japan", "value": 150, "parent": "asia_pacific", "children": ["tokyo", "osaka", "kyoto"]},
    "australia": {
        "name": "Australia",
        "value": 100,
        "parent": "asia_pacific",
        "children": ["sydney", "melbourne", "brisbane"],
    },
    "singapore": {"name": "Singapore", "value": 70, "parent": "asia_pacific", "children": []},
    # Level 3: Cities (leaf nodes - no children)
    "new_york": {"name": "New York", "value": 120, "parent": "usa", "children": []},
    "los_angeles": {"name": "Los Angeles", "value": 95, "parent": "usa", "children": []},
    "chicago": {"name": "Chicago", "value": 65, "parent": "usa", "children": []},
    "toronto": {"name": "Toronto", "value": 45, "parent": "canada", "children": []},
    "vancouver": {"name": "Vancouver", "value": 30, "parent": "canada", "children": []},
    "montreal": {"name": "Montreal", "value": 20, "parent": "canada", "children": []},
    "mexico_city": {"name": "Mexico City", "value": 40, "parent": "mexico", "children": []},
    "guadalajara": {"name": "Guadalajara", "value": 20, "parent": "mexico", "children": []},
    "monterrey": {"name": "Monterrey", "value": 15, "parent": "mexico", "children": []},
    "london": {"name": "London", "value": 65, "parent": "uk", "children": []},
    "manchester": {"name": "Manchester", "value": 40, "parent": "uk", "children": []},
    "birmingham": {"name": "Birmingham", "value": 35, "parent": "uk", "children": []},
    "berlin": {"name": "Berlin", "value": 55, "parent": "germany", "children": []},
    "munich": {"name": "Munich", "value": 45, "parent": "germany", "children": []},
    "hamburg": {"name": "Hamburg", "value": 30, "parent": "germany", "children": []},
    "paris": {"name": "Paris", "value": 50, "parent": "france", "children": []},
    "lyon": {"name": "Lyon", "value": 35, "parent": "france", "children": []},
    "marseille": {"name": "Marseille", "value": 25, "parent": "france", "children": []},
    "tokyo": {"name": "Tokyo", "value": 70, "parent": "japan", "children": []},
    "osaka": {"name": "Osaka", "value": 50, "parent": "japan", "children": []},
    "kyoto": {"name": "Kyoto", "value": 30, "parent": "japan", "children": []},
    "sydney": {"name": "Sydney", "value": 45, "parent": "australia", "children": []},
    "melbourne": {"name": "Melbourne", "value": 35, "parent": "australia", "children": []},
    "brisbane": {"name": "Brisbane", "value": 20, "parent": "australia", "children": []},
}

# Get data for a specific level
root_children = hierarchy_data["root"]["children"]
names = [hierarchy_data[child]["name"] for child in root_children]
values = [hierarchy_data[child]["value"] for child in root_children]
ids = root_children
has_children = [len(hierarchy_data[child].get("children", [])) > 0 for child in root_children]

# Colors for bars (Python blue and complementary colors)
colors = ["#306998", "#FFD43B", "#4B8BBE", "#FFE873", "#646464"]

# Create ColumnDataSource
source = ColumnDataSource(
    data={
        "names": names,
        "values": values,
        "ids": ids,
        "colors": [colors[i % len(colors)] for i in range(len(names))],
        "has_children": has_children,
        "label_y": [v + 10 for v in values],
    }
)

# State source to track current level and path
state_source = ColumnDataSource(
    data={"current_parent": ["root"], "breadcrumb_path": ["All"], "breadcrumb_ids": ["root"]}
)

# Create figure with categorical x-axis
p = figure(
    x_range=names,
    width=4800,
    height=2700,
    title="bar-drilldown · bokeh · pyplots.ai",
    tools="tap",
    toolbar_location=None,
)

# Render bars
bars = p.vbar(
    x="names",
    top="values",
    width=0.7,
    source=source,
    fill_color="colors",
    line_color="white",
    line_width=2,
    fill_alpha=0.9,
)

# Add value labels on bars
labels = LabelSet(
    x="names",
    y="label_y",
    text="values",
    source=source,
    text_align="center",
    text_baseline="bottom",
    text_font_size="28pt",
    text_font_style="bold",
    text_color="#333333",
)
p.add_layout(labels)

# Styling - increased font sizes for better legibility
p.title.text_font_size = "42pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label = "Category"
p.yaxis.axis_label = "Sales (millions $)"
p.xaxis.axis_label_text_font_size = "30pt"
p.yaxis.axis_label_text_font_size = "30pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.major_label_orientation = 0  # Horizontal labels
p.y_range.start = 0
p.y_range.end = max(values) * 1.15

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = [6, 4]

# Outline
p.outline_line_color = "#cccccc"
p.outline_line_width = 2

# Hover cursor indicator
bars.selection_glyph = bars.glyph
bars.nonselection_glyph = bars.glyph

# Add legend showing region colors using separate renderers for reliable PNG export
legend_renderers = []
for i, child_id in enumerate(root_children):
    # Create invisible scatter points for legend entries
    legend_source = ColumnDataSource(data={"x": [names[i]], "y": [values[i] / 2]})
    scatter = p.scatter(
        x="x",
        y="y",
        source=legend_source,
        fill_color=colors[i % len(colors)],
        line_color="white",
        size=0,  # Invisible points
        marker="square",
    )
    legend_renderers.append((hierarchy_data[child_id]["name"], [scatter]))

legend = Legend(items=legend_renderers, location="top_right", label_text_font_size="24pt")
legend.background_fill_alpha = 0.9
legend.background_fill_color = "white"
legend.border_line_color = "#cccccc"
legend.border_line_width = 2
legend.padding = 20
legend.spacing = 12
legend.glyph_height = 30
legend.glyph_width = 30
legend.label_standoff = 10
p.add_layout(legend, "right")

# Breadcrumb div for navigation (display only - Back button handles navigation)
breadcrumb_div = Div(
    text='<div style="font-size: 28pt; font-family: Arial, sans-serif; padding: 15px; '
    'background: #f5f5f5; border-radius: 8px; display: inline-block;">'
    '<span style="color: #306998; font-weight: bold;">📍 </span>'
    '<span style="color: #333; font-weight: bold;">All</span>'
    "</div>",
    width=2400,
)

# Back button (visible but only functional when not at root)
back_button = Button(label="⬅ Back", button_type="primary", width=200, height=60)

# Instructions div - increased font size for better legibility
instructions_div = Div(
    text='<div style="font-size: 28pt; font-family: Arial, sans-serif; padding: 20px; '
    'color: #333; text-align: center; background: #e8f4fc; border-radius: 8px; margin-top: 20px;">'
    "👆 <b>Click on a bar to drill down</b> | Use Back button to navigate up"
    "</div>",
    width=4800,
)

# JavaScript callback for drilling down
drill_callback = CustomJS(
    args={
        "source": source,
        "state": state_source,
        "p": p,
        "hierarchy": hierarchy_data,
        "colors": colors,
        "breadcrumb_div": breadcrumb_div,
        "back_button": back_button,
    },
    code="""
    const indices = source.selected.indices;
    if (indices.length === 0) return;

    const idx = indices[0];
    const clicked_id = source.data['ids'][idx];
    const node = hierarchy[clicked_id];

    // Check if this node has children
    if (!node || !node.children || node.children.length === 0) {
        source.selected.indices = [];
        return;
    }

    // Get children data
    const children_ids = node.children;
    const names = [];
    const values = [];
    const has_children = [];

    for (const child_id of children_ids) {
        const child = hierarchy[child_id];
        names.push(child.name);
        values.push(child.value);
        has_children.push(child.children && child.children.length > 0);
    }

    // Update source data
    source.data['names'] = names;
    source.data['values'] = values;
    source.data['ids'] = children_ids;
    source.data['has_children'] = has_children;
    source.data['colors'] = names.map((_, i) => colors[i % colors.length]);
    source.data['label_y'] = values.map(v => v + 5);

    // Update x_range
    p.x_range.factors = names;

    // Update y_range
    const max_val = Math.max(...values);
    p.y_range.end = max_val * 1.15;

    // Update state
    const current_path = state.data['breadcrumb_path'].slice();
    const current_ids = state.data['breadcrumb_ids'].slice();
    current_path.push(node.name);
    current_ids.push(clicked_id);
    state.data['current_parent'] = [clicked_id];
    state.data['breadcrumb_path'] = current_path;
    state.data['breadcrumb_ids'] = current_ids;

    // Update breadcrumb display
    let breadcrumb_html = '<div style="font-size: 28pt; font-family: Arial, sans-serif; padding: 15px; background: #f5f5f5; border-radius: 8px; display: inline-block;">';
    breadcrumb_html += '<span style="color: #306998; font-weight: bold;">📍 </span>';

    for (let i = 0; i < current_path.length; i++) {
        if (i > 0) {
            breadcrumb_html += '<span style="color: #999;"> › </span>';
        }
        const is_last = (i === current_path.length - 1);
        if (is_last) {
            breadcrumb_html += '<span style="color: #333; font-weight: bold;">' + current_path[i] + '</span>';
        } else {
            breadcrumb_html += '<span style="color: #306998;">' + current_path[i] + '</span>';
        }
    }
    breadcrumb_html += '</div>';
    breadcrumb_div.text = breadcrumb_html;

    // Enable Back button when not at root
    back_button.disabled = false;

    source.selected.indices = [];
    source.change.emit();
    state.change.emit();
""",
)

# JavaScript callback for drilling up (Back button)
drill_up_callback = CustomJS(
    args={
        "source": source,
        "state": state_source,
        "p": p,
        "hierarchy": hierarchy_data,
        "colors": colors,
        "breadcrumb_div": breadcrumb_div,
        "back_button": back_button,
    },
    code="""
    const current_path = state.data['breadcrumb_path'];
    const current_ids = state.data['breadcrumb_ids'];

    // If at root level, do nothing
    if (current_ids.length <= 1) return;

    // Go up one level
    const new_path = current_path.slice(0, -1);
    const new_ids = current_ids.slice(0, -1);
    const parent_id = new_ids[new_ids.length - 1];

    // Get data for parent level
    let children_ids;
    if (parent_id === 'root') {
        children_ids = hierarchy['root']['children'];
    } else {
        children_ids = hierarchy[parent_id]['children'];
    }

    const names = [];
    const values = [];
    const has_children = [];

    for (const child_id of children_ids) {
        const child = hierarchy[child_id];
        names.push(child.name);
        values.push(child.value);
        has_children.push(child.children && child.children.length > 0);
    }

    // Update source data
    source.data['names'] = names;
    source.data['values'] = values;
    source.data['ids'] = children_ids;
    source.data['has_children'] = has_children;
    source.data['colors'] = names.map((_, i) => colors[i % colors.length]);
    source.data['label_y'] = values.map(v => v + 5);

    // Update x_range
    p.x_range.factors = names;

    // Update y_range
    const max_val = Math.max(...values);
    p.y_range.end = max_val * 1.15;

    // Update state
    state.data['current_parent'] = [parent_id];
    state.data['breadcrumb_path'] = new_path;
    state.data['breadcrumb_ids'] = new_ids;

    // Update breadcrumb display
    let breadcrumb_html = '<div style="font-size: 28pt; font-family: Arial, sans-serif; padding: 15px; background: #f5f5f5; border-radius: 8px; display: inline-block;">';
    breadcrumb_html += '<span style="color: #306998; font-weight: bold;">📍 </span>';

    for (let i = 0; i < new_path.length; i++) {
        if (i > 0) {
            breadcrumb_html += '<span style="color: #999;"> › </span>';
        }
        const is_last = (i === new_path.length - 1);
        if (is_last) {
            breadcrumb_html += '<span style="color: #333; font-weight: bold;">' + new_path[i] + '</span>';
        } else {
            breadcrumb_html += '<span style="color: #306998;">' + new_path[i] + '</span>';
        }
    }
    breadcrumb_html += '</div>';
    breadcrumb_div.text = breadcrumb_html;

    // Disable Back button if at root
    if (new_ids.length <= 1) {
        back_button.disabled = true;
    }

    source.change.emit();
    state.change.emit();
""",
)

# Attach drill-up callback to back button
back_button.js_on_click(drill_up_callback)
back_button.disabled = True  # Start disabled since we're at root

# Add tap tool callback
p.select(TapTool).callback = drill_callback

# Create layout with navigation row containing breadcrumb and back button
nav_row = row(breadcrumb_div, back_button)
layout = column(nav_row, p, instructions_div)

# Save outputs (PNG for static preview, HTML for interactivity)
export_png(layout, filename="plot.png")
save(layout, filename="plot.html", title="bar-drilldown · bokeh · pyplots.ai")
