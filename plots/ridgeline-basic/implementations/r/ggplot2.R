#' anyplot.ai
#' ridgeline-basic: Basic Ridgeline Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-07-25

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data: monthly high-temperature readings, seasonal pattern --------------
months        <- month.abb
seasonal_mean <- c(2, 4, 8, 13, 18, 23, 26, 25, 20, 14, 8, 3)
seasonal_sd   <- c(3.2, 3.0, 3.4, 3.6, 3.2, 2.8, 2.6, 2.6, 3.0, 3.2, 3.4, 3.2)

temperatures <- do.call(rbind, lapply(seq_along(months), function(i) {
  data.frame(
    month       = months[i],
    temperature = rnorm(180, mean = seasonal_mean[i], sd = seasonal_sd[i])
  )
}))
temperatures$month <- factor(temperatures$month, levels = months)

# --- Per-group density curves, computed natively (ggridges is unavailable) --
ridge_curves <- temperatures %>%
  group_by(month) %>%
  reframe(
    x = density(temperature, n = 256, adjust = 1.2)$x,
    y = density(temperature, n = 256, adjust = 1.2)$y
  ) %>%
  mutate(idx = as.integer(month))

spacing <- 1
scale_h <- spacing / max(ridge_curves$y) * 1.65

ridge_curves <- ridge_curves %>%
  mutate(
    baseline = idx * spacing,
    ymax     = baseline + y * scale_h,
    # Bottom (earliest month) ridges draw last so they sit in front of the
    # ridges behind them, producing the classic overlapping-mountain look.
    z        = factor(month, levels = rev(months))
  )

# --- Plot ---------------------------------------------------------------------
plot_title     <- "Monthly Temperatures · ridgeline-basic · r · ggplot2 · anyplot.ai"
title_fontsize <- round(12 * min(1, 67 / nchar(plot_title)))

p <- ggplot(ridge_curves) +
  geom_ribbon(
    aes(x = x, ymin = baseline, ymax = ymax, group = z, fill = idx),
    colour = PAGE_BG, linewidth = 0.6
  ) +
  scale_fill_gradient(low = "#009E73", high = "#4467A3", guide = "none") +
  scale_y_continuous(breaks = spacing * seq_along(months), labels = months) +
  labs(title = plot_title, x = "Temperature (°C)", y = NULL) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid         = element_blank(),
    axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.title.x       = element_text(color = INK, size = 10),
    axis.title.y       = element_blank(),
    axis.text.x        = element_text(color = INK_SOFT, size = 8),
    axis.text.y        = element_text(color = INK_SOFT, size = 8),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = title_fontsize),
    plot.margin        = margin(12, 20, 10, 10)
  )

# --- Save ---------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
