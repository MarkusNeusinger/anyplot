### Fixed

- **The sequential colour ramps change hue along their whole length, and their lowest values stay
  visible on a dark map.** In the per-theme ramps a long stretch changed in lightness only, so
  neighbouring levels read as one colour: blue to navy over the upper two thirds of the light ramps,
  deep green to brand green below the middle of the dark ones. The stops now take palette hues in
  one order from low to high, lime → green → blue → lavender: on the light page brand green → deep
  blue `#024582` → dark violet `#351E45` (fields start at pale mint as before), on the dark page
  olive or dark olive → brand green → pale blue. Positions stay proportional to lightness, and the
  smallest colour difference between neighbouring tenths rises or holds (light marks 3.9 → 5.3, dark
  fields 5.3 → 6.7 in CAM02-UCS); only the dark marks ramp, shorter at its low end, loses some under
  protanopia and tritanopia (4.5 → 3.8, 3.3 → 2.9). The low end of the dark marks ramp
  moves from `#007755` to `#6F7E20`, which keeps 3:1 against the page, the elevated shade and a land
  fill close to the page. A new style guide rule draws whatever a ramp colours opaque, keeps the
  thinnest line about 5 px wide, gives lines and points on a map the marks ramp, and keeps a dark
  map's land close to the page: translucency and light land fills had pushed thin low-value routes
  to 1.6:1 against the land. `core/palette.py`, the style guide, the generator prompt, the library
  prompts, the JavaScript harness's tokens, the contract check's allowed colours and the palette
  page carry the new stops; the palette page also keeps a stop's label clear of the end labels when
  the two sit close.
