### Fixed

- **Two set v2 fix patterns recognize the P3.1 arm's wording.** The #11960
  gridline fix now also matches "value labels are clear of the grid", and the
  #11954 axis-title fix matches "the count axis now carries an explicit title".
  Both are genuine fixes that the P3.1 arm cited in words the patterns did not
  know, so its forward merges without a labeled carrier drop from 2/18 to 0/18.
  The v2-baseline and p3-v2 reports don't change. (#11979)
