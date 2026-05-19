#' anyplot.ai
#' timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 81/100 | Updated: 2026-05-19

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# --- Data generation (sales forecast) ----------------------------------------
# Historical: 36 months of actual sales data
dates_hist <- seq(as.Date("2022-01-01"), by = "month", length.out = 36)
actual_sales <- 50000 + cumsum(rnorm(36, 500, 1000)) +
                5000 * sin(seq(0, 4 * pi, length.out = 36))

# Forecast: 6 months ahead with confidence intervals
dates_fcst <- seq(dates_hist[length(dates_hist)] + 31, by = "month", length.out = 6)
forecast_values <- tail(actual_sales, 1) + cumsum(rnorm(6, 400, 800))

# Confidence intervals based on forecast uncertainty
forecast_std <- 2500  # Standard error of forecast
forecast_lower_80 <- forecast_values - qnorm(0.9) * forecast_std
forecast_upper_80 <- forecast_values + qnorm(0.9) * forecast_std
forecast_lower_95 <- forecast_values - qnorm(0.975) * forecast_std
forecast_upper_95 <- forecast_values + qnorm(0.975) * forecast_std

# Combine into single dataframe
df <- tibble::tibble(
  date = c(dates_hist, dates_fcst),
  actual = c(actual_sales, rep(NA, 6)),
  forecast = c(rep(NA, 36), forecast_values),
  lower_80 = c(rep(NA, 36), forecast_lower_80),
  upper_80 = c(rep(NA, 36), forecast_upper_80),
  lower_95 = c(rep(NA, 36), forecast_lower_95),
  upper_95 = c(rep(NA, 36), forecast_upper_95),
  period = c(rep("Historical", 36), rep("Forecast", 6))
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = date)) +
  # 95% confidence band (lighter shade)
  geom_ribbon(aes(ymin = lower_95, ymax = upper_95, fill = "95% CI"),
              alpha = 0.15, color = NA) +
  # 80% confidence band (darker shade)
  geom_ribbon(aes(ymin = lower_80, ymax = upper_80, fill = "80% CI"),
              alpha = 0.25, color = NA) +
  # Forecast line
  geom_line(aes(y = forecast, color = "Forecast"), linewidth = 1.2) +
  # Historical data line
  geom_line(aes(y = actual, color = "Historical"), linewidth = 1.2) +
  # Forecast start marker
  geom_vline(xintercept = dates_hist[36] + 15.5, linetype = "dashed",
             color = INK_SOFT, linewidth = 0.8, alpha = 0.6) +
  # Manual color scales
  scale_color_manual(
    values = c("Historical" = OKABE_ITO[1], "Forecast" = OKABE_ITO[2]),
    breaks = c("Historical", "Forecast")
  ) +
  scale_fill_manual(
    values = c("80% CI" = OKABE_ITO[2], "95% CI" = OKABE_ITO[2]),
    breaks = c("95% CI", "80% CI")
  ) +
  labs(
    title = "timeseries-forecast-uncertainty · ggplot2 · anyplot.ai",
    x = "Date",
    y = "Sales ($)",
    color = NULL,
    fill = NULL
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK, size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK, size = 24, face = "plain"),
    legend.position  = "top",
    legend.text      = element_text(color = INK_SOFT, size = 16),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.spacing.x = unit(1, "cm")
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
