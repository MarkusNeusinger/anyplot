### Fixed

- **Library counts and layouts that still described the catalogue before JavaScript.** The language filter's tooltip
  named only Python and R and now names all four languages; the `GET /stats` example in `docs/reference/api.md`
  showed three fields and 9 libraries and now shows the live payload with `languages` and `lines_of_code`, each field
  explained; and `docs/reference/repository.md` drew `metadata/` and `implementations/` as flat Python lists with
  Highcharts among them and no `javascript/` directory, and now shows the four language directories in every tree:
  8 Python files, ggplot2, Makie, and the five JavaScript ones. (#12526)
