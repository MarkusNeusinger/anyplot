### Changed

- **Two series of a family trade columns instead of one dropping out.** In
  the data panel, picking for one member of a numbered series family
  (`y1`, `y2`, ...) the column another member holds now swaps the two:
  with `y1` on Sales and `y2` on Cost, setting `y2` to Sales puts `y1` on
  Cost, and both series stay in the plot. Until now the other member was
  cleared and the family closed up, so Cost left the plot. A member without
  a column, the next member's `— add a column —`, has nothing to trade, so
  the column still moves there. (#12567)
