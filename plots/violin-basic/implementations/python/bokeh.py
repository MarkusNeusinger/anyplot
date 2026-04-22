""" pyplots.ai
violin-basic: Basic Violin Plot
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-21
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from scipy.stats import gaussian_kde


# Data - Salary distributions by department (realistic scenario)
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Support"]

# Engineering: normal, high mean — represents typical salaried professionals
eng = np.random.normal(85000, 15000, 150)

# Marketing: normal, mid-range
mkt = np.random.normal(65000, 12000, 150)

# Sales: right-skewed — most earn base salary, some earn high commissions
sales_base = np.random.exponential(15000, 150) + 45000
sales = np.clip(sales_base, 30000, 150000)

# Support: bimodal — junior vs senior tiers with distinct pay bands
support_junior = np.random.normal(42000, 5000, 90)
support_senior = np.random.normal(62000, 6000, 60)
support = np.concatenate([support_junior, support_senior])

data = {"Engineering": eng, "Marketing": mkt, "Sales": sales, "Support": support}

# Colors - four distinct colorblind-safe hues
colors = ["#306998", "#E8943A", "#2A9D8F", "#E76F6F"]

# Visual hierarchy: emphasize non-normal distributions to guide the viewer
alphas = [0.55, 0.55, 0.85, 0.85]

# Distribution type labels for data storytelling
dist_labels = ["normal", "normal", "right-skewed", "bimodal"]

# Create figure with subtle warm background tint
p = figure(
    width=4800,
    height=2700,
    title="violin-basic · bokeh · pyplots.ai",
    x_axis_label="Department",
    y_axis_label="Annual Salary (USD)",
    x_range=categories,
    toolbar_location=None,
    background_fill_color="#FAFAF8",
)

# Title styling — lighter secondary color for visual weight
p.title.text_font_size = "36pt"
p.title.text_color = "#2D3436"
p.title.text_font_style = "bold"

# Text sizing for 4800x2700 px
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = "#555555"
p.yaxis.axis_label_text_color = "#555555"

# Format y-axis as readable currency
p.yaxis.formatter = NumeralTickFormatter(format="$0,0")

# Visual refinement - clean, polished design
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_dash = "dashed"
p.ygrid.grid_line_color = "#B0B0B0"
p.outline_line_color = None
p.axis.minor_tick_line_color = None
p.axis.major_tick_line_color = None
p.axis.axis_line_color = "#D5D5D5"
p.border_fill_color = "#FAFAF8"

# Tighten y-axis to data range with room for annotations
all_values = np.concatenate(list(data.values()))
y_pad = (all_values.max() - all_values.min()) * 0.12
p.y_range.start = all_values.min() - y_pad
p.y_range.end = all_values.max() + y_pad

# Violin width scaling
violin_width = 0.4

# Draw violins for each category
for i, cat in enumerate(categories):
    values = data[cat]

    # Compute KDE using scipy (idiomatic, robust bandwidth selection)
    kde = gaussian_kde(values)
    y_grid = np.linspace(values.min() - np.std(values) * 0.5, values.max() + np.std(values) * 0.5, 100)
    density = kde(y_grid)

    # Scale density to violin width
    density_scaled = density / density.max() * violin_width

    # Create mirrored violin shape using categorical offset tuples
    xs_left = [(cat, float(-d)) for d in density_scaled]
    xs_right = [(cat, float(d)) for d in density_scaled[::-1]]

    # Draw violin patch via ColumnDataSource with varying alpha for hierarchy
    violin_source = ColumnDataSource(data={"x": xs_left + xs_right, "y": list(y_grid) + list(y_grid[::-1])})
    p.patch(
        x="x",
        y="y",
        source=violin_source,
        fill_color=colors[i],
        fill_alpha=alphas[i],
        line_color=colors[i],
        line_alpha=min(alphas[i] + 0.15, 1.0),
        line_width=3,
    )

    # Quartiles and median
    q1, median, q3 = np.percentile(values, [25, 50, 75])

    # Inner box (Q1-Q3) with ColumnDataSource for HoverTool
    box_width = 0.06
    box_source = ColumnDataSource(
        data={
            "left": [(cat, -box_width)],
            "right": [(cat, box_width)],
            "top": [q3],
            "bottom": [q1],
            "dept": [cat],
            "median_val": [f"${median:,.0f}"],
            "q1_val": [f"${q1:,.0f}"],
            "q3_val": [f"${q3:,.0f}"],
            "n": [str(len(values))],
        }
    )
    box_renderer = p.quad(
        left="left",
        right="right",
        top="top",
        bottom="bottom",
        source=box_source,
        fill_color="white",
        fill_alpha=0.9,
        line_color="black",
        line_width=3,
    )

    # Add HoverTool for interactive HTML output
    hover = HoverTool(
        renderers=[box_renderer],
        tooltips=[
            ("Department", "@dept"),
            ("Median", "@median_val"),
            ("Q1", "@q1_val"),
            ("Q3", "@q3_val"),
            ("N", "@n"),
        ],
    )
    p.add_tools(hover)

    # Median line
    med_source = ColumnDataSource(
        data={"x0": [(cat, -box_width * 1.5)], "y0": [median], "x1": [(cat, box_width * 1.5)], "y1": [median]}
    )
    p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=med_source, line_color="black", line_width=5)

    # Whiskers (1.5*IQR or data extent)
    iqr_val = q3 - q1
    whisker_low = max(values.min(), q1 - 1.5 * iqr_val)
    whisker_high = min(values.max(), q3 + 1.5 * iqr_val)

    whisker_source = ColumnDataSource(
        data={"x0": [cat, cat], "y0": [q1, q3], "x1": [cat, cat], "y1": [whisker_low, whisker_high]}
    )
    p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=whisker_source, line_color="black", line_width=3)

    # Whisker caps
    cap_width = 0.04
    cap_source = ColumnDataSource(
        data={
            "x0": [(cat, -cap_width), (cat, -cap_width)],
            "y0": [whisker_low, whisker_high],
            "x1": [(cat, cap_width), (cat, cap_width)],
            "y1": [whisker_low, whisker_high],
        }
    )
    p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=cap_source, line_color="black", line_width=3)

# Distribution type annotations — guide the viewer to the data story
annotation_y = all_values.min() - y_pad * 0.65
ann_source = ColumnDataSource(data={"x": categories, "y": [annotation_y] * len(categories), "text": dist_labels})
p.text(
    x="x",
    y="y",
    text="text",
    source=ann_source,
    text_font_size="18pt",
    text_font_style="italic",
    text_color="#999999",
    text_align="center",
    text_baseline="top",
)

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
