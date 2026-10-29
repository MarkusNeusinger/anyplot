#' anyplot.ai
#' box-basic: Basic Box Plot
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 84/100 | Updated: 2026-10-29

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
    "#009E73", "#C475FD", "#4467A3", "#BD8233",
    "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Columns: set these to your table's column names -----------------------
DEPARTMENT <- "Department"          # role: category
SALARY     <- "Annual Salary (USD)" # role: value

# --- Data: replace this block with your own table, e.g. df <- read.csv("salaries.csv", check.names = FALSE)
set.seed(42)
departments <- c("Engineering", "Marketing", "Sales", "Design", "Research")
dept_means  <- c(95000, 72000, 78000, 82000, 105000)
dept_sds    <- c(18000, 12000, 15000, 13000, 20000)
n_per_dept  <- 80

df <- tibble::tibble(
    !!DEPARTMENT := rep(departments, each = n_per_dept),
    !!SALARY     := unlist(lapply(seq_along(departments), function(i) {
        rnorm(n_per_dept, mean = dept_means[i], sd = dept_sds[i])
    }))
)

# --- Plot: reads only df and the constants above ----------------------------
df[[DEPARTMENT]] <- factor(df[[DEPARTMENT]], levels = unique(df[[DEPARTMENT]]))

p <- ggplot(df, aes(x = .data[[DEPARTMENT]], y = .data[[SALARY]], fill = .data[[DEPARTMENT]])) +
    # Whiskers reach 1.5 * IQR; values beyond are drawn as individual outlier points
    geom_boxplot(
        color                = INK_SOFT,
        linewidth            = 0.6,
        median.linewidth     = 1.4,
        median.colour        = INK,
        outlier.size         = 1.6,
        outlier.alpha        = 0.8,
        width                = 0.55,
        alpha                = 0.85
    ) +
    scale_fill_manual(values = IMPRINT_PALETTE, guide = "none") +
    scale_y_continuous(
        labels = label_dollar(scale = 0.001, suffix = "k"),
        expand = expansion(mult = c(0.05, 0.08))
    ) +
    labs(
        title    = "box-basic · r · ggplot2 · anyplot.ai",
        x        = DEPARTMENT,
        y        = SALARY
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background   = element_rect(fill = PAGE_BG, color = NA),
        panel.border       = element_blank(),
        panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.2),
        panel.grid.major.x = element_blank(),
        panel.grid.minor   = element_blank(),
        axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.4),
        axis.line.y        = element_line(color = INK_SOFT, linewidth = 0.4),
        axis.title         = element_text(color = INK,      size = 10),
        axis.text          = element_text(color = INK_SOFT, size = 8),
        plot.title         = element_text(
            color  = INK,
            size   = 12,
            margin = margin(b = 10)
        ),
        plot.margin = margin(t = 16, r = 20, b = 16, l = 16)
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
