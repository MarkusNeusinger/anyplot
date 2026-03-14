"""pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-14
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

# Inversion region: shade between inverted curve and the 10Y yield baseline
# Shows where short-term rates exceed the long-term benchmark
ten_year_yield = yields_inverted[8]  # 10Y = 1.52%
inv_mat = [maturity_years[i] for i in range(9)]  # 1M through 10Y
inv_upper = [yields_inverted[i] for i in range(9)]
inv_lower = [ten_year_yield] * 9
inversion_df = pd.DataFrame({"maturity_years": inv_mat, "y_upper": inv_upper, "y_lower": inv_lower})

# Reduce x-axis labels to avoid overlap at short maturities
tick_positions = [0.25, 1, 2, 5, 10, 20, 30]
tick_labels = ["3M", "1Y", "2Y", "5Y", "10Y", "20Y", "30Y"]

# Colorblind-safe palette: blue, amber, teal-green
colors = ["#306998", "#E69F00", "#009E73"]

plot = (
    ggplot()  # noqa: F405
    # Inversion region highlight — ribbon between inverted curve and 10Y baseline
    + geom_ribbon(  # noqa: F405
        data=inversion_df,
        mapping=aes(x="maturity_years", ymin="y_lower", ymax="y_upper"),  # noqa: F405
        fill="#C44E52",
        alpha=0.2,
    )
    # Yield curve lines with tooltips
    + geom_line(  # noqa: F405
        data=df,
        mapping=aes(x="maturity_years", y="yield_pct", color="date"),  # noqa: F405
        size=2.5,
        tooltips=layer_tooltips()  # noqa: F405
        .line("@date")
        .line("Maturity: @maturity")
        .line("Yield: @yield_pct%"),
    )
    + geom_point(  # noqa: F405
        data=df,
        mapping=aes(x="maturity_years", y="yield_pct", color="date"),  # noqa: F405
        size=5,
        alpha=0.85,
    )
    # Annotation for inversion region
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=pd.DataFrame({"x": [1.5], "y": [2.18], "label": ["Inversion Region"]}),
        color="#C44E52",
        size=12,
        fontface="italic",
    )
    + scale_color_manual(values=colors)  # noqa: F405
    + scale_x_continuous(breaks=tick_positions, labels=tick_labels)  # noqa: F405
    + labs(  # noqa: F405
        x="Maturity", y="Yield (%)", title="line-yield-curve · letsplot · pyplots.ai", color=""
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
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
