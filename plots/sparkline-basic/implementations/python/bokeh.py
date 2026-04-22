""" pyplots.ai
sparkline-basic: Basic Sparkline
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.plotting import figure


# Data - Daily website traffic over 30 days showing realistic trends
np.random.seed(42)
base = 1000
trend = np.linspace(0, 200, 30)  # Gradual upward trend
noise = np.random.randn(30) * 80
seasonality = 50 * np.sin(np.linspace(0, 4 * np.pi, 30))  # Weekly pattern
values = base + trend + noise + seasonality

x = list(range(len(values)))

# Find min/max points for highlighting
min_idx = np.argmin(values)
max_idx = np.argmax(values)

# Plot - Sparkline with compact aspect ratio
# Using 4800x1200 for ~4:1 aspect ratio (sparkline characteristic)
p = figure(width=4800, height=1200, toolbar_location=None, title="sparkline-basic · bokeh · pyplots.ai")

# Remove all chart chrome for sparkline minimalism
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Main sparkline
p.line(x, values, line_width=4, color="#306998", alpha=0.9)

# Highlight first point (reference)
p.scatter([x[0]], [values[0]], size=20, color="#306998", alpha=0.7)

# Highlight last point (current)
p.scatter([x[-1]], [values[-1]], size=20, color="#306998", alpha=0.7)

# Highlight min point
p.scatter([x[min_idx]], [values[min_idx]], size=25, color="#E74C3C", alpha=0.9)

# Highlight max point
p.scatter([x[max_idx]], [values[max_idx]], size=25, color="#27AE60", alpha=0.9)

# Title styling
p.title.text_font_size = "28pt"
p.title.align = "center"

# Add some padding
p.min_border = 40

# Save outputs
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
