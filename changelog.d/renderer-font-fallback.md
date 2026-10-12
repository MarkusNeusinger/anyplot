### Added

- **Plot text in any script.** The renderer image installs Noto Sans, Noto
  Sans CJK and the Noto Sans faces of the scripts DejaVu Sans lacks (37 files,
  46.8 MB, Regular and Bold, with their OFL notices), and the harness appends
  them to every font lookup after the font the code chose, so a Chinese,
  Japanese, Korean, Arabic, Devanagari or Thai title draws with real glyphs
  while the catalogue's DejaVu Sans stays the first font. The lookup-level
  append is what survives seaborn's `set_theme`, which rewrites `font.family`
  in 306 catalogue files, and a `monospace` or `serif` set on one text. The
  image build fails when a fallback family is missing from the cache. Arabic
  and Hebrew already rendered shaped and right to left through the pinned
  matplotlib's libraqm; the documented limits are `$…$` math text, the Han
  regional forms and the scripts outside the installed set. (#12144)
- **G10, the glyph gate.** The harness records every code point matplotlib
  reports as having no glyph in any font of its text, plain text and `$…$`
  math alike, as `missing_glyphs` in the probe; the host turns it into a
  VQ-01 line that names the count and up to three characters with their code
  points, tells the repair that a user's column name stays as it is, and
  stays in the result's residual lines even after a reviewer `ok`, because a
  measured missing glyph is not a judgement. The CI image job renders a
  seven-script fixture through the image and a DejaVu-only control, and
  asserts the probe on both. (#12144)
