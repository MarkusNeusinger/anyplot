### Changed

- **A 1-D NumPy array converts to one column.** "Use with my data" used to refuse a
  plain 1-D `.npy` array as `file_array_shape`; it now becomes one column, `value`,
  which is what a histogram, a box plot or a line over the index needs. An `.npz` of
  two or more plain 1-D arrays of one length, which is what
  `np.savez(path, t=t, y=y)` writes, becomes one table with a column per array named
  after it; scalars saved next to them are left out and named. Any other `.npz` is
  still read one array at a time: a 2-D or structured array before a 1-D one. Still
  refused are 0-D arrays, arrays of three or more dimensions and structured arrays of
  more than one. (#12413)

### Fixed

- **Missing values in a converted NumPy array keep their rows.** A row whose cells
  were all missing reached the paste box as a blank line, which the parser skips, so
  every later value moved up one row. The converter now writes such a row as `NaN`,
  which the parser reads as missing and reports. An array without any value is now
  refused as `file_empty` instead of failing later in the paste. (#12413)
