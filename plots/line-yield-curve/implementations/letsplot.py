"""pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - U.S. Treasury yield curves on three dates
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = [1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

# Normal upward-sloping curve (Jan 2018)
yields_normal = [1.28, 1.53, 1.72, 1.89, 2.05, 2.19, 2.41, 2.55, 2.66, 2.83, 2.96]

# Inverted curve (Aug 2019 - recession signal)
yields_inverted = [2.09, 2.00, 1.92, 1.75, 1.52, 1.46, 1.44, 1.48, 1.52, 1.77, 1.97]

# Steep post-pandemic curve (Mar 2021)
yields_steep = [0.03, 0.03, 0.04, 0.07, 0.14, 0.32, 0.83, 1.18, 1.62, 2.19, 2.35]

rows = []
for i in range(len(maturities)):
    rows.append(
        {
            "maturity": maturities[i],
            "maturity_years": maturity_years[i],
            "yield_pct": yields_normal[i],
            "date": "Jan 2018 (Normal)",
        }
    )
    rows.append(
        {
            "maturity": maturities[i],
            "maturity_years": maturity_years[i],
            "yield_pct": yields_inverted[i],
            "date": "Aug 2019 (Inverted)",
        }
    )
    rows.append(
        {
            "maturity": maturities[i],
            "maturity_years": maturity_years[i],
            "yield_pct": yields_steep[i],
            "date": "Mar 2021 (Steep)",
        }
    )

df = pd.DataFrame(rows)

# Plot
colors = ["#306998", "#C44E52", "#55A868"]

plot = (
    ggplot(df, aes(x="maturity_years", y="yield_pct", color="date"))  # noqa: F405
    + geom_line(size=2.5)  # noqa: F405
    + geom_point(size=5, alpha=0.85)  # noqa: F405
    + scale_color_manual(values=colors)  # noqa: F405
    + scale_x_continuous(  # noqa: F405
        breaks=maturity_years, labels=maturities
    )
    + labs(  # noqa: F405
        x="Maturity",
        y="Yield (%)",
        title="U.S. Treasury Yield Curves · line-yield-curve · letsplot · pyplots.ai",
        color="",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=22),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position="top",
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),  # noqa: F405
    )
)

# Save
export_ggsave(plot, "plot.png", path=".", scale=3)
export_ggsave(plot, "plot.html", path=".")
