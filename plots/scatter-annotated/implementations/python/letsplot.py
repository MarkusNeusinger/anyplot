"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-13
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#D8D7D0" if THEME == "light" else "#3A3A36"  # INK at ~15 % over the page background

# Imprint palette: position 1 is the single series
BRAND = "#009E73"

# Columns: set these to your table's column names
COMPANY = "company"  # role: label
REVENUE = "Annual Revenue ($ millions)"  # role: x
MARGIN = "Profit Margin (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("companies.csv")
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
revenue = np.random.uniform(50, 500, len(companies))
profit_margin = np.random.uniform(5, 35, len(companies))

# A few outliers for visual interest
revenue[4], profit_margin[4] = 480, 32  # NeuraTech: high revenue, strong margins
revenue[8], profit_margin[8] = 120, 28  # QuantumAI: low revenue, good margins
revenue[10], profit_margin[10] = 520, 18  # MegaSoft: highest revenue, lower margins

df = pd.DataFrame({COMPANY: companies, REVENUE: revenue, MARGIN: profit_margin})

# Plot: reads only df and the constants above
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.5),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=16, face="bold"),
)

plot = (
    ggplot(df, aes(x=REVENUE, y=MARGIN))
    + geom_point(size=4, color=BRAND, alpha=0.7)
    + geom_text_repel(
        aes(label=COMPANY), size=4, color=INK_SOFT, point_padding=4, box_padding=1, seed=7, max_iter=300, max_time=1
    )
    + scale_y_continuous(limits=[0, df[MARGIN].max() * 1.15])
    + labs(title="scatter-annotated · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG (800 x 450 at scale 4 = 3200 x 1800 px) and HTML
_script_dir = Path(__file__).parent
ggsave(plot, f"plot-{THEME}.png", path=str(_script_dir), scale=4)
ggsave(plot, f"plot-{THEME}.html", path=str(_script_dir))
