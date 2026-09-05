#' anyplot.ai
#' line-annotated-events: Annotated Line Plot with Event Markers
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
BRAND <- IMPRINT_PALETTE[1]

# --- Data ---------------------------------------------------------------------
trading_days <- seq(as.Date("2024-01-02"), as.Date("2024-12-20"), by = "day")
trading_days <- trading_days[!weekdays(trading_days) %in% c("Saturday", "Sunday")]

daily_returns <- rnorm(length(trading_days), mean = 0.0006, sd = 0.016)
close_price   <- 148 * cumprod(1 + daily_returns)

stock_df <- tibble::tibble(date = trading_days, value = close_price)

events_df <- tibble::tibble(
  event_date  = as.Date(c("2024-02-01", "2024-04-25", "2024-07-24",
                          "2024-09-10", "2024-10-30")),
  event_label = c("Q4'23 Earnings Beat", "Q1 Earnings Miss", "Q2 Earnings Beat",
                  "New Product Launch", "Q3 Earnings Beat"),
  label_step  = c(1, 2, 1, 2, 1)
)

price_range   <- range(stock_df$value)
span          <- diff(price_range)
label_row_gap <- span * 0.09
label_base_y  <- price_range[2] + span * 0.04
events_df <- events_df |>
  mutate(
    label_y = label_base_y + (label_step - 1) * label_row_gap,
    dot_y   = approx(stock_df$date, stock_df$value, event_date)$y,
    leader_y = label_y - span * 0.02
  )

# --- Plot -----------------------------------------------------------------
title_text <- "line-annotated-events · r · ggplot2 · anyplot.ai"

p <- ggplot() +
  geom_vline(
    data = events_df, aes(xintercept = as.numeric(event_date)),
    color = INK, linewidth = 0.4, linetype = "dashed", alpha = 0.5
  ) +
  geom_line(
    data = stock_df, aes(x = date, y = value),
    color = BRAND, linewidth = 1.0
  ) +
  geom_segment(
    data = events_df,
    aes(x = event_date, xend = event_date, y = dot_y, yend = leader_y),
    color = IMPRINT_PALETTE[5], linewidth = 0.5, alpha = 0.55
  ) +
  geom_point(
    data = events_df,
    aes(x = event_date, y = dot_y),
    color = IMPRINT_PALETTE[5], size = 2.8
  ) +
  geom_label(
    data = events_df,
    aes(x = event_date, y = label_y, label = event_label),
    color = INK_SOFT, fill = ELEVATED_BG, size = 3.0,
    hjust = 0.5, vjust = 0, lineheight = 0.9,
    label.size = 0.2, label.padding = unit(0.18, "lines"),
    label.r = unit(0.08, "lines")
  ) +
  scale_y_continuous(
    labels = scales::dollar_format(),
    expand = expansion(mult = c(0.06, 0.20))
  ) +
  scale_x_date(date_labels = "%b", date_breaks = "2 months") +
  labs(
    title = title_text,
    x = "Trading Date (2024)",
    y = "Closing Price"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12),
    plot.margin       = margin(t = 10, r = 16, b = 8, l = 8)
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
