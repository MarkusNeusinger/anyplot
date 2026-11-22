#' anyplot.ai
#' timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
#' Library: ggplot2 | R
#' Quality: 88/100 | Updated: 2026-05-19

library(ggplot2)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
# Imprint palette
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
# Translucent fills read weaker on the dark page, so the bands get more alpha there.
ALPHA_95    <- if (THEME == "light") 0.10 else 0.30
ALPHA_80    <- if (THEME == "light") 0.18 else 0.45

# Columns: set these to your table's column names
DATE     <- "Date"           # role: x
ACTUAL   <- "Actual"         # role: y (history)
FORECAST <- "Forecast"       # role: y (forecast)
LOWER_80 <- "Lower 80%"      # role: band
UPPER_80 <- "Upper 80%"      # role: band
LOWER_95 <- "Lower 95%"      # role: band
UPPER_95 <- "Upper 95%"      # role: band
SALES    <- "Monthly Sales ($)"  # role: axis title

# Data: replace this block with your own table, for example df <- read.csv("sales.csv", check.names = FALSE)
set.seed(42)
n_hist <- 36
n_fcst <- 6
dates_hist <- seq(as.Date("2022-01-01"), by = "month", length.out = n_hist)
actual_sales <- 50000 + cumsum(rnorm(n_hist, 500, 1000)) +
                5000 * sin(seq(0, 4 * pi, length.out = n_hist))

dates_fcst <- seq(dates_hist[n_hist] + 31, by = "month", length.out = n_fcst)
forecast_values <- tail(actual_sales, 1) + cumsum(rnorm(n_fcst, 400, 800))

# Uncertainty widens with forecast horizon
forecast_std <- 2000 * sqrt(seq_len(n_fcst))

df <- tibble::tibble(
  !!DATE     := c(dates_hist, dates_fcst),
  !!ACTUAL   := c(actual_sales, rep(NA, n_fcst)),
  # the forecast line starts at the last observation so it picks up where history ends
  !!FORECAST := c(rep(NA, n_hist - 1), tail(actual_sales, 1), forecast_values),
  !!LOWER_80 := c(rep(NA, n_hist), forecast_values - qnorm(0.9)   * forecast_std),
  !!UPPER_80 := c(rep(NA, n_hist), forecast_values + qnorm(0.9)   * forecast_std),
  !!LOWER_95 := c(rep(NA, n_hist), forecast_values - qnorm(0.975) * forecast_std),
  !!UPPER_95 := c(rep(NA, n_hist), forecast_values + qnorm(0.975) * forecast_std)
)

# --- Plot -------------------------------------------------------------------
forecast_start <- max(df[[DATE]][!is.na(df[[ACTUAL]])])

p <- ggplot(df, aes(x = .data[[DATE]])) +
  geom_ribbon(aes(ymin = .data[[LOWER_95]], ymax = .data[[UPPER_95]], fill = "95% CI"),
              alpha = ALPHA_95, color = NA) +
  geom_ribbon(aes(ymin = .data[[LOWER_80]], ymax = .data[[UPPER_80]], fill = "80% CI"),
              alpha = ALPHA_80, color = NA) +
  geom_vline(xintercept = forecast_start, linetype = "dotted",
             color = INK_SOFT, linewidth = 0.8) +
  geom_line(aes(y = .data[[FORECAST]], color = "Forecast"),
            linewidth = 1.2, linetype = "dashed") +
  geom_line(aes(y = .data[[ACTUAL]], color = "Historical"), linewidth = 1.2) +
  scale_color_manual(
    values = c("Historical" = IMPRINT_PALETTE[1], "Forecast" = IMPRINT_PALETTE[2]),
    breaks = c("Historical", "Forecast")
  ) +
  scale_fill_manual(
    values = c("80% CI" = IMPRINT_PALETTE[2], "95% CI" = IMPRINT_PALETTE[2]),
    breaks = c("95% CI", "80% CI")
  ) +
  scale_x_date(expand = expansion(mult = c(0.02, 0.05))) +
  labs(
    title = "timeseries-forecast-uncertainty · r · ggplot2 · anyplot.ai",
    x     = DATE,
    y     = SALES,
    color = NULL,
    fill  = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.2),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(color = INK,      size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK,      size = 12),
    legend.position    = "top",
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.background  = element_rect(fill = PAGE_BG,   color = NA),
    legend.spacing.x   = unit(1, "cm")
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
