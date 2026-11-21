### Fixed

- **The chat's validator reads column names unpacked in one line.** plotnine
  code that names its columns as `POS_X, POS_Y = "x", "y"` and then passes them
  to `aes()` was refused as if the names hid code, while `POS_X = "x"` on its own
  line passed; a regeneration of venn-basic in plotnine was kept for that alone.
  A top-level unpacking of literals now counts as the one binding the rule
  needs, and a starred item, a nested target or a value the walk cannot read
  is still refused. (#13480)
