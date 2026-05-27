#' anyplot.ai
#' stock-event-flags: Stock Chart with Event Flags
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-27

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- adjustcolor(INK, alpha.f = 0.12)

ANYPLOT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

EVENT_COLORS <- c(
  "Earnings" = ANYPLOT_PALETTE[3],  # blue — financial results
  "Dividend" = ANYPLOT_PALETTE[4],  # ochre — income
  "News"     = ANYPLOT_PALETTE[2],  # lavender — analyst / market news
  "Launch"   = ANYPLOT_PALETTE[6]   # cyan — product / tech
)

# Generate 190 trading days (weekdays only, Jan–Sep 2023)
all_days     <- seq(as.Date("2023-01-03"), as.Date("2023-12-29"), by = "day")
trading_days <- all_days[!weekdays(all_days) %in% c("Saturday", "Sunday")]
trading_days <- trading_days[seq_len(190)]

# Geometric random walk starting at $150 (fictional tech company)
returns      <- rnorm(190, mean = 0.0005, sd = 0.015)
close_prices <- 150 * cumprod(1 + returns)

price_df <- data.frame(
  date  = trading_days,
  close = close_prices
)

# Seven corporate events across the period
event_df <- data.frame(
  date       = as.Date(c(
    "2023-02-01", "2023-03-15", "2023-05-02",
    "2023-06-20", "2023-07-27", "2023-08-15",
    "2023-09-06"
  )),
  event_type = c(
    "Earnings", "Dividend", "Earnings",
    "News",     "Earnings", "Launch",
    "Dividend"
  ),
  label = c(
    "Q4 Beat", "Div $0.25", "Q1 Beat",
    "Upgrade", "Q2 Miss",   "New Model",
    "Div $0.28"
  ),
  stringsAsFactors = FALSE
)

# Attach closing price at each event date
event_df <- event_df |>
  left_join(price_df, by = "date")

# Stagger flag heights in two rows to prevent overlap
price_max   <- max(price_df$close)
price_range <- price_max - min(price_df$close)

event_df <- event_df |>
  mutate(
    row_alt = row_number() %% 2,
    flag_y  = price_max + price_range * (0.11 + row_alt * 0.09)
  )

y_ceiling <- price_max + price_range * 0.36

# Title (46 chars → size stays at default 12)
title_str  <- "stock-event-flags · r · ggplot2 · anyplot.ai"
title_size <- 12

# Plot
p <- ggplot() +
  # Price line (first categorical series = brand green)
  geom_line(
    data      = price_df,
    aes(x = date, y = close),
    color     = ANYPLOT_PALETTE[1],
    linewidth = 1.0
  ) +
  # Dashed connectors from price level to flag
  geom_segment(
    data      = event_df,
    aes(x = date, xend = date, y = close, yend = flag_y, color = event_type),
    linetype  = "dashed",
    linewidth = 0.45,
    alpha     = 0.75,
    show.legend = FALSE
  ) +
  # Flag markers (shape encodes event type)
  geom_point(
    data = event_df,
    aes(x = date, y = flag_y, color = event_type, shape = event_type),
    size = 3.5
  ) +
  # Short labels above flags
  geom_text(
    data  = event_df,
    aes(x = date, y = flag_y, label = label, color = event_type),
    size  = 2.2,
    vjust = -0.65,
    fontface    = "bold",
    show.legend = FALSE
  ) +
  scale_color_manual(values = EVENT_COLORS, name = "Event") +
  scale_shape_manual(
    values = c("Earnings" = 17L, "Dividend" = 15L, "News" = 19L, "Launch" = 18L),
    name   = "Event"
  ) +
  scale_x_date(date_breaks = "2 months", date_labels = "%b '%y") +
  scale_y_continuous(
    labels = scales::dollar_format(),
    limits = c(NA_real_, y_ceiling),
    expand = expansion(mult = c(0.04, 0.01))
  ) +
  labs(
    title = title_str,
    x     = "Date",
    y     = "Close Price (USD)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG,      color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG,      color = NA),
    panel.grid.major.y = element_line(color = GRID_COLOR,  linewidth = 0.5),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.border       = element_blank(),
    axis.line          = element_line(color = INK_SOFT,    linewidth = 0.4),
    axis.title         = element_text(color = INK,         size = 10),
    axis.text          = element_text(color = INK_SOFT,    size = 8),
    plot.title         = element_text(color = INK,         size = title_size,
                                      face = "bold"),
    legend.background  = element_rect(fill = ELEVATED_BG,  color = INK_SOFT,
                                      linewidth = 0.3),
    legend.key         = element_rect(fill = PAGE_BG,      color = NA),
    legend.text        = element_text(color = INK_SOFT,    size = 8),
    legend.title       = element_text(color = INK,         size = 10),
    legend.position    = "bottom",
    legend.direction   = "horizontal",
    plot.margin        = margin(15, 30, 10, 15)
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
