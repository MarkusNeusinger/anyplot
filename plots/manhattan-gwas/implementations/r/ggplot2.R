#' anyplot.ai
#' manhattan-gwas: Manhattan Plot for GWAS
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
ANYPLOT_AMBER <- "#DDCC77"

# --- Data --------------------------------------------------------------------
# Approximate human chromosome lengths (Mb), chromosomes 1-22
chr_lengths <- c(
  249, 243, 198, 191, 180, 171, 159, 145, 138, 133,
  135, 133, 114, 107, 102, 90, 83, 80, 59, 63, 48, 51
)
n_chr <- length(chr_lengths)

chr_info <- tibble::tibble(
  chromosome = 1:n_chr,
  length_mb  = chr_lengths
) %>%
  mutate(offset = lag(cumsum(length_mb), default = 0) * 1e6)

n_snps_total <- 9000
snps_per_chr <- round(n_snps_total * chr_lengths / sum(chr_lengths))

snps <- lapply(1:n_chr, function(i) {
  tibble::tibble(
    chromosome = i,
    position   = sort(sample(seq_len(chr_lengths[i] * 1e6), snps_per_chr[i])),
    p_value    = runif(snps_per_chr[i])
  )
}) %>% bind_rows()

# Simulated GWAS hits: clusters of low p-values around a few causal loci
peak_chr      <- c(3, 8, 14, 19)
peak_lead_log <- c(12.0, 9.2, 15.4, 7.8)
peaks <- Map(function(chr, lead_log) {
  cluster_size <- 24
  spread_bp    <- rnorm(cluster_size, 0, 1.5e6)
  lead_pos     <- sample(seq_len(chr_lengths[chr] * 1e6), 1)
  cluster_pos  <- pmin(pmax(lead_pos + spread_bp, 1), chr_lengths[chr] * 1e6)
  cluster_log  <- pmax(0.1, lead_log - abs(spread_bp) / 4e5 + rnorm(cluster_size, 0, 0.3))
  tibble::tibble(
    chromosome = chr,
    position   = round(cluster_pos),
    p_value    = 10^(-cluster_log)
  )
}, peak_chr, peak_lead_log) %>% bind_rows()

gwas <- bind_rows(snps, peaks) %>%
  left_join(chr_info, by = "chromosome") %>%
  mutate(
    bp_cum     = position + offset,
    neg_log_p  = -log10(p_value),
    chr_parity = ifelse(chromosome %% 2 == 0, "even", "odd")
  )

chr_axis <- chr_info %>%
  mutate(center = offset + length_mb * 1e6 / 2)

genome_wide_line <- -log10(5e-8)
suggestive_line  <- -log10(1e-5)
sig_hits         <- gwas %>% filter(p_value < 5e-8)

# --- Plot ----------------------------------------------------------------
p <- ggplot(gwas, aes(x = bp_cum, y = neg_log_p, color = chr_parity)) +
  geom_hline(yintercept = suggestive_line, linetype = "dotted",
             color = ANYPLOT_AMBER, linewidth = 0.5) +
  geom_hline(yintercept = genome_wide_line, linetype = "dashed",
             color = IMPRINT_PALETTE[5], linewidth = 0.6) +
  geom_point(size = 0.6, alpha = 0.65) +
  geom_point(data = sig_hits, aes(x = bp_cum, y = neg_log_p),
             color = IMPRINT_PALETTE[5], size = 2.2, alpha = 0.9, inherit.aes = FALSE) +
  scale_color_manual(values = c(odd = IMPRINT_PALETTE[1], even = IMPRINT_PALETTE[3])) +
  scale_x_continuous(breaks = chr_axis$center, labels = chr_axis$chromosome,
                      expand = expansion(mult = 0.01)) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.08))) +
  labs(
    title = "manhattan-gwas · r · ggplot2 · anyplot.ai",
    x     = "Chromosome",
    y     = expression(-log[10](italic(p) * "-value"))
  ) +
  guides(color = "none") +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    panel.grid.minor.y = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.2),
    axis.title        = element_text(color = INK, size = 10),
    axis.text.y       = element_text(color = INK_SOFT, size = 8),
    axis.text.x       = element_text(color = INK_SOFT, size = 6.5),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = 12)
  )

# --- Save --------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
