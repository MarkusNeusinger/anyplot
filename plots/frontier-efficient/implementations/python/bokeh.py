""" pyplots.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from scipy.optimize import minimize


# Set seed for reproducibility
np.random.seed(42)

# Generate realistic asset data (5 assets)
n_assets = 5

# Expected returns (annualized)
expected_returns = np.array([0.04, 0.10, 0.12, 0.09, 0.07])

# Covariance matrix (realistic correlations)
volatilities = np.array([0.05, 0.18, 0.25, 0.20, 0.22])
correlations = np.array(
    [
        [1.00, 0.20, 0.15, 0.10, 0.05],
        [0.20, 1.00, 0.85, 0.70, 0.30],
        [0.15, 0.85, 1.00, 0.65, 0.35],
        [0.10, 0.70, 0.65, 1.00, 0.40],
        [0.05, 0.30, 0.35, 0.40, 1.00],
    ]
)
cov_matrix = np.outer(volatilities, volatilities) * correlations
risk_free_rate = 0.02


def portfolio_return(weights):
    return np.dot(weights, expected_returns)


def portfolio_risk(weights):
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))


def neg_sharpe_ratio(weights):
    ret = portfolio_return(weights)
    risk = portfolio_risk(weights)
    return -(ret - risk_free_rate) / risk


# Generate random portfolios
n_portfolios = 300
portfolio_returns = []
portfolio_risks = []
portfolio_sharpes = []

for _ in range(n_portfolios):
    weights = np.random.random(n_assets)
    weights /= weights.sum()

    ret = portfolio_return(weights)
    risk = portfolio_risk(weights)
    sharpe = (ret - risk_free_rate) / risk

    portfolio_returns.append(ret)
    portfolio_risks.append(risk)
    portfolio_sharpes.append(sharpe)

portfolio_returns = np.array(portfolio_returns)
portfolio_risks = np.array(portfolio_risks)
portfolio_sharpes = np.array(portfolio_sharpes)

# Calculate efficient frontier using scipy optimization
constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
bounds = tuple((0, 1) for _ in range(n_assets))
init_weights = np.array([1 / n_assets] * n_assets)

# Find minimum variance portfolio
min_var_result = minimize(portfolio_risk, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
min_var_weights = min_var_result.x
min_var_return = portfolio_return(min_var_weights)
min_var_risk = portfolio_risk(min_var_weights)

# Find maximum Sharpe ratio portfolio
max_sharpe_result = minimize(neg_sharpe_ratio, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
max_sharpe_weights = max_sharpe_result.x
max_sharpe_return = portfolio_return(max_sharpe_weights)
max_sharpe_risk = portfolio_risk(max_sharpe_weights)
max_sharpe = (max_sharpe_return - risk_free_rate) / max_sharpe_risk

# Generate efficient frontier
frontier_returns = []
frontier_risks = []
target_returns = np.linspace(min_var_return, expected_returns.max(), 50)

for target in target_returns:
    constraints_ef = (
        {"type": "eq", "fun": lambda x: np.sum(x) - 1},
        {"type": "eq", "fun": lambda x, t=target: portfolio_return(x) - t},
    )
    result = minimize(portfolio_risk, init_weights, method="SLSQP", bounds=bounds, constraints=constraints_ef)
    if result.success:
        frontier_returns.append(portfolio_return(result.x))
        frontier_risks.append(portfolio_risk(result.x))

# Map Sharpe ratios to colors
sharpe_min = min(portfolio_sharpes)
sharpe_max = max(portfolio_sharpes)
sharpe_normalized = [(s - sharpe_min) / (sharpe_max - sharpe_min) for s in portfolio_sharpes]
color_indices = [int(s * 255) for s in sharpe_normalized]
colors = [Viridis256[min(i, 255)] for i in color_indices]

# Create ColumnDataSource
source = ColumnDataSource(
    data={"risk": portfolio_risks, "return": portfolio_returns, "sharpe": portfolio_sharpes, "color": colors}
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="frontier-efficient · bokeh · pyplots.ai",
    x_axis_label="Risk (Standard Deviation)",
    y_axis_label="Expected Return",
    tools="pan,box_zoom,reset,save",
)

# Style the plot
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Plot random portfolios with Sharpe ratio color coding
p.scatter(
    "risk",
    "return",
    source=source,
    size=18,
    color="color",
    alpha=0.7,
    legend_label="Random Portfolios (color = Sharpe)",
)

# Plot efficient frontier curve
frontier_source = ColumnDataSource(data={"risk": frontier_risks, "return": frontier_returns})
p.line("risk", "return", source=frontier_source, line_width=6, color="#306998", legend_label="Efficient Frontier")

# Mark minimum variance portfolio
min_var_source = ColumnDataSource(data={"risk": [min_var_risk], "return": [min_var_return]})
p.scatter(
    "risk",
    "return",
    source=min_var_source,
    size=45,
    color="#FFD43B",
    marker="star",
    line_color="#333333",
    line_width=3,
    legend_label="Min Variance Portfolio",
)

# Mark maximum Sharpe ratio portfolio
max_sharpe_source = ColumnDataSource(data={"risk": [max_sharpe_risk], "return": [max_sharpe_return]})
p.scatter(
    "risk",
    "return",
    source=max_sharpe_source,
    size=45,
    color="#E74C3C",
    marker="diamond",
    line_color="#333333",
    line_width=3,
    legend_label="Max Sharpe Portfolio",
)

# Capital Market Line (from risk-free rate tangent to max Sharpe portfolio)
cml_x_end = max(portfolio_risks) * 1.1
cml_y_end = risk_free_rate + max_sharpe * cml_x_end
cml_source = ColumnDataSource(data={"x": [0, cml_x_end], "y": [risk_free_rate, cml_y_end]})
p.line(
    "x", "y", source=cml_source, line_width=4, line_dash="dashed", color="#9B59B6", legend_label="Capital Market Line"
)

# Style legend
p.legend.location = "top_left"
p.legend.label_text_font_size = "22pt"
p.legend.background_fill_alpha = 0.85
p.legend.border_line_width = 2
p.legend.glyph_height = 30
p.legend.glyph_width = 30
p.legend.spacing = 10
p.legend.padding = 15

# Add grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Format axes as percentages
p.xaxis.formatter.use_scientific = False
p.yaxis.formatter.use_scientific = False

# Add color bar for Sharpe ratio
color_mapper = LinearColorMapper(palette=Viridis256, low=sharpe_min, high=sharpe_max)
color_bar = ColorBar(
    color_mapper=color_mapper,
    title="Sharpe Ratio",
    title_text_font_size="24pt",
    major_label_text_font_size="18pt",
    label_standoff=15,
    width=40,
    location=(0, 0),
)
p.add_layout(color_bar, "right")

# Add right margin for color bar
p.min_border_right = 120

# Set background
p.background_fill_color = "#fafafa"

# Save as PNG and HTML
export_png(p, filename="plot.png")

# Also save HTML for interactive version
output_file("plot.html")
save(p)
