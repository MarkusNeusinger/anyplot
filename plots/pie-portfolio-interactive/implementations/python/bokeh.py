""" anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-27
"""

import os
import sys
import time
from pathlib import Path


# Remove the script's own directory from sys.path so "bokeh" resolves to the
# installed package, not this file (which shares the name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir]

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, LabelSet, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Semantic color mapping: green=growth, blue=stable, ochre=commodity, muted=neutral cash
category_colors = {
    "Equities": IMPRINT_PALETTE[0],  # #009E73 green
    "Fixed Income": IMPRINT_PALETTE[2],  # #4467A3 blue
    "Alternatives": IMPRINT_PALETTE[3],  # #BD8233 ochre
    "Cash": INK_MUTED,  # muted neutral
}

# Portfolio data — 10 holdings across 4 asset classes
np.random.seed(42)
holdings = {
    "Equities": {
        "asset": ["Apple Inc.", "Microsoft", "Google", "Int'l Equities"],
        "weight": [18, 15, 12, 10],
        "value": [180000, 150000, 120000, 100000],
    },
    "Fixed Income": {"asset": ["US Treasury 10Y", "Corporate Bonds"], "weight": [15, 10], "value": [150000, 100000]},
    "Alternatives": {
        "asset": ["Gold ETF", "Real Estate Fund", "Commodities"],
        "weight": [5, 8, 3],
        "value": [50000, 80000, 30000],
    },
    "Cash": {"asset": ["Cash"], "weight": [4], "value": [40000]},
}

total_portfolio_value = sum(sum(v["value"]) for v in holdings.values())  # 1,000,000
categories = list(holdings.keys())

INNER_R = 0.42
OUTER_R = 0.82
LABEL_R = 1.04  # labels outside ring for both overview and detail

# --- Category overview data ---
cat_weights = np.array([sum(holdings[c]["weight"]) for c in categories])
cat_values = np.array([sum(holdings[c]["value"]) for c in categories])
cat_angles = cat_weights / cat_weights.sum() * 2 * np.pi
cat_end = np.cumsum(cat_angles) - np.pi / 2
cat_start = cat_end - cat_angles
cat_mid = (cat_start + cat_end) / 2

overview_source = ColumnDataSource(
    data={
        "category": categories,
        "weight": cat_weights.tolist(),
        "value": cat_values.tolist(),
        "color": [category_colors[c] for c in categories],
        "start_angle": cat_start.tolist(),
        "end_angle": cat_end.tolist(),
        "label_x": (LABEL_R * np.cos(cat_mid)).tolist(),
        "label_y": (LABEL_R * np.sin(cat_mid)).tolist(),
        "label_text": [f"{c}\n{w}%" for c, w in zip(categories, cat_weights.tolist(), strict=True)],
    }
)

# --- Pre-computed per-category holdings data (passed to JS) ---
detail_data_js = {}
for cat in categories:
    ws = np.array(holdings[cat]["weight"])
    angs = ws / ws.sum() * 2 * np.pi
    ends = np.cumsum(angs) - np.pi / 2
    starts = ends - angs
    mids = (starts + ends) / 2
    detail_data_js[cat] = {
        "asset": holdings[cat]["asset"],
        "weight": ws.tolist(),
        "value": holdings[cat]["value"],
        "category": [cat] * len(ws),
        "color": [category_colors[cat]] * len(ws),
        "start_angle": starts.tolist(),
        "end_angle": ends.tolist(),
        "label_x": (LABEL_R * np.cos(mids)).tolist(),
        "label_y": (LABEL_R * np.sin(mids)).tolist(),
        "total_value": sum(holdings[cat]["value"]),
        "total_weight": int(ws.sum()),
    }

# --- Detail source (initially hidden, populated by JS) ---
detail_source = ColumnDataSource(
    data={
        "asset": [""],
        "weight": [0.0],
        "value": [0],
        "category": [""],
        "color": [category_colors["Equities"]],
        "start_angle": [0.0],
        "end_angle": [0.0],
        "label_x": [0.0],
        "label_y": [0.0],
    }
)

# Center label sources — updated by JS callback on drill-down
center_header_source = ColumnDataSource(data={"x": [0], "y": [0.12], "text": ["Total Portfolio"]})
center_value_source = ColumnDataSource(data={"x": [0], "y": [-0.08], "text": [f"${total_portfolio_value:,.0f}"]})

# --- Figure ---
W, H = 2400, 2400
title = "pie-portfolio-interactive · python · bokeh · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_pt = max(34, round(50 * ratio))

p = figure(
    width=W, height=H, title=title, x_range=(-1.38, 1.38), y_range=(-1.38, 1.38), tools="tap", toolbar_location=None
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.axis.visible = False
p.grid.visible = False

p.title.text_font_size = f"{title_pt}pt"
p.title.text_color = INK
p.title.align = "center"

# --- Overview layer: 4 category wedges ---
overview_glyph = p.annular_wedge(
    x=0,
    y=0,
    inner_radius=INNER_R,
    outer_radius=OUTER_R,
    start_angle="start_angle",
    end_angle="end_angle",
    color="color",
    alpha=0.92,
    source=overview_source,
    line_color=PAGE_BG,
    line_width=6,
    hover_fill_alpha=1.0,
    hover_line_color=INK,
    hover_line_width=8,
    name="overview_wedge",
)

overview_labels = LabelSet(
    x="label_x",
    y="label_y",
    text="label_text",
    source=overview_source,
    text_font_size="34pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
)
p.add_layout(overview_labels)

# HoverTool scoped to overview wedge
overview_hover = HoverTool(
    renderers=[overview_glyph],
    tooltips=[("Asset Class", "@category"), ("Total Weight", "@weight{0.0}%"), ("Total Value", "$$@value{0,0}")],
    mode="mouse",
)
p.add_tools(overview_hover)

# --- Detail layer: individual holdings of selected category ---
detail_glyph = p.annular_wedge(
    x=0,
    y=0,
    inner_radius=INNER_R,
    outer_radius=OUTER_R,
    start_angle="start_angle",
    end_angle="end_angle",
    color="color",
    alpha=0.92,
    source=detail_source,
    line_color=PAGE_BG,
    line_width=6,
    hover_fill_alpha=1.0,
    hover_line_color=INK,
    hover_line_width=8,
    name="detail_wedge",
    visible=False,
)

detail_labels = LabelSet(
    x="label_x",
    y="label_y",
    text="asset",
    source=detail_source,
    text_font_size="34pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
    visible=False,
)
p.add_layout(detail_labels)

detail_hover = HoverTool(
    renderers=[detail_glyph],
    tooltips=[("Asset", "@asset"), ("Category", "@category"), ("Weight", "@weight{0.0}%"), ("Value", "$$@value{0,0}")],
    mode="mouse",
)
p.add_tools(detail_hover)

# Center label: "Total Portfolio" header + value
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=center_header_source,
        text_font_size="26pt",
        text_align="center",
        text_baseline="middle",
        text_color=INK_SOFT,
    )
)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=center_value_source,
        text_font_size="34pt",
        text_align="center",
        text_baseline="middle",
        text_color=INK,
        text_font_style="bold",
    )
)

# --- Legend (inside plot, top-right) ---
legend_items = []
for cat, color in category_colors.items():
    dummy = ColumnDataSource(data={"x": [9999], "y": [9999]})
    r = p.scatter(x="x", y="y", size=20, color=color, source=dummy, marker="square")
    legend_items.append(LegendItem(label=cat, renderers=[r]))

legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "34pt"
legend.label_text_color = INK_SOFT
legend.glyph_width = 44
legend.glyph_height = 44
legend.spacing = 18
legend.padding = 28
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.92
legend.border_line_color = INK_SOFT
legend.border_line_width = 1
p.add_layout(legend)

# --- JS Callback: click overview category → drill into its holdings ---
drill_callback = CustomJS(
    args={
        "overview_source": overview_source,
        "detail_source": detail_source,
        "center_header": center_header_source,
        "center_value": center_value_source,
        "overview_glyph": overview_glyph,
        "overview_labels": overview_labels,
        "detail_glyph": detail_glyph,
        "detail_labels": detail_labels,
        "all_details": detail_data_js,
        "total_portfolio": total_portfolio_value,
    },
    code="""
    const indices = overview_source.selected.indices;
    if (indices.length === 0) return;
    const idx = indices[0];
    const cat = overview_source.data["category"][idx];
    overview_source.selected.indices = [];

    const det = all_details[cat];

    // Populate detail source with holdings of selected category
    detail_source.data = {
        "asset": det.asset,
        "weight": det.weight,
        "value": det.value,
        "category": det.category,
        "color": det.color,
        "start_angle": det.start_angle,
        "end_angle": det.end_angle,
        "label_x": det.label_x,
        "label_y": det.label_y,
    };
    detail_source.change.emit();

    // Switch to detail view
    overview_glyph.visible = false;
    overview_labels.visible = false;
    detail_glyph.visible = true;
    detail_labels.visible = true;

    // Update center labels to show category totals
    center_header.data = {"x": [0], "y": [0.12], "text": [cat]};
    center_value.data = {"x": [0], "y": [-0.08], "text": ["$" + det.total_value.toLocaleString() + " (" + det.total_weight + "%)"]};
    center_header.change.emit();
    center_value.change.emit();

    // Show or create the Back to Overview button
    let btn = document.getElementById('ap-back-btn');
    if (!btn) {
        btn = document.createElement('button');
        btn.id = 'ap-back-btn';
        btn.textContent = '← Back to Overview';
        btn.style.cssText = [
            'position:fixed', 'top:24px', 'left:24px',
            'background:#009E73', 'color:#fff',
            'border:none', 'border-radius:6px',
            'padding:10px 22px', 'font-size:17px',
            'font-weight:600', 'cursor:pointer',
            'z-index:1000', 'font-family:system-ui,sans-serif',
            'box-shadow:0 3px 12px rgba(0,0,0,0.22)'
        ].join(';');
        document.body.appendChild(btn);

        btn.addEventListener('click', function() {
            // Restore category overview
            overview_glyph.visible = true;
            overview_labels.visible = true;
            detail_glyph.visible = false;
            detail_labels.visible = false;

            center_header.data = {"x": [0], "y": [0.12], "text": ["Total Portfolio"]};
            center_value.data = {"x": [0], "y": [-0.08], "text": ["$" + total_portfolio.toLocaleString()]};
            center_header.change.emit();
            center_value.change.emit();

            detail_source.selected.indices = [];
            detail_source.change.emit();

            btn.style.display = 'none';
        });
    }
    btn.style.display = 'block';
""",
)
overview_source.selected.js_on_change("indices", drill_callback)

# Save interactive HTML
output_file(f"plot-{THEME}.html", title="Interactive Portfolio Allocation Chart")
save(p)

# Screenshot with headless Chrome — use driver.save_screenshot() per library guide
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
