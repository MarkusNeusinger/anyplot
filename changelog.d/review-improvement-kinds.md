### Changed

- **Polish and optional additions no longer carry a regeneration.** Every
  improvement in a regeneration review now names its kind: a fix, a removal,
  an addition, or polish. Only a fix or a removal can replace the live
  implementation; adding an optional feature the spec only allows, or
  restyling an element the spec's scope excludes, rides along, and an
  improvement without a kind never carries. Feature coverage (DQ-01) no
  longer carries a replacement on its own, like the design and
  library-mastery criteria, and a missing optional feature no longer costs
  DQ-01 points. A kept regeneration stores a predecessor finding of kind
  addition or polish as a suggestion, not a defect, and the gate record and
  `gate-report` count the kinds. (#11977)
