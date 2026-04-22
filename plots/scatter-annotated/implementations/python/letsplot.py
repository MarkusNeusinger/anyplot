""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Company performance metrics (neutral business context)
np.random.seed(42)

companies = [
    "Acme Corp",
    "TechFlow",
    "DataSys",
    "CloudNet",
    "NeuraTech",
    "ByteWorks",
    "InfoPlex",
    "CyberDyn",
    "QuantumAI",
    "LogiCore",
    "MegaSoft",
    "SynergyX",
    "DigiHub",
    "SmartScale",
    "CoreLogic",
]

# Revenue (millions) and growth rate (percentage)
revenue = np.random.uniform(50, 500, len(companies))
growth = np.random.uniform(5, 45, len(companies))

# Add some outliers for visual interest
revenue[4] = 480  # NeuraTech - high revenue
growth[4] = 42  # NeuraTech - high growth
revenue[8] = 120  # QuantumAI - low revenue
growth[8] = 48  # QuantumAI - exceptional growth (startup)
revenue[10] = 520  # MegaSoft - highest revenue
growth[10] = 8  # MegaSoft - low growth (mature company)

df = pd.DataFrame({"company": companies, "revenue": revenue, "growth": growth})

# Create annotated scatter plot
plot = (
    ggplot(df, aes(x="revenue", y="growth"))
    + geom_point(size=8, color="#306998", alpha=0.7)
    + geom_text(aes(label="company"), size=12, nudge_y=2.5, color="#333333")
    + scale_y_continuous(limits=[0, 55])
    + labs(
        x="Annual Revenue ($ millions)",
        y="Year-over-Year Growth (%)",
        title="scatter-annotated · lets-plot · pyplots.ai",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#cccccc", size=0.5),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML version
ggsave(plot, "plot.html", path=".")
