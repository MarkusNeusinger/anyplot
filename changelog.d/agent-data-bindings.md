### Fixed

- **An id never labels the bars, and a founding year is never the
  measure.** The default bindings of "Use with my data" rank a text column
  of record ids (every value distinct, named like `Organization Id`, `UUID`
  or `EAN`) after every other text column for a category or label, and read
  a year named for an event of each row (`Founded`, `Year built`, `Baujahr`)
  as no measure and no time key. A table of organizations now binds
  `Name` and `Number of employees` to a bar chart, where it bound
  `Organization Id` and `Founded`. A lone id column still labels, and
  codes such as `iso3` keep their rank.
- **A header in two lines is joined or named, never misread.** A grouped
  header copied from a spreadsheet or an expanded web table (`Density` over
  `/km2` and `/mi2`) becomes one name per column, `Density /km2`, with a
  warning. A browser's text copy that lost the spans is refused with that
  cause instead of a hint about quotes that did not apply, and a header
  shorter than rows that all agree says so.
- **A replacing paste keeps the plot's axes.** New data that replaces the
  old carries each binding to the new column of the same name or meaning
  (`Land area km2` to `Area km2`), so `x` stays the area instead of
  flipping to the first number column. The other roles get the defaults.
