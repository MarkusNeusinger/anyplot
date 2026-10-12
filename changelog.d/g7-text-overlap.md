### Changed

- **The overlap gate G7 measures every drawn text, not only tick labels.** An axis
  label, title, legend text or annotation that overlaps any other text by more than
  3 px becomes an advisory VQ-02 line naming both roles and the depth, such as "the
  radial axis label overlaps the tick label by 36 px", with a polar hint when polar
  axes are involved. The owner's polar case had the label `y` on the `270°` tick
  label, which the reviewer read as a missing label; the probe now catches it.
