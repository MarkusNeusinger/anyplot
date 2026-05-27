#' anyplot.ai
#' line-navigator: Line Chart with Mini Navigator
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-27

library(ggplot2)
library(ragg)
library(gridExtra)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

ANYPLOT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)
LINE_COLOR  <- ANYPLOT_PALETTE[1]
SEL_ALPHA   <- if (THEME == "light") 0.22 else 0.38

# --- Data -------------------------------------------------------------------
# Daily temperature sensor over 2 years (730 data points)
dates       <- seq.Date(as.Date("2022-01-01"), as.Date("2023-12-31"), by = "day")
n           <- length(dates)
day_of_yr   <- as.numeric(format(dates, "%j"))
trend       <- seq(0, 8, length.out = n)
seasonal    <- 14 * sin(2 * pi * day_of_yr / 365 - pi / 2)
noise       <- cumsum(rnorm(n, 0, 0.35))
temperature <- 20 + trend + seasonal + noise
df          <- data.frame(date = dates, temperature = temperature)

# Selection window: summer 2023 — the detail view shown in the main chart
sel_start <- as.Date("2023-06-01")
sel_end   <- as.Date("2023-08-31")
df_main   <- df[df$date >= sel_start & df$date <= sel_end, ]

# --- Title ------------------------------------------------------------------
TITLE      <- "line-navigator · r · ggplot2 · anyplot.ai"
title_len  <- nchar(TITLE)
title_size <- min(12, max(8, round(12 * 67 / title_len)))

# --- Shared theme -----------------------------------------------------------
base_theme <- theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks        = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = title_size, face = "bold"),
    plot.subtitle     = element_text(color = INK_SOFT, size = 9),
    plot.margin       = margin(t = 8, r = 10, b = 4, l = 10, unit = "pt")
  )

# --- Main chart: detail view of selected range ------------------------------
p_main <- ggplot(df_main, aes(x = date, y = temperature)) +
  geom_line(color = LINE_COLOR, linewidth = 1.0) +
  scale_x_date(
    date_labels = "%b %d",
    date_breaks = "2 weeks",
    expand      = expansion(mult = c(0.02, 0.02))
  ) +
  scale_y_continuous(
    labels = function(x) paste0(round(x, 0), "°C"),
    expand = expansion(mult = c(0.05, 0.12))
  ) +
  labs(
    title    = TITLE,
    subtitle = sprintf(
      "Detail view: %s – %s",
      format(sel_start, "%b %d, %Y"),
      format(sel_end,   "%b %d, %Y")
    ),
    x = NULL,
    y = "Temperature (°C)"
  ) +
  base_theme +
  theme(
    panel.grid.major.x = element_blank(),
    axis.text.x        = element_text(angle = 30, hjust = 1, size = 8)
  )

# --- Navigator: full history with selection window highlighted --------------
p_nav <- ggplot(df, aes(x = date, y = temperature)) +
  annotate(
    "rect",
    xmin = sel_start, xmax = sel_end,
    ymin = -Inf,      ymax = Inf,
    fill  = LINE_COLOR, alpha = SEL_ALPHA
  ) +
  geom_line(color = LINE_COLOR, linewidth = 0.45, alpha = 0.75) +
  scale_x_date(
    date_labels = "%b '%y",
    date_breaks = "3 months",
    expand      = expansion(mult = c(0.01, 0.01))
  ) +
  scale_y_continuous(labels = NULL, breaks = NULL) +
  labs(x = "Full history – Jan 2022 to Dec 2023", y = NULL) +
  base_theme +
  theme(
    panel.grid.major = element_blank(),
    axis.title.x     = element_text(color = INK_SOFT, size = 8),
    axis.text.x      = element_text(size = 7, color = INK_SOFT),
    plot.margin      = margin(t = 2, r = 10, b = 6, l = 10, unit = "pt")
  )

# --- Combine and save -------------------------------------------------------
ragg::agg_png(
  filename   = sprintf("plot-%s.png", THEME),
  width      = 8,
  height     = 4.5,
  units      = "in",
  res        = 400,
  background = PAGE_BG
)
gridExtra::grid.arrange(p_main, p_nav, nrow = 2, heights = c(5, 1))
invisible(dev.off())
