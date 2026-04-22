""" pyplots.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Load and prepare data
iris = load_iris()
X = iris.data
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

# Normalize variables to similar scales
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


# Andrews curve function: f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + ...
def andrews_curve(coeffs, t):
    n = len(coeffs)
    result = coeffs[0] / np.sqrt(2)
    for i in range(1, n):
        if i % 2 == 1:
            result += coeffs[i] * np.sin((i // 2 + 1) * t)
        else:
            result += coeffs[i] * np.cos((i // 2) * t)
    return result


# Generate t values from -π to π
t_values = np.linspace(-np.pi, np.pi, 200)

# Colors for each species (Python Blue, Python Yellow, and a colorblind-safe teal)
colors = ["#306998", "#FFD43B", "#2AA198"]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="andrews-curves · bokeh · pyplots.ai",
    x_axis_label="t (radians)",
    y_axis_label="f(t)",
)

# Store legend items
legend_items = []

# Plot curves for each species
for species_idx in range(3):
    species_mask = y == species_idx
    X_species = X_scaled[species_mask]

    # Track first line for legend
    first_line = None

    for coeffs in X_species:
        curve_values = andrews_curve(coeffs, t_values)

        source = ColumnDataSource(data={"x": t_values, "y": curve_values})

        line = p.line(x="x", y="y", source=source, line_color=colors[species_idx], line_alpha=0.4, line_width=2)

        if first_line is None:
            first_line = line

    legend_items.append((species_names[species_idx], [first_line]))

# Create and add legend
legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "20pt"
legend.background_fill_alpha = 0.8
p.add_layout(legend, "right")

# Style the plot
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html", title="Andrews Curves - Bokeh")
save(p)
