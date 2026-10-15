### Added

- **Agent chat: gates for crowded value labels and the plot language's
  number format.** G11 counts the value labels, dots and shadows the
  catalogue draws once per bar or point and writes a measured VQ-03 line
  when more than 25 crowd a plot, or bar labels are wider than the space
  per bar (the live case: 52 labelled, dotted, shadowed bars of 26
  regions). G12 writes a VQ-06 line when a numeric tick label or annotation
  uses the other decimal mark than the plot language (`5.30` and `6.0 M`
  in a German plot). A server-side table of decimal and thousands marks and
  large-number words per language (`de`: `5,30`, `6,5 Mio.`) goes into the
  adapter's instruction, and the house-style exemption of the reviewer and
  scorer no longer covers elements whose count grows with the data
  (#12184).
