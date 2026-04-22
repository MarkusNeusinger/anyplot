""" pyplots.ai
rug-basic: Basic Rug Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - bimodal distribution showing clustering patterns and gaps
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(25, 5, 60),  # Dense cluster around 25
        np.random.normal(55, 8, 40),  # Sparser cluster around 55
    ]
)

df = pd.DataFrame(
    {
        "values": values,
        "y": [0] * len(values),  # Base of tick marks
        "y2": [1] * len(values),  # Top of tick marks (relative height)
    }
)

# Create rug plot using rule marks positioned at bottom
rug = (
    alt.Chart(df)
    .mark_rule(strokeWidth=3, opacity=0.6, color="#306998")
    .encode(
        x=alt.X("values:Q", title="Measurement Value", scale=alt.Scale(domain=[5, 80])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 10]), axis=None),
        y2="y2:Q",
    )
)

# Configure chart with 16:9 aspect ratio (1600x900 * scale_factor=3 = 4800x2700)
chart = (
    rug.properties(width=1600, height=900, title=alt.Title("rug-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, tickSize=10, gridOpacity=0.3)
    .configure_view(strokeWidth=1)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
