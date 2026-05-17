""" anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os
import sys
import time
from pathlib import Path

import numpy as np


# Workaround for bokeh.py shadowing: clear current dir from sys.path and inject site-packages at beginning
_site_packages = next((p for p in sys.path if "site-packages" in p), None)
sys.path = [p for p in sys.path if not (p == "" or p == "." or "site-packages" in p)]
if _site_packages:
    sys.path.insert(0, _site_packages)


def main():
    """Main implementation function to avoid module name shadowing."""
    from bokeh.io import output_file, save
    from bokeh.models import ColumnDataSource, HoverTool, Whisker
    from bokeh.palettes import Cividis256
    from bokeh.plotting import figure
    from bokeh.transform import linear_cmap
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    # Theme tokens
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

    # Data: Simulated permutation importance results
    np.random.seed(42)

    features = [
        "Square Footage",
        "Number of Bedrooms",
        "Neighborhood Score",
        "Year Built",
        "Lot Size",
        "Distance to City Center",
        "Number of Bathrooms",
        "Garage Capacity",
        "School Rating",
        "Crime Index",
        "Property Tax Rate",
        "Previous Sale Price",
        "Days on Market",
        "Walk Score",
        "Public Transit Access",
    ]

    # Generate importance values (higher = more important)
    importance_mean = np.array(
        [0.182, 0.145, 0.128, 0.095, 0.078, 0.065, 0.052, 0.041, 0.035, 0.028, 0.018, 0.012, 0.005, -0.003, -0.008]
    )

    # Standard deviations (variability across shuffles)
    importance_std = np.array(
        [0.025, 0.022, 0.020, 0.018, 0.015, 0.014, 0.012, 0.011, 0.010, 0.009, 0.008, 0.007, 0.006, 0.005, 0.004]
    )

    # Sort by importance (highest first)
    sort_idx = np.argsort(importance_mean)[::-1]
    features_sorted = [features[i] for i in sort_idx]
    importance_mean_sorted = importance_mean[sort_idx]
    importance_std_sorted = importance_std[sort_idx]

    # Reverse for plotting (highest at top)
    features_plot = features_sorted[::-1]
    importance_mean_plot = importance_mean_sorted[::-1]
    importance_std_plot = importance_std_sorted[::-1]

    # Create data source
    source = ColumnDataSource(
        data={
            "features": features_plot,
            "importance": importance_mean_plot,
            "std": importance_std_plot,
            "upper": importance_mean_plot + importance_std_plot,
            "lower": importance_mean_plot - importance_std_plot,
        }
    )

    # Create figure with categorical y-axis
    p = figure(
        width=4800,
        height=2700,
        y_range=features_plot,
        x_axis_label="Mean Decrease in Model Score",
        title="bar-permutation-importance · bokeh · anyplot.ai",
    )

    # Color mapper for bars (darker = more important)
    mapper = linear_cmap(
        field_name="importance", palette=Cividis256, low=min(importance_mean_plot), high=max(importance_mean_plot)
    )

    # Draw horizontal bars
    p.hbar(
        y="features",
        right="importance",
        left=0,
        height=0.7,
        source=source,
        fill_color=mapper,
        line_color=INK_SOFT,
        line_width=1,
    )

    # Add error bars (whiskers)
    whisker = Whisker(
        source=source,
        base="features",
        upper="upper",
        lower="lower",
        dimension="width",
        line_color=INK_SOFT,
        line_width=2,
        upper_head=None,
        lower_head=None,
    )
    p.add_layout(whisker)

    # Add vertical reference line at x=0
    p.line(x=[0, 0], y=[-1, len(features_plot)], line_color=INK_SOFT, line_width=2, line_dash="dashed")

    # Add hover tool
    hover = HoverTool(
        tooltips=[("Feature", "@features"), ("Importance", "@importance{0.000}"), ("Std Dev", "@std{0.000}")]
    )
    p.add_tools(hover)

    # Styling
    p.title.text_font_size = "28pt"
    p.title.text_font_style = "bold"
    p.title.text_color = INK
    p.xaxis.axis_label_text_font_size = "22pt"
    p.yaxis.axis_label_text_font_size = "22pt"
    p.xaxis.axis_label_text_color = INK
    p.yaxis.axis_label_text_color = INK
    p.xaxis.major_label_text_font_size = "18pt"
    p.yaxis.major_label_text_font_size = "18pt"
    p.xaxis.major_label_text_color = INK_SOFT
    p.yaxis.major_label_text_color = INK_SOFT

    # Grid styling
    p.xgrid.grid_line_color = INK
    p.xgrid.grid_line_alpha = 0.10
    p.ygrid.grid_line_color = None

    # Axis styling
    p.xaxis.axis_line_color = INK_SOFT
    p.yaxis.axis_line_color = INK_SOFT
    p.xaxis.axis_line_width = 1
    p.yaxis.axis_line_width = 1
    p.outline_line_color = INK_SOFT
    p.outline_line_width = 1

    # Background
    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG

    # Save HTML
    output_file(f"plot-{THEME}.html")
    save(p)

    # Screenshot with headless Chrome using Selenium
    W, H = 4800, 2700
    opts = Options()
    for arg in (
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        f"--window-size={W},{H}",
        "--hide-scrollbars",
    ):
        opts.add_argument(arg)
    driver = webdriver.Chrome(options=opts)
    driver.set_window_size(W, H)
    driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
    time.sleep(3)
    driver.save_screenshot(f"plot-{THEME}.png")
    driver.quit()


if __name__ == "__main__":
    main()
