""" pyplots.ai
heatmap-annotated: Annotated Heatmap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-24
"""

import numpy as np
import plotly.figure_factory as ff


# Data: Correlation matrix for stock market sectors
np.random.seed(42)

sectors = ["Technology", "Healthcare", "Finance", "Energy", "Consumer", "Industrial", "Materials", "Utilities"]
n_sectors = len(sectors)

# Generate realistic correlation matrix
base = np.random.randn(100, n_sectors)
# Add some structure: sectors within similar groups correlate more
base[:, 0:3] += np.random.randn(100, 1) * 0.5  # Tech, Healthcare, Finance
base[:, 3:6] += np.random.randn(100, 1) * 0.4  # Energy, Consumer, Industrial
base[:, 6:8] += np.random.randn(100, 1) * 0.3  # Materials, Utilities

correlation_matrix = np.corrcoef(base.T)
correlation_matrix = np.round(correlation_matrix, 2)

# Create annotated heatmap using figure factory
fig = ff.create_annotated_heatmap(
    z=correlation_matrix,
    x=sectors,
    y=sectors,
    annotation_text=np.array([[f"{val:.2f}" for val in row] for row in correlation_matrix]),
    colorscale="RdBu_r",
    zmid=0,
    zmin=-1,
    zmax=1,
    showscale=True,
    hovertemplate="%{x} vs %{y}<br>Correlation: %{z:.2f}<extra></extra>",
)

# Update annotation font size and auto-contrast colors
for i, annotation in enumerate(fig.layout.annotations):
    annotation.font.size = 18
    # Get the value from the corresponding cell
    row = i // n_sectors
    col = i % n_sectors
    val = correlation_matrix[row, col]
    # Use white text for dark backgrounds, black for light
    annotation.font.color = "white" if abs(val) > 0.5 else "black"

# Add colorbar configuration
fig.data[0].colorbar = dict(
    title=dict(text="Correlation", font=dict(size=20)), tickfont=dict(size=16), thickness=30, len=0.8
)

# Layout styling for 4800x2700 px
fig.update_layout(
    title=dict(
        text="Sector Correlation Matrix · heatmap-annotated · plotly · pyplots.ai",
        font=dict(size=32),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(title=dict(text="Sector", font=dict(size=24)), tickfont=dict(size=18), tickangle=45, side="bottom"),
    yaxis=dict(title=dict(text="Sector", font=dict(size=24)), tickfont=dict(size=18), autorange="reversed"),
    template="plotly_white",
    margin=dict(l=150, r=100, t=120, b=150),
)

# Reverse y-axis to show matrix conventionally
fig.update_yaxes(autorange="reversed")

# Make cells square
fig.update_xaxes(scaleanchor="y", constrain="domain")

# Save PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
