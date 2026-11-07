### Fixed

- **A data change no longer fills a role that was open before it.** The
  rule from the plot-button fix that has the assistant bind a required role
  itself now applies only to a role the turn's own data change left open. A
  role that was open before the turn follows the conversion lines again, so
  "drop the Total row" no longer adds a row-number column for an empty axis.
  The prep eval caught it: from that fix on, 7 of 8 runs of the drop cases
  added a `row_number`, against 0 of 9 before it. (#12595)
