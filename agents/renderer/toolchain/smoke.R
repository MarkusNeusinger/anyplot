# The toolchain image's own check (agents/renderer/toolchain.Dockerfile): R starts under the
# exec filter, every package of r-packages.txt loads, a program start is refused, and
# ggplot2 writes a PNG through ragg with a non-ASCII label.
packages <- readLines("/opt/anyplot/toolchain/r-packages.txt")
packages <- packages[nzchar(packages) & !startsWith(packages, "#")]
for (package in packages) suppressPackageStartupMessages(library(package, character.only = TRUE))

# The filter kills the child before it runs anything: a non-zero status, never a started program.
stopifnot(system("true") != 0)
stopifnot(identical(unname(Sys.which("uname")), ""))
stopifnot(identical(l10n_info()$`UTF-8`, TRUE))

png <- file.path(tempdir(), "smoke.png")
plot <- ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg)) +
  ggplot2::geom_point() +
  ggplot2::labs(title = "Gewicht über Verbrauch – été")
ggplot2::ggsave(png, plot, device = ragg::agg_png, width = 4, height = 3, dpi = 100)
stopifnot(file.exists(png), file.info(png)$size > 1000)
cat("toolchain smoke: R", as.character(getRversion()), "ggplot2", as.character(packageVersion("ggplot2")), "\n")
