# frontier-efficient: Efficient Frontier for Portfolio Optimization

## Description

The efficient frontier is a fundamental visualization in Modern Portfolio Theory (MPT) that displays a curve of optimal portfolios offering the highest expected return for each level of risk (standard deviation). Portfolios on the frontier are "efficient" because no other portfolio exists with higher return for the same risk, or lower risk for the same return. This plot is essential for asset allocation decisions and understanding the risk-return tradeoff in investment portfolios.

## Applications

- Portfolio managers selecting optimal asset allocations based on client risk tolerance
- Financial advisors demonstrating the benefits of diversification to investors
- Quantitative analysts comparing actual portfolio positions against theoretical optimums
- Academic research in finance and economics illustrating mean-variance optimization concepts

## Data

- `return` (numeric) - Expected portfolio return (annualized, typically 0.0-0.3)
- `risk` (numeric) - Portfolio risk as standard deviation (annualized, typically 0.0-0.4)
- `weight` (optional, list) - Asset weights for each portfolio point
- Size: 50-500 simulated portfolios plus the efficient frontier curve
- Example: Randomly generated portfolios from 5-10 asset universe with historical return/covariance data

## Notes

- X-axis should show risk (standard deviation), Y-axis should show expected return
- The efficient frontier curve should be clearly distinguished (thicker line, distinct color)
- Include random portfolio scatter points to show suboptimal portfolios below the frontier
- Mark key points: minimum variance portfolio, maximum Sharpe ratio (tangency) portfolio
- Optional: Show capital market line from risk-free rate tangent to frontier
- Color coding can indicate Sharpe ratio for scatter points

## What a good version looks like

- A good version shows: risk as standard deviation on the x-axis and expected return on the y-axis, as the Notes ask, with every portfolio a point at its own risk and return, never jittered or displaced.
- A good version shows: the efficient frontier as a curve clearly distinguished from the scatter by a thicker line or a distinct color, as the Notes ask, running along the upper left edge of the cloud so that the random portfolios lie below it.
- A good version shows: the random portfolios as a scatter cloud, as the Notes ask, whose dense core stays readable, with a color scale explaining the Sharpe ratio coloring the Notes allow, if used.
- A good version shows: the minimum variance portfolio and the maximum Sharpe ratio portfolio marked, as the Notes ask, and told apart from each other, the first at the leftmost point of the frontier and the second on the frontier where the capital market line would touch it.
- A good version shows: the capital market line the Notes allow, if drawn, as a straight line that would pass through the risk-free rate at zero risk and touches the frontier at the tangency portfolio, lying above the frontier everywhere else.
- Expected, not a defect: a cloud that is dense in its core and thin at its edges, a gap between the random portfolios and the frontier, an empty region above and to the left of the frontier, and axes that do not start at zero.
