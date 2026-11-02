### Fixed

- **Library counts and layouts that still described the catalogue before JavaScript.** The language filter's tooltip
  named only Python and R and now names all four languages; the `GET /stats` example in `docs/reference/api.md`
  showed three fields and 9 libraries and now shows the live payload with `languages` and `lines_of_code`, each field
  explained; and `docs/reference/repository.md` listed 9 Python libraries with Highcharts among them and no
  `javascript/` directory, and now shows the 8 Python files and the five JavaScript ones. (#12526)
