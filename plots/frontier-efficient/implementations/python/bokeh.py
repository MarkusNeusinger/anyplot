"""anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os
import sys
import time
from pathlib import Path


# Fix for running script named bokeh.py (avoid shadowing the bokeh package)
if Path(__file__).name == "bokeh.py":
    sys.path = [p for p in sys.path if Path(__file__).parent != Path(p)]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.plotting import figure
from scipy.optimize import minimize
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    """Linear interpolation between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


# Imprint sequential ramp (single-polarity) for the Sharpe ratio
IMPRINT_SEQ256 = [lerp_hex("#009E73", "#4467A3", i / 255) for i in range(256)]

# Constants
RISK_FREE_RATE = 0.02  # annual rate of the riskless asset behind Sharpe ratio and capital market line

# Columns: set these to your table's column names
RISK = "Risk (standard deviation)"  # role: risk
RETURN = "Expected return"  # role: return
EFFICIENT = "On efficient frontier"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("portfolios.csv")
np.random.seed(42)
asset_returns = np.array([0.04, 0.10, 0.12, 0.09, 0.07])
asset_vols = np.array([0.05, 0.18, 0.25, 0.20, 0.22])
asset_corr = np.array(
    [
        [1.00, 0.20, 0.15, 0.10, 0.05],
        [0.20, 1.00, 0.85, 0.70, 0.30],
        [0.15, 0.85, 1.00, 0.65, 0.35],
        [0.10, 0.70, 0.65, 1.00, 0.40],
        [0.05, 0.30, 0.35, 0.40, 1.00],
    ]
)
asset_cov = np.outer(asset_vols, asset_vols) * asset_corr
n_assets = len(asset_returns)


def port_risk(w):
    return np.sqrt(w @ asset_cov @ w)


# 300 random long-only portfolios
weights = np.random.random((300, n_assets))
weights /= weights.sum(axis=1, keepdims=True)
rand_ret = weights @ asset_returns
rand_risk = np.array([port_risk(w) for w in weights])

# Efficient frontier: minimum risk for each target return, from the minimum-variance portfolio up
bounds = [(0, 1)] * n_assets
start = np.full(n_assets, 1 / n_assets)
min_var = minimize(
    port_risk, start, method="SLSQP", bounds=bounds, constraints={"type": "eq", "fun": lambda w: w.sum() - 1}
)
front_ret, front_risk = [], []
for target in np.linspace(min_var.x @ asset_returns, asset_returns.max(), 120):
    cons = (
        {"type": "eq", "fun": lambda w: w.sum() - 1},
        {"type": "eq", "fun": lambda w, t=target: w @ asset_returns - t},
    )
    res = minimize(port_risk, start, method="SLSQP", bounds=bounds, constraints=cons)
    if res.success:
        front_ret.append(res.x @ asset_returns)
        front_risk.append(port_risk(res.x))

df = pd.DataFrame(
    {
        RISK: np.concatenate([front_risk, rand_risk]),
        RETURN: np.concatenate([front_ret, rand_ret]),
        EFFICIENT: [True] * len(front_ret) + [False] * len(rand_ret),
    }
)

# Plot: reads only df and the constants above
on_frontier = df[EFFICIENT].fillna(False).astype(bool)
random_df = df[~on_frontier].dropna(subset=[RISK, RETURN]).copy()
random_df["sharpe"] = (random_df[RETURN] - RISK_FREE_RATE) / random_df[RISK]
frontier_df = df[on_frontier].dropna(subset=[RISK, RETURN]).sort_values(RISK)

# Key portfolios chosen by rule over the frontier
min_var_row = frontier_df.loc[frontier_df[RISK].idxmin()]
frontier_sharpe = (frontier_df[RETURN] - RISK_FREE_RATE) / frontier_df[RISK]
max_sharpe_row = frontier_df.loc[frontier_sharpe.idxmax()]
max_sharpe = frontier_sharpe.max()

# Capital market line: from the risk-free rate at zero risk through the tangency portfolio
cml_end = df[RISK].max() * 1.05
cml_x = [0.0, cml_end]
cml_y = [RISK_FREE_RATE, RISK_FREE_RATE + max_sharpe * cml_end]

# Sharpe ratio -> sequential Imprint color
s_low, s_high = random_df["sharpe"].min(), random_df["sharpe"].max()
span = (s_high - s_low) or 1.0
idx = ((random_df["sharpe"] - s_low) / span * 255).round().astype(int)
random_df["color"] = [IMPRINT_SEQ256[i] for i in idx]

p = figure(
    width=3200,
    height=1800,
    title="frontier-efficient · python · bokeh · anyplot.ai",
    x_axis_label=RISK,
    y_axis_label=RETURN,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.scatter(
    RISK,
    RETURN,
    source=ColumnDataSource(random_df),
    size=24,
    color="color",
    alpha=0.75,
    line_color=PAGE_BG,
    line_width=1,
)

# CML first so the frontier and key markers sit on top
p.line(
    cml_x,
    cml_y,
    line_width=5,
    line_dash="dashed",
    color=INK_SOFT,
    legend_label=f"Capital market line (rf = {RISK_FREE_RATE:.0%})",
)
p.line(
    RISK,
    RETURN,
    source=ColumnDataSource(frontier_df),
    line_width=10,
    color=IMPRINT_PALETTE[0],
    legend_label="Efficient frontier",
)
p.scatter(
    [min_var_row[RISK]],
    [min_var_row[RETURN]],
    size=70,
    marker="star",
    color=IMPRINT_PALETTE[3],
    line_color=INK,
    line_width=3,
    legend_label="Minimum variance",
)
p.scatter(
    [max_sharpe_row[RISK]],
    [max_sharpe_row[RETURN]],
    size=60,
    marker="diamond",
    color=IMPRINT_PALETTE[1],
    line_color=INK,
    line_width=3,
    legend_label=f"Maximum Sharpe ({max_sharpe:.2f})",
)

# Style
title_pt = round(50 * min(1.0, 67 / len(p.title.text)))
p.title.text_font_size = f"{title_pt}pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xaxis.formatter.use_scientific = False
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.legend.location = "bottom_right"
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.glyph_height = 36
p.legend.glyph_width = 50
p.legend.spacing = 10
p.legend.padding = 18

color_bar = ColorBar(
    color_mapper=LinearColorMapper(palette=IMPRINT_SEQ256, low=s_low, high=s_high),
    title="Sharpe ratio",
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="30pt",
    major_label_text_color=INK_SOFT,
    label_standoff=15,
    width=50,
    background_fill_color=PAGE_BG,
    major_tick_line_color=INK_SOFT,
    bar_line_color=INK_SOFT,
)
p.add_layout(color_bar, "right")

# Save HTML + screenshot
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
