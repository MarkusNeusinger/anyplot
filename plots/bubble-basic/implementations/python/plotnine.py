"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: plotnine 0.15.8 | Python 3.13.15
Quality: 83/100 | Updated: 2026-09-27
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_smooth,
    ggplot,
    guide_legend,
    labs,
    scale_fill_manual,
    scale_size_area,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — countries across 4 regions: GDP per capita, life expectancy, population
np.random.seed(42)

regions = ["Asia-Pacific", "Europe", "Americas", "Middle East & Africa"]
region_params = {
    "Asia-Pacific": {"n": 18, "gdp_mean": 25, "gdp_std": 18, "le_base": 72, "pop_mean": 3.6},
    "Europe": {"n": 18, "gdp_mean": 45, "gdp_std": 15, "le_base": 78, "pop_mean": 2.6},
    "Americas": {"n": 18, "gdp_mean": 30, "gdp_std": 20, "le_base": 70, "pop_mean": 3.2},
    "Middle East & Africa": {"n": 18, "gdp_mean": 12, "gdp_std": 10, "le_base": 62, "pop_mean": 3.0},
}

rows = []
for region, p in region_params.items():
    gdp = np.abs(np.random.normal(p["gdp_mean"], p["gdp_std"], p["n"]))
    gdp = np.clip(gdp, 3, 85)
    le = p["le_base"] + 0.15 * gdp + np.random.normal(0, 2.5, p["n"])
    le = np.clip(le, 52, 88)
    # Clip to a raised size-value floor (18-100, within the spec's 10-100 band) so
    # even the smallest bubble renders with a clearly visible radius at max_size=18
    pop = np.random.lognormal(mean=p["pop_mean"], sigma=0.55, size=p["n"])
    pop = np.clip(pop, 18, 100)
    for i in range(p["n"]):
        rows.append({"gdp_per_capita": gdp[i], "life_expectancy": le[i], "population": pop[i], "region": region})

df = pd.DataFrame(rows)
df["region"] = pd.Categorical(df["region"], categories=regions, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="gdp_per_capita", y="life_expectancy", size="population", fill="region"))
    + geom_smooth(
        aes(x="gdp_per_capita", y="life_expectancy"), method="lm", se=False, color=INK_SOFT, size=0.7, inherit_aes=False
    )
    # geom_point's default shape already splits fill (region color) from edge
    # (color); fixing color to the page bg gives each bubble a subtle halo that
    # separates it from overlapping neighbors
    + geom_point(color=PAGE_BG, alpha=0.65, stroke=0.5)
    # limits=(0, 100) anchors the area scaling to a true zero baseline; without it
    # plotnine anchors the sqrt-area formula to the data's own min, which maps the
    # smallest (floor-clipped) bubbles to a near-zero rendered size.
    # override_aes gives the size-legend's key glyphs a visible INK_SOFT fill/edge —
    # without it they'd inherit geom_point's fixed color=PAGE_BG stroke, which blends
    # into the PAGE_BG legend_key background and renders as empty boxes.
    + scale_size_area(
        max_size=18,
        breaks=[20, 50, 90],
        limits=(0, 100),
        name="Population (M)",
        guide=guide_legend(override_aes={"fill": INK_SOFT, "color": INK_SOFT, "alpha": 1}),
    )
    + scale_fill_manual(values=IMPRINT_PALETTE[:4], name="Region")
    + scale_x_continuous(labels=lambda lst: [f"${v:.0f}k" for v in lst], breaks=[10, 20, 30, 40, 50, 60, 70, 80])
    + scale_y_continuous(labels=lambda lst: [f"{v:.0f}" for v in lst])
    + labs(
        x="GDP per Capita (USD thousands)",
        y="Life Expectancy (years)",
        title="bubble-basic · python · plotnine · anyplot.ai",
        subtitle="Higher GDP per capita tracks with longer life expectancy across all four regions",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_margin_right=0.025,
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        plot_subtitle=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_key=element_rect(fill=PAGE_BG, color="none"),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
