#' anyplot.ai
#' acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-06-10

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens — Imprint palette (see prompts/default-style-guide.md)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first series)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# Data: synthetic AR(2) time series (n = 300 observations)
# phi1 = 0.7, phi2 = -0.3 produces geometrically decaying ACF and PACF cutoff at lag 2
ts_data <- arima.sim(model = list(ar = c(0.7, -0.3)), n = 300, sd = 0.5)
n_obs   <- length(ts_data)
n_lags  <- 36
ci      <- 1.96 / sqrt(n_obs)

# Compute ACF (lags 0–36) and PACF (lags 1–36)
acf_out  <- acf(ts_data,  lag.max = n_lags, plot = FALSE)
pacf_out <- pacf(ts_data, lag.max = n_lags, plot = FALSE)

acf_df <- data.frame(
  lag  = 0:n_lags,
  corr = as.numeric(acf_out$acf),
  type = "ACF"
)
pacf_df <- data.frame(
  lag  = 1:n_lags,
  corr = as.numeric(pacf_out$acf),
  type = "PACF"
)
df      <- rbind(acf_df, pacf_df)
df$type <- factor(df$type, levels = c("ACF", "PACF"))
df$significant <- abs(df$corr) > ci

plot_title <- "acf-pacf · r · ggplot2 · anyplot.ai"

# Plot
p <- ggplot(df, aes(x = lag, y = corr)) +
  geom_hline(yintercept = 0,   color = INK_SOFT,  linewidth = 0.4) +
  geom_hline(yintercept =  ci, color = INK_MUTED, linetype = "dashed", linewidth = 0.5) +
  geom_hline(yintercept = -ci, color = INK_MUTED, linetype = "dashed", linewidth = 0.5) +
  geom_segment(
    aes(xend = lag, yend = 0, color = significant),
    linewidth = 1.2
  ) +
  scale_color_manual(
    values = c("TRUE" = IMPRINT_PALETTE[1], "FALSE" = INK_MUTED),
    guide  = "none"
  ) +
  facet_wrap(~ type, ncol = 1, scales = "free_y") +
  scale_x_continuous(breaks = seq(0, n_lags, by = 5)) +
  labs(
    x     = "Lag",
    y     = "Autocorrelation",
    title = plot_title
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG,     color = NA),
    panel.grid.major = element_line(color = INK_SOFT,   linewidth = 0.2),
    panel.grid.minor = element_blank(),
    panel.border          = element_blank(),
    axis.line.x.bottom    = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.line.y.left      = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.title       = element_text(color = INK,        size = 10),
    axis.text        = element_text(color = INK_SOFT,   size = 8),
    plot.title       = element_text(color = INK,        size = 12,
                                    margin = margin(b = 8)),
    strip.text       = element_text(color = INK,        size = 10, face = "bold"),
    strip.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    plot.margin      = margin(t = 12, r = 12, b = 12, l = 12)
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
