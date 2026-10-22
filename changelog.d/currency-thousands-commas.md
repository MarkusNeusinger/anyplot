### Fixed

- **Three-digit comma groups in currency columns read as thousands.** A column
  whose unit is a currency (`€`, `$`, `£`, `CHF`, `EUR`, `USD`, `GBP`) and whose
  comma cells all sit in three-digit groups (`"$1,200"`, `"$12,500"`,
  `"1,200 USD"`) was previously typed as decimal commas (`1.2`, `12.5`) unless
  another column carried two comma groups or a dot decimal behind a comma group.
  Because a currency amount has at most two decimal places, `_commas_as_thousands`
  in `agents/anyplot/data/parse.py` now retypes such a column as whole numbers
  with comma thousands and announces the reading in a warning, while any cell
  with a one- or two-digit fraction after a comma (`"$1,25"`, `"$3,50"`) keeps
  the column on decimal commas.
