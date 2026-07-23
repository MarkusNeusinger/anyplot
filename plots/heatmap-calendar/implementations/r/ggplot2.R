#' anyplot.ai
#' heatmap-calendar: Basic Calendar Heatmap
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 93/100 | Created: 2026-07-23

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data: one year of daily commit activity, one mini-calendar per month ---
dates <- seq(as.Date("2025-01-01"), as.Date("2025-12-31"), by = "day")
n <- length(dates)

weekday_num <- as.integer(format(dates, "%u")) # 1 = Mon ... 7 = Sun
seasonal_wave <- 1 + 0.5 * sin(2 * pi * seq_len(n) / n) # busier toward year-end
base_lambda <- ifelse(weekday_num %in% 6:7, 1.2, 6.0) * seasonal_wave
commits <- rpois(n, lambda = base_lambda)

# A handful of days have no recorded activity (tracker offline)
missing_idx <- sample.int(n, size = round(0.03 * n))
commits[missing_idx] <- NA_integer_

day_labels <- c("1" = "Mon", "2" = "Tue", "3" = "Wed", "4" = "Thu",
                "5" = "Fri", "6" = "Sat", "7" = "Sun")

df <- tibble(
  date = dates,
  month_label = factor(format(dates, "%b"), levels = month.abb),
  day_of_month = as.integer(format(dates, "%d")),
  day_label = factor(day_labels[as.character(weekday_num)],
                      levels = rev(c("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"))),
  weekday_num = weekday_num,
  commits = commits
)

# Week-of-month row index (1-indexed), aligned so day 1 lands on its weekday
month_offsets <- df %>%
  filter(day_of_month == 1) %>%
  transmute(month_label, offset = weekday_num - 1)

df <- df %>%
  left_join(month_offsets, by = "month_label") %>%
  mutate(week_in_month = (day_of_month - 1 + offset) %/% 7 + 1)

# --- Peak-activity callout: busiest month + single-day high ------------
month_totals <- df %>%
  group_by(month_label) %>%
  summarise(total = sum(commits, na.rm = TRUE), .groups = "drop")
peak_month_row <- month_totals %>% slice_max(total, n = 1, with_ties = FALSE)
peak_month     <- peak_month_row$month_label
peak_panel     <- tibble(month_label = peak_month)

peak_day <- df %>%
  filter(!is.na(commits)) %>%
  slice_max(commits, n = 1, with_ties = FALSE)

subtitle_str <- sprintf(
  "Busiest month: %s (%d commits) · single-day high: %d on %s",
  peak_month, peak_month_row$total, peak_day$commits, format(peak_day$date, "%b %d")
)

# --- Plot ---------------------------------------------------------------
title_str <- "heatmap-calendar · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = week_in_month, y = day_label, fill = commits)) +
  geom_rect(
    data = peak_panel, aes(xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = Inf),
    inherit.aes = FALSE, fill = IMPRINT_PALETTE[1], alpha = 0.10
  ) +
  geom_tile(color = PAGE_BG, linewidth = 0.9, width = 0.85, height = 0.8) +
  geom_tile(
    data = peak_day, aes(x = week_in_month, y = day_label),
    inherit.aes = FALSE, fill = NA, color = INK, linewidth = 1.1,
    width = 0.85, height = 0.8
  ) +
  scale_fill_gradient(
    low = IMPRINT_PALETTE[1], high = IMPRINT_PALETTE[3],
    na.value = INK_MUTED, name = "Commits (count)",
    guide = guide_colorbar(barwidth = 14, barheight = 0.6, ticks = FALSE)
  ) +
  scale_x_continuous(breaks = NULL) +
  facet_wrap(~month_label, ncol = 4) +
  labs(title = title_str, subtitle = subtitle_str, x = NULL, y = NULL) +
  theme_minimal(base_size = 8) +
  theme(
    aspect.ratio      = 7 / 6,
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    panel.spacing     = unit(1.1, "lines"),
    axis.ticks        = element_blank(),
    axis.text.y       = element_text(color = INK_SOFT, size = 8),
    strip.background  = element_rect(fill = ELEVATED_BG, color = NA),
    strip.text        = element_text(color = INK, size = 9, face = "bold"),
    plot.title        = element_text(color = INK, size = 13, face = "bold", hjust = 0),
    plot.subtitle     = element_text(color = INK_SOFT, size = 8.5, hjust = 0,
                                      margin = margin(t = 2, b = 8)),
    legend.position   = "bottom",
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    plot.margin       = margin(t = 12, r = 16, b = 10, l = 10)
  )

# --- Save --------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
