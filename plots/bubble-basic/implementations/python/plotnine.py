""" pyplots.ai
bubble-basic: Basic Bubble Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_size_area,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — cities across 4 regions with well-spread GDP distribution
np.random.seed(42)

regions = ["Asia-Pacific", "Europe", "Americas", "Middle East & Africa"]
region_params = {
    "Asia-Pacific": {"n": 10, "gdp_mean": 25, "gdp_std": 18, "le_base": 72, "pop_mean": 3.2},
    "Europe": {"n": 10, "gdp_mean": 45, "gdp_std": 15, "le_base": 78, "pop_mean": 2.0},
    "Americas": {"n": 10, "gdp_mean": 30, "gdp_std": 20, "le_base": 70, "pop_mean": 2.8},
    "Middle East & Africa": {"n": 10, "gdp_mean": 12, "gdp_std": 10, "le_base": 62, "pop_mean": 2.5},
}

rows = []
for region, p in region_params.items():
    gdp = np.abs(np.random.normal(p["gdp_mean"], p["gdp_std"], p["n"]))
    gdp = np.clip(gdp, 3, 85)
    le = p["le_base"] + 0.15 * gdp + np.random.normal(0, 2.5, p["n"])
    le = np.clip(le, 52, 88)
    pop = np.random.lognormal(mean=p["pop_mean"], sigma=0.8, size=p["n"])
    for i in range(p["n"]):
        rows.append({"gdp_per_capita": gdp[i], "life_expectancy": le[i], "population": pop[i], "region": region})

df = pd.DataFrame(rows)
df["region"] = pd.Categorical(df["region"], categories=regions, ordered=True)

# Custom palette starting with Python Blue
palette = ["#306998", "#E3784A", "#4DAF4A", "#B07CC6"]

# Plot
plot = (
    ggplot(df, aes(x="gdp_per_capita", y="life_expectancy", size="population", color="region"))
    + geom_point(alpha=0.65)
    + scale_size_area(max_size=24, breaks=[5, 25, 75], name="Population (M)")
    + scale_color_manual(values=palette, name="Region")
    + scale_x_continuous(labels=lambda lst: [f"${v:.0f}k" for v in lst], breaks=[10, 20, 30, 40, 50, 60, 70, 80])
    + scale_y_continuous(labels=lambda lst: [f"{v:.0f}" for v in lst])
    + labs(
        x="GDP per Capita (USD thousands)", y="Life Expectancy (years)", title="bubble-basic · plotnine · pyplots.ai"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2d2d2d"),
        axis_title=element_text(size=20, margin={"t": 12, "r": 12}),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, weight="bold", margin={"b": 16}),
        legend_title=element_text(size=18, weight="bold"),
        legend_text=element_text(size=16),
        legend_key=element_rect(fill="white", color="none"),
        panel_grid_major=element_line(color="#e0e0e0", size=0.4),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
