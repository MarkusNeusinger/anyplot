### Changed

- **Review retest labels confirmed for sets v1 and v2.** Both manifests switch
  to `labels: confirmed`, so retest reports now fill the label metrics each
  set supports: named-defect and false-alarm rates, gate accuracy, and (set v2
  only) the carrier metric. The owner's corrections:
  the d3 force-collision pair of set v1 keeps in both orders; in set v2,
  #11960 merges forward on a fixed VQ-02 defect (the gridline through the
  value label), #11963 keeps, and #11953's label-clearance fix is dropped as a
  suggestion. (#11976)
