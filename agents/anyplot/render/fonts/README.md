# Bundled fonts

This directory holds the two font files that `agents/anyplot/render/watermark.py`
draws the footer strip of user plots with. They are the only fonts the repository
ships, and the anyplot-agents service loads them when it starts.

| File | Font | Version | SHA-256 |
|---|---|---|---|
| `JetBrainsMono-Regular.ttf` | JetBrains Mono Regular | 2.304 | `a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f` |
| `JetBrainsMono-Bold.ttf` | JetBrains Mono Bold | 2.304 | `5590990c82e097397517f275f430af4546e1c45cff408bde4255dad142479dcb` |
| `OFL.txt` | The licence text shipped with the release | 2.304 | `30f0c136e3c88e422d0791acd97238870f9054a9729bc34cf2ff0d4ed8cac4ad` |

## Source

All three files come unmodified from the official release asset
<https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip>
(SHA-256 `6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf`):
`fonts/ttf/JetBrainsMono-Regular.ttf`, `fonts/ttf/JetBrainsMono-Bold.ttf` and
`OFL.txt`. No glyph, table or name was changed, subset or renamed.

## Licence

Copyright 2020 The JetBrains Mono Project Authors
(<https://github.com/JetBrains/JetBrainsMono>).

JetBrains Mono is licensed under the SIL Open Font License, Version 1.1. The
full text is in [`OFL.txt`](OFL.txt) next to the fonts and at
<https://openfontlicense.org>. The licence header declares no Reserved Font
Name. The OFL lets you use, bundle and redistribute the fonts with software as
long as they are not sold by themselves and this licence travels with them; the
rest of the repository stays under its own MIT licence.

## Updating

To move to a newer release, replace the files from that release's zip without
modifying them, then update the version, the source URL and every SHA-256 value
in this file. `tests/unit/agents/runtime/test_watermark.py` checks the hashes,
so a file that differs from this table fails the tests.
