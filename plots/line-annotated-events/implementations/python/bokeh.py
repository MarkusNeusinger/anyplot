"""anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 55/100 | Updated: 2026-05-16
"""

if __name__ == "__main__":
    import os
    import time
    from pathlib import Path

    import numpy as np
    import pandas as pd
    from bokeh.io import output_file, save
    from bokeh.models import ColumnDataSource, Label, Span
    from bokeh.plotting import figure
    from bokeh.resources import CDN
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=365, freq="D")
    base_trend = np.linspace(100, 180, 365)
    seasonal = 15 * np.sin(np.arange(365) * 2 * np.pi / 365)
    noise = np.cumsum(np.random.randn(365) * 0.8)
    values = base_trend + seasonal + noise

    event_dates = pd.to_datetime(["2024-02-15", "2024-05-01", "2024-07-20", "2024-09-10", "2024-11-25"])
    event_labels = ["Product Launch", "Feature Update", "Server Upgrade", "API v2 Release", "Mobile App Launch"]
    event_heights = [0.92, 0.84, 0.92, 0.84, 0.92]

    source = ColumnDataSource(data={"date": dates, "value": values})

    p = figure(
        width=4800,
        height=2700,
        title="line-annotated-events · bokeh · anyplot.ai",
        x_axis_type="datetime",
        x_axis_label="Date",
        y_axis_label="Active Users (thousands)",
    )

    p.line("date", "value", source=source, line_width=4, color="#009E73", legend_label="Daily Active Users")

    for event_date, label, h in zip(event_dates, event_labels, event_heights, strict=True):
        vline = Span(location=event_date, dimension="height", line_color="#FFD43B", line_width=3, line_dash="dashed")
        p.add_layout(vline)

        y_range = values.max() - values.min()
        y_pos = values.min() + y_range * h
        event_label = Label(
            x=event_date,
            y=y_pos,
            text=label,
            text_font_size="16pt",
            text_color=INK,
            text_font_style="bold",
            x_offset=5,
            y_offset=0,
        )
        p.add_layout(event_label)

    p.title.text_font_size = "28pt"
    p.title.text_color = INK
    p.xaxis.axis_label_text_font_size = "22pt"
    p.xaxis.axis_label_text_color = INK
    p.yaxis.axis_label_text_font_size = "22pt"
    p.yaxis.axis_label_text_color = INK
    p.xaxis.major_label_text_font_size = "18pt"
    p.xaxis.major_label_text_color = INK_SOFT
    p.yaxis.major_label_text_font_size = "18pt"
    p.yaxis.major_label_text_color = INK_SOFT
    p.xaxis.axis_line_color = INK_SOFT
    p.yaxis.axis_line_color = INK_SOFT
    p.xaxis.major_tick_line_color = INK_SOFT
    p.yaxis.major_tick_line_color = INK_SOFT

    p.xgrid.grid_line_color = INK
    p.ygrid.grid_line_color = INK
    p.xgrid.grid_line_alpha = 0.10
    p.ygrid.grid_line_alpha = 0.10

    p.legend.label_text_font_size = "18pt"
    p.legend.location = "bottom_right"
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT

    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = INK_SOFT

    p.toolbar_location = None

    output_file(f"plot-{THEME}.html")
    save(p, resources=CDN, title="line-annotated-events · bokeh · anyplot.ai")

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
