### Changed

- **The chat adapts catalogue files that load a built-in example dataset.** A
  `sklearn.datasets` toy loader or generator, or `sns.load_dataset`, in a
  catalogue original is now a hint for the adapter at the eligibility scan
  (`validate_original`) instead of a security refusal, the way R's dataset
  packages already were; adapted code that keeps the loader or its import is
  refused as before, and downloads (`fetch_*`) and loaders that read a path stay
  refused everywhere. The chat never runs the original, so this costs no
  safety, and 68 of the 69 Python files that load such a dataset (the
  machine-learning specs) become eligible. The readiness self-check accepts
  these files, and the generator prompts no longer tell the sessions to keep a
  dataset refusal. The eval harness's preflight renders a catalogue file only
  when it passes the adapted code's security profile, so nothing renders an
  original that profile refuses.
