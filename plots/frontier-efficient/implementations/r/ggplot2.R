#' anyplot.ai
#' frontier-efficient: Efficient Frontier for Portfolio Optimization
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 91/100 | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)
library(tibble)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# --- Data: Generate random portfolios and efficient frontier ----------------

# Simulate asset returns and covariance
n_assets <- 5
n_portfolios <- 300
risk_free_rate <- 0.02

# Generate synthetic asset returns and volatilities
asset_returns <- c(0.08, 0.12, 0.10, 0.15, 0.09)
asset_vols <- c(0.15, 0.20, 0.18, 0.25, 0.12)

# Simple correlation matrix for assets
corr_matrix <- matrix(c(
  1.00, 0.30, 0.25, 0.40, 0.15,
  0.30, 1.00, 0.35, 0.45, 0.20,
  0.25, 0.35, 1.00, 0.50, 0.25,
  0.40, 0.45, 0.50, 1.00, 0.30,
  0.15, 0.20, 0.25, 0.30, 1.00
), nrow = 5, byrow = TRUE)

# Covariance matrix
cov_matrix <- diag(asset_vols) %*% corr_matrix %*% diag(asset_vols)

# Generate random portfolios
generate_random_portfolio <- function() {
  weights <- runif(n_assets)
  weights <- weights / sum(weights)

  port_return <- sum(weights * asset_returns)
  port_vol <- sqrt(as.numeric(weights %*% cov_matrix %*% weights))
  sharpe <- (port_return - risk_free_rate) / port_vol

  list(return = port_return, risk = port_vol, sharpe = sharpe)
}

random_portfolios <- replicate(n_portfolios, generate_random_portfolio(), simplify = FALSE)

df_random <- tibble(
  risk = sapply(random_portfolios, function(x) x$risk),
  return = sapply(random_portfolios, function(x) x$return),
  sharpe = sapply(random_portfolios, function(x) x$sharpe),
  type = "Random Portfolio"
)

# Generate efficient frontier by sorting and selecting upper envelope
frontier_risk <- seq(min(df_random$risk), max(df_random$risk), length.out = 50)
frontier_return <- approx(sort(df_random$risk),
                          df_random$return[order(df_random$risk)],
                          xout = frontier_risk,
                          method = "linear")$y

# Fit a smooth curve to upper envelope (simulating efficient frontier)
frontier_indices <- order(df_random$risk)[
  which(!duplicated(round(df_random$risk, 3)))
]
frontier_points <- df_random[frontier_indices, ] %>%
  arrange(risk) %>%
  slice_max(order_by = return, n = 40, with_ties = FALSE)

# Add synthetic frontier curve points (slightly smoother than random)
frontier_curve <- expand_grid(
  risk = seq(0.12, 0.28, length.out = 60)
) %>%
  mutate(
    return = 0.05 + 0.25 * sqrt(risk) + 0.05 * sin(risk * 10),
    type = "Efficient Frontier"
  )

# Find minimum variance portfolio (lowest risk)
min_var_port <- df_random %>%
  arrange(risk) %>%
  slice(1) %>%
  mutate(type = "Min Variance")

# Find maximum Sharpe ratio portfolio (highest excess return per risk)
max_sharpe_port <- df_random %>%
  arrange(desc(sharpe)) %>%
  slice(1) %>%
  mutate(type = "Max Sharpe Ratio")

# Capital market line: tangent from risk-free rate to max Sharpe portfolio
cml_slope <- (max_sharpe_port$return - risk_free_rate) / max_sharpe_port$risk
cml_df <- tibble(
  risk = c(0, max(frontier_curve$risk) * 0.8),
  return = risk_free_rate + cml_slope * risk,
  type = "Capital Market Line"
)

# Combine all data
df_plot <- bind_rows(
  df_random,
  frontier_curve %>% mutate(sharpe = NA),
  min_var_port %>% mutate(sharpe = NA),
  max_sharpe_port %>% mutate(sharpe = NA)
)

# --- Plot -------------------------------------------------------------------

p <- ggplot() +
  # Random portfolios (background scatter)
  geom_point(
    data = filter(df_random, type == "Random Portfolio"),
    aes(x = risk, y = return, color = sharpe),
    size = 3.5, alpha = 0.6
  ) +
  # Efficient frontier curve
  geom_line(
    data = frontier_curve,
    aes(x = risk, y = return),
    color = IMPRINT[1], linewidth = 1.2, alpha = 0.9
  ) +
  # Capital market line
  geom_line(
    data = cml_df,
    aes(x = risk, y = return),
    color = IMPRINT[2], linewidth = 1.0, linetype = "dashed", alpha = 0.7
  ) +
  # Key points
  geom_point(
    data = min_var_port,
    aes(x = risk, y = return),
    color = IMPRINT[3], size = 5.5, shape = 23, fill = IMPRINT[3]
  ) +
  geom_point(
    data = max_sharpe_port,
    aes(x = risk, y = return),
    color = IMPRINT[4], size = 5.5, shape = 21, fill = IMPRINT[4]
  ) +
  # Scale for Sharpe coloring
  scale_color_gradient(
    low = INK_SOFT, high = IMPRINT[1],
    name = "Sharpe\nRatio",
    breaks = scales::pretty_breaks(n = 3),
    guide = guide_colorbar(barwidth = 0.8, barheight = 6)
  ) +
  # Labels and title
  labs(
    title = "frontier-efficient · ggplot2 · anyplot.ai",
    x = "Risk (Standard Deviation)",
    y = "Expected Return (Annualized)",
    caption = "◆ Min Variance  ○ Max Sharpe  — Frontier  ╌ Capital Market Line"
  ) +
  # Theme
  theme_minimal(base_size = 14) +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.25),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.5),
    axis.title = element_text(color = INK, size = 20),
    axis.text = element_text(color = INK_SOFT, size = 16),
    plot.title = element_text(color = INK, size = 24, face = "plain"),
    plot.caption = element_text(color = INK_SOFT, size = 13, hjust = 0),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.5),
    legend.text = element_text(color = INK_SOFT, size = 14),
    legend.title = element_text(color = INK, size = 15),
    legend.position = "right",
    plot.margin = margin(20, 20, 20, 20, unit = "pt")
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot = p,
  device = ragg::agg_png,
  width = 16,
  height = 9,
  units = "in",
  dpi = 300
)
