#' anyplot.ai
#' barcode-code128: Code 128 Barcode
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-05-21

library(ggplot2)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Code 128 Subset B patterns (values 0-106 in order, stop appended) -----
# Each string: 6 digit widths (bar-space-bar-space-bar-space), 11 modules each
# Stop pattern: 7 digit widths, 13 modules
CODE128 <- c(
  "212222","222122","222221","121223","121322","131222","122213","122312",
  "132212","221213","221312","231212","112232","122132","122231","113222",
  "123122","123221","223211","221132","221231","213212","223112","312131",
  "311222","321122","321221","312212","322112","322211","212123","212321",
  "232121","111323","131123","131321","112313","132113","132311","211313",
  "231113","231311","112133","112331","132131","113123","113321","133121",
  "313121","211331","231131","213113","213311","213131","311123","311321",
  "331121","312113","312311","332111","314111","221411","431111","111224",
  "111422","121124","121421","141122","141221","112214","112412","122114",
  "122411","142112","142211","241211","221114","413111","241112","134111",
  "111242","121142","121241","114212","124112","124211","411212","421112",
  "421211","212141","214121","412121","111143","111341","131141","114113",
  "114311","411113","411311","113141","114131","311141","411131","211412",
  "211214","211232",
  "2331112"  # stop symbol (index 108 in R / code value 106+stop)
)

# --- Encode a string using Code 128 Subset B --------------------------------
# Returns vector of pattern strings (data + check + stop)
encode_code128b <- function(text) {
  chars     <- strsplit(text, "")[[1]]
  code_vals <- vapply(chars, function(ch) utf8ToInt(ch) - 32L, integer(1L))
  start_val <- 104L  # Start B
  check_val <- (start_val + sum(seq_along(code_vals) * code_vals)) %% 103L
  all_vals  <- c(start_val, code_vals, check_val)
  c(CODE128[all_vals + 1L], CODE128[107L])  # patterns + stop (stop is at index 107)
}

# --- Build rectangle data frame from encoded patterns -----------------------
patterns_to_df <- function(patterns, quiet_modules = 10L) {
  x    <- quiet_modules
  rows <- list()
  for (pat in patterns) {
    widths <- as.integer(strsplit(pat, "")[[1]])
    for (i in seq_along(widths)) {
      if (i %% 2L == 1L) {  # odd index = bar (black)
        rows[[length(rows) + 1L]] <- c(x, x + widths[i])
      }
      x <- x + widths[i]
    }
  }
  total_w <- x + quiet_modules
  mat <- do.call(rbind, rows)
  df  <- data.frame(xmin = mat[, 1], xmax = mat[, 2], ymin = 0, ymax = 1)
  list(df = df, total_w = total_w)
}

# --- Data -------------------------------------------------------------------
set.seed(42)
label_text <- "SPEC-LAB-2024-X789"
patterns   <- encode_code128b(label_text)
barcode    <- patterns_to_df(patterns)
bar_df     <- barcode$df
total_w    <- barcode$total_w

# White barcode background (always white for scan reliability)
bg_rect <- data.frame(xmin = 0, xmax = total_w, ymin = 0, ymax = 1)

x_pad <- total_w * 0.05

# --- Plot -------------------------------------------------------------------
p <- ggplot() +
  geom_rect(
    data = bg_rect,
    aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax),
    fill = "white", color = NA
  ) +
  geom_rect(
    data = bar_df,
    aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax),
    fill = "black", color = NA
  ) +
  annotate(
    "text",
    x = total_w / 2, y = -0.30,
    label    = label_text,
    size     = 5.5,
    family   = "mono",
    color    = INK,
    fontface = "plain"
  ) +
  annotate(
    "text",
    x = total_w / 2, y = 1.32,
    label    = "Specimen Label — Healthcare Lab Tracking",
    size     = 4,
    color    = INK_SOFT,
    fontface = "plain"
  ) +
  labs(title = "barcode-code128 · r · ggplot2 · anyplot.ai") +
  coord_cartesian(
    xlim   = c(-x_pad, total_w + x_pad),
    ylim   = c(-0.70, 1.55),
    expand = FALSE,
    clip   = "off"
  ) +
  theme_void() +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.title       = element_text(
      color  = INK,
      size   = 12,
      hjust  = 0.5,
      margin = margin(b = 10, t = 8)
    ),
    plot.margin = margin(30, 80, 40, 80)
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
