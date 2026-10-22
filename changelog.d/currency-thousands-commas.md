### Fixed

- **Currency columns read three-digit comma groups as thousands.** A pasted
  price column such as `"$1,200"`, `"$950"`, `"$12,500"` (also `1,200 USD`,
  `€ 1,200`, `CHF 12,500`) read as 1.2, 950 and 12.5; it now reads as 1200,
  950 and 12500 with a warning, since a money amount mostly has at most two
  decimals. A cell with a one- or two-digit fraction (`$1,25`) keeps the
  decimal comma, and a file that speaks for decimal commas keeps the question:
  one delimited by semicolons, or with a column of dot groups or of `1.234`
  shapes, so a fuel price of `1,789 €` stays 1.789. (#12228)
