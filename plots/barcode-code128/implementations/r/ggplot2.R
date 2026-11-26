#' anyplot.ai
#' barcode-code128: Code 128 Barcode
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: pending | Updated: 2026-11-26

library(ggplot2)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

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

# --- Data -------------------------------------------------------------------
label_text    <- "SPEC-LAB-2024-X789"
quiet_modules <- 10L

# Subset B: Start B (104), values ord(ch) - 32, mod-103 check character, stop
code_vals <- utf8ToInt(label_text) - 32L
start_val <- 104L
check_val <- (start_val + sum(seq_along(code_vals) * code_vals)) %% 103L
patterns  <- c(CODE128[c(start_val, code_vals, check_val) + 1L], CODE128[107L])

# Module widths of every pattern; odd positions are bars, even are spaces
widths  <- unlist(lapply(strsplit(patterns, ""), as.integer))
# Each pattern has an even digit count except the 7-digit stop, which also
# starts with a bar, so bar/space parity is restarted per pattern
is_bar  <- unlist(lapply(strsplit(patterns, ""), function(p) rep_len(c(TRUE, FALSE), length(p))))
edges   <- quiet_modules + cumsum(widths)
bar_df  <- data.frame(
  xmin = (edges - widths)[is_bar],
  xmax = edges[is_bar],
  ymin = 0,
  ymax = 1
)
total_w <- max(edges) + quiet_modules

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
  # Subtle frame around barcode to anchor it visually
  geom_rect(
    data = bg_rect,
    aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax),
    fill = NA, color = INK_SOFT, linewidth = 0.5
  ) +
  annotate(
    "text",
    x = total_w / 2, y = -0.26,
    label    = label_text,
    size     = 6.5,
    family   = "mono",
    color    = INK,
    fontface = "plain"
  ) +
  annotate(
    "text",
    x = total_w / 2, y = 1.30,
    label    = "Specimen Label — Healthcare Lab Tracking",
    size     = 4.5,
    color    = INK_SOFT,
    fontface = "italic"
  ) +
  labs(
    title   = "barcode-code128 · r · ggplot2 · anyplot.ai",
    caption = "Code 128 Subset B · Mod-103 check digit · Quiet zones: 10× module width"
  ) +
  coord_cartesian(
    xlim   = c(-x_pad, total_w + x_pad),
    ylim   = c(-0.55, 1.50),
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
      face   = "bold",
      margin = margin(b = 10, t = 8)
    ),
    plot.caption     = element_text(
      color  = INK_MUTED,
      size   = 8,
      hjust  = 0.5,
      margin = margin(t = 6, b = 4)
    ),
    plot.margin = margin(30, 80, 20, 80)
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
