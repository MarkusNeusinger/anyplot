""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Generate realistic S-N curve data for steel specimen
np.random.seed(42)

# Material properties (typical structural steel in MPa)
ultimate_strength = 500
yield_strength = 350
endurance_limit = 200

# Generate data points at different stress levels
stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 240, 220, 210])

# Base cycles following Basquin equation: S = A * N^b (b typically -0.05 to -0.15)
# Rearranged: N = (S/A)^(1/b)
A = 800
b = -0.10
base_cycles = (stress_levels / A) ** (1 / b)

# Generate multiple test specimens per stress level with scatter
all_stress = []
all_cycles = []
for stress, base_N in zip(stress_levels, base_cycles, strict=True):
    n_specimens = np.random.randint(3, 6)
    scatter = np.random.lognormal(0, 0.15, n_specimens)
    cycles = base_N * scatter
    all_stress.extend([stress] * n_specimens)
    all_cycles.extend(cycles)

df = pd.DataFrame({"stress": all_stress, "cycles": all_cycles})

# Create fit line data
fit_cycles = np.logspace(2, 7, 100)
fit_stress = A * fit_cycles**b

df_fit = pd.DataFrame({"cycles": fit_cycles, "stress": fit_stress})

# Create the S-N curve plot
plot = (
    ggplot()  # noqa: F405
    # Basquin fit line
    + geom_line(  # noqa: F405
        data=df_fit,
        mapping=aes(x="cycles", y="stress"),  # noqa: F405
        color="#306998",
        size=2,
        alpha=0.8,
    )
    # Data points with tooltips
    + geom_point(  # noqa: F405
        data=df,
        mapping=aes(x="cycles", y="stress"),  # noqa: F405
        color="#306998",
        size=5,
        alpha=0.7,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Cycles|@cycles")
        .line("Stress|@stress MPa"),
    )
    # Reference lines for material properties
    + geom_hline(yintercept=ultimate_strength, color="#DC2626", size=1.5, linetype="dashed")  # noqa: F405
    + geom_hline(yintercept=yield_strength, color="#B8860B", size=1.5, linetype="dashed")  # noqa: F405
    + geom_hline(yintercept=endurance_limit, color="#22C55E", size=1.5, linetype="dashed")  # noqa: F405
    # Labels for reference lines (positioned on left side)
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"cycles": [200], "stress": [ultimate_strength * 1.04], "label": ["Ultimate Strength"]}),
        mapping=aes(x="cycles", y="stress", label="label"),  # noqa: F405
        color="#DC2626",
        size=14,
        hjust=0,
    )
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"cycles": [200], "stress": [yield_strength * 1.04], "label": ["Yield Strength"]}),
        mapping=aes(x="cycles", y="stress", label="label"),  # noqa: F405
        color="#B8860B",
        size=14,
        hjust=0,
    )
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"cycles": [200], "stress": [endurance_limit * 1.04], "label": ["Endurance Limit"]}),
        mapping=aes(x="cycles", y="stress", label="label"),  # noqa: F405
        color="#22C55E",
        size=14,
        hjust=0,
    )
    # Scales - log on both axes
    + scale_x_log10()  # noqa: F405
    + scale_y_log10()  # noqa: F405
    # Labels
    + labs(  # noqa: F405
        title="sn-curve-basic · letsplot · pyplots.ai", x="Number of Cycles to Failure (N)", y="Stress Amplitude (MPa)"
    )
    # Theme
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        panel_grid=element_line(color="#CCCCCC", size=0.5, linetype="dashed"),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
