""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

from pathlib import Path

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

# Data - Simulated stock daily returns (realistic financial scenario)
np.random.seed(42)
# Mix of normal returns with slightly heavier tails (leptokurtic)
returns = np.concatenate(
    [
        np.random.normal(0.001, 0.015, 400),  # Normal market days
        np.random.normal(-0.02, 0.03, 50),  # Volatile down days
        np.random.normal(0.02, 0.025, 50),  # Volatile up days
    ]
)
returns = returns * 100  # Convert to percentage

df = pd.DataFrame({"Daily Return (%)": returns})

# Plot - Histogram with KDE overlay
plot = (
    ggplot(df, aes(x="Daily Return (%)"))  # noqa: F405
    + geom_histogram(  # noqa: F405
        aes(y="..density.."),  # noqa: F405
        bins=35,
        fill="#306998",
        alpha=0.5,
        color="#1e4263",
        size=0.5,  # noqa: F405
    )
    + geom_density(color="#FFD43B", size=2, fill="rgba(0,0,0,0)")  # noqa: F405
    + labs(x="Daily Return (%)", y="Density", title="histogram-kde · letsplot · pyplots.ai")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        panel_grid_major=element_line(color="#cccccc", size=0.5),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x for 4800 × 2700 px)
output_dir = Path(__file__).parent
ggsave(plot, str(output_dir / "plot.png"), scale=3)  # noqa: F405

# Save interactive HTML
ggsave(plot, str(output_dir / "plot.html"))  # noqa: F405
