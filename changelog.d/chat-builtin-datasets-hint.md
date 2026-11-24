### Changed

- **The chat adapts catalogue files that load an example dataset.** A
  scikit-learn toy loader or generator (built-in data), or `sns.load_dataset`
  (which downloads its CSV), in a catalogue original is now a hint for the
  adapter at the eligibility scan (`validate_original`) instead of a security
  refusal, the way R's dataset packages already were. The original never runs,
  which is why even seaborn's download is accepted there and nowhere else:
  adapted code that keeps the loader or its import is refused as before, and
  scikit-learn's own downloads (`fetch_*`) and path readers stay refused in the
  original too. 68 of the 69 Python files that load such a dataset (the
  machine-learning specs) become eligible. The readiness self-check accepts
  these files, and the generator prompts no longer tell the sessions to keep a
  dataset refusal. The eval harness's preflight renders a catalogue file only
  when it passes the adapted code's security profile, so nothing renders an
  original that profile refuses. (#14245)
