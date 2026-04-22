""" pyplots.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data: Simulated word embeddings for programming languages
np.random.seed(42)

# Programming languages with 2D coordinates (like t-SNE output)
labels = [
    "Python",
    "JavaScript",
    "Java",
    "C++",
    "Ruby",
    "Go",
    "Rust",
    "Swift",
    "Kotlin",
    "TypeScript",
    "PHP",
    "Scala",
    "R",
    "Julia",
    "Perl",
    "Lua",
    "Haskell",
    "Clojure",
    "Erlang",
    "Elixir",
    "Dart",
    "MATLAB",
    "Fortran",
    "COBOL",
    "Assembly",
    "SQL",
    "Bash",
    "PowerShell",
    "Groovy",
    "F#",
]

# Create clustered coordinates (simulating embedding space)
# Cluster 1: Modern general-purpose (center-right)
# Cluster 2: Systems languages (upper-left)
# Cluster 3: Functional languages (lower-left)
# Cluster 4: Legacy/specialized (scattered)

n = len(labels)
x = np.zeros(n)
y = np.zeros(n)

# Modern general-purpose languages
modern = [0, 1, 2, 8, 9, 10, 18, 20]  # Python, JS, Java, Kotlin, TS, PHP, Erlang, Dart
for i in modern:
    x[i] = np.random.normal(4, 1.2)
    y[i] = np.random.normal(3, 1.2)

# Systems languages
systems = [3, 5, 6, 7, 24]  # C++, Go, Rust, Swift, Assembly
for i in systems:
    x[i] = np.random.normal(-3, 1.0)
    y[i] = np.random.normal(4, 1.0)

# Functional languages - spread them more to avoid overlap
functional = [11, 16, 17, 19, 29]  # Scala, Haskell, Clojure, Elixir, F#
for i, idx in enumerate(functional):
    x[idx] = np.random.normal(-3.5 + i * 0.8, 0.5)
    y[idx] = np.random.normal(-2.5 + i * 0.5, 0.5)

# Data science / Scientific
scientific = [4, 12, 13, 21]  # Ruby, R, Julia, MATLAB
for i in scientific:
    x[i] = np.random.normal(1, 1.2)
    y[i] = np.random.normal(-3.5, 1.0)

# Scripting languages
scripting = [14, 15, 26, 27]  # Perl, Lua, Bash, PowerShell
for i in scripting:
    x[i] = np.random.normal(-1, 1.5)
    y[i] = np.random.normal(0.5, 1.5)

# Legacy languages
legacy = [22, 23, 25, 28]  # Fortran, COBOL, SQL, Groovy
for i in legacy:
    x[i] = np.random.normal(3, 1.5)
    y[i] = np.random.normal(-1, 1.5)

# Add slight jitter to prevent exact overlap
x += np.random.normal(0, 0.2, n)
y += np.random.normal(0, 0.2, n)

# Create data source
source = ColumnDataSource(data={"x": x, "y": y, "labels": labels})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-text · bokeh · pyplots.ai",
    x_axis_label="Embedding Dimension 1",
    y_axis_label="Embedding Dimension 2",
    tools="",
)

# Style the figure
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Add invisible scatter points (for positioning reference)
p.scatter("x", "y", source=source, size=1, alpha=0)

# Add text labels at each coordinate
text_labels = LabelSet(
    x="x",
    y="y",
    text="labels",
    source=source,
    text_font_size="22pt",
    text_color="#306998",  # Python Blue
    text_alpha=0.85,
    text_align="center",
    text_baseline="middle",
)
p.add_layout(text_labels)

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#fafafa"

# Export PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="scatter-text · bokeh · pyplots.ai")
