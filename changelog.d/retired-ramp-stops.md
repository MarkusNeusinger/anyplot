### Fixed

- **The generator replaces a ramp stop that the style guide has retired.**
  `contract_check.py` gains a `retired-ramp` rule for `#002850`, `#00573D`
  and `#007755`, the ends of the per-theme ramps before they turned in hue.
  It must be fixed, also on a regeneration. In the regeneration batch of
  2026-11-27, 4 of 34 merged regenerations of files on the old ramps had
  copied their predecessor's ramp and kept it under the advisory `palette`
  line, with the reason that its stops were the style guide's. On `main` the
  rule flags 9 of 4,863 files. (#15000)
