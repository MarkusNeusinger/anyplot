#' anyplot.ai
#' frontier-efficient: Efficient Frontier for Portfolio Optimization
#' Library: ggplot2 | R
#' Quality: 91/100 | Updated: 2026-11-22

library(ggplot2)
library(dplyr)
library(ragg)
library(tibble)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
RISK   <- "Risk (Standard Deviation)"      # role: x
RETURN <- "Expected Return (Annualized)"   # role: y
SHARPE <- "Sharpe Ratio"                   # role: color

# --- Data: random long-only portfolios of a 5-asset universe ----------------
set.seed(42)
n_portfolios <- 300
risk_free_rate <- 0.02

asset_returns <- c(0.08, 0.12, 0.10, 0.15, 0.09)
asset_vols <- c(0.15, 0.20, 0.18, 0.25, 0.12)
corr_matrix <- matrix(c(
  1.00, 0.30, 0.25, 0.40, 0.15,
  0.30, 1.00, 0.35, 0.45, 0.20,
  0.25, 0.35, 1.00, 0.50, 0.25,
  0.40, 0.45, 0.50, 1.00, 0.30,
  0.15, 0.20, 0.25, 0.30, 1.00
), nrow = 5, byrow = TRUE)
cov_matrix <- diag(asset_vols) %*% corr_matrix %*% diag(asset_vols)

weights <- matrix(runif(n_portfolios * length(asset_returns)), ncol = length(asset_returns))
weights <- weights / rowSums(weights)
port_return <- as.numeric(weights %*% asset_returns)
port_risk <- sqrt(rowSums((weights %*% cov_matrix) * weights))

df <- tibble::tibble(
  !!RISK   := port_risk,
  !!RETURN := port_return,
  !!SHARPE := (port_return - risk_free_rate) / port_risk
)

# Efficient frontier of the same universe (closed-form mean-variance solution)
inv_cov <- solve(cov_matrix)
ones <- rep(1, length(asset_returns))
a_coef <- as.numeric(ones %*% inv_cov %*% ones)
b_coef <- as.numeric(ones %*% inv_cov %*% asset_returns)
c_coef <- as.numeric(asset_returns %*% inv_cov %*% asset_returns)
det_coef <- a_coef * c_coef - b_coef^2
frontier_risk_at <- function(r) sqrt((a_coef * r^2 - 2 * b_coef * r + c_coef) / det_coef)

min_var_return <- b_coef / a_coef
frontier_return <- seq(min_var_return, max(df[[RETURN]]) + 0.01, length.out = 200)
frontier <- tibble::tibble(
  !!RISK   := frontier_risk_at(frontier_return),
  !!RETURN := frontier_return
)

# Key portfolios on the frontier: minimum variance and tangency (max Sharpe)
min_var <- tibble::tibble(!!RISK := frontier_risk_at(min_var_return), !!RETURN := min_var_return)
tangency_w <- inv_cov %*% (asset_returns - risk_free_rate)
tangency_w <- as.numeric(tangency_w / sum(tangency_w))
tangency_return <- sum(tangency_w * asset_returns)
max_sharpe <- tibble::tibble(
  !!RISK   := sqrt(as.numeric(tangency_w %*% cov_matrix %*% tangency_w)),
  !!RETURN := tangency_return
)

# Capital market line: from the risk-free rate through the tangency portfolio
cml_slope <- (max_sharpe[[RETURN]] - risk_free_rate) / max_sharpe[[RISK]]
cml <- tibble::tibble(
  !!RISK   := c(0, max(df[[RISK]], frontier[[RISK]])),
  !!RETURN := risk_free_rate + cml_slope * .data[[RISK]]
)

key_points <- bind_rows(
  min_var %>% mutate(point = "Minimum variance"),
  max_sharpe %>% mutate(point = "Maximum Sharpe ratio")
)
key_points$point <- factor(key_points$point, levels = c("Minimum variance", "Maximum Sharpe ratio"))

# --- Plot -------------------------------------------------------------------
p <- ggplot() +
  geom_point(
    data = df,
    aes(x = .data[[RISK]], y = .data[[RETURN]], color = .data[[SHARPE]]),
    size = 3.2, alpha = 0.65
  ) +
  scale_color_gradient(
    low = INK_SOFT, high = IMPRINT_PALETTE[1], name = SHARPE,
    guide = guide_colorbar(order = 1, barwidth = 1.2, barheight = 10)
  ) +
  geom_line(
    data = cml,
    aes(x = .data[[RISK]], y = .data[[RETURN]]),
    color = IMPRINT_PALETTE[5], linewidth = 1.2, linetype = "dashed"
  ) +
  geom_line(
    data = frontier,
    aes(x = .data[[RISK]], y = .data[[RETURN]]),
    color = IMPRINT_PALETTE[3], linewidth = 2.6
  ) +
  geom_point(
    data = key_points,
    aes(x = .data[[RISK]], y = .data[[RETURN]], shape = point, fill = point),
    color = INK, size = 5, stroke = 1
  ) +
  scale_shape_manual(values = c("Minimum variance" = 23, "Maximum Sharpe ratio" = 24), name = NULL) +
  scale_fill_manual(
    values = c("Minimum variance" = IMPRINT_PALETTE[2], "Maximum Sharpe ratio" = IMPRINT_PALETTE[4]),
    name = NULL
  ) +
  guides(
    shape = guide_legend(order = 2, override.aes = list(size = 4.5)),
    fill = guide_legend(order = 2)
  ) +
  annotate(
    "text", x = 0.06, y = 0.045, hjust = 0,
    label = "Capital market line", color = IMPRINT_PALETTE[5], size = 3.6
  ) +
  annotate(
    "text", x = 0.1, y = 0.14, hjust = 1,
    label = "Efficient frontier", color = IMPRINT_PALETTE[3], size = 3.6, fontface = "bold"
  ) +
  labs(
    title = "frontier-efficient · r · ggplot2 · anyplot.ai",
    x = RISK, y = RETURN
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.1),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.4),
    axis.title = element_text(color = INK, size = 10),
    axis.text = element_text(color = INK_SOFT, size = 8),
    plot.title = element_text(color = INK, size = 12, face = "plain"),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.4),
    legend.key = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text = element_text(color = INK_SOFT, size = 8),
    legend.title = element_text(color = INK, size = 9),
    legend.position = "right",
    plot.margin = margin(12, 12, 12, 12, unit = "pt")
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot = p,
  device = ragg::agg_png,
  width = 8,
  height = 4.5,
  units = "in",
  dpi = 400
)
